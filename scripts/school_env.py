"""SchoolHeroShort brief: load public/school/audio.mp3 and extract AUDIO_ENV for lip-sync.
Writes src/videos/school/audioEnv.ts (one amplitude per composition frame at 30 fps)."""
import wave, struct

SRC = "out/school/_voice.wav"
OUT = "src/videos/school/audioEnv.ts"
FRAMES = 3660
FPS = 30

w = wave.open(SRC, "rb")
sr, n = w.getframerate(), w.getnframes()
data = struct.unpack("<%dh" % n, w.readframes(n))
w.close()

step = sr / FPS
vals = []
for i in range(FRAMES):
    a, b = int(i * step), int((i + 1) * step)
    if a >= n:
        vals.append(0.0)
        continue
    seg = data[a:b]
    vals.append((sum(x * x for x in seg) / max(1, len(seg))) ** 0.5)
peak = sorted(vals)[int(len(vals) * 0.97)] or 1
vals = [min(1.0, (v / peak) ** 0.7) for v in vals]
out = []
for i in range(FRAMES):
    v = (vals[max(0, i - 1)] + vals[i] * 2 + vals[min(FRAMES - 1, i + 1)]) / 4
    out.append(0.0 if v < 0.06 else round(v, 2))

with open(OUT, "w", encoding="utf-8") as f:
    f.write("// per-frame voice amplitude (0..1) of public/school/audio.mp3, 30 fps\n")
    f.write("export const AUDIO_ENV: number[] = [\n")
    for i in range(0, FRAMES, 30):
        f.write("  " + ",".join("%.2f" % v for v in out[i:i + 30]) + ",\n")
    f.write("];\n")
print("frames", FRAMES, "max", max(out), "mean %.2f" % (sum(out) / FRAMES), "speaking", sum(1 for v in out if v > 0))
