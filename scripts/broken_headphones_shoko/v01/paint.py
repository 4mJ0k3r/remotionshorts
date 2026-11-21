"""Paint the original cast's expression and clothing cards."""
from pathlib import Path
from random import Random

from PIL import Image,ImageDraw

ART=Path(__file__).with_name("art")
INK="#161020"
MODES={
    "boy":("deadpan_blush","year7_shock","panic_sweat","shout_what","warm_smile","joyful_grin","hollow_still"),
    "shoko":("shy_glance","happy_chatter","worried_brows","peaceful_sleep","stunned_freeze",
             "deep_crimson_blush","radiant_joy","chat_A","chat_E","chat_O","chat_M"),
    "classmate":("greet","smile"),
}


def draw_face(role,mode):
    image=Image.new("RGBA",(1024,1024),(22,16,32,0))
    d=ImageDraw.Draw(image)

    def ellipse(x,y,rx,ry,fill):
        d.ellipse(tuple(round(v*4) for v in (x-rx,y-ry,x+rx,y+ry)),fill=fill)

    def poly(p,color):
        d.polygon([(round(4*x),round(4*y)) for x,y in p],fill=color)

    def line(p,w,color=INK):
        d.line([(round(x*4),round(y*4)) for x,y in p],width=round(w*4),fill=color,joint="curve")
        for x,y in (p[0],p[-1]):
            ellipse(x,y,w/2,w/2,color)

    fright=mode in ("year7_shock","panic_sweat","shout_what","stunned_freeze")
    closed=mode in ("peaceful_sleep","joyful_grin","radiant_joy")
    dead=mode in ("deadpan_blush","hollow_still")
    violet=role=="shoko"
    for side in (-1,1):
        x=128+side*48
        brow=58 if fright else 67
        line([(x-24,brow+side*1.8),(x-12,brow-3),(x+7,brow-1),(x+21,brow+3)],9.5)
        if closed:
            line([(x-26,116),(x-15,102),(x,96),(x+15,102),(x+27,115)],7)
        else:
            ry=29 if fright else 15 if dead else 24
            ellipse(x,108,33,ry,INK)
            ellipse(x,108,28,ry-4,"#fff9f6")
            ox=x+(9 if mode in ("shy_glance","happy_chatter","chat_A","chat_E","chat_O","chat_M") else -3 if dead else 1)
            ellipse(ox,108+(3 if dead else 0),9 if fright else 13,10 if fright else ry-6,
                    "#563683" if violet else "#403246")
            ellipse(ox+1,108,5 if fright else 7,7 if fright else min(10,ry-4),INK)
            ellipse(ox-4,104,3.1,3.1,"#fffbf6")
            if dead:
                line([(x-31,100),(x-8,99),(x+28,100)],7)
            if violet:
                for k in range(2):
                    q=x+side*(27+3*k)
                    line([(q,97+k*3),(q+side*(5+k),91+k*3)],3)
        if violet or mode in ("deadpan_blush","warm_smile"):
            tone="#d86d87" if mode=="deep_crimson_blush" else "#ecabaf"
            for k in range(4):
                sx=x-14+8*k
                line([(sx,145+k*.7),(sx+3.5,137+k*.7)],2.8,tone)
    if mode in ("panic_sweat","shout_what","year7_shock","stunned_freeze","chat_A","chat_O","greet"):
        w,h=(23,23) if fright else (16,15) if mode=="chat_O" else (24,12)
        ellipse(128,175,w,h,INK)
        ellipse(128,180,w*.63,h*.38,"#da788b")
        if mode not in ("chat_O","stunned_freeze"):
            ellipse(128,166,w*.67,h*.18,"#fff5e5")
    elif mode in ("hollow_still","deadpan_blush","chat_M","worried_brows","peaceful_sleep","deep_crimson_blush"):
        line([(108,175),(124,176),(144,175)],4)
    else:
        poly([(98,164),(115,167),(140,167),(159,161),(150,182),(130,190),(113,186)],INK)
        poly([(104,167),(145,169),(151,165),(147,174),(118,176)],"#fff4e1")
        ellipse(132,182,12,4,"#d87993")
    return image


def coat(role):
    bg={"boy":"#21242f","shoko":"#a6a1b0","classmate":"#324968"}[role]
    image=Image.new("RGBA",(1024,1024),bg)
    d=ImageDraw.Draw(image)
    if role=="boy":
        d.arc((215,-240,809,390),190,350,fill="#545465",width=42)
        d.arc((225,-205,799,395),18,162,fill="#c8d2df",width=19)
        for j in range(12):
            x=282+j*42
            y=168+int(49*(1-((x-512)/242)**2))
            d.ellipse((x,y,x+24,y+14),outline="#b2beca",width=4)
        d.polygon([(334,410),(520,332),(699,424),(633,587),(508,674),(341,593)],fill="#ebe5de")
        d.polygon([(402,466),(510,389),(624,466),(579,546),(510,584),(416,539)],fill="#40354c")
        d.polygon([(526,420),(472,511),(524,502),(488,563),(575,469),(524,475)],fill="#eee8e1")
        for x in (403,621):
            d.line([(x,104),(x+12,288)],fill="#9599a7",width=18)
        d.arc((284,690,742,927),200,340,fill="#57596a",width=16)
    elif role=="shoko":
        for j in range(52):
            x=j*20
            for i in range(17):
                y=i*39
                tone=("#b6afbd","#9692a3")[int(j%3==0)]
                d.line([(x-8,y),(x,y+13),(x+8,y)],fill=tone,width=3)
        d.polygon([(320,0),(700,0),(540,383),(476,383)],fill="#fbf0ed")
        d.polygon([(459,172),(327,109),(350,246),(474,224),(665,261),(699,135),(541,169)],fill="#ae88cc")
        d.rounded_rectangle((462,159,547,251),radius=15,fill="#c99be1")
        for x in (365,654):
            d.line([(x,34),(x-18,222),(x+30,589)],fill="#7f758e",width=13)
        d.rectangle((0,675,1023,1023),fill="#5d596e")
        for x in range(15,1024,130):
            d.line([(x,675),(x,1024)],fill="#827b92",width=16)
            d.line([(x+22,675),(x+22,1024)],fill="#b1a3ba",width=3)
        for y in range(700,1024,82):
            d.line([(0,y),(1024,y)],fill="#a093a9",width=7)
    else:
        d.polygon([(315,0),(705,0),(555,554),(450,554)],fill="#f1e6d8")
        d.polygon([(470,67),(556,67),(547,349),(512,418),(477,346)],fill="#b45a68")
        d.rounded_rectangle((637,364,762,488),radius=13,fill="#a9784c")
        d.ellipse((660,383,741,468),fill="#d9ba72")
    return image


def notebook():
    image=Image.new("RGB",(850,1080),"#fcf2df")
    d=ImageDraw.Draw(image)
    for y in range(90,1080,43):d.line((40,y,818,y+1),fill="#829cbb",width=5)
    d.line((113,22,113,1061),fill="#c87f8b",width=5)
    for y in range(34,1070,43):
        d.arc((-34,y,72,y+33),180,360,fill="#70698a",width=7)
    d.ellipse((247,284,602,617),outline="#43415b",width=13)
    d.arc((219,235,630,643),175,367,fill="#353447",width=27)
    d.rounded_rectangle((213,411,276,562),radius=25,fill="#353447")
    d.rounded_rectangle((571,416,638,562),radius=25,fill="#353447")
    d.line([(258,429),(310,310),(345,346),(404,273),(450,323),(500,278),(562,350),(591,411)],
           fill="#353447",width=18,joint="curve")
    for x in (344,509):
        d.ellipse((x-42,433,x+41,482),outline="#43415b",width=10)
        d.ellipse((x-9,447,x+10,476),fill="#43415b")
    d.arc((382,490,470,551),1,156,fill="#43415b",width=8)
    d.line([(246,547),(269,640),(298,720)],fill="#43415b",width=11)
    d.arc((324,600,530,858),180,362,fill="#43415b",width=12)
    rng=Random(83)
    for x,y,r in ((196,215,48),(674,270,52),(159,674,40),(704,627,48),(592,846,36),(258,879,33)):
        p=[(x-r*.62,y-r*.39),(x-r*.95,y-r*.76),(x-r*.65,y-r*1.18),(x-r*.25,y-r*.93),
           (x,y-r*.56),(x+r*.34,y-r*.96),(x+r*.80,y-r*.80),(x+r*.68,y-r*.36),(x,y+r*.39)]
        d.line(p+[p[0]],fill="#d76c97",width=rng.randint(7,10),joint="curve")
    return image


if __name__=="__main__":
    ART.mkdir(exist_ok=True)
    for role,modes in MODES.items():
        coat(role).save(ART/f"{role}_coat.png")
        for mode in modes:
            draw_face(role,mode).save(ART/f"{role}_{mode}.png")
    notebook().save(ART/"notebook.png")
