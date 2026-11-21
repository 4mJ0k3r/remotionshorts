"""Evidence sheets and measured image differences for this version."""
from pathlib import Path
import json,numpy as np
from PIL import Image,ImageDraw,ImageOps
P=Path(__file__).resolve().parents[3]/'renders/gold_mine_salting_v4'
def sheet(files,out,width=270,columns=7,crop=None):
 cellh=500;canvas=Image.new('RGB',(columns*width,((len(files)+columns-1)//columns)*cellh),'#181820');d=ImageDraw.Draw(canvas)
 for i,p in enumerate(files):
  im=Image.open(p).convert('RGB')
  if crop:im=im.crop(tuple(int(v*(im.width if j%2==0 else im.height)) for j,v in enumerate(crop)))
  im=ImageOps.contain(im,(width-8,cellh-30));x=(i%columns)*width;y=(i//columns)*cellh
  canvas.paste(im,(x+(width-im.width)//2,y+25));d.text((x+4,y+5),p.stem,fill='white')
 canvas.save(out)
if __name__=='__main__':
 import sys
 if sys.argv[1]=='shadows':
  crops={1:(.35,.432,.64,.46),151:(.36,.322,.63,.352),288:(.25,.285,.68,.325)};rows=[]
  for f,c in crops.items():
   a=np.array(Image.open(P/'hat_shadow_probes'/f'{f}_brim_on.png')).astype(float);b=np.array(Image.open(P/'hat_shadow_probes'/f'{f}_brim_off.png')).astype(float)
   h,w=a.shape[:2];x1,y1,x2,y2=[int(v*(w if i%2==0 else h)) for i,v in enumerate(c)]
   delta=(b-a)[y1:y2,x1:x2].mean(axis=2)
   rows.append({'frame':f,'receiver_crop':c,'mean_hat_shadow_darkening_255':float(delta.mean()),'pixels_darker_over_5_levels':int((delta>5).sum())})
  (P/'hat_shadow_evidence.json').write_text(json.dumps(rows,indent=2))
  sheet([P/'hat_shadow_probes'/f'{f}_{s}.png' for f in crops for s in ['brim_on','brim_off']],P/'hat_shadow_comparison.jpg',columns=6,crop=(.15,.25,.85,.58))
  print(rows)
 elif sys.argv[1]=='cal':
  folder=P/sys.argv[2];sheet(sorted(folder.glob('frame*.png')),folder/'sequence.jpg')
 elif sys.argv[1]=='encoded':
  import subprocess
  report=json.loads((P/'qa_final/report.json').read_text());indices=set([10,37,39,41,43,45,49,54,60,64,92,120,135,150,165,180,200,206,214,220,235,255,267,280,285,294])
  for i in report['mad']['review']:
   indices.update(range(max(0,i-2),min(300,i+3)))
  for a,b in report['frozen']:indices.update([a,(a+b)//2,b])
  out=P/'qa_final/encoded_native';out.mkdir(exist_ok=False)
  for i in sorted(indices):
   subprocess.run(['ffmpeg','-v','error','-i',str(P/'gold_mine_salting_v4_1080x1920.mp4'),'-vf',f'select=eq(n\\,{i})','-frames:v','1',str(out/f'frame_{i+1:04d}.png')],check=True)
  sheet(sorted(out.glob('frame*.png')),out/'encoded_sequence.jpg')
