"""Create the proof sheet and render-ready score, then validate the Stage 1 mux."""
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

from PIL import Image, ImageDraw
import numpy as np

from plan import HERE, ROOT, SOURCE

OUT=ROOT/"renders/one_year_no_wipe/v01"
RATE=48000
COUNT=837*1600


def run(*args,check=True,**kwargs):
    return subprocess.run(list(map(str,args)),cwd=ROOT,check=check,**kwargs)


def ff(*args,**kwargs):
    return run("ffmpeg","-hide_banner","-nostdin",*args,**kwargs)


def mix(*, full=False):
    from native import ENDS, RENDERS

    count=ENDS[-1]*1600 if full else COUNT
    src=json.loads((HERE/"master_plan.json").read_text(encoding="utf-8"))["source_audio"]
    if sha256(SOURCE.read_bytes()).hexdigest()!=src["sha256"]:
        raise ValueError("The locked narration file changed")
    voice_filter=f"aresample={RATE}" if full else f"aresample={RATE},atrim=end_sample={COUNT}"
    raw=ff("-v","error","-i",SOURCE,"-ac",1,"-ar",RATE,"-af",voice_filter,"-f","f32le","-",
           capture_output=True).stdout
    voice=np.frombuffer(raw,"<f4")
    if (not full and len(voice)!=COUNT) or (full and not 0<=count-len(voice)<RATE):
        raise ValueError("Incomplete narration slice")
    audio=np.zeros((count,2),dtype=np.float32)
    audio[:len(voice)]=voice[:,None]*.82
    rng=np.random.default_rng(20261120)

    def cue(at,dur,gain,a,b,mode,pan=0):
        start=round(at*RATE)
        end=min(count,start+round(dur*RATE))
        if start>=end:
            return
        t=np.arange(end-start)/RATE
        u=t/dur
        ph=math.tau*t*(a+(b-a)*.5*u)
        base=np.sin(ph)
        env=np.minimum(1,t/.004)*(1-u)**1.7
        if mode=="pluck":
            base=.71*base+.15*np.sin(2.006*ph)+.11*np.sin(3.024*ph)
            env*=np.exp(-u*2.5)
        elif mode=="page":
            noise=rng.standard_normal(len(t))
            base=(noise-.53*np.roll(noise,2))*(.5+.5*np.sin(t*137)**2)
            env=np.sin(math.pi*u)**1.3
        elif mode in ("spin","chair","chalk"):
            noise=rng.standard_normal(len(t))
            base=.14*noise+(.41*base+.28*np.sin(2.72*ph))*(.39+.61*np.sin(t*(63 if mode=="spin" else 124))**2)
            env=np.sin(math.pi*u)**1.45
        elif mode=="stamp":
            base=.49*base+.13*np.sin(2.07*ph)+.29*rng.standard_normal(len(t))*np.exp(-t*48)
            env=np.minimum(1,t/.002)*(1-u)**2.1
        elif mode=="bloop":
            base=.9*base+.1*np.sin(2.46*ph)
        elif mode=="sting":
            base=.78*base+.21*np.sin(ph*2.01)
        audio[start:end]+=(gain*env*base)[:,None]*np.array((1-pan,1+pan))

    chords=((130.813,164.814,195.998),(146.832,174.614,220.),(97.999,123.471,146.832),(110.,130.813,164.814))
    for j,t in enumerate(np.arange(.04,82.2 if full else 27.84,.468)):
        harmony=chords[(j//6)%4]
        fx=.52 if 26.35<t<27.9 else 1
        if full and 30.58<=t<=37.28:
            continue
        cue(t,.40,.048*fx,harmony[0],harmony[0]*.998,"pluck",-.18)
        cue(t+.044,.30,.043*fx,harmony[(j+1)%3]*2,harmony[(j+1)%3]*1.994,"pluck",.25)
        if j%2==0:
            cue(t+.234,.29,.028*fx,harmony[(j+2)%3]*2,harmony[(j+2)%3]*1.992,"pluck",.13)
    for event in (
        (6.27,.25,.14,268,145,"page",-.20),
        (7.72,.67,.17,295,108,"spin",.13),
        (8.25,.19,.05,248,154,"spin",.13),
        (10.50,.26,.14,520,220,"bloop",-.13),
        (13.07,.24,.14,320,116,"page",-.23),
        (16.17,.28,.13,111,339,"chair",-.11),
        (17.73,.22,.105,137,276,"chair",.08),
        (19.12,.28,.095,198,331,"chair",-.12),
        (20.87,.26,.125,185,367,"chair",.22),
        (21.47,.39,.086,160,300,"chair",-.11),
        (23.57,.37,.255,147,45,"stamp",.05),
        (25.43,.24,.089,811,271,"chalk",-.13),
        (26.48,.21,.10,943,647,"sting",.23),
        (27.73,.15,.06,486,260,"bloop",.08),
    ):
        cue(*event)
    if full:
        from audio_finish import play
        play(cue)
    result=(RENDERS/"final/master_audio.wav") if full else OUT/"part1_preview_mix.wav"
    result.parent.mkdir(parents=True,exist_ok=True)
    with tempfile.TemporaryDirectory(dir=result.parent) as folder:
        scratch=Path(folder)/"mixed.f32"
        audio.astype("<f4").tofile(scratch)
        args=("-f","f32le","-ar",RATE,"-ac",2,"-i",scratch)
        target="loudnorm=I=-13.8:TP=-4.25:LRA=8" if full else "loudnorm=I=-14:TP=-3.8:LRA=8"
        measured=ff(*args,"-af",target+":print_format=json","-f","null","-",capture_output=True).stderr.decode(errors="replace")
        report=json.loads(measured[measured.rfind("{"):measured.rfind("}")+1])
        gain=",volume=.55dB" if full else ""
        setting=(f'{target}:measured_I={report["input_i"]}:measured_TP={report["input_tp"]}:'
                 f'measured_LRA={report["input_lra"]}:measured_thresh={report["input_thresh"]}:'
                 f'offset={report["target_offset"]}:linear=true,aresample={RATE}{gain},apad,atrim=end_sample={count}')
        ff("-v","error","-y",*args,"-af",setting,"-c:a","pcm_s24le",result)
    return result


def proof():
    report=json.loads((OUT/"benchmark.json").read_text())
    shots=json.loads((OUT/"shots.json").read_text())
    frames=OUT/report["proofs_dir"]
    with (OUT/"proof_edge.json").open("w",encoding="utf-8") as log:
        result=run("python",ROOT/"scripts/ricks_metrics_gate.py","--edge-density",frames,stdout=log,check=False)
    sheet=Image.new("RGB",(1296,1168),"#171423")
    draw=ImageDraw.Draw(sheet)
    choices=(
        ("Red-Cap Boy", (shots["panels"][0],shots["proof_frames"][0],shots["proof_frames"][7])),
        ("Stern teacher and curly-haired classmate",(shots["proof_frames"][-1],shots["proof_frames"][8])),
        ("Mint bathroom",(shots["panels"][2],)),
        ("Water-cycle classroom",(shots["panels"][3],)),
    )
    for i,(label,picks) in enumerate(choices):
        x,y=(i%2)*648,(i//2)*584
        cell=630//len(picks)
        for j,f in enumerate(picks):
            with Image.open(frames/f"frame_{f:04}.png") as plate:
                plate.thumbnail((cell-12,535))
                sheet.paste(plate.convert("RGB"),(x+9+j*cell+(cell-plate.width)//2,y+19))
        draw.text((x+26,y+560),label,fill="#f3e5d5")
    sheet.save(OUT/"cast_and_sets_lookdev.png")
    raise SystemExit(result.returncode)


def mux():
    audio=mix()
    mp4=OUT/"part1_v01_540p.mp4"
    pending=mp4.with_suffix(".pending.mp4")
    ff("-v","error","-y","-framerate",30,"-i",OUT/"preview_frames/frame_%04d.png","-i",audio,
       "-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","fast","-crf",16,"-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","240k","-video_track_timescale",15360,"-movie_timescale",48000,
       "-movflags","+faststart",pending)
    streams=json.loads(run("ffprobe","-v","error","-count_frames","-show_streams","-of","json",pending,capture_output=True).stdout)
    video,sound=streams["streams"]
    assert (video["width"],video["height"],video["r_frame_rate"],int(video["nb_read_frames"]))==(540,960,"30/1",837)
    assert sound["duration_ts"]==COUNT and sound["start_pts"]==video["start_pts"]==0
    ff("-v","error","-xerror","-i",pending,"-map",0,"-f","null","-")
    pending.replace(mp4)
    (OUT/"decode.json").write_text(json.dumps(streams,indent=2))
    print(mp4)


if __name__=="__main__":
    if sys.argv[-1]=="proof":
        proof()
    else:
        mux()
