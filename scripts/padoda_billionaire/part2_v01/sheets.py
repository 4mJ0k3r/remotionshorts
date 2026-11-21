"""Present the approved camera stills in two Stage 1 sheets."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

out=Path(__file__).resolve().parents[3]/"renders/padoda_billionaire/part2_v01"
report=json.loads((out/"benchmark.json").read_text())
frames=out/report["native_stills_dir"]
heading=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",41)
label=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",23)
meta=ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf",19)
width,height=352,626

def still(frame,w=width,h=height):
    with Image.open(frames/f"frame_{frame:04d}.png") as image:
        return image.convert("RGB").resize((w,h),Image.Resampling.LANCZOS)

def sheet(filename,title,panels):
    canvas=Image.new("RGB",(1494,122+((len(panels)+3)//4)*697),"#171a2a")
    draw=ImageDraw.Draw(canvas)
    draw.text((22,18),title,font=heading,fill="#fff2dd")
    draw.text((23,77),"Padoda Billionaire  /  Part 2 v01  •  Native 1080 × 1920 stills",font=meta,fill="#b9c9e4")
    for i,(frame,caption) in enumerate(panels):
        x,y=22+i%4*369,112+i//4*697
        if isinstance(frame,tuple):
            for j,value in enumerate(frame):
                image=still(value)
                crop=image.crop((17,85,334,409))
                canvas.paste(crop.resize((width,height//2-4),Image.Resampling.LANCZOS),(x,y+j*(height//2+2)))
        else:
            canvas.paste(still(frame),(x,y))
        draw.text((x,y+height+7)," / ".join(f"f{f:03d}" for f in frame) if isinstance(frame,tuple)
                  else f"f{frame:03d}",font=meta,fill="#fcbe78")
        draw.text((x,y+height+32),caption,font=label,fill="#fff2df")
    canvas.save(out/filename)

sheet("lookdev_turnaround.png","Kid-Hero and the mosquito cast",[(10,"Annoyed eye-track"),(134,"Lime-lit strain"),
      (272,"Smug shrug"),((168,192),"Mosquito shock and faint")])
sheet("calibration_8frames.png","Childhood and fainting mosquitoes",[(1,"Amber ring entry"),(72,"Mischievous bed brace"),
      (134,"Three-quarter lime eruption"),(168,"Macro shock"),(192,"Upside-down faint"),(212,"Spiraling drop"),
      (235,"Toy-block landing"),(272,"Settled shrug")])
