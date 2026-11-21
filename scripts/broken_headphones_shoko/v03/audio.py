"""Score the revised Part 1 with the locked narration and original foley."""
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess

import numpy as np

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[2]/"renders/broken_headphones_shoko/v03"
RATE=48000
COUNT=790*1600


def ff(*args,capture=False):
    return subprocess.run(["ffmpeg","-hide_banner","-nostdin",*map(str,args)],
                          check=True,capture_output=capture)


def school_bed(cue, end=26.11, *, start=0.0):
    """Play the approved arrangement on the reel's continuous beat grid."""
    chords=((130.81,164.81,196),(110,130.81,164.81),(87.31,110.,130.81),(98,123.47,146.83))
    for j,t in enumerate(np.arange(.055,end,.535)):
        if t+.535<start:
            continue
        chord=chords[j//4%4]
        brush=.62 if 2.65<t<3.66 else 1
        for k in range(3):
            freq=chord[(k+j)%3]*(1 if k==0 else 2)
            cue(t+k*.032,.41,.035*brush/(1+k*.47),freq,freq*.998,"pluck",(-1)**k*.35)
        cue(t,.45,.039*brush,chord[0]*.5,chord[0]*.497,"bass")
        cue(t+.255,.204,.027*brush,chord[(j+1)%3]*2,chord[(j+1)%3]*1.997,"pluck",.25)
        if j%2:
            cue(t+.25,.112,.020,185,80,"air",-.24)


def part1_foley(cue):
    for a,b,period,gain in ((.13,4.0,.45,.047),(14.16,17.42,.45,.053),
                            (19.30,21.03,.45,.039),(22.15,24.10,.45,.042)):
        for i,t in enumerate(np.arange(a,b,period)):
            cue(t,.112,gain,121-i%2*15,69,"step",(-1)**i*.27)
    effects=(
        (2.92,.19,.041,554,643,"pluck",.19),
        (7.27,.29,.108,514,784,"bloop",-.22),
        (8.50,.33,.067,443,311,"pluck",0),
        (10.09,.18,.088,303,175,"bite",-.28),(10.65,.19,.099,327,197,"bite",-.27),
        (11.16,.17,.092,355,189,"bite",-.28),(11.88,.25,.131,725,153,"zap",-.24),
        (12.13,.18,.078,178,67,"step",.20),(12.81,.15,.079,251,149,"bite",-.22),
        (14.54,.32,.082,191,384,"air",.29),(15.12,.26,.055,474,569,"pluck",.24),
        (17.57,.33,.067,458,702,"pluck",.16),(19.22,1.46,.048,132,147,"murmur",-.30),
        (19.40,1.59,.036,173,124,"murmur",.28),(20.18,.54,.031,210,98,"murmur",.19),
        (24.34,.25,.076,448,556,"bloop",.24),(24.73,.24,.132,581,91,"zap",.11),
        (25.24,.71,.088,476,315,"paper",-.15),(25.85,.33,.054,541,730,"pluck",.22),
    )
    for effect in effects:
        cue(*effect)


def mix():
    master=json.loads((HERE/"master_plan.json").read_text(encoding="utf-8"))
    source=Path.home()/"Downloads"/master["source_audio"]["file"]
    if sha256(source.read_bytes()).hexdigest()!=master["source_audio"]["sha256"]:
        raise ValueError("Narration checksum mismatch")
    raw=ff("-v","error","-i",source,"-map","0:a:0","-ac",1,"-ar",RATE,
           "-af",f"aresample={RATE},atrim=end_sample={COUNT}","-f","f32le","-",capture=True).stdout
    narration=np.frombuffer(raw,"<f4")
    assert len(narration)==COUNT
    soundtrack=np.repeat(narration[:,None],2,axis=1).copy()*.78
    rng=np.random.default_rng(4916)

    def cue(at,dur,volume,pitch,end,mode,pan=0):
        start=round(at*RATE)
        wave_length=min(round(dur*RATE),COUNT-start)
        if wave_length<=0:
            return
        t=np.arange(wave_length)/RATE
        u=t/dur
        theta=2*math.pi*t*(pitch+(end-pitch)*u*.5)
        signal=np.sin(theta)
        shape=np.minimum(1,t/.010)*(1-u)**1.8
        if mode=="pluck":
            signal=.63*signal+.25*np.sin(2.006*theta)+.12*np.sin(3.008*theta)
            shape*=np.exp(-2.1*u)
        elif mode in ("air","paper","step","murmur"):
            noise=rng.standard_normal(wave_length)
            if mode=="step":
                signal=.45*signal+.32*np.convolve(noise,(.17,.25,.31,.27),mode="same")
            elif mode=="murmur":
                a=.5+.5*np.sin(2*math.pi*t*3.77+1.8*np.sin(t*3))
                b=.5+.5*np.cos(2*math.pi*t*4.51+.7*np.sin(t*12))
                signal=.37*a*signal+.47*b*np.sin(1.43*theta)+.08*noise
                shape=np.sin(math.pi*u)**1.4
            else:
                texture=noise-.62*np.roll(noise,2)
                signal=.66*texture+.26*signal
                if mode=="paper":
                    signal*=.24+.76*(.5+.5*np.sin(t*math.tau*37))**1.4
                else:
                    shape=np.sin(math.pi*u)**1.4
        elif mode=="bite":
            signal=.66*signal+.27*np.sin(theta*2.71)+.07*np.sin(theta*5.51)
            shape*=.49+.51*np.sin(2*math.pi*27*t)**2
        elif mode=="zap":
            signal=.56*signal+.25*np.sign(signal)+.19*np.sin(theta*2.39)
        elif mode=="bloop":
            signal=.88*signal+.12*np.sin(2.44*theta)
        soundtrack[start:start+len(t)]+=(volume*shape*signal)[:,None]*np.array([1-pan,1+pan])

    school_bed(cue)
    part1_foley(cue)
    scratch=OUT/"part1_mix_in.f32"
    result=OUT/"part1_preview_mix.wav"
    soundtrack.astype("<f4").tofile(scratch)
    args=("-f","f32le","-ar",RATE,"-ac",2,"-i",scratch)
    # This short mix measures slightly quieter after resampling back to 48 kHz.
    loud="loudnorm=I=-13.85:TP=-3.55:LRA=7"
    try:
        scan=ff(*args,"-af",loud+":print_format=json","-f","null","-",capture=True).stderr.decode(errors="replace")
        pre=json.loads(scan[scan.rfind("{"):scan.rfind("}")+1])
        filters=(f'{loud}:measured_I={pre["input_i"]}:measured_LRA={pre["input_lra"]}:'
                 f'measured_TP={pre["input_tp"]}:measured_thresh={pre["input_thresh"]}:'
                 f'offset={pre["target_offset"]}:linear=true,aresample={RATE},apad,atrim=end_sample={COUNT}')
        ff("-v","error","-y",*args,"-af",filters,"-c:a","pcm_s24le",result)
    finally:
        scratch.unlink()
    return result


if __name__=="__main__":
    print(mix())
