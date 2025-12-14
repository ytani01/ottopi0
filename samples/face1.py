#
# (c) 2025 Yoichi Tanibayashi
#
from pi0disp import ST7789V
from PIL import Image, ImageDraw


def face(lcd, draw, color):
    """face."""
    x1, y1 = 0, 0
    x2, y2 = lcd.width - 1, lcd.height - 1
    draw.rounded_rectangle(
        [(x1, y1), (x2, y2)], radius=80, fill=color, outline="black", width=10
    )


def eyes1(lcd, draw, r, y, d, color):
    """Eyes."""
    x00, y00 = lcd.width / 2, y

    x0, y0 = x00 - d / 2, y00
    x1, y1 = x0 - r / 2, y0 - r / 2
    x2, y2 = x0 + r / 2, y0 + r / 2
    draw.ellipse([(x1, y1), (x2, y2)], fill=color, width=10)

    x0, y0 = x00 + d / 2, y00
    x1, y1 = x0 - r / 2, y0 - r / 2
    x2, y2 = x0 + r / 2, y0 + r / 2
    draw.ellipse([(x1, y1), (x2, y2)], fill=color, width=10)


def mouth1(lcd, draw, color):
    """Mouse1"""
    w = 150
    x1, y1 = lcd.width / 2 - w / 2, 110
    x2, y2 = lcd.width / 2 + w / 2, 190
    a = 15
    # draw.ellipse([(x1, y1), (x2, y2)], outline="black")
    draw.arc([(x1, y1), (x2, y2)], start=a, end=180 - a, fill=color, width=10)


def main():
    """Main."""

    with ST7789V(rotation=90) as lcd:
        image1 = Image.new("RGB", (lcd.width, lcd.height), (0, 0, 0))
        draw1 = ImageDraw.Draw(image1)

        face(lcd, draw1, (128, 192, 192))
        eyes1(lcd, draw1, r=50, y=90, d=120, color=(0, 32, 192))
        mouth1(lcd, draw1, (255, 32, 0))

        lcd.display(image1)

        lcd.display(image1)


if __name__ == "__main__":
    main()
