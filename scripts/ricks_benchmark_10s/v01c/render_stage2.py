"""Render the approved scene at 540p, assemble its soundtrack, and verify the MP4."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import tempfile
import time
import uuid
import wave

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "renders/ricks_benchmark_10s/v01c"
LOCK = ROOT / ".blender_gpu.lock"
MASTER = OUT / "ricks_benchmark_v01c.blend"
AUDIO = OUT / "ricks_benchmark_sfx.wav"
FINAL = OUT / "ricks_benchmark_v01c.mp4"
FRAMES = OUT / "frames_540p"
COUNT = 300
FPS = 30


def digest(path):
    with path.open("rb") as stream:
        return hashlib.file_digest(stream,"sha256").hexdigest()


def render():
    report = json.loads((OUT / "benchmark.json").read_text(encoding="utf-8"))
    master_hash = digest(MASTER)
    if report["status"] != "PASS" or master_hash != report["blend_sha256"]:
        raise RuntimeError("Approved Blender project does not match the passing benchmark.")
    with wave.open(str(AUDIO),"rb") as audio:
        if audio.getnframes()*FPS != audio.getframerate()*COUNT:
            raise RuntimeError("Soundtrack duration must match the frame range exactly.")
    identity = {"blend_sha256":master_hash,"audio_sha256":digest(AUDIO),
                "resolution":[540,960],"fps":FPS,"frames":COUNT}
    FRAMES.mkdir(exist_ok=True)
    identity_file = FRAMES / "identity.json"
    if identity_file.exists():
        if json.loads(identity_file.read_text(encoding="utf-8")) != identity:
            raise RuntimeError("Cached frames belong to different source or output settings.")
    else:
        with identity_file.open("x",encoding="utf-8") as file:
            json.dump(identity,file,indent=2)

    owner = uuid.uuid4().hex
    while True:
        try:
            with LOCK.open("x",encoding="utf-8") as file:
                json.dump({"project":"ricks_benchmark_10s/v01c","pid":os.getpid(),"owner":owner},file)
            break
        except FileExistsError:
            print("Waiting for the current GPU owner.",flush=True)
            time.sleep(10)
    memory = []
    started = time.monotonic()
    try:
        with (OUT / ("stage2_render_"+owner[:8]+".log")).open("x",encoding="utf-8") as log:
            command = [os.environ.get("BLENDER_EXE","D:/tools/Blender/4.2.23/blender.exe"),
                       "-b","--factory-startup",str(MASTER),"--python-exit-code","1",
                       "--python",str(Path(__file__).resolve()),"--","worker"]
            with subprocess.Popen(command,cwd=ROOT,stdout=log,stderr=subprocess.STDOUT) as child:
                while child.poll() is None:
                    result = subprocess.run(
                        ["nvidia-smi","--query-gpu=memory.used","--format=csv,noheader,nounits"],
                        capture_output=True,text=True,timeout=4,check=True,
                        creationflags=getattr(subprocess,"CREATE_NO_WINDOW",0))
                    memory.append(max(float(row) for row in result.stdout.splitlines())/1024)
                    time.sleep(.45)
                if child.returncode:
                    raise RuntimeError(f"Blender exited with code {child.returncode}. See {log.name}.")
    finally:
        if json.loads(LOCK.read_text(encoding="utf-8"))["owner"] == owner:
            LOCK.unlink()
    identity.update(render_wall_seconds=round(time.monotonic()-started,3),
                    sampled_board_peak_gib=max(memory),telemetry_samples=len(memory))
    if identity["sampled_board_peak_gib"] > 3.3:
        raise RuntimeError("Render exceeded the shared sampled VRAM budget.")
    return identity


def worker():
    import bpy
    scene = bpy.context.scene
    assert scene.render.engine == "BLENDER_EEVEE_NEXT" and not scene.eevee.use_raytracing
    assert (scene.render.resolution_x,scene.render.resolution_y) == (1080,1920)
    assert (scene.frame_start,scene.frame_end,scene.render.fps,scene.render.fps_base) == (1,COUNT,FPS,1)
    scene.render.resolution_percentage = 50
    scene.render.image_settings.file_format = "PNG"
    for frame in range(1,COUNT+1):
        final = FRAMES / f"frame_{frame:04d}.png"
        if not final.exists():
            start = time.monotonic()
            scene.frame_set(frame)
            pending = FRAMES / ".frame_pending.png"
            scene.render.filepath = str(pending)
            bpy.ops.render.render(write_still=True)
            pending.replace(final)
            print(f"STAGE2_FRAME {frame:03}/{COUNT} {time.monotonic()-start:.3f}s",flush=True)


def verify_movie(candidate):
    probe = json.loads(subprocess.check_output(
        ["ffprobe","-v","error","-count_frames","-show_streams","-show_format","-of","json",str(candidate)],
        text=True))
    video,audio = probe["streams"]
    assert (video["codec_name"],video["width"],video["height"],video["avg_frame_rate"],
            int(video["nb_read_frames"])) == ("h264",540,960,"30/1",300)
    assert (audio["codec_name"],audio["sample_rate"],audio["channels"]) == ("aac","48000",2)
    for stream in (video,audio):
        assert float(stream["start_time"]) == 0 and float(stream["duration"]) == 10
    assert float(probe["format"]["duration"]) == 10
    subprocess.run(["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror","-i",str(candidate),
                    "-map","0:v:0","-map","0:a:0","-f","null","-"],check=True)
    return probe


def main():
    from PIL import Image

    stats = render()
    names = sorted(FRAMES.glob("frame_*.png"))
    if names != [FRAMES / f"frame_{frame:04d}.png" for frame in range(1,COUNT+1)]:
        raise RuntimeError("The contiguous 300-frame cache is incomplete.")
    for path in names:
        with Image.open(path) as frame:
            assert frame.size == (540,960)
            frame.verify()
    if digest(AUDIO) != stats["audio_sha256"] or digest(MASTER) != stats["blend_sha256"]:
        raise RuntimeError("An approved input changed during rendering.")
    with tempfile.TemporaryDirectory(prefix="mux_",dir=OUT) as scratch:
        candidate = Path(scratch) / FINAL.name
        subprocess.run(["ffmpeg","-hide_banner","-nostdin","-v","error","-xerror",
                        "-framerate","30","-start_number","1","-i",str(FRAMES/"frame_%04d.png"),
                        "-i",str(AUDIO),"-map","0:v:0","-map","1:a:0",
                        "-c:v","libx264","-preset","medium","-crf","16","-pix_fmt","yuv420p",
                        "-c:a","aac","-b:a","256k","-movflags","+faststart",str(candidate)],check=True)
        verify_movie(candidate)
        if FINAL.exists():
            raise FileExistsError(FINAL)
        candidate.rename(FINAL)
    stats.update(movie_sha256=digest(FINAL),duration_seconds=10.0,decoded_video_frames=300,
                 audio_codec="aac",video_codec="h264",decode_check="PASS")
    (OUT/"stage2_verification.json").write_text(json.dumps(stats,indent=2),encoding="utf-8")
    print(f"VERIFIED {FINAL}",flush=True)


if __name__ == "__main__":
    import sys

    if sys.argv[-1] == "worker":
        worker()
    else:
        main()
