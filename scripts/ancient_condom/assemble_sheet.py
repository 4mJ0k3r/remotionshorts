"""Preserve every full-resolution tile and measure the paired shadow evidence."""
from pathlib import Path
import json,sys
import numpy as np
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');data=json.loads((OUT/'shots.json').read_text());font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',22);version=next((x[2:] for x in sys.argv if x in ['--v2','--v3','--v4','--v5','--cel_v1','--cel_v2','--master']),'v1');cal=OUT/('calibration_'+version if version!='v1' else 'calibration')
sheet=Image.new('RGB',(4*560+20,5*1008+20),'#17202b');d=ImageDraw.Draw(sheet)
for j,f in enumerate(data['samples']):
    im=Image.open(cal/f'f{f:04}.png').convert('RGB');assert im.size==(540,960)
    row=next(x for x in data['shots'] if x['start_frame']<=f<=x['end_frame']);x=20+(j%4)*560;y=20+(j//4)*1008;sheet.paste(im,(x,y+30));d.text((x,y),f"CUT {row['id']:02} | {f/30:05.2f}s | f{f}",font=font,fill='white')
sheet.save(OUT/f'sheet_{version}.jpg',quality=95,subsampling=0)
on=np.array(Image.open(OUT/'qa/shadow_on.png')).astype(float)/255;off=np.array(Image.open(OUT/'qa/shadow_off.png')).astype(float)/255
def luminance(im):
    a=np.where(im<=.04045,im/12.92,((im+.055)/1.055)**2.4);return a@np.array([.2126,.7152,.0722])
l1=luminance(on);l2=luminance(off);contrast=(l2-l1)/np.maximum(l2,.001)
# Exclude the overhead central sheep and all furniture: bottom 35% is unobstructed earth.
mask=np.zeros(l1.shape,bool);mask[int(.68*l1.shape[0]):int(.95*l1.shape[0]),int(.1*l1.shape[1]):int(.90*l1.shape[1])]=True
changed=mask&(contrast>.05);report={'receiver_roi':'lower unobstructed earth in paired overhead diagnostic','shadow_changed_pixels':int(changed.sum()),'contrast_p90':float(np.quantile(contrast[changed],.9)) if changed.any() else 0,'over_30_percent_pixels':int((mask&(contrast>.3)).sum()),'cut4_max_rgb_channel_spread':int(np.ptp(np.array(Image.open(cal/'f0310.png')).astype(int),axis=2).max())}
(OUT/f'qa/measurements_{version}.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2));print(OUT/f'sheet_{version}.jpg')
