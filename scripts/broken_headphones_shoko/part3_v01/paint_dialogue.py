"""Paint mouth cards for the named lines without changing the approved faces."""
from pathlib import Path
import sys

from PIL import ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "v03"))
from paint import draw_face


def make_card(role, base, mode):
    image = draw_face(role, base)
    draw = ImageDraw.Draw(image)
    ink = "#161020"
    if mode == "crimson":
        for x in (82,174):
            draw.ellipse(((x-31)*4,132*4,(x+31)*4,156*4),fill=(208,63,92,166))
        return image
    draw.rectangle((332,602,692,835), fill=(22,16,32,0))
    shapes = {
        "A": (23,11), "E": (19,6), "I": (16,5), "O": (12,11), "U": (9,7),
        "M": (14,2.5), "F": (17,5), "L": (16,8), "S": (16,3.5), "W": (26,20),
    }
    x,y = shapes[mode]
    if base=="peaceful_sleep":
        x,y = .66*x,.68*y
    draw.ellipse((4*(128-x),4*(174-y),4*(128+x),4*(174+y)),fill=ink)
    if y>4:
        draw.ellipse((4*(128-x*.61),4*(174-y*.64),4*(128+x*.61),4*(174-y*.18)),fill="#fff1eb")
        if y>8:
            draw.ellipse((4*(128-x*.55),4*(174+y*.14),4*(128+x*.55),4*(174+y*.70)),fill="#d9859a")
    return image


if __name__=="__main__":
    for name,role,base,modes in (
        ("sleep","shoko","peaceful_sleep","AEIOUMFLS"),
        ("tender","boy","warm_smile","IELOUTFM"),
        ("radiant","shoko","radiant_joy","AEIOULW"),
        ("blush","shoko","deep_crimson_blush",("crimson",)),
    ):
        for mode in modes:
            if mode=="T":
                continue
            make_card(role,base,mode).save(HERE/f"{name}_{mode}.png")
