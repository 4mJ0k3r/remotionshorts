import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT=Path(__file__).resolve().parents[3]
OUT=ROOT/"renders/padoda_billionaire/v01"

def font(name,size):return ImageFont.truetype("C:/Windows/Fonts/"+name,size)

def sheet(dst,title,sub,panels,width):
    h=round(width*16/9)
    margin,gap=38,18
    rows=(len(panels)+3)//4
    height=h+76
    im=Image.new("RGB",(2*margin+4*width+3*gap,154+rows*height),"#151827")
    d=ImageDraw.Draw(im)
    d.text((margin,26),title,fill="#f9edde",font=font("segoeuib.ttf",46))
    d.text((margin,91),sub,fill="#aeb9ce",font=font("segoeui.ttf",22))
    for i,(f,label) in enumerate(panels):
        x,y=margin+i%4*(width+gap),146+i//4*height
        with Image.open(base/f"frame_{f:04}.png") as frame:
            im.paste(frame.convert("RGB").resize((width,h),Image.Resampling.LANCZOS),(x,y))
        d.rectangle((x,y,x+width-1,y+h-1),outline="#384362")
        d.text((x,y+h+10),f"FRAME {f:03}",fill="#ffc681",font=font("consola.ttf",17))
        d.text((x,y+h+33),label,fill="#f8f2e9",font=font("segoeuib.ttf",23))
    im.save(OUT/dst)

report=json.loads((OUT/"benchmark.json").read_text())
base=OUT/report["native_stills_dir"]
sheet("lookdev_turnaround.png","Padoda Billionaire  /  Hero lookdev",
      "Cream cel bands, teal-and-gold costume, and graphic ink under two lighting setups",
      [(61,"Workshop strain"),(112,"Billionaire mode"),(188,"Lowered glasses and coin flick"),(223,"Warm-key storyteller")],412)
sheet("calibration_8frames.png","Padoda Billionaire  /  Opening hook",
      "Eight native delivery-camera stills  •  1080 × 1920  •  30 fps",
      [(14,"Workshop opening"),(61,"Redline"),(77,"Green-to-gold shockwave"),(89,"Vault reveal"),
       (145,"Bullion crane-back"),(188,"Coin flick"),(223,"Storyteller lean-in"),(261,"Wink and amber tail")],376)
