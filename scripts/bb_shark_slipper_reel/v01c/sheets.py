"""Compose approval sheets from native delivery-camera frames and pose stills."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"renders/bb_shark_slipper_reel/v01c"
FONT_ROOT=Path("C:/Windows/Fonts")
CAL_LABELS=("Scheme by the shark","Hood flip","Fake victim shiver","Mask slips",
            "Scout enters","Silent side-eye","Slipper wind-up","Flight tracking",
            "Sole meets face","Hurt and dizzy pullback")


def font(name,size):
    return ImageFont.truetype(str(FONT_ROOT/name),size)


def sheet(path,title,subtitle,tiles,count,panel_w):
    panel_h=round(panel_w*16/9)
    gap=18
    margin=38
    stride=panel_h+92
    rows=(len(tiles)+count-1)//count
    canvas=Image.new("RGB",(2*margin+count*panel_w+(count-1)*gap,146+rows*stride),"#171a2a")
    draw=ImageDraw.Draw(canvas)
    draw.text((margin,27),title,fill="#f5ede4",font=font("segoeuib.ttf",44))
    draw.text((margin,87),subtitle,fill="#adb6cc",font=font("segoeui.ttf",23))
    for i,(frame,tag,label) in enumerate(tiles):
        x=margin+i%count*(panel_w+gap)
        y=139+i//count*stride
        with Image.open(frame) as im:
            canvas.paste(im.convert("RGB").resize((panel_w,panel_h),Image.Resampling.LANCZOS),(x,y))
        draw.rectangle((x,y,x+panel_w-1,y+panel_h-1),outline="#56607b")
        draw.text((x,y+panel_h+12),tag,fill="#ffc984",font=font("consola.ttf",18))
        draw.text((x,y+panel_h+35),label,fill="#f7f2eb",font=font("segoeuib.ttf",23))
    canvas.save(path)


def main():
    bench=json.loads((OUT/"benchmark.json").read_text())
    ch=json.loads((OUT/"choreography.json").read_text())
    folder=OUT/bench["native_stills_dir"]
    sheet(OUT/"calibration_10frames_v01c.png","Acting Start / Flying Slipper",
          "Delivery cameras  •  10 native 1080 × 1920 frames  •  30 fps",
          [(folder/f"frame_{f:04}.png",f"FRAME {f:03}",label)
           for f,label in zip(ch["calibration_frames"],CAL_LABELS)],5,332)
    look=OUT/"lookdev"
    sheet(OUT/"lookdev_turnaround_v01c.png","Acting Start / Character Look Development",
          "Blender 4.2 EEVEE  •  Love and Scout  •  Woodland camo and carnival lighting",
          [(look/(name+".png"),tag,label) for name,tag,label in (
              ("love_scheme","LOVE / HOOD DOWN","Scheming by the pool"),
              ("love_hood","LOVE / HOOD UP","Shiver and fake tears"),
              ("scout_walk","SCOUT / COURTYARD","White tee and red sneakers"),
              ("love_dizzy","LOVE / PAYOFF","Hurt expression and dizzy stars"))],4,408)


if __name__=="__main__":
    main()
