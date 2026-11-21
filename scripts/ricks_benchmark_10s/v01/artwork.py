"""Draw original marker decals as supersampled, transparent RGBA artwork."""
from pathlib import Path
from PIL import Image, ImageDraw

OUT = Path(__file__).with_name("art")
INK = "#0A0A0E"
WHITE = "#FFF6DC"
NAMES = ("suspicious", "excited_awe", "smug_focus", "sneaky", "shock_terror",
         "broker_neutral", "broker_creepy_grin", "jacket")


class Canvas:
    def __init__(self):
        self.image = Image.new("RGBA", (2048, 2048), (10, 10, 14, 0))
        self.pen = ImageDraw.Draw(self.image)

    @staticmethod
    def px(point):
        return tuple(round(value * 8) for value in point)

    def oval(self, box, color=INK):
        self.pen.ellipse(self.px(box), fill=color)

    def polygon(self, points, color=INK):
        self.pen.polygon([self.px(p) for p in points], fill=color)

    def line(self, points, width=5, color=INK):
        points = [self.px(p) for p in points]
        self.pen.line(points, fill=color, width=round(width * 8), joint="curve")
        radius = width * 4
        for x, y in (points[0], points[-1]):
            self.pen.ellipse((x-radius, y-radius, x+radius, y+radius), fill=color)

    def curve(self, control, width=5, color=INK):
        points = []
        for i in range(31):
            t = i / 30
            u = 1 - t
            weights = (u**3, 3*u*u*t, 3*u*t*t, t**3)
            points.append(tuple(sum(w*p[axis] for w, p in zip(weights, control))
                                for axis in range(2)))
        self.line(points, width, color)

    def save(self, name):
        image = self.image.resize((1024, 1024), Image.Resampling.LANCZOS)
        # Keep dark RGB in fully transparent texels for hardware filtering.
        blank = Image.new("RGBA", image.size, (10, 10, 14, 0))
        blank.paste(image, mask=image.getchannel("A").point(lambda a: 255 if a else 0))
        blank.save(OUT / f"{name}.png")


def hero(name):
    c = Canvas()
    if name in {"excited_awe", "shock_terror"}:
        for x in (74, 181):
            c.oval((x-30, 77, x+30, 149))
            c.oval((x-24, 82, x+24, 143), WHITE)
            r = 7 if name == "excited_awe" else 4
            c.oval((x-r, 110-r, x+r, 110+r))
            top = 52 if name == "excited_awe" else (42 if x < 100 else 64)
            c.curve(((x-20, 64), (x-9, top), (x+6, top), (x+20, 64)), 6)
        if name == "excited_awe":
            c.oval((76, 160, 181, 223))
            c.polygon([(84, 177), (171, 175), (160, 187), (96, 189)], WHITE)
            c.oval((110, 202, 155, 216), "#DF726D")
        else:
            c.curve(((83, 190), (105, 141), (106, 209), (132, 177)), 8)
            c.curve(((132, 177), (149, 151), (158, 206), (180, 186)), 8)
            c.curve(((86, 196), (112, 217), (152, 219), (177, 192)), 6)
    else:
        look = -11 if name == "sneaky" else (5 if name == "suspicious" else -2)
        for x in (74, 180):
            c.line(((x-21, 104), (x+19, 102)), 6)
            c.oval((x+look-9, 103, x+look+9, 132))
            left = x < 100
            a, b = ((76, 90) if left else (92, 75))
            if name == "sneaky":
                a, b = ((84, 68) if left else (85, 96))
            c.line(((x-20, a), (x+21, b)), 8)
        endpoint = (167, 163) if name != "suspicious" else (162, 173)
        c.curve(((96, 178), (116, 190), (150, 185), endpoint), 7)
    c.save(name)


def broker(name):
    c = Canvas()
    for x in (77, 179):
        c.oval((x-15, 95, x+15, 118), "#1B111E")
        c.oval((x-11, 98, x+11, 115), "#FFF0B1")
    if name == "broker_neutral":
        c.line(((105, 184), (151, 184)), 6)
    else:
        xs = list(range(52, 206, 3))
        c.polygon([(x, 168+16*(1-((x-128)/77)**2)) for x in xs] +
                  [(x, 171+56*(1-((x-128)/77)**2)) for x in reversed(xs)])
        xs = list(range(63, 195, 3))
        c.polygon([(x, 172+16*(1-((x-128)/66)**2)) for x in xs] +
                  [(x, 174+41*(1-((x-128)/66)**2)) for x in reversed(xs)], WHITE)
        for x in (93, 120, 148, 171):
            c.line(((x, 200), (x+2, 208)), 1.6, "#7A5762")
    c.save(name)


def jacket():
    c = Canvas()
    c.polygon([(63, 5), (196, 5), (155, 84), (108, 166), (91, 61)], "#222942")
    c.line(((66, 31), (118, 120), (145, 120), (184, 24)), 7, "#BF4230")
    c.line(((66, 31), (118, 120), (145, 120), (184, 24)), 2, "#FF7355")
    c.line(((131, 120), (132, 144)), 6, "#C64030")
    c.polygon([(106, 141), (160, 141), (160, 186), (106, 186)], "#3B2F32")
    c.polygon([(111, 145), (155, 145), (155, 181), (111, 181)], "#F6EBDD")
    c.oval((117, 154, 132, 168), "#58868D")
    c.line(((138, 157), (150, 157)), 3, "#74675D")
    c.line(((138, 165), (147, 165)), 2, "#74675D")
    c.line(((48, 179), (83, 181)), 4, "#765420")
    c.line(((50, 175), (81, 177)), 2, "#F8D070")
    c.line(((176, 197), (207, 190)), 4, "#765420")
    c.save("jacket")


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    for expression in NAMES[:5]:
        hero(expression)
    for expression in NAMES[5:7]:
        broker(expression)
    jacket()
