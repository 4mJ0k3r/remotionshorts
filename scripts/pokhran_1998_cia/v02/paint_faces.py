"""Original Studio face cards at the larger v02 eye and eyebrow scale."""
from pathlib import Path
from shutil import copyfile
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
SOURCE = HERE.parent / "v01b/art"
OUT = HERE / "art"
INK = "#161020"


def face(source, mode):
    im = Image.open(source).convert("RGBA")
    d = ImageDraw.Draw(im)
    d.rectangle((0,0,1023,563), fill=(22,16,32,0))

    def ellipse(x,y,rx,ry,fill):
        d.ellipse(tuple(round(v*4) for v in (x-rx,y-ry,x+rx,y+ry)),fill=fill)

    def stroke(points,width,color=INK):
        d.line([(round(4*x),round(4*y)) for x,y in points],fill=color,width=width*4,joint="curve")
        for x,y in (points[0],points[-1]):
            ellipse(x,y,width/2,width/2,color)

    for sign in (-1,1):
        x=128+sign*48
        y=105 if mode!="shock" else 107
        brow=(54 if mode=="shock" else 61)+(6 if sign==1 and mode=="rest" else 0)
        stroke([(x-25,brow+5),(x-12,brow),(x+5,brow-2),(x+22,brow+2)],12)
        if mode=="sip":
            stroke([(x-27,y+12),(x-15,y-1),(x,y-8),(x+14,y-2),(x+27,y+10)],8)
        else:
            r=34 if mode=="shock" else 25
            ellipse(x,y,37 if mode=="shock" else 33,r,INK)
            ellipse(x,y,32 if mode=="shock" else 28,r-5,"#fff7e8")
            px=x+(0 if mode=="shock" else 7)
            ellipse(px,y+1,9 if mode=="shock" else 14,14 if mode=="shock" else 17,INK)
            ellipse(px-4,y-5,3.6,3.6,"#fff7e8")
    if mode=="shock":
        d.rectangle((320,534,700,828),fill=(22,16,32,0))
        ellipse(128,180,34,33,INK)
        ellipse(128,196,20,7,"#d26c70")
    return im


if __name__=="__main__":
    OUT.mkdir(exist_ok=True)
    for source in SOURCE.glob("*.png"):
        if source.stem.endswith("_coat"):
            copyfile(source, OUT/source.name)
            continue
        mode=source.stem.split("_")[1]
        face(source,mode).save(OUT/source.name)
        if mode=="AA":
            face(source,"shock").save(OUT/(source.stem.split("_")[0]+"_shock.png"))
