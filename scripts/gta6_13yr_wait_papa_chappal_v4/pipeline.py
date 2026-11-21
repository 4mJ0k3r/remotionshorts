"""Lock-aware production entry point for the bedroom short."""
from __future__ import annotations

import argparse
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
OUT = ROOT / "renders" / HERE.name
SOURCE = OUT / (HERE.name + ".blend")
LOCK = ROOT / ".blender_gpu.lock"
BLENDER = Path("D:/tools/Blender/4.2.23/blender.exe")
RESOLUTION = (1080, 1920)
DEFAULT_BENCHMARK = (51, 236, 366, 549, 711, 924, 1057, 1244, 1359, 1451, 1704, 1760)


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8-sig"))


def write_json(path, value):
    temporary = path.with_name(f".{path.name}.{os.getpid()}.tmp")
    temporary.write_text(json.dumps(value, indent=2), encoding="utf-8")
    temporary.replace(path)


def source_hash():
    return hashlib.sha256(SOURCE.read_bytes()).hexdigest()


def frame_prefix(folder, count):
    from PIL import Image
    for frame in range(1, count + 1):
        path = folder / f"frame_{frame:04d}.png"
        if not path.exists():
            return frame - 1
        try:
            with Image.open(path) as image:
                if image.size != RESOLUTION or image.format != "PNG":
                    return frame - 1
                image.verify()
        except (OSError, ValueError, SyntaxError):
            return frame - 1
    return count


def run_blender(action, blender, parameters):
    token = uuid.uuid4().hex
    try:
        handle = os.open(LOCK, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError as exc:
        raise SystemExit(f"GPU lock already owned. Recheck {LOCK} when that job ends.") from exc
    with os.fdopen(handle, "w", encoding="utf-8") as lock:
        json.dump({"project": HERE.name, "owner": token, "pid": os.getpid(), "action": action}, lock)
    child = None
    peak = None
    samples = 0
    interrupted = False
    now = datetime.now().strftime("%Y%m%d-%H%M%S-%f")
    log_path = OUT / "logs" / f"{now}-{action}.log"
    command = [str(blender), "-b", "--factory-startup", "--python-exit-code", "1"]
    if action == "build":
        command += ["--python", str(HERE / "build.py"), "--", str(parameters["samples"])]
    else:
        command += [str(SOURCE), "--python", str(HERE / "worker.py"), "--", action, json.dumps(parameters)]
    print(log_path, flush=True)
    try:
        log_path.parent.mkdir(parents=True, exist_ok=True)
        with log_path.open("w", encoding="utf-8") as log:
            child = subprocess.Popen(
                command, cwd=ROOT, stdout=log, stderr=subprocess.STDOUT,
                creationflags=getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0),
            )
            while child.poll() is None:
                try:
                    gpu = subprocess.run(
                        ["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                        capture_output=True, text=True, check=True, timeout=3,
                        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
                    )
                    used = max(float(line.strip()) / 1024 for line in gpu.stdout.splitlines())
                    peak = used if peak is None else max(peak, used)
                    samples += 1
                except (subprocess.SubprocessError, ValueError, OSError):
                    pass
                time.sleep(.4)
    except KeyboardInterrupt:
        interrupted = True
    finally:
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=15)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        try:
            telemetry = {"peak_gib": peak, "sample_count": samples, "interrupted": interrupted,
                         "source_sha256": parameters.get("source_sha256"), "log": str(log_path)}
            write_json(OUT / f"board_vram_{action}.json", telemetry)
            write_json(log_path.with_suffix(".gpu.json"), telemetry)
        finally:
            if LOCK.exists() and read_json(LOCK).get("owner") == token:
                LOCK.unlink()
    if interrupted:
        raise SystemExit("Stopped this job. Its completed frames are available to validate or resume.")
    if child.returncode:
        raise SystemExit(f"Blender {action} failed. See {log_path}")


def assemble_sheets(plan, folder, full):
    from PIL import Image
    sys.path.insert(0, str(ROOT / "scripts"))
    from calibration_sheet import make_sheet

    def load(index):
        with Image.open(folder / f"frame_{index + 1:04d}.png") as frame:
            return frame.copy()

    if not full:
        output = OUT / "calibration_quick.jpg"
        make_sheet(load, plan, output)
        print(output, flush=True)
        return
    output = OUT / "calibration_sheet.jpg"
    make_sheet(load, plan, output, columns=8, cell=(148, 288))
    overview = OUT / "calibration_overview.jpg"
    manifest = read_json(OUT / "shots.json")
    indices = {(s["a"] + s["b"] - 1) // 2 for s in manifest["shots"]}
    indices.update(manifest.get("calibration_frames", ()))
    panels = [p for p in plan["panels"] if p["frame"] in indices]
    make_sheet(load, {"panels": panels, "closeups": plan["closeups"]}, overview)
    print(output, overview, sep="\n", flush=True)


def require_gates(sha, frames):
    for filename in ("visual_acceptance.json", "audit.json"):
        result = read_json(OUT / filename)
        if result.get("pass") is not True or result.get("source_sha256") != sha:
            raise SystemExit(f"Current source has not passed {filename}")
        if filename == "audit.json" and result.get("frames_checked") != frames:
            raise SystemExit(f"{filename} did not cover all {frames} frames")
    benchmark = read_json(OUT / "benchmark_gate.json")
    if benchmark.get("resolution") != list(RESOLUTION):
        raise SystemExit("The benchmark did not use native output dimensions")
    if benchmark.get("status") != "PASS" or benchmark.get("source_sha256") != sha:
        raise SystemExit("Current source has not passed the native 12-frame benchmark")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("action", choices=["build", "calibrate", "audit", "benchmark", "render", "deliver"])
    parser.add_argument("frames", nargs="*", type=int, help="Select one-based frames for calibrate or benchmark")
    parser.add_argument("--blender", type=Path, default=BLENDER)
    parser.add_argument("--samples", type=int, default=32, help="Build-time EEVEE render samples")
    parser.add_argument("--prefix", action="store_true", help="Deliver only the complete current prefix")
    args = parser.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if args.frames and args.action not in {"calibrate", "benchmark"}:
        parser.error("Frame selection applies only to calibrate or benchmark")
    if args.action == "build":
        if not 1 <= args.samples <= 512:
            parser.error("--samples must be 1 to 512")
        run_blender("build", args.blender, {"samples": args.samples})
        return

    timing = read_json(OUT / "timing.json")
    count = timing["frames"]
    sha = source_hash()
    parameters = {"source_sha256": sha}
    if args.frames and (min(args.frames) < 1 or max(args.frames) > count):
        parser.error(f"Choose frame numbers from 1 to {count}")
    if args.action == "calibrate":
        sys.path.insert(0, str(ROOT / "scripts"))
        from calibration_sheet import build_plan
        manifest = read_json(OUT / "shots.json")
        if args.frames:
            frames = sorted(set(args.frames))
            plan = {"blender_frames": frames, "closeups": [], "panels": [
                {"frame": frame - 1, "label": next(s["id"] for s in manifest["shots"] if s["a"] <= frame - 1 < s["b"])}
                for frame in frames
            ]}
        else:
            plan = build_plan(manifest, count)
        folder = OUT / "calibration" / sha[:12]
        parameters.update(frames=plan["blender_frames"], folder=str(folder))
        run_blender("calibrate", args.blender, parameters)
        assemble_sheets(plan, folder, full=not args.frames)
        write_json(OUT / "calibration.latest.json", {"source_sha256": sha, "directory": str(folder)})
    elif args.action == "benchmark":
        frames = sorted(set(args.frames or DEFAULT_BENCHMARK))
        if len(frames) != 12:
            parser.error("The benchmark requires exactly 12 distinct frames")
        parameters["frames"] = frames
        run_blender("benchmark", args.blender, parameters)
    elif args.action == "audit":
        run_blender("audit", args.blender, parameters)
    else:
        require_gates(sha, count)
        if LOCK.exists() and args.action == "deliver":
            claim = read_json(LOCK)
            if claim.get("project") == HERE.name and claim.get("action") == "render":
                raise SystemExit("Wait for this native render to finish or stop before packaging")
        folder = OUT / "native_frames" / sha
        complete = frame_prefix(folder, count)
        if args.action == "render" and complete < count:
            parameters.update(folder=str(folder), start=complete + 1)
            run_blender("render", args.blender, parameters)
        elif args.action == "deliver":
            if complete != count and not args.prefix:
                raise SystemExit(f"Only {complete} of {count} valid native frames. Complete render before delivery.")
            from deliver import package
            package(folder, complete, count, sha, timing["audio_sha256"])
        else:
            print(f"All {complete} native frames already verified: {folder}", flush=True)


if __name__ == "__main__":
    main()
