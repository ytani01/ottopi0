import math
import random
import socket
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import click
from PIL import Image, ImageDraw, ImageOps

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
    curve: float = (
        0.0  # 閉じたときの目の曲がり具合 (-1.0: 谷, 0.0: 直線, 1.0: 山)
    )

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
        "nikoniko": FaceState(
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

        # アニメーションタイミング管理
        now = time.time()
        self._next_mood_time: float = now + 5.0
        self._next_gaze_time: float = now + 5.0

        # 視線状態管理
        self.current_gaze_x: float = 0.0
        self.target_gaze_x: float = 0.0

    def animate_step(self):
        """アニメーションのステップを実行する"""
        now = time.time()

        # 表情変更
        if now > self._next_mood_time:
            new_mood = random.choice(list(self.MOODS.keys()))
            print(f"表情: {new_mood}")
            self.set_target_mood(new_mood)
            self._next_mood_time = now + random.uniform(3.0, 5.0)

        # 視線変更
        if now > self._next_gaze_time:
            gaze = random.uniform(-10, 10)
            self.set_gaze(gaze)
            self._next_gaze_time = now + random.uniform(0.5, 2.0)

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

    def _xy(self, x, y, screen_height):
        sx = screen_height / 100.0
        sy = screen_height / 100.0
        return (x * sx, y * sy)

    def _w(self, width):
        return max(1, int(width * self.scale))

    def _draw_eye(
        self,
        draw,
        cx,
        eye_y,
        eye_state: EyeState,
        tilt,
        gaze_offset,
        screen_height,
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
                p0 = self._xy(real_cx - 8, eye_y + 2, screen_height)
                p1 = self._xy(
                    real_cx, eye_y - 8 * eye_state.curve, screen_height
                )
                p2 = self._xy(real_cx + 8, eye_y + 2, screen_height)

                points = []
                steps = 10
                for i in range(steps + 1):
                    t = i / steps
                    bx = (
                        (1 - t) ** 2 * p0[0]
                        + 2 * (1 - t) * t * p1[0]
                        + t**2 * p2[0]
                    )
                    by = (
                        (1 - t) ** 2 * p0[1]
                        + 2 * (1 - t) * t * p1[1]
                        + t**2 * p2[1]
                    )
                    points.append((bx, by))

                draw.line(
                    points,
                    fill=self.LINE_COLOR,
                    width=self._w(4),
                    joint="curve",
                )
            else:
                # 直線
                draw.line(
                    [
                        self._xy(real_cx - 7, eye_y, screen_height),
                        self._xy(real_cx + 7, eye_y, screen_height),
                    ],
                    fill=self.LINE_COLOR,
                    width=self._w(4),
                )
        else:
            # 開いている場合: 楕円
            bbox = [
                self._xy(real_cx, eye_y, screen_height)[0] - r,
                self._xy(real_cx, eye_y, screen_height)[1] - ry,
                self._xy(real_cx, eye_y, screen_height)[0] + r,
                self._xy(real_cx, eye_y, screen_height)[1] + ry,
            ]
            draw.ellipse(
                bbox, outline=(0, 0, 192), fill="white", width=self._w(10)
            )

        # 眉毛
        if abs(tilt) > 1:
            brow_y = eye_y - 12
            offset_y = math.tan(math.radians(tilt)) * 10
            # 左目(cx<50)と右目で傾きの符号を変える簡易ロジック
            # 実際には引数でleft/rightフラグをもらう方が綺麗だが、ここでは座標判定
            if cx < 50:
                p1 = self._xy(real_cx - 9, brow_y - offset_y, screen_height)
                p2 = self._xy(real_cx + 9, brow_y + offset_y, screen_height)
            else:
                p1 = self._xy(real_cx - 9, brow_y + offset_y, screen_height)
                p2 = self._xy(real_cx + 9, brow_y - offset_y, screen_height)
            draw.line([p1, p2], fill=(128, 64, 64), width=self._w(5))

    def draw(self, screen_width: int, screen_height: int, bg_color: str):
        # 画像生成
        # 正方形キャンバスを作成してからパディングする
        img = Image.new("RGB", (screen_height, screen_height), bg_color)
        draw = ImageDraw.Draw(img)

        # 輪郭
        box = [
            self._xy(0, 0, screen_height)[0],
            self._xy(0, 0, screen_height)[1],
            self._xy(100, 100, screen_height)[0],
            self._xy(100, 100, screen_height)[1],
        ]
        draw.rounded_rectangle(
            box,
            radius=20 * self.scale,
            outline="black",
            fill=self.FACE_BG_COLOR,  # ここを修正
            width=1,
        )

        # 目
        eye_y = 45
        eye_offset = 32
        self._draw_eye(
            draw,
            eye_offset,
            eye_y,
            self.current_state.left_eye,
            self.current_state.brow_tilt,
            self.current_gaze_x,
            screen_height,
        )
        self._draw_eye(
            draw,
            100 - eye_offset,
            eye_y,
            self.current_state.right_eye,
            self.current_state.brow_tilt,
            self.current_gaze_x,
            screen_height,
        )

        # 口
        mouth_cx, mouth_cy = 50, 70
        mouth_line_color = (255, 32, 0)
        st = self.current_state

        if st.mouth_open > 0.5:
            # 丸い口 (驚きなど)
            factor = (st.mouth_open - 0.5) * 2
            r = 8 * self.scale * factor
            if r > 1:
                cx, cy = self._xy(mouth_cx, mouth_cy, screen_height)
                draw.ellipse(
                    [cx - r, cy - r * 1.2, cx + r, cy + r * 1.2],
                    outline=mouth_line_color,
                    fill=(128, 0, 0),
                    width=self._w(4),
                )
        if st.mouth_open <= 0.5:
            # カーブする口
            p0 = self._xy(35, mouth_cy, screen_height)
            p2 = self._xy(65, mouth_cy, screen_height)
            p1 = self._xy(50, mouth_cy + st.mouth_curve, screen_height)

            points = []
            steps = 15
            for i in range(steps + 1):
                t = i / steps
                bx = (
                    (1 - t) ** 2 * p0[0]
                    + 2 * (1 - t) * t * p1[0]
                    + t**2 * p2[0]
                )
                by = (
                    (1 - t) ** 2 * p0[1]
                    + 2 * (1 - t) * t * p1[1]
                    + t**2 * p2[1]
                )
                points.append((bx, by))

            draw.line(
                points, fill=mouth_line_color, width=self._w(5), joint="curve"
            )

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

    def __init__(
        self,
        mood: str,
        output: DisplayOutput,
        screen_width: int,
        screen_height: int,
        bg_color: str,
        debug=False,
    ):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("mood=%a", mood)

        self.mood = mood
        self.output = output
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bg_color = bg_color

        try:
            self.face = RobotFace(self.mood, debug=self.__debug)
        except Exception as e:
            self.__log.error(errmsg(e))
            raise e

    def main(self):
        """Main."""

        if not self.mood:
            self.mood = "neutral"
            self.__log.info("mood=%a", self.mood)

        while True:
            self.face.animate_step()

            # 更新と描画
            self.face.update(speed=0.5)
            img = self.face.draw(
                self.screen_width, self.screen_height, self.bg_color
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
