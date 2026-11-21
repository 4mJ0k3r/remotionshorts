"""November cast built on the shared cel rig with fitted costume props."""
import math

from mathutils import Euler, Matrix, Vector
import ricks_v2_kit as k
from sets import ART, stroke

REST=tuple(((s*.193,-.148,.17),(s*.205,-.075,.26)) for s in (-1,1))
STAND=tuple(((s*.119,-.025,.028),(s*.113,-.094,.269)) for s in (-1,1))
SHORT=.090


def accent_ink(col,obj,rig):
    mod=k.apply_character_ink(obj,col,pixels=3.0)
    mod.id_data.data.materials[0]=k.bpy.data.materials["Studio | espresso hull"]
    rig.ink_modifiers.append(mod)


def figure(col,name,role):
    hero=role=="hero"
    k.STUDIO_PORTRAITS[role]=((1.01,.91,1.025),.23,"#F5DBC2","#CDA994","#42303c") if hero else (
        (1.04,.91,.935),.34,"#D7A782","#A97974","#2c3345")
    ring=k.RING
    k.RING=26 if hero else 20
    try:
        cards={p.stem.removeprefix(role+"_"):p for p in ART.glob(role+"_*.png") if not p.stem.endswith("_outfit")}
        rig=k.build_studio_character(name,col,portrait=role,costume_image=ART/f"{role}_outfit.png",
                                     expression_images=cards,dot_contrast=0)
    finally:
        k.RING=ring
    face=k.bpy.data.objects[name+" | ellipsoid head"]
    old=face.data.materials[0]
    _,_,tone,shade,hair=k.STUDIO_PORTRAITS[role]
    clean=k.make_lit_cel_face_material(name+" clean matte skin",tone=tone,shadow=shade)
    for obj in rig.root.children_recursive:
        if obj.type=="MESH" and obj.data.materials and obj.data.materials[0]==old:
            obj.data.materials[0]=clean
    torso=k.bpy.data.objects[name+" | graphic pill torso"]
    torso.data.materials[0]=k.make_cel_character_material(name+" pullover fabric","#9e283b" if hero else "#17807f")
    scalp=k.bpy.data.objects[name+" | shaped hair cap"]
    if not hero:
        for obj in (scalp,*(m.id_data for m in rig.ink_modifiers if m.id_data.parent==scalp)):
            for modifier in obj.modifiers:
                if modifier.type=="SUBSURF":
                    modifier.levels=modifier.render_levels=1
    hair_mat=k.make_cel_character_material(name+" charcoal brown hair",hair)
    scalp.data.materials[0]=hair_mat
    for obj in rig.head.children:
        if obj.type=="CURVE" and "highlight" in obj.name:
            obj.data.materials[0]=k.make_cel_character_material(name+" quiet hair sheen","#806157")
    if hero:
        for j in range(7):
            x=(j-3)*.064
            length=.063+.067*math.sin(j*1.5)**2
            top=.151+.043*(1-abs(x)*3.8)
            vertices=[]
            for row,width in enumerate((.077,.056,.029,.001)):
                t=row/3
                center=x+t*(.065-.035*math.sin(j))
                for i in range(10):
                    angle=i*math.tau/10
                    vertices.append((center+width*math.cos(angle),-.045-.083*t+.86*width*math.sin(angle),top+length*t))
            faces=[(i+10*r,(i+1)%10+10*r,(i+1)%10+10*(r+1),i+10*(r+1)) for r in range(3) for i in range(10)]
            faces.extend((tuple(reversed(range(10))),tuple(range(30,40))))
            spike=k.mesh("Swept dark-brown tuft",col,vertices,faces,hair_mat,rig.head,smoothing=True)
            accent_ink(col,spike,rig)
        gloss=k.make_cel_character_material("Subtle warm brown ink hair highlights","#806052")
        for j in range(3):
            start=-.166+j*.105
            stroke(col,"Painted curved quiff glint",[(start+i*.014,-.120-i*.003,.194+.031*math.sin(i*.44))
                   for i in range(8)],.004,gloss,rig.head)
    else:
        blue=k.make_cel_character_material("Two-step blue cap","#3262a6")
        bill=k.make_cel_character_material("Cap dark navy underbrim","#263765")
        cap=k.ball("Gym bro blue baseball cap",col,(0,.014,.166),(.246,.199,.113),blue,rig.head,26,15)
        brim=k.ball("Blue curved cap visor",col,(0,-.163,.131),(.229,.153,.023),bill,rig.head,26,11)
        accent_ink(col,cap,rig)
        accent_ink(col,brim,rig)
        k.ball("Small embroidered peak patch",col,(0,-.166,.217),(.031,.018,.034),blue,rig.head,13,8)
    white=k.make_cel_character_material("Cream white sneaker leather","#f7ebdd")
    sole=k.make_cel_character_material("Cool charcoal sneaker soles","#6a7189")
    for shoe in rig.feet:
        shoe.data.materials[0]=white
        shoe.scale=(1.48,1.60,1.08)
        k.ball("Contrasting rubber shoe sole",col,(0,0,-.009),(.026,.036,.007),sole,shoe,12,7)
        for j in range(2):
            stroke(col,"Slate sneaker lace",[(-.015,-.019+j*.012,.014),(.015,-.019+j*.012,.014)],.003,sole,shoe)
    return rig


def padding(col,rig,width_cm,*,scale=1.,forward=.006,height=.066):
    """Two smooth fabric pods on the outside of the sweatpants hips."""
    radius=width_cm/200*scale
    cloth=k.make_cel_character_material("Matte heather-grey sweatpant padding","#747986")
    trim=k.make_cel_character_material("Heather-grey side seam","#a5a1ab")
    for s in (-1,1):
        cx=s*(.110+radius*.42)
        pad=k.ball("Clothed sweatpants side pad",col,(cx,forward,height),
                   (radius,radius*.90,radius),cloth,rig.body,21,13)
        accent_ink(col,pad,rig)
        stroke(col,"Curved gray fabric seam",[(cx+s*.16*radius,forward-.87*radius,height+z*radius)
               for z in (-.34,0,.34)],.003,trim,rig.body)


def key(obj,f,*props):
    for prop in props:
        obj.keyframe_insert(prop,frame=f)


def pose(rig,f,loc,mode,*,yaw=0,tilt=0,sway=0,head=(0,0),arms=REST,legs=STAND,bob=0,sweat=None):
    rig.pose(f,loc,yaw,tilt,arms,legs,mode,bounce=bob-SHORT,head_tilt=head[0],head_yaw=head[1],sweat=sweat)
    rig.body.rotation_euler.y=sway
    key(rig.body,f,"rotation_euler")
    k.studio_pose_hands(rig,f)


def body_transform(rig):
    def local(obj):
        return Matrix.LocRotScale(obj.location,obj.rotation_euler.to_quaternion(),obj.scale)
    return local(rig.root) @ local(rig.body)


def world_arm(target,loc,yaw,tilt,elbow,*,bob=0):
    rotation=Euler((0,0,yaw)).to_matrix()@Euler((tilt,0,0)).to_matrix()
    pivot=Vector(loc)+Vector((0,0,.59-SHORT+bob))
    goal=rotation.transposed()@(Vector(target)-pivot)
    return goal-.016*(goal-Vector(elbow)).normalized(),elbow


def waddle(t,route,heading,phase=0.,amount=1.,period=.78,width=.13):
    """Small forward knee bends and world-pinned feet, cut with stiff shoulders."""
    root=Vector(route(t))
    yaw=heading(t)
    c,s=math.cos(yaw),math.sin(yaw)
    legs=[]
    for side,step in ((-1,0),(1,period*.5)):
        cycle=(t-phase-step)%period
        strike=t-cycle
        swing=max(0.,(cycle/period-.63)/.37)
        settle=k.look.ease5(swing)
        def anchor(when):
            angle=heading(when)
            return Vector(route(when))+Vector((width*math.cos(angle)*side,width*math.sin(angle)*side,0))
        anticipation=period*.29
        foot=anchor(strike+anticipation).lerp(anchor(strike+period+anticipation),settle)
        dx,dy,_=foot-root
        x=c*dx+s*dy
        y=-s*dx+c*dy+.021
        lift=.057*math.sin(math.pi*swing)**1.35*amount
        legs.append(((x,y,.027+lift),(x*.76,min(-.047,y*.48)-.37*lift,.275+.35*lift)))
    sway=.095*math.sin((t-phase)*math.tau/period)*amount
    bob=.018*math.sin((t-phase)*math.tau/period)**2*amount
    return root,legs,sway,bob
