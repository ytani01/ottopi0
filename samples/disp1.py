import time

from PIL import Image, ImageDraw

from pi0disp import ST7789V

INTERVAL = .5
with ST7789V(rotation=90) as lcd:
    image = Image.new("RGB", (lcd.width, lcd.height), 128)
    lcd.display(image)
    time.sleep(INTERVAL)

    draw = ImageDraw.Draw(image)

    W, H = 100, 150
    X, Y = 20, 20
    draw.ellipse((X, Y, X + W, Y + H), fill="blue", outline="red", width=5)
    # lcd.display(image)
    # time.sleep(INTERVAL)

    W, H = 150, 100
    X, Y = 100, 100
    draw.rectangle((X, Y, X + W, Y + H), fill="green", outline="yellow", width=10)
    # lcd.display(image)
    # time.sleep(INTERVAL)

    x1, x2, y1, y2 = 20, lcd.width - 20, lcd.height - 150, lcd.height - 20
    deg = 30
    draw.arc([(x1, y1), (x2, y2)], 10, 180 - 10, fill="pink", width=10)

    lcd.display(image)
