import math
import random
import socket
import sys
import time

# --- 依存ライブラリのチェック ---
# 画像描画用
try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    print(
        "エラー: PIL (Pillow) が見つかりません。インストールしてください: pip install pillow"
    )
    sys.exit(1)

# ディスプレイ制御用 (Raspberry Pi + ST7789用)
# PCでテストする場合はエラーになってもプレビューモードで動きます
try:
    from pi0disp import ST7789V

    HAS_DISPLAY = True
except ImportError:
    HAS_DISPLAY = False

# PCプレビュー用 (OpenCV)
try:
    import cv2
    import numpy as np

    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False

# 動作モード決定
# 優先順位:
# 1. SSD7789V (実機)
# 2. OpenCV (PCプレビュー)
# 3. なし (コンソールのみ)

USE_PREVIEW = False  # デフォルト値（main関数で最終決定）


# --- 設定 ---
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
BG_COLOR = "white"
LINE_COLOR = "black"

# --- アニメーションの状態管理クラス ---


class FaceState:
    def __init__(
        self,
        mouth_curve=0,
        eye_height=6,
        eye_tilt=0,
        wink_left=1.0,
        wink_right=1.0,
        mouth_open=0,
    ):
        self.mouth_curve = (
            mouth_curve  # 口の曲がり具合: +20(笑顔) ～ -20(への字)
        )
        self.eye_height = eye_height  # 目の縦半径
        self.eye_tilt = eye_tilt  # 眉毛の角度（怒り表現など）
        self.wink_left = wink_left  # 左目の開き具合: 1.0(開) ～ 0.1(閉)
        self.wink_right = wink_right  # 右目の開き具合
        self.mouth_open = mouth_open  # 口の開き具合: 0(線) ～ 1(丸)

    def copy(self):
        return FaceState(
            self.mouth_curve,
            self.eye_height,
            self.eye_tilt,
            self.wink_left,
            self.wink_right,
            self.mouth_open,
        )


# --- 表情の定義 (ターゲットとなる状態) ---
MOODS = {
    "neutral": FaceState(mouth_curve=0, eye_height=9, eye_tilt=0),
    "happy": FaceState(mouth_curve=15, eye_height=8, eye_tilt=0),
    "sad": FaceState(mouth_curve=-15, eye_height=8, eye_tilt=-10),
    "angry": FaceState(mouth_curve=-10, eye_height=6, eye_tilt=25),
    "wink": FaceState(
        mouth_curve=15, eye_height=8, eye_tilt=0, wink_right=0.1
    ),
    "surprised": FaceState(
        mouth_curve=0, eye_height=5, eye_tilt=0, mouth_open=1.0
    ),
    "sleepy": FaceState(
        mouth_curve=0, eye_height=8, eye_tilt=0, wink_left=0.1, wink_right=0.1
    ),
}

# --- 補間ロジック ---


def lerp(a, b, t):
    """線形補間: a から b へ t (0.0～1.0) の割合で近づける"""
    return a + (b - a) * t


def interpolate_state(current, target, speed=0.1):
    """現在の状態をターゲットの状態へ少し近づけた新しい状態を返す"""
    new_state = current.copy()
    new_state.mouth_curve = lerp(
        current.mouth_curve, target.mouth_curve, speed
    )
    new_state.eye_height = lerp(current.eye_height, target.eye_height, speed)
    new_state.eye_tilt = lerp(current.eye_tilt, target.eye_tilt, speed)
    new_state.wink_left = lerp(current.wink_left, target.wink_left, speed)
    new_state.wink_right = lerp(current.wink_right, target.wink_right, speed)
    new_state.mouth_open = lerp(current.mouth_open, target.mouth_open, speed)
    return new_state


def check_pigpio(host="localhost", port=8888, timeout=0.1):
    """pigpioデーモンが動いているかチェックする"""
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def init_display():
    """ディスプレイを初期化する。失敗した場合はNoneを返す"""
    if not HAS_DISPLAY:
        return None

    # pigpioデーモンの存在確認 (これをしないと pigpio.pi() で長時間ハングする)
    if not check_pigpio():
        print("警告: pigpioデーモン(port 8888)が見つかりません。")
        return None

    try:
        print("ST7789 ディスプレイを初期化中...")
        disp = ST7789V(rotation=270)
        return disp
    except Exception as e:
        print(
            f"警告: ST7789の初期化に失敗しました (これはPC環境では正常です): {e}"
        )
        return None


def draw_face(draw, state, size=240):
    # 座標計算用ヘルパー
    s = size / 100.0  # スケール係数 (100x100座標系からの変換)
    sx, sy = SCREEN_HEIGHT / 100.0, SCREEN_HEIGHT / 100.0

    def xy(x, y):
        # return (x * s, y * s)
        return (x * sx, y * sy)

    def line_w(width):
        return max(1, int(width * s))

    # 背景クリア
    # draw.rectangle([0, 0, size, size], fill="black")
    # draw.rectangle([0, 0, SCREEN_WIDTH - 1, SCREEN_HEIGHT - 1], fill="black")

    x0, y0 = 0, 0

    # 顔の輪郭（四角いボックス）
    face_color = (255, 255, 220)
    box = [
        xy(x0, y0)[0],
        xy(x0, y0)[1],
        xy(100 - x0, 100 - y0)[0],
        xy(100 - x0, 100 - y0)[1],
    ]
    draw.rounded_rectangle(
        box, radius=20 * s, outline=(0, 0, 0), fill=face_color, width=1
    )

    # --- 動的なパーツ ---

    # 目の描画関数
    eye_y = 45

    def draw_eye(cx, scale_y, tilt_angle):
        # 目の基本半径
        r = state.eye_height * s
        # まばたき・ウインクによる縦方向の潰れ
        ry = r * scale_y

        # ほぼ閉じている場合は線を描画
        if ry < 4:
            draw.line(
                [xy(cx - 7, eye_y), xy(cx + 7, eye_y)],
                fill=LINE_COLOR,
                width=line_w(4),
            )
        else:
            # 開いている場合は楕円を描画
            bbox = [
                xy(cx, eye_y)[0] - r,
                xy(cx, eye_y)[1] - ry,
                xy(cx, eye_y)[0] + r,
                xy(cx, eye_y)[1] + ry,
            ]
            draw.ellipse(
                bbox,
                outline=(0, 0, 192),
                fill=(255, 255, 255),
                width=line_w(10),
            )

        # 眉毛（tilt）の表現
        # 目の上に線を描き、角度をつけることで怒りや悲しみを表現
        if abs(tilt_angle) > 1:
            brow_y = eye_y - 12
            offset_y = math.tan(math.radians(tilt_angle)) * 10

            # 左右で傾きを反転させる
            if cx < 50:  # 左目
                # 怒り: 内側が下がる, 悲しみ: 内側が上がる
                p1 = xy(cx - 9, brow_y - offset_y)
                p2 = xy(cx + 9, brow_y + offset_y)
            else:  # 右目
                p1 = xy(cx - 9, brow_y + offset_y)
                p2 = xy(cx + 9, brow_y - offset_y)

            draw.line([p1, p2], fill=(128, 64, 64), width=line_w(5))

    # 左右の目を描画
    eye_x = 32
    draw_eye(eye_x, state.wink_left, state.eye_tilt)
    draw_eye(100 - eye_x, state.wink_right, state.eye_tilt)

    # 口の描画
    mouth_line_color = (255, 32, 0)
    mouth_cx, mouth_cy = 50, 70

    # 驚き口（丸）への遷移
    if state.mouth_open > 0.5:
        # 開き具合(0.5~1.0)に応じて円を大きくする
        open_factor = (state.mouth_open - 0.5) * 2
        r_mouth = 7 * s * open_factor
        if r_mouth > 1:
            cx_m, cy_m = xy(mouth_cx, mouth_cy)
            draw.ellipse(
                [
                    cx_m - r_mouth,
                    cy_m - r_mouth * 1.2,
                    cx_m + r_mouth,
                    cy_m + r_mouth * 1.2,
                ],
                outline=mouth_line_color,
                fill=(128, 0, 0),
                width=line_w(4),
            )

    # 通常の口（線・カーブ）への遷移
    if state.mouth_open <= 0.5:
        # ベジェ曲線で口のカーブを描く
        # P0(左端) -> P1(制御点) -> P2(右端)
        p0 = xy(35, mouth_cy)
        p2 = xy(65, mouth_cy)

        # 制御点を上下させて笑顔/への字を表現
        mid_y_offset = state.mouth_curve
        p1 = xy(50, mouth_cy + mid_y_offset)

        # 線分に分割して曲線を描画
        points = []
        steps = 15
        for i in range(steps + 1):
            t = i / steps
            # 2次ベジェ曲線 B(t) = (1-t)^2 P0 + 2(1-t)t P1 + t^2 P2
            x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
            y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
            points.append((x, y))

        draw.line(
            points, fill=mouth_line_color, width=line_w(5), joint="curve"
        )

    return


# --- メイン処理 ---


def main():
    global USE_PREVIEW

    # ディスプレイ初期化試行
    disp = init_display()

    # ディスプレイが使えない場合、OpenCVプレビューを試みる
    if disp is None:
        if HAS_OPENCV:
            USE_PREVIEW = True
            print("OpenCVによるプレビューモードで動作します。")
        else:
            print(
                "警告: ディスプレイもOpenCVも使用できません。画面出力なしで動作します。"
            )
            if not HAS_DISPLAY:
                print("  - ST7789ライブラリが見つかりません")
            if not HAS_OPENCV:
                print(
                    "  - OpenCV (cv2) が見つかりません (pip install opencv-python numpy)"
                )

    # 初期状態
    current_state = MOODS["neutral"].copy()
    target_state = MOODS["neutral"]
    next_change_time = time.time() + 2

    print("ロボットフェイス アニメーション開始...")
    print("終了するには Ctrl+C を押してください")

    try:
        while True:
            now = time.time()

            # 1. 一定時間ごとに次の表情をランダムに決定
            if now > next_change_time:
                mood_name = random.choice(list(MOODS.keys()))
                target_state = MOODS[mood_name]
                print(f"表情変更: {mood_name}")
                # 2〜4秒間その表情をキープ
                next_change_time = now + random.uniform(2.0, 4.0)

            # 2. 現在の状態をターゲットに少し近づける (イージング効果)
            # speed=0.15 は毎フレーム残りの距離の15%ずつ近づくという意味
            current_state = interpolate_state(
                current_state, target_state, speed=0.5
            )

            # 3. 描画
            # img_size = min(SCREEN_WIDTH, SCREEN_HEIGHT)
            # img = Image.new("RGB", (img_size, img_size), BG_COLOR)
            img = Image.new("RGB", (SCREEN_HEIGHT, SCREEN_HEIGHT), "black")
            draw = ImageDraw.Draw(img)
            draw_face(draw, current_state)

            img = ImageOps.pad(
                img,
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                # color=(128, 128, 128),
                color=(0, 0, 0),
                # centering=(0.5, 0.5),
                centering=(0.1, 0.5),
            )

            # 4. ディスプレイ転送 or PCプレビュー
            if HAS_DISPLAY and disp:
                disp.display(img)

            elif USE_PREVIEW:
                # PIL -> OpenCV (BGR)
                frame = np.array(img)
                frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
                cv2.imshow("Robot Face (Preview)", frame)
                # キー入力待機 (1ms)。これがないとウィンドウが更新されない
                key = cv2.waitKey(1) & 0xFF
                if key == 27:  # ESCキーで終了
                    break

            # フレームレート調整
            time.sleep(0.1)

    except KeyboardInterrupt:
        print("\n終了します...")

    finally:
        if HAS_DISPLAY and disp:
            disp.close(True)
        if USE_PREVIEW:
            cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
