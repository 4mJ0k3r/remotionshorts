"""Mix the unbroken narration and assemble the four native v02 parts."""
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

from production import BASE, BOUNDS, HERE

RATE=48000
TARGET=BASE/"pokhran_1998_v02_FINAL_1080p.mp4"


def ff(*args,capture=False):
    return subprocess.run(["ffmpeg","-hide_banner","-nostdin",*map(str,args)],capture_output=capture,check=True)


def read_pcm(source,channels):
    output=ff("-v","error","-i",source,"-map","0:a:0","-ac",channels,"-ar",RATE,
              "-f","f32le","-",capture=True).stdout
    return np.frombuffer(output,"<f4").reshape(-1,channels)


def soundtrack():
    plan=json.loads((HERE.parent/"v01b/master_plan.json").read_text(encoding="utf-8"))
    source=Path.home()/"Downloads"/plan["source_audio"]["file"]
    assert sha256(source.read_bytes()).hexdigest()==plan["source_audio"]["sha256"]
    original=read_pcm(source,1)[:,0]
    total=BOUNDS[-1]*1600
    intro=BOUNDS[1]*1600
    assert total-1600 < len(original)<=total
    approved=read_pcm(BASE.parent/"v02b/hook_preview_mix.wav",2)
    assert len(approved)==intro
    voice=original[:intro]
    gain=np.dot(voice,approved.mean(axis=1))/np.dot(voice,voice)
    mix=np.zeros((total,2),dtype=np.float32)
    mix[:len(original)]=original[:,None]*gain
    # These first samples already contain the same narration on the same clock.
    mix[:intro]=approved
    rng=np.random.default_rng(6258)

    def sound(at,duration,amp,low,high,texture,pan=0):
        start=round(at*RATE)
        t=np.arange(min(round(duration*RATE),total-start))/RATE
        u=t/duration
        theta=2*math.pi*t*(low+(high-low)*u*.5)
        note=np.sin(theta)
        attack=np.minimum(1,t/(.003 if texture in ("snap","metal") else .045))
        envelope=attack*(1-u)**1.85
        if texture in ("snap","wind","metal"):
            white=rng.standard_normal(len(t))
            fleck=white-np.roll(white,2)*.64
        if texture=="snap":
            tone=.72*fleck+.31*note
        elif texture=="wind":
            tone=.65*fleck+.28*note
            envelope=np.sin(np.pi*u)**2
        elif texture=="metal":
            tone=.55*note+.18*np.sin(2.64*theta)+.17*np.sin(4.58*theta)+.15*fleck
        elif texture=="alarm":
            tone=.72*note+.16*np.sin(3*theta)+.10*np.sin(5*theta)
            envelope=attack*np.minimum(1,(1-u)*5)
        else:
            tone=.86*note+.18*np.sin(2.08*theta)
        mix[start:start+len(t)]+=(amp*envelope*tone)[:,None]*np.array([1-pan,1+pan])

    for i,beat in enumerate(np.arange(14.87,52.6,.39)):
        tone=(49,49,58.27,46.25)[i%4]
        scene_gain=.037+.017*(beat>=25)+.018*(beat>=40)
        sound(beat,.54,scene_gain,tone,tone-.41,"bass",(-1)**i*.12)
        sound(beat+.195,.22,scene_gain*.36,2*tone,2*tone-.42,"bass",(-1)**i*.31)
    cues=[
        (15.26,.27,.095,690,804,"metal",-.28),(16.38,.106,.083,276,194,"snap",.23),
        (17.46,.24,.10,284,74,"wind",.18),(18.14,.20,.12,389,607,"metal",-.18),
        (19.40,.28,.10,97,511,"wind",.12),(19.60,.16,.19,217,66,"snap",-.28),
        (19.87,.16,.18,246,88,"snap",.28),(20.20,.23,.11,472,388,"metal",.21),
        (23.80,.22,.15,241,65,"wind",-.18),(25.24,.44,.115,685,742,"alarm",.14),
        (28.60,.23,.11,188,90,"metal",-.17),(32.22,.28,.10,593,710,"metal",.17),
        (33.62,.72,.088,417,235,"wind",-.22),(34.36,.28,.096,607,812,"metal",.18),
        (35.60,.27,.09,303,96,"wind",-.13),(36.10,.15,.087,121,74,"snap",-.25),
        (36.65,.15,.095,123,76,"snap",-.16),(37.17,.15,.092,107,67,"snap",.03),
        (37.72,.16,.091,144,78,"snap",.13),(38.08,.30,.14,386,112,"wind",.11),
        (39.73,.18,.222,242,68,"snap",.12),(39.74,.24,.14,286,173,"metal",.24),
        (40.30,.16,.18,223,81,"snap",.14),(41.04,.44,.108,218,65,"wind",-.16),
        (41.76,.28,.145,206,77,"metal",-.28),(42.80,.26,.145,209,122,"metal",.24),
        (45.20,.78,.095,179,123,"wind",-.31),(45.90,.38,.084,235,175,"wind",.16),
        (50.93,1.61,.238,69,24,"bass",0),(51.06,1.5,.132,97,38,"wind",.03),
        (52.05,.24,.154,179,44,"metal",0),(52.32,.32,.18,696,869,"alarm",-.25),
        (52.68,.38,.17,788,639,"alarm",.21),(53.23,.31,.194,389,120,"metal",.17),
        (53.29,.25,.111,194,98,"snap",.20),(53.68,.37,.14,730,570,"alarm",-.12),
        (54.17,.37,.124,773,641,"alarm",.17)
    ]
    for cue in cues:
        sound(*cue)
    for at in np.arange(43.22,45.04,.24):
        sound(at,.19,.122,206,145,"metal",.24)
    for at in np.arange(46.54,49.65,.59):
        sound(at,.48,.105,186,71,"wind",-.30)
        sound(at+.22,.36,.091,159,78,"wind",.27)
    scratch=BASE/"master_mix_raw.f32"
    audio=BASE/"hook_and_continuation_master_mix.wav"
    mix.astype("<f4").tofile(scratch)
    try:
        args=("-f","f32le","-ar",RATE,"-ac",2,"-i",scratch)
        loud="loudnorm=I=-14.3:TP=-3.45:LRA=7"
        scan=ff(*args,"-af",loud+":print_format=json","-f","null","-",capture=True).stderr.decode(errors="replace")
        measured=json.loads(scan[scan.rfind("{"):scan.rfind("}")+1])
        filters=(f'{loud}:measured_I={measured["input_i"]}:measured_LRA={measured["input_lra"]}:'
                 f'measured_TP={measured["input_tp"]}:measured_thresh={measured["input_thresh"]}:'
                 f'offset={measured["target_offset"]}:linear=true,aresample={RATE},apad,atrim=end_sample={total}')
        ff("-v","error","-y",*args,"-af",filters,"-c:a","pcm_s24le",audio)
        assert len(read_pcm(audio,2))==total
    finally:
        scratch.unlink()
    return audio


def main():
    parts=[BASE/f"pokhran_part{i}_v02_1080p.mp4" for i in (1,2,3,4)]
    if not all(path.is_file() for path in parts):
        raise ValueError("The four native parts must be encoded first.")
    audio=soundtrack()
    listing=BASE/"native_concat.ffconcat"
    listing.write_text("ffconcat version 1.0\n"+"".join(f"file '{p.as_posix()}'\n" for p in parts),encoding="utf-8")
    pending=TARGET.with_stem(TARGET.stem+".pending")
    ff("-v","error","-y","-safe",0,"-f","concat","-i",listing,"-i",audio,
       "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","256k",
       "-video_track_timescale",15360,"-movie_timescale",RATE,"-movflags","+faststart",pending)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams",
                                               "-show_format","-of","json",str(pending)],text=True))
    video, sound=probe["streams"]
    assert (video["width"],video["height"],video["r_frame_rate"],int(video["nb_read_frames"]))==(1080,1920,"30/1",1652)
    assert sound["codec_type"]=="audio" and video["start_pts"]==sound["start_pts"]==0
    assert abs(float(sound["duration"])-1652/30)<.001
    pts=json.loads(subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_frames",
                   "-show_entries","frame=best_effort_timestamp","-of","json",str(pending)],text=True))
    assert [f["best_effort_timestamp"] for f in pts["frames"]]==list(range(0,1652*512,512))
    ff("-v","error","-xerror","-i",pending,"-map","0:v","-map","0:a","-f","null","-")
    pending.replace(TARGET)
    (BASE/"master_decode_check.json").write_text(json.dumps(probe,indent=2))
    print(TARGET)


if __name__=="__main__":
    print(soundtrack()) if "--audio-only" in sys.argv else main()
