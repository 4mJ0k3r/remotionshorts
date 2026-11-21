"""Head silhouettes, cel ink, signature hair and continuity props."""
import math
from pathlib import Path
from types import SimpleNamespace

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


def strand(c,rig,name,parent,centers,widths,depth,material,outlined=True):
    points=[Vector(point) for point in centers]
    smooth=[]
    radii=[]
    for i in range(len(points)-1):
        a,b,c1,d=points[max(0,i-1)],points[i],points[i+1],points[min(len(points)-1,i+2)]
        for x in (0,.5):
            smooth.append(.5*(2*b+(-a+c1)*x+(2*a-5*b+4*c1-d)*x*x+(-a+3*b-3*c1+d)*x*x*x))
            radii.append(widths[i]*(1-x)+widths[i+1]*x)
    smooth.append(points[-1])
    radii.append(widths[-1])
    vertices=[]
    for i,(point,width) in enumerate(zip(smooth,radii)):
        previous=smooth[max(0,i-1)]
        following=smooth[min(len(smooth)-1,i+1)]
        bend=following-previous
        across=Vector((-bend.z,0,bend.x)).normalized()
        center=Vector(point)
        for j in range(10):
            theta=j*math.tau/10
            vertices.append(center+across*(width*math.cos(theta))+Vector((0,width*depth*math.sin(theta),0)))
    faces=[(i*10+j,(i+1)*10+j,(i+1)*10+(j+1)%10,i*10+(j+1)%10)
           for i in range(len(smooth)-1) for j in range(10)]
    end=(len(smooth)-1)*10
    faces.extend((tuple(range(10)),tuple(reversed(range(end,end+10)))))
    obj=k.mesh(name,c,vertices,faces,material,parent,True)
    if outlined:
        accent_ink(rig,obj,c)


def figure(c,name,role,*,headphones=True,compact=False,expressions=None):
    custom={
        "boy":((1.02,.91,1.01),.19,"#F6DFC9","#D6BAB2","#21212d"),
        "shoko":((.90,.89,1.094),-.13,"#F6DFC9","#D6BAB2","#9a79ba"),
        "classmate":((1.02,.91,.96),.26,"#F6DFC9","#D6BAB2","#353344"),
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
    head_mesh=bpy.data.objects[name+" | ellipsoid head"]
    previous=head_mesh.data.materials[0]
    skin=k.make_lit_cel_face_material(name+" clean two-tone cel skin",tone="#F6DFC9",shadow="#D6BAB2")
    for obj in c.objects:
        if obj.type=="MESH" and obj.data.materials and obj.data.materials[0]==previous:
            obj.data.materials[0]=skin
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
            centers=[(side*x,y,z) for x,y,z in ((.125,-.133,.165),(.179,-.133,.112),
                     (.202,-.118,.049),(.197,-.117,-.028),(.174,-.127,-.115))]
            strand(c,rig,"Slim curved lavender cheek strand",rig.head,centers,(.043,.037,.026,.017,.002),.70,hair)
        fringe=k.make_cel_character_material("Upper lavender bang layer","#ab89c7")
        for side in (-1,1):
            centers=[(side*x,y,z) for x,y,z in ((.014,-.121,.190),(.067,-.160,.153),
                     (.105,-.166,.107),(.145,-.145,.080))]
            strand(c,rig,"Swept lavender bang panel",rig.head,centers,(.052,.049,.031,.002),.60,fringe,outlined=False)
        tie=k.ball("Lavender hair elastic",c,(.101,.151,.193),(.072,.059,.057),
                   k.make_cel_character_material("Lavender hair tie","#c18db0"),rig.head,segments=16,rings=9)
        accent_ink(rig,tie,c)
        pony=k.empty("High lavender ponytail swing",c,(.108,.158,.189),rig.head)
        rig.pony=pony
        stream=[(.015,.005,.028),(.091,.064,.039),(.162,.126,-.018),(.204,.163,-.107),
                (.221,.180,-.199),(.247,.196,-.273),(.290,.203,-.321)]
        strand(c,rig,"Continuous flowing lavender ponytail",pony,stream,(.029,.059,.068,.062,.050,.033,.0015),1.08,hair)
        gloss=k.make_cel_character_material("Ponytail pastel hair glint","#d2afe2")
        line(c,"Curved gloss down the ponytail",[(.085,.012,.058),(.161,.059,.009),
             (.211,.109,-.090),(.230,.137,-.197),(.257,.165,-.265)],.010,gloss,pony)
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
    pos=Vector(route(f))
    delta=Vector(route(last))-Vector(route(first))
    yaw=math.atan2(delta.x,-delta.y) if delta.length>.001 else yaw
    forward=Vector((math.sin(yaw),-math.cos(yaw),0))
    right=Vector((math.cos(yaw),math.sin(yaw),0))
    period=27
    stance_frames=period*.60
    cycle=(f-first)*math.tau/period
    arms=[]
    legs=[]
    for index,side in enumerate((-1,1)):
        offset=first-index*period*.5
        contact=offset+period*math.floor((f-offset)/period)
        elapsed=f-contact
        def plant(at):
            anticipate=min(last,max(first,at+stance_frames*.51))
            return Vector(route(anticipate))+right*(side*.098)
        foot=plant(contact)
        lift=0.
        if elapsed>stance_frames:
            swing=(elapsed-stance_frames)/(period-stance_frames)
            foot=foot.lerp(plant(contact+period),k.look.ease5(swing))
            lift=.09*math.sin(math.pi*swing)**1.55
        distance=(foot-pos).dot(forward)
        foot_y=-distance+.021
        knee_y=min(-.057,foot_y*.47-.082)-.27*lift
        legs.append(((side*.098,foot_y,.027+lift),(side*.098,knee_y,.320+.21*lift)))
        opposite=math.cos(cycle+index*math.pi)
        arms.append(((side*.157,-.084+.123*opposite,.122+.025*abs(opposite)),
                     (side*.180,-.069+.060*opposite,.249)))
    for index,arm in (override or {}).items():
        arms[index]=arm
    bob=.020*(.5-.5*math.cos(cycle*2))
    act(rig,f,pos,yaw,.047,arms,legs,expression,face,bounce=bob)
    return SimpleNamespace(bounce=bob,yaw=yaw)
