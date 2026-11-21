"""Narration timing, non-emissive facial decals and a scale-independent vignette."""
from pathlib import Path
from PIL import Image,ImageDraw
import json,numpy as np,wave
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');ART=OUT/'assets'
ART.mkdir(parents=True,exist_ok=True)
for pose in ['smile','shy','panic','horror','blink']:
    im=Image.new('RGBA',(512,512),(35,24,20,0));d=ImageDraw.Draw(im);ink='#271b19'
    for x in [190,322]:
        if pose=='blink':d.line([(x-21,225),(x+21,225)],fill=ink,width=7)
        else:d.ellipse((x-17,201,x+17,249),fill=ink)
        d.line([(x-28,183+(14 if pose in ['panic','horror'] else 0)),(x+24,180-(12 if pose in ['panic','horror'] else 0))],fill=ink,width=8)
    if pose=='horror':
        d.ellipse((218,292,294,397),fill='#301b24');d.ellipse((228,365,284,393),fill='#c66d82')
    elif pose=='panic':
        d.rounded_rectangle((187,315,325,368),radius=20,fill='#f5edd9',outline=ink,width=6)
        for k in range(1,6):x=189+k*22;d.line([(x,321),(x,363)],fill=ink,width=3)
        d.line([(193,341),(320,341)],fill=ink,width=3)
    else:d.arc((176,272,336,362),4,174,fill=ink,width=8)
    if pose=='shy':
        d.ellipse((115,281,172,306),fill=(226,133,127,140));d.ellipse((340,281,397,306),fill=(226,133,127,140))
    im.save(ART/f'face_{pose}.png')
W,H=1080,1920;y,x=np.mgrid[0:H,0:W];r=np.sqrt(((x-W/2)/(W*.56))**2+((y-H/2)/(H*.57))**2)
u=np.clip((r-.45)/.83,0,1);m=np.round(255*(1-.18*u*u*(3-2*u))).astype(np.uint8)
Image.fromarray(np.repeat(m[:,:,None],3,axis=2)).save(ART/'vignette.png')
im=Image.new('RGBA',(256,256));yy,xx=np.mgrid[0:256,0:256];a=np.clip(1-((xx-127.5)/128)**2-((yy-127.5)/128)**2,0,1)**2
arr=np.zeros((256,256,4),dtype=np.uint8);arr[:,:,:3]=255;arr[:,:,3]=(a*255).astype(np.uint8);Image.fromarray(arr).save(ART/'soft_alpha.png')
bounds=[1,78,156,264,354,474,546,612,708,804,900,1026,1104,1176,1245,1386,1485,1575,1716,1876]
actions=['rose','panic','sheep_lower','clay_shatter','scrape','alkaline','vinegar','roast','rinse','peel','ash_soak','peach_peel','fit_peg','shade_dry','warm_water','honey','tie','hero','final_rinse']
samples=[40,115,210,310,415,510,580,660,755,850,960,1065,1140,1210,1315,1435,1530,1645,1760,1830]
rows=[{'id':i+1,'shot':str(i+1),'start_frame':bounds[i],'end_frame':bounds[i+1]-1,'a':bounds[i]-1,'b':bounds[i+1]-1,'action':action,'scene':f'AC_{i+1:02}'} for i,action in enumerate(actions)]
(OUT/'shots.json').write_text(json.dumps({'fps':30,'frames':1875,'seconds':62.5,'shots':rows,'samples':samples,'whip_ends':[353,611,707,1715],'crossfade':[1176,1183]},indent=2))
with wave.open(str(OUT/'audio_master.wav')) as w:sr=w.getframerate();n=w.getnframes()
(OUT/'audio_info.json').write_text(json.dumps({'audio_frames':n,'sample_rate':sr,'seconds':n/sr,'original_container_seconds':62.040813,'tail_padding_seconds':62.5-62.040813,'classification':'narration; couple reactions are silent acting'},indent=2))
print('Assets, exact 19-cut table, and 62.5s audio prepared.')
