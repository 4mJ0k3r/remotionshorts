"""Build and bake the approved-scope Part 1 edit."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parents[2]/"scripts")]
import ricks_v2_kit as k
from cast import REST, STAND, body_transform, figure, key, padding, pose, waddle, world_arm
from sets import ART, bedroom, box, dumbbell, gym, palette, phone, stroke
from timing import CLANK, DAY1, DAY2, DROP, LENGTH, OUT, PHONE_IN, PHONE_OUT, WRONG_NUMBER, at


def smooth(t,a,b):
    return k.look.ease5((t-a)/(b-a))


def glide(t,a,b,start,end):
    return Vector(start).lerp(Vector(end),smooth(t,a,b))


def stage(scene,label):
    col=bpy.data.collections.new(label)
    scene.collection.children.link(col)
    return col


def visible(obj,f,state):
    obj.hide_render=obj.hide_viewport=not state
    key(obj,f,"hide_render","hide_viewport")


def restrict(collection,start,end,offset=0):
    pivot=k.empty(collection.name+" stage offset",collection)
    for obj in tuple(collection.objects):
        if obj!=pivot and obj.parent is None:
            obj.parent=pivot
    pivot.location.x=offset
    for obj in collection.objects:
        if obj==pivot:
            continue
        for channel in ("hide_render","hide_viewport"):
            action=obj.animation_data.action if obj.animation_data else None
            track=action.fcurves.find(channel) if action else None
            driver=obj.driver_add(channel).driver
            driver.expression=f"frame < {start} or frame > {end}"
            if track:
                prop=f'["authored_{channel}"]'
                obj[f"authored_{channel}"]=getattr(obj,channel)
                track.data_path=prop
                var=driver.variables.new()
                var.name="hidden"
                var.type="SINGLE_PROP"
                var.targets[0].id=obj
                var.targets[0].data_path=prop
                driver.expression+=" or hidden > 0.5"


def camera(scene,label,lens,focus,stop):
    cam=bpy.data.objects.new(label,bpy.data.cameras.new(label))
    scene.collection.objects.link(cam)
    k.setup_ricks_camera(cam,lens=lens)
    k.apply_portrait_dof(cam,focus,stop)
    return cam


def shot(cam,f,t,span,offset=0):
    a,b,p,q,u,v,lens=span
    shift=Vector((offset,0,0))
    cam.location=shift+glide(t,a,b,p,q)
    k.aim(cam,shift+glide(t,a,b,u,v))
    cam.data.lens=lens
    key(cam,f,"location","rotation_quaternion")
    key(cam.data,f,"lens")


def bind(scene,cam,time,label):
    marker=scene.timeline_markers.new(label,frame=at(time))
    marker.camera=cam


def put_hud(scene):
    tree=scene.node_tree
    out=next(n for n in tree.nodes if n.type=="COMPOSITE")
    current=out.inputs[0].links[0].from_socket
    for day,a,b in ((0,0,DAY1),(1,DAY1,DAY2),(2,DAY2,LENGTH/30)):
        sprite=tree.nodes.new("CompositorNodeImage")
        sprite.name=f"November scale HUD phase {day}"
        sprite.image=bpy.data.images.load(str(ART/f"hud_{day}.png"),check_existing=True)
        sprite.image.pack()
        scale=tree.nodes.new("CompositorNodeScale")
        scale.space="RENDER_SIZE"
        scale.frame_method="STRETCH"
        tree.links.new(sprite.outputs["Image"],scale.inputs[0])
        over=tree.nodes.new("CompositorNodeAlphaOver")
        over.name=f"November HUD phase {day} overlay"
        tree.links.new(current,over.inputs[1])
        tree.links.new(scale.outputs[0],over.inputs[2])
        factor=over.inputs[0]
        for f,value in sorted({1:0,at(a):1,at(b):0}.items()):
            factor.default_value=value
            factor.keyframe_insert("default_value",frame=f)
        track=tree.animation_data.action.fcurves.find(factor.path_from_id("default_value"))
        for point in track.keyframe_points:
            point.interpolation="CONSTANT"
        current=over.outputs[0]
    tree.links.new(current,out.inputs[0])


def move(obj,f,location,angles=(0,0,0),scale=None):
    obj.location=location
    obj.rotation_euler=angles
    key(obj,f,"location","rotation_euler")
    if scale is not None:
        obj.scale=(scale,)*3
        key(obj,f,"scale")


HOOK=(
    (0,2.33,(.31,-1.92,1.45),(.26,-1.73,1.41),(-.62,.02,1.13),(-.60,.02,1.15),26),
    (2.33,3.20,(1.14,.79,1.91),(1.16,.98,1.91),(1.22,2.70,1.91),(1.22,2.72,1.88),49),
    (3.20,6.37,(.04,-2.28,1.52),(.12,-2.10,1.49),(-.38,.18,1.18),(-.36,.18,1.21),26),
    (6.37,9.80,(-1.39,-1.42,1.49),(-1.26,-1.26,1.38),(-.60,-.015,1.19),(-.59,-.015,1.21),28),
)
BED=(
    (DAY1,PHONE_IN,(.85,-1.87,1.57),(.77,-1.73,1.55),(.57,.20,1.43),(.54,.20,1.46),26),
    (PHONE_IN,PHONE_OUT,(.55,-.66,1.425),(.55,-.59,1.421),(.55,-.02,1.407),(.55,-.02,1.407),52),
    (PHONE_OUT,13.67,(.13,-1.27,1.63),(.14,-1.18,1.56),(.41,.26,1.52),(.40,.27,1.48),28),
    (13.67,14.03,(1.17,-1.51,1.57),(1.143,-1.474,1.557),(.47,.25,1.47),(.47,.25,1.47),28),
)
GYM=(
    (DAY2,17.66,(.56,-2.35,1.39),(.72,-2.21,1.45),(-.79,-.34,.86),(-.53,-.34,.89),26),
    (17.66,19.55,(.81,-2.45,1.33),(.87,-2.39,1.32),(-.20,-.18,.82),(.17,-.18,.80),26),
    (19.55,20.22,(1.38,-1.55,1.43),(1.31,-1.47,1.41),(.63,.18,1.16),(.62,.19,1.17),28),
    (20.22,20.77,(.58,-.91,.411),(.58,-.89,.395),(.40,-.47,.13),(.38,-.43,.12),51),
    (20.77,LENGTH/30,(.36,-2.21,1.41),(.23,-2.27,1.43),(-.10,-.19,.81),(.33,-.12,.94),26),
)
CUTS=tuple(x[0] for x in (*HOOK,*BED,*GYM))
CHECKS=(.37,2.77,4.83,7.72,10.83,11.96,13.05,15.91,18.62,19.86,20.47,21.58)
PANELS=(4.83,13.05,18.62,15.91)


def find_shot(t,shots):
    return next(span for span in reversed(shots) if at(t)>=at(span[0]))


def build(output=OUT,polish=False):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    k.configure_ricks_scene(s,frame_end=LENGTH,samples=6)
    s.world=bpy.data.worlds.new("Deep blue November ambient")
    s.world.use_nodes=True
    background=s.world.node_tree.nodes.get("Background")
    background.inputs[0].default_value=k.look.rgba("#6c6885")
    background.inputs[1].default_value=.26
    m=palette()
    bedroom_set=stage(s,"Bedroom | physical set")
    opening=stage(s,"Bedroom | standing Hero")
    sleeping=stage(s,"Bedroom | seated Hero")
    training=stage(s,"Gym | set and cast")
    clocks=bedroom(bedroom_set,m)
    gym(training,m)
    hero=figure(opening,"November Hero on his feet","hero")
    sitter=figure(sleeping,"November Hero sitting up","hero")
    walker=figure(training,"November Hero in the gym","hero")
    bro=figure(training,"Teal-shirt gym bro","bro")
    padding(sleeping,sitter,8,scale=1.38 if polish else 1.,forward=-.087 if polish else .006,
            height=.091 if polish else .066)
    padding(training,walker,16,scale=2 if polish else 1.,forward=-.040 if polish else .006,
            height=.075 if polish else .066)
    for foot in (*sitter.feet,*sitter.legs):
        for obj in (foot,*foot.children_recursive):
            visible(obj,at(DAY1),False)
    prop,screens=phone(sleeping,m)
    weight=[dumbbell(training,m,"Hero's blue dumbbell") for _ in range(2)]
    calendar_focus=k.empty("Focus | circled Nov 1",bedroom_set,(.974,2.710,1.975))
    phone_focus=k.empty("Focus | phone glass",sleeping,(0,-.024,0),prop)
    drop_focus=k.empty("Focus | gym floor impact",training)
    tracked=[k.empty("Focus | Hero face plane",col,(0,-.166,.021),rig.head)
             for col,rig in ((opening,hero),(sleeping,sitter),(training,walker),(training,bro))]
    cams=[camera(s,name,lens,target,stop) for name,lens,target,stop in (
        ("26mm standing portrait",26,tracked[0],1.2),("Calendar insert",49,calendar_focus,2.6),
        ("26mm bedside portrait",26,tracked[1],1.2),("Phone macro",52,phone_focus,3.4),
        ("26mm gym walking portrait",26,tracked[2],1.2),("Gym bro reaction",28,tracked[3],1.2),
        ("Dumbbell impact macro",51,drop_focus,3.4))]
    s.camera=cams[0]
    k.setup_ricks_compositor(s,camera=s.camera)
    phone_in,phone_out=(11.30,12.30) if polish else (PHONE_IN,PHONE_OUT)
    opening_shots=HOOK if not polish else (
        (0,2.33,(-1.46,-1.83,1.42),(-1.45,-1.63,1.38),(-.30,.09,1.14),(-.30,.09,1.17),26),
        HOOK[1],
        (3.20,6.37,(-1.51,-1.89,1.44),(-1.45,-1.71,1.40),(-.30,.09,1.16),(-.30,.09,1.17),26),
        HOOK[3],
    )
    bed_shots=BED if not polish else (
        (DAY1,phone_in,*BED[0][2:]),
        (phone_in,phone_out,(.55,-.607,1.418),(.55,-.58,1.417),(.55,-.026,1.407),(.55,-.026,1.407),52),
        (phone_out,13.67,*BED[2][2:]),BED[3],
    )
    gym_shots=GYM if not polish else (
        GYM[0],(17.66,19.55,(.63,-2.78,1.49),(.83,-2.88,1.49),(.21,.09,.88),(.34,.10,.89),26),
        (19.55,20.22,(1.82,-.94,1.49),(1.75,-.93,1.47),(1.23,.68,1.17),(1.23,.68,1.17),28),*GYM[3:],
    )
    for kcam,t,label in ((0,0,"Bedroom hook"),(1,2.33,"November calendar"),(0,3.20,"Doubling gesture"),
                         (0,6.37,"Day thirty reaction"),(2,DAY1,"Day one at 2 AM"),(3,phone_in,"Incoming message"),
                         (2,phone_out,"Heartbreak"),(2,13.67,"Deadpan hold"),(4,DAY2,"Day two gym"),
                         (4,17.66,"Penguin walk"),(5,19.55,"Gym bro clocking Hero"),(6,20.22,"Dumbbell clank"),
                         (4,20.77,"Awkward wave and exit")):
        bind(s,cams[kcam],t,label)
    for rig in (hero,sitter,walker):
        k.setup_hero_portrait_lighting(rig.head,bg_dim=.68)
    visible(clocks[0],1,True)
    visible(clocks[0],at(DAY1),False)
    visible(clocks[1],1,False)
    visible(clocks[1],at(DAY1),True)
    put_hud(s)
    start_loc=(-1.34,-.347,0)
    db_release=None

    def route(t):
        forward=.1+.335*max(0,min(5.08,t-14.77))
        # The pause gives both feet a planted beat before the about-face.
        step=max(0,min(1.13,t-20.83))
        back=1.54*(step-.098*(1-math.exp(-step/.098)))
        return (start_loc[0]+forward-back,start_loc[1]+.161*smooth(t,20.76,21.91),0)

    def heading(t):
        return .93-2.28*smooth(t,20.71,21.30)

    for f in range(1,LENGTH+1):
        t=(f-1)/30
        if f<at(DAY1):
            span=find_shot(t,opening_shots)
            shot(cams[1] if span==opening_shots[1] else cams[0],f,t,span)
            point=smooth(t,.06,.66)*(1-smooth(t,4.87,5.14))
            double=smooth(t,4.38,5.18)*(1-smooth(t,6.03,6.46))
            notice=smooth(t,6.07,6.62)
            root=(-.64+.032*smooth(t,0,.75),-.02,0)
            right=((.19+.17*point+.087*double,-.14+.106*point,.17+.43*point+.104*double),
                   (.219+.085*point,-.055+.081*point,.26+.143*point))
            left=((- .203-.158*double,-.137,.17+.17*double),(-.231,-.064,.268))
            pose(hero,f,root,("shock" if polish else "curious") if f>=at(6.43) else "grin",yaw=.16+.28*point,
                 tilt=.046*smooth(t,0,.83)-.09*notice,sway=-.075*double,
                 head=(.08*point+(.21 if polish else -.097)*notice,.25*point),
                 arms=(left,right),bob=.012*smooth(t,4.81,5.16)*(1-smooth(t,5.26,5.70)))
        elif f<at(DAY2):
            span=find_shot(t,bed_shots)
            shot(cams[3] if span==bed_shots[1] else cams[2],f,t,span)
            wake=smooth(t,DAY1,10.58)
            slump=smooth(t,12.15,13.49)
            root=(.37,.24,.222+.082*wake-.028*slump)
            turn=.10-.19*slump
            tilt=-.13*(1-wake)+.12*slump
            phone_p=glide(t,10.18,11.22,(.62,.012,1.016),(.55,-.025,1.407))
            if f>=at(phone_out):
                phone_p=glide(t,phone_out+.16,13.54,(.55,-.025,1.407),(.64,-.03,1.008))
            move(prop,f,phone_p,(.064*(1-wake)+.174*slump,-.11*slump,.026*slump))
            if f in (at(DAY1),at(WRONG_NUMBER)):
                for j,screen in enumerate(screens):
                    visible(screen,f,j==int(f>=at(WRONG_NUMBER)))
            grip=Vector(phone_p)+Vector((.053,.003,-.059))
            arm=world_arm(grip,root,turn,tilt,(.232,-.128,.406))
            pose(sitter,f,root,"deadpan" if f>=at(phone_out) else "hope",yaw=turn,tilt=tilt,
                 head=(.19*slump+.067*(1-wake),.19*(1-slump)),arms=(REST[0],arm))
        else:
            span=find_shot(t,gym_shots)
            cam=cams[5] if span==gym_shots[2] else cams[6] if span==gym_shots[3] else cams[4]
            shot(cam,f,t,span,offset=32)
            yaw=heading(t)
            amount=(1-.88*smooth(t,19.80,20.03))+.73*smooth(t,20.91,21.36)
            if t>=20.77:
                root,legs,sway,bob=waddle(t,route,heading,phase=20.84,amount=amount,period=.37,width=.194 if polish else .13)
            else:
                root,legs,sway,bob=waddle(t,route,heading,phase=DAY2,amount=amount,width=.194 if polish else .13)
            wave=smooth(t,20.62,20.91)*(1-smooth(t,21.20,21.58))
            sag=smooth(t,19.86,20.36)
            recoil=smooth(t,CLANK,CLANK+.10)*(1-smooth(t,CLANK+.10,CLANK+.32))
            arms=(((-.223,-.166,.178),(-.232,-.064,.277)),
                  ((.216+.055*wave,-.176,.192-.036*sag+.057*recoil+.36*wave),
                   (.232+.082*wave,-.076,.265+.12*wave)))
            pose(walker,f,root,"awkward" if f>=at(CLANK) else "strain",yaw=yaw,tilt=.065*recoil,
                 sway=sway,head=(-.061*recoil,-.47+.14*wave),arms=arms,legs=legs,bob=bob,
                 sweat=.19 if 19.15<=t<21.36 else None)
            surprise=smooth(t,18.25,19.48)
            pose(bro,f,(1.23,.71,0) if polish else (.59,.30,0),"shock" if surprise>.60 else "sideeye",yaw=-.35,
                 tilt=-.10*surprise,head=(-.072*surprise,-.29),arms=REST)
            transform=body_transform(walker)
            for j,obj in enumerate(weight):
                hand=walker.studio_hands[j]
                position=transform@(Vector(hand.location)+Vector((0,-.014,-.010)))
                if j==1:
                    if f<at(DROP):
                        db_release=position.copy()
                    else:
                        u=max(0,min(1,(t-DROP)/(CLANK-DROP)))
                        position=Vector((db_release.x+.076*u,db_release.y-.026*u,db_release.z*(1-u*u)+.062*u*u))
                        bounce=smooth(t,CLANK,CLANK+.13)*(1-smooth(t,CLANK+.13,CLANK+.29))
                        position.z+=.08*bounce
                        position.x+=.05*smooth(t,CLANK,CLANK+.36)
                        move(obj,f,position,(0,.64*math.sin(math.pi*u)+1.2*bounce,yaw+.52*u))
                        if span==GYM[3]:
                            mark=Vector((db_release.x+.092,db_release.y-.025,.287))
                            drop_focus.location=mark
                            base=Vector((32,0,0))+mark
                            cam.location=base+Vector((.34,-.99,.24))
                            k.aim(cam,base)
                            key(cam,f,"location","rotation_quaternion")
                        continue
                move(obj,f,position,(0,.077*math.sin(t*8),yaw))
    for col,first,last,offset in ((bedroom_set,1,at(DAY2)-1,0),(opening,1,at(DAY1)-1,0),
                                  (sleeping,at(DAY1),at(DAY2)-1,0),(training,at(DAY2),LENGTH,32)):
        restrict(col,first,last,offset)
    for rig in (hero,sitter,walker,bro):
        rig.finish_bake()
    for action in bpy.data.actions:
        for track in action.fcurves:
            if action==s.node_tree.animation_data.action:
                continue
            mode="CONSTANT" if "hide_" in track.data_path or track.data_path=="lens" else "LINEAR"
            for point in track.keyframe_points:
                point.interpolation=mode
    s.frame_set(1)
    s.render.image_settings.file_format="PNG"
    bpy.ops.file.pack_all()
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output/("part1_v02.blend" if polish else "part1_v01.blend")))
    split=[at(shot[0])-1 for shot in (*opening_shots,*bed_shots,*gym_shots)]+[LENGTH]
    (output/"shots.json").write_text(json.dumps({
        "cuts":split[1:-1],"proof_frames":[at(t) for t in CHECKS],"panels":[at(t) for t in PANELS],
        "shots":[{"id":i,"a":a,"b":b} for i,(a,b) in enumerate(zip(split,split[1:]),1)],
    },indent=2),encoding="utf8")


if __name__=="__main__":
    build()
