"""Original painted cel assets for the spa cast."""
from pathlib import Path
from math import sin, cos, tau, pi
from PIL import Image, ImageDraw, ImageChops, ImageFilter

OUT = Path(__file__).resolve().parents[2] / 'renders' / 'spa_fart_twist' / 'sprites'
INK = '#161219'
CREAM = '#fdfaf2'

def canvas():
    image = Image.new('RGBA',(768,768))
    return image,ImageDraw.Draw(image)

def crescent(image, mask):
    shifted=Image.new('L',image.size)
    shifted.paste(mask,(37,-31))
    edge=ImageChops.multiply(mask,ImageChops.subtract(mask,shifted).filter(ImageFilter.GaussianBlur(10)))
    paint=Image.new('RGBA',image.size,'#758aa2')
    paint.putalpha(edge.point(lambda v: round(v*.15)))
    image.alpha_composite(paint)

def head(actor, role, mouth):
    im,d=canvas()
    masseur=actor=='m'
    cy=417 if masseur else 408
    radius=257
    def contour(inner):
        return [(384+(radius-inner+3*sin(3*a))*cos(a),cy+(radius-inner+4*cos(2*a))*sin(a))
                for a in (i*tau/144 for i in range(144))]
    if masseur:
        d.ellipse((283,14,471,214),fill='#202025',outline=INK,width=15)
        d.arc((307,28,450,184),198,335,fill='#44404a',width=8)
        d.rounded_rectangle((321,148,449,190),radius=18,fill='#2ec4b6',outline=INK,width=7)
    d.polygon(contour(0),fill=INK)
    mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(contour(14),fill=255)
    fill=Image.new('RGBA',im.size,CREAM);fill.putalpha(mask);im.alpha_composite(fill)
    crescent(im,mask)
    d=ImageDraw.Draw(im)
    if masseur:
        if role=='rear':
            d.ellipse((150,166,618,483),fill='#25242b',outline=INK,width=14)
            for offset in (-100,-50,0,50,100):
                d.line([(384+offset*.25,183),(384+offset,263),(384+offset*1.7,391)],fill='#49434a',width=7)
            return im
        points=[(133,378),(137,310),(166,247),(211,204),(277,172),(365,155),(457,166),
                (545,198),(604,257),(630,337),(607,344),(562,298),(508,285),
                (450,288),(398,320),(344,326),(282,293),(228,296),(180,350)]
        d.polygon(points,fill='#24232a',outline=INK,width=13)
    else:
        points=[(122,454),(100,329),(142,334),(122,241),(182,263),(184,207),(221,220),
                (248,148),(290,185),(357,128),(362,161),(447,128),(425,193),(533,164),
                (516,206),(609,213),(584,258),(649,297),(610,315),(636,391),
                (565,353),(508,292),(478,334),(421,281),(366,343),(309,307),
                (235,408),(226,349),(170,445)]
        d.polygon(points,fill='#4a2810',outline=INK,width=14)
        d.line([(163,307),(237,244),(300,213),(372,192)],fill='#97613a',width=12,joint='curve')
        d.line([(371,241),(439,202),(503,199)],fill='#80502b',width=10)
    closed=role in ('zen','calm','peace')
    angry=role=='angry'
    gaze=26 if role=='skeptic' else 0
    for side in (-1,1):
        x=384+side*98
        y=425
        if role=='dizzy':
            path=[(x+(3+i*.30)*cos(i*.19),y+(3+i*.30)*sin(i*.19)) for i in range(145)]
            d.line(path,fill=INK,width=10)
        elif closed:
            d.arc((x-44,y-16,x+44,y+40),195,345,fill=INK,width=13)
        else:
            ry=45 if role in ('shock','horror','startled') else 35
            pupil=Image.new('L',im.size)
            ImageDraw.Draw(pupil).ellipse((x+gaze-20,y-ry,x+gaze+20,y+ry),fill=255)
            aperture=Image.new('L',im.size)
            ImageDraw.Draw(aperture).rectangle((x-65,y-(15 if role=='skeptic' else 55),x+70,y+55),fill=255)
            eye=Image.new('RGBA',im.size,INK);eye.putalpha(ImageChops.multiply(pupil,aperture));im.alpha_composite(eye);d=ImageDraw.Draw(im)
        if angry:
            d.line((x-49,355-side*21,x+49,355+side*21),fill=INK,width=18)
        elif role not in ('dizzy',):
            d.arc((x-54,338-(13 if role=='shock' else 0),x+54,401),195,340,fill=INK,width=15)
    if mouth or role in ('shock','horror','startled','dizzy'):
        mw=49+mouth*16
        mh=(31+mouth*17) if role!='horror' else 67
        d.ellipse((384-mw,547-mh,384+mw,547+mh),fill='#28161c',outline=INK,width=7)
        if angry or role=='horror': d.rounded_rectangle((384-mw+17,551-mh,384+mw-17,568-mh),radius=7,fill='#fff6e8')
        d.ellipse((350,538+mh*.31,419,540+mh*.76),fill='#de7977')
    elif role=='skeptic':
        d.line((356,550,410,541),fill=INK,width=12)
    else:
        d.arc((324,498,448,580),15,165,fill=INK,width=12)
    return im

def costume(name):
    im,d=canvas()
    if name.startswith('scrub'):
        shape=[(292,92),(478,92),(547,129),(654,233),(588,337),(535,301),(575,651),
               (481,670),(449,634),(392,674),(205,659),(221,303),(174,347),
               (108,247),(202,140)]
        mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(shape,fill=255)
        d.polygon(shape,fill='#2ec4b6',outline=INK,width=15)
        crescent(im,mask);d=ImageDraw.Draw(im)
        if name=='scrub_front':
            d.polygon([(292,94),(476,94),(423,216),(379,333)],fill='#e8fff4',outline=INK,width=8)
            d.line([(296,109),(391,341),(477,603)],fill='#207e80',width=17)
            d.line([(472,109),(430,215),(391,341)],fill='#1a676e',width=10)
            d.rounded_rectangle((465,392,529,465),radius=8,outline='#23817c',width=8)
        else:
            d.arc((297,70,476,156),0,180,fill='#22968e',width=9)
    elif name.startswith('pants'):
        d.polygon([(221,41),(546,41),(577,241),(625,670),(460,673),(390,343),
                   (302,677),(137,672),(186,278)],fill='#f8f9fa',outline=INK,width=15)
        d.line([(247,205),(223,424),(199,652)],fill='#d2d8dd',width=16)
        d.line([(519,233),(544,407),(568,651)],fill='#dfe2e2',width=14)
        if name.endswith('stain'):
            d.polygon([(338,202),(362,183),(395,200),(427,194),(448,234),(432,268),
                       (411,272),(396,304),(370,278),(344,285),(323,245)],fill='#754420')
    else:
        d.polygon([(16,449),(27,368),(73,363),(105,327),(200,269),(277,274),(367,303),
                   (491,319),(667,307),(741,344),(753,509),(683,535),(226,534),
                   (126,511),(76,489)],fill='#f7d7b5',outline=INK,width=13)
        d.line([(82,355),(141,314),(202,284),(275,288),(369,318),(504,334)],
               fill='#ffeacf',width=10,joint='curve')
        d.arc((117,379,378,532),195,302,fill='#ce997b',width=9)
    return im

def effects():
    for name in ('sweat','soul','puff'):
        im,d=canvas()
        if name=='sweat':
            d.polygon([(406,124),(270,367),(244,488),(312,580),(421,626),(526,550),(545,427)],fill='#76e8ef',outline='#286078',width=18)
            d.ellipse((307,374,349,482),fill='#dafbff')
        elif name=='soul':
            size=(512,512)
            mask=Image.new('L',size);shape=ImageDraw.Draw(mask)
            shape.ellipse((66,37,446,405),fill=184)
            shape.polygon([(175,353),(350,342),(325,406),(253,438),(228,488),
                           (165,505),(202,465),(188,415),(149,386)],fill=184)
            mask=mask.filter(ImageFilter.GaussianBlur(8))
            outer=ImageChops.subtract(mask.filter(ImageFilter.MaxFilter(25)),mask)
            im=Image.new('RGBA',size,(236,250,255,0))
            im.putalpha(outer.filter(ImageFilter.GaussianBlur(8)))
            head_layer=Image.new('RGBA',size,(176,231,255,0));head_layer.putalpha(mask)
            im.alpha_composite(head_layer)
            d=ImageDraw.Draw(im)
            for x in (187,322):
                pts=[(x+(2+i*.20)*cos(i*.20),209+(2+i*.20)*sin(i*.20)) for i in range(159)]
                d.line(pts,fill=(55,104,139,210),width=7)
                d.arc((x-34,139,x+36,177),192,338,fill=(76,122,153,210),width=7)
            d.polygon([(191,308),(206,279),(228,273),(251,284),(275,274),(301,283),
                       (323,310),(302,332),(276,324),(245,335),(218,326)],
                      fill=(69,109,141,211))
            d.arc((218,296,303,328),190,319,fill=(202,238,250,175),width=5)
        else:
            for x,y,r in [(320,399,184),(468,380,162),(523,494,135),(211,459,115),(364,527,143)]:
                d.ellipse((x-r,y-r,x+r,y+r),fill=(170,196,84,101),outline=(216,210,109,130),width=12)
            im=im.filter(ImageFilter.GaussianBlur(23))
        im.save(OUT/f'{name}.png')

if __name__=='__main__':
    OUT.mkdir(parents=True,exist_ok=True)
    roles={'m':['zen','shock','talk','startled','rear','calm'],
           'c':['peace','shock','skeptic','angry','horror','dizzy']}
    for actor,poses in roles.items():
        for role in poses:
            for mouth in (range(4) if role in ('talk','calm','angry') else (0,)):
                head(actor,role,mouth).save(OUT/f'{actor}_{role}_{mouth}.png')
    for name in ('scrub_front','scrub_back','pants','pants_stain','client_body'):
        costume(name).save(OUT/f'{name}.png')
    effects()
