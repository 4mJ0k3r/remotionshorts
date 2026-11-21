"""Compose the eight native camera proofs for a modular part."""
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont

parts={
    3:((42,"Lightbulb eureka"),(75,"Circular match"),(127,"Goggles and wrench"),(208,"Breaker slam"),
       (221,"Gas and lightning"),(233,"Glass chamber"),(264,"Machine reveal"),(294,"Settled inventor")),
    4:((14,"Twilight exterior"),(135,"Window approach"),(171,"Dining console"),(212,"Puffed bhatura"),
       (269,"Slapstick dinner"),(304,"Maximum power"),(330,"Power lines advance"),(377,"National grid")),
    5:((29,"Running arrival"),(153,"Shoulder contact"),(197,"Elon speaking"),(252,"Launchpad"),
       (319,"Mars arrival"),(387,"Handshake"),(445,"Powered Earth"),(609,"Vault payoff")),
}
part=int(sys.argv[1])
root=Path(__file__).resolve().parents[2]/"renders/padoda_billionaire"
out=root/f"part{part}_v01"
gate=json.loads((out/"benchmark.json").read_text())
frames=out/gate["native_stills_dir"]
title=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",34)
caption=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",19)

def create(panels,filename,heading):
    width,height=250,444
    canvas=Image.new("RGB",(1080,82+((len(panels)+3)//4)*493),"#151829")
    d=ImageDraw.Draw(canvas)
    d.text((19,18),heading,font=title,fill="#fff2db")
    for i,(f,name) in enumerate(panels):
        x,y=18+i%4*263,76+i//4*493
        shot=frames/f"frame_{f:04d}.png"
        if not shot.exists():
            shot=out/"native_frames"/shot.name
        with Image.open(shot) as image:
            canvas.paste(image.convert("RGB").resize((width,height),Image.Resampling.LANCZOS),(x,y))
        d.text((x,y+height+7),f"f{f:03d}  {name}",font=caption,fill="#ffe5bc")
    canvas.save(out/filename)
    (root/"final"/filename).write_bytes((out/filename).read_bytes())

create(parts[part],f"part{part}_calibration.png",f"Padoda Billionaire / Part {part} native proofs")
if part==5:
    speaking=204 if (out/"native_frames/frame_0204.png").exists() else 197
    create(((29,"Arrival"),(153,"Shoulder contact"),(speaking,"Speaking"),(387,"Deal grin")),
           "elon_lookdev.png","Elon / Character and contact proofs")
