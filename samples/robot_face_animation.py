import math
import random
import socket
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import click
from PIL import Image, ImageColor, ImageDraw, ImageOps

from ottopi0 import __version__, click_common_opts, errmsg, get_logger

# ディスプレイ制御用
try:
    from pi0disp import ST7789V

    HAS_LCD = True
except ImportError:
    HAS_LCD = False

# PCプレビュー用 (OpenCV)
try:
    import cv2
    import numpy as np

    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


# --- 設定 ---


# --- 状態クラス ---
@dataclass
class EyeState:
    openness: float = 1.0  # 目の開き具合 (0.0: 閉, 1.0: 開)
    size: float = 8.0  # 目の大きさの基準となる半径
    # 閉じたときの目の曲がり具合 (-1.0: 谷, 0.0: 直線, 1.0: 山)
    curve: float = 0.0

    def copy(self):
        return EyeState(self.openness, self.size, self.curve)


@dataclass
class FaceState:
    mouth_curve: float = 0  # 口の曲がり具合: +20(笑顔) ～ -20(への字)
    brow_tilt: float = 0  # 眉毛の角度
    mouth_open: float = 0  # 口の開き具合: 0(線) ～ 1(丸)
    left_eye: EyeState = field(default_factory=EyeState)
    right_eye: EyeState = field(default_factory=EyeState)

    def copy(self):
        return FaceState(
            self.mouth_curve,
            self.brow_tilt,
            self.mouth_open,
            self.left_eye.copy(),
            self.right_eye.copy(),
        )


# --- 表情定義 ---


# --- ヘルパー関数 ---
def lerp(a, b, t):
    """線形補間"""
    return a + (b - a) * t


# --- クラス定義 ---


class DisplayOutput(ABC):
    """ディスプレイ出力を抽象化するクラス"""

    def __init__(self, debug=False):
        """Constructor."""
        self._debug = debug
        self._log = get_logger(self.__class__.__name__, self._debug)
        self._log.debug("initialized DisplayOutput (abstract)")

    @abstractmethod
    def show(self, pil_image):
        """画像をデバイスに転送"""
        pass

    @abstractmethod
    def close(self):
        """リソース解放"""
        pass


class LcdOutput(DisplayOutput):
    """LCDへの出力を担当する具象クラス"""

    def __init__(self, debug=False):
        super().__init__(debug)
        self.lcd = ST7789V(rotation=270)
        self._log.debug("initialized LcdOutput")

    def show(self, pil_image):
        self.lcd.display(pil_image)

    def close(self):
        self.lcd.close(True)


class PreviewOutput(DisplayOutput):
    """OpenCVウィンドウへの出力を担当する具象クラス"""

    def __init__(self, debug=False):
        super().__init__(debug)
        self._log.debug("initialized PreviewOutput")

    def show(self, pil_image):
        # PIL -> OpenCV (BGR)
        frame = np.array(pil_image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Robot Face", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            raise KeyboardInterrupt("ESC pressed")

    def close(self):
        cv2.destroyAllWindows()


def _check_pigpio(host="localhost", port=8888, timeout=0.1):
    """pigpioデーモンの存在確認"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def create_output_device(debug=False) -> DisplayOutput:
    """利用可能な出力デバイスを検出し、適切なDisplayOutputインスタンスを返すファクトリ関数"""
    _log = get_logger("create_output_device", debug)

    # 1. ハードウェア (ST7789) の確認
    if HAS_LCD:
        if _check_pigpio():
            try:
                _log.debug("Found LCD, returning LcdOutput.")
                return LcdOutput(debug=debug)
            except Exception as e:
                _log.warning(errmsg(e))
        else:
            _log.warning("no pigpiod")

    # 2. OpenCVプレビュー
    if HAS_OPENCV:
        _log.debug("Found OpenCV, returning PreviewOutput.")
        return PreviewOutput(debug=debug)

    # 3. なし
    _log.warning("警告: 表示可能なデバイスがありません (コンソール実行のみ)")
    # 実際には、何も表示しないDummyOutputなどを返すことも検討できる
    raise RuntimeError("No suitable display output device found.")


class RobotFace:
    """顔の状態管理と描画を担当するクラス"""

    LINE_COLOR = "black"
    FACE_BG_COLOR = (255, 255, 220)

    # レイアウト定数 (顔のパーツの相対座標)
    LAYOUT = {
        "eye_y": 45,
        "eye_offset": 32,
        "brow_y_offset": -12,  # 目のY座標からのオフセット
        "mouth_cy": 70,
        "mouth_width": 30,
        "mouth_open_radius_factor": 8,
        "mouth_curve_p0_x": 35,
        "mouth_curve_p2_x": 65,
        "eye_closed_bezier_offset_x": 8,
        "eye_closed_bezier_offset_y": 2,
        "eye_closed_line_offset_x": 7,
        "brow_bezier_offset_x": 9,
        "brow_bezier_y_offset_factor": 10,
    }

    # カラー定数
    COLORS = {
        "line": "black",
        "face_bg": (255, 255, 220),
        "brow": (128, 64, 64),
        "eye_outline": (0, 0, 192),  # 開いている目の輪郭
        "mouth_line": (255, 32, 0),  # 口の線
        "mouth_fill": (128, 0, 0),  # 開いている口の塗りつぶし
        "eye_fill": "white",  # 開いている目の塗りつぶし
    }

    MOODS = {
        "neutral": FaceState(brow_tilt=0),
        "happy": FaceState(
            mouth_curve=15,
            brow_tilt=0,
            left_eye=EyeState(size=8, curve=1),
            right_eye=EyeState(size=8, curve=1),
        ),
        "sad": FaceState(
            mouth_curve=-15,
            brow_tilt=-10,
            left_eye=EyeState(size=7, curve=-1),
            right_eye=EyeState(size=7, curve=-1),
        ),
        "angry": FaceState(
            mouth_curve=-10,
            brow_tilt=25,
            left_eye=EyeState(size=6),
            right_eye=EyeState(size=6),
        ),
        "wink-r": FaceState(
            mouth_curve=15,
            brow_tilt=0,
            left_eye=EyeState(size=8, openness=0.1, curve=1),
            right_eye=EyeState(size=8, curve=1),
        ),
        "wink-l": FaceState(
            mouth_curve=15,
            brow_tilt=0,
            left_eye=EyeState(size=8, curve=1),
            right_eye=EyeState(size=8, openness=0.1, curve=1),
        ),
        "surprised": FaceState(
            mouth_curve=0,
            mouth_open=1.0,
            left_eye=EyeState(size=12),
            right_eye=EyeState(size=12),
        ),
        "sleepy": FaceState(
            mouth_curve=0,
            brow_tilt=0,
            left_eye=EyeState(size=8, openness=0.1, curve=-1),
            right_eye=EyeState(size=8, openness=0.1, curve=-1),
        ),
        "smily": FaceState(
            mouth_curve=20,
            brow_tilt=0,
            left_eye=EyeState(size=7, openness=0.1, curve=1),
            right_eye=EyeState(size=7, openness=0.1, curve=1),
        ),
    }

    def __init__(self, mood: str, size=240, debug=False):
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("mood=%s,size=%s", mood, size)

        if mood not in self.MOODS:
            raise ValueError(
                f"invalid mood: '{mood}' not in {list(self.MOODS.keys())}",
            )

        self.mood = mood
        self.size = size

        self.current_state = self.MOODS[self.mood].copy()
        self.target_state = self.MOODS[self.mood].copy()

        # 描画用ヘルパー係数
        self.scale = size / 100.0

        # 視線状態管理
        self.current_gaze_x: float = 0.0
        self.target_gaze_x: float = 0.0

    def update(self, speed=0.5):
        """状態をターゲットに近づける"""
        c, t = self.current_state, self.target_state
        c.mouth_curve = lerp(c.mouth_curve, t.mouth_curve, speed)
        c.brow_tilt = lerp(c.brow_tilt, t.brow_tilt, speed)
        c.mouth_open = lerp(c.mouth_open, t.mouth_open, speed)
        self.current_gaze_x = lerp(
            self.current_gaze_x, self.target_gaze_x, speed
        )

        # left eye
        c.left_eye.openness = lerp(
            c.left_eye.openness, t.left_eye.openness, speed
        )
        c.left_eye.size = lerp(c.left_eye.size, t.left_eye.size, speed)
        c.left_eye.curve = lerp(c.left_eye.curve, t.left_eye.curve, speed)

        # right eye
        c.right_eye.openness = lerp(
            c.right_eye.openness, t.right_eye.openness, speed
        )
        c.right_eye.size = lerp(c.right_eye.size, t.right_eye.size, speed)
        c.right_eye.curve = lerp(c.right_eye.curve, t.right_eye.curve, speed)

    def set_target_mood(self, mood_name):
        """表情セット"""
        if mood_name in self.MOODS:
            self.target_state = self.MOODS[mood_name].copy()

    def set_gaze(self, x):
        """視線セット (-20 to +20)"""
        self.target_gaze_x = x

    def _xy(self, x, y):
        return (x * self.scale, y * self.scale)

    def _w(self, width):
        return max(1, int(width * self.scale))

    def _draw_bezier_curve(self, draw, p0, p1, p2, color, width, steps=15):
        """3点の制御点からベジェ曲線を計算して描画する"""
        points = []
        for i in range(steps + 1):
            t = i / steps
            # 2次ベジェ曲線の公式
            bx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
            by = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
            points.append((bx, by))

        draw.line(points, fill=color, width=width, joint="curve")

    def _draw_eye(
        self,
        draw,
        cx,
        eye_y,
        eye_state: EyeState,
        tilt,
        gaze_offset,
    ):
        # 視線を加味した中心X
        real_cx = cx + gaze_offset

        # 目のサイズ
        r = eye_state.size * self.scale
        ry = r * eye_state.openness

        # 描画
        if ry < 4:
            # 目が閉じている場合
            if eye_state.curve != 0:
                # ベジェ曲線
                p0 = self._xy(
                    real_cx - self.LAYOUT["eye_closed_bezier_offset_x"],
                    eye_y + self.LAYOUT["eye_closed_bezier_offset_y"],
                )
                p1 = self._xy(
                    real_cx,
                    eye_y
                    - self.LAYOUT["eye_closed_bezier_offset_x"]
                    * eye_state.curve,
                )
                p2 = self._xy(
                    real_cx + self.LAYOUT["eye_closed_bezier_offset_x"],
                    eye_y + self.LAYOUT["eye_closed_bezier_offset_y"],
                )
                self._draw_bezier_curve(
                    draw,
                    p0,
                    p1,
                    p2,
                    color=self.COLORS["line"],
                    width=self._w(4),
                    steps=10,
                )
            else:
                # 直線
                draw.line(
                    [
                        self._xy(
                            real_cx - self.LAYOUT["eye_closed_line_offset_x"],
                            eye_y,
                        ),
                        self._xy(
                            real_cx + self.LAYOUT["eye_closed_line_offset_x"],
                            eye_y,
                        ),
                    ],
                    fill=self.COLORS["line"],
                    width=self._w(4),
                )
        else:
            # 開いている場合: 楕円
            s_cx, s_cy = self._xy(real_cx, eye_y)
            bbox = [s_cx - r, s_cy - ry, s_cx + r, s_cy + ry]
            draw.ellipse(
                bbox,
                outline=self.COLORS["eye_outline"],
                fill=self.COLORS["eye_fill"],
                width=self._w(10),
            )

    def _draw_brows(self, draw, left_cx, right_cx, eye_y, brow_tilt):
        if abs(brow_tilt) > 1:
            brow_y = eye_y + self.LAYOUT["brow_y_offset"]
            offset_y = (
                math.tan(math.radians(brow_tilt))
                * self.LAYOUT["brow_bezier_y_offset_factor"]
            )

            # 左眉
            p1_l = self._xy(
                left_cx - self.LAYOUT["brow_bezier_offset_x"],
                brow_y - offset_y,
            )
            p2_l = self._xy(
                left_cx + self.LAYOUT["brow_bezier_offset_x"],
                brow_y + offset_y,
            )
            draw.line(
                [p1_l, p2_l], fill=self.COLORS["brow"], width=self._w(5)
            )

            # 右眉
            # 右目の眉毛はX軸方向のオフセットの符号が逆になる
            p1_r = self._xy(
                right_cx - self.LAYOUT["brow_bezier_offset_x"],
                brow_y + offset_y,
            )
            p2_r = self._xy(
                right_cx + self.LAYOUT["brow_bezier_offset_x"],
                brow_y - offset_y,
            )
            draw.line(
                [p1_r, p2_r], fill=self.COLORS["brow"], width=self._w(5)
            )

    def _draw_outline(self, draw):
        box = [*self._xy(0, 0), *self._xy(100, 100)]
        draw.rounded_rectangle(
            box,
            radius=20 * self.scale,
            outline=self.COLORS["line"],
            fill=self.COLORS["face_bg"],
            width=1,
        )

    def _draw_mouth(self, draw):
        mouth_cx = 50  # 水平中央
        mouth_cy = self.LAYOUT["mouth_cy"]
        st = self.current_state

        if st.mouth_open > 0.5:
            # 丸い口 (驚きなど)
            factor = (st.mouth_open - 0.5) * 2
            r = self.LAYOUT["mouth_open_radius_factor"] * self.scale * factor
            if r > 1:
                cx, cy = self._xy(mouth_cx, mouth_cy)
                draw.ellipse(
                    [cx - r, cy - r * 1.2, cx + r, cy + r * 1.2],
                    outline=self.COLORS["mouth_line"],
                    fill=self.COLORS["mouth_fill"],
                    width=self._w(4),
                )
        if st.mouth_open <= 0.5:
            # カーブする口
            p0 = self._xy(mouth_cx - self.LAYOUT["mouth_width"] / 2, mouth_cy)
            p2 = self._xy(mouth_cx + self.LAYOUT["mouth_width"] / 2, mouth_cy)
            p1 = self._xy(mouth_cx, mouth_cy + st.mouth_curve)

            self._draw_bezier_curve(
                draw,
                p0,
                p1,
                p2,
                color=self.COLORS["mouth_line"],
                width=self._w(5),
            )

    def _draw_eyes(self, draw):
        eye_y = self.LAYOUT["eye_y"]
        eye_offset = self.LAYOUT["eye_offset"]
        self._draw_eye(
            draw,
            eye_offset,
            eye_y,
            self.current_state.left_eye,
            self.current_state.brow_tilt,
            self.current_gaze_x,
        )
        self._draw_eye(
            draw,
            100 - eye_offset,
            eye_y,
            self.current_state.right_eye,
            self.current_state.brow_tilt,
            self.current_gaze_x,
        )

    def draw(self, screen_width: int, screen_height: int, bg_color: tuple):
        # 画像生成
        # 正方形キャンバスを作成してからパディングする
        img = Image.new("RGB", (self.size, self.size), bg_color)
        draw = ImageDraw.Draw(img)

        self._draw_outline(draw)
        self._draw_eyes(draw)
        # 眉毛は目の上に描画されるべきなので、ここで呼び出す
        eye_y = self.LAYOUT["eye_y"]
        eye_offset = self.LAYOUT["eye_offset"]
        left_eye_cx = eye_offset  # 視線に追従しない眉毛のX座標
        right_eye_cx = 100 - eye_offset
        self._draw_brows(
            draw,
            left_eye_cx,
            right_eye_cx,
            eye_y,
            self.current_state.brow_tilt,
        )
        self._draw_mouth(draw)

        # パディングして画面サイズに合わせる (中央寄せなど)
        final_img = ImageOps.pad(
            img,
            (screen_width, screen_height),
            color=bg_color,
            centering=(0.1, 0.5),
        )
        return final_img


class RobotFaceApp:
    """Robot face App class."""

    GAZE_WIDTH = 5

    def __init__(
        self,
        init_mood: str,
        output: DisplayOutput,
        screen_width: int,
        screen_height: int,
        bg_color: str,
        debug=False,
    ):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("init_mood=%a", init_mood)

        self.mood = init_mood
        self.output = output
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bg_color = bg_color
        self.bg_color_tuple = ImageColor.getrgb(bg_color)

        # アニメーションタイミング管理
        now = time.time()
        self._next_mood_time: float = now + 5.0
        self._next_gaze_time: float = now + 5.0

        try:
            face_size = min(self.screen_width, self.screen_height)
            self.face = RobotFace(
                self.mood, size=face_size, debug=self.__debug
            )
        except Exception as e:
            self.__log.error(errmsg(e))
            raise e

    def main(self):
        """Main."""

        if not self.mood:
            self.mood = "neutral"
            self.__log.info("mood=%a", self.mood)

        while True:
            now = time.time()

            # 表情変更
            if now > self._next_mood_time:
                new_mood = random.choice(list(self.face.MOODS.keys()))
                print(f"mood: {new_mood}")
                self.face.set_target_mood(new_mood)
                self._next_mood_time = now + random.uniform(3.0, 5.0)

            # 視線変更
            if now > self._next_gaze_time:
                gaze = random.uniform(-self.GAZE_WIDTH, self.GAZE_WIDTH)
                self.face.set_gaze(gaze)
                self._next_gaze_time = now + random.uniform(0.5, 2.0)

            # 更新と描画
            self.face.update(speed=0.5)
            img = self.face.draw(
                self.screen_width, self.screen_height, self.bg_color_tuple
            )
            self.output.show(img)

            time.sleep(0.1)

    def end(self):
        """End."""
        self.output.close()


@click.command(__file__.split("/")[-1])  # file name
@click.argument("mood", type=str, default="")
@click_common_opts(__version__)
def main(ctx, mood, debug):
    """Main."""
    __log = get_logger(__name__, debug)
    __log.info("mood=%a", mood)

    app = None
    try:
        if not mood:
            mood = "neutral"

        output_device = create_output_device(debug=debug)
        app = RobotFaceApp(
            mood,
            output_device,
            320,  # SCREEN_WIDTH
            240,  # SCREEN_HEIGHT
            "black",  # BG_COLOR
            debug=debug,
        )
        app.main()
    except KeyboardInterrupt:
        print("\nEnd.")
    except Exception as e:
        __log.error(errmsg(e))
    finally:
        if app:
            app.end()


if __name__ == "__main__":
    main()
