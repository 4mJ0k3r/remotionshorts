"""V2 local artwork corrections; preserve all V1 packed art and narration."""
from pathlib import Path
from PIL import Image,ImageDraw,ImageChops,ImageFilter,ImageFont
import prepare_assets as a
a.ART=Path(r'D:\remotionshorts\renders\bamboo_ambush\assets_v2');a.ART.mkdir(exist_ok=True)
original_eye=a.draw_clipped_eye
def solid_eye(im,cx,cy,rx,ry,top_ratio,bot_ratio,pupil_dx=0,pupil_dy=0,pupil_scale=1.,veins=False):
 if veins:return original_eye(im,cx,cy,rx,ry,top_ratio,bot_ratio,pupil_dx,pupil_dy,pupil_scale,veins=True)
 d=ImageDraw.Draw(im)
 if top_ratio>=bot_ratio:a.ink_line(d,[(cx-rx*.65,cy),(cx+rx*.65,cy)],width=12);return im
 layer=a.canvas();ld=ImageDraw.Draw(layer);px=cx+pupil_dx;py=cy+pupil_dy;prx=rx*.43;pry=ry*.78;ld.ellipse((px-prx,py-pry,px+prx,py+pry),fill='#161219')
 clip=Image.new('L',(a.N,a.N),0);cd=ImageDraw.Draw(clip);top=cy-ry+2*ry*top_ratio;bottom=cy-ry+2*ry*bot_ratio;cd.rectangle((cx-rx,top,cx+rx,bottom),fill=255);layer.putalpha(ImageChops.multiply(layer.getchannel('A'),clip));im=Image.alpha_composite(im,layer)
 if top_ratio>.02:a.ink_line(ImageDraw.Draw(im),[(cx-rx*.67,top),(cx+rx*.67,top)],width=10)
 if bot_ratio<.98:a.ink_line(ImageDraw.Draw(im),[(cx-rx*.58,bottom),(cx+rx*.58,bottom)],width=8)
 return im
a.draw_clipped_eye=solid_eye
a.build_soldier_head();a.build_enemy_head();a.build_soldier_torso();a.build_soldier_faces();a.build_enemy_faces();a.build_fx_and_hud()
# Restore the exact cream/shading and brown strap beneath the removed brass buckle.
im=Image.open(a.ART/'soldier_head.png').convert('RGBA');under=a.canvas();d=ImageDraw.Draw(under);outer,inner=a.rough_head_contours(cx=768,cy=825,rx=500,ry=480,w0=14);d.polygon(outer,fill=a.INK);d.polygon(inner,fill=a.CREAM);mask=Image.new('L',(a.N,a.N),0);ImageDraw.Draw(mask).polygon(inner,fill=255);under=a.apply_cel_shading(under,mask,a.CREAM,.25,.18,True);d=ImageDraw.Draw(under);strap=[(280,760),(312,990),(470,1210),(768,1285),(1066,1210),(1224,990),(1256,760)];d.line(strap,fill=a.INK,width=42,joint='curve');d.line(strap,fill='#5c3d24',width=22,joint='curve');box=(417,1137,494,1220);im.paste(under.crop(box),box);im.save(a.ART/'soldier_head.png')
# Unified jersey silhouette without the protruding neck tab.
mask=Image.new('L',(a.N,a.N),0);ImageDraw.Draw(mask).rounded_rectangle((270,220,1266,1370),radius=265,fill=255);outline=Image.new('RGBA',(a.N,a.N),a.INK);outline.putalpha(mask);inner=mask.filter(ImageFilter.MinFilter(29));fill=a.canvas();fill.paste(Image.new('RGBA',(a.N,a.N),'#008751'),(0,0),inner);fill=a.apply_cel_shading(fill,inner,'#008751',.25,.18);im=Image.alpha_composite(outline,fill);detail=a.canvas();d=ImageDraw.Draw(detail)
for pts in [[(310,345),(560,220),(610,250),(340,410)],[(1226,345),(976,220),(926,250),(1196,410)]]:d.polygon(pts,fill='white',outline=a.INK,width=9)
d.polygon([(642,220),(894,220),(768,402)],fill=a.CREAM);a.ink_line(d,[(642,225),(768,402),(894,225)],width=39,fill=a.INK);a.ink_line(d,[(642,225),(768,402),(894,225)],width=23,fill='white')
d.text((768,555),'NEW YORK',font=ImageFont.truetype(a.FONT_BOLD,108),anchor='mm',fill='white',stroke_width=10,stroke_fill=a.INK);d.text((768,890),'17',font=ImageFont.truetype(a.FONT_BOLD,410),anchor='mm',fill='white',stroke_width=14,stroke_fill=a.INK);detail.putalpha(ImageChops.multiply(detail.getchannel('A'),inner));im=Image.alpha_composite(im,detail);im.save(a.ART/'enemy_torso.png')
print('V2 assets: solid pupils, recessed jersey collar, no chin buckle. V1 preserved.')
