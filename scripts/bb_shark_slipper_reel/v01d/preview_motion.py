"""Render the review or native master from the benchmarked v01d scene."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import uuid
import wave

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/bb_shark_slipper_reel/v01d"
BLEND=OUT/"bb_shark_slipper_v01d.blend"
AUDIO=OUT/"master_audio.wav"
PROFILE="1080p" if "--1080p" in sys.argv else "540p"
MOVIE=OUT/f"bb_shark_slipper_v01d_{PROFILE}.mp4"
FRAMES=OUT/f"frames_{PROFILE}"
LOCK=ROOT/".blender_gpu.lock"
SIZE=(1080,1920) if PROFILE=="1080p" else (540,960)
FPS=30


def sha(path):
    with path.open("rb") as file:
        return hashlib.file_digest(file,"sha256").hexdigest()


def worker():
    import bpy

    scene=bpy.context.scene
    assert scene.render.engine=="BLENDER_EEVEE_NEXT" and not scene.eevee.use_raytracing
    assert (scene.render.resolution_x,scene.render.resolution_y,scene.render.fps)==(1080,1920,FPS)
    scene.render.resolution_percentage=100 if PROFILE=="1080p" else 50
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.compression=0
    for frame in range(scene.frame_start,scene.frame_end+1):
        dest=FRAMES/f"frame_{frame:04}.png"
        if dest.exists():
            continue
        start=time.monotonic()
        scene.frame_set(frame)
        pending=FRAMES/".pending.png"
        scene.render.filepath=str(pending)
        bpy.ops.render.render(write_still=True)
        pending.replace(dest)
        print(f"MOTION_FRAME {frame:03}/{scene.frame_end} {time.monotonic()-start:.3f}s",flush=True)


def render(identity):
    FRAMES.mkdir(exist_ok=True)
    manifest=FRAMES/"identity.json"
    if manifest.exists():
        if json.loads(manifest.read_text(encoding="utf-8"))!=identity:
            raise RuntimeError("The frame cache belongs to a different scene or soundtrack.")
    else:
        with manifest.open("x",encoding="utf-8") as file:
            json.dump(identity,file,indent=2)
    owner=uuid.uuid4().hex
    while True:
        try:
            with LOCK.open("x",encoding="utf-8") as lock:
                json.dump({"project":f"bb_shark_slipper_reel/v01d_{PROFILE}","owner":owner,"pid":os.getpid()},lock)
            break
        except FileExistsError:
            print("Waiting for the current GPU owner.",flush=True)
            time.sleep(8)
    start=time.monotonic()
    memory=[]
    try:
        with (OUT/f"motion_render_{PROFILE}_{owner[:8]}.log").open("x",encoding="utf-8") as log:
            command=[os.environ.get("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),
                     "-b","--factory-startup",str(BLEND),"--python-exit-code","1",
                     "--python",str(Path(__file__).resolve()),"--"]
            if PROFILE=="1080p":
                command.append("--1080p")
            command.append("worker")
            with subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT) as child:
                try:
                    while child.poll() is None:
                        value=subprocess.check_output(
                             ["nvidia-smi","--query-gpu=memory.used","--format=csv,noheader,nounits"],
                             text=True,timeout=4,creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                        peak=max(float(line) for line in value.splitlines())/1024
                        memory.append(peak)
                        if peak>3.3:
                            raise RuntimeError(f"Sampled VRAM exceeded the 3.3 GiB budget ({peak:.3f}).")
                        time.sleep(.50)
                except BaseException:
                    if child.poll() is None:
                        child.terminate()
                        child.wait()
                    raise
                if child.returncode:
                    raise RuntimeError(f"Blender exited with code {child.returncode}. See {log.name}.")
    finally:
        if json.loads(LOCK.read_text(encoding="utf-8")).get("owner")==owner:
            LOCK.unlink()
    if not memory:
        raise RuntimeError("No VRAM samples were recorded.")
    return {"render_wall_seconds":round(time.monotonic()-start,3),
            "sampled_board_peak_gib":max(memory),"telemetry_samples":len(memory)}


def checked_frames(count, folder):
    from PIL import Image

    expected=[folder/f"frame_{i:04}.png" for i in range(1,count+1)]
    if sorted(folder.glob("frame_*.png"))!=expected:
        raise RuntimeError("The frame sequence is incomplete.")
    for path in expected:
        with Image.open(path) as frame:
            assert frame.size==SIZE
            frame.verify()


def mux(folder,candidate):
    subprocess.run(["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror",
                    "-framerate",str(FPS),"-start_number","1","-i",str(folder/"frame_%04d.png"),
                    "-i",str(AUDIO),"-map","0:v:0","-map","1:a:0",
                    "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p",
                    "-c:a","aac","-b:a","192k","-movflags","+faststart",str(candidate)],check=True)


def verify(path,identity,choreography):
    import numpy as np
    sys.path.insert(0,str(ROOT/"scripts"))
    from shorts_qa_checks import frame_differences, frozen_spans, mad_spikes

    raw=subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams","-show_format",
                                "-of","json",str(path)],text=True)
    info=json.loads(raw)
    streams=info["streams"]
    if len(streams)!=2:
        raise RuntimeError("Expected one video stream and one audio stream.")
    video=next(stream for stream in streams if stream["codec_type"]=="video")
    audio=next(stream for stream in streams if stream["codec_type"]=="audio")
    count=identity["frames"]
    assert (video["codec_name"],video["width"],video["height"],video["avg_frame_rate"],
            int(video["nb_read_frames"]))==("h264",*SIZE,"30/1",count)
    assert (audio["codec_name"],audio["channels"],int(audio["sample_rate"]))==("aac",1,44100)
    assert float(video["start_time"])==float(audio["start_time"])==0.
    assert abs(float(video["duration"])-count/FPS)<.001
    subprocess.run(["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror","-i",str(path),
                    "-map","0:v:0","-map","0:a:0","-f","null","-"],check=True)

    with wave.open(str(AUDIO),"rb") as wav:
        assert (wav.getnchannels(),wav.getsampwidth(),wav.getframerate())==(1,2,44100)
        sample_count=wav.getnframes()
        original=np.frombuffer(wav.readframes(sample_count),dtype="<i2").astype(np.float64)
    assert abs(float(audio["duration"])-sample_count/44100)<.001
    assert not original[-int(4.5*44100):].any()
    pcm=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-map","0:a:0",
                                "-f","s16le","-"])
    decoded=np.frombuffer(pcm,dtype="<i2")[:sample_count].astype(np.float64)
    assert len(decoded)==sample_count
    pad=1<<(2*sample_count-1).bit_length()
    correlation=np.fft.irfft(np.fft.rfft(decoded,n=pad)*np.fft.rfft(original,n=pad).conj(),n=pad)
    lag=int(correlation.argmax())
    lag=lag if lag<pad//2 else lag-pad
    assert lag==0,lag

    rgb=subprocess.check_output(["ffmpeg","-v","error","-i",str(path),"-map","0:v:0",
                                 "-vf","scale=144:256:flags=area","-f","rawvideo",
                                 "-pix_fmt","rgb24","-"])
    frames=np.frombuffer(rgb,np.uint8).reshape(-1,256,144,3)
    brightness=frames.mean(axis=(1,2)) @ np.array([.2126,.7152,.0722])/255
    differences=frame_differences(frames)
    flags=mad_spikes(differences,{"cuts":[f-1 for f in choreography["cut_frames_1_based"]]})
    return {"decode_check":"PASS","decoded_video_frames":len(frames),
            "duration_seconds":float(info["format"]["duration"]),
            "audio_seconds":sample_count/44100,"audio_sync_lag_samples":lag,
            "black_frames_1_based":[int(i)+1 for i in np.flatnonzero(brightness<.04)],
            "white_frames_1_based":[int(i)+1 for i in np.flatnonzero(brightness>.93)],
            "frozen_spans_zero_based":frozen_spans(differences),
            "adjacent_frame_flags_zero_based":flags}


def main():
    benchmark=json.loads((OUT/"benchmark.json").read_text(encoding="utf-8"))
    if benchmark["status"]!="PASS" or sha(BLEND)!=benchmark["blend_sha256"]:
        raise RuntimeError("The v01d delivery scene must match the passing native benchmark.")
    choreography=json.loads((OUT/"choreography.json").read_text(encoding="utf-8"))
    audit=json.loads((OUT/"audio_check.json").read_text(encoding="utf-8"))
    if sha(AUDIO)!=audit["sha256"]:
        raise RuntimeError("The audio differs from the verified aud1 → aud2 → aud3 master.")
    identity={"blend_sha256":sha(BLEND),"audio_sha256":sha(AUDIO),"resolution":list(SIZE),
              "fps":FPS,"frames":choreography["frame_count"]}
    telemetry=render(identity)
    checked_frames(identity["frames"],FRAMES)
    assert sha(BLEND)==identity["blend_sha256"] and sha(AUDIO)==identity["audio_sha256"]
    with tempfile.TemporaryDirectory(prefix="motion_mux_",dir=OUT) as scratch:
        candidate=Path(scratch)/MOVIE.name
        mux(FRAMES,candidate)
        result=verify(candidate,identity,choreography)
        if MOVIE.exists():
            raise FileExistsError(MOVIE)
        candidate.rename(MOVIE)
    result.update(identity,**telemetry,movie_sha256=sha(MOVIE),movie_size_bytes=MOVIE.stat().st_size)
    report="native_verification.json" if PROFILE=="1080p" else "motion_verification.json"
    (OUT/report).write_text(json.dumps(result,indent=2),encoding="utf-8")
    print("MOTION_EXPORT_VERIFIED",MOVIE,flush=True)


if __name__=="__main__":
    if sys.argv[-1]=="worker":
        worker()
    else:
        main()
