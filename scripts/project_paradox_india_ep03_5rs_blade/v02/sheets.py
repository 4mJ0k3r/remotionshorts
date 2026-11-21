"""Write the V2 calibration, contact close-ups, and V1/V2 comparison."""
import json
from pathlib import Path
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(ROOT / 'scripts'))
from calibration_sheet import make_sheet

V2 = ROOT / 'renders/project_paradox_india_ep03_5rs_blade/v02'
V1 = V2.parent / 'v01'
frames = json.loads((V2 / 'overview_frames.json').read_text())
plan = json.loads((V2 / 'calibration_plan.json').read_text())
manifest = json.loads((V2 / 'shots.json').read_text())

def v2_image(index):
    with Image.open(V2 / 'calibration' / f'frame_{index+1:04d}.png') as source:
        return source.copy()

panels = []
for frame in frames:
    shot = next(shot for shot in manifest['shots'] if shot['a'] <= frame-1 < shot['b'])
    panels.append({'frame': frame-1, 'label': shot['id'].replace('_', ' ').title()})

make_sheet(v2_image, {'panels': panels, 'closeups': []}, V2/'V2_24_panel_sheet.jpg', cell=(254,477))
make_sheet(v2_image, {'panels': [], 'closeups': plan['closeups']}, V2/'V2_contact_closeups.jpg',
           columns=4, cell=(340,335))
overview_indices = set(f-1 for f in frames)
junction_panels = [p for p in plan['panels'] if p['frame'] not in overview_indices
                   and any(key in p['label'] for key in ('junction','transition'))]
make_sheet(v2_image, {'panels': junction_panels, 'closeups': []}, V2/'V2_junctions.jpg',
           columns=8, cell=(162,314))

w, h = 180, 320
cell_w, cell_h = 372, 371
sheet = Image.new('RGB', (6*cell_w, 4*cell_h+62), '#171c26')
draw = ImageDraw.Draw(sheet)
font = ImageFont.truetype('C:/Windows/Fonts/segoeuib.ttf', 19)
small = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 15)
draw.text((12,9),'The ₹5 Blade Loophole  |  24 matched moments',font=font,fill='#f8f4e9')
draw.text((12,34),'V1 preview and calibration stills on the left   ·   V2 calibration stills on the right',font=small,fill='#b8c9da')
for idx, panel in enumerate(panels):
    frame = panel['frame'] + 1
    x, y = idx%6*cell_w+5, idx//6*cell_h+62
    source = V1 / ('preview_540p_first10_frames' if frame <= 300 else 'calibration_010649')
    draw.text((x,y),f'{idx+1:02d}   {panel["label"]}  ·  f{frame}',font=small,fill='#ffda99')
    for offset, label, image in [(0,'V1',Image.open(source/f'frame_{frame:04d}.png')),
                                  (w+4,'V2',v2_image(frame-1))]:
        with image:
            sheet.paste(ImageOps.fit(image.convert('RGB'),(w,h)),(x+offset,y+22))
        draw.text((x+offset+4,y+344),label,font=small,fill='#d9e4ef')
sheet.save(V2/'V1_vs_V2_24_panel_comparison.jpg',quality=94,subsampling=0)
