"""Action-span contact strips decoded from the delivered, audio-muxed movie."""
import subprocess
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/sendha_namak_science'
SPANS=[
 ('01_lick',[12,30,49,70,85]),('02_chart_pan',[86,94,103,122,150]),
 ('03_phone',[160,195,215,225,250]),('04_panic',[270,290,320,365,435]),
 ('05_mouth_zoom',[450,465,480,490,500]),('06_bacteria',[495,520,550,590,630]),
 ('07_tissue',[640,690,738,780,830]),('08_invasion',[860,885,920,975,1015]),
 ('09_virus_flags',[1030,1070,1115,1155,1250]),('10_shrug',[1265,1278,1295,1310,1320]),
 ('11_dining',[1330,1360,1400,1440,1470]),('12_safari',[1485,1510,1540,1560,1610]),
 ('13_clinic_faint',[1637,1656,1675,1695,1724])]

def main():
    frames=sorted({f for _,span in SPANS for f in span})
    expression='+'.join(f'eq(n\\,{f-1})' for f in frames)
    raw=subprocess.check_output(['ffmpeg','-v','error','-i',str(OUT/'sendha_namak_v2_master.mp4'),'-vf',f'select={expression},scale=270:480','-vsync','0','-f','rawvideo','-pix_fmt','rgb24','pipe:1'])
    pictures=np.frombuffer(raw,dtype=np.uint8).reshape((-1,480,270,3));assert len(pictures)==len(frames)
    images={f:Image.fromarray(picture) for f,picture in zip(frames,pictures)}
    directory=OUT/'qa_v2/action_strips';directory.mkdir(parents=True,exist_ok=True)
    font=ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf',18)
    for name,span in SPANS:
        result=Image.new('RGB',(5*280+10,520),'#182432');draw=ImageDraw.Draw(result)
        for i,f in enumerate(span):
            draw.text((10+i*280,5),f'{name} / f{f}',font=font,fill='white');result.paste(images[f],(10+i*280,32))
        result.save(directory/(name+'.jpg'),quality=94)
    print('Action strips decoded from delivered movie:',directory)

if __name__=='__main__':main()
