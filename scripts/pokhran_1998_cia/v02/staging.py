"""Shared v02 set dressing, actor constraints, and shot export."""
from pathlib import Path
import sys
from math import sin, cos, pi, tau

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import hook_continuation as shared
from hook_continuation import *
import build as original
from build import aim_scan
from sets import orbit, scan_pyramid, war_room

HERE=Path(__file__).resolve().parent
BASE=ROOT/"renders/pokhran_1998_cia/v02"
BOUNDS=(0,444,858,1230,1652)


def opening(part):
    start,stop=BOUNDS[part-1:part+1]
    scene,cam,_,_=shared.begin(part)
    scene.frame_end=stop-start
    return scene,cam,lambda seconds: ftime(seconds)-start


def actor(c,name,archetype,small=False):
    previous,ring=original.HERE,k.RING
    original.HERE=HERE
    k.RING=24
    try:
        rig=original.cast(c,name,archetype)
    finally:
        original.HERE=previous
        k.RING=ring
    if small:
        for part in (*rig.head.children, *(modifier.id_data for modifier in rig.ink_modifiers)):
            for mod in part.modifiers:
                if mod.type=="SUBSURF":
                    mod.levels=mod.render_levels=1
    return rig


def finish(scene,part,actors,stages,cuts,frames,flashes=()):
    for rig in actors:
        rig.finish_bake()
    for stage,start,end in stages:
        activate(stage,f"frame < {start} or frame > {end}")
    for action in bpy.data.actions:
        for track in action.fcurves:
            constant="hide_" in track.data_path or track.data_path=="lens"
            for point in track.keyframe_points:
                point.interpolation="CONSTANT" if constant else "LINEAR"
    if len(set(frames))!=12 or not all(1<=f<=scene.frame_end for f in frames):
        raise ValueError(f"Invalid part {part} proof frames: {frames}")
    out=BASE/f"part{part}_v02"
    (out/"shot_map.json").write_text(json.dumps({"cuts":cuts,"proof_frames":frames,"flashes":flashes},indent=2))
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(out/f"part{part}_v02.blend"))


def console(c,m,alarm=False):
    box(c,"Main dark control wall",(0,2.60,2.28),(8,.12,4.62),m["navy"])
    box(c,"Control room slate floor",(0,.5,-.102),(10,9,.20),m["steel"])
    dark=k.emission("Aged phosphor blue" if not alarm else "Crimson alarm phosphor",
                    "#143040" if not alarm else "#54182c",.81)
    wall=[]
    for col in range(6):
        x=(col-2.5)*1.06
        box(c,"Steel vertical wall rail",(x-.51,2.46,2.18),(.062,.12,4.36),m["steel"],True)
        for row,z in enumerate((.87,1.48,2.08,2.68)):
            box(c,"Period monitor case",(x,2.287,z),(.94,.17,.53),m["steel"],True)
            box(c,"Monitor glass",(x,2.188,z),(.86,.021,.447),dark)
            if alarm and row>0:
                label(c,"SEISMIC EVENT",(x,2.148,z+.056),.067,m["paper"])
                label(c,"DETECTED: INDIA",(x,2.149,z-.063),.055,m["red"])
                trace(c,"Alarm amber underline",[(x-.29,2.152,z-.16),(x+.29,2.152,z-.16)],.008,m["red"])
            else:
                monitor(c,x,z,(col+2*row)%5,m["cyan"],m["red"],m["paper"])
        trace(c,"Architectural upper rib",[(x-.48,2.436,3.30),(x+.47,2.436,3.30)],.019,m["steel"])
    for x in (-1.42,1.42):
        lights_color="#ff9b88" if alarm else "#ffd6a2"
        k.cylinder("Copper practical shade",c,(x,1.81,3.10),.193,.145,m["wood"],r2=.126)
        k.make_light_cone("Overhead practical wash",c,(x,1.81,3.01),(x,1.81,1.03),.13,.67,lights_color)
    lights(c)
    for obj in c.objects:
        if obj.type=="CURVE" and obj.parent is None and obj.data.splines:
            curve=obj.data.splines[0]
            if curve.bezier_points and curve.bezier_points[0].co.y>2:
                obj.data.resolution_u=1
                obj.data.bevel_resolution=0
    return dark


def desk(c,m,x,y,name):
    box(c,name+" worktop",(x,y,.80),(.91,.56,.10),m["navy"],True)
    box(c,name+" solid apron",(x,y-.256,.403),(.87,.065,.77),m["steel"],True)
    box(c,name+" black swivel seat",(x,y+.51,.883),(.42,.40,.077),m["ink"],True)
    box(c,name+" high backrest",(x,y+.70,1.20),(.46,.09,.74),m["navy"],True)
    for i in range(8):
        box(c,name+" keyboard key", (x-.20+i*.057,y+.08,.857),(.034,.075,.015),
            m["cyan"] if i%3==0 else m["paper"])
        box(c,name+" cabinet vent",(x-.31+i*.088,y-.292,.44),(.012,.009,.38),m["navy"])
    return Vector((x,y+.49,.286))


def seated(rig,f,root,yaw=0.,tilt=.025,arms=REST,face="rest",head=(0,0)):
    legs=[((sign*.125,-.06,-.25),(sign*.14,-.21,.31)) for sign in (-1,1)]
    pose(rig,f,root,yaw,tilt,arms,face,head,legs)


def grip(world, root, yaw, tilt):
    basis=Euler((0,0,yaw)).to_matrix()@Euler((tilt,0,0)).to_matrix()
    return basis.transposed()@(Vector(world)-Vector(root)-Vector((0,0,.59)))


def glasses(c,rig,mat):
    for x in (-.093,.093):
        trace(c,"Flat front glasses rim",[(x-.067,-.237,-.012),(x+.067,-.237,-.012),
              (x+.067,-.237,.091),(x-.067,-.237,.091),(x-.067,-.237,-.012)],.0039,mat,rig.head)
    trace(c,"Glasses bridge",[(-.028,-.242,.047),(.028,-.242,.047)],.0041,mat,rig.head)


def pathspark(c,m,name,size=.20):
    root=k.empty(name,c)
    for j in range(14):
        a=j*tau/14
        d=size*(.80+.25*sin(j*1.77)**2)
        trace(c,"Comic impact ray",[(.24*d*cos(a),0,.24*d*sin(a)),(d*cos(a),0,d*sin(a))],
              .006,m["paper"] if j%2 else m["red"],root)
    return root


def spark_at(root,f,where,amount):
    root.location=where
    root.scale=(max(.0001,amount),)*3
    key(root,f,"location","scale")
