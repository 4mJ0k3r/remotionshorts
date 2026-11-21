"""CPU-only V4 sprites: enclosed scalloped beard and painted cave shading."""
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageChops
import sprites_caveman_v2 as G

ROOT=Path(__file__).resolve().parents[2]/'renders'/'caveman_toilet'
DEST=ROOT/'sprites_v4'
original_hair=G.draw_hair
G.HAIR['elder_clean']=G.HAIR['elder']


def hair_and_beard(img,char):
    original_hair(img,'elder_clean' if char=='elder' else char)
    if char!='elder': return
    # Beard stays strictly inside the round facial contour, including scallops.
    mask=Image.new('L',img.size,0)
    d=ImageDraw.Draw(mask)
    d.rounded_rectangle([G.P(270,620),G.P(754,788)],radius=86*G.SS,fill=255)
    for x,y,r in [(326,760,68),(402,786,70),(486,798,72),(570,798,72),(650,780,68),(704,748,52)]:
        d.ellipse([G.P(x-r,y-r),G.P(x+r,y+r)],fill=255)
    face=Image.new('L',img.size,0)
    ImageDraw.Draw(face).polygon([G.P(*p) for p in G.contour(-1)],fill=255)
    clip=Image.new('L',img.size,0)
    ImageDraw.Draw(clip).rectangle([G.P(0,580),G.P(1024,820)],fill=255)
    mask=ImageChops.multiply(ImageChops.multiply(mask,face),clip)
    beard=Image.new('RGBA',img.size,(232,235,238,0))
    beard.putalpha(mask)
    img.alpha_composite(beard)
    # Fine rounded lobes read as soft hair, never as a pendant triangle.
    line=ImageDraw.Draw(img)
    for x,y in [(345,754),(429,790),(516,799),(604,789),(681,755)]:
        line.arc([G.P(x-27,y-22),G.P(x+27,y+20)],15,155,fill=(181,192,205,190),width=4*G.SS)


def tint(image,warm_right):
    a=np.array(image).astype(np.float32)
    alpha=a[:,:,3].copy()
    bounds=image.getbbox()
    xmin,_,xmax,_=bounds
    x=np.clip((np.arange(image.width)-xmin)/max(1,xmax-xmin),0,1)
    if not warm_right: x=1-x
    x=x*x*(3-2*x)
    cool=np.array([.82*.90,.82*.97,.82*1.08])
    warm=np.array([1.035,.965,.835])
    colors=cool[None,:]*(1-x[:,None])+warm[None,:]*x[:,None]
    a[:,:,:3]=np.clip(a[:,:,:3]*colors[None,:,:],0,255)
    a[:,:,3]=alpha
    return Image.fromarray(a.astype(np.uint8),'RGBA')


def main():
    G.draw_hair=hair_and_beard
    for folder in ('day','warm_left','warm_right'):
        (DEST/folder).mkdir(parents=True,exist_ok=True)
    for char in ('caveman','buddy','elder'):
        names=[f'v2head_{char}_{expr}.png' for expr in G.EXPRS]+[f'v2torso_{char}.png']
        for name in names:
            if char=='elder' and 'head_' in name:
                expr=name.removeprefix('v2head_elder_').removesuffix('.png')
                im=G.draw_head('elder',expr).resize((1024,1024),Image.Resampling.LANCZOS)
            else:
                im=Image.open(ROOT/'sprites'/name).convert('RGBA')
                if 'head_' in name: im=im.resize((1024,1024),Image.Resampling.LANCZOS)
            im.save(DEST/'day'/name)
            tint(im,False).save(DEST/'warm_left'/name)
            tint(im,True).save(DEST/'warm_right'/name)
        print(f'V4 sprites ready: {char}',flush=True)

if __name__=='__main__': main()
