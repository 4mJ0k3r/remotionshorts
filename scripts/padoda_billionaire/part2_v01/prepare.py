"""Extract the frame-aligned narration, mix effects and draw Kid-Hero decals."""
import json
from pathlib import Path
import subprocess
import wave

import numpy as np
from PIL import Image, ImageDraw

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[2]/"renders/padoda_billionaire/part2_v01"
ART=HERE/"art"
ART.mkdir(exist_ok=True)
source=next((Path.home()/"Downloads").glob("ElevenLabs_2026-11-19T12_48_43*.mp3"))
rate=int(subprocess.check_output(["ffprobe","-v","error","-select_streams","a:0",
    "-show_entries","stream=sample_rate","-of","csv=p=0",str(source)],text=True))
decoded=np.frombuffer(subprocess.check_output(["ffmpeg","-v","error","-i",str(source),
    "-t","18.72","-ac","1","-f","s16le","-"]),"<i2")
first,last=round(8.7*rate),round(18.1*rate)
start_rms,end_rms=(float(np.std(decoded[i-round(.015*rate):i+round(.015*rate)].astype(float))/32768)
                   for i in (first,last))
assert max(start_rms,end_rms)<.002
pcm=decoded[first:last]
rng=np.random.default_rng(52)
mix=np.zeros(len(pcm))

def s(t,f):
    return np.sin(2*np.pi*t*f)

def effect(t0,duration,gain,signal):
    start=round(t0*rate)
    count=min(round(duration*rate),len(mix)-start)
    t=np.arange(count)/rate
    edge=np.minimum(1,t/.022)*np.minimum(1,(duration-t)/.035)
    mix[start:start+count]+=gain*signal(t)*edge

effect(0,.4,.024,lambda t: np.exp(-9*t)*(s(t,784)+.43*s(t,1175)))
effect(.30,4.50,.012,lambda t: (.56+.44*s(t,1.9))*(s(t,441+14*s(t,.40))+.22*s(t,882)))
effect(3.95,1.05,.054,lambda t: np.exp(-2.8*t)*(s(t,86-22*t)+.32*s(t,145-68*t)+.18*rng.normal(size=len(t))))
effect(5.23,.31,.026,lambda t: np.exp(-6*t)*(s(t,1120+480*t)+.25*rng.normal(size=len(t))))
effect(6.18,1.38,.021,lambda t: (.8+.2*s(t,13))*s(t,1320-475*t))
for t in (7.50,7.69,7.83):
    effect(t,.24,.032,lambda x: np.exp(-19*x)*(s(x,183-180*x)+.25*rng.normal(size=len(x))))
mixed=pcm.astype(float)+32768*mix
assert max(abs(mixed))<32767
for name,values in (("part2_narration",pcm),("part2_master_audio",np.round(mixed))):
    with wave.open(str(OUT/(name+".wav")),"wb") as clip:
        clip.setparams((1,2,rate,0,"NONE","not compressed"))
        clip.writeframes(values.astype("<i2").tobytes())
(OUT/"audio_cut.json").write_text(json.dumps({"source_start":8.7,"source_end":18.1,
    "last_words":"gir jaate hain","next_phrase_start_estimate":18.66,"frames":282,
    "start_rms":start_rms,"end_rms":end_rms},indent=2))

INK="#090910"

def face(name,mode,look=0):
    image=Image.new("RGBA",(1024,1024),(8,8,12,0))
    d=ImageDraw.Draw(image)
    def oval(rect,color):
        d.ellipse(tuple(round(x*4) for x in rect),fill=color)
    def line(points,width,color=INK):
        d.line([(round(x*4),round(y*4)) for x,y in points],fill=color,width=width*4,joint="curve")
        r=width/2
        for x,y in (points[0],points[-1]):
            oval((x-r,y-r,x+r,y+r),color)
    for side in (-1,1):
        x=128+side*49
        if mode=="strain":
            line(((x+side*22,70),(x-side*19,93)),10)
            line(((x+side*18,102),(x-side*15,117),(x+side*17,130)),9)
        elif mode=="track":
            line(((x+side*23,69),(x-side*19,79)),9)
            oval((x-23,91,x+23,141),INK)
            oval((x-18,96,x+18,136),"#fff9f0")
            oval((x+look-7,105,x+look+7,127),INK)
        else:
            line(((x-23,78),(x-4,63 if side==-1 else 74),(x+22,74)),9)
            line(((x-23,105),(x+22,105)),8)
            oval((x-5,104,x+9,127),INK)
    if mode=="strain":
        oval((79,151,178,206),INK)
        oval((88,162,167,190),"#fff9ef")
        line(((91,177),(166,177)),3)
        for x in (111,133,152):line(((x,163),(x,188)),2)
        line(((39,51),(44,64),(36,75)),4,"#e14f4b")
        line(((57,49),(52,62),(60,70)),4,"#e14f4b")
    elif mode=="track":
        line(((101,181),(124,172),(147,178)),8)
    else:
        line(((93,173),(117,185),(143,183),(168,166)),8)
    image.save(ART/(name+".png"))

for i,look in enumerate((-13,-6,2,9,13)):face(f"kid_annoyed_track_{i}","track",look)
face("kid_mischievous","smirk")
face("kid_intense_strain","strain")
face("kid_smug_shrug","smirk")
image=Image.new("RGBA",(1024,1024),"#177474")
d=ImageDraw.Draw(image)
d.rectangle((0,0,1024,695),fill="#238c9e")
for y in (151,307,463,619):
    d.rectangle((0,y,1024,y+59),fill="#ffcb47")
    d.rectangle((0,y+60,1024,y+71),fill="#14687a")
d.polygon([(310,0),(713,0),(639,112),(389,112)],fill="#143e62")
d.rectangle((0,694,1024,1024),fill="#263049")
d.line([(512,743),(512,1024)],fill="#12192b",width=34)
image.save(ART/"striped_tee.png")
