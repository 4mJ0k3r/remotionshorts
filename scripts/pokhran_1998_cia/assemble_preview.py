"""Mix the continuous narration and assemble the exact four preview ranges."""
from hashlib import sha256
import json
import math
from pathlib import Path
import re
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
FPS = 30
RATE = 48000
SOURCE = HERE / "v01b/master_plan.json"
PROJECT = ROOT / "renders/pokhran_1998_cia"


def ffmpeg(*args, capture=False):
    return subprocess.run(["ffmpeg", "-hide_banner", "-nostdin", *map(str, args)],
                          capture_output=capture, check=True)


def score(original, audio, frames):
    narration = np.frombuffer(ffmpeg("-v", "error", "-i", original, "-map", "0:a:0",
                              "-ac", 1, "-ar", RATE, "-f", "f32le", "-", capture=True).stdout, "<f4")
    count = frames * (RATE // FPS)
    if len(narration) > count or count-len(narration) >= RATE // FPS:
        raise ValueError("Narration and locked video boundaries disagree.")
    mix = np.zeros((count, 2), dtype=np.float32)
    mix[:len(narration)] = narration[:, None] * .80
    rng = np.random.default_rng(927)

    def sound(at, duration, amplitude, mode, low, high, pan=0):
        initial = round(at * RATE)
        length = min(round(duration * RATE), count-initial)
        t = np.arange(length)/RATE
        u = t/duration
        phase = 2*math.pi*(low*t + .5*(high-low)*t*u)
        envelope = np.minimum(1,t/.013) * (1-u)**2
        signal = np.sin(phase)
        if mode == "noise":
            white = rng.standard_normal(length)
            signal = .77*(white-np.roll(white,1))+.23*signal
        elif mode == "rumble":
            signal = .83*signal+.17*np.sin(2.41*phase)
        elif mode == "bell":
            signal = .66*signal+.22*np.sin(2.53*phase)+.12*np.sin(4.11*phase)
        mix[initial:initial+length] += (signal*envelope*amplitude)[:, None]*np.array([1-pan,1+pan])

    for beat in np.arange(16.1,53.00,.49):
        motif = [55,65.41,73.42,58.27][int(round((beat-16.1)/.49))%4]
        volume = .019 if beat<28.6 else .025
        sound(beat,.76,volume,"rumble",motif,motif-.18)
        if 29<beat<41:
            sound(beat+.245,.15,.008,"bell",3*motif,3*motif,-.2)
    cues = [
        (3.86,.45,.027,"rumble",94,167,-.30), (5.65,.18,.035,"bell",390,520,.43),
        (7.87,.44,.032,"rumble",175,93,0), (12.32,.18,.036,"bell",720,380,-.20),
        (19.52,.28,.033,"bell",450,625,-.18), (22.87,.16,.045,"noise",187,70,.40),
        (25.23,.34,.042,"bell",752,553,.22), (32.49,.43,.029,"noise",290,210,-.33),
        (34.04,.22,.023,"bell",423,490,.26), (39.73,.17,.083,"noise",300,79,.22),
        (39.81,.58,.020,"bell",420,780,.48), (41.06,.54,.029,"rumble",135,74,-.15),
        (43.28,.48,.042,"bell",177,117,.30), (44.06,.24,.041,"bell",230,132,.15),
        (45.86,1.66,.018,"noise",100,56,-.28), (47.48,.65,.035,"noise",165,100,.23),
        (48.49,.51,.031,"noise",102,73,-.19), (49.32,.54,.025,"noise",130,81,.25),
        (50.95,1.75,.105,"rumble",71,29,0), (51.56,.51,.072,"noise",107,52,0),
        (52.61,.48,.045,"bell",230,562,-.17), (53.23,.22,.053,"bell",610,730,.18),
        (53.55,.21,.066,"bell",267,128,.31), (53.83,.35,.034,"bell",660,470,-.20),
    ]
    for cue in cues:
        sound(*cue)
    raw = audio.with_suffix(".f32")
    mix.astype("<f4").tofile(raw)
    settings = ("-f", "f32le", "-ar", str(RATE), "-ac", "2", "-i", str(raw))
    try:
        measurement = ffmpeg(*settings, "-af", "ebur128=peak=true", "-f", "null", "-", capture=True)
        summary = measurement.stderr.decode(errors="replace").rsplit("Summary:",1)[-1]
        integrated = float(re.search(r"I:\s+(-?\d+(?:\.\d+)?) LUFS", summary)[1])
        peak = float(re.search(r"Peak:\s+(-?\d+(?:\.\d+)?) dBFS", summary)[1])
        gain = min(-14.3-integrated, -3.25-peak)
        ffmpeg("-v", "error", "-y", *settings, "-af", f"volume={gain:.4f}dB",
               "-c:a", "pcm_s24le", audio)
    finally:
        raw.unlink()


def main():
    plan = json.loads(SOURCE.read_text(encoding="utf-8"))
    original = Path(sys.argv[1]) if len(sys.argv)>1 else Path.home()/"Downloads"/plan["source_audio"]["file"]
    if sha256(original.read_bytes()).hexdigest() != plan["source_audio"]["sha256"]:
        raise ValueError("The supplied narration differs from the approved master.")
    boundaries = plan["part_boundaries_frames"]
    ranges = [b-a for a,b in zip(boundaries,boundaries[1:])]
    folders = [PROJECT/"v01b", *(PROJECT/f"part{i}_v01" for i in (2,3,4))]
    for folder,length in zip(folders,ranges):
        frames = folder/"preview_540p_frames"
        missing = [i for i in range(1,length+1) if not (frames/f"frame_{i:04d}.png").is_file()]
        if missing:
            raise ValueError(f"Missing {len(missing)} frame(s) in {folder}: {missing[:10]}")
    final = PROJECT/"final"
    final.mkdir(exist_ok=True)
    audio = final/"pokhran_preview_mix.wav"
    score(original, audio, boundaries[-1])
    chunks = []
    for index,(folder,length) in enumerate(zip(folders,ranges),1):
        chunk = folder/f"pokhran_part{index}_540p_video.mp4"
        ffmpeg("-loglevel","error","-y","-framerate",FPS,"-start_number",1,
               "-i",folder/"preview_540p_frames/frame_%04d.png","-frames:v",length,
               "-an","-c:v","libx264","-threads","4","-preset","fast","-crf","18",
               "-pix_fmt","yuv420p","-video_track_timescale",15360,"-movie_timescale",RATE,chunk)
        chunks.append(chunk)
    listing = final/"preview_concat.ffconcat"
    listing.write_text("ffconcat version 1.0\n"+"".join(f"file '{p.as_posix()}'\n" for p in chunks),encoding="utf-8")
    target = final/"pokhran_1998_FULL_540p_PREVIEW.mp4"
    pending = final/"pokhran_1998_FULL_540p_PREVIEW.pending.mp4"
    ffmpeg("-loglevel","error","-y","-safe",0,"-f","concat","-i",listing,"-i",audio,
           "-map","0:v:0","-map","1:a:0","-c:v","copy","-c:a","aac","-b:a","256k",
           "-video_track_timescale",15360,"-movie_timescale",RATE,"-movflags","+faststart",pending)
    scan = json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams",
                                               "-show_format","-of","json",str(pending)],text=True))
    video, audio_stream = scan["streams"]
    assert (video["width"],video["height"],video["r_frame_rate"],int(video["nb_read_frames"])) == (540,960,"30/1",boundaries[-1])
    assert audio_stream["codec_type"] == "audio" and video["start_pts"] == audio_stream["start_pts"] == 0
    assert abs(float(audio_stream["duration"])-float(video["duration"])) < .001
    timeline = json.loads(subprocess.check_output([
        "ffprobe","-v","error","-select_streams","v:0","-show_frames",
        "-show_entries","frame=best_effort_timestamp","-of","json",str(pending)],text=True))
    stamps = [frame["best_effort_timestamp"] for frame in timeline["frames"]]
    assert stamps == list(range(0,boundaries[-1]*512,512)), "The 30 fps sequence has a gap or jitter."
    ffmpeg("-v","error","-xerror","-i",pending,"-map","0:v:0","-map","0:a:0","-f","null","-")
    pending.replace(target)
    (final/"preview_streams.json").write_text(json.dumps(scan,indent=2),encoding="utf-8")
    cuts = [116, 278, 378]
    for offset, folder in zip(boundaries[1:], folders[1:]):
        cuts.extend(offset+f-1 for f in json.loads((folder/"shot_map.json").read_text())["cuts"])
    shots = [{"id":i,"a":a,"b":b} for i,(a,b) in enumerate(zip((0,*cuts), (*cuts,boundaries[-1])),1)]
    final_cuts = json.loads((folders[-1]/"shot_map.json").read_text())["cuts"]
    impact_start, impact_stop = (boundaries[-2]+frame-1 for frame in final_cuts[-2:])
    metadata = {"cuts":cuts,"shots":shots,"planned":[[impact_start,impact_stop-1]]}
    (final/"preview_shots.json").write_text(json.dumps(metadata,indent=2),encoding="utf-8")
    print(target)


if __name__ == "__main__":
    main()
