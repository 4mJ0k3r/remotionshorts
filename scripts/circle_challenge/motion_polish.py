"""Visual corrections from the first motion calibration."""
import math
import bpy
from mathutils import Vector

s=bpy.context.scene
D=bpy.data.objects

# One capsule mesh shared by the segment objects. The wrist, shoe and knee
# caps remain separate, and the existing joint animation drives the mesh.
mesh=bpy.data.meshes.new('Rounded constant-width limb capsule')
vertices=[]
faces=[]
profile=[(-1,.12),(-.98,.66),(-.92,1),(.92,1),(.98,.66),(1,.12)]
sides=12
for z,radius in profile:
    vertices.extend((radius*math.cos(i*math.tau/sides),radius*math.sin(i*math.tau/sides),z) for i in range(sides))
for row in range(len(profile)-1):
    for i in range(sides):
        j=(i+1)%sides
        faces.append((row*sides+i,row*sides+j,(row+1)*sides+j,(row+1)*sides+i))
faces.extend([tuple(reversed(range(sides))),tuple(range((len(profile)-1)*sides,len(profile)*sides))])
mesh.from_pydata(vertices,[],faces)
ink=bpy.data.materials['Motion plum ink']
shader=ink.node_tree.nodes.get('Principled BSDF')
shader.inputs['Specular IOR Level'].default_value=0
shader.inputs['Roughness'].default_value=1
shader.inputs['Emission Color'].default_value=(.036,.016,.022,1)
shader.inputs['Emission Strength'].default_value=.72
mesh.materials.append(ink)
for obj in s.objects:
    if obj.name.endswith(('proximal ink','distal ink')):
        obj.data=mesh

def set_key(obj,prop,frame,value,interpolation='LINEAR'):
    setattr(obj,prop,value)
    obj.keyframe_insert(prop,frame=frame)
    for curve in obj.animation_data.action.fcurves:
        if curve.data_path==prop:
            for point in curve.keyframe_points:
                if int(point.co.x)==frame:
                    point.interpolation=interpolation

for who,side in [('char_you',1),('char_mummy',-1)]:
    head=D[who+'_head_independent_pivot']
    home=(0,(1474-380)*3/1474,0)
    set_key(head,'location',1,home,'CONSTANT')
    set_key(head,'location',2013,home)
    set_key(head,'location',2031,(side*.175,home[1]+side*.036,.006))
    set_key(head,'location',2094,(side*.145,home[1]+side*.029,.006),'CONSTANT')
    set_key(head,'location',2095,home,'CONSTANT')

cheque=D['Ignored cheque on grass']
s.frame_set(2140)
final_position=cheque.location.copy()
final_scale=cheque.scale.copy()
set_key(cheque,'location',2013,(-.45,-.81,.12),'CONSTANT')
set_key(cheque,'location',2095,final_position,'CONSTANT')
set_key(cheque,'scale',2013,(.72,)*3,'CONSTANT')
set_key(cheque,'scale',2095,final_scale,'CONSTANT')

pole=D['Three meter award pole']
set_key(pole,'location',1740,(-2.64,-.19,.39),'CONSTANT')
car=D['Mom family car']
set_key(car,'delta_rotation_euler',1895,(0,-.055,0))
for obj in D:
    if obj.name.startswith('Hug heart'):
        for curve in obj.animation_data.action.fcurves:
            if curve.data_path=='delta_location' and curve.array_index==2:
                for point in curve.keyframe_points:
                    point.co.y*=.56
                curve.update()
s.frame_set(70)
bpy.ops.wm.save_as_mainfile(filepath='D:/remotionshorts/renders/circle_challenge/circle_challenge.blend')
