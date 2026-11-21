"""User-requested short quality preview and 24 timestamps; no Blender launch."""
import json,subprocess,hashlib
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');ROOT=OUT.parents[1]
rows=json.loads((OUT/'shots.json').read_text())['shots'];last=0
for f in range(1,1636):
    p=OUT/'frames'/f'{f:04}.png'
    if not p.exists():break
    try:
        with Image.open(p) as im:assert im.size==(540,960);im.verify()
    except Exception:break
    last=f
ends=[r['end_frame'] for r in rows if r['end_frame']<=last]
end=max(ends) if ends else last//30*30
assert end>0;duration=end/30
video=OUT/'classroom_fart_initial_quality_preview.mp4'
subprocess.run(['ffmpeg','-v','warning','-y','-framerate','30','-start_number','1','-i',str(OUT/'frames/%04d.png'),'-i',str(OUT/'audio_master.wav'),'-map','0:v:0','-map','1:a:0','-frames:v',str(end),'-t',f'{duration:.9f}','-c:v','libx264','-preset','medium','-crf','18','-threads','0','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(video)],check=True)
short={'shots':[{**r,'b':min(end,r['b'])} for r in rows if r['a']<end]}
(OUT/'shots_opening.json').write_text(json.dumps(short,indent=2))
subprocess.run(['python',str(ROOT/'scripts/short_qa.py'),str(video),str(OUT/'qa_opening'),str(OUT/'shots_opening.json')],check=True)
selected=[60,160,232,300,385,455,520,620,702,751,786,855,940,1007,1060,1145,1245,1360,1410,1446,1466,1484,1580,1635]
mapping=json.loads((OUT/'calibration_frame_map.json').read_text())['frames'];font=ImageFont.truetype(r'C:\Windows\Fonts\arialbd.ttf',18);small=ImageFont.truetype(r'C:\Windows\Fonts\arial.ttf',15)
cols,tw,th,gap=4,270,480,16;canvas=Image.new('RGB',(cols*(tw+gap)+gap,80+6*(th+44)),'#142a38');d=ImageDraw.Draw(canvas)
d.text((16,12),'CLASSROOM FART / 24 TIMESTAMPS / 54.5s TIMELINE',font=font,fill='#f4d99e')
d.text((16,42),'Opening: rendered frames | Later: calibration stills | No full video rendered',font=small,fill='#dbe9ee')
evidence=[]
for i,f in enumerate(selected):
    p=OUT/'frames'/f'{f:04}.png';kind='rendered'
    if not p.exists():
        p=OUT/'benchmark_static'/f'{f:04}.png';kind='calibration'
        if not p.exists():p=Path(mapping[str(f)])
    r=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);t=(f-1)/30
    x=gap+i%cols*(tw+gap);y=80+i//cols*(th+44)
    d.text((x,y),f'{r["shot"]}  {int(t//60):02}:{t%60:05.2f}  f{f}',font=font,fill='white')
    im=Image.open(p).convert('RGB');im.thumbnail((tw,th));canvas.paste(im,(x,y+28))
    evidence.append({'frame':f,'seconds':t,'shot':r['shot'],'kind':kind,'source':str(p)})
sheet=OUT/'sheet_24_timestamps.jpg';canvas.save(sheet,quality=94)
probe=json.loads(subprocess.run(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)],capture_output=True,text=True,check=True).stdout)
v=next(x for x in probe['streams'] if x['codec_type']=='video');assert int(v['nb_frames'])==end
result={'video':str(video),'sheet':str(sheet),'frames':end,'seconds':duration,'dimensions':[v['width'],v['height']],'fps':v['r_frame_rate'],'available_completed_frames':last,'video_sha256':hashlib.sha256(video.read_bytes()).hexdigest(),'sheet_frames':evidence,'full_render':'stopped by user; do not resume without instruction'}
(OUT/'opening_delivery.json').write_text(json.dumps(result,indent=2))
status=json.loads((OUT/'production_status.json').read_text());status.update(stage='opening-and-24-frame-sheet-delivered-full-render-stopped',opening_video=video.name,opening_seconds=duration,sheet=sheet.name,full_render_stopped_by_user=True);(OUT/'production_status.json').write_text(json.dumps(status,indent=2))
print(json.dumps({k:v for k,v in result.items() if k!='sheet_frames'},indent=2))
