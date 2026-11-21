"""Project-local painted cels, face poses, HUD plates, and timing data."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageFont,ImageChops,ImageFilter
import json,math,wave,numpy as np
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');ART=OUT/'assets_surgical_v2'
FONT=r'C:\Windows\Fonts\arialbd.ttf'
INK='#331c12';CREAM='#fdfaf2'
def font(n):return ImageFont.truetype(FONT,n)
def canvas():return Image.new('RGBA',(1024,1024),(32,20,16,0))
def shadow_layer(im,mask):
    shifted=Image.new('L',mask.size,0);shifted.paste(mask,(65,-42))
    c=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(14))
    c=ImageChops.multiply(c,mask).point(lambda v:round(v*.24))
    layer=Image.new('RGBA',im.size,'#c4d4e6');layer.putalpha(c)
    return Image.alpha_composite(im,layer)
def head(who,hair):
    im=canvas();d=ImageDraw.Draw(im);outer=[];inner=[]
    for i in range(256):
        a=i*math.tau/256;r=1+.018*math.sin(2*a+.6)-.012*math.cos(3*a-.8)
        w=16*max(.45,1+.35*math.cos(a-2.35))
        outer.append((512+(427*r+w/2)*math.cos(a),530+(435*r+w/2)*math.sin(a)))
        inner.append((512+(427*r-w/2)*math.cos(a),530+(435*r-w/2)*math.sin(a)))
    d.polygon(outer,fill=INK);d.polygon(inner,fill=CREAM)
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(inner,fill=255);im=shadow_layer(im,mask);d=ImageDraw.Draw(im)
    # Cover the complete upper skull, then clip against its inner silhouette.
    fringe=[(-80,460),(82,425),(179,367),(230,273),(329,284),(424,225),(525,287),(606,241),(694,313),(772,267),(824,344),(925,428),(1100,460)]
    hair_layer=canvas();hd=ImageDraw.Draw(hair_layer)
    hd.polygon([(-80,-80),(1100,-80)]+list(reversed(fringe)),fill=hair)
    hd.line(fringe,fill=INK,width=16,joint='curve')
    for k in range(3):hd.line([(174+75*k,279-38*k),(251+75*k,200-32*k),(317+75*k,177-28*k)],fill='#9c5822' if who!='teacher' else '#d4dbea',width=12,joint='curve')
    hair_layer.putalpha(ImageChops.multiply(hair_layer.getchannel('A'),mask));im=Image.alpha_composite(im,hair_layer);d=ImageDraw.Draw(im)
    if who=='teacher':d.ellipse((710,35,928,245),fill=hair,outline=INK,width=16)
    im.save(ART/f'{who}_head.png')
def face(name):
    im=canvas();d=ImageDraw.Draw(im);eye_y=530
    closed=name=='blink';panic=name in ('clenched','scream','soul')
    for x in (352,677):
        if name=='soul':
            pts=[]
            for i in range(100):
                a=i/99*math.pi*5;r=3+i*.58;pts.append((x+r*math.cos(a),eye_y+r*math.sin(a)))
            d.line(pts,fill=INK,width=12)
        elif closed or (name=='skeptical' and x==677):d.line([(x-65,eye_y),(x+65,eye_y)],fill=INK,width=12)
        else:
            gaze=-24 if name=='look_left' else 24 if name=='look_right' else 0
            # Solid pupils clipped by the current horizontal lid aperture.
            pupil=Image.new('L',im.size);pd=ImageDraw.Draw(pupil);pd.ellipse((x-34+gaze,eye_y-46,x+34+gaze,eye_y+46),fill=255)
            if name=='smug':pd.rectangle((0,0,1024,eye_y+4),fill=0)
            lay=Image.new('RGBA',im.size,'#1c1417');lay.putalpha(pupil);im=Image.alpha_composite(im,lay);d=ImageDraw.Draw(im)
        by=eye_y-115
        d.line([(x-83,by+(26 if panic else 0)),(x+67,by-(15 if panic or name=='smug' else 0))],fill=INK,width=17)
    if name=='clenched':
        d.rounded_rectangle((340,704,692,828),radius=54,fill=CREAM,outline=INK,width=13)
        d.line([(350,766),(682,766)],fill=INK,width=8)
        for k in range(1,6):x=350+k*55;d.line([(x,712),(x,820)],fill=INK,width=7)
    elif name in ('scream','talk_c'):
        d.ellipse((417,674,611,895),fill='#26171a',outline=INK,width=12);d.ellipse((446,822,585,875),fill='#dc6e8c')
    elif name=='talk_b':
        d.rounded_rectangle((389,728,640,844),radius=40,fill='#26171a',outline=INK,width=10);d.rectangle((414,733,613,756),fill=CREAM)
    elif name=='talk_a':d.ellipse((462,742,563,812),fill='#26171a',outline=INK,width=10)
    elif name=='skeptical':d.line([(392+i*12,774+13*math.sin(i*.7)) for i in range(22)],fill=INK,width=12)
    elif name=='smug':d.arc((344,609,701,826),0,155,fill=INK,width=15)
    else:d.arc((411,756,616,836),190,345,fill=INK,width=12)
    im.save(ART/f'face_{name}.png')
def torso(who,color,tie):
    im=canvas();d=ImageDraw.Draw(im)
    mask=Image.new('L',im.size);md=ImageDraw.Draw(mask)
    md.rounded_rectangle((153,115,871,923),radius=170,fill=255)
    d.rounded_rectangle((136,98,888,940),radius=175,fill=INK)
    d.rounded_rectangle((153,115,871,923),radius=170,fill=color)
    im=shadow_layer(im,mask);d=ImageDraw.Draw(im)
    d.line([(277,237),(277,657),(328,770),(511,825),(704,770),(747,655),(747,237)],fill='#fdfaf2',width=18,joint='curve')
    d.polygon([(355,126),(512,268),(668,126)],fill=CREAM,outline=INK,width=8)
    if tie:d.polygon([(478,220),(548,220),(571,319),(546,754),(512,815),(479,754),(454,319)],fill='#e61919',outline=INK,width=8)
    im.save(ART/f'{who}_torso.png')
def fx():
    im=Image.new('RGBA',(256,256));pix=im.load()
    for y in range(256):
        for x in range(256):
            r=math.hypot((x-128)/128,(y-128)/128)
            pix[x,y]=(175,255,108,round(255*max(0,1-r*r)**2))
    im.save(ART/'vapor.png')
    im=Image.new('RGBA',(256,384));d=ImageDraw.Draw(im)
    d.polygon([(128,14),(50,166),(42,245),(64,305),(117,332),(172,315),(206,262),(208,208)],fill='#65e4ff',outline='#b6f7ff',width=7)
    d.ellipse((69,203,102,252),fill='#e2fcff');im.save(ART/'drop.png')
def main():
    ART.mkdir(parents=True,exist_ok=True)
    for who,hair,col,tie in [('you','#45230e','#4895ef',True),('friend','#d94e1f','#38b000',False),('teacher','#8d99ae','#adb5bd',False)]:head(who,hair);torso(who,col,tie)
    for name in ['look_left','look_right','clenched','scream','skeptical','smug','soul','talk_a','talk_b','talk_c','blink']:face(name)
    fx()
    bbox=Image.open(ART/'you_head.png').getchannel('A').getbbox()
    (ART/'head_bounds.json').write_text(json.dumps({'you_lower_world':(bbox[3]-512)*1.13/1024,'bbox':bbox},indent=2))
    boundaries=[1,123,198,266,336,435,477,579,663,735,804,905,971,1083,1215,1299,1410,1484,1636]
    labels=['1A','1B','1C','2A','2B','2C','2D','2E','3A','3B','3C','4A','4B','4C','4D','5A','5B','5C']
    hud=['SILENT CLASSROOM: SUDDEN DANGER','INTERNAL PRESSURE: 99% CRITICAL','WHAT IS YOUR ESCAPE PLAN?','MISTAKE #1: CLENCHING THE SEAT','WORST MOVE: PRESSURE TRAP!','SYSTEM OVERLOAD: CRITICAL!','STOMACH ROAR: GENERATOR MODE','TEACHER ALERT: SOUND DETECTED!','COVER-UP FAIL: FAKE COUGHING','COVER-UP FAIL: CHAIR SQUEAK','SUSPICION LEVEL: 100% ON YOU','THE PRO MOVE: 45-DEGREE STEALTH','LEAN BACK 45°: AIRLOCK OPEN','100% SILENT MODE: ZERO SOUND','MISSION SUCCESS: NOBODY HEARD','WARNING: NUCLEAR STENCH DETECTED!','EMERGENCY PROTOCOL: BLAME SHIFT!','ULTIMATE ESCAPE: BLAME YOUR BRO!']
    actions=['nervous','belly','head','grip','grip','sigh','roar','teacher_shock','cough','scuff_rock','soul','point_up','lean','release','teach','nose','jump','blame']
    shots=[]
    for i,(label,text,action) in enumerate(zip(labels,hud,actions)):
        a,b=boundaries[i],boundaries[i+1]-1
        shots.append({'id':i+1,'a':a-1,'b':b,'shot':label,'start_frame':a,'end_frame':b,'start':(a-1)/30,'end':b/30,'action':action,'hud':text})
        im=Image.new('RGBA',(1080,1920));d=ImageDraw.Draw(im)
        d.rounded_rectangle((55,77,1025,168),radius=28,fill='#0d1826',outline='#d4a359',width=2)
        fs=29
        while d.textbbox((0,0),text,font=font(fs))[2]>920:fs-=1
        d.text((540,122),text,font=font(fs),anchor='mm',fill='white')
        im.save(ART/f'hud_{label}.png')
    (OUT/'shots.json').write_text(json.dumps({'fps':30,'frames':1635,'shots':shots},indent=2))
    with wave.open(str(OUT/'audio_master.wav')) as w:
        sr=w.getframerate();samples=np.frombuffer(w.readframes(w.getnframes()),dtype=np.int16).astype(float)/32768
    env=[]
    for f in range(1635):
        chunk=samples[round(f*sr/30):round((f+1)*sr/30)]
        env.append(float(np.sqrt(np.mean(chunk*chunk))) if len(chunk) else 0)
    scale=np.percentile(env,90);env=[round(min(1,x/max(scale,.001)),3) for x in env]
    (OUT/'audio_envelope.json').write_text(json.dumps(env))
    print('Painted assets and 18 non-overlapping cuts ready.',flush=True)
if __name__=='__main__':main()
