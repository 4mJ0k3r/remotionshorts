"""Original face cards and clothing for the three Part 1 characters."""
from pathlib import Path

from PIL import Image, ImageDraw

OUT=Path(__file__).with_name("art")
INK="#161020"
MODES={
    "boy": ("calm","look","smirk","squirm","wince","sweat","deadpan"),
    "teacher": ("stern","A","E","I","O","U","M","L","F","S","W"),
    "student": ("side_eye","frown"),
    "florist": ("happy","sweat"),
}


def face(role,mode):
    image=Image.new("RGBA",(1024,1024),(22,16,32,0))
    draw=ImageDraw.Draw(image)

    def ellipse(x,y,w,h,color):
        draw.ellipse((4*(x-w),4*(y-h),4*(x+w),4*(y+h)),fill=color)

    def line(points,weight,color=INK):
        draw.line([(4*x,4*y) for x,y in points],fill=color,width=int(4*weight),joint="curve")
        for x,y in (points[0],points[-1]):
            ellipse(x,y,weight/2,weight/2,color)

    def polygon(points,color):
        draw.polygon([(4*x,4*y) for x,y in points],fill=color)

    for side in (-1,1):
        x=128+side*51
        anger = role=="teacher" or mode in ("wince","frown")
        yb=62 if mode in ("look","sweat") else 69
        line([(x-26,yb-6*side if anger else yb+2),(x-4,yb-5),(x+25,yb+7*side if anger else yb+3)],9)
        height={"calm":21,"look":29,"smirk":21,"squirm":27,"wince":15,"sweat":30,"deadpan":16,
                "side_eye":19,"frown":16}.get(mode,23)
        ellipse(x,107,35,height,INK)
        ellipse(x,107,30,height-4,"#fff5e7")
        pupil=x+(-13 if mode in ("side_eye","frown") else 12 if mode in ("look","smirk") else 0)
        ellipse(pupil,109,11,min(14,height-5),"#49335d" if role=="student" else "#513826")
        ellipse(pupil+1,109,6,9,INK)
        ellipse(pupil-3,105,3,3,"#fff9e9")
        if mode=="happy":
            draw.rectangle((4*(x-37),4*81,4*(x+37),4*136),fill=(22,16,32,0))
            line([(x-27,116),(x-15,104),(x,97),(x+16,103),(x+28,114)],7)
        if anger or mode=="deadpan":
            line([(x-29,96-6*side),(x+26,96+5*side)],5)
        if role=="teacher":
            draw.rounded_rectangle((4*(x-42),344,4*(x+42),526),radius=15,outline=INK,width=25)
        else:
            for i in range(3):
                line([(x-12+i*10,147),(x-7+i*10,140)],2.6,"#c9756c")
    if role=="teacher":
        line([(116,102),(140,102)],5)
        polygon([(79,154),(89,139),(108,132),(126,139),(146,132),(166,138),(176,154),
                 (153,152),(126,160),(106,151)],INK)
    if mode in ("A","E","I","O","U","M","L","F","S","W","squirm","sweat"):
        w,h={"A":(31,23),"E":(29,10),"I":(21,7),"O":(18,19),"U":(13,11),"M":(21,3),
             "L":(23,12),"F":(25,8),"S":(22,5),"W":(34,26),"squirm":(24,13),"sweat":(15,15)}[mode]
        ellipse(128,177,w,h,INK)
        if h>7:
            ellipse(128,177-h*.40,w*.72,h*.22,"#fff3e7")
            ellipse(128,177+h*.40,w*.59,h*.24,"#d67b82")
    elif mode in ("wince","frown","side_eye","stern"):
        line([(102,183),(115,173),(136,172),(151,178)],5.5)
    elif mode=="deadpan":
        line([(109,177),(144,177)],4.5)
    else:
        line([(99,171),(114,179),(135,176),(154,162 if mode=="smirk" else 172)],6.)
        if mode=="smirk":
            polygon([(115,176),(145,169),(140,177),(127,181)],"#fff7eb")
    return image


def costume(role):
    base={"boy":"#f8c430","teacher":"#f3e6d9","student":"#9950ac","florist":"#4a8658"}[role]
    image=Image.new("RGBA",(1024,1024),base)
    draw=ImageDraw.Draw(image)
    if role=="boy":
        draw.polygon([(0,435),(294,480),(510,580),(736,480),(1024,438),(1024,1024),(0,1024)],fill="#275eb6")
        draw.polygon([(0,808),(1024,808),(1024,1024),(0,1024)],fill="#22364f")
        draw.arc((244,-103,780,355),0,180,fill=INK,width=27)
        for x in (444,580):
            draw.line((x,154,x,400),fill="#fff2ab",width=26)
            draw.ellipse((x-19,372,x+19,410),fill=INK)
        draw.rounded_rectangle((330,627,692,764),radius=52,outline="#b3d3f4",width=15)
    elif role=="teacher":
        for x in range(30,1024,93):
            draw.line((x,44,x,948),fill="#d0bdb9",width=7)
        draw.polygon([(300,0),(521,161),(390,273),(241,0)],fill="#fbf3df")
        draw.polygon([(720,0),(511,161),(644,273),(798,0)],fill="#fbf3df")
        draw.polygon([(468,177),(549,177),(571,623),(513,709),(447,631)], fill="#a53d4e")
        draw.rectangle((0,795,1024,1024),fill="#35465b")
        draw.rectangle((473,801,553,858),fill="#e0ad54")
    elif role=="student":
        for y in (160,246,790,855):
            draw.rectangle((0,y,1024,y+20),fill="#dc9fe0")
        draw.rounded_rectangle((643,278,758,427),radius=26,fill="#426888")
    else:
        draw.polygon([(268,0),(341,0),(414,240),(606,240),(681,0),(742,0),(740,553),(1024,669),
                      (1024,1024),(0,1024),(0,669),(281,554)],fill="#b7404a")
        for x in (438,481,525,570):
            draw.line((x,270,x,677),fill="#f8e3cb",width=14)
        draw.rounded_rectangle((328,729,693,894),radius=38,outline="#f8e3cb",width=21)
    return image


if __name__=="__main__":
    OUT.mkdir(exist_ok=True)
    for role,modes in MODES.items():
        costume(role).save(OUT/f"{role}_coat.png")
        for mode in modes:
            face(role,mode).save(OUT/f"{role}_{mode}.png")
