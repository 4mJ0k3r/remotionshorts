"""Continue the approved score, add Part 2 Foley, and validate the preview mux."""
from hashlib import sha256
import json
import math
from pathlib import Path
import subprocess
import sys

import numpy as np

from timing import BONK, FPS, LENGTH, OUT, PLAN, RATE, SHARED, START, STOP, TAP

sys.path.insert(0,str(SHARED))
from audio import school_bed


SPF=RATE//FPS
COUNT=LENGTH*SPF


def ff(*args,capture=False):
    return subprocess.run(["ffmpeg","-hide_banner","-nostdin",*map(str,args)],capture_output=capture,check=True)


def global_time(f):
    return (START+f-1)/FPS


def part2_foley(cue):
    for j,t in enumerate(np.arange(26.68,34.25,.45)):
        cue(t,.115,.044,130-j%2*17,59,"step",(-1)**j*.27)
    for t,end in ((45.06,45.98),(45.50,46.13)):
        cue(t,end-t,.101,105,95,"rain",.21 if t<45.2 else -.36)
    for j,t in enumerate((45.27,45.72)):
        cue(t,.12,.060,121,72,"step",(-1)**j*.31)
    for event in (
        (26.40,.29,.075,544,732,"pluck",.09),
        (29.44,.21,.046,556,631,"pluck",.24),
        (31.60,.38,.042,599,314,"air",-.18),
        (global_time(BONK),.58,.215,377,231,"bonk",.15),
        (34.39,.28,.087,773,348,"pluck",-.19),
        (35.42,.22,.050,267,402,"air",.17),
        (38.43,.18,.049,228,524,"air",.24),
        (40.54,.32,.035,180,97,"air",-.29),
        (45.08,.26,.066,566,662,"pluck",.05),
        (global_time(TAP),.12,.100,610,287,"bonk",.22),
        (49.68,.42,.187,950,112,"scratch",-.20),
        (50.93,.23,.077,511,708,"pluck",.22),
        (52.14,.28,.077,626,752,"pluck",.08),
        (54.22,.16,.070,692,828,"pluck",-.16),
        (55.26,.19,.067,712,940,"pluck",.21),
        (55.64,.38,.053,374,443,"pluck",-.27),
        (56.13,.32,.059,497,441,"pluck",.21),
    ):
        cue(*event)


def mix():
    source=Path.home()/"Downloads"/PLAN["source_audio"]["file"]
    if sha256(source.read_bytes()).hexdigest()!=PLAN["source_audio"]["sha256"]:
        raise ValueError("Narration checksum mismatch")
    voice=ff("-v","error","-i",source,"-map","0:a:0","-ac",1,
             "-af",f"aresample={RATE},atrim=start_sample={START*SPF}:end_sample={STOP*SPF}",
             "-f","f32le","-",capture=True).stdout
    narration=np.frombuffer(voice,"<f4")
    if len(narration)!=COUNT:
        raise ValueError("The locked narration slice is incomplete")
    soundtrack=np.repeat(narration[:,None],2,axis=1).copy()*.78
    rng=np.random.default_rng(5839)

    def cue(at,dur,gain,hz,end,mode,pan=0):
        dest=round(at*RATE)-START*SPF
        a=max(0,dest)
        b=min(COUNT,dest+round(dur*RATE))
        if b<=a:
            return
        t=np.arange(a-dest,b-dest)/RATE
        u=t/dur
        theta=math.tau*t*(hz+(end-hz)*u*.5)
        signal=np.sin(theta)
        shape=np.minimum(1,t/.010)*(1-u)**1.8
        if mode=="pluck":
            signal=.63*signal+.25*np.sin(2.006*theta)+.12*np.sin(3.008*theta)
            shape*=np.exp(-2.1*u)
        elif mode in ("air","step","rain","scratch","bonk"):
            white=rng.standard_normal(len(t))
            grain=white-.62*np.roll(white,2)
            if mode=="step":
                signal=.45*signal+.32*np.convolve(white,(.17,.25,.31,.27),mode="same")
            elif mode=="rain":
                signal=.42*np.convolve(white,np.ones(7)/7,mode="same")+.16*grain+.09*signal
                shape=np.minimum(1,t/.045)*np.minimum(1,(1-u)*7)
            elif mode=="scratch":
                sway=(.4+.6*np.sin(math.tau*t*(11+5*u))**2)
                signal=sway*(.43*grain+.29*np.sin(theta+.28*np.sin(6.8*theta))+.20*np.sign(signal))
                shape=np.minimum(1,t/.002)*(1-u)**1.15
            elif mode=="bonk":
                signal=(.45*signal+.23*np.sin(2.42*theta)+.16*np.sin(4.21*theta))*np.exp(-t*7)+.19*grain*np.exp(-t*91)
                shape=np.minimum(1,t/.001)*(1-u)**1.3
            else:
                signal=.66*grain+.26*signal
                shape=np.sin(math.pi*u)**1.4
        soundtrack[a:b]+=(gain*shape*signal)[:,None]*np.array([1-pan,1+pan])

    school_bed(cue,end=STOP/FPS,start=START/FPS)
    part2_foley(cue)
    raw=OUT/"mix_raw.f32"
    audio=OUT/"part2_preview_mix.wav"
    soundtrack.astype("<f4").tofile(raw)
    args=("-f","f32le","-ar",RATE,"-ac",2,"-i",raw)
    loud="loudnorm=I=-14.0:TP=-3.55:LRA=7"
    try:
        scan=ff(*args,"-af",loud+":print_format=json","-f","null","-",capture=True).stderr.decode(errors="replace")
        pre=json.loads(scan[scan.rfind("{"):scan.rfind("}")+1])
        filters=(f'{loud}:measured_I={pre["input_i"]}:measured_LRA={pre["input_lra"]}:measured_TP={pre["input_tp"]}:'
                 f'measured_thresh={pre["input_thresh"]}:offset={pre["target_offset"]}:linear=true,'
                 f'aresample={RATE},apad,atrim=end_sample={COUNT}')
        ff("-v","error","-y",*args,"-af",filters,"-c:a","pcm_s24le",audio)
    finally:
        raw.unlink()
    return audio


def handoff():
    clock={"T1_END_s":START/FPS,"T2_END_s":STOP/FPS,"T2_END_exclusive_frame":STOP,
           "T2_END_exclusive_sample_at_48k":STOP*SPF,"part2_frame_count":LENGTH,
           "part2_global_frame_range_1_based":[START+1,STOP],
           "part3_first_frame_1_based":STOP+1,"fps":FPS,"transcript_last_phrase_end_s":56.72,
           "ending_phrase":"Dhinchak Pooja ke 40 songs ratt kar aa gayi!"}
    (OUT/"part2_timing.json").write_text(json.dumps(clock,indent=2))


def mux():
    frames=OUT/"preview_540p_frames"
    missing=next((i for i in range(1,LENGTH+1) if not (frames/f"frame_{i:04}.png").is_file()),None)
    if missing is not None:
        raise RuntimeError(f"Missing preview frame {missing}")
    final=OUT/"part2_v01_540p.mp4"
    pending=final.with_stem(final.stem+".pending")
    ff("-v","error","-y","-framerate",FPS,"-start_number",1,"-i",frames/"frame_%04d.png","-i",mix(),
       "-map","0:v:0","-map","1:a:0","-frames:v",LENGTH,"-c:v","libx264","-preset","fast",
       "-crf",17,"-pix_fmt","yuv420p","-c:a","aac","-b:a","240k","-video_track_timescale",15360,
       "-movie_timescale",RATE,"-movflags","+faststart",pending)
    scan=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams",
                                            "-of","json",str(pending)]))
    vi,au=scan["streams"]
    assert (vi["width"],vi["height"],vi["r_frame_rate"],int(vi["nb_read_frames"]))==(540,960,"30/1",LENGTH)
    assert vi["start_pts"]==au["start_pts"]==0 and abs(float(au["duration"])-LENGTH/FPS)<.001
    ff("-v","error","-xerror","-i",pending,"-map","0:v","-map","0:a","-f","null","-")
    pending.replace(final)
    handoff()
    (OUT/"preview_decode_check.json").write_text(json.dumps(scan,indent=2))
    print(final)


if __name__=="__main__":
    print(mix()) if "--audio-only" in sys.argv else mux()
