"""Lay out the two approval sheets from their rendered source PNGs."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "renders/ricks_benchmark_10s/v01b"
FONTS = Path("C:/Windows/Fonts")
INK, SUB, GOLD = "#F3ECE1", "#A8ADC3", "#FFC684"


def font(size, weight="regular"):
    name = {"regular":"segoeui.ttf", "bold":"segoeuib.ttf", "mono":"consola.ttf"}[weight]
    return ImageFont.truetype(str(FONTS / name), size)


def line(draw, xy, label, size, color, weight="regular"):
    draw.text(xy,label,font=font(size,weight),fill=color,anchor="lt")


def compose(title, subtitle, panels, destination):
    width, height = 416, 740
    margin, spacing, top, block = 48, 20, 150, 825
    rows = (len(panels)+3)//4
    image = Image.new("RGB", (2*margin+width*4+spacing*3, top+rows*block+20),"#111421")
    draw = ImageDraw.Draw(image)
    line(draw,(margin,35),title,47,INK,"bold")
    line(draw,(margin,99),subtitle,23,SUB)
    for i,(path, tag, caption) in enumerate(panels):
        x = margin+(width+spacing)*(i%4)
        y = top+block*(i//4)
        with Image.open(path) as source:
            source = source.convert("RGB").resize((width,height),Image.Resampling.LANCZOS)
            image.paste(source,(x,y))
        draw.rectangle((x,y,x+width-1,y+height-1),outline="#353A50")
        line(draw,(x,y+height+12),tag,19,GOLD,"mono")
        line(draw,(x,y+height+39),caption,24,INK,"bold")
    image.save(destination)


def main():
    report = json.loads((OUT/"benchmark.json").read_text(encoding="utf-8"))
    frames = OUT / report["native_stills_dir"]
    look = OUT / "lookdev"
    compose("Golden Polaroid  /  Character look development",
            "Blender 4.2 EEVEE Next  •  Direct-lit cel faces and matte stick limbs",
            [(look/(name+".png"),tag,caption) for name,tag,caption in (
                ("hero_front","HERO / FRONT","Excited awe"),
                ("hero_three_quarter","HERO / ¾","Warm key and cobalt fill"),
                ("broker_hood","BROKER / ¾","Hood shadow and grin"),
                ("hero_terror","HERO / CLOSE","Terror snap"),
            )],OUT/"lookdev_turnaround_v01b.png")
    compose("Golden Polaroid  /  Camera calibration",
            "Version 01b  •  Eight native 1080 × 1920 frames  •  30 fps",
            [(frames/f"frame_{f:04d}.png",f"FRAME {f:03}",caption) for f,caption in (
                (15,"Midnight desk"),(30,"Discovery"),(80,"Polaroid pickup"),(122,"Match-zoom into the print"),
                (134,"Rain alley reveal"),(180,"Sneak-run"),(250,"The broker’s offer"),(285,"Terror reaction"),
            )],OUT/"calibration_8frames_v01b.png")


if __name__ == "__main__":
    main()
