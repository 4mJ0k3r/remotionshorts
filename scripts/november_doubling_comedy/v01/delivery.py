"""Assemble native proof panels, prepare the comedy mix, and verify the preview."""
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys
import tempfile

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from timing import BOUNDARIES, CLANK, DAY1, DAY2, HERE, FPS, LENGTH, OUT, ROOT, SOURCE, WRONG_NUMBER

RATE=48000
SAMPLES=LENGTH*RATE//FPS
def run(*args,check=True,**kwargs):
    return subprocess.run(list(map(str,args)),cwd=ROOT,check=check,**kwargs)


def ff(*args,**kwargs):
    return run("ffmpeg","-hide_banner","-nostdin",*args,**kwargs)


def audio(path=None):
    full = path is not None
    length = BOUNDARIES[-1] if full else LENGTH
    samples = length * RATE // FPS
    path = path or OUT/"part1_preview_mix.wav"
    path.parent.mkdir(exist_ok=True,parents=True)
    source=json.loads((HERE/"master_plan.json").read_text(encoding="utf8"))["source_audio"]
    if sha256(SOURCE.read_bytes()).hexdigest()!=source["sha256"]:
        raise ValueError("Narration checksum mismatch")
    filters = () if full else ("-af",f"aresample={RATE},atrim=end_sample={samples}")
    decoded=ff("-v","error","-i",SOURCE,"-map","0:a:0","-ac",1,"-ar",RATE,
               *filters,"-f","f32le","-",
               capture_output=True).stdout
    voice=np.frombuffer(decoded,"<f4")
    if not 0 <= samples-len(voice) < (1600 if full else 1):
        raise ValueError("Unexpected narration sample count")
    bed=np.zeros((samples,2),dtype=np.float32)
    rng=np.random.default_rng(1121)

    def cue(at,dur,gain,low,high,kind,pan=0):
        start=round(at*RATE)
        end=min(samples,start+round(dur*RATE))
        if end<=start:
            return
        t=np.arange(end-start)/RATE
        u=t/dur
        phase=math.tau*t*(low+(high-low)*u/2)
        pure=np.sin(phase)
        env=np.minimum(1,t/.007)*(1-u)**1.45
        if kind in ("pluck","bass"):
            signal=(.67*pure+.22*np.sin(2.001*phase)+.10*np.sin(3.025*phase))
            env*=np.exp(-u*(1.6 if kind=="bass" else 2.9))
        elif kind in ("scratch","tick","clap","clank","kick"):
            white=rng.standard_normal(len(t))
            crisp=white-.58*np.roll(white,1)
            if kind=="tick":
                signal=.45*crisp+.20*strictly_high(phase)
                env*=np.exp(-15*u)
            elif kind=="scratch":
                signal=crisp*(.34+.66*np.sin(117*t)**4)
                env=np.sin(math.pi*u)**1.2
            elif kind=="clank":
                signal=(.33*pure+.21*np.sin(1.599*phase)+.19*np.sin(2.668*phase)+.17*np.sin(5.03*phase))*np.exp(-t*9)+.31*crisp*np.exp(-t*100)
                env=np.minimum(1,t/.002)*(1-u)**1.20
            elif kind=="clap":
                signal=(.43*crisp+.16*np.sin(phase))*(.45+.55*np.sin(486*t)**2)
                env*=np.exp(-4.3*u)
            else:
                signal=.85*np.sin(math.tau*(42*t+1.13*(1-np.exp(-t*44))))+.09*crisp*np.exp(-t*90)
                env*=np.exp(-3.5*u)
        elif kind=="buzz":
            signal=(.56*pure+.22*np.sin(3*phase)+.11*np.sin(5*phase))*(.36+.64*np.cos(45*t)**2)
        elif kind=="trombone":
            signal=.48*pure+.23*np.sin(2*phase)+.13*np.sin(3*phase)+.075*np.sin(4*phase)
            env=np.sin(math.pi*u)**.87*(.9+.1*np.sin(t*29))
        else:
            signal=.73*pure+.18*np.sin(2.03*phase)+.07*np.sin(3.3*phase)
        bed[start:end]+=(gain*signal*env)[:,None]*np.array((1-pan,1+pan))

    chords=((65.41,164.81,196.0,261.63),(58.27,146.83,174.61,233.08),
            (55.,130.81,164.81,220.),(49.,123.47,146.83,196.))
    for beat,t in enumerate(np.arange(.035,62.43 if full else length/FPS,.4545)):
        chord=chords[(beat//4)%4]
        duck=.50 if 11.40<t<13.34 or 59.15<t<61.33 else .72 if 19.90<t<20.73 else 1
        cue(t,.21,.087*duck,70,47,"kick")
        cue(t+.019,.37,.114*duck,chord[0]*(2 if beat%4==3 else 1),chord[0],"bass",.045)
        cue(t+.101,.182,.035*duck,chord[1],chord[1]*.998,"pluck",-.42)
        cue(t+.227,.112,.049*duck,chord[2]*(2 if beat%3==0 else 1),chord[2],"pluck",.43)
        cue(t+.281,.132,.036*duck,chord[3],chord[3]*.999,"pluck",.24)
        cue(t+.215,.114,.027*duck,3800,6300,"tick",.27)
        if beat%2:
            cue(t+.016,.125,.058*duck,171,291,"clap",-.22)
    for event in (
        (1.06,.19,.063,427,690,"pluck",-.25),
        (2.41,.57,.100,304,168,"scratch",.18),
        (4.94,.21,.067,479,655,"pluck",.18),
        (5.13,.22,.067,640,853,"pluck",-.13),
        (6.43,.22,.081,591,388,"plink",.22),
        (DAY1,.19,.112,683,511,"plink",-.23),
        (10.73,.28,.154,110,130,"buzz",.19),
        (11.06,.22,.102,185,151,"buzz",.17),
        (WRONG_NUMBER,.24,.122,792,543,"plink",.19),
        (12.15,.77,.118,229,144,"trombone",.09),
        (12.39,.56,.064,181,111,"trombone",-.12),
        (DAY2,.20,.126,623,840,"plink",-.18),
        (18.25,.14,.057,460,523,"plink",.18),
        (19.83,.14,.063,765,528,"plink",-.06),
        (CLANK,.59,.245,293,193,"clank",.30),
        (20.56,.27,.092,546,299,"clank",-.08),
        (21.18,.21,.067,514,461,"pluck",-.13),
    ):
        cue(*event)
    for i,t in enumerate(np.arange(15.12,21.92,.394)):
        if 19.9<t<20.71:
            continue
        cue(t,.11,.067,583+32*(i%3),285,"plink",.23*(-1)**i)
        cue(t,.103,.064,111,59,"kick",.15*(-1)**i)
    if full:
        for event in (
            (22.49,.49,.100,600,120,"scratch",-.29),  # paper cup slide
            (23.94,.16,.110,532,305,"clank",.25),
            (24.21,.21,.098,718,872,"plink"),
            (25.28,.35,.182,188,96,"clank",.26),    # tabletop strike
            (25.44,.30,.080,261,129,"scratch",.13),
            (27.72,.23,.072,535,759,"pluck",-.18),
            (29.47,.33,.076,109,66,"kick"),
            (31.00,.22,.152,713,1073,"plink",.17),   # HR approval bell
            (31.08,.48,.074,1073,1092,"plink",.14),
            (33.53,.23,.132,391,242,"clank"),
            (34.66,.35,.128,128,89,"trombone",-.35),
            (35.17,.38,.113,159,104,"trombone",.34),
            (35.74,.36,.124,131,93,"trombone",-.33),
            (36.18,.44,.101,163,117,"trombone",.39),
            (36.77,.19,.205,229,729,"plink"),       # doorway release
            (37.00,.36,.108,121,78,"kick"),
            (38.08,.42,.129,132,65,"kick"),          # three-story reveal
            (40.56,.56,.130,618,915,"trombone",.23),
            (41.02,.48,.137,904,622,"trombone",.25), # siren
            (41.27,.25,.133,281,165,"clank",.18),
            (41.49,.22,.108,255,189,"clank",.11),
            (41.70,.22,.113,310,188,"clank",.08),
            (42.04,.22,.116,338,198,"clank",.03),
            (42.31,.34,.119,521,311,"scratch",.31), # grocery bag paper
            (42.90,.17,.101,278,191,"clank"),
            (44.47,.27,.117,398,253,"scratch",-.23),
            (45.79,.36,.173,459,296,"clank",.18),
            (46.03,.36,.229,225,151,"clank",.16),   # safe lid lock
            (46.46,.09,.104,1262,1783,"tick"),
            (46.60,.09,.106,1142,1634,"tick"),
            (46.74,.09,.106,1212,1703,"tick"),
            (46.92,.47,.130,713,1011,"plink",.19),
            (47.74,.40,.212,286,163,"clank",.19),
            (48.85,.82,.093,182,87,"trombone"),
            (52.53,1.11,.137,525,1042,"scratch",.32),
            (53.10,.59,.129,712,242,"trombone",-.30), # satellite swoop
            (54.03,.18,.077,1073,849,"plink",-.26),
            (56.0,.34,.109,401,253,"scratch",.26),   # calendar turn
            (58.23,.28,.140,783,675,"plink"),
            (59.19,.32,.180,473,309,"clank",.13),
            (60.59,.64,.103,523,526,"plink",-.16),
            (60.74,.62,.116,659,661,"plink",-.02),
            (60.89,.59,.124,784,788,"plink",.15),
            (61.04,.70,.151,1047,1045,"plink",.08),  # trophy fanfare
            (62.43,.27,.120,641,119,"scratch"),      # record drop
            (63.22,.17,.024,3190,3501,"pluck",-.25),
            (63.52,.15,.021,3631,3837,"pluck",.30),
        ):
            cue(*event)
    bed[:len(voice)]+=voice[:,None]*.83
    with tempfile.TemporaryDirectory(dir=path.parent) as temp:
        raw=Path(temp)/"mix.f32"
        bed.astype("<f4").tofile(raw)
        args=("-f","f32le","-ar",RATE,"-ac",2,"-i",raw)
        norm=f"loudnorm=I={-14.3 if full else -14.0}:TP=-3.8:LRA=7"
        log=ff(*args,"-af",norm+":print_format=json","-f","null","-",capture_output=True).stderr.decode(errors="replace")
        values=json.loads(log[log.rfind("{"):log.rfind("}")+1])
        limiter=("aresample=96000,volume=0.6dB,"
                 "alimiter=limit=0.638:attack=2:release=30:level=0:latency=1,") if full else ""
        filters=(f'{norm}:measured_I={values["input_i"]}:measured_TP={values["input_tp"]}:'
                 f'measured_LRA={values["input_lra"]}:measured_thresh={values["input_thresh"]}:'
                 f'offset={values["target_offset"]}:linear=true,{limiter}'
                 f'aresample={RATE},apad,atrim=end_sample={samples}')
        ff("-v","error","-y",*args,"-af",filters,"-c:a","pcm_s24le",path)
    return path


def strictly_high(phase):
    return np.sin(phase)*.5+.45*np.sin(phase*1.31)


def proof():
    report=json.loads((OUT/"benchmark.json").read_text())
    markers=json.loads((OUT/"shots.json").read_text())
    native=OUT/report["proofs_dir"]
    with (OUT/"proof_edge.json").open("w",encoding="utf8") as log:
        status=run("python",ROOT/"scripts/ricks_metrics_gate.py","--edge-density",native,stdout=log,check=False)
    sheet=Image.new("RGB",(2210,4016),"#171725")
    mark=ImageDraw.Draw(sheet)
    font=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",42)
    for j,(name,n) in enumerate(zip(("Bedroom portrait","2 AM wrong-number reaction","Gym waddle","Day 2 scale and calendar"),markers["panels"])):
        x,y=15+j%2*1095,18+j//2*2002
        mark.text((x,y),name,fill="#f7e6d5",font=font)
        with Image.open(native/f"frame_{n:04}.png") as img:
            assert img.size==(1080,1920)
            sheet.paste(img.convert("RGB"),(x,y+63))
    sheet.save(OUT/"v6_lookdev_check.png",compress_level=4)
    raise SystemExit(status.returncode)


def mux():
    out=OUT/"part1_v01_540p.mp4"
    pending=out.with_suffix(".pending.mp4")
    for f in range(1,LENGTH+1):
        if not (OUT/f"preview_frames/frame_{f:04}.png").is_file():
            raise ValueError(f"Missing preview frame {f}")
    ff("-v","error","-y","-framerate",FPS,"-i",OUT/"preview_frames/frame_%04d.png","-i",audio(),
       "-map","0:v:0","-map","1:a:0","-c:v","libx264","-preset","fast","-crf",17,"-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","240k","-video_track_timescale",15360,"-movie_timescale",RATE,"-movflags","+faststart",pending)
    report=json.loads(run("ffprobe","-v","error","-count_frames","-show_streams","-of","json",pending,
                          capture_output=True).stdout)
    v,a=report["streams"]
    assert (v["width"],v["height"],v["avg_frame_rate"],int(v["nb_read_frames"]))==(540,960,"30/1",LENGTH)
    assert a["duration_ts"]==SAMPLES and v["start_pts"]==a["start_pts"]==0
    ff("-v","error","-xerror","-i",pending,"-map",0,"-f","null","-")
    pending.replace(out)
    (OUT/"decode.json").write_text(json.dumps(report,indent=2))
    print(out)


if __name__=="__main__":
    {"proof":proof,"mux":mux,"audio":audio}[sys.argv[-1]]()
