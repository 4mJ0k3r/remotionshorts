"""Shared set and rig routines for the three locked-timeline preview modules."""
import json
import math
from pathlib import Path
from random import Random
import sys

import bpy
from mathutils import Euler, Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
sys.path[:0]=[str(HERE/"v01b"),str(ROOT/"scripts")]
from build import activate, bake_paper, camera_at, cast, ease, group, key, mug_grip
from sets import box, label, lights, monitor, oval, trace, translucent
import ricks_v2_kit as k

PLAN=json.loads((HERE/"v01b/master_plan.json").read_text(encoding="utf-8"))
BOUNDS=PLAN["part_boundaries_frames"]
OUT=ROOT/"renders/pokhran_1998_cia"
REST=[((-.201,-.105,.146),(-.239,-.033,.254)),((.201,-.105,.146),(.239,-.033,.254))]
LEGS=[((s*.135,-.027,.027),(s*.138,-.087,.32)) for s in (-1,1)]

def ftime(second):
    return round(second*30)+1

def palette():
    return {
        "navy":k.surface("Architectural ink navy","#22344a",.78),
        "steel":k.surface("Brushed graphite steel","#405578",.72,.21),
        "wood":k.texture("Ginger grain and compressed timber",("#362636","#8a5b43","#b78960"),"wood",(.66,.82)),
        "sand":k.texture("Golden layered silt",("#77504b","#b78654","#ddab6f"),"plaster",(.74,.85)),
        "cyan":k.emission("Cool monitor bloom","#68c7d2",1.36),
        "paper":k.emission("Ivory printed accent","#e8cb9c",1.03),
        "red":k.emission("Alarm red accent","#fc5266",1.55),
        "green":k.emission("Sea glass green accent","#8bd7a4",1.28),
        "ink":k.emission("Studio espresso prop ink",k.STUDIO_INK),
    }

def begin(part):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    start,stop=BOUNDS[part-1:part+1]
    k.configure_ricks_scene(s,frame_end=stop-start,samples=6)
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.compression=0
    s.world=bpy.data.worlds.new("Deep cinematic ambient")
    s.world.use_nodes=True
    bg=next(n for n in s.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#182749")
    bg.inputs[1].default_value=.36
    cam=bpy.data.objects.new("Wide vertical delivery camera",bpy.data.cameras.new("Vertical 26 mm"))
    s.collection.objects.link(cam)
    s.camera=cam
    k.setup_ricks_compositor(s,camera=cam)
    bake_paper(s)
    return s,cam,start,stop

def close(s,part,actors,stages,cuts,stills):
    for rig in actors:
        rig.finish_bake()
    for stage,first,last in stages:
        activate(stage,f"frame < {first} or frame > {last}")
    for action in bpy.data.actions:
        for curve in action.fcurves:
            flag="hide_" in curve.data_path or curve.data_path=="lens"
            for point in curve.keyframe_points:
                point.interpolation="CONSTANT" if flag else "LINEAR"
    out=OUT/f"part{part}_v01"
    (out/"shot_map.json").write_text(json.dumps({"cuts":cuts,"proof_frames":stills},indent=2))
    s.frame_set(1)
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f"pokhran_part{part}_v01.blend"))

def styled(c,name,portrait):
    # Narrower construction rings keep multi-actor sets within the geometry budget.
    old=k.RING
    k.RING=28
    try:
        return cast(c,name,portrait)
    finally:
        k.RING=old

def pose(rig,f,root,yaw,tilt,arms=REST,face=None,head=(0,0),legs=LEGS,bounce=0):
    rig.pose(f,root,yaw,tilt,arms,legs,face,head_tilt=head[0],head_yaw=head[1],bounce=bounce)
    k.studio_pose_hands(rig,f)

def grip_target(target,root,yaw,tilt,elbow,bounce=0):
    basis=Euler((0,0,yaw)).to_matrix() @ Euler((tilt,0,0)).to_matrix()
    local=basis.transposed()@(Vector(target)-Vector(root)-Vector((0,0,.59+bounce)))
    return local-(local-Vector(elbow)).normalized()*.016

def desk_legs():
    return [((side*.134,-.108,.154),(side*.149,-.232,.31)) for side in (-1,1)]

def camera_move(cam,f,stage,a,b,p0,p1,at0,at1,lens=26):
    t=ease(f,a,b)
    camera_at(cam,f,stage,Vector(p0).lerp(Vector(p1),t),Vector(at0).lerp(Vector(at1),t),lens)

def rings(c,name,x,y,z,radius,mat,width=.008):
    return oval(c,name,x,y,z,radius,radius,mat,width)

def scan_panel(c,m,center=(0,1.60,1.25),width=1.55,height=1.02):
    x,y,z=center
    box(c,"Beveled terminal frame",(x,y,z),(width+.12,.16,height+.14),m["steel"],True)
    plate=k.emission("Overhead photograph blue grey","#2b4659",1.1)
    box(c,"Aerial image under glass",(x,y-.09,z),(width,.031,height),plate)
    for row in range(14):
        z0=z-height*.44+row*height*.067
        trace(c,"Dune ridges on enlarged archival photograph",[
            (x-width*.46+i*width*.084,y-.113,z0+.045*math.sin(i*.64+row*.82)) for i in range(12)
        ],.0048,m["paper"] if row%4==0 else m["cyan"])
    for col in range(13):
        x0=x-width*.46+col*width*.075
        trace(c,"Survey image reticle",[(x0,y-.117,z-height*.46),(x0,y-.117,z+height*.46)],.0028,m["cyan"])
    for col in range(1,5):
        x0=x-width*.42+col*width*.171
        trace(c,"Interrupted topography marks",[(x0-.051,y-.121,z-.25),(x0+.012,y-.121,z-.145),
                (x0+.021,y-.121,z-.051)],.0088,m["paper"])
    return y-.13

def command_wall(c,m):
    box(c,"Framed navy war-room wall",(0,2.55,2.42),(9,.14,5.0),m["navy"])
    box(c,"Satin control room floor",(0,0,-.114),(10,10,.22),m["steel"])
    teal=k.emission("Period monitor phosphor","#142f3d",.92)
    for col in range(7):
        x=-2.85+.91*col
        box(c,"Wall vertical steel rib",(x-.46,2.43,2.33),(.066,.12,4.52),m["steel"],True)
        box(c,"Console floor joint",(x,-.3,.001),(.014,9,.006),m["navy"])
        for row,z in enumerate((.98,1.53,2.10,2.64)):
            box(c,"Period CRT graphite case",(x,2.297,z),(.824,.19,.491),m["steel"],True)
            box(c,"Dark glass CRT screen",(x,2.185,z),(.755,.031,.429),teal)
            monitor(c,x,z,(col+2*row)%5,m["cyan"],m["red"],m["paper"])
    lights(c)

def ribbon(c,name,points,width,material):
    verts=[(x,y,z+offset) for x,y,z in points for offset in (-width,width)]
    faces=[(i,i+1,i+3,i+2) for i in range(0,len(verts)-2,2)]
    return k.mesh(name,c,verts,faces,material)

def sky(c,m,night=False):
    color=("#111c45","#263461","#6d5a79") if night else ("#2b517f","#5586af","#d1a083")
    sky_mat=k.emission("Desert gradient twilight",color[0],1.1)
    nodes,links=sky_mat.node_tree.nodes,sky_mat.node_tree.links
    tex=nodes.new("ShaderNodeTexCoord"); axis=nodes.new("ShaderNodeSeparateXYZ")
    ramp=nodes.new("ShaderNodeValToRGB")
    k.look._ramp(ramp,[(0,color[2]),(.39,color[1]),(1,color[0])])
    links.new(tex.outputs["Generated"],axis.inputs[0])
    links.new(axis.outputs["Z"],ramp.inputs[0])
    links.new(ramp.outputs[0],next(n for n in nodes if n.type=="EMISSION").inputs["Color"])
    box(c,"Layered sky backdrop",(0,7.2,2.66),(18,.032,8.43),sky_mat)
    for j in range(4):
        y=6.84-.94*j
        color=("#303767","#46416b","#63506f","#8c6170")[j] if night else ("#7e829e","#a88a8b","#bb8c69","#b57f59")[j]
        horizon=k.emission("Distant dune ridge ink",color)
        crest=[(-9+i*.288,y,.75+.23*j+.15*math.sin(i*.25+j)+.11*math.sin(i*.43+j*1.7))
               for i in range(64)]
        k.mesh("Distant Thar dune layer",c,[*crest,(9.14,y,-.26),(-9,y,-.26)],
               [tuple(range(len(crest)+2))],horizon)
    disk=k.cylinder("Soft distant sun or moon",c,(1.77,6.92,2.75),.24,.052,m["paper"],length_segments=32)
    disk.rotation_euler.x=math.pi/2
    if night:
        rng=Random(981)
        verts=[];faces=[]
        for _ in range(138):
            x,z=rng.uniform(-8,8),rng.uniform(1.90,6.44)
            radius=rng.uniform(.005,.018);i=len(verts)
            verts.extend(((x-radius,7.05,z),(x,7.05,z+radius),(x+radius,7.05,z),(x,7.05,z-radius)))
            faces.append((i,i+1,i+2,i+3))
        k.mesh("Faint lights over the dusk desert",c,verts,faces,m["cyan"])
    # Printed cloud bands and dune cross-hatching give depth to the distant plane.
    sky_ink=k.emission("Far cloud shadows","#495586" if night else "#587a9b",1.01)
    sky_rim=k.emission("Far cloud teeth on warm sky","#aa91a7" if night else "#c8c8c2",.93)
    for j in range(12):
        x=(-1 if j%2 else 1) * (j%3*.78+.55)
        z=1.87+(j//2)*.31
        pts=[(x+i*.27-1.36,6.89,z+.067*math.sin(i*.65+j*.91)) for i in range(11)]
        ribbon(c,"Cloud ribbon volume",pts,.041,sky_ink)
        ribbon(c,"Cloud silver lining",[(xx,yy-.012,zz+.031) for xx,yy,zz in pts[1:10]],.012,sky_rim)
    dune_ink=k.emission("Printed contours in shaded dunes","#51486e" if night else "#966d66")
    dune_rim=k.emission("Printed contours in sunlit dunes","#9d7583" if night else "#ddb482")
    for j in range(30):
        z=.36+j*.048
        pts=[(i*.36-6.48,3.77,z+.05*math.sin(i*.58+j*.24)+.09*math.sin(i*.28+j*.31)) for i in range(37)]
        ribbon(c,"Long print contour across a distant dune",pts,.012 if j%3 else .018,dune_ink if j%3 else dune_rim)

def desert_floor(c,m,night=False):
    sky(c,m,night)
    box(c,"Fine matte desert sand plane",(0,2,-.130),(13,14,.252),m["sand"])
    rng=Random(764)
    accent=k.surface("Dry ochre ridges and scrub","#90605a" if night else "#a57a54",.82)
    ridge=k.surface("Ripple edge lit from the sky","#b98f8e" if night else "#e5b67c",.80,.0,.22)
    for j in range(185):
        y=rng.uniform(-2.8,3.9)
        x=rng.uniform(-3.35,3.35)
        span=rng.uniform(.11,.28)
        trace(c,"Rippled sand edge",[(x+q*span,y+.031*math.sin(q*.66+j),-.001)
              for q in range(6)],.009,ridge if j%3==0 else accent)
    for i in range(21):
        x=(i-10)*.44
        y=1.84+.12*math.sin(i)
        for j in range(2):
            x0=x+.058*j
            trace(c,"Dusty folded scrub",[(x0-.056,y,0),(x0,y-.026,.158+.063*j),(x0+.054,y,.027)],.013,accent)
    for i in range(12):
        x=-3.17+.55*i
        trace(c,"Thin boundary fence guide",[(x,2.34,0),(x,2.34,.548)],.017,m["wood"])
    for z in (.23,.421):
        trace(c,"Simple wire along desert fence",[(-3.4,2.34,z),(3.46,2.34,z)],.011,m["wood"])
    lights(c,"#f4b588" if night else "#ffd5a0","#688de9" if night else "#89b5f7")

def push(f,a,middle,hit,hold,settle):
    return .18*ease(f,a,middle)+.82*ease(f,middle,hit)-ease(f,hold,settle)

def aim_object(obj,f,start,end,axis="Z"):
    obj.location=start
    obj.rotation_mode="QUATERNION"
    obj.rotation_quaternion=(Vector(end)-Vector(start)).to_track_quat(axis,"Y")
    key(obj,f,"location","rotation_quaternion")
