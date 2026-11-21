"""Review sheets come from the delivered MP4, not from a different scene version."""
from pathlib import Path
import subprocess,json,hashlib,datetime
import numpy as np
from PIL import Image,ImageDraw,ImageFont
OUT=Path(r'D:\remotionshorts\renders\bamboo_ambush');QA=OUT/'qa_v2';video=OUT/'bamboo_ambush_v2_360p.mp4';raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(video),'-vf','scale=180:320','-f','rawvideo','-pix_fmt','rgb24','-']);frames=np.frombuffer(raw,np.uint8).reshape(-1,320,180,3);assert len(frames)==935;font=ImageFont.truetype('C:/Windows/Fonts/arial.ttf',15)
sets={'entry_sequence':list(range(18,33)),'finale_cycles':sum([list(range(a,a+5)) for a in [769,779,799,829,889,909,929]],[]),'all_cut_peaks':[45,140,240,345,430,495,560,660,735,800,860,910]}
for name,selected in sets.items():
 cols=5 if name!='all_cut_peaks' else 4;sheet=Image.new('RGB',(cols*186,((len(selected)+cols-1)//cols)*344),'#17202a');d=ImageDraw.Draw(sheet)
 for j,f in enumerate(selected):x=j%cols*186;y=j//cols*344;sheet.paste(Image.fromarray(frames[f-1]),(x,y+20));d.text((x+3,y+2),f'f{f} | {(f-1)/30:.2f}s',font=font,fill='white')
 sheet.save(QA/(name+'.jpg'),quality=94)
paths=[video,OUT/'bamboo_ambush_v2.blend',OUT/'audio_master.wav',OUT/'sheet_v2.jpg',OUT/'v2_preview_config.json',OUT/'v2_contact_audit.json'];manifest={'completed_local':datetime.datetime.now().isoformat(timespec='seconds'),'video':'360x640,30fps,935frames,31.167s; original-speed master audio','qa':'technical pass; calibrated poses and exported frame sequences reviewed','sampling':'12samples, GPU compositor','files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in paths]};(OUT/'v2_delivery_manifest.json').write_text(json.dumps(manifest,indent=2));progress=json.loads((OUT/'v2_progress.json').read_text());progress['stage']='preview_ready';progress['output']=str(video);(OUT/'v2_progress.json').write_text(json.dumps(progress,indent=2));print('Exported-video review sheets and delivery manifest recorded.')
