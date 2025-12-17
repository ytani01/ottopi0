import math
import random
import socket
import time
from dataclasses import dataclass

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
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
BG_COLOR = "black"
LINE_COLOR = "black"
FACE_BG_COLOR = (255, 255, 220)


# --- 状態クラス ---
@dataclass
class FaceState:
    mouth_curve: float = 0  # 口の曲がり具合: +20(笑顔) ～ -20(への字)
    eye_height: float = 6  # 目の縦半径
    eye_tilt: float = 0  # 眉毛の角度
    wink_left: float = 1.0  # 左目の開き具合: 1.0(開) ～ 0.1(閉)
    wink_right: float = 1.0  # 右目の開き具合
    mouth_open: float = 0  # 口の開き具合: 0(線) ～ 1(丸)
    gaze_x: float = 0  # 視線の水平位置: 0(正面), +20(右), -20(左)
    eye_curve: float = 0  # 目の曲がり具合: +1(山なり) ～ -1(谷なり)

    def copy(self):
        return FaceState(
            self.mouth_curve,
            self.eye_height,
            self.eye_tilt,
            self.wink_left,
            self.wink_right,
            self.mouth_open,
            self.gaze_x,
            self.eye_curve,
        )


# --- 表情定義 ---


# --- ヘルパー関数 ---
def lerp(a, b, t):
    """線形補間"""
    return a + (b - a) * t


# --- クラス定義 ---


class DisplayOutput:
    """ディスプレイ出力を抽象化するクラス"""

    MODE_NONE = 0
    MODE_LCD = 1
    MODE_PREVIEW = 2

    def __init__(self, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

        self.mode = self.MODE_NONE
        self.lcd = None
        self._detect_hardware()
        self.__log.debug("mode=%s", self.mode)

    def _check_pigpio(self, host="localhost", port=8888, timeout=0.1):
        """pigpioデーモンの存在確認"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def _detect_hardware(self):
        """Detect hardware."""

        # 1. ハードウェア (ST7789) の確認
        if HAS_LCD:
            if self._check_pigpio():
                try:
                    self.lcd = ST7789V(rotation=270)
                    self.mode = self.MODE_LCD
                    return
                except Exception as e:
                    self.__log.warning(errmsg(e))
            else:
                self.__log.warning("no pigpiod")

        # 2. OpenCVプレビュー
        if HAS_OPENCV:
            self.mode = self.MODE_PREVIEW
            return

        # 3. なし
        self.__log.warning(
            "警告: 表示可能なデバイスがありません (コンソール実行のみ)"
        )

    def show(self, pil_image):
        """画像をデバイスに転送"""
        if self.mode == self.MODE_LCD and self.lcd:
            self.lcd.display(pil_image)

        elif self.mode == self.MODE_PREVIEW:
            # PIL -> OpenCV (BGR)
            frame = np.array(pil_image)
            frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
            cv2.imshow("Robot Face", frame)
            key = cv2.waitKey(1) & 0xFF
            if key == 27:  # ESC
                raise KeyboardInterrupt("ESC pressed")

    def close(self):
        """リソース解放"""
        if self.mode == self.MODE_LCD and self.lcd:
            self.lcd.close(True)
        elif self.mode == self.MODE_PREVIEW:
            cv2.destroyAllWindows()


class RobotFace:
    """顔の状態管理と描画を担当するクラス"""

    MOODS = {
        "neutral": FaceState(
            eye_height=9,
            eye_tilt=0,
            eye_curve=0,
            mouth_curve=0,
        ),
        "happy": FaceState(
            eye_height=8,
            eye_tilt=0,
            eye_curve=1,
            mouth_curve=15,
        ),
        "sad": FaceState(
            eye_height=7,
            eye_tilt=-10,
            eye_curve=-1,
            mouth_curve=-15,
        ),
        "angry": FaceState(
            eye_height=6,
            eye_tilt=25,
            eye_curve=0,
            mouth_curve=-10,
        ),
        "winkr": FaceState(
            mouth_curve=15,
            eye_height=8,
            eye_tilt=0,
            wink_right=0.1,
            eye_curve=1,
        ),
        "winkl": FaceState(
            eye_height=8,
            eye_tilt=0,
            wink_left=0.1,
            eye_curve=1,
            mouth_curve=15,
        ),
        "surprised": FaceState(
            eye_height=12,
            eye_tilt=0,
            eye_curve=0,
            mouth_open=1.0,
            mouth_curve=0,
        ),
        "sleepy": FaceState(
            eye_height=8,
            eye_tilt=0,
            wink_left=0.1,
            wink_right=0.1,
            eye_curve=-1,
            mouth_curve=0,
        ),
        "smily": FaceState(
            eye_height=7,
            eye_tilt=0,
            eye_curve=1,
            wink_left=0.1,
            wink_right=0.1,
            mouth_curve=20,
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
        # 画面サイズに対するスケーリング (320x240画面向け調整)
        self.sx = SCREEN_HEIGHT / 100.0
        self.sy = SCREEN_HEIGHT / 100.0

    def update(self, speed=0.5):
        """状態をターゲットに近づける"""
        c, t = self.current_state, self.target_state
        c.mouth_curve = lerp(c.mouth_curve, t.mouth_curve, speed)
        c.eye_height = lerp(c.eye_height, t.eye_height, speed)
        c.eye_tilt = lerp(c.eye_tilt, t.eye_tilt, speed)
        c.wink_left = lerp(c.wink_left, t.wink_left, speed)
        c.wink_right = lerp(c.wink_right, t.wink_right, speed)
        c.mouth_open = lerp(c.mouth_open, t.mouth_open, speed)
        c.gaze_x = lerp(c.gaze_x, t.gaze_x, speed)
        c.eye_curve = lerp(c.eye_curve, t.eye_curve, speed)

    def set_mood(self, mood_name):
        """表情セット"""
        if mood_name in self.MOODS:
            # 視線(gaze_x)は表情定義に依存せず維持したいが
            # 今回はリファクタ前の挙動に合わせて、表情を変えたら
            # 表情定義の視線値(通常0)をターゲットにする。
            # ただしメインループ側で直後にgazeを上書きする運用も可。
            # ここではシンプルにMood定義をコピーする。
            current_gaze = self.target_state.gaze_x
            self.target_state = self.MOODS[mood_name].copy()
            # 視線を維持する場合はアンコメント
            self.target_state.gaze_x = current_gaze

    def set_gaze(self, x):
        """視線セット (-20 to +20)"""
        self.target_state.gaze_x = x

    def _xy(self, x, y):
        return (x * self.sx, y * self.sy)

    def _w(self, width):
        return max(1, int(width * self.scale))

    def _draw_eye(self, draw, cx, eye_y, wink_scale, tilt, gaze_offset):
        # 視線を加味した中心X
        real_cx = cx + gaze_offset

        # 目のサイズ
        r = self.current_state.eye_height * self.scale
        ry = r * wink_scale

        # 描画
        if ry < 4:
            # 目が閉じている場合
            if self.current_state.eye_curve != 0:
                # ベジェ曲線
                p0 = self._xy(real_cx - 8, eye_y + 2)
                p1 = self._xy(
                    real_cx, eye_y - 8 * self.current_state.eye_curve
                )
                p2 = self._xy(real_cx + 8, eye_y + 2)

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
                    points, fill=LINE_COLOR, width=self._w(4), joint="curve"
                )
            else:
                # 直線
                draw.line(
                    [
                        self._xy(real_cx - 7, eye_y),
                        self._xy(real_cx + 7, eye_y),
                    ],
                    fill=LINE_COLOR,
                    width=self._w(4),
                )
        else:
            # 開いている場合: 楕円
            bbox = [
                self._xy(real_cx, eye_y)[0] - r,
                self._xy(real_cx, eye_y)[1] - ry,
                self._xy(real_cx, eye_y)[0] + r,
                self._xy(real_cx, eye_y)[1] + ry,
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
                p1 = self._xy(real_cx - 9, brow_y - offset_y)
                p2 = self._xy(real_cx + 9, brow_y + offset_y)
            else:
                p1 = self._xy(real_cx - 9, brow_y + offset_y)
                p2 = self._xy(real_cx + 9, brow_y - offset_y)
            draw.line([p1, p2], fill=(128, 64, 64), width=self._w(5))

    def draw(self):
        # 画像生成
        # 正方形キャンバスを作成してからパディングする
        img = Image.new("RGB", (SCREEN_HEIGHT, SCREEN_HEIGHT), BG_COLOR)
        draw = ImageDraw.Draw(img)

        # 輪郭
        box = [
            self._xy(0, 0)[0],
            self._xy(0, 0)[1],
            self._xy(100, 100)[0],
            self._xy(100, 100)[1],
        ]
        draw.rounded_rectangle(
            box,
            radius=20 * self.scale,
            outline="black",
            fill=FACE_BG_COLOR,
            width=1,
        )

        # 目
        eye_y = 45
        eye_offset = 32
        self._draw_eye(
            draw,
            eye_offset,
            eye_y,
            self.current_state.wink_left,
            self.current_state.eye_tilt,
            self.current_state.gaze_x,
        )
        self._draw_eye(
            draw,
            100 - eye_offset,
            eye_y,
            self.current_state.wink_right,
            self.current_state.eye_tilt,
            self.current_state.gaze_x,
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
                cx, cy = self._xy(mouth_cx, mouth_cy)
                draw.ellipse(
                    [cx - r, cy - r * 1.2, cx + r, cy + r * 1.2],
                    outline=mouth_line_color,
                    fill=(128, 0, 0),
                    width=self._w(4),
                )
        if st.mouth_open <= 0.5:
            # カーブする口
            p0 = self._xy(35, mouth_cy)
            p2 = self._xy(65, mouth_cy)
            p1 = self._xy(50, mouth_cy + st.mouth_curve)

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
            (SCREEN_WIDTH, SCREEN_HEIGHT),
            color=BG_COLOR,
            centering=(0.1, 0.5),
        )
        return final_img


class RobotFaceApp:
    """Robot face App class."""

    def __init__(self, mood: str, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("mood=%a", mood)

        self.mood = mood

        try:
            self.output = DisplayOutput(debug=self.__debug)
            self.face = RobotFace(self.mood, debug=self.__debug)
        except Exception as e:
            self.__log.error(errmsg(e))
            raise e

    def main(self):
        """Main."""

        if not self.mood:
            self.mood = "neutral"
            self.__log.info("mood=%a", self.mood)

        next_mood_time = time.time() + 2.0
        next_gaze_time = time.time() + 1.0

        while True:
            now = time.time()

            # 表情変更
            if now > next_mood_time:
                self.mood = random.choice(list(RobotFace.MOODS.keys()))
                print(f"表情: {self.mood}")
                self.face.set_mood(self.mood)
                next_mood_time = now + random.uniform(3.0, 5.0)

            # 視線変更
            if now > next_gaze_time:
                gaze = random.uniform(-10, 10)
                self.face.set_gaze(gaze)
                next_gaze_time = now + random.uniform(0.5, 2.0)

            # 更新と描画
            self.face.update(speed=0.5)
            img = self.face.draw()
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
        app = RobotFaceApp(mood, debug=debug)
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
