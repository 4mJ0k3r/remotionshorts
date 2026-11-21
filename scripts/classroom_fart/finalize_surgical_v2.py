"""Rebake only the pressure, rear stream, rear lens and shoe thickness fixes."""
import bpy,ast,json,math,sys
from pathlib import Path
from mathutils import Vector as V,Matrix,Quaternion
HERE=Path(__file__).resolve().parent;OUT=Path(r'D:\remotionshorts\renders\classroom_fart');sys.path.insert(0,str(HERE))
from primitives import key,linear
SEAT=.46;DESK_TOP=1.0125;CHAIR_Y=-.2;SHOE_R=.015
HEAD_LOWER=json.loads((OUT/'assets_surgical_v2/head_bounds.json').read_text())['you_lower_world'];SLUMP_PITCH=math.acos(.18/HEAD_LOWER)
ENV=json.loads((OUT/'audio_envelope.json').read_text());rows=json.loads((OUT/'shots_v2.json').read_text())['shots']
def author(p):return V((-p[0],-p[1]-.2,p[2]))
def ease(a,b,f):u=max(0.,min(1.,(f-a)/(b-a)));return u*u*(3-2*u)
def lerp(a,b,u):return V(a).lerp(V(b),u)
def setloc(o,p,f):o.location=p;key(o,'location',f)
def scale(o,s,f):o.scale=(s,)*3 if isinstance(s,(float,int)) else s;key(o,'scale',f)
tree=ast.parse((HERE/'build_classroom_fart.py').read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['camera_pose','effects','curve_set']]
cls=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='Actor');functions.append(next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='pose'))
exec(compile(ast.Module(body=functions,type_ignores=[]),'<surgical function rebake>','exec'),globals())
CAM=bpy.data.objects['Delivery camera'];FOCUS=bpy.data.objects['Active face or physical contact focus'];BELLY=bpy.data.objects['Internal pressure pulse'];GASLIGHT=bpy.data.objects['Translucent vapor local bounce'];FILL=bpy.data.objects['Quiet cool classroom bounce']
def objs(prefix):return sorted([o for o in bpy.data.objects if o.name.startswith(prefix)],key=lambda o:o.name)
PRESSURE=[bpy.data.objects['V2 centered compressed pressure '+str(i)] for i in range(3)]
STREAM=[bpy.data.objects['V2 rear fart stream '+str(i)] for i in range(14)];HAZE=[bpy.data.objects['V2 desk toxic haze '+str(i)] for i in range(16)]
RINGS=[bpy.data.objects['Generator acoustic wave '+str(i)] for i in range(3)];QUESTIONS=[bpy.data.objects['Elastic question mark '+str(i)] for i in range(3)];COUGHS=[bpy.data.objects['White soft cough puff '+str(i)] for i in range(4)]
class Rig:pass
Rig.pose=pose;r=Rig();r.name='you';r.pos=V((0,-.2,0));r.teacher=False
for attr,name in [('pelvis','char_you glossy royal-blue pelvis'),('body','char_you connected torso pivot'),('head','char_you independent camera-facing head'),('aim','you camera parallel head aim'),('neck','you neck connection'),('features','you grouped painted face turn'),('soul','you translucent soul head pivot'),('finger','you pointing index finger')]:setattr(r,attr,bpy.data.objects[name])
r.faces={n:bpy.data.objects['you face '+n] for n in ['look_left','look_right','clenched','scream','skeptical','smug','soul','talk_a','talk_b','talk_c','blink']}
r.drops=objs('you temple-attached cyan sweat');r.shadows=objs('you shoe contact')
for attr,prefix in [('arms','you curved stick arm '),('hands','you rounded mitten '),('legs','you curved stick leg '),('feet','you oval grounded foot ')]:setattr(r,attr,[bpy.data.objects[prefix+str(i)] for i in [-1,1]])
chairpair=(bpy.data.objects['Chair 0.0 0.7 floor pivot'],bpy.data.objects['Chair 0.0 0.7 backrest hinge'])
for foot in r.feet:foot.scale=(.105,.15,.015);key(foot,'scale',1)
s=bpy.data.scenes['Classroom_Master'];bpy.context.window.scene=s
for f in list(range(266,477))+list(range(1083,1215))+list(range(1422,1636)):
    row=next(x for x in rows if x['start_frame']<=f<=x['end_frame']);camera_pose(f,row)
    if f>=1422:p=r.pose(f,row['action'],chairpair)
    else:
        s.frame_set(f);s.view_layers[0].update();p={'hip':list(r.pelvis.location),'head':list(r.head.location)}
    effects(f,row,p)
for o in [CAM,CAM.data,FOCUS]+PRESSURE+STREAM+HAZE+r.feet:
    linear(o);o.update_tag()
for o in [r.head,r.aim,r.body,r.pelvis]+r.arms+r.legs:
    if o.animation_data:o.animation_data.action.update_tag()
bpy.context.window.scene=bpy.data.scenes['CF_1A'];bpy.context.scene.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_surgical_v2_final.blend'))
