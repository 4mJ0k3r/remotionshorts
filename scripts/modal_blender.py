"""Modal.com serverless GPU runner for the Rick's Clips Blender 4.2 LTS pipeline.

D:\\remotionshorts stays the source of truth. Each call uploads a minimal bundle
(core kit + ONE project folder), runs Blender headless on an NVIDIA L4/T4 via
hardware EGL, downloads the outputs into renders/, and the container exits.
Nothing stays warm: no idle GPU billing.

Usage (from the repo root, after `modal token new`):

  # Hardware / dependency / EGL proof (about 2-4 GPU minutes)
  modal run scripts/modal_blender.py --mode verify
  modal run scripts/modal_blender.py --mode verify --gpu T4

  # Build / benchmark / render one project. {out} becomes the repo-relative
  # output dir (default renders/<project>), mirrored locally after the run.
  modal run scripts/modal_blender.py --mode run --project ricks_benchmark_10s/v01c \\
      --script scripts/templates/ricks_short_template.py --script-args "--out {out}/v01"

  # Second stage that needs a previous stage's outputs: upload them with --include
  modal run scripts/modal_blender.py --mode run --project ricks_benchmark_10s/v01c \\
      --script scripts/templates/ricks_short_template.py \\
      --script-args "--out {out}/v01 --render" --include renders/ricks_benchmark_10s/v01c/v01

  # A Blender-side script (runs inside blender -b --factory-startup --python ...)
  modal run scripts/modal_blender.py --mode run --project my_short/v01 \\
      --script build.py --runner blender --script-args "{out}/v01"

Rules this runner enforces
  * Uploads ONLY scripts/*.py, scripts/studio/, scripts/templates/, tests/*.py,
    requirements-blender.txt, scripts/<project>/ and any explicit --include paths.
    Never renders/ (unless explicitly --include'd), out/, node_modules/, .git/.
  * Never touches the local GPU, local Blender, or D:\\remotionshorts\\.blender_gpu.lock.
    Launchers that take the lock take a container-local copy of it.
  * Never overwrites an existing local file (versioned folders); use --overwrite.
  * Credentials live in %USERPROFILE%\\.modal.toml (outside this repo). Nothing here
    reads or writes tokens.
  * CPU-only QA stays local and free: short_qa.py, ricks_metrics_gate.py, ffprobe,
    unit tests and visual review run on the PC.

Prices below are approximate Modal list prices for estimates only. Check
https://modal.com/pricing and update RATES if they change.
"""
from __future__ import annotations

import fnmatch
import io
import json
import os
from pathlib import Path, PurePosixPath
import shlex
import subprocess
import sys
import tarfile
import threading
import time

import modal

# --------------------------------------------------------------------------- config
APP_NAME = "remotionshorts-blender"
BLENDER_VERSION = "4.2.23"
BLENDER_TARBALL = f"blender-{BLENDER_VERSION}-linux-x64.tar.xz"
BLENDER_URL = f"https://download.blender.org/release/Blender4.2/{BLENDER_TARBALL}"
BLENDER_SHA_URL = f"https://download.blender.org/release/Blender4.2/blender-{BLENDER_VERSION}.sha256"
BLENDER_DIR = "/opt/blender42"
BLENDER_EXE = f"{BLENDER_DIR}/blender"
REMOTE_ROOT = "/root/project"
GLCACHE_DIR = "/root/.cache/nvidia/GLCache"
GLCACHE_VOLUME = "remotionshorts-glcache"
DEFAULT_TIMEOUT = 900          # seconds; hard safety stop per job
CPU_CORES = 2.0                # scene authoring in Blender Python is mostly single-threaded
MEMORY_MIB = 8192
# USD per second (approx. list prices). CPU is billed per physical core, memory per GiB.
RATES = {"gpu": {"L4": 0.000222, "T4": 0.000164}, "cpu_core": 0.0000131, "mem_gib": 0.00000222}

CORE_PATTERNS = ("scripts/*.py", "scripts/studio/**", "scripts/templates/**",
                 "assets/mascot/*.py", "assets/mascot/mascot_master.blend", "assets/mascot/expressions/**",
                 "tests/*.py", "requirements-blender.txt")
NEVER_UPLOAD = {"renders", "out", "output", "node_modules", ".git", "__pycache__",
                ".venv", "backup", "refs", "remotion-tmp", ".remotion",
                "_scratch", "tmp_scratch", "docs"}
SKIP_FILES = ("*.pyc", ".blender_gpu.lock", "*.blend1", "*.log")
DOWNLOAD_EXT = {".mp4", ".mov", ".png", ".jpg", ".jpeg", ".webp", ".blend", ".json",
                ".txt", ".csv", ".md", ".wav", ".m4a", ".aac"}
GPUS = ("L4", "T4")

# --------------------------------------------------------------------------- image
EGL_VENDOR_JSON = '{"file_format_version":"1.0.0","ICD":{"library_path":"libEGL_nvidia.so.0"}}'

image = (
    modal.Image.debian_slim(python_version="3.11")
    .apt_install(
        "ffmpeg", "xz-utils", "curl", "ca-certificates",
        "libegl1", "libgl1", "libglvnd0", "libxi6", "libxfixes3", "libxrender1",
        "libxxf86vm1", "libxkbcommon0", "libsm6", "libice6", "libx11-6", "libxext6",
        "procps",
    )
    .run_commands(
        f"curl -fsSL -o /tmp/{BLENDER_TARBALL} {BLENDER_URL}",
        f"curl -fsSL -o /tmp/blender.sha256 {BLENDER_SHA_URL}",
        f"cd /tmp && grep ' {BLENDER_TARBALL}$' blender.sha256 | sha256sum -c -",
        f"mkdir -p {BLENDER_DIR} && tar -xJf /tmp/{BLENDER_TARBALL} -C {BLENDER_DIR} --strip-components=1",
        f"rm -f /tmp/{BLENDER_TARBALL} /tmp/blender.sha256",
        f"ln -sf {BLENDER_EXE} /usr/local/bin/blender",
        # Hardware EGL: route glvnd to the NVIDIA ICD, never Mesa llvmpipe/swrast.
        "mkdir -p /usr/share/glvnd/egl_vendor.d",
        f"echo '{EGL_VENDOR_JSON}' > /usr/share/glvnd/egl_vendor.d/10_nvidia.json",
        "rm -f /usr/share/glvnd/egl_vendor.d/50_mesa.json",
        f"{BLENDER_EXE} --version | head -n 1",
    )
    .pip_install("numpy>=1.24", "Pillow>=10", "scipy")  # requirements-blender.txt + scipy for ricks_metrics_gate
    .env({
        "BLENDER_EXE": BLENDER_EXE,
        "NVIDIA_DRIVER_CAPABILITIES": "all",
        "__EGL_VENDOR_LIBRARY_FILENAMES": "/usr/share/glvnd/egl_vendor.d/10_nvidia.json",
        "__GLX_VENDOR_LIBRARY_NAME": "nvidia",
        "__GL_SHADER_DISK_CACHE": "1",
        "__GL_SHADER_DISK_CACHE_PATH": GLCACHE_DIR,
        "__GL_SHADER_DISK_CACHE_SKIP_CLEANUP": "1",
        "__GL_SHADER_DISK_CACHE_SIZE": str(2 * 1024**3),
        "PYTHONUNBUFFERED": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    })
)

glcache = modal.Volume.from_name(GLCACHE_VOLUME, create_if_missing=True)
OUTPUTS_DIR = "/outputs"
OUTPUTS_VOLUME = "remotionshorts-outputs"   # survives client disconnects / `modal run --detach`
outputs = modal.Volume.from_name(OUTPUTS_VOLUME, create_if_missing=True)
app = modal.App(APP_NAME)

FUNCTION_OPTS = dict(
    image=image,
    gpu="L4",
    volumes={GLCACHE_DIR: glcache, OUTPUTS_DIR: outputs},
    timeout=DEFAULT_TIMEOUT,
    min_containers=0,            # never keep a warm GPU
    max_containers=1,            # one job at a time per run (cloud equivalent of the GPU lock)
    scaledown_window=2,          # container ends ~immediately after the call
    single_use_containers=True,  # exit after one input: billing stops when Blender exits
    cpu=CPU_CORES,
    memory=MEMORY_MIB,
)

# --------------------------------------------------------------------------- remote helpers
EEVEE_PROBE = r'''
import bpy, gpu, json, math, sys, time
out = sys.argv[sys.argv.index("--") + 1]
bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.render.engine = "BLENDER_EEVEE_NEXT"
sc.render.resolution_x, sc.render.resolution_y, sc.render.resolution_percentage = 540, 960, 100
sc.render.fps, sc.render.fps_base = 30, 1
sc.eevee.taa_render_samples = 8
sc.eevee.use_raytracing = False
sc.render.image_settings.file_format = "PNG"
world = bpy.data.worlds.new("Probe world"); sc.world = world; world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (0.05, 0.07, 0.12, 1)
bpy.ops.mesh.primitive_cube_add(size=1.2, location=(0, 0, 0))
cube = bpy.context.object
mat = bpy.data.materials.new("Probe orange"); mat.use_nodes = True
mat.node_tree.nodes["Principled BSDF"].inputs["Base Color"].default_value = (1.0, 0.45, 0.1, 1)
cube.data.materials.append(mat)
bpy.ops.object.light_add(type="SUN", location=(2, -2, 4)); bpy.context.object.data.energy = 4
bpy.ops.object.camera_add(location=(2.4, -3.4, 2.2))
cam = bpy.context.object; sc.camera = cam
from mathutils import Vector
cam.rotation_euler = (Vector((0, 0, 0)) - cam.location).to_track_quat("-Z", "Y").to_euler()
times = []
for name in ("cold", "warm1", "warm2"):
    sc.render.filepath = f"{out}/probe_{name}.png"
    t = time.perf_counter(); bpy.ops.render.render(write_still=True); times.append(time.perf_counter() - t)
info = {"seconds": dict(zip(("cold", "warm1", "warm2"), times)), "engine": sc.render.engine,
        "raytracing": sc.eevee.use_raytracing, "samples": sc.eevee.taa_render_samples,
        "resolution": [sc.render.resolution_x, sc.render.resolution_y]}
for key, fn in (("vendor", "vendor_get"), ("renderer", "renderer_get"), ("gl_version", "version_get"),
                ("backend", "backend_type_get"), ("device_type", "device_type_get")):
    try:
        info[key] = str(getattr(gpu.platform, fn)())
    except Exception as exc:  # report, never hide
        info[key] = f"ERROR {exc}"
info["blender"] = bpy.app.version_string
print("EEVEE_PROBE " + json.dumps(info))
'''


def _sh(cmd, cwd=None, env=None, timeout=600):
    """Run a command, return (code, combined output)."""
    proc = subprocess.run(cmd, shell=isinstance(cmd, str), cwd=cwd, env=env, text=True,
                          stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=timeout)
    return proc.returncode, proc.stdout


def _stream(cmd, cwd=None, env=None, prefix=""):
    """Run a command streaming its output to the Modal log; return (code, full text)."""
    proc = subprocess.Popen(cmd, cwd=cwd, env=env, text=True, bufsize=1,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    lines = []
    for line in proc.stdout:
        lines.append(line)
        print(prefix + line, end="", flush=True)
    return proc.wait(), "".join(lines)


class VramSampler:
    """Polls whole-board nvidia-smi memory.used (MiB) like shorts_preflight.benchmark()."""

    def __init__(self, period=0.1):
        self.period, self.samples, self.errors = period, [], []
        self._stop = threading.Event()
        self._thread = threading.Thread(target=self._run, daemon=True)

    def _run(self):
        while not self._stop.is_set():
            try:
                out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                                     capture_output=True, text=True, timeout=3, check=True).stdout
                self.samples.append(max(float(x) for x in out.split()))
            except Exception as exc:  # telemetry gaps are reported, not hidden
                self.errors.append(str(exc))
                if len(self.errors) > 20:
                    return
            self._stop.wait(self.period)

    def __enter__(self):
        self._thread.start()
        return self

    def __exit__(self, *exc):
        self._stop.set()
        self._thread.join(timeout=5)

    def report(self, baseline_mib=None):
        peak = max(self.samples) if self.samples else None
        return {"peak_board_mib": peak, "peak_board_gib": round(peak / 1024, 3) if peak else None,
                "baseline_board_mib": baseline_mib,
                "peak_above_baseline_mib": (peak - baseline_mib) if peak is not None and baseline_mib is not None else None,
                "samples": len(self.samples), "errors": self.errors[:3]}


def _gpu_info():
    code, out = _sh(["nvidia-smi", "--query-gpu=name,memory.total,memory.used,driver_version",
                     "--format=csv,noheader,nounits"])
    if code:
        return {"error": out.strip()}
    name, total, used, driver = [x.strip() for x in out.splitlines()[0].split(",")]
    return {"name": name, "memory_total_mib": float(total), "memory_used_mib": float(used), "driver": driver}


def _ensure_nvidia_egl():
    """Make libEGL_nvidia.so.0 resolvable for the glvnd ICD JSON. Returns diagnostics."""
    _, ldc = _sh("ldconfig -p | grep -Ei 'libEGL_nvidia|libGLX_nvidia|libnvidia-eglcore|libnvidia-glcore' || true")
    _, found = _sh("find / -xdev \\( -path /proc -o -path /sys \\) -prune -o "
                   "-name 'libEGL_nvidia.so*' -print 2>/dev/null | head -n 20")
    paths = [p for p in found.split() if p]
    if paths and "libEGL_nvidia.so.0" not in ldc:
        libdir = str(Path(paths[0]).parent)
        if not (Path(libdir) / "libEGL_nvidia.so.0").exists():
            real = sorted(paths)[-1]
            os.makedirs("/usr/local/lib/nvidia-egl", exist_ok=True)
            os.symlink(real, "/usr/local/lib/nvidia-egl/libEGL_nvidia.so.0")
            libdir = "/usr/local/lib/nvidia-egl"
        Path("/etc/ld.so.conf.d/zz-nvidia-egl.conf").write_text(libdir + "\n")
        _sh("ldconfig")
        _, ldc = _sh("ldconfig -p | grep -Ei 'libEGL_nvidia|libGLX_nvidia|libnvidia-eglcore|libnvidia-glcore' || true")
    return {"ldconfig": ldc.strip().splitlines(), "files": paths,
            "vendor_json": Path("/usr/share/glvnd/egl_vendor.d/10_nvidia.json").read_text().strip(),
            "egl_nvidia_resolvable": "libEGL_nvidia.so.0" in ldc}


def _unpack(bundle: bytes):
    os.makedirs(REMOTE_ROOT, exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(bundle), mode="r:gz") as tar:
        tar.extractall(REMOTE_ROOT, filter="data")


def _cache_stats():
    files = [p for p in Path(GLCACHE_DIR).rglob("*") if p.is_file()]
    return {"files": len(files), "mib": round(sum(p.stat().st_size for p in files) / 2**20, 2)}


def _snapshot(root):
    return {str(p.relative_to(root)).replace("\\", "/"): p.stat().st_mtime_ns
            for p in Path(root).rglob("*") if p.is_file()}


# --------------------------------------------------------------------------- remote: verify
@app.function(**FUNCTION_OPTS)
def verify(bundle: bytes) -> dict:
    t0 = time.perf_counter()
    report = {"checks": {}}
    _unpack(bundle)
    env = dict(os.environ, BLENDER_EXE=BLENDER_EXE)
    report["glcache_before"] = _cache_stats()

    # 1. Hardware + dependencies
    report["gpu"] = _gpu_info()
    report["nvidia_smi"] = _sh(["nvidia-smi"])[1]
    report["uname_m"] = _sh(["uname", "-m"])[1].strip()
    report["ffmpeg"] = _sh("ffmpeg -version | head -n 1")[1].strip()
    report["ffprobe"] = _sh("ffprobe -version | head -n 1")[1].strip()
    report["python"] = _sh(["python3", "-c", "import sys, numpy, PIL, scipy; print(sys.version.split()[0], "
                            "'numpy', numpy.__version__, 'PIL', PIL.__version__, 'scipy', scipy.__version__)"])[1].strip()
    report["blender_version"] = _sh([BLENDER_EXE, "--version"])[1].strip().splitlines()[0]
    report["egl"] = _ensure_nvidia_egl()
    print(json.dumps({k: report[k] for k in ("gpu", "uname_m", "ffmpeg", "python", "blender_version")}, indent=1))

    # 2. Unit tests (CPU; cheap, proves the uploaded kit imports on Linux)
    code, out = _stream(["python3", "-m", "unittest", "tests.test_ricks_camera", "tests.test_shorts_pipeline"],
                        cwd=REMOTE_ROOT, env=env, prefix="[unittest] ")
    report["checks"]["unittest"] = {"pass": code == 0, "tail": out.strip().splitlines()[-3:]}

    # 3. Opt-in construction smoke (takes the CONTAINER-local lock, no render)
    t = time.perf_counter()
    code, out = _stream(["python3", "tests/blender_optin_smoke.py"], cwd=REMOTE_ROOT, env=env, prefix="[smoke] ")
    report["checks"]["blender_optin_smoke"] = {"pass": code == 0 and "OPTIN_SMOKE_OK NO_RENDER" in out,
                                               "seconds": round(time.perf_counter() - t, 1),
                                               "marker": next((l for l in out.splitlines() if l.startswith("OPTIN_SMOKE_OK")), None)}

    # 4. 1-frame EEVEE Next hardware-EGL proof
    import tempfile
    from PIL import Image, ImageStat
    with tempfile.TemporaryDirectory() as tmp:
        probe = Path(tmp) / "eevee_probe.py"
        probe.write_text(EEVEE_PROBE)
        baseline = _gpu_info().get("memory_used_mib")
        t = time.perf_counter()
        with VramSampler() as vram:
            code, out = _stream([BLENDER_EXE, "-b", "--factory-startup", "--python-exit-code", "1",
                                 "--python", str(probe), "--", tmp], env=env, prefix="[eevee] ")
        wall = time.perf_counter() - t
        line = next((l for l in out.splitlines() if l.startswith("EEVEE_PROBE ")), None)
        info = json.loads(line[len("EEVEE_PROBE "):]) if line else {}
        png = Path(tmp) / "probe_warm2.png"
        stats = None
        if png.exists():
            img = Image.open(png).convert("RGB")
            st = ImageStat.Stat(img)
            stats = {"size": list(img.size), "mean_rgb": [round(x, 1) for x in st.mean],
                     "stddev_rgb": [round(x, 1) for x in st.stddev], "bytes": png.stat().st_size}
        software = any(s in (out + json.dumps(info)).lower() for s in ("llvmpipe", "swrast", "softpipe"))
        hardware = "nvidia" in info.get("vendor", "").lower() and "nvidia" in info.get("renderer", "").lower()
        non_black = bool(stats and max(stats["mean_rgb"]) > 5 and max(stats["stddev_rgb"]) > 2)
        report["checks"]["eevee_egl"] = {
            "pass": code == 0 and hardware and not software and non_black,
            "hardware_nvidia": hardware, "software_renderer_detected": software, "non_black_png": non_black,
            "probe": info, "png": stats, "blender_wall_seconds": round(wall, 2), "vram": vram.report(baseline),
        }
        if not report["checks"]["eevee_egl"]["pass"]:
            report["checks"]["eevee_egl"]["log_tail"] = out.strip().splitlines()[-40:]
    report["temp_cleaned"] = not Path(tmp).exists()

    glcache.commit()
    report["glcache_after"] = _cache_stats()
    report["function_seconds"] = round(time.perf_counter() - t0, 1)
    report["pass"] = all(c["pass"] for c in report["checks"].values())
    return report


# --------------------------------------------------------------------------- remote: run
@app.function(**FUNCTION_OPTS)
def job(bundle: bytes, runner: str, entry: str, args: list, out_rel: str, download_frames: bool, encode_frames: bool):
    t0 = time.perf_counter()
    _unpack(bundle)
    egl = _ensure_nvidia_egl()
    gpu = _gpu_info()
    print(f"[modal] GPU {gpu.get('name')} {gpu.get('memory_total_mib')} MiB | driver {gpu.get('driver')} | "
          f"EGL resolvable {egl['egl_nvidia_resolvable']}", flush=True)
    out_abs = Path(REMOTE_ROOT) / out_rel
    env = dict(os.environ, BLENDER_EXE=BLENDER_EXE, MODAL_OUT_DIR=str(out_abs), RICKS_REMOTE="modal")
    before = _snapshot(REMOTE_ROOT)
    if runner == "blender":
        cmd = [BLENDER_EXE, "-b", "--factory-startup", "--python-exit-code", "1", "--python", entry, "--", *args]
    else:
        cmd = ["python3", entry, *args]
    print("[modal] $ " + " ".join(shlex.quote(c) for c in cmd), flush=True)
    baseline = gpu.get("memory_used_mib")
    t = time.perf_counter()
    with VramSampler(period=0.2) as vram:
        code, out = _stream(cmd, cwd=REMOTE_ROOT, env=env)
    run_seconds = time.perf_counter() - t
    software = any(s in out.lower() for s in ("llvmpipe", "swrast", "softpipe"))

    # Encode new PNG sequences in */frames/ dirs (canonical H.264 yuv420p setsar=1 30 fps).
    after = _snapshot(REMOTE_ROOT)
    changed = sorted(p for p, m in after.items() if before.get(p) != m)
    encoded = []
    if encode_frames and code == 0:
        frame_dirs = sorted({str(PurePosixPath(p).parent) for p in changed
                             if PurePosixPath(p).parent.name == "frames" and p.endswith(".png")})
        for d in frame_dirs:
            dst = PurePosixPath(d).parent / "frames_h264.mp4"
            if (Path(REMOTE_ROOT) / dst).exists():
                continue
            c, o = _sh(["ffmpeg", "-v", "error", "-n", "-framerate", "30", "-pattern_type", "glob",
                        "-i", f"{REMOTE_ROOT}/{d}/*.png", "-c:v", "libx264", "-vf", "setsar=1",
                        "-pix_fmt", "yuv420p", "-r", "30", f"{REMOTE_ROOT}/{dst}"])
            _, probe = _sh(["ffprobe", "-v", "error", "-select_streams", "v:0", "-count_frames", "-show_entries",
                            "stream=width,height,sample_aspect_ratio,r_frame_rate,nb_read_frames",
                            "-of", "json", f"{REMOTE_ROOT}/{dst}"])
            encoded.append({"mp4": str(dst), "ok": c == 0, "ffprobe": probe.strip() if c == 0 else o.strip()})
        after = _snapshot(REMOTE_ROOT)
        changed = sorted(p for p, m in after.items() if before.get(p) != m)

    sent, skipped, total = [], 0, 0
    import shutil
    for rel in changed:
        p = PurePosixPath(rel)
        if p.suffix.lower() not in DOWNLOAD_EXT or rel.endswith(".blender_gpu.lock") or "__pycache__" in p.parts:
            continue
        if p.parent.name == "frames" and p.suffix.lower() == ".png" and not download_frames:
            continue
        dst = Path(OUTPUTS_DIR) / rel          # persistent copy: `modal volume get remotionshorts-outputs <rel>`
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(Path(REMOTE_ROOT) / rel, dst)
    outputs.commit()
    for rel in changed:
        p = PurePosixPath(rel)
        if p.suffix.lower() not in DOWNLOAD_EXT or rel.endswith(".blender_gpu.lock") or "__pycache__" in p.parts:
            skipped += 1
            continue
        if p.parent.name == "frames" and p.suffix.lower() == ".png" and not download_frames:
            skipped += 1
            continue
        data = (Path(REMOTE_ROOT) / rel).read_bytes()
        total += len(data)
        sent.append(rel)
        yield {"kind": "file", "path": rel, "data": data}

    glcache.commit()
    yield {"kind": "report", "report": {
        "exit_code": code, "gpu": gpu, "egl_nvidia_resolvable": egl["egl_nvidia_resolvable"],
        "software_renderer_detected": software, "run_seconds": round(run_seconds, 2),
        "function_seconds": round(time.perf_counter() - t0, 2), "vram": vram.report(baseline),
        "encoded": encoded, "files_sent": len(sent), "files_skipped": skipped, "bytes_sent": total,
        "log_tail": out.strip().splitlines()[-25:] if code else [],
    }}


# --------------------------------------------------------------------------- local side
def _repo_root() -> Path:
    here = Path(__file__).resolve()
    return next(p for p in here.parents if (p / "scripts/ricks_v2_kit.py").is_file())


def _allowed(rel: PurePosixPath) -> bool:
    return not (set(rel.parts) & NEVER_UPLOAD) and not any(fnmatch.fnmatch(rel.name, s) for s in SKIP_FILES)


def _collect(root: Path, project_dir: Path | None, includes: list[Path]) -> list[Path]:
    files = set()
    for pattern in CORE_PATTERNS:
        files.update(p for p in root.glob(pattern) if p.is_file())
    for base in ([project_dir] if project_dir else []):
        files.update(p for p in base.rglob("*") if p.is_file())
    out = [p for p in files if _allowed(PurePosixPath(p.relative_to(root).as_posix()))]
    for inc in includes:  # explicit includes may live under renders/ (previous stage outputs)
        items = [inc] if inc.is_file() else [p for p in inc.rglob("*") if p.is_file()]
        out += [p for p in items if not any(fnmatch.fnmatch(p.name, s) for s in SKIP_FILES)
                and "__pycache__" not in p.parts]
    return sorted(set(out))


def _bundle(root: Path, files: list[Path]) -> bytes:
    buf = io.BytesIO()
    with tarfile.open(fileobj=buf, mode="w:gz", compresslevel=6) as tar:
        for p in files:
            tar.add(p, arcname=p.relative_to(root).as_posix(), recursive=False)
    return buf.getvalue()


def _estimate(seconds: float, gpu: str) -> float:
    per_s = RATES["gpu"][gpu] + CPU_CORES * RATES["cpu_core"] + MEMORY_MIB / 1024 * RATES["mem_gib"]
    return seconds * per_s


def _inside(root: Path, rel: str) -> Path:
    path = (root / rel).resolve()
    if root not in path.parents and path != root:
        raise SystemExit(f"Path escapes the repo: {rel}")
    return path


@app.local_entrypoint()
def main(mode: str = "verify", gpu: str = "L4", project: str = "", script: str = "", script_args: str = "",
         out: str = "", include: str = "", runner: str = "python", download_frames: bool = False,
         encode_frames: bool = True, overwrite: bool = False, timeout: int = DEFAULT_TIMEOUT):
    gpu = gpu.upper()
    if gpu not in GPUS:
        raise SystemExit(f"--gpu must be one of {GPUS}")
    root = _repo_root()
    opts = dict(gpu=gpu, timeout=timeout)
    started = time.perf_counter()
    stamp = time.strftime("%Y%m%d_%H%M%S")

    if mode == "verify":
        files = _collect(root, None, [])
        bundle = _bundle(root, files)
        print(f"[local] Uploading {len(files)} core files ({len(bundle) / 1024:.0f} KiB gz) -> Modal {gpu}")
        report = verify.with_options(**opts).remote(bundle)
        wall = time.perf_counter() - started
        report["local_round_trip_seconds"] = round(wall, 1)
        report["estimated_cost_usd"] = round(_estimate(report["function_seconds"], gpu), 4)
        dst = root / "renders" / "modal_verify" / f"verify_{gpu}_{stamp}.json"
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(json.dumps(report, indent=2), encoding="utf-8")
        _print_verify(report, gpu, dst)
        if not report["pass"]:
            raise SystemExit(1)
        return

    if mode != "run":
        raise SystemExit("--mode must be verify or run")
    if not project or not script:
        raise SystemExit("--mode run needs --project <scripts/ subpath or assets/mascot> and --script <entry>")
    if runner not in ("python", "blender"):
        raise SystemExit("--runner must be python or blender")
    project_rel = project.replace("\\", "/").strip("/")
    if project_rel.startswith("assets/") and _inside(root, project_rel).is_dir():
        project_dir = _inside(root, project_rel)
        project_label = project_rel
    else:
        project_rel = project_rel[len("scripts/"):] if project_rel.startswith("scripts/") else project_rel
        project_dir = _inside(root, f"scripts/{project_rel}")
        project_label = f"scripts/{project_rel}"
        if not project_dir.is_dir() or project_dir == root / "scripts":
            raise SystemExit(f"Project folder not found: scripts/{project_rel}")
    entry = script.replace("\\", "/")
    entry_path = _inside(root, entry) if (root / entry).is_file() else _inside(root, f"{project_label}/{entry}")
    if not entry_path.is_file():
        raise SystemExit(f"Entry script not found: {script}")
    out_local = _inside(root, out) if out else root / "renders" / project_rel
    out_rel = out_local.relative_to(root).as_posix()
    includes = [_inside(root, i.strip()) for i in include.split(",") if i.strip()]
    for inc in includes:
        if not inc.exists():
            raise SystemExit(f"--include path not found: {inc}")

    files = _collect(root, project_dir, includes)
    if entry_path not in files:
        raise SystemExit(f"Entry script is outside the upload set: {entry_path.relative_to(root)}")
    bundle = _bundle(root, files)
    if len(bundle) > 300 * 2**20:
        raise SystemExit(f"Bundle is {len(bundle) / 2**20:.0f} MiB; trim the project or --include list")
    args = [a.replace("{out}", out_rel) for a in shlex.split(script_args, posix=True)]
    print(f"[local] Uploading {len(files)} files ({len(bundle) / 2**20:.2f} MiB gz): core kit + {project_label}"
          + (f" + {len(includes)} include(s)" if includes else ""))
    print(f"[local] Remote: {runner} {entry_path.relative_to(root).as_posix()} {' '.join(args)}  [{gpu}]")

    written, kept, report = [], [], None
    for item in job.with_options(**opts).remote_gen(bundle, runner, entry_path.relative_to(root).as_posix(),
                                                    args, out_rel, download_frames, encode_frames):
        if item["kind"] == "report":
            report = item["report"]
            continue
        dst = _inside(root, item["path"])
        if dst.exists() and not overwrite:
            kept.append(dst)
            continue
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_bytes(item["data"])
        written.append(dst)
    wall = time.perf_counter() - started
    if report is None:
        raise SystemExit("Remote job ended without a report")
    cost = _estimate(report["function_seconds"], gpu)
    print("\n================ Modal run summary ================")
    print(f"GPU            : {report['gpu'].get('name')} ({report['gpu'].get('memory_total_mib')} MiB)")
    print(f"Exit code      : {report['exit_code']}" + ("  <-- FAILED" if report["exit_code"] else ""))
    print(f"Hardware EGL   : {'yes' if report['egl_nvidia_resolvable'] and not report['software_renderer_detected'] else 'CHECK LOG'}")
    print(f"Blender wall   : {report['run_seconds']} s   container fn: {report['function_seconds']} s   local round trip: {wall:.1f} s")
    print(f"Peak VRAM      : {report['vram']['peak_board_gib']} GiB board (baseline {report['vram']['baseline_board_mib']} MiB)")
    print(f"Est. cost      : ${cost:.4f} ({gpu}, approx list price)")
    for e in report["encoded"]:
        print(f"Encoded        : {e['mp4']} ok={e['ok']}")
    print(f"Downloaded     : {len(written)} file(s), {report['bytes_sent'] / 2**20:.1f} MiB -> {out_local}")
    if kept:
        print(f"Kept existing  : {len(kept)} local file(s) not overwritten (use --overwrite)")
    if report["log_tail"]:
        print("---- remote log tail ----\n" + "\n".join(report["log_tail"]))
    summary = dict(report, local_round_trip_seconds=round(wall, 1), estimated_cost_usd=round(cost, 4),
                   written=[p.relative_to(root).as_posix() for p in written])
    summary.pop("log_tail", None)
    log_dir = out_local if out_rel.startswith("renders") else root / "renders" / "modal_runs"
    log_dir.mkdir(parents=True, exist_ok=True)
    (log_dir / f"modal_run_{stamp}.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if report["exit_code"]:
        raise SystemExit(report["exit_code"])


def _print_verify(r: dict, gpu: str, dst: Path):
    c = r["checks"]
    e = c["eevee_egl"]
    ok = lambda b: "PASS" if b else "FAIL"
    print("\n================ Modal verify summary ================")
    print(f"GPU            : {r['gpu'].get('name')} | {r['gpu'].get('memory_total_mib')} MiB | driver {r['gpu'].get('driver')}")
    print(f"Arch / tools   : {r['uname_m']} | {r['ffmpeg'][:40]} | {r['ffprobe'][:40]}")
    print(f"Python deps    : {r['python']}")
    print(f"Blender        : {r['blender_version']}")
    print(f"unittest       : {ok(c['unittest']['pass'])}  {' | '.join(c['unittest']['tail'])}")
    print(f"optin smoke    : {ok(c['blender_optin_smoke']['pass'])}  {c['blender_optin_smoke']['marker']} "
          f"({c['blender_optin_smoke']['seconds']} s)")
    p = e["probe"]
    print(f"EEVEE EGL      : {ok(e['pass'])}  vendor={p.get('vendor')!r} renderer={p.get('renderer')!r} "
          f"backend={p.get('backend')}")
    if p.get("seconds"):
        s = p["seconds"]
        print(f"Render times   : cold {s['cold']:.2f} s | warm {s['warm1']:.2f} s | warm {s['warm2']:.2f} s "
              f"({p.get('resolution')}, {p.get('samples')} samples, RT {p.get('raytracing')})")
    print(f"Peak VRAM      : {e['vram']['peak_board_mib']} MiB board (baseline {e['vram']['baseline_board_mib']} MiB)")
    print(f"PNG            : {e['png']}")
    print(f"Shader cache   : before {r['glcache_before']} -> after {r['glcache_after']}")
    print(f"Timing / cost  : container fn {r['function_seconds']} s, round trip {r['local_round_trip_seconds']} s, "
          f"~${r['estimated_cost_usd']} ({gpu})")
    print(f"OVERALL        : {ok(r['pass'])}   report -> {dst}")
