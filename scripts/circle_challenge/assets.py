"""Raster cels: opaque cream heads, independent head/body artwork, no image swapping."""
from PIL import Image, ImageDraw, ImageFont, ImageChops, ImageFilter
from pathlib import Path
import math, json
OUT=Path('D:/remotionshorts/renders/circle_challenge/assets'); OUT.mkdir(parents=True,exist_ok=True)
INK='#352329'; CLEAR=(22,18,25,0)
FONT='C:/Windows/Fonts/seguisb.ttf'
def font(n): return ImageFont.truetype(FONT,n)
def line(d,pts,fill=INK,w=20):
    # Catmull-Rom interpolated rounded ink limbs.
    pp=[pts[0]]+pts+[pts[-1]]; out=[]
    for i in range(1,len(pp)-2):
        a,b,c,e=pp[i-1:i+3]
        for k in range(16):
            t=k/16
            out.append(tuple(.5*((2*b[j])+(-a[j]+c[j])*t+(2*a[j]-5*b[j]+4*c[j]-e[j])*t*t+(-a[j]+3*b[j]-3*c[j]+e[j])*t**3) for j in (0,1)))
    out.append(pts[-1]);d.line(out,fill=fill,width=w,joint='curve')
    for x,y in (out[0],out[-1]): d.ellipse((x-w/2,y-w/2,x+w/2,y+w/2),fill=fill)
def shade(im,mask):
    shifted=Image.new('L',im.size);shifted.paste(mask,(24,-18))
    cres=ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(4))
    layer=Image.new('RGBA',im.size,(76,102,132,0));layer.putalpha(cres.point(lambda p:int(p*.16)))
    return Image.alpha_composite(im,layer)
COLORS={'you':'#eab308','host':'#0284c7','rival':'#ea580c','mom':'#db2777','operator':'#eabf32','extra':'#ef4444'}
POSES=['happy','belly','shock','panic','squat','smug','sniff','cry','shout','phone','raise','hug','run','press','blink']
def draw_actor(who,pose,*,motion=False,blink=False,turn=0,mouth=None):
    body=Image.new('RGBA',(1024,1536),CLEAR);d=ImageDraw.Draw(body)
    bulge=who=='you' and pose not in ('happy','belly')
    squat=pose=='squat'; hip=850 if not squat else 890
    # Curved legs / grounded shoe silhouettes.
    legs=[[(450,hip),(420,1240),(395,1450)],[(570,hip),(590,1250),(626,1450)]]
    if pose=='run': legs=[[(450,hip),(320,1190),(220,1340)],[(570,hip),(720,1160),(790,1400)]]
    if squat: legs=[[(450,hip),(315,1215),(370,1450)],[(570,hip),(680,1215),(625,1450)]]
    if who=='you' and pose=='panic': legs[1]=[(570,hip),(690,1200),(730,1418)]
    for p in ([] if motion else legs):
        line(d,p,w=17 if who=='you' and squat else 29);x,y=p[-1];d.ellipse((x-48,y-12,x+60,y+24),fill=INK)
    seat=(430,782,665,907) if bulge else (430,792,594,879)
    d.rounded_rectangle(seat,55,fill='#58606e',outline=INK,width=14)
    if bulge:
        d.arc((459,798,649,893),15,143,fill='#454e5b',width=12)
    # Arms first: hidden roots beneath sleeves.
    arms=[[(370,700),(300,905),(350,1030)],[(653,700),(720,900),(680,1040)]]
    if pose in ('belly','panic'):arms=[[(370,700),(280,880),(480,890)],[(653,700),(745,900),(535,910)]]
    if pose in ('smug','squat'):arms=[[(370,700),(270,870),(401,920)],[(653,700),(755,870),(625,920)]]
    if squat: arms=[[(370,700),(272,1000),(318,1204)],[(653,700),(745,990),(682,1205)]]
    if pose in ('sniff','cry'):arms[1]=[(653,700),(786,658),(566,470)]
    if pose in ('phone','shout'):arms[1]=[(653,700),(800,650),(737,406)]
    if pose=='raise':arms[1]=[(653,700),(825,610),(835,300)]
    if pose=='hug':arms=[[(370,700),(240,760),(170,670)],[(653,700),(775,760),(865,680)]]
    if pose=='press':arms[1]=[(653,700),(790,805),(845,930)]
    if pose=='run':arms=[[(370,700),(250,600),(310,485)],[(653,700),(775,825),(835,710)]]
    arms=[[(444 if i==0 else 580,651),*arm[1:]] for i,arm in enumerate(arms)]
    if pose in ('belly','panic'):
        arms=[[(444,651),(398,748),(480,782)],[(580,651),(625,753),(535,792)]]
    if pose=='smug':
        arms=[[(444,651),(392,763),(435,806)],[(580,651),(644,755),(584,806)]]
    for arm in ([] if motion else arms):
        line(d,arm,w=22)
    mask=Image.new('L',body.size)
    ImageDraw.Draw(mask).rounded_rectangle((435,585,590,835),radius=70,fill=255)
    outline=mask.filter(ImageFilter.MaxFilter(17))
    body.paste(INK,(0,0),outline)
    body.paste(COLORS[who],(0,0),mask)
    body=shade(body,mask)
    d=ImageDraw.Draw(body)
    if who=='you':
        d.arc((450,610,568,812),112,247,fill='#f6cf55',width=6)
        d.rounded_rectangle((462,685,562,741),12,fill='#a62529')
        d.text((512,711),'042',font=font(35),anchor='mm',fill='white')
    if who=='host':
        line(d,[(465,660),(475,755)],'#fffdf8',10);line(d,[(550,660),(540,755)],'#fffdf8',10)
        if pose not in ('sniff','run'):
            d.polygon([(277,913),(172,857),(172,1033),(277,977)],fill='#f5f3ee',outline=INK,width=10)
            d.rounded_rectangle((264,916,365,976),12,fill='#ef4444',outline=INK,width=8)
    if who=='mom':
        d.polygon([(387,647),(441,660),(438,920),(377,914)],fill='#36d5e6',outline=INK,width=7)
        for x in (392,408,424):d.line((x,885,x,923),fill='#127f9f',width=5)
    if who=='operator':d.rounded_rectangle((464,675,560,773),20,fill='#303c48');d.text((512,720),'!',font=font(66),anchor='mm',fill='#ffdb45')
    if who=='you' and pose in ('belly','panic'):
        d.arc((392,738,430,811),102,258,fill='#cf4927',width=11)
        d.arc((595,738,633,811),-78,78,fill='#cf4927',width=11)
    for a in ([] if motion else arms):
        x,y=a[-1]
        if who=='you' and pose in ('belly','panic','squat'): continue
        if bulge and pose in ('happy','shock','smug','shout','phone') and x>580 and 785<y<925: continue
        d.ellipse((x-22,y-23,x+22,y+23),fill='#fffdf8',outline=INK,width=7)
    if pose in ('phone','shout') and not motion:
        d.rounded_rectangle((709,338,770,493),15,fill='#192133',outline=INK,width=8);d.rounded_rectangle((720,358,758,455),5,fill='#72bdd4')
    # Head separate, compact 512x512 image with origin centered on skull.
    head=Image.new('RGBA',(512,512),CLEAR);h=ImageDraw.Draw(head);cx=256;cy=256;r=205
    if who=='mom':h.ellipse((120,27,244,130),fill='#24202b',outline=INK,width=14)
    outer=[];inner=[]
    for i in range(256):
        a=i*math.tau/256;rr=r*(1+.017*math.sin(2*a+.6)-.01*math.cos(3*a))
        w=17+2*math.cos(a-2.3)
        outer.append((cx+(rr+w/2)*math.cos(a),cy+(rr+w/2)*math.sin(a)))
        inner.append((cx+(rr-w/2)*math.cos(a),cy+(rr-w/2)*math.sin(a)))
    mask=Image.new('L',head.size);ImageDraw.Draw(mask).polygon(inner,fill=255)
    h.polygon(outer,fill=INK);h.polygon(inner,fill='#d8ebd0' if pose in ('sniff','choke') else '#ffe0d8' if pose=='shock' else '#fffdf8')
    head=shade(head,mask);h=ImageDraw.Draw(head)
    if who=='you':
        h.polygon([(82,204),(94,130),(155,77),(298,61),(394,119),(405,180),(311,143),(234,149),(193,125),(144,180)],fill='#6b3e25')
        h.polygon([(93,299),(142,320),(181,359),(335,359),(389,310),(422,294),(403,387),(345,440),(242,451),(153,410)],fill='#6b3e25')
    if who=='host':
        h.polygon([(95,171),(115,89),(185,111),(219,36),(260,108),(334,62),(385,130),(415,183)],fill='#ed7b28',outline=INK,width=7)
        h.rounded_rectangle((90,151,415,188),12,fill='#fffdf8',outline=INK,width=7)
    if who in ('rival','extra'):
        h.polygon([(78,205),(94,123),(135,135),(169,59),(218,112),(275,52),(310,111),(371,80),(423,189),(366,155),(298,166),(231,140),(160,184)],fill=INK)
    if who=='mom':
        h.pieslice((64,59,451,382),180,352,fill='#28212c');h.ellipse((243,178,265,200),fill='#cf233c')
    ex=[192+turn,317+turn];ey=253
    for x in ex:
        if blink or pose=='blink':h.line((x-15,ey,x+15,ey),fill=INK,width=9)
        elif pose=='choke' or (motion and pose=='shout'):
            sign=1 if x==ex[0] else -1
            line(h,[(x-sign*20,ey-15),(x+sign*13,ey),(x-sign*20,ey+15)],w=12)
        else:
            eh=32 if pose in ('shock','shout','panic','press') else 21
            h.ellipse((x-13,ey-eh,x+13,ey+eh),fill=INK)
            if pose in ('sniff','smug'):h.rectangle((x-17,ey-eh-2,x+17,ey-3),fill='#d8ebd0' if pose=='sniff' else '#fffdf8')
        dy=14 if pose in ('cry','panic','press') else -8 if pose=='smug' else 0
        line(h,[(x-29,ey-57+dy),(x,ey-66),(x+28,ey-54-dy)],w=9)
    if who=='rival':
        for x in ex:h.ellipse((x-47,ey-45,x+47,ey+46),outline=INK,width=12)
        h.line((239,ey,270,ey),fill=INK,width=9)
        for x in ex:h.arc((x-32,ey+30,x+32,ey+57),0,180,fill='#5f5662',width=8)
    if mouth is not None or pose in ('shout','shock','phone','cry','press','choke'):
        height=mouth if mouth is not None else (105 if motion and pose=='shout' else 69)
        if height<=12:
            h.line((222+turn,347,289+turn,347),fill=INK,width=8)
        else:
            h.rounded_rectangle((211+turn,346-height/2,301+turn,346+height/2),min(31,height/2),fill=INK)
            h.ellipse((236+turn,339+height*.27,280+turn,344+height*.42),fill='#ef7d89')
    elif pose in ('panic','squat','belly','sniff'):h.rounded_rectangle((206,328,304,356),13,fill=INK);h.rectangle((220,333,289,341),fill='#fffdf8')
    else:h.arc((201,293,310,357),0,180,fill=INK,width=12)
    if pose in ('shock','sniff','panic','press'):
        h.polygon([(419,203),(440,243),(434,266),(417,268),(407,252)],fill='#5dd6f7',outline='#267b9f',width=3)
    if pose in ('cry','choke'):
        for x in ex:
            h.polygon([(x-15,278),(x+13,278),(x+25,408),(x-4,425),(x-22,398)],fill='#76d9f3');h.line((x-3,290,x+6,399),fill='#dbf9ff',width=8)
    if motion:
        return body,head
    # Embed head in full required 1024x1536 coordinate canvas too for audit.
    full=body.copy();full.alpha_composite(head,(256,124));full.save(OUT/f'{who}_{pose}_full.png')
    body.save(OUT/f'{who}_{pose}_body.png');head.save(OUT/f'{who}_{pose}_head.png')
    assert head.getpixel((256,220))[3]==255
    if who=='extra':
        for variant,color in enumerate(('#ab4738','#305d86','#bc8e45')):
            capped=head.copy()
            cap=ImageDraw.Draw(capped)
            if variant==0:
                cap.rounded_rectangle((101,52,406,166),44,fill=color,outline=INK,width=13)
                cap.ellipse((226,142,459,179),fill=color,outline=INK,width=9)
            elif variant==1:
                cap.pieslice((66,45,443,280),180,360,fill=color,outline=INK,width=12)
                cap.rounded_rectangle((64,138,449,176),17,fill='#e3c4a2',outline=INK,width=8)
            else:
                cap.rounded_rectangle((78,149,433,188),14,fill=color,outline=INK,width=8)
            capped.save(OUT/f'extra_{pose}_hat{variant}.png')

def label(name,title,sub='',bg='#111b2b',fg='#fff5cc',size=(1600,600)):
    im=Image.new('RGBA',size,bg);d=ImageDraw.Draw(im);w,h=size
    d.rounded_rectangle((8,8,w-9,h-9),35,outline='#e5b84a',width=12)
    fs=150 if len(title)<15 else 95
    while d.textbbox((0,0),title,font=font(fs))[2]>w-100:fs-=2
    d.text((w/2,h*.43),title,font=font(fs),anchor='mm',fill=fg)
    if sub:d.text((w/2,h*.78),sub,font=font(49),anchor='mm',fill=fg)
    im.save(OUT/f'{name}.png')
def hud(i,day,count,title):
    im=Image.new('RGBA',(1080,260),CLEAR);d=ImageDraw.Draw(im)
    d.rounded_rectangle((22,14,179,78),21,fill='#f3c54b')
    d.text((101,46),day,font=font(34),anchor='mm',fill='#172132')
    d.rounded_rectangle((22,91,362,151),20,fill='#142235',outline='#f5c94f',width=2)
    d.text((192,121),f'PLAYERS LEFT: {count}',font=font(28),anchor='mm',fill='#ffffff')
    im.save(OUT/f'hud_{i}.png')
if __name__=='__main__':
    for who in COLORS:
        for p in POSES:draw_actor(who,p)
    label('score','₹7,00,00,000','$500,000 / ₹7 CRORE')
    label('winner','WINNER!','₹7 CRORE • LAST TO LEAVE',bg='#efbd28',fg='#172132')
    label('check','₹7,00,00,000','PAY TO THE WINNER',bg='#effbec',fg='#176b45')
    label('brain','VOMIT CENTER','AREA POSTREMA',bg='#6f152f')
    label('toilet','WC','PORTABLE TOILET',bg='#0586ba')
    info=[('DAY 1','100','LAST TO LEAVE WINS ₹7 CRORE'),('DAY 1','100','ONE VERY BAD STOMACH'),('DAY 1','100','DISASTER IN THE PANTS'),('DAY 1','100','LEAVE CIRCLE = LOSE 7 CRORE'),('DAY 1','100',"SITTING IS NOT AN OPTION"),('DAY 2','100','SUPERPOWER UNLOCKED'),('DAY 2','100','37°C + SKATOLE + H2S'),('DAY 2','100','VOMIT CENTER: TRIGGERED!'),('DAY 2','88','THE GREAT ESCAPE'),('DAY 2','14','EVEN THE HOST RETREATS'),('DAY 4','2','FINAL SHOWDOWN'),('DAY 4','2','HIS SOUL IS LEAVING'),('WINNER','1','₹7 CRORE WON! CALLING MOM'),('LATER','1','MOM ARRIVES FOR THE RESCUE'),('LOVE','1',"7 CRORE IGNORED. MOM'S LOVE WINS.")]
    for i,x in enumerate(info):hud(i,*x)
    hud(15,'DAY 2','42','THE GREAT ESCAPE');hud(16,'DAY 2','14','THE GREAT ESCAPE');hud(17,'DAY 2','74','THE GREAT ESCAPE')
    print('Generated opaque layered cels and screen graphics.')
