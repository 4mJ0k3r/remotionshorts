"""Build one frame-locked mix from the complete untouched narration."""
from hashlib import sha256
import json
import math
from pathlib import Path
import sys

import numpy as np

from native_pipeline import BOUNDARIES, FPS, HERE, PLAN, RENDERS, shell

sys.path[:0] = [str(HERE/"v03"),str(HERE/"part2_v01")]
from audio import part1_foley, school_bed
from part2_v01.deliver import part2_foley

RATE = 48000
COUNT = BOUNDARIES[-1]*RATE//FPS
CRASH = round(86.167*FPS)/FPS
CEMETERY = BOUNDARIES[3]/FPS
FINAL = RENDERS/"final"


def ff(*args, **kwargs):
    return shell("ffmpeg", "-hide_banner", "-nostdin", *args, **kwargs)


def read_source(clip):
    path = Path.home()/"Downloads"/clip["file"]
    if sha256(path.read_bytes()).hexdigest()!=clip["sha256"]:
        raise ValueError(f"Source checksum differs for {path.name}")
    raw = ff("-v","error","-i",path,"-map","0:a:0","-ac",1,"-ar",RATE,
             "-f","f32le","-",capture_output=True).stdout
    return np.frombuffer(raw,"<f4")


def score(cue):
    school_bed(cue, end=66.50)
    for j,t in enumerate(np.arange(57.23,57.81,.119)):
        cue(t,.215,.12 if j==0 else .083,730+j*8,708,"bell",-.22)
    cue(58.89,.24,.038,221,148,"paper",-.12)
    cue(59.97,.45,.050,515,783,"pluck",.19)
    for j,t in enumerate(np.arange(60.14,65.96,1.06)):
        cue(t,1.23,.063,48+j%2*3,54,"bus",.11*(-1)**j)
    cue(60.75,.30,.039,308,156,"air",.20)
    cue(61.80,.24,.029,255,158,"paper",-.16)
    cue(69.82,.39,.048,148,280,"paper",.06)
    cue(70.39,.38,.041,306,693,"air",-.12)
    cue(75.79,.29,.054,212,181,"paper",-.08)
    for j,t in enumerate(np.arange(78.30,80.24,.31)):
        cue(t,.126,.065,142-j%2*22,68,"step",.29*(-1)**j)
    cue(81.06,.29,.031,248,435,"air",.22)
    progression=((130.813,164.814,195.998,261.626),(97.999,146.832,195.998,246.942),
                 (110.,130.813,164.814,220.),(87.307,130.813,174.614,220.))
    for j,t in enumerate(np.arange(66.50,CRASH,.433)):
        chord = progression[(j//8)%4]
        pulse = .54+.40*min(1,(t-66.50)/16.)
        cue(t,.70,.048*pulse,chord[j%4]*2,chord[j%4]*1.999,"pluck",.17)
        if j%2==0:
            cue(t,.84,.050*pulse,chord[(j//2+1)%4]*2,chord[(j//2+1)%4]*2,"piano",-.17)
        if j%4==0:
            cue(t,1.64,.050*pulse,chord[0]*.50,chord[0]*.50,"piano",-.04)
            cue(t,1.74,.026*pulse,chord[1],chord[1],"swell",-.24)
            cue(t,1.68,.021*pulse,chord[2],chord[2],"swell",.29)
    cue(CRASH+.53,.54,.25,126,43,"crash",.07)
    cue(CRASH+.55,.42,.103,347,171,"bonk",-.19)
    cue(CEMETERY+.14,1.45,.033,90,80,"wind",-.26)
    cue(92.16,1.74,.028,106,85,"wind",.21)
    cue(98.73,2.15,.049,105,99,"wind",-.15)
    for j,t in enumerate(np.arange(94.65,100.52,.71)):
        cue(t,.126,.042,108+j%2*13,66,"step",.14*(-1)**j)
    for j,(t,note) in enumerate(((88.12,220.),(89.32,261.626),(90.64,329.628),(92.07,293.665),
                                 (93.07,261.626),(94.57,196.),(96.21,220.),(97.76,164.814),
                                 (99.34,261.626),(100.72,293.665),(102.91,329.628),(104.55,261.626),
                                 (106.28,220.),(108.12,196.),(110.24,164.814))):
        cue(t,2.06,.055 if j not in (2,10) else .042,note,note*.9999,"piano",-.13 if j%2 else .13)
        if j%3==0:
            cue(t+.125,2.00,.034,note*.5,note*.5,"piano",-.14)


def mix():
    FINAL.mkdir(exist_ok=True,parents=True)
    narration = read_source(PLAN["source_audio"])
    if abs(len(narration)-round(PLAN["audio_seconds"]*RATE))>1 or not 0<=COUNT-len(narration)<RATE//FPS:
        raise ValueError("Original narration length does not match the locked edit")
    bed = np.zeros((COUNT,2),np.float32)
    rng = np.random.default_rng(20261120)

    def cue(at,duration,gain,pitch,end,mode,pan=0):
        start=round(at*RATE)
        limit = round(CRASH*RATE) if 0<=at<CRASH else COUNT
        end_sample=min(start+round(duration*RATE),limit)
        if start>=end_sample:
            return
        time=np.arange(end_sample-start)/RATE
        u=time/duration
        phase=math.tau*time*(pitch+(end-pitch)*u*.5)
        wave=np.sin(phase)
        env=np.minimum(1,time/.009)*(1-u)**1.8
        if mode in ("pluck","piano","swell","bell"):
            wave=.68*wave+.21*np.sin(2.006*phase)+.085*np.sin(3.013*phase)
            if mode=="bell":
                wave+=.19*np.sin(2.76*phase)+.14*np.sin(4.19*phase)
            env*=np.exp(-u*(2.35 if mode=="piano" else 1.56))
            if mode=="swell":
                env=np.sin(math.pi*u)**1.65
        elif mode in ("step","air","murmur","paper","rain","wind","scratch","bonk","crash","bus"):
            noise=rng.standard_normal(len(time))
            coarse=np.convolve(noise,np.ones(11)/11,mode="same")
            bright=noise-.63*np.roll(noise,2)
            if mode=="step":
                wave=.50*wave+.46*coarse
            elif mode=="bus":
                wave=.49*wave+.18*np.sin(2.99*phase)+.27*coarse
                env=np.sin(math.pi*u)**1.23
            elif mode in ("rain","wind","murmur"):
                wave=.30*wave+.50*coarse+.10*bright
                env=np.sin(math.pi*u)**1.09
            elif mode in ("bonk","crash"):
                wave=(.51*wave+.24*np.sin(2.42*phase)+.21*np.sin(4.21*phase))*np.exp(-time*6)+.23*bright*np.exp(-time*18)
                env=np.minimum(1,time/.001)*(1-u)**1.3
            elif mode=="scratch":
                wave=(.45*bright+.23*np.sin(phase+.26*np.sin(6.8*phase))+.20*np.sign(wave))*(.42+.58*np.sin(time*77)**2)
            else:
                wave=.67*bright+.32*wave
                env=np.sin(math.pi*u)**1.4
        elif mode=="bite":
            wave=.68*wave+.23*np.sin(2.71*phase)+.09*np.sin(5.51*phase)
            env*=.54+.46*np.sin(time*170)**2
        elif mode=="zap":
            wave=.54*wave+.23*np.sign(wave)+.19*np.sin(2.39*phase)
        elif mode=="bloop":
            wave=.88*wave+.12*np.sin(2.44*phase)
        bed[start:end_sample]+=(gain*env*wave)[:,None]*np.array([1-pan,1+pan])

    part1_foley(cue)
    part2_foley(cue)
    score(cue)
    brake=read_source(PLAN["brake_effect"])
    start=round(CRASH*RATE)
    max_length=round(1.21*RATE)
    brake_in = int(np.flatnonzero(np.abs(brake)>.035)[0])
    fx=brake[brake_in:brake_in+max_length].copy()
    fx*=np.minimum(1,np.arange(len(fx))/87)*np.minimum(1,np.arange(len(fx),0,-1)/5184)
    fx*=.54/max(.05,float(np.max(np.abs(fx))))
    bed[start:start+len(fx),:]+=fx[:,None]*np.array([.83,1.0])
    # Reverb taps use only a low-passed tail of the recorded whisper, at original speed.
    a,b=round(102.48*RATE),round(103.11*RATE)
    whisper=np.convolve(narration[a:b],np.ones(19)/19,mode="same")
    for delay,pan,gain in ((.122,-.43,.055),(.204,.38,.038)):
        dest=a+round(delay*RATE)
        bed[dest:dest+len(whisper)]+=whisper[:,None]*np.array([1-pan,1+pan])*gain
    bed[:len(narration)]+=narration[:,None]*.80
    scratch=FINAL/"mix.f32"
    mix_path=FINAL/"master_audio.wav"
    bed.astype("<f4").tofile(scratch)
    input_args=("-f","f32le","-ar",RATE,"-ac",2,"-i",scratch)
    target="loudnorm=I=-14.10:TP=-3.85:LRA=9"
    try:
        stderr=ff(*input_args,"-af",target+":print_format=json","-f","null","-",capture_output=True).stderr.decode()
        measured=json.loads(stderr[stderr.rfind("{"):stderr.rfind("}")+1])
        filters=(f'{target}:measured_I={measured["input_i"]}:measured_TP={measured["input_tp"]}:'
                 f'measured_LRA={measured["input_lra"]}:measured_thresh={measured["input_thresh"]}:'
                 f'offset={measured["target_offset"]}:linear=true,aresample={RATE},volume=.35dB,apad,atrim=end_sample={COUNT}')
        ff("-v","error","-y",*input_args,"-af",filters,"-c:a","pcm_s24le",mix_path)
    finally:
        scratch.unlink()
    return mix_path


if __name__=="__main__":
    print(mix())
