"""Original cast on the studio's tapered-arm rig."""
import math
from pathlib import Path

from mathutils import Euler, Vector
import ricks_v2_kit as k
from sets import line, rim

ART=Path(__file__).with_name("art")
REST=tuple(((s*.212,-.120,.17),(s*.211,-.06,.258)) for s in (-1,1))
STAND=tuple(((s*.124,-.040,.027),(s*.117,-.103,.282)) for s in (-1,1))
SEATED=tuple(((s*.232,-.372,.194),(s*.257,-.224,.505)) for s in (-1,1))
CHAIR=tuple(((s*.110,-.174,.027),(s*.118,-.199,.417)) for s in (-1,1))
PORTRAITS={
    "boy": ((1.0,.91,1.02),.18,"#F5DBC2","#C49D90","#493449"),
    "teacher": ((1.04,.88,1.06),.36,"#E3BA99","#AA8179","#493337"),
    "student": ((.95,.92,.92),-.08,"#E3B581","#AE7F74","#422a42"),
    "florist": ((.91,.91,1.10),-.10,"#EDBE9E","#B17F72","#5a3440"),
}


def figure(c,name,role):
    k.STUDIO_PORTRAITS[role]=PORTRAITS[role]
    ring=k.RING
    k.RING=21
    try:
        cards={p.stem.split("_",1)[1]:p for p in ART.glob(role+"_*.png") if p.stem!=role+"_coat"}
        rig=k.build_studio_character(name,c,portrait=role,costume_image=ART/f"{role}_coat.png",
                                     expression_images=cards,dot_contrast=0)
    finally:
        k.RING=ring
    face=k.bpy.data.objects[name+" | ellipsoid head"]
    old=face.data.materials[0]
    _,_,lit,shade,hair=PORTRAITS[role]
    clean=k.make_lit_cel_face_material(name+" clean skin",tone=lit,shadow=shade)
    for ob in rig.root.children_recursive:
        if ob.type=="MESH" and ob.data.materials and ob.data.materials[0]==old:
            ob.data.materials[0]=clean
    torso=k.bpy.data.objects[name+" | graphic pill torso"]
    torso.data.materials[0]=k.make_cel_character_material(name+" body",
                     {"boy":"#ebc23b","teacher":"#e8d9cb","student":"#8e58a6","florist":"#3a7252"}[role])
    hair_mat=k.make_cel_character_material(name+" hair",hair)
    cap=k.bpy.data.objects[name+" | shaped hair cap"]
    cap.data.materials[0]=hair_mat
    if role=="boy":
        red=k.make_cel_character_material("Poppy-red twill baseball cap","#db412f")
        trim=k.make_cel_character_material("Deep cherry brim underside","#9c2630")
        seam=k.make_cel_character_material("Warmer cap stitching","#ff835e")
        top=k.ball("Structured red baseball-cap crown",c,(0,.018,.155),(.248,.203,.132),red,rig.head,28,17)
        brim=k.ball("Curved red cap visor",c,(0,-.168,.115),(.247,.165,.026),trim,rig.head,30,12)
        brim.rotation_euler.x=.11
        edge=k.ball("Red twill visor face",c,(0,-.168,.128),(.240,.159,.018),red,rig.head,30,12)
        edge.rotation_euler.x=.11
        for ob in (top,brim):
            outline=k.apply_character_ink(ob,c)
            outline.id_data.data.materials[0]=k.bpy.data.materials["Studio | espresso hull"]
            rig.ink_modifiers.append(outline)
        medallion=k.ball("Warm cream embroidered cap patch",c,(0,-.174,.201),(.055,.020,.037),
             k.make_cel_character_material("Cap cloth badge","#ffe3a3"),rig.head,18,10)
        line(c,"Arcing raised cap seams",[(x,-.156+.067*(abs(x)/.18)**2,.186+.09*(1-abs(x)/.19))
              for x in (-.18,-.13,-.07,0,.07,.13,.18)],.0045,seam,rig.head)
    elif role=="florist":
        bun=k.ball("Rounded florist bun",c,(.079,.158,.187),(.132,.108,.124),hair_mat,rig.head,20,13)
        mod=k.apply_character_ink(bun,c,pixels=2.6)
        mod.id_data.data.materials[0]=k.bpy.data.materials["Studio | espresso hull"]
        rig.ink_modifiers.append(mod)
        k.ball("Small rose bun tie",c,(.078,.139,.213),(.094,.088,.096),
               k.make_cel_character_material("Dusty pink bow","#c97189"),rig.head,16,10)
    elif role=="student":
        for ob in (cap,*(mod.id_data for mod in rig.ink_modifiers if mod.id_data.parent==cap)):
            for modifier in ob.modifiers:
                if modifier.type=="SUBSURF":
                    modifier.levels=modifier.render_levels=1
        for i in range(17):
            a=(i+2)*2.4
            u=.105+.108*((i*7)%13)/12
            x=u*math.cos(a)
            curl=k.ball("Rounded charcoal curl",c,(x,.031+.70*u*math.sin(a),.124+.076*(1-u/.225)),
                        (.081,.076,.079),hair_mat,rig.head,12,7)
            mod=k.apply_character_ink(curl,c,pixels=2.5)
            mod.id_data.data.materials[0]=k.bpy.data.materials["Studio | espresso hull"]
            rig.ink_modifiers.append(mod)
    rig.pose(None,(0,0,0),0,0,REST,STAND,bounce=-.09)
    rig.normal_legs=rig.measure_leg_lengths()
    return rig


def key(obj,frame,*props):
    for prop in props:
        obj.keyframe_insert(prop,frame=frame)


def pose(rig,f,root,*,yaw=0,tilt=0,arms=REST,legs=STAND,mode=None,seat=False,head=(0,0),sweat=None):
    short=-.138 if seat else -.09
    rig.pose(f,root,yaw,tilt,arms,legs,mode,bounce=short,head_tilt=head[0],head_yaw=head[1],sweat=sweat,
             leg_lengths=rig.normal_legs if seat else None)
    k.studio_pose_hands(rig,f)


def contact_arm(world,root,yaw,tilt,elbow,seat=True):
    mat=Euler((0,0,yaw)).to_matrix()@Euler((tilt,0,0)).to_matrix()
    pivot=Vector(root)+Vector((0,0,.452 if seat else .5))
    hand=mat.transposed()@(Vector(world)-pivot)
    return (hand-.016*(hand-Vector(elbow)).normalized(),elbow)
