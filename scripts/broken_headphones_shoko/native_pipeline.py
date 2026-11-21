"""Run production jobs and verify the exact frame grid of native deliverables."""
import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
import subprocess
import time
from uuid import uuid4

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
RENDERS = ROOT / "renders" / HERE.name
PLAN = json.loads((HERE / "v03/master_plan.json").read_text(encoding="utf-8"))
FPS = 30
BOUNDARIES = (0, 790, 1702, 2630, 3357)
VERSIONS = ("v03", "part2_v02", "part3_v01", "part4_v01")
SCENES = ("part1_v03", *VERSIONS[1:])


def shell(*args, **kwargs):
    return subprocess.run(list(map(str, args)), cwd=ROOT, check=True, **kwargs)


@contextmanager
def gpu_lock(project):
    lock = ROOT / ".blender_gpu.lock"
    owner = uuid4().hex
    while True:
        try:
            with lock.open("x", encoding="utf-8") as stream:
                json.dump({"project": f"{HERE.name}/{project}", "pid": os.getpid(), "owner": owner}, stream)
            break
        except FileExistsError:
            time.sleep(3)
    try:
        yield
    finally:
        if json.loads(lock.read_text(encoding="utf-8"))["owner"] == owner:
            lock.unlink()


def blender(output, phase, args):
    with gpu_lock(output.name), (output / f"{phase}_native.log").open("w", encoding="utf-8") as log:
        shell(os.getenv("BLENDER_EXE", "D:/tools/Blender/4.2.23/blender.exe"),
              "-b", "--factory-startup", "--python-exit-code", 1, *args, stdout=log, stderr=subprocess.STDOUT)


def probe(video, frames, audio=False):
    info = json.loads(shell("ffprobe", "-v", "error", "-count_frames", "-show_streams",
                            "-of", "json", video, capture_output=True).stdout)
    vs, *others = info["streams"]
    assert (vs["width"], vs["height"], vs["sample_aspect_ratio"],
            vs["avg_frame_rate"], int(vs["nb_read_frames"])) == (1080, 1920, "1:1", "30/1", frames)
    assert int(vs["start_pts"]) == 0 and abs(float(vs["duration"]) - frames / FPS) < .00001
    assert len(others) == int(audio)
    if audio:
        assert others[0]["codec_type"] == "audio" and others[0]["start_pts"] == 0
    shell("ffmpeg", "-v", "error", "-xerror", "-i", video, "-map", "0", "-f", "null", "-")
    return info


def native_mp4(number, output, frames):
    folder = output / "native_frames"
    if any(not (folder / f"frame_{f:04}.png").exists() for f in range(1, frames + 1)):
        raise RuntimeError("Missing native frames")
    video = output / f"part{number}_1080p.mp4"
    pending = video.with_suffix(".pending.mp4")
    shell("ffmpeg", "-v", "error", "-nostdin", "-y", "-framerate", FPS, "-i", folder / "frame_%04d.png",
          "-frames:v", frames, "-an", "-vf", "setsar=1", "-c:v", "libx264", "-preset", "fast",
          "-crf", 16, "-bf", 0, "-pix_fmt", "yuv420p", "-video_track_timescale", 15360,
          "-movflags", "+faststart", pending)
    info = probe(pending, frames)
    pending.replace(video)
    (output / "native_decode_check.json").write_text(json.dumps(info, indent=2), encoding="utf-8")


def calibration(output, number, frames):
    from PIL import Image, ImageDraw

    source = output / json.loads((output / "benchmark.json").read_text())["native_stills_dir"]
    names = sorted(source.glob("*.png"))
    if len(names) != len(frames):
        raise RuntimeError("Incomplete native calibration")
    cell_w, cell_h = 240, 445
    sheet = Image.new("RGB", (cell_w * 4, cell_h * ((len(names) + 3) // 4)), "#151926")
    draw = ImageDraw.Draw(sheet)
    for index, (path, frame) in enumerate(zip(names, frames)):
        with Image.open(path) as still:
            still.thumbnail((cell_w - 10, cell_h - 23))
            x, y = (index % 4) * cell_w, (index // 4) * cell_h
            sheet.paste(still.convert("RGB"), (x + (cell_w - still.width) // 2, y))
        time_s = (BOUNDARIES[number - 1] + frame - 1) / FPS
        draw.text((x + 14, y + cell_h - 19), f"f{frame:04}  |  {time_s:.2f} s", fill="#e5e6ed")
    sheet.save(output / f"part{number}_calibration.png")
    with (output / "proof_edge.json").open("w", encoding="utf-8") as report:
        shell("python", ROOT / "scripts/ricks_metrics_gate.py", "--edge-density", source, stdout=report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("part", type=int, choices=range(1, 5))
    parser.add_argument("phases", nargs="+", choices=("build", "proof", "render", "encode"))
    parser.add_argument("--span", help="Optional repair range of inclusive local frames, first:last")
    args = parser.parse_args()
    number = args.part
    output = RENDERS / VERSIONS[number - 1]
    output.mkdir(parents=True, exist_ok=True)
    scene = output / f"{SCENES[number - 1]}.blend"
    duration = BOUNDARIES[number] - BOUNDARIES[number - 1]
    for phase in args.phases:
        if phase == "build":
            if number == 1:
                raise ValueError("Part 1 is frozen at the approved scene")
            builder = HERE / VERSIONS[number - 1] / "build_scene.py"
            blender(output, phase, ["--python", builder])
        elif phase in ("proof", "render"):
            frames = json.loads((output / "shot_map.json").read_text())["proof_frames"] if phase == "proof" else []
            if phase == "render":
                report = json.loads((output / "benchmark.json").read_text())
                if report["status"] != "PASS":
                    raise RuntimeError("A passed native benchmark is required")
                if number >= 3 and json.loads((output / "proof_edge.json").read_text())["status"] != "PASS":
                    raise RuntimeError("A passed edge-density gate is required")
            tail=frames if phase=="proof" else [args.span] if args.span else []
            blender(output, phase, [scene, "--python", HERE / "native_worker.py", "--", phase,
                                   output, duration, *tail])
            if phase == "proof":
                calibration(output, number, frames)
        else:
            native_mp4(number, output, duration)


if __name__ == "__main__":
    main()
