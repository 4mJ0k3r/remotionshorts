import json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from random import Random

out=Path("renders/bb_shark_slipper_reel/v01d")
art=Path(__file__).with_name("art")
art.mkdir(exist_ok=True)
rate=44100
inputs=[Path.home()/"Downloads"/f"aud{i}.mp3" for i in (1,2,3)]
def clip(path):
    subprocess.run(["ffprobe","-v","error","-show_entries","format=duration","-of","csv=p=0",str(path)],check=True)
    return np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-f","s16le","-"]),"<i2")
samples=[clip(p) for p in inputs]
track=np.concatenate([*samples,np.zeros(round(4.5*rate),dtype="<i2")])
with wave.open(str(out/"master_audio.wav"),"wb") as w:
    w.setparams((1,2,rate,0,"NONE","not compressed"))
    w.writeframes(track.astype("<i2").tobytes())
frames=math.ceil(len(track)*30/rate)
energy=[]
for f in range(frames):
    x=track[f*1470:(f+1)*1470].astype(float)
    energy.append(float(np.sqrt(np.mean(x*x)))/32768)
(out/"timeline.json").write_text(json.dumps({"samples":[len(x) for x in samples],"rate":rate,"frames":frames,"rms":energy},indent=2))

def picture(name,draw,bg=(10,10,14,0)):
    im=Image.new("RGBA",(1024,1024),bg)
    draw(ImageDraw.Draw(im))
    im.save(art/f"{name}.png")

def face(d, mode, mouth):
    is_scout=mode in ("scout","glare")
    ink="#0A0A0E" if is_scout else "#100e17"
    def stroke(points, width=29, color=ink):
        p=[(int(x*4),int(y*4)) for x,y in points]
        d.line(p,fill=color,width=width,joint="curve")
        for x,y in (p[0],p[-1]):
            r=width/2
            d.ellipse((x-r,y-r,x+r,y+r),fill=color)
    def oval(rect,c):
        d.ellipse(tuple(v*4 for v in rect),fill=c)
    def filled(points):
        d.polygon([(round(x*4),round(y*4)) for x,y in points],fill=ink)
    for j,x in enumerate((76,178)):
        if mode=="hurt":
            stroke([(x-15,96),(x+15,128)],34);stroke([(x+15,96),(x-15,128)],34)
        else:
            a,b= {"sad":(75,62),"cheeky":(70,64),"scout":(79,79),"evil":(77,87)}.get(mode,(70,88))
            if j: a,b=b,a
            if is_scout:
                stroke([(x-24,a+1),(x-7,a*.73+b*.27-2),(x+21,b)],42)
            else:
                stroke([(x-21,a),(x+19,b)],32)
            stroke([(x-18,103),(x+18,102)],22)
            look=-10 if mode in ("evil","scheme") else 0
            oval((x+look-8,102,x+look+8,123),ink)
            if mode=="sad":
                oval((x+15,125,x+28,160),ink)
                oval((x+18,128,x+25,156),"#64d7f9")
                oval((x+19,132,x+22,139),"#e9ffff")
    if is_scout:
        # Trimmed two-lobed moustache with turned ends and a small philtrum.
        for side in (-1,1):
            filled([(128+side*x,y) for x,y in ((3,151),(11,147),(22,147),(34,151),
                   (43,156),(48,157),(45,163),(36,162),(23,157),(13,158),(3,163))])
        # Tapered jaw contour, deliberately light in weight beside the goatee.
        filled([(52,160),(59,175),(70,188),(89,197),(106,199),(111,205),
                (88,204),(67,194),(54,178)])
        filled([(204,160),(197,175),(186,188),(167,197),(150,199),(145,205),
                (168,204),(189,194),(202,178)])
        filled([(105,193),(115,195),(128,192),(141,195),(152,192),(147,206),
                (138,214),(125,217),(114,211),(108,203)])
        filled([(119,181),(137,181),(133,186),(128,189),(123,186)])
        stroke([(111,172),(129,171),(148,172 if mode=="scout" else 174)],25)
        return
    if mode=="hurt":
        oval((180,131,220,165),"#d86067")
        stroke([(94,187),(111,170),(131,187),(148,170),(170,186)],31)
    elif mouth:
        oval((91,154,165,176+mouth*12),ink)
        oval((103,158,153,166),"#fff4e5")
        if mouth==2: oval((111,183,146,192),"#ef8c88")
    elif mode=="sad":
        stroke([(98,179),(113,167),(136,167),(157,177)])
    elif mode in ("evil","cheeky","scheme"):
        stroke([(93,166),(111,176),(138,176),(165,159)])
    else:
        stroke([(108,165),(149,165)],24)

for mode in ("scheme","cheeky","sad","evil","hurt","scout","glare"):
    for mouth in (range(3) if mode in ("scheme","cheeky","sad","evil") else (0,)):
        picture(f"{mode}{mouth}",lambda d,m=mode,p=mouth:face(d,m,p))

def costume(d, camo):
    if camo:
        d.rectangle((0,0,1024,1024),fill="#666847")
        rng=Random(82)
        for _ in range(56):
            x,y=rng.randrange(1024),rng.randrange(1024)
            rr=rng.randrange(39,140)
            pts=[(x+rr*(.68+rng.random()*.65)*math.cos(i*math.tau/15),
                  y+.71*rr*(.66+rng.random()*.65)*math.sin(i*math.tau/15)) for i in range(15)]
            d.polygon(pts,fill=rng.choice(("#343831","#525236","#a08961","#423a30")))
    else:
        d.rounded_rectangle((1,7,1022,1017), radius=70, fill="#efece0")
        d.rounded_rectangle((1,714,1022,1017),radius=62,fill="#777a86")
        d.rectangle((1,714,1022,783),fill="#777a86")
        d.line((23,746,1000,746),width=14,fill="#515461")
        d.line((432,774,449,1000),width=9,fill="#999ba4")
        d.arc((284,-158,728,235),1,179,fill="#a8a9a8",width=20)
    d.line((191,75,802,935),fill="#11121d",width=66)
    d.rounded_rectangle((550,600,668,741),radius=17,fill="#192235")
    d.line((571,619,644,619),fill="#797c89",width=9)
picture("camo",lambda d:costume(d,True))
picture("tee",lambda d:costume(d,False))
