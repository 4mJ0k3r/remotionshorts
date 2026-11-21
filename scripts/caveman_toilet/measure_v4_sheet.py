"""Measure shirt highlight clipping and cave upper-band readability."""
import json
import sys
from pathlib import Path
import numpy as np
from PIL import Image
OUT=Path(__file__).resolve().parents[2]/'renders'/'caveman_toilet'
folder=OUT/('calibration_'+(sys.argv[1] if len(sys.argv)>1 else 'v4_confirm'))
regions=json.loads((OUT/'qa_v4_regions.json').read_text())
rows=[]
for r in regions:
    image=np.asarray(Image.open(folder/f"tile_{r['tile']:02d}_f{r['frame']:04d}.png").convert('RGB'))/255
    x0,y0,x1,y1=r['box'];x0=max(0,x0);x1=min(540,x1);y0=max(0,y0);y1=min(960,y1)
    crop=image[y0:y1,x0:x1]
    if not crop.size:continue
    white=float((crop.min(axis=2)>.94).mean())
    pink=float(((crop[:,:,0]>.90)&(crop[:,:,1]>.60)&(crop[:,:,2]>.60)).mean())
    rows.append(dict(frame=r['frame'],char=r['char'],white_fraction=white,pink_fraction=pink))
cave=[]
for p in sorted(folder.glob('tile_*.png')):
    f=int(p.stem.split('_f')[-1])
    if not 540<=f<1370:continue
    pixels=np.asarray(Image.open(p).convert('RGB'))/255
    upper=pixels[70:360,40:500]
    luma=upper@np.array([.2126,.7152,.0722])
    cave.append(dict(frame=f,upper_cave_mean_luma=float(luma.mean())))
errors=[]
for r in rows:
    if r['white_fraction']>.005 or r['pink_fraction']>.01:errors.append(f"Shirt clipped: {r}")
for r in cave:
    if r['upper_cave_mean_luma']<.04:errors.append(f"Cave upper band too dark: {r}")
report=dict(shirts=rows,cave=cave,errors=errors)
(OUT/'qa_v4_calibration.json').write_text(json.dumps(report,indent=2))
print('V4 calibration:',len(rows),'shirt regions;',len(cave),'cave tiles;',len(errors),'errors')
print('Max shirt white/pink fractions:',max(r['white_fraction'] for r in rows),max(r['pink_fraction'] for r in rows))
print('Minimum upper-cave luma:',min(r['upper_cave_mean_luma'] for r in cave))
if errors:raise RuntimeError(errors)
