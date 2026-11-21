"""Paint the opening gauge glances on the original expression UV space."""
from pathlib import Path

from PIL import Image, ImageDraw

ART = Path(__file__).with_name("art")
INK = "#09090d"


def paint_glance(index, pupil_x, pupil_y, focus):
    image = Image.new("RGBA", (1024, 1024), (4, 4, 7, 0))
    draw = ImageDraw.Draw(image)

    def oval(x0, y0, x1, y1, color):
        draw.ellipse(tuple(round(4 * value) for value in (x0, y0, x1, y1)), fill=color)

    def mark(path, width):
        draw.line([(round(4 * x), round(4 * y)) for x, y in path], fill=INK,
                  width=4 * width, joint="curve")
        for x, y in (path[0], path[-1]):
            radius = width / 2
            oval(x - radius, y - radius, x + radius, y + radius, INK)

    for side in (-1, 1):
        x = 128 + side * 50
        top = 87 + 6 * focus
        oval(x - 26, top, x + 26, 144, INK)
        oval(x - 21, top + 5, x + 21, 139, "#fffaf4")
        oval(x + pupil_x - 7, 104 + pupil_y, x + pupil_x + 7, 122 + pupil_y, INK)
        mark([(x + side * 22, 74 - 7 * focus), (x + side * 5, 68 + 3 * focus),
              (x - side * 20, 74 + 8 * focus)], 8)
    mark([(105, 172), (125, 169 + 4 * focus), (150, 171 + 6 * focus)], 7)
    image.save(ART / f"dial_glance_{index}.png")


for index, pose in enumerate(((6, 0, 0), (9, 1, .12), (12, 2, .25), (12, 6, .72), (13, 10, 1))):
    paint_glance(index, *pose)
