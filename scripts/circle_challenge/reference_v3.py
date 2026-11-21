"""Reference-based v3 changes applied to the calibrated v2 scene."""
import bpy, math, random, re
from pathlib import Path
from mathutils import Vector

ROOT=Path('D:/remotionshorts/scripts/circle_challenge')
OUT=ROOT.parent.parent/'renders/circle_challenge'
helpers={}
source=(ROOT/'cinematic.py').read_text(encoding='utf-8-sig')
exec(compile(source.split('# Replace checker blocks')[0],'cinematic helpers','exec'),helpers)
key=helpers['key']
material=helpers['material']
prop=helpers['mesh_prop']
s=bpy.context.scene
objects=bpy.data.objects
cam=s.camera
rng=random.Random(305)

art_helpers={}
exec((ROOT/'reference_art.py').read_text(),art_helpers)
art_helpers['refresh_art'](bpy,OUT/'assets')

for mat in bpy.data.materials:
    if not mat.use_nodes:
        continue
    for node in mat.node_tree.nodes:
        if node.type=='TEX_IMAGE' and node.image and node.image.filepath.endswith('_head.png'):
            for emission in mat.node_tree.nodes:
                if emission.type=='EMISSION':
                    emission.inputs['Strength'].default_value=1.18
    if mat.name.startswith('Tapered translucent stink'):
        shader=mat.node_tree.nodes.get('Principled BSDF')
        shader.inputs['Alpha'].default_value=.42

for index in range(38):
    actor=objects[f'Contestant_{index:02d}']
    if index<21:
        scale=.60+rng.random()*.12
        for frame in (144,264,459,576,732):
            x=(index%7-3)*1.26+rng.uniform(-.27,.27)
            y=3.5+(index//7)*1.8+rng.uniform(0,1.2)
            key(actor,'location',frame,(x,y,0))
            key(actor,'scale',frame,(scale,)*3)
        # Restore the previous boundary-cut crowd staging.
        key(actor,'location',378,((index%7-3)*1.14,4.8+index//7*.72,0))
art_helpers['add_hats'](bpy,OUT/'assets')

# Timber stands sit beyond the circle. Roofs, stepped benches and braces are real geometry.
navy=material('V3 painted grandstand teal',(.027,.14,.145))
timber=material('V3 grandstand honey timber',(.40,.21,.082))
cream=material('V3 canvas ivory',(.92,.83,.67))
red=material('V3 canvas brick red',(.55,.049,.05))
gold=material('V3 canvas marigold',(.89,.51,.063))
blue=material('V3 canvas cobalt',(.057,.26,.60))
for cx in (-8.7,8.7):
    cy=8.7
    prop('Grandstand raised foundation',(cx,cy,.26),(2.45,1.65,.26),navy)
    for step in range(4):
        y=cy-1.18+step*.62
        z=.49+step*.32
        prop('Stepped timber bench',(cx,y,z),(2.32,.28,.13),timber)
        prop('Painted grandstand riser',(cx,y+.15,z-.19),(2.34,.11,.19),navy)
    for x in (cx-2.32,cx,cx+2.32):
        for y in (cy-1.62,cy+1.62):
            prop('Grandstand upright',(x,y,1.92),(.06,.06,1.92),timber)
    for stripe in range(12):
        x=cx-2.4+(stripe+.5)*.40
        paint=red if stripe%2==0 else cream
        roof=prop('Striped pitched awning',(x,cy,3.85),(.20,1.84,.06),paint)
        roof.rotation_euler.x=.11
        prop('Striped canvas valance',(x,cy-1.81,3.52),(.20,.045,.17),paint)
    prop('Grandstand fascia',(cx,cy-1.58,3.28),(2.36,.11,.12),navy)

def flags(name,a,b,droop):
    a,b=Vector(a),Vector(b)
    data=bpy.data.curves.new(name,'CURVE')
    data.dimensions='3D'
    data.bevel_depth=.017
    spline=data.splines.new('POLY')
    spline.points.add(20)
    for i,point in enumerate(spline.points):
        t=i/20
        p=a.lerp(b,t)
        p.z-=droop*4*t*(1-t)
        point.co=(*p,1)
    line=bpy.data.objects.new(name,data)
    s.collection.objects.link(line)
    data.materials.append(timber)
    for i in range(1,20):
        t=i/20
        p=a.lerp(b,t)
        p.z-=droop*4*t*(1-t)
        edge=(b-a).normalized()*.16
        mesh=bpy.data.meshes.new('Canvas pennant triangle')
        mesh.from_pydata([p-edge,p+edge,p+Vector((.045,-.04,-.36))],[],[(0,1,2)])
        flag=bpy.data.objects.new('Festive canvas pennant',mesh)
        s.collection.objects.link(flag)
        mesh.materials.append((red,gold,blue,cream)[i%4])
flags('Bunting across outer arena',(-10.9,7,4.8),(10.9,7,4.8),.55)
flags('Bunting left approach',(-11.1,3.8,4.45),(-3.8,8.6,4.65),.42)
flags('Bunting right approach',(3.8,8.6,4.65),(11.1,3.8,4.45),.42)

leaf=material('V3 grass blades',(.16,.29,.046))
stone=material('V3 dirt pebbles',(.30,.24,.17))
for i in range(28):
    angle=rng.uniform(0,math.tau)
    radius=rng.uniform(7,12)
    x,y=radius*math.cos(angle),radius*math.sin(angle)
    if i%7==0:
        box=prop('Timber equipment crate',(x,y,.29),(.39,.30,.29),timber)
        box.rotation_euler.z=angle
        for dx in (-.22,.22):
            prop('Crate face batten',(dx,-.31,0),(.045,.027,.27),cream,box)
    elif i%3==0:
        rock=prop('Low stone beside the track',(x,y,.06),(.19,.12,.10),stone,kind='sphere')
        rock.rotation_euler.z=angle
    else:
        mesh=bpy.data.meshes.new('Three folded blades')
        verts=[]
        faces=[]
        for j in range(3):
            dx=(j-1)*.07
            verts.extend([(dx-.035,0,0),(dx+.035,0,0),(dx*2,.05,.20+.06*(j%2))])
            faces.append((j*3,j*3+1,j*3+2))
        mesh.from_pydata(verts,[],faces)
        tuft=bpy.data.objects.new('Arena grass tuft',mesh)
        s.collection.objects.link(tuft)
        tuft.location=(x,y,.012)
        tuft.rotation_euler.z=angle
        mesh.materials.append(leaf)

# Fit the full character and hovering shoe into the boundary shot. The award
# shot leaves a separate lower-left area for the cheque and a right lane for the call.
hud=objects['hud_rig']
overlay=bpy.data.scenes.get('Circle Challenge HUD pass')
for frame, eye, target, lens in [
    (70,(0,-23,13),(0,3,2),22),
    (378,(-.42,-11.08,1.18),(.03,-5.65,1.53),35),
    (1740,(-.82,-7.55,2.37),(-.82,0,1.57),27),
]:
    direction=Vector(target)-Vector(eye)
    rotation=direction.to_track_quat('-Z','Y').to_euler()
    for camera in (cam,overlay.camera):
        key(camera,'location',frame,eye)
        key(camera,'rotation_euler',frame,rotation)
        key(camera.data,'lens',frame,lens)
    cam.data.dof.focus_distance=direction.length
    cam.data.dof.keyframe_insert('focus_distance',frame=frame)
    factor=direction.length*24/lens/10
    key(hud,'scale',frame,(factor,)*3)
    key(hud,'location',frame,(0,0,-direction.length+factor))
for curve in cam.data.animation_data.action.fcurves:
    for point in curve.keyframe_points:
        point.interpolation='CONSTANT'
check=objects['Prize check']
pole=objects['Three meter award pole']
key(check,'scale',1740,(.61,)*3)
key(check,'location',1740,(-1.56,-.30,1.04))
key(check,'delta_location',1740,(0,0,0))
key(check,'scale',1854,(0,0,0))
key(pole,'scale',1740,(1,1,1))
key(pole,'scale',1854,(0,0,0))
key(pole,'location',1740,(-2.64,-.33,.49))
key(pole,'rotation_euler',1,pole.rotation_euler.copy())
key(pole,'rotation_euler',1740,Vector((1,0,.41)).to_track_quat('Z','Y').to_euler())
for child in objects['char_you'].children:
    if child.name.startswith('Rear pants stink ribbon'):
        child.location.x-=.24
        child.location.z+=.43
s.frame_set(70)
s['calibration_revision']=3
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'circle_challenge.blend'))

