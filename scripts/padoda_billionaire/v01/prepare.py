import json, math, subprocess, wave
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw

here=Path(__file__).resolve().parent
out=here.parents[2]/"renders/padoda_billionaire/v01"
art=here/"art"
art.mkdir(exist_ok=True)
source=next((Path.home()/"Downloads").glob("ElevenLabs_2026-11-19T12_48_43*"))
rate=int(subprocess.check_output(["ffprobe","-v","error","-select_streams","a:0","-show_entries","stream=sample_rate","-of","csv=p=0",str(source)],text=True))
raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(source),"-t","9.3","-f","s16le","-ac","1","-"])
pcm=np.frombuffer(raw,"<i2")
end=round(rate*8.7)
def rms(a,b):
    x=pcm[round(a*rate):round(b*rate)].astype(float)/32768
    return float(np.sqrt(np.mean(x*x)))
window=[rms(i/100,(i+1)/100) for i in range(866,874)]
assert max(window)<.015,window
voice=pcm[:end].copy()
def save(name,x):
    with wave.open(str(out/name),"wb") as f:
        f.setparams((1,2,rate,0,"NONE","not compressed"));f.writeframes(x.astype("<i2").tobytes())
save("hook_narration.wav",voice)
rng=np.random.default_rng(28)
fx=np.zeros(end)
def layer(at,duration,amplitude,sound):
    start=round(at*rate); count=min(round(duration*rate),end-start)
    t=np.arange(count)/rate
    env=np.minimum(1,t/.012)*np.minimum(1,(duration-t)/.027)
    fx[start:start+count]+=amplitude*env*sound(t)
def sine(t,h): return np.sin(math.tau*h*t)
def noise(t): return rng.normal(0,1,len(t))
layer(1.06,1.18,.032,lambda t: sine(t,78)*np.sin(44*t+20*t*t)*np.sin(np.pi*t/1.18)**1.6)
layer(2.14,.34,.075,lambda t: np.exp(-11*t)*(sine(t,930)+.25*sine(t,1677)))
layer(2.43,.54,.057,lambda t: np.sin(np.pi*t/.54)*(.34*noise(t)+np.sin(math.tau*(62*t+385*t*t))))
for j,h in enumerate((523,659,784,1047,1319,1568)):
    layer(2.66+j*.063,.43,.054,lambda t,h=h: np.exp(-10*t)*(sine(t,h)+.18*sine(t,2.47*h)))
for at,h in ((4.2,1560),(6.0,2080)):
    layer(at,.36,.048,lambda t,h=h: np.exp(-13*t)*(sine(t,h)+.24*sine(t,2.63*h)))
layer(8.20,.50,.031,lambda t: np.sin(np.pi*t/.50)*(.33*noise(t)+np.sin(math.tau*(234*t-132*t*t))))
mixed=voice.astype(float)+32768*fx
assert np.max(np.abs(mixed))<32767
save("hook_master_audio.wav",np.round(mixed))
frames=261
env=[rms(i/30,(i+1)/30) for i in range(frames)]
(out/"audio_check.json").write_text(json.dumps({"trim_end_seconds":end/rate,"frames":frames,"last_word":"suno","suno_end_estimate":8.32,"next_word_estimate":8.84,"trim_window_peak_rms":max(window),"audio_rms":env},indent=2))

def picture(name,paint):
    im=Image.new("RGBA",(1024,1024),(4,4,7,0));d=ImageDraw.Draw(im)
    def line(points,w=8,c="#0a0a0e"):
        points=[(x*4,y*4) for x,y in points];d.line(points,fill=c,width=int(w*4),joint="curve")
        for x,y in (points[0],points[-1]):
            r=w*2;d.ellipse((x-r,y-r,x+r,y+r),fill=c)
    def oval(box,c): d.ellipse(tuple(v*4 for v in box),fill=c)
    def poly(points,c): d.polygon([(x*4,y*4) for x,y in points],fill=c)
    paint(line,oval,poly)
    im.save(art/(name+".png"))

def face(mode,l,o,p):
    for s in (-1,1):
        x=128+s*50
        if mode=="strain":
            l([(x+s*23,76),(x-s*22,96)],11)
            l([(x+s*18,107),(x-s*14,119),(x+s*18,135)],8)
        elif mode=="pop":
            o((x-27,83,x+27,146),"#09090d");o((x-21,89,x+21,140),"#fffaf4")
            o((x-6,108,x+6,122),"#09090d");l([(x-21,71),(x,60),(x+21,68)],7)
        else:
            l([(x-26,81),(x-4,74 if s==-1 else 81),(x+21,80)],8)
            if mode=="wink" and s==1:l([(x-20,113),(x,101),(x+20,112)],7)
            else:
                l([(x-23,105),(x+21,105)],7);o((x-7,104,x+10,125),"#09090d")
    if mode=="strain":
        o((74,151,181,207),"#0a0a0e");p([(84,164),(169,162),(173,187),(84,188)],"#fff1de")
        l([(86,175),(170,174)],3)
        for x in (106,128,151):l([(x,166),(x,186)],2)
        l([(37,49),(50,63),(51,77)],4,"#db503e");l([(65,49),(59,61),(71,69)],4,"#db503e")
    elif mode=="pop":
        o((110,147,155,213),"#0a0a0e");o((120,193,146,205),"#d46262")
    elif mode=="story":
        o((86,170,171,218),"#0a0a0e");p([(96,181),(162,177),(156,190),(99,192)],"#fff0da")
        o((112,200,151,211),"#e47874")
    else:
        l([(87,181),(112,190),(142,186),(171,169)],8)

for key in ("strain","pop","smug","story","wink"):picture(key,lambda *a,key=key:face(key,*a))
def outfit(l,o,p):
    p([(0,0),(256,0),(256,256),(0,256)],"#238b98")
    p([(56,0),(198,0),(173,70),(165,256),(89,256),(82,74)],"#f4b824")
    p([(0,4),(69,3),(91,132),(50,167)],"#145e75")
    p([(256,4),(190,4),(171,130),(209,167)],"#136177")
    l([(77,34),(99,104),(103,235)],4,"#efd49a");l([(180,33),(162,103),(157,235)],4,"#efd49a")
    l([(34,180),(72,173)],4,"#15586c");l([(191,175),(223,181)],4,"#15586c")
    l([(65,68),(58,125)],4,"#dbecdc");l([(192,68),(200,125)],4,"#dbecdc")
picture("outfit",outfit)
