"""Original rear-three-quarter cel: face sliver points toward the bowl."""
from math import sin,cos,pi
from PIL import Image,ImageDraw,ImageChops,ImageFilter
from timeline import OUT

im=Image.new('RGBA',(1024,1024),(22,18,25,0));d=ImageDraw.Draw(im)
ink='#141215';cream='#f5f2e8'
outer=[];inner=[]
for j in range(256):
    a=j*2*pi/256;r=1+.015*sin(2*a+.4)-.009*cos(3*a-.7);w=9*(1+.35*cos(a-2.4))
    outer.append((512+(365*r+w)*cos(a),513+(379*r+w)*sin(a)))
    inner.append((512+(365*r-w)*cos(a),513+(379*r-w)*sin(a)))
d.polygon(outer,fill=ink);d.polygon(inner,fill=cream)
mask=Image.new('L',im.size);ImageDraw.Draw(mask).polygon(inner,fill=255)
shift=Image.new('L',im.size);shift.paste(mask,(29,-22))
cres=ImageChops.subtract(mask,shift).filter(ImageFilter.GaussianBlur(7))
shade=Image.new('RGBA',im.size,(59,91,122,0));shade.putalpha(cres.point(lambda x:round(x*.15)));im.alpha_composite(shade)
d=ImageDraw.Draw(im)
d.polygon([(168,367),(193,244),(317,149),(481,107),(641,129),(788,226),(867,361),
           (875,530),(828,633),(720,680),(604,656),(497,574),(417,474),(356,348),(281,318),(222,353)],fill='#46302b',outline=ink,width=16)
d.line([(230,269),(341,192),(472,159),(603,175),(727,245)],fill='#856142',width=13,joint='curve')
d.line([(785,349),(801,483),(755,577)],fill='#684932',width=10,joint='curve')
# Only the near ear and a narrow profile are visible; no front-facing face.
d.ellipse((316,476,413,622),fill=cream,outline=ink,width=15)
d.arc((339,505,389,589),95,285,fill=ink,width=11)
d.line([(168,460),(208,449),(227,464)],fill=ink,width=10,joint='curve')
d.line([(166,512),(134,558),(163,577)],fill=cream,width=20,joint='curve')
d.line([(166,512),(134,558),(163,577)],fill=ink,width=9,joint='curve')
d.line([(166,626),(203,634)],fill=ink,width=9)
im.save(OUT/'sprites'/'boy_rear_0_0.png')
print('Rear/side head art prepared')
