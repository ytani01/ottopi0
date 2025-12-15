import random
import sys
import time

# Check for Pillow
try:
    from PIL import Image, ImageDraw, ImageOps
except ImportError:
    print(
        "Error: PIL (Pillow) not found. Install it with: pip install pillow"
    )
    sys.exit(1)

# Check for ST7789 (Pimoroni library)
try:
    from pi0disp import ST7789V

    HAS_DISPLAY = True
except ImportError:
    print("Warning: ST7789V library not found. Running in preview mode.")
    HAS_DISPLAY = False

# --- Configuration ---
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240


def init_display():
    """Initializes the ST7789 display driver."""
    if not HAS_DISPLAY:
        return None

    print("Initializing ST7789 Display...")
    disp = ST7789V(rotation=90)
    return disp


def draw_bezier(draw, p0, p1, p2, fill, width):
    """
    Draws a Quadratic Bezier curve using linear interpolation steps.
    Pillow does not have native Bezier support.
    B(t) = (1-t)^2 * P0 + 2(1-t)t * P1 + t^2 * P2
    """
    points = []
    steps = 5
    for i in range(steps + 1):
        t = i / steps
        x = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
        y = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
        points.append((x, y))

    draw.line(points, fill=fill, width=width, joint="curve")


def create_robot_face(mood, size=240, bg_color="white", line_color="black"):
    """
    Generates a PIL Image of the robot face based on the mood.
    Logic mimics the SVG paths in the React web app.
    """
    # Create canvas
    img = Image.new("RGB", (size, size), bg_color)
    draw = ImageDraw.Draw(img)

    # Scale factor (Reference SVG is 100x100)
    s = size / 100.0

    # Helper for scaling coordinates
    def c(x, y):
        return (x * s, y * s)

    # Helper for scaling width (min 1px)
    def w(width):
        return max(1, int(width * s))

    # # --- Antenna ---
    # draw.line([c(50, 20), c(50, 10)], fill=line_color, width=w(4))

    # r_ant = 4 * s
    # cx_a, cy_a = c(50, 8)
    # draw.ellipse(
    #     [cx_a - r_ant, cy_a - r_ant, cx_a + r_ant, cy_a + r_ant],
    #     fill=line_color,
    # )

    # --- Head Box ---
    # PIL rounded rectangle expects [x0, y0, x1, y1]
    # SVG Reference: x=15, y=20, w=70, h=60
    box = [c(5, 10)[0], c(5, 10)[1], c(95, 90)[0], c(95, 90)[1]]
    draw.rounded_rectangle(box, radius=12 * s, outline=line_color, width=w(5))

    # --- Eyes Helpers ---
    eye_y = 45
    eye_radius = 6 * s

    def draw_eye(cx_base, cy_base):
        cx, cy = c(cx_base, cy_base)
        draw.ellipse(
            [
                cx - eye_radius,
                cy - eye_radius,
                cx + eye_radius,
                cy + eye_radius,
            ],
            fill=line_color,
        )

    # --- Mood Logic: Eyes ---
    if mood == "angry":
        # Left
        draw_eye(35, eye_y)
        draw.line([c(25, 35), c(45, 45)], fill=line_color, width=w(5))
        # Right
        draw_eye(65, eye_y)
        draw.line([c(55, 45), c(75, 35)], fill=line_color, width=w(5))

    elif mood == "wink":
        # Left (Open)
        draw_eye(35, eye_y)
        # Right (Wink >)
        # polyline 57,42 65,50 73,42
        # points = [c(57, 42), c(65, 50), c(73, 42)]
        # draw.line(points, fill=line_color, width=w(5), joint="curve")
        draw_bezier(
            draw, c(57, 42), c(65, 50), c(73, 42), line_color, width=w(5)
        )

    else:
        # Normal
        draw_eye(35, eye_y)
        draw_eye(65, eye_y)

    # --- Mood Logic: Mouth ---
    if mood in ["happy", "wink"]:
        # Smile: M 35 65 Q 50 80 65 65
        draw_bezier(draw, c(35, 65), c(50, 80), c(65, 65), line_color, w(5))

    elif mood in ["angry", "sad"]:
        # Frown: M 35 75 Q 50 60 65 75
        draw_bezier(draw, c(35, 75), c(50, 60), c(65, 75), line_color, w(5))

    elif mood == "surprised":
        # O mouth
        r_mouth = 6 * s
        cx_m, cy_m = c(50, 70)
        draw.ellipse(
            [cx_m - r_mouth, cy_m - r_mouth, cx_m + r_mouth, cy_m + r_mouth],
            outline=line_color,
            width=w(5),
        )

    else:  # Neutral
        draw.line([c(35, 70), c(65, 70)], fill=line_color, width=w(5))

    return img


def main():
    disp = init_display()

    # List of moods to cycle through
    moods = ["happy", "neutral", "wink", "surprised", "sad", "angry"]
    print(f"Starting Robot Face Loop... (Modes: {moods})")
    print("Press Ctrl+C to exit")

    try:
        while True:
            # Pick a random mood
            mood = random.choice(moods)
            print(f"Displaying: {mood}")

            # Generate Image (matching screen resolution)
            img = create_robot_face(mood, size=SCREEN_HEIGHT)
            img = ImageOps.pad(
                img,
                (SCREEN_WIDTH, SCREEN_HEIGHT),
                color=(128, 128, 128),
                centering=(0.5, 0.5),
            )

            if disp:
                # Send to ST7789
                disp.display(img)
            else:
                # Debug mode for PC
                img.show()
                # Sleep longer in debug so we don't spam windows
                time.sleep(2)

            time.sleep(3)

    except KeyboardInterrupt:
        print("\nExiting...")

    finally:
        disp.close()


if __name__ == "__main__":
    main()
