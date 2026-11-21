"""CPU-only 20-frame contact sheet from the completed condom reel."""
import io
import json
import subprocess
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont

SOURCE=Path('D:/TOBEUPLOADED/ancient_condom_1080p_master.mp4')
OUT=Path(__file__).resolve().parents[2]/'renders'/'ancient_condom'
metadata=json.loads(subprocess.run(['ffprobe','-v','error','-show_entries','format=duration',
    '-of','json',str(SOURCE)],capture_output=True,text=True,check=True).stdout)
duration=float(metadata['format']['duration'])
w,h,label=270,480,26
sheet=Image.new('RGB',(4*w,5*(h+label)),(18,18,22))
draw=ImageDraw.Draw(sheet)
font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',15)
times=[]
for i in range(20):
    second=(i+.5)*duration/20
    raw=subprocess.run(['ffmpeg','-v','error','-ss',str(second),'-i',str(SOURCE),
        '-frames:v','1','-vf',f'scale={w}:{h}:flags=lanczos','-f','image2pipe','-vcodec','png','-'],
        capture_output=True,check=True).stdout
    tile=Image.open(io.BytesIO(raw)).convert('RGB')
    x,y=i%4*w,i//4*(h+label)
    sheet.paste(tile,(x,y))
    draw.text((x+7,y+h+5),f'{i+1:02d}  |  {int(second//60):02d}:{second%60:04.1f}',font=font,fill=(242,229,203))
    times.append(round(second,3))
OUT.mkdir(parents=True,exist_ok=True)
target=OUT/'sheet_master.jpg'
sheet.save(target,quality=94)
(OUT/'sheet_master_source.json').write_text(json.dumps(dict(source=str(SOURCE),duration=duration,timestamps=times),indent=2))
print(target,flush=True)
