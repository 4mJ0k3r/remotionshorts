"""Head silhouettes, cel ink, signature hair and continuity props."""
import math
from pathlib import Path

import bpy
from mathutils import Vector
import ricks_v2_kit as k

from scenery import line

ART=Path(__file__).with_name("art")
REST=[((-.211,-.15,.17),(-.223,-.065,.26)),((.211,-.15,.17),(.223,-.065,.26))]
LEGS=[((a*.123,-.03,.027),(a*.126,-.09,.32)) for a in (-1,1)]


def accent_ink(rig,obj,c):
    hull=k.apply_character_ink(obj,c,pixels=2.75)
    hull.id_data.data.materials[0]=bpy.data.materials["Studio | espresso hull"]
    rig.ink_modifiers.append(hull)


def figure(c,name,role,*,headphones=True,compact=False,expressions=None):
    custom={
        "boy":((1.02,.91,1.01),.19,"#F2D6BE","#C4A58E","#21212d"),
        "shoko":((.90,.89,1.094),-.13,"#F9E1CE","#CCAFA0","#9a79ba"),
        "classmate":((1.02,.91,.96),.26,"#E1B392","#A87768","#353344"),
    }
    k.STUDIO_PORTRAITS[role]=custom[role]
    old=k.RING
    k.RING=21 if compact else 25
    try:
        rig=k.build_studio_character(name,c,portrait=role,costume_image=ART/f"{role}_coat.png",
            expression_images={p.stem.removeprefix(role+"_"):p for p in ART.glob(role+"_*.png")
                               if not p.stem.endswith("_coat") and
                               (expressions is None or p.stem.removeprefix(role+"_") in expressions)},
            dot_contrast=1.08)
    finally:
        k.RING=old
    base={"boy":"#262635","shoko":"#a9a2b0","classmate":"#324968"}[role]
    torso=bpy.data.objects[name+" | graphic pill torso"]
    torso.data.materials[0]=k.make_cel_character_material(name+" textile base",base)
    k.studio_shadow_dots(torso.data.materials[0],.26)
    cap=bpy.data.objects[name+" | shaped hair cap"]
    hair=cap.data.materials[0]
    for obj in rig.head.children:
        if obj.type=="CURVE" and "highlight" in obj.name:
            obj.data.materials[0]=k.make_cel_character_material("Lavender hair sheen" if role=="shoko" else "Graphite hair sheen",
                                                               "#c6a3da" if role=="shoko" else "#676579")
    if role=="shoko":
        for side in (-1,1):
            lock=k.ball("Soft tapered lavender cheek lock",c,(.171*side,-.131,.067),
                (.066,.104,.139),hair,rig.head,segments=20,rings=12)
            lock.rotation_euler.y=-.43*side
            accent_ink(rig,lock,c)
        tie=k.ball("Lavender hair elastic",c,(.109,.122,.179),(.086,.064,.065),
                   k.make_cel_character_material("Lavender hair tie","#c18db0"),rig.head,segments=16,rings=9)
        accent_ink(rig,tie,c)
        pony=k.empty("Soft high ponytail swing",c,(.102,.139,.188),rig.head)
        rig.pony=pony
        for j,(loc,radii,tilt) in enumerate((
            ((.051,.032,-.045),(.112,.089,.129),-.52),
            ((.128,.075,-.149),(.101,.079,.150),-.61),
            ((.165,.080,-.246),(.074,.068,.110),-.28))):
            lock=k.ball("Joined lavender ponytail curl",c,loc,radii,hair,pony,segments=21,rings=13)
            lock.rotation_euler.y=tilt
            accent_ink(rig,lock,c)
        gloss=k.make_cel_character_material("Ponytail pastel hair glint","#d2afe2")
        line(c,"Curved gloss down the ponytail",[(.055,-.048,-.008),(.117,-.006,-.110),(.162,.012,-.251)],
             .014,gloss,pony)
    else:
        for j in range(7 if role=="boy" else 5):
            x=(j-3)*.055 if role=="boy" else (j-2)*.061
            z=.153+.052*(1-abs(x)*3)
            length=.053+.066*math.sin(j*1.37)**2
            widths=(.066,.046,.022,.001)
            vertices=[]
            for r,width in enumerate(widths):
                u=r/3
                x0=x+u*(.060+.05*math.sin(j))
                for i in range(9):
                    a=i*math.tau/9
                    vertices.append((x0+width*math.cos(a),-.020-.082*u+width*.92*math.sin(a),z+length*u))
            faces=[(r*9+i,r*9+(i+1)%9,(r+1)*9+(i+1)%9,(r+1)*9+i) for r in range(3) for i in range(9)]
            faces.extend((tuple(reversed(range(9))),tuple(range(27,36))))
            tuft=k.mesh("Tapered swept hair spike",c,vertices,faces,hair,rig.head,True)
            accent_ink(rig,tuft,c)
    rig.cable_end=None
    if role=="boy" and headphones:
        shell=k.make_cel_character_material("Matte graphite headphones","#272a39")
        cloth=k.make_cel_character_material("Slate headphone foam","#474358")
        rim=k.make_cel_character_material("Graphite headphone outer rim","#6e7389")
        cup_center=.240
        line(c,"Arched matte headphone band",[(.244*math.cos(a),.02,.274*math.sin(a)+.009)
             for a in (math.pi*i/30 for i in range(31))],.026,shell,rig.head)
        line(c,"Soft graphite band rim",[(.244*math.cos(a),-.005,.275*math.sin(a)+.017)
             for a in (math.pi*i/28 for i in range(29))],.011,rim,rig.head)
        for side in (-1,1):
            for gap,radius,depth,material in ((0,.099,.058,shell),(-.035,.078,.035,cloth),(.031,.079,.018,rim),(.043,.066,.021,shell)):
                obj=k.cylinder("Round matte headphone earcup",c,(side*(cup_center+gap),-.006,-.030),radius,depth,
                               material,rig.head,length_segments=24)
                obj.rotation_euler.y=math.pi/2
        line(c,"Cable leaving left earcup",[(-.249,-.021,-.076),(-.252,-.065,-.151),(-.239,-.091,-.221)],
             .013,rim,rig.head)
        broken=k.empty("Visible damaged cable tip",c,(-.136,-.123,.155),rig.body)
        rig.cable_end=broken
        rig.cable=line(c,"Visible chewed black headphone wire",[(-.229,-.103,.428),(-.229,-.164,.317),
                   (-.173,-.152,.245),(-.160,-.134,.173)],.013,shell,rig.body)
        line(c,"Cable cool rim highlight",[(-.231,-.118,.397),(-.228,-.175,.315),
                  (-.179,-.166,.241),(-.166,-.144,.188)],.005,rim,rig.body)
        for j,(tone,x) in enumerate((("#e5606c",-.021),("#61a9e0",.004),("#eab775",-.003))):
            material=k.emission("Exposed red blue or copper strand",tone,.96)
            line(c,"Exposed torn strand",[(-.023+j*.006,.005,.023),(x,-.004,-.007-j*.011),
                       (x*1.38,-.013,-.032-j*.008)],.005,material,broken)
    return rig


def key(obj,frame,*properties):
    for prop in properties:
        obj.keyframe_insert(prop,frame=frame)


def act(rig,f,root,yaw=0,tilt=0,arms=REST,legs=LEGS,expression=None,head=(0,0),bounce=0,sweat=None):
    rig.pose(f,root,yaw,tilt,arms,legs,expression,bounce=bounce,head_tilt=head[0],head_yaw=head[1],sweat=sweat)
    k.studio_pose_hands(rig,f)
    if hasattr(rig,"pony"):
        rig.pony.rotation_euler.y=.11*math.sin(f*.265)+head[1]*.29
        rig.pony.rotation_euler.x=.05*math.cos(f*.36)
        key(rig.pony,f,"rotation_euler")


def walk(rig,f,route,yaw,first,last,expression,*,face=(0,0),override=None):
    stance=k.eval_stick_walk_cycle(f,route,yaw,start_frame=first,stop_frame=last,plant_yaw=yaw,strength=.57)
    arms=list(stance.arms)
    for index,arm in (override or {}).items():
        arms[index]=arm
    act(rig,f,stance.location,yaw,stance.tilt*.58,arms,stance.legs,expression,face,bounce=stance.bounce*.76)
    return stance
