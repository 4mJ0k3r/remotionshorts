"""Original flat face and costume artwork for The Last Gumball v01.

Run with system Python (Pillow). Writes 1024 px alpha PNGs to ./art.
Transparent pixels carry ink RGB so the decals never show a white halo.
Image top is the top of the face; image left is screen left in a front view.
"""
from pathlib import Path

from PIL import Image, ImageChops, ImageDraw

HERE = Path(__file__).resolve().parent
ART = HERE / "art"
S = 2048  # supersampled canvas
INK = (10, 9, 14)
WHITE = (255, 252, 246)


def canvas():
    return Image.new("RGBA", (S, S), INK + (0,))


def px(u, v):
    return u * S, v * S


def ellipse_mask(cx, cy, rx, ry):
    mask = Image.new("L", (S, S), 0)
    ImageDraw.Draw(mask).ellipse([px(cx - rx, cy - ry), px(cx + rx, cy + ry)], fill=255)
    return mask


def paste(img, color, mask):
    layer = Image.new("RGBA", (S, S), color + (255,))
    img.paste(layer, (0, 0), mask)


def eye(img, cx, cy, rx, ry, look=(0, 0), lid=0.0, pupil=.42, ring=.022, lid_tilt=0.0):
    outer = ellipse_mask(cx, cy, rx + ring, ry + ring)
    white = ellipse_mask(cx, cy, rx, ry)
    paste(img, INK, outer)
    paste(img, WHITE, white)
    # Pupil, clipped to the sclera.
    pr = rx * pupil
    px_, py_ = cx + look[0] * (rx - pr * .9), cy + look[1] * (ry - pr * 1.05) * -1
    pm = ImageChops.multiply(ellipse_mask(px_, py_, pr, pr * 1.12), white)
    paste(img, INK, pm)
    # Catch-light.
    hl = ImageChops.multiply(ellipse_mask(px_ - pr * .35, py_ - pr * .4, pr * .22, pr * .22), pm)
    paste(img, WHITE, hl)
    if lid > 0:
        top = cy - ry - ring
        edge = cy - ry + 2 * ry * lid
        lidmask = Image.new("L", (S, S), 0)
        d = ImageDraw.Draw(lidmask)
        d.polygon([px(cx - rx * 1.3, top - .05), px(cx + rx * 1.3, top - .05),
                   px(cx + rx * 1.3, edge - lid_tilt), px(cx - rx * 1.3, edge + lid_tilt)], fill=255)
        lid_fill = ImageChops.multiply(lidmask, outer)
        paste(img, (36, 30, 44), lid_fill)
        # Bold lid line.
        line = Image.new("L", (S, S), 0)
        ImageDraw.Draw(line).line([px(cx - rx * 1.08, edge + lid_tilt), px(cx + rx * 1.08, edge - lid_tilt)],
                                  fill=255, width=int(ring * S * 1.25))
        paste(img, INK, ImageChops.multiply(line, ellipse_mask(cx, cy, rx + ring * 1.1, ry + ring * 1.1)))


def brow(img, cx, cy, half, angle, thick=.032, arch=0.0):
    """Pill-bar marker brow. angle >0 raises the outer end."""
    d = ImageDraw.Draw(img)
    pts = []
    for i in range(9):
        t = i / 8 * 2 - 1
        pts.append(px(cx + t * half, cy - angle * t - arch * (1 - t * t)))
    d.line(pts, fill=INK + (255,), width=int(thick * S), joint="curve")
    for end in (pts[0], pts[-1]):
        r = thick * S / 2
        d.ellipse([end[0] - r, end[1] - r, end[0] + r, end[1] + r], fill=INK + (255,))


def mouth(img, kind):
    d = ImageDraw.Draw(img)
    w = int(.028 * S)
    def stroke(points, width=w):
        pts = [px(*p) for p in points]
        d.line(pts, fill=INK + (255,), width=width, joint="curve")
        for e in (pts[0], pts[-1]):
            r = width / 2
            d.ellipse([e[0] - r, e[1] - r, e[0] + r, e[1] + r], fill=INK + (255,))
    if kind == "flat":
        stroke([(.40, .735), (.50, .738), (.61, .732)])
    elif kind == "flat_long":
        stroke([(.37, .728), (.50, .733), (.62, .735), (.64, .731)])
    elif kind == "small_o":
        paste(img, INK, ellipse_mask(.52, .735, .045, .05))
        paste(img, (120, 40, 52), ellipse_mask(.52, .745, .022, .022))
    elif kind == "smirk":
        stroke([(.40, .725), (.49, .745), (.58, .735), (.64, .705)])
    elif kind == "smile":
        stroke([(.39, .715), (.45, .748), (.53, .758), (.61, .742), (.65, .712)])
    elif kind == "gasp":
        paste(img, INK, ellipse_mask(.51, .755, .10, .115))
        paste(img, (128, 38, 52), ellipse_mask(.51, .80, .062, .045))
        paste(img, WHITE, ellipse_mask(.51, .668, .065, .018))
    elif kind == "open_o":
        paste(img, INK, ellipse_mask(.51, .755, .065, .08))
        paste(img, (128, 38, 52), ellipse_mask(.51, .785, .038, .03))


L, R = .30, .70  # eye centres (u)
EY = .40


def face(name, *, look, lid=0.0, scale=1.0, pupil=.42, brows, mouth_kind, lid_tilt=0.0):
    img = canvas()
    rx, ry = .105 * scale, .125 * scale
    for i, cx in enumerate((L, R)):
        # The head is slightly asymmetric; the art carries a matching hint.
        k = 1.0 if i == 0 else 1.04
        eye(img, cx, EY, rx * k, ry * k, look, lid, pupil, lid_tilt=lid_tilt * (1 if i else -1))
    for cx, side in ((L, -1), (R, 1)):
        height, angle, arch = brows
        brow(img, cx, height, .085, angle * side, arch=arch)
    mouth(img, mouth_kind)
    img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    # Re-ink transparent RGB after resampling to avoid halos.
    r, g, b, a = img.split()
    bg = Image.new("RGBA", img.size, INK + (0,))
    bg.paste(img, (0, 0), a)
    out = Image.merge("RGBA", (*bg.split()[:3], a))
    out.save(ART / f"{name}.png")


def costume():
    """Commuter coat front: lapels, ochre knit, buttons, crossbody strap."""
    img = Image.new("RGBA", (S, S), (24, 26, 40, 0))
    d = ImageDraw.Draw(img)
    knit = (222, 170, 70, 255)
    collar = (232, 226, 210, 255)
    lapel = (44, 52, 82, 255)
    ink = INK + (255,)
    # Ochre knit V under the open coat.
    d.polygon([px(.33, .02), px(.67, .02), px(.56, .50), px(.44, .50)], fill=knit)
    for i in range(6):
        y = .07 + i * .07
        d.line([px(.40 + i * .01, y), px(.60 - i * .01, y)], fill=(190, 136, 48, 255), width=10)
    # Shirt collar points.
    d.polygon([px(.38, .02), px(.50, .14), px(.43, .20)], fill=collar)
    d.polygon([px(.62, .02), px(.50, .14), px(.57, .20)], fill=collar)
    # Lapels with ink edges.
    for sign in (-1, 1):
        pts = [px(.5 + sign * .17, .0), px(.5 + sign * .06, .48), px(.5 + sign * .26, .26), px(.5 + sign * .30, .0)]
        d.polygon(pts, fill=lapel, outline=ink)
        d.line(pts + [pts[0]], fill=ink, width=18, joint="curve")
    # Placket line and buttons.
    d.line([px(.53, .50), px(.53, 1.0)], fill=ink, width=16)
    for y in (.60, .75, .90):
        d.ellipse([px(.49, y - .025), px(.54, y + .025)], fill=(196, 174, 120, 255), outline=ink, width=8)
    # Pockets.
    for x in (.18, .70):
        d.line([px(x, .78), px(x + .14, .76)], fill=ink, width=14)
    # Crossbody bag strap, shoulder to hip.
    d.line([px(.86, .0), px(.12, .98)], fill=(88, 60, 44, 255), width=64)
    d.line([px(.86, .0), px(.12, .98)], fill=(122, 86, 60, 255), width=36)
    d.ellipse([px(.60, .32), px(.67, .39)], fill=(214, 186, 110, 255), outline=ink, width=8)
    img = img.resize((1024, 1024), Image.Resampling.LANCZOS)
    img.save(ART / "commuter_coat.png")


def main():
    ART.mkdir(exist_ok=True)
    # (brow height v, outer-end raise, arch)
    face("bored", look=(-.35, .05), lid=.28, brows=(.235, -.005, .0), mouth_kind="flat")
    face("notice", look=(.55, .10), lid=0.0, scale=1.08, brows=(.19, .02, .025), mouth_kind="small_o")
    face("eager", look=(.45, -.35), lid=.08, brows=(.21, .025, .01), mouth_kind="smirk")
    face("hopeful", look=(.05, -.65), lid=.12, brows=(.20, .03, .02), mouth_kind="smile")
    face("shock", look=(0.0, -.15), lid=0.0, scale=1.24, pupil=.30, brows=(.135, .045, .03), mouth_kind="gasp")
    face("shock_track", look=(.15, -.75), lid=0.0, scale=1.2, pupil=.32, brows=(.15, .04, .02), mouth_kind="open_o")
    face("deadpan_down", look=(.05, -.85), lid=.46, brows=(.25, -.004, -.004), mouth_kind="flat_long")
    face("deadpan", look=(0.0, -.42), lid=.50, brows=(.25, -.006, -.004), mouth_kind="flat_long", lid_tilt=.004)
    costume()
    print("art written to", ART)


if __name__ == "__main__":
    main()
