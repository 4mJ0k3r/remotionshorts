"""Isolated headless Blender runner for caveman_toilet with the shared GPU mutex.

Isolation: own project folders, own BLENDER_USER_RESOURCES profile,
--factory-startup so the shared GUI addons (including the MCP socket server on
port 9876) never load. The live GUI is never contacted.

Mutex: D:\\remotionshorts\\.blender_gpu.lock is shared with the other agents.
Busy means the lock exists, a HEADLESS `blender -b` process is alive, or the GPU
is genuinely loaded. An idle GUI is deliberately not a blocker. The lock is only
ever removed when the owner token inside matches this run. A stale FOREIGN lock
older than STALE_MINUTES is never deleted here -- exit 3 and ask the user.
"""
import argparse
import json
import os
import subprocess
import sys
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PROJECT = "caveman_toilet"
OUT = ROOT / "renders" / PROJECT
SCRIPTS = ROOT / "scripts" / PROJECT
LOCK = ROOT / ".blender_gpu.lock"
PAUSE = OUT / ".gpu_pause"
USER_RES = OUT / ".blender_user"
BLENDER = OUT / ".blender_cli" / "blender.exe"
POLL_S = 15
VRAM_BUSY_MIB = 2600
UTIL_BUSY_PCT = 70
STALE_MINUTES = 25


def log(msg):
    print(f"[{datetime.now().strftime('%H:%M:%S')}] {msg}", flush=True)


def gpu_state():
    try:
        r = subprocess.run(
            ["nvidia-smi", "--query-gpu=memory.used,utilization.gpu",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=20)
        mem, util = r.stdout.strip().splitlines()[0].split(",")
        return int(mem.strip()), int(util.strip())
    except Exception:
        return -1, -1


def headless_blender_pids():
    """Only `blender -b` processes count; an idle GUI must not block the queue."""
    ps = ("Get-CimInstance Win32_Process -Filter \"Name='blender.exe'\" | "
          "ForEach-Object { \"$($_.ProcessId)|$($_.CommandLine)\" }")
    try:
        r = subprocess.run(["powershell", "-NoProfile", "-Command", ps],
                           capture_output=True, text=True, timeout=60)
    except Exception:
        return []
    pids = []
    for line in r.stdout.splitlines():
        if "|" not in line:
            continue
        pid, cmd = line.split("|", 1)
        if "-b" in cmd.split() or " -b " in cmd or cmd.strip().endswith("-b"):
            try:
                pids.append(int(pid.strip()))
            except ValueError:
                pass
    return pids


def read_lock():
    try:
        return json.loads(LOCK.read_text(encoding="utf-8"))
    except Exception:
        return None


def busy_reason():
    if LOCK.exists():
        rec = read_lock() or {}
        return f"lock held by project={rec.get('project')} phase={rec.get('phase')}"
    pids = headless_blender_pids()
    if pids:
        return f"headless blender running pids={pids}"
    mem, util = gpu_state()
    if mem > VRAM_BUSY_MIB or util > UTIL_BUSY_PCT:
        return f"GPU loaded mem={mem}MiB util={util}%"
    return None


def claim(phase):
    owner = uuid.uuid4().hex
    waited = 0
    while True:
        reason = busy_reason()
        if reason is None:
            try:
                fd = os.open(str(LOCK), os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o644)
            except FileExistsError:
                reason = "lock appeared during claim"
            else:
                rec = dict(project=PROJECT, pid=os.getpid(), owner=owner,
                           phase=phase,
                           started=datetime.now(timezone.utc).isoformat())
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    json.dump(rec, f)
                log(f"claimed GPU lock owner={owner[:8]} phase={phase}")
                return owner
        if LOCK.exists():
            rec = read_lock() or {}
            if rec.get("project") != PROJECT:
                try:
                    age = (datetime.now(timezone.utc)
                           - datetime.fromisoformat(rec["started"])).total_seconds() / 60
                except Exception:
                    age = 0
                if age > STALE_MINUTES and not headless_blender_pids():
                    log(f"STALE FOREIGN LOCK ({age:.0f} min, project="
                        f"{rec.get('project')}). Not deleting it. Ask the user.")
                    raise SystemExit(3)
        if waited % 60 == 0:
            log(f"waiting: {reason}")
        time.sleep(POLL_S)
        waited += POLL_S


def release(owner):
    if not LOCK.exists():
        return
    rec = read_lock() or {}
    if rec.get("owner") == owner:
        LOCK.unlink()
        log("released GPU lock")
    else:
        log(f"lock owner changed (now {rec.get('project')}); left untouched")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("phase", choices=["check", "build", "sheet", "preview", "master"])
    ap.add_argument("--script", help="python entry point for this phase")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--blender", help="override blender executable path")
    ap.add_argument("rest", nargs="*", help="args passed to the blender script")
    a = ap.parse_args()

    exe = Path(a.blender) if a.blender else BLENDER
    if not exe.exists():
        log(f"blender not found at {exe}")
        return 2
    USER_RES.mkdir(parents=True, exist_ok=True)
    (OUT / "logs").mkdir(parents=True, exist_ok=True)

    env = dict(os.environ)
    env["BLENDER_USER_RESOURCES"] = str(USER_RES)
    env["BLENDER_USER_CONFIG"] = str(USER_RES / "config")

    if a.phase == "check":
        args = ["-b", "--factory-startup", "--version"]
    else:
        if not a.script:
            log("--script is required for this phase")
            return 2
        entry = Path(a.script)
        if not entry.is_absolute():
            entry = SCRIPTS / entry
        args = ["-b", "--factory-startup", "--python-exit-code", "7",
                "-P", str(entry), "--", a.phase, *a.rest]

    logfile = OUT / "logs" / f"headless_{a.phase}.log"
    if a.phase != "check" and PAUSE.exists():
        log(f"pause sentinel present; not claiming GPU for phase={a.phase}")
        return 0
    owner = claim(a.phase)
    code = 1
    try:
        mem, util = gpu_state()
        log(f"GPU before launch: {mem}MiB used, {util}% util")
        log(f"launch: {exe} {' '.join(args[:6])}...")
        log(f"BLENDER_USER_RESOURCES={USER_RES}")
        t0 = time.time()
        with open(logfile, "w", encoding="utf-8", errors="replace") as lf:
            p = subprocess.Popen([str(exe), *args], cwd=str(SCRIPTS),
                                 env=env, stdout=subprocess.PIPE,
                                 stderr=subprocess.STDOUT, text=True,
                                 encoding="utf-8", errors="replace")
            last_beat = time.time()
            tail = []
            for line in p.stdout:
                lf.write(line)
                lf.flush()
                tail.append(line.rstrip())
                if len(tail) > 40:
                    tail.pop(0)
                s = line.strip()
                if s.startswith(("Error", "Traceback", "Warning: ", "Saved:",
                                 "PROBE", "BUILD", "SHEET", "QA")) or "Fra:" in s:
                    if time.time() - last_beat > 10 or not s.startswith("Fra:"):
                        log(s[:200])
                        last_beat = time.time()
                if time.time() - t0 > a.timeout:
                    log("TIMEOUT - terminating own blender process only")
                    p.terminate()
                    break
            code = p.wait()
        log(f"blender exited {code} in {time.time() - t0:.1f}s")
        if code != 0:
            log("--- last output ---")
            for line in tail[-25:]:
                print("   " + line[:200], flush=True)
        cfg = USER_RES / "4.2" / "config"
        log(f"profile isolation: {cfg} exists={cfg.exists()}")
    finally:
        release(owner)
    return code


if __name__ == "__main__":
    sys.exit(main())