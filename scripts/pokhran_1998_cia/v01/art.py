"""Paint original costumes and reusable expression cards."""
from pathlib import Path
from random import Random

from PIL import Image, ImageDraw

ART=Path(__file__).with_name("art")
ART.mkdir(exist_ok=True)
INK="#161020"
VISEMES=("rest","MBP","AA","EH","EE","OH","OO","FV","L","SH")

def face(cast,mode):
    image=Image.new("RGBA",(1024,1024),(22,16,32,0))
    draw=ImageDraw.Draw(image)
    def ellipse(box,color):
        draw.ellipse(tuple(round(v*4) for v in box),fill=color)
    def stroke(points,width,color=INK):
        draw.line([(round(x*4),round(y*4)) for x,y in points],fill=color,width=width*4,joint="curve")
        r=width/2
        for x,y in (points[0],points[-1]):
            ellipse((x-r,y-r,x+r,y+r),color)
    for sign in (-1,1):
        x=128+sign*48
        stroke(((x-22,72+8*(sign==1)),(x-2,67),(x+20,72+8*(sign==-1))),8)
        ellipse((x-20,94,x+20,126),INK)
        ellipse((x-16,98,x+16,122),"#fff2d8")
        ellipse((x-2,98,x+12,120),INK)
        stroke(((x-20,100),(x+20,100)),7)
    if cast=="engineer":
        stroke(((87,145),(112,138),(127,141),(144,138),(169,145)),11)
    mouth_sizes={"MBP":(28,3),"AA":(23,17),"EH":(26,12),"EE":(32,8),"OH":(19,17),"OO":(13,14),
                 "FV":(26,7),"L":(21,12),"SH":(16,9)}
    if mode in mouth_sizes:
        w,h=mouth_sizes[mode]
        ellipse((128-w,164-h,128+w,164+h),INK)
        if h>=7:ellipse((128-w*.70,164+h*.12,128+w*.70,164+h*.66),"#db7d81")
    elif mode=="sip":
        ellipse((118,156,138,174),INK)
    else:
        stroke(((94,166),(123,174),(149,168),(164,156)),7)
    image.save(ART/f"{cast}_{mode}.png")

for cast in ("kalam","engineer","analyst"):
    for mouth in (*VISEMES,"sip"):face(cast,mouth)
    coat=Image.new("RGBA",(1024,1024),"#444b34" if cast!="analyst" else "#252f4c")
    g=ImageDraw.Draw(coat)
    if cast!="analyst":
        rng=Random(65)
        for j in range(80):
            x,y=rng.randrange(-100,1024),rng.randrange(-100,1024)
            g.polygon([(x,y),(x+81,y-43),(x+135,y-12),(x+175,y+81),(x+62,y+87)],
                      fill=("#7c8054","#232d26","#5e6846")[j%3])
        g.rectangle((0,782,1024,866),fill="#26262d")
        g.rounded_rectangle((418,780,604,874),radius=18,fill="#b6a673")
    else:
        g.polygon([(304,0),(720,0),(565,678),(437,678)],fill="#e9d9c8")
        g.polygon([(472,90),(552,90),(560,370),(512,458),(469,370)],fill="#a32f48")
        g.line([(178,0),(354,389),(275,505)],fill="#5a657a",width=17)
        g.line([(804,0),(660,384),(728,505)],fill="#5a657a",width=17)
        g.line([(341,0),(628,523),(716,0)],fill="#567c86",width=22)
        g.rounded_rectangle((547,499,705,628),radius=15,fill="#65a9af")
    coat.save(ART/f"{cast}_coat.png")
