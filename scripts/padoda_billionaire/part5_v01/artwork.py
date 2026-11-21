"""Draw Elon's expression and costume cards at 1024 × 1024."""
from pathlib import Path
from PIL import Image, ImageDraw

out=Path(__file__).with_name("art")
out.mkdir(exist_ok=True)
ink="#090910"
for state in ("awe","rest","talk0","talk1","talk2","grin"):
    im=Image.new("RGBA",(1024,1024),(9,9,16,0))
    d=ImageDraw.Draw(im)
    def oval(rect,color):
        d.ellipse(tuple(int(v*4) for v in rect),fill=color)
    def mark(points,width):
        d.line([(int(x*4),int(y*4)) for x,y in points],fill=ink,width=width*4,joint="curve")
        for x,y in (points[0],points[-1]):
            r=width/2;oval((x-r,y-r,x+r,y+r),ink)
    for i,x in enumerate((76,178)):
        mark(((x-24,74+5*i),(x-3,61+i*8),(x+22,76)),9)
        if state in ("awe","talk2"):
            oval((x-24,90,x+24,141),ink);oval((x-18,95,x+18,137),"#fff9ee")
            oval((x-6,106,x+10,126),ink)
        else:
            mark(((x-23,101),(x+23,104)),8)
            oval((x-5,103,x+11,128),ink)
    if state in ("awe","talk2"):
        oval((101,151,156,208),ink)
        oval((115,183,146,201),"#ee8395")
    elif state in ("talk0","talk1"):
        oval((87,159,171,182+(state=="talk1")*12),ink)
        oval((98,164,160,171+(state=="talk1")*6),"#fff3db")
    elif state=="grin":
        oval((83,151,173,193),ink);oval((94,157,162,177),"#fff3dd")
    else:
        mark(((93,172),(126,178),(159,164)),8)
    im.save(out/f"{state}.png")
im=Image.new("RGBA",(1024,1024),"#171a25");p=ImageDraw.Draw(im)
p.polygon([(0,0),(324,0),(402,1024),(0,1024)],fill="#252936")
p.polygon([(1024,0),(700,0),(622,1024),(1024,1024)],fill="#242836")
p.line([(304,100),(384,980)],fill="#697181",width=12)
p.line([(712,100),(641,980)],fill="#5c6374",width=12)
p.line([(430,340),(594,558)],fill="#fff9f0",width=23)
p.line([(598,338),(427,559)],fill="#fff9f0",width=23)
im.save(out/"elon_jacket.png")
