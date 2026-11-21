"""Original ink expressions, fabric cards and on-screen scale graphics."""
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

ART = Path(__file__).with_name("art")
INK = "#161020"
IVORY = "#fff3df"
GOLD = "#ffd05f"


def face(role, mode):
    canvas = Image.new("RGBA", (1024, 1024), (22, 16, 32, 0))
    draw = ImageDraw.Draw(canvas)

    def oval(x, y, width, height, fill):
        draw.ellipse(tuple(round(i*4) for i in (x-width,y-height,x+width,y+height)), fill=fill)

    def line(points, width, tone=INK):
        draw.line([(x*4,y*4) for x,y in points], fill=tone, width=round(width*4), joint="curve")
        for x,y in (points[0],points[-1]):
            oval(x,y,width/2,width/2,tone)

    for sign in (-1,1):
        x = 128+sign*49
        raise_brow = 10 if mode in {"curious","shock","hope"} else 0
        line([(x-25,69-raise_brow+3*sign),(x-8,61-raise_brow),(x+22,66-raise_brow-4*sign)],9.6)
        height = {"grin":21,"curious":30,"hope":29,"deadpan":13,"strain":19,"awkward":21,
                  "shock":34,"sideeye":18}.get(mode,23)
        oval(x,108,34,height,INK)
        oval(x,108,28.7,height-4.7,IVORY)
        iris = x+(12 if mode in {"curious","hope","sideeye"} else -9 if mode=="awkward" else 0)
        pupil = 7 if mode in {"shock","strain"} else 11
        oval(iris,110,pupil,min(height-6,14),"#4e4439" if role=="hero" else "#4b6876")
        oval(iris+.8,111,pupil*.58,min(height-7,9),INK)
        oval(iris-3.1,106,3.2,3.2,IVORY)
        if mode in {"deadpan","strain","sideeye"}:
            line([(x-30,104),(x-2,98),(x+29,101)],5.0)
        for j in range(3):
            line([(x-10+j*7,142),(x-6+j*7,138)],2.5,"#cf897c")

    if mode in {"shock","curious"}:
        oval(130,178,22,22,INK)
        oval(130,185,13,7,"#dc7c86")
        oval(130,167,14,3,IVORY)
    elif mode in {"deadpan","sideeye"}:
        line([(105,177),(126,176),(150,177)],4.8)
    elif mode == "strain":
        line([(92,171),(109,176),(125,169),(145,175),(162,168)],7.0)
    else:
        draw.polygon([(x*4,y*4) for x,y in ((93,167),(109,172),(140,170),(162,159),
                     (153,185),(129,196),(106,186))],fill=INK)
        line([(105,174),(128,177),(150,169)],5,IVORY)
        oval(130,188,12,4,"#d47987")
    return canvas


def outfit(role):
    hero = role=="hero"
    canvas=Image.new("RGBA",(1024,1024),"#b62a35" if hero else "#168984")
    draw=ImageDraw.Draw(canvas)
    draw.polygon(((0,690),(261,742),(680,736),(1024,688),(1024,1024),(0,1024)),
                 fill="#657087" if hero else "#2b4453")
    draw.arc((253,-116,774,302),0,180,fill=INK,width=33)
    if hero:
        for x,d in ((417,-22),(603,34)):
            draw.line((x,151,x+d,446),fill="#ffd8b6",width=25)
            draw.rounded_rectangle((x+d-15,417,x+d+13,464),radius=12,fill="#3b202e")
        draw.rounded_rectangle((290,520,731,688),radius=63,outline="#f76e66",width=19)
        draw.line((310,596,710,596),fill="#8c263b",width=8)
    else:
        draw.polygon(((422,274),(559,274),(513,372),(604,372),(442,513),(470,398),(393,398)),fill="#c9e7d4")
    return canvas


def font(size, kind="bold"):
    names={"bold":"segoeuib.ttf","normal":"segoeui.ttf","heavy":"seguisb.ttf"}
    return ImageFont.truetype(str(Path("C:/Windows/Fonts")/names[kind]),size)


def calendar(draw, x, y, size, day, *, shadow=True):
    s=size/240
    def p(a,b):
        return x+round(a*s), y+round(b*s)
    def rounded(a,b,c,d,fill,r=18):
        draw.rounded_rectangle((*p(a,b),*p(c,d)),radius=round(r*s),fill=fill)
    def label(a,b,text,scale,fill,kind="bold"):
        draw.text(p(a,b),text,font=font(max(9,round(scale*s)),kind),fill=fill,anchor="mm")
    if shadow:
        rounded(5,8,245,230,(13,15,32,165))
    rounded(0,0,240,222,IVORY)
    rounded(0,0,240,58,"#b53442")
    draw.rectangle((*p(0,34),*p(240,58)),fill="#b53442")
    label(120,29,"NOVEMBER",31,IVORY)
    for i in range(6):
        yy=66+i*27
        draw.line((*p(14,yy),*p(226,yy)),fill="#c7a4a6",width=max(1,round(1.4*s)))
    for i in range(8):
        xx=14+i*30
        draw.line((*p(xx,66),*p(xx,200)),fill="#d0afb0",width=max(1,round(1.4*s)))
    for n in range(1,31):
        xx=29+((n-1)%7)*30
        yy=80+((n-1)//7)*27
        label(xx,yy,str(n),16,"#3a354e")
        if n<=day:
            if day==0:
                continue
            for tilt in (-1,1):
                draw.line((*p(xx-7,yy-7*tilt),*p(xx+7,yy+7*tilt)),fill="#bb263f",width=max(2,round(3.5*s)))
        elif n==1 and day==0:
            draw.ellipse((*p(xx-11,yy-11),*p(xx+11,yy+11)),outline="#bb263f",width=max(2,round(3*s)))


def hud(day):
    canvas=Image.new("RGBA",(1080,1920),(0,0,0,0))
    draw=ImageDraw.Draw(canvas)
    calendar(draw,780,75,235,day)
    if day:
        draw.rounded_rectangle((61,78,510,310),radius=32,fill=(9,10,24,228))
        draw.text((86,87),f"DAY {day}",font=font(40),fill=GOLD)
        draw.text((81,117),("8 cm" if day==1 else "16 cm"),font=font(88),fill=IVORY)
        draw.text((87,221),("LIKE ORANGES" if day==1 else "LIKE MELONS"),font=font(28),fill=IVORY)
        draw.rounded_rectangle((85,263,331,302),radius=20,fill=GOLD)
        draw.text((208,282),"×2 EVERY DAY",font=font(24),fill=INK,anchor="mm")
    return canvas


def feature_hud(day, size="", comparison=""):
    canvas=Image.new("RGBA",(1080,1920),(0,0,0,0))
    d=ImageDraw.Draw(canvas)
    if day==0:
        d.rounded_rectangle((780,75,1015,262),radius=20,fill=IVORY)
        d.rounded_rectangle((780,75,1015,133),radius=20,fill="#b53442")
        d.text((897,105),"DECEMBER",font=font(31),anchor="mm",fill=IVORY)
        d.text((897,191),"1",font=font(71),anchor="mm",fill=INK)
        return canvas
    calendar(d,780,75,235,day)
    d.rounded_rectangle((61,78,571,310),radius=30,fill=(9,10,24,228))
    d.text((86,87),f"DAY {day}",font=font(40),fill=GOLD)
    d.text((81,124),size,font=font(69 if len(size)>6 else 84),fill=IVORY)
    d.text((87,221),comparison,font=font(27),fill=IVORY)
    d.rounded_rectangle((85,263,331,302),radius=20,fill=GOLD)
    d.text((208,282),"×2 EVERY DAY",font=font(24),fill=INK,anchor="mm")
    return canvas


def victory():
    im=Image.new("RGBA",(600,1060),"#202744")
    d=ImageDraw.Draw(im)
    for y in range(50,1040,25):
        for x in range(38+(y%2)*12,590,28):
            d.line((x-4,y,x+4,y),fill="#536388",width=2)
            d.line((x,y-4,x,y+4),fill="#536388",width=2)
    for i in range(9):
        d.arc((-120+15*i,256+13*i,720-15*i,968-13*i),222,322,fill="#7e6b99",width=2)
        d.arc((-120+15*i,256+13*i,720-15*i,968-13*i),39,141,fill="#7e6b99",width=2)
    d.rounded_rectangle((27,28,573,1032),radius=50,outline="#575886",width=8)
    d.text((300,117),"TUE, DEC 1",font=font(47),fill=IVORY,anchor="mm")
    d.text((300,218),"12:00",font=font(119),fill=IVORY,anchor="mm")
    d.rounded_rectangle((84,347,516,809),radius=63,fill="#272440",outline="#dca777",width=5)
    for ring in range(7):
        pad=ring*10
        d.ellipse((140+pad,380+pad,460-pad,700-pad),outline="#655176",width=2)
    d.arc((164,420,439,605),0,180,fill=GOLD,width=20)
    d.polygon(((208,427),(392,427),(370,563),(320,606),(320,644),(362,644),(362,668),
              (238,668),(238,644),(280,644),(280,606),(230,563)),fill=GOLD)
    d.text((300,721),"CHALLENGE",font=font(47),fill=GOLD,anchor="mm")
    d.text((300,774),"COMPLETED",font=font(48),fill=IVORY,anchor="mm")
    for x in (178,239,300,361,422):
        d.polygon(((x,893),(x+5,903),(x,913),(x-5,903)),fill=GOLD)
    return im


def turning_page(phase):
    november=feature_hud(30,"42,950 km","OVER 3 EARTHS WIDE")
    december=feature_hud(0)
    image=november if phase<2 else december
    rect=(765,66,1029,313)
    page=image.crop(rect)
    image.paste((0,0,0,0),rect)
    proportion=(.68,.22,.20,.69)[phase]
    page=page.resize((264,round(247*proportion)),Image.Resampling.LANCZOS)
    image.alpha_composite(page,(765,76+(44 if phase in (1,2) else 16)))
    return image


def phone(rejected):
    canvas=Image.new("RGBA",(600,1060),"#172039")
    d=ImageDraw.Draw(canvas)
    d.rounded_rectangle((10,10,590,1050),radius=48,fill="#252942")
    for j in range(17):
        xx=25+j*34
        d.line((xx,191,xx,970),fill="#475772" if j%3 else "#59708d",width=3)
    for j in range(19):
        yy=196+j*43
        d.line((22,yy,576,yy),fill="#475772",width=3)
    d.rectangle((18,104,582,182),fill="#354669")
    d.text((55,35),"2:00 AM",font=font(39),fill=IVORY)
    d.text((300,142),"MESSAGES",font=font(40),fill=IVORY,anchor="mm")
    d.ellipse((56,264,122,330),fill="#587ba5")
    d.rounded_rectangle((138,242,474,344),radius=32,fill="#597dab")
    d.text((161,265),"u up?",font=font(44),fill=IVORY)
    if rejected:
        d.ellipse((56,426,122,492),fill="#b66a8b")
        d.rounded_rectangle((140,403,550,501),radius=33,fill="#855570")
        d.text((160,427),"wrong number lol",font=font(36),fill=IVORY)
        d.polygon(((288,615),(250,580),(228,585),(213,605),(217,633),(285,700),(302,668),
                   (275,641)),fill="#b85b78")
        d.polygon(((310,613),(345,580),(369,587),(384,607),(378,635),(301,702),(313,669),
                   (297,646)),fill="#b85b78")
        for cx,cy in ((188,611),(408,630),(235,708),(380,710)):
            d.line((cx-10,cy,cx+10,cy),fill="#da98ae",width=3)
            d.line((cx,cy-10,cx,cy+10),fill="#da98ae",width=3)
    d.rounded_rectangle((52,862,548,945),radius=27,outline="#67718d",width=4)
    d.text((81,879),"Message",font=font(33),fill="#adb8cf")
    d.ellipse((479,881,526,928),fill="#587ba5")
    d.rounded_rectangle((214,995,387,1009),radius=6,fill="#e0dce8")
    return canvas


if __name__=="__main__":
    ART.mkdir(exist_ok=True)
    for role, modes in (("hero",("grin","curious","hope","deadpan","strain","awkward","shock")),
                        ("bro",("sideeye","shock","grin","strain"))):
        outfit(role).save(ART/f"{role}_outfit.png")
        for mode in modes:
            face(role,mode).save(ART/f"{role}_{mode}.png")
    for i in range(3):
        hud(i).save(ART/f"hud_{i}.png")
    wall=Image.new("RGBA",(480,444),(0,0,0,0))
    calendar(ImageDraw.Draw(wall),0,0,480,0,shadow=False)
    wall.save(ART/"wall_calendar.png")
    for i in range(2):
        phone(i).save(ART/f"phone_{i}.png")
    for spec in ((3,"32 cm","LIKE WATERMELONS"),(4,"64 cm","LIKE YOGA BALLS"),(6,"2.56 m","TALLER THAN A DOORWAY"),
                 (8,"10.2 m","3-STORY BUILDING"),(30,"42,950 km","OVER 3 EARTHS WIDE"),(0,"","")):
        suffix = "december" if spec[0] == 0 else spec[0]
        feature_hud(*spec).save(ART/f"hud_{suffix}.png")
    victory().save(ART/"victory.png")
    for phase in range(4):
        turning_page(phase).save(ART/f"hud_turn{phase}.png")
