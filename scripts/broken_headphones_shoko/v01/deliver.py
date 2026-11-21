"""Contact sheets, word-gate inputs, original voice mix, and preview mux."""
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/broken_headphones_shoko/v01"
END=790
RATE=48000
COUNT=END*1600


def ff(*arguments,capture=False):
    return subprocess.run(["ffmpeg","-hide_banner","-nostdin",*map(str,arguments)],check=True,capture_output=capture)


def visual_proofs():
    report=json.loads((OUT/"benchmark.json").read_text())
    folder=OUT/report["native_stills_dir"]
    art=OUT/"cast_stills"
    title=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",32)
    labels=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",17)
    card=Image.new("RGB",(1488,760),"#1d1727")
    pen=ImageDraw.Draw(card)
    pen.text((23,20),"BROKEN HEADPHONES / SHOKO    •    ORIGINAL CAST",font=title,fill="#f8e1cd")
    captions=("Boy / deadpan and panic","Shoko / shy and crimson","Year 7 / puppy and cable","Brick street and school hall")
    for index,text in enumerate(captions):
        x=22+index*366
        if index<3:
            with Image.open(art/f"frame_{901+index:04}.png") as source:
                card.paste(source.convert("RGB").resize((346,615),Image.Resampling.LANCZOS),(x,81))
        else:
            for j,path in enumerate((folder/"frame_0001.png",art/"frame_0904.png")):
                with Image.open(path) as source:
                    card.paste(source.convert("RGB").crop((0,420,1080,1380)).resize((346,307),Image.Resampling.LANCZOS),
                               (x,81+j*308))
        pen.text((x,712),text,font=labels,fill="#eec1ad")
    card.save(OUT/"cast_lookdev.png")
    files=sorted(folder.glob("frame_*.png"))
    contact=Image.new("RGB",(1056,642),"#1d1727")
    pen=ImageDraw.Draw(contact)
    for i,path in enumerate(files):
        x=i%6*176
        y=i//6*321
        with Image.open(path) as im:
            contact.paste(im.resize((176,303),Image.Resampling.LANCZOS),(x,y))
        pen.text((x+6,y+303),path.stem,font=labels,fill="#f7d2b6")
    contact.save(OUT/"motion_calibration.jpg",quality=80)


def mix():
    data=json.loads((HERE/"master_plan.json").read_text(encoding="utf-8"))
    source=Path.home()/"Downloads"/data["source_audio"]["file"]
    if sha256(source.read_bytes()).hexdigest()!=data["source_audio"]["sha256"]:
        raise ValueError("Narration checksum mismatch.")
    sample=ff("-v","error","-i",source,"-map","0:a:0","-ac",1,"-ar",RATE,
              "-af",f"aresample={RATE},atrim=end_sample={COUNT}","-f","f32le","-",capture=True).stdout
    original=np.frombuffer(sample,"<f4")
    assert len(original)==COUNT
    audio=np.repeat(original[:,None],2,axis=1).copy()*.78
    rng=np.random.default_rng(8745)

    def tone(at,dur,amp,freq,end,shape,pan=0):
        start=round(at*RATE)
        t=np.arange(min(round(dur*RATE),COUNT-start))/RATE
        phase=2*math.pi*t*(freq+(end-freq)*t/(2*dur))
        attack=np.minimum(1,t/.009)
        amp=amp*attack*(1-t/dur)**1.7
        wave=np.sin(phase)
        if shape=="pluck":
            wave=.63*wave+.22*np.sin(phase*2.01)+.10*np.sin(phase*3.02)
            amp*=np.exp(-2.4*t/dur)
        elif shape=="air":
            noise=rng.standard_normal(len(t))
            wave=.66*(noise-.67*np.roll(noise,1))+.30*wave
        elif shape=="bite":
            wave=.52*wave+.38*np.sin(3.13*phase)+.1*np.sin(7*phase)
        elif shape=="zap":
            wave=.42*wave+.34*np.sign(wave)+.24*np.sin(2.48*phase)
        audio[start:start+len(t)]+=(wave*amp)[:,None]*np.array([1-pan,1+pan])

    chords=[(130.81,164.81,196),(110.0,130.81,164.81),(87.31,110.0,130.81),(98.,123.47,146.83)]
    for beat,t in enumerate(np.arange(.06,25.98,.544)):
        chord=chords[beat//4%4]
        duck=.83 if 2.68<t<3.7 or 12.25<t<13.8 else 1
        tone(t,.37,.033*duck,chord[beat%3],chord[beat%3]*.999,"pluck",(-1)**beat*.25)
        tone(t+.17,.25,.019*duck,chord[(beat+1)%3]*2,chord[(beat+1)%3]*2,"pluck",.21)
        tone(t,.34,.019,chord[0]*.51,chord[0]*.49,"bass")
        if beat%2:
            tone(t+.25,.10,.009,201,92,"air",-.21)
    for a,b,amp in ((.17,4.10,.035),(14.2,16.91,.046),(19.30,21.0,.029),(22.15,24.38,.033)):
        for i,t in enumerate(np.arange(a,b,.338)):
            tone(t,.12,amp,133,73,"air",(-1)**i*.35)
    cues=[
        (2.91,.25,.061,642,823,"pluck",.2),
        (6.77,.31,.067,271,73,"air",-.19),(7.14,.20,.068,462,338,"bite",-.2),
        (8.49,.55,.069,423,163,"pluck",0),(10.40,.35,.075,375,517,"pluck",.16),
        (12.43,.18,.080,213,144,"bite",-.17),(12.78,.15,.084,241,178,"bite",-.17),
        (13.08,.17,.088,233,142,"bite",-.17),(13.10,.24,.105,621,171,"zap",-.18),
        (14.28,.27,.063,196,355,"air",.21),(15.16,.22,.061,433,571,"pluck",.33),
        (17.57,.33,.071,461,698,"pluck",.12),(19.22,.60,.021,119,194,"air",.13),
        (19.91,.55,.020,164,258,"air",-.21),(20.47,.17,.048,498,372,"bite",-.12),
        (21.10,.21,.047,394,277,"pluck",.09),(24.68,.19,.065,423,548,"pluck",.19),
        (24.88,.22,.103,503,98,"zap",.02),(25.51,.54,.061,523,407,"air",-.14),
        (25.76,.43,.060,552,735,"pluck",.23),
    ]
    for cue in cues:
        tone(*cue)
    raw=OUT/"mix_raw.f32"
    wav=OUT/"part1_preview_mix.wav"
    audio.astype("<f4").tofile(raw)
    try:
        input_args=("-f","f32le","-ar",RATE,"-ac",2,"-i",raw)
        loud="loudnorm=I=-14.3:TP=-3.45:LRA=7"
        response=ff(*input_args,"-af",loud+":print_format=json","-f","null","-",capture=True)
        scan=response.stderr.decode(errors="replace")
        values=json.loads(scan[scan.rfind("{"):scan.rfind("}")+1])
        filters=(f'{loud}:measured_I={values["input_i"]}:measured_LRA={values["input_lra"]}:'
                 f'measured_TP={values["input_tp"]}:measured_thresh={values["input_thresh"]}:'
                 f'offset={values["target_offset"]}:linear=true,aresample={RATE},apad,atrim=end_sample={COUNT}')
        ff("-v","error","-y",*input_args,"-af",filters,"-c:a","pcm_s24le",wav)
    finally:
        raw.unlink()
    return wav


def mux():
    folder=OUT/"preview_540p_frames"
    missing=[i for i in range(1,END+1) if not (folder/f"frame_{i:04}.png").is_file()]
    if missing:
        raise ValueError(f"Incomplete sequence. First missing frames: {missing[:5]}")
    target=OUT/"part1_v01_540p.mp4"
    pending=target.with_stem(target.stem+".pending")
    ff("-v","error","-y","-framerate",30,"-start_number",1,"-i",folder/"frame_%04d.png",
       "-i",mix(),"-map","0:v:0","-map","1:a:0","-frames:v",END,"-c:v","libx264",
       "-preset","fast","-crf",17,"-pix_fmt","yuv420p","-c:a","aac","-b:a","240k",
       "-video_track_timescale",15360,"-movie_timescale",RATE,"-movflags","+faststart",pending)
    scan=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams",
                                             "-of","json",str(pending)]))
    video,audio=scan["streams"]
    assert (video["width"],video["height"],video["r_frame_rate"],int(video["nb_read_frames"]))==(540,960,"30/1",END)
    assert video["start_pts"]==audio["start_pts"]==0
    assert abs(float(audio["duration"])-END/30)<.001 and abs(float(video["duration"])-END/30)<.001
    ff("-v","error","-xerror","-i",pending,"-map","0:v","-map","0:a","-f","null","-")
    pending.replace(target)
    (OUT/"preview_decode_check.json").write_text(json.dumps(scan,indent=2))
    print(target)


if __name__=="__main__":
    visual_proofs()
    if "--proof-only" not in sys.argv:
        mux()
