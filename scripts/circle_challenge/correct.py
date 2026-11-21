"""Consolidated calibration corrections; also applied at the end of fresh builds."""
import bpy,math,random
from pathlib import Path
from mathutils import Vector
s=bpy.context.scene;D=bpy.data.objects;OUT=Path('D:/remotionshorts/renders/circle_challenge')
def key(o,path,f,value,mode='CONSTANT'):
    setattr(o,path,value);o.keyframe_insert(data_path=path,frame=f)
    for fc in o.animation_data.action.fcurves:
        if fc.data_path==path:
            for k in fc.keyframe_points:
                if abs(k.co.x-f)<.01:k.interpolation=mode
def show(o,events):
    for f,v in events:key(o,'scale',f,(v,v,v))
# Level the feet through the crouch; the silhouette itself bends the knees.
you=D['char_you']
if you.animation_data:
    for fc in list(you.animation_data.action.fcurves):
        if fc.data_path=='delta_location':you.animation_data.action.fcurves.remove(fc)
you.delta_location=(0,0,0)
show(you,[(1,1),(1854,0),(2013,1),(2120,0)])
# Solo hero Mom shot, unobstructed by her car.
show(D['Mom family car'],[(1,0),(1854,1),(1910,0)])
# Sky visible behind the stage instead of an endless elevated checker field.
g=D['Grass field'];g.dimensions=(65,35,.35);g.location.y=-1.5
# Give each crowd contestant a distinct colored shirt using per-material tint.
palette=[(1,.45,.09,1),(.05,.6,.9,1),(.7,.12,.42,1),(.45,.18,.8,1),(.1,.65,.46,1)]
# Keep the original opaque sprites; color variety comes from texture hue shifts.
for i in range(38):
    a=D[f'Contestant_{i:02d}']
    for child in a.children:
        for card in child.children:
            if '_body' in card.name and card.type=='MESH':
                m=card.active_material.copy();card.active_material=m;n=m.node_tree.nodes;l=m.node_tree.links;t=next(n for n in n if n.type=='TEX_IMAGE');h=n.new('ShaderNodeHueSaturation');h.inputs['Hue'].default_value=.5+(i%6)*.10
                destinations=[ln.to_socket for ln in list(l) if ln.from_node==t and ln.from_socket.name=='Color']
                l.new(t.outputs['Color'],h.inputs['Color'])
                for dst in destinations:l.new(h.outputs['Color'],dst)
    if i<18:
        x=1.0+(i%6)*.36;y=.3+(i//6)*.95;start=1104+i*3;end=1270+i
        # The motivated tracking cut reveals the group already running right.
        key(a,'location',1104,(x,y,0));key(a,'location',start,(x,y,0),'LINEAR');key(a,'location',end,(7.3,y-.8,0))
        # Remove old stale end keys so trajectories remain continuous.
        for fc in a.animation_data.action.fcurves:
            if fc.data_path=='location':
                for kp in list(fc.keyframe_points):
                    if 1104<kp.co.x<1299 and int(kp.co.x) not in (start,end):fc.keyframe_points.remove(kp)
        for child in a.children:
            for card in child.children:
                if card.type=='MESH' and ('_body' in card.name):
                    key(card,'scale',1104,(1,1,1) if '_run_' in card.name else (0,0,0))
cam=s.camera
pos=(2.3,-18,7);target=(2.3,1,1.3)
key(cam,'location',1104,pos);key(cam,'rotation_euler',1104,(Vector(target)-Vector(pos)).to_track_quat('-Z','Y').to_euler())
# Reframe brain: operator in front of console at a real raised platform.
op=D['char_brain_op'];key(op,'location',965,(49.98,-.7,.54))
bpy.ops.mesh.primitive_cube_add(size=1,location=(49.98,-.75,.2));platform=bpy.context.object;platform.name='Hazmat operator support step';platform.dimensions=(1.6,1.15,.4);platform.data.materials.append(bpy.data.materials['console'])
# The console lives behind the operating hand; hand and button align at peak.
s.frame_set(1030);bpy.context.view_layer.update();body=D['char_brain_op_body_billboard'];grip=body.matrix_world@Vector(((845-512)*3/1474,(1474-930)*3/1474,0))
button=D['Fixed VOMIT CENTER button'];button.animation_data_clear();button.location=(grip.x,grip.y+.12,grip.z-.12)
for f,dz in [(1000,.13),(1015,.13),(1030,0),(1040,0),(1055,.13)]:key(button,'delta_location',f,(0,0,dz),'LINEAR')
# Reduce the extreme red cast and reveal the yellow hazmat operator.
for o in s.objects:
    if o.type=='LIGHT' and o.data.type=='POINT':o.data.energy=15
# Background scoreboard stays only in wide and prize shots; no cropped text behind HUD.
for name in ['Prize LED','Scoreboard housing']:
    o=D[name]
    # housing uses baked dimensions, unit scale.
    if name=='Prize LED':show(o,[(1,1),(144,0),(1668,0)])
    else:show(o,[(1,1),(144,0),(1668,1),(1740,0)])
show(D['Winner LED'],[(1,0),(1668,1),(1740,0)])
# Remove small camera tripod from the toilet guard composition.
for o in s.objects:
    if o.name.startswith(('TV tripod','TV camera','Camera lens')) and o.location.x>3:
        for f,v in [(1,1),(2095,0)]:key(o,'hide_render',f,not bool(v))
s.frame_set(70)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'circle_challenge.blend'))
