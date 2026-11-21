"""Assemble the five native clips and verify the continuous master."""
from fractions import Fraction
import json
from pathlib import Path
import re
import subprocess
import sys
from tempfile import TemporaryDirectory

import numpy as np

root=Path(__file__).resolve().parents[2]
base=root/"renders/padoda_billionaire"
out=base/"final"
timeline=json.loads((out/"timeline.json").read_text())
bounds=timeline["frame_boundaries"]
frames=bounds[-1]
clips=[base/"v04/padoda_part1_1080p.mp4",
       *(base/f"part{i}_v01/padoda_part{i}_1080p.mp4" for i in range(2,6))]

def run(argv):
    return subprocess.run(argv,check=True,capture_output=True,text=True)

def probe(path,*args):
    return json.loads(run(["ffprobe","-v","error",*args,"-of","json",str(path)]).stdout)

def concat_sources(work):
    manifest=work/"video_concat.ffconcat"
    lines=["ffconcat version 1.0"]
    for i,path in enumerate(clips):
        info=probe(path,"-select_streams","v:0","-show_streams")["streams"][0]
        count=bounds[i+1]-bounds[i]
        assert (info["width"],info["height"],info["r_frame_rate"],int(info["nb_frames"]))==(1080,1920,"30/1",count)
        track=work/f"video_{i+1}.mp4"
        run(["ffmpeg","-v","error","-i",str(path),"-map","0:v:0","-c:v","copy",str(track)])
        lines.append(f"file '{track.as_posix()}'")
        lines.append(f"duration {count/30:.9f}")
    manifest.write_text("\n".join(lines)+"\n",encoding="utf-8")
    return manifest

def normalize():
    source=out/"master_mix_before_loudness.wav"
    normalized=out/"padoda_master_audio.wav"
    standard="acompressor=threshold=.09:ratio=2.8:attack=.55:release=81:detection=peak,loudnorm=I=-14.3:TP=-3.35:LRA=11"
    data=run(["ffmpeg","-hide_banner","-i",str(source),"-af",standard+":print_format=json","-f","null","-"]).stderr
    measured=json.loads(re.findall(r'\{[^{}]+\}',data)[-1])
    args=":".join(f"measured_{k}={measured['input_'+m]}" for k,m in
                 (("I","i"),("TP","tp"),("LRA","lra"),("thresh","thresh")))
    chain=f"{standard}:{args}:offset={measured['target_offset']}:linear=true,aresample=44100,apad,atrim=end_sample={frames*1470}"
    run(["ffmpeg","-y","-v","error","-i",str(source),"-af",chain,"-c:a","pcm_s24le",str(normalized)])
    return normalized

def metadata():
    editorial=[(35,53,81,152,203),(85,151,199,238),(76,80,191,213,235),(157,288,309),(166,244,334,414,476)]
    # The supplementary absolute-MAD gate exempts reviewed whip moves,
    # impact shakes, spark bursts and cuts, using each part's one-based frames.
    event_spans=[
        ((35,52),(67,82),(96,116)),
        ((1,3),(119,125),(164,169),(183,198),(203,230)),
        ((63,80),(88,95)),(),
        ((400,420),(472,478)),
    ]
    cuts=sorted({*bounds[1:-1],*(bounds[i]+f-1 for i,shot in enumerate(editorial) for f in shot)})
    events=[[bounds[i]+a-1,bounds[i]+b-1] for i,events in enumerate(event_spans) for a,b in events]
    shot_starts=[0,*cuts,frames]
    content={"cuts":cuts,"planned":events,"shots":[{"id":i+1,"a":a,"b":b} for i,(a,b) in
             enumerate(zip(shot_starts,shot_starts[1:]))],
             "shadow_checks":[{"name":"Settled vault upper wall","start":1836,"end":1849,
                                "registration":"locked-camera","regions":[[.19,.055,.30,.14]],
                                "max_adjacent_luma":2}]}
    path=out/"qa_manifest.json"
    path.write_text(json.dumps(content,indent=2))
    return path

def audio_alignment(reference,movie):
    def mono(path):
        raw=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-map","0:a:0",
                                    "-ac","1","-ar","8000","-f","f32le","-"])
        return np.frombuffer(raw,"<f4")
    x,y=mono(reference),mono(movie)
    checks=[]
    for time in (1,9.5,19,29,42,53,60):
        i=int(time*8000);n=4000
        samples=x[i:i+n]
        lags=range(-32,33)
        scores=[np.corrcoef(samples,y[i+lag:i+n+lag])[0,1] for lag in lags]
        best=int(np.argmax(scores))
        assert abs(lags[best])<=1 and scores[best]>.98,(time,lags[best],scores[best])
        checks.append({"seconds":time,"lag_at_8k":lags[best],"correlation":scores[best]})
    return checks

def main():
    audio=normalize()
    pending=out/"padoda_billionaire_FINAL_1080p_pending.mp4"
    movie=out/"padoda_billionaire_FINAL_1080p.mp4"
    with TemporaryDirectory() as work:
        concat=concat_sources(Path(work))
        run(["ffmpeg","-nostdin","-v","error","-y","-f","concat","-safe","0","-i",str(concat),
             "-i",str(audio),"-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","192k",
             "-movie_timescale","44100","-movflags","+faststart",str(pending)])
    report=probe(pending,"-count_frames","-show_streams","-show_format")
    v,a=report["streams"]
    assert (v["width"],v["height"],v["r_frame_rate"],int(v["nb_read_frames"]))==(1080,1920,"30/1",frames)
    for stream in (v,a):
        assert abs(float(stream["start_time"]))<.0001 and abs(float(stream["duration"])-frames/30)<.002
    pts=probe(pending,"-select_streams","v:0","-show_frames","-show_entries","frame=best_effort_timestamp")["frames"]
    ticks=Fraction(v["time_base"])
    assert all(int(frame["best_effort_timestamp"])*ticks==Fraction(i,30) for i,frame in enumerate(pts))
    run(["ffmpeg","-nostdin","-v","error","-xerror","-i",str(pending),"-map","0:v:0","-map","0:a:0","-f","null","-"])
    loud=run(["ffmpeg","-hide_banner","-i",str(pending),"-map","0:a:0","-af","ebur128=peak=true","-f","null","-"]).stderr
    summary=loud[loud.rfind("Summary:"):]
    values={label:float(value) for label,value in re.findall(r"^\s*(I|Peak):\s+(-?[\d.]+)",summary,re.M)}
    assert abs(values["I"]+14.3)<=.35 and values["Peak"]<=-3.0,values
    pending.replace(movie)
    report["format"]["filename"]=str(movie)
    report["audio_loudness"]=values
    report["frame_pts_continuous"]=True
    report["audio_alignment"]=audio_alignment(audio,movie)
    (out/"delivery_check.json").write_text(json.dumps(report,indent=2))
    subprocess.run([sys.executable,str(root/"scripts/short_qa.py"),str(movie),str(out/"qa"),
                    str(metadata()),"--strict"],check=True)

if __name__=="__main__":
    main()
