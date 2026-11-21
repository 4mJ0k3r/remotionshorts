"""Assemble contact art, annotated cut and word maps, and the 444-frame preview."""
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np
from PIL import Image,ImageDraw,ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/pokhran_1998_cia/v02b"
RATE=48000
END=444
COUNT=END*1600


def ff(*args,capture=False):
    return subprocess.run(["ffmpeg","-hide_banner","-nostdin",*map(str,args)],capture_output=capture,check=True)


def sheet():
    canvas=Image.new("RGB",(1452,776),"#171322")
    draw=ImageDraw.Draw(canvas)
    font="C:/Windows/Fonts/segoeuib.ttf"
    draw.text((24,14),"POKHRAN-II   /   V02B VERIFICATION",font=ImageFont.truetype(font,35),fill="#f9ddc5")
    panels=((25,"Console and SCAN reach"),(215,"All five shafts"),(315,"Kalam and Engineer"),(420,"Mug-to-lips contact"))
    for index,(frame,caption) in enumerate(panels):
        x=20+index*358
        with Image.open(OUT/"preview_540p_frames"/f"frame_{frame:04d}.png") as img:
            canvas.paste(img.convert("RGB").resize((337,599),Image.Resampling.LANCZOS),(x,86))
        draw.text((x,705),f"f{frame:03}  {caption}",font=ImageFont.truetype(font,20),fill="#f9c69e")
    canvas.save(OUT/"pokhran_part1_v02b_verification.png")


def manifests():
    p=json.loads((HERE.parent/"v01b/master_plan.json").read_text(encoding="utf-8"))
    p["words"]=[w for w in p["words"] if w["start"]<14.8]
    p["audio_seconds"]=14.8
    p["part_boundaries_frames"]=[0,END]
    # Intervals document the rendered shot or prop holding the concept on screen.
    events={
        "w001":("console date",0,2.2),"w003":("American intelligence room",0,2.2),
        "w007":("Keyhole spacecraft",2.2,5.8),"w009":("Rajasthan terrain and placard",3.0,6.65),
        "w011":("Three aerial photographs, then carried contact print",3.7,6.68),
        "w020":("Below-ground cutaway",7.6,9.8),"w021":("Kalam and Engineer gallery",9.8,11.23),
        "w023":("Five illuminated indicators in the gallery",9.8,11.23),
        "w024":("Five indicator lights and cutback to abstract markers",9.8,11.23),
        "w025":("Five abstract numbered test markers",11.23,12.30),
        "w026":("Five locked markers on screen",11.23,12.30),
        "w030":("CIA clear-screen gag",12.30,13.2),
        "w033":("The unaware CIA boss savors coffee",13.2,14.8),
    }
    p["visual_events"]=[{"kind":"face","start":0.0,"end":2.2}]+[
        {"word_id":wid,"kind":"prop","visual":name,"start":a,"end":b} for wid,(name,a,b) in events.items()]
    (HERE/"master_plan.json").write_text(json.dumps(p,indent=2,ensure_ascii=False),encoding="utf-8")
    (OUT/"cuts.json").write_text(json.dumps({"cuts":[66,90,174,294,337,369,396]},indent=2))
    return p


def mix(plan):
    source=Path.home()/"Downloads"/plan["source_audio"]["file"]
    if sha256(source.read_bytes()).hexdigest()!=plan["source_audio"]["sha256"]:
        raise ValueError("Narration checksum mismatch.")
    voice=np.frombuffer(ff("-v","error","-i",source,"-map","0:a:0","-ac",1,"-ar",RATE,
                         "-af",f"aresample={RATE},atrim=end_sample={COUNT}","-f","f32le","-",capture=True).stdout,"<f4")
    if len(voice)!=COUNT:
        raise ValueError("The verbatim hook slice is incomplete.")
    soundtrack=np.repeat(voice[:,None],2,axis=1).copy()*.79
    noise=np.random.default_rng(571)

    def cue(at,dur,amp,start,finish,texture,pan=0):
        i=round(at*RATE)
        n=min(COUNT-i,round(dur*RATE))
        t=np.arange(n)/RATE
        u=t/dur
        theta=2*math.pi*t*(start+(finish-start)*u*.5)
        fundamental=np.sin(theta)
        white=noise.standard_normal(n)
        hiss=white-.74*np.roll(white,1)
        if texture=="metal":
            signal=.56*fundamental+.17*np.sin(theta*2.53)+.10*np.sin(theta*4.23)+.21*hiss
        elif texture=="snap":
            signal=.72*hiss+.31*fundamental
        elif texture=="wind":
            signal=(.5*fundamental+.27*np.sin(theta*1.77))+.31*hiss
        elif texture=="sip":
            signal=(.54*fundamental+.44*hiss)*(.4+.6*np.sin(2*math.pi*t*33)**2)
        else:
            signal=.82*fundamental+.18*np.sin(theta*2)
        if texture=="wind":
            envelope=np.sin(np.pi*u)**1.85
        else:
            envelope=np.minimum(1,t/.005)*(1-u)**1.85
        soundtrack[i:i+n] += (signal*envelope*amp)[:,None]*np.array([1-pan,1+pan])

    for index,t in enumerate(np.arange(.18,13.5,.39)):
        hz=(49,49,58.27,46.25)[index%4]
        cue(t,.49,.075,hz,hz-.32,"note",.10 if index%2 else -.10)
        if index>6 and index%2:
            cue(t+.195,.24,.024,hz*4,hz*3.98,"note",-.23)
    cue(31/30,.16,.16,648,864,"note",-.19)
    cue(2.28,.39,.12,98,760,"wind",.10)
    cue(74/30,.13,.22,480,176,"metal",.00)
    for index,frame in enumerate((112,139,164)):
        cue((frame-1)/30,.135,.205,220,71,"snap",(index-1)*.34)
    cue(5.77,1.62,.17,418,59,"wind",.15)
    cue(7.55,.36,.13,93,39,"metal",-.11)
    # Keep the v02 impact sounds and reposition them to the new lock frames.
    for index,frame in enumerate((242,254,266,278,290)):
        cue((frame-1)/30,.24,.186+index*.012,205+index*19,48,"metal",(index-2)*.16)
    cue(12.54,.50,.18,800,639,"metal",.08)
    cue(13.72,.37,.16,330,99,"sip",-.15)
    cue(14.16,.16,.078,650,332,"note",.08)
    raw=OUT/"hook_mix.f32"
    soundtrack.astype("<f4").tofile(raw)
    args=("-f","f32le","-ar",str(RATE),"-ac","2","-i",raw)
    try:
        analysis=ff(*args,"-af","ebur128=peak=true","-f","null","-",capture=True)
        summary=analysis.stderr.decode(errors="replace").rsplit("Summary:",1)[-1]
        integration=float(re.search(r"I:\s+(-?\d+\.\d+) LUFS",summary)[1])
        maximum=float(re.search(r"Peak:\s+(-?\d+\.\d+) dBFS",summary)[1])
        gain=min(-14.3-integration,-3.25-maximum)
        audio=OUT/"hook_preview_mix.wav"
        ff("-v","error","-y",*args,"-af",f"volume={gain:.3f}dB","-c:a","pcm_s24le",audio)
    finally:
        raw.unlink()
    return audio


def mux(audio):
    frames=OUT/"preview_540p_frames"
    if not all((frames/f"frame_{f:04d}.png").is_file() for f in range(1,END+1)):
        raise RuntimeError("Missing preview frames.")
    final=OUT/"pokhran_part1_v02b_540p.mp4"
    pending=final.with_stem(final.stem+".pending")
    ff("-v","error","-y","-framerate",30,"-start_number",1,"-i",frames/"frame_%04d.png",
       "-i",audio,"-map","0:v:0","-map","1:a:0","-frames:v",END,"-c:v","libx264","-preset","fast",
       "-crf",17,"-pix_fmt","yuv420p","-c:a","aac","-b:a","256k","-movie_timescale",RATE,
       "-movflags","+faststart",pending)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames",
                                             "-show_streams","-of","json",str(pending)]))
    video,voice=probe["streams"]
    assert (video["width"],video["height"],video["r_frame_rate"],int(video["nb_read_frames"]))==(540,960,"30/1",END)
    assert all(s["start_pts"]==0 and abs(float(s["duration"])-14.8)<.001 for s in (video,voice))
    ff("-v","error","-xerror","-i",pending,"-map","0:v","-map","0:a","-f","null","-")
    pending.replace(final)
    (OUT/"preview_decode_check.json").write_text(json.dumps(probe,indent=2),encoding="utf-8")


if __name__=="__main__":
    sheet()
    plan=manifests()
    if "--proof-only" not in sys.argv:
        mux(mix(plan))
