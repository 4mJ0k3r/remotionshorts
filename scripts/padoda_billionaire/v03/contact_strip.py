"""Lay out the six requested stills from the native benchmark."""
import json
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont


output = Path(__file__).resolve().parents[3] / "renders/padoda_billionaire/v03"
report = json.loads((output / "benchmark.json").read_text())
frames = output / report["native_stills_dir"]
panels = [
    (70, "Recoil jolt"),
    (80, "Gold flash"),
    (84, "Vault landing"),
    (178, "Three-quarter pinch"),
    (225, "Storyteller lean"),
    (250, "Held wink"),
]
width, height, margin, gap = 240, 427, 22, 12
sheet = Image.new("RGB", (2 * margin + 6 * width + 5 * gap, height + 112), "#151827")
draw = ImageDraw.Draw(sheet)
title = ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf", 30)
label = ImageFont.truetype("C:/Windows/Fonts/segoeui.ttf", 18)
draw.text((margin, 14), "Padoda Billionaire v03", font=title, fill="#fff3e5")
for i, (frame, caption) in enumerate(panels):
    x = margin + i * (width + gap)
    with Image.open(frames / f"frame_{frame:04}.png") as still:
        sheet.paste(still.convert("RGB").resize((width, height), Image.Resampling.LANCZOS), (x, 66))
    draw.text((x, 503), f"f{frame:03}  {caption}", font=label, fill="#fff3e5")
sheet.save(output / "contact_strip_v03.png")
