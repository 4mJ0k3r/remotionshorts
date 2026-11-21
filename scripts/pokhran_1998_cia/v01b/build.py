"""Bake Part 1 and four out-of-range studio portrait cameras."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Euler, Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
sys.path[:0]=[str(HERE),str(ROOT/"scripts")]
import ricks_v2_kit as k
from sets import box, cutaway, label, lights, orbit, war_room

OUT=ROOT/"renders/pokhran_1998_cia/v01b"
END=455
CAL=(1,89,143,190,284,329,405,452)
BENCH=(*CAL,116,117,279,379)

def key(obj,frame,*props):
    for prop in props:obj.keyframe_insert(prop,frame=frame)

def group(scene,name,x):
    collection=bpy.data.collections.new(name)
    scene.collection.children.link(collection)
    return collection,x

def activate(stage,expression):
    collection,offset=stage
    root=k.empty(collection.name+" anchor",collection)
    for obj in tuple(collection.objects):
        if obj!=root and obj.parent is None:obj.parent=root
    root.location.x=offset
    for obj in collection.objects:
        if obj==root:continue
        for prop in ("hide_render","hide_viewport"):
            action=obj.animation_data.action if obj.animation_data else None
            track=action.fcurves.find(prop) if action else None
            driver=obj.driver_add(prop).driver
            driver.expression=expression
            if track:
                name="pose_"+prop
                obj[name]=bool(getattr(obj,prop));track.data_path=f'["{name}"]'
                v=driver.variables.new();v.name="pose_hidden";v.type="SINGLE_PROP"
                v.targets[0].id=obj;v.targets[0].data_path=track.data_path
                driver.expression+=" or pose_hidden > .5"

def cast(c,name,portrait):
    art=HERE/"art"
    rig=k.build_studio_character(name,c,portrait=portrait,costume_image=art/f"{portrait}_coat.png",
        dot_contrast=1.15, expression_images={path.stem.removeprefix(portrait+"_"):path for path in art.glob(portrait+"_*.png")
                           if not path.stem.endswith("_coat")})
    torso=bpy.data.objects[name+" | graphic pill torso"]
    torso.data.materials[0]=k.make_cel_character_material(name+" costume backing",
                                                        "#29334c" if portrait=="analyst" else "#4a543b")
    k.studio_shadow_dots(torso.data.materials[0], .24, contrast=1.15)
    if portrait=="kalam":
        hair=bpy.data.objects[name+" | shaped hair cap"]
        shell=next(item.id_data for item in rig.ink_modifiers if item.id_data.parent==hair)
        columns=len(hair.data.vertices)//14
        for index,vertex in enumerate(hair.data.vertices):
            row,column=divmod(index,columns)
            angle=math.tau*column/columns
            front=max(0.,-math.sin(angle))
            center=math.exp(-((angle-1.5*math.pi)/.21)**2)
            hem=1.96-.70*front-.135*center+.044*math.cos(3*angle)
            polar=.012+(hem-.012)*row/13
            vertex.co=((k.HEAD[0]+.011)*math.sin(polar)*math.cos(angle),
                       (k.HEAD[1]+.011)*math.sin(polar)*math.sin(angle)+.010,
                       (k.HEAD[2]+.019)*math.cos(polar)+.014)
            shell.data.vertices[index].co=vertex.co
    if portrait=="engineer":
        ink=k.emission("Patrol-boot silhouette",k.STUDIO_INK)
        for foot in rig.feet:
            foot.scale=(1.16,1.35,1.12)
            foot.data.materials[0]=ink
    return rig

def stage_look(c):
    coat=k.texture("Warm plum studio paper",("#292238","#4b3e57","#705b6a"),"plaster",(.7,.84))
    box(c,"Portrait studio backdrop",(0,1.13,1.65),(6,.18,4),coat)
    lights(c,"#ffc994","#879bd3")

def ease(f,a,b):
    return k.look.ease5((f-a)/(b-a))

def camera_at(cam,frame,stage,p,aim,lens=26,focus=None):
    forward=(Vector(aim)-Vector(p)).normalized()
    cam.location=Vector(p)+Vector((stage[1],0,0))
    cam.rotation_mode="QUATERNION"
    cam.rotation_quaternion=forward.to_track_quat("-Z","Y")
    cam.data.lens=lens
    cam.data.dof.focus_distance=max(.085,(Vector(focus or aim)-Vector(p)).dot(forward))
    key(cam,frame,"location","rotation_quaternion")
    key(cam.data,frame,"lens","dof.focus_distance")

def aim_scan(obj,frame,start,finish,width,depth):
    direction=Vector(finish)-Vector(start)
    obj.location=start
    obj.rotation_mode="QUATERNION"
    obj.rotation_quaternion=direction.to_track_quat("Z","Y")
    obj.scale=(width,depth,direction.length)
    key(obj,frame,"location","rotation_quaternion","scale")

def mug_grip(mug,boss,frame,root,yaw,tilt,sip):
    tip=Vector(boss.arms[1].data.splines[0].bezier_points[-1].co)
    contact=root+Euler((0,0,yaw)).to_matrix()@(
        Euler((tilt,0,0)).to_matrix()@tip+Vector((0,0,.59)))
    mug.rotation_euler=(-.15*sip,.21*sip,math.pi+yaw+.10*sip)
    # The outer arc is the visible contact point, in the mug's local space.
    anchor=Vector((.113,0,0))
    mug.location=contact-mug.rotation_euler.to_matrix()@anchor
    key(mug,frame,"location","rotation_euler")
    return (mug.location+mug.rotation_euler.to_matrix()@anchor-contact).length

def bake_paper(scene):
    nodes,links=scene.node_tree.nodes,scene.node_tree.links
    output=next(n for n in nodes if n.type=="COMPOSITE")
    source=output.inputs[0].links[0].from_socket
    image=bpy.data.images.new("Warm paper grain",320,320)
    from random import Random
    rng=Random(38)
    pixels=[]
    for _ in range(320*320):
        dot=.44+rng.random()*.12
        pixels.extend((dot*1.08,dot,dot*.93,1))
    image.colorspace_settings.name="Non-Color"
    image.pixels.foreach_set(pixels);image.pack()
    grain=nodes.new("CompositorNodeImage");grain.image=image
    scale=nodes.new("CompositorNodeScale");scale.space="RENDER_SIZE";scale.frame_method="STRETCH"
    mix=nodes.new("CompositorNodeMixRGB");mix.blend_type="SOFT_LIGHT";mix.inputs[0].default_value=.03
    links.new(grain.outputs[0],scale.inputs[0]);links.new(source,mix.inputs[1])
    links.new(scale.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],output.inputs[0])

def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    k.configure_ricks_scene(scene,frame_end=END,samples=7)
    scene.render.image_settings.file_format="PNG";scene.render.image_settings.compression=0
    scene.world=bpy.data.worlds.new("Indigo night");scene.world.use_nodes=True
    bg=next(n for n in scene.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#141e3b");bg.inputs[1].default_value=.34
    room=group(scene,"Period surveillance room",0); space=group(scene,"Stylized orbit",25)
    desert=group(scene,"Symbolic Thar test-site cutaway",50)
    kportrait=group(scene,"Kalam portrait",75); eportrait=group(scene,"Engineer portrait",100)
    boss=cast(room[0],"CIA Boss","analyst")
    mug=war_room(room[0],boss)
    satellite,sweep,orbital_scan=orbit(space[0])
    test_glow,desert_scan=cutaway(desert[0])
    index=k.emission("Museum exhibit marker cream","#f5d4a7",1.32)
    label(space[0],"RAJASTHAN",(.36,1.17,.14),.112,index)
    label(desert[0],"POKHRAN",(-.91,.47,2.16),.127,index)
    kalam=cast(kportrait[0],"Dr. Kalam","kalam"); engineer=cast(eportrait[0],"Field engineer","engineer")
    stage_look(kportrait[0]);stage_look(eportrait[0])
    camera=bpy.data.objects.new("26 mm delivery camera",bpy.data.cameras.new("Portrait camera"))
    scene.collection.objects.link(camera);scene.camera=camera
    k.setup_ricks_compositor(scene,camera=camera)
    bake_paper(scene)
    legs=[((side*.138,-.028,.027),(side*.14,-.085,.32)) for side in (-1,1)]
    seated_legs=[((side*.134,-.108,.154),(side*.149,-.232,.31)) for side in (-1,1)]
    contacts={}
    for f in range(1,END+1):
        look=ease(f,1,27)
        # Notice, wind-up, reach, sip, settle, still. Every segment has a soft stop.
        sip=.10*ease(f,393,397)+.57*ease(f,397,401)+.33*ease(f,401,404)-ease(f,407,415)
        test_glow.default_value=1.10+.81*ease(f,345,350)
        key(test_glow,f,"default_value")
        weight=.03*look
        root=Vector((-.34+weight,.49,.033))
        yaw=.19+.09*look
        tilt=.09+.07*look
        arms=[((-.202,-.104,.375),(-.232,-.026,.324)),
              (Vector((.283,-.275,.424)).lerp(Vector((-.096,-.283,.526)),sip),(.273,-.173,.329+.120*sip))]
        boss.pose(f,root,yaw,tilt,arms,seated_legs,"rest" if f in (1,415) else "sip" if f==404 else None,
                  head_yaw=.17*look, head_tilt=-.027*sip)
        k.studio_pose_hands(boss,f)
        error=mug_grip(mug,boss,f,root,yaw,tilt,sip)
        if f in (1,89,405,452):
            view=Euler((0,0,yaw)).to_matrix()
            leg_front=min((root+view@point).y for curve in boss.legs for item in curve.data.splines[0].bezier_points
                          for point in (item.co,item.handle_left,item.handle_right))
            contacts[str(f)]={"handle_error_m":error,"leg_clearance_behind_panel_m":leg_front-.027+.010}
        orbit_progress=ease(f,117,248)
        satellite.rotation_euler=(.04+.22*orbit_progress,.15+.26*orbit_progress,-.18+.38*orbit_progress)
        key(satellite,f,"rotation_euler")
        sweep.location.y=.14+2.71*ease(f,141,228)
        key(sweep,f,"location")
        if 117<=f<=278:
            lens_tip=satellite.location+satellite.rotation_euler.to_matrix()@Vector((0,-.661,-.06))
            aim_scan(orbital_scan,f,lens_tip,(.0,sweep.location.y,-.209),2.29,.42)
        if 279<=f<=378:
            sweep_x=-1.08+2.57*ease(f,279,378)
            aim_scan(desert_scan,f,(sweep_x-.27,1.46,4.6),(sweep_x,.60,1.97),.65,.48)
        if f<=116:
            t=ease(f,1,92); insert=ease(f,108,116)
            p=Vector((-.69,-2.26,1.34)).lerp(Vector((.45,-2.34,1.66)),t)
            p=p.lerp(Vector((.42,-1.51,1.42)),insert)
            aim=Vector((.08,.16,1.08)).lerp(Vector((.15,.31,1.07)),t)
            camera_at(camera,f,room,p,aim,26,(-.15,.31,1.23))
        elif f<=278:
            t=orbit_progress
            camera_at(camera,f,space,Vector((-.28,-3.21,1.82)).lerp(Vector((1.05,-2.48,1.59)),t),
                      (.07,.34,1.05),26,(0,.16,1.33))
        elif f<=378:
            t=ease(f,279,342)
            camera_at(camera,f,desert,(.27-.39*t,-3.25-.40*t,2.14-1.03*t),
                      (0,.56,1.56-.48*t),26)
        else:
            t=ease(f,379,391)
            camera_at(camera,f,room,(-.55+.16*t,-2.25+.15*t,1.38),(.05,.20,1.09),26,(-.23,.34,1.24))
        # Keep the outline thickness in the native delivery camera's pixel range.
        for mod in boss.ink_modifiers:
            mod.strength=-k.look.ink_width(max(1.4,abs(camera.location.y)),26,3.)
            key(mod,f,"strength")
    for f,stage,rig in ((501,kportrait,kalam),(502,eportrait,engineer),(503,room,boss),(504,kportrait,kalam)):
        arm=[((-.224,-.105,.280),(-.262,-.027,.254)),((.241,-.196,.376),(.260,-.105,.265))]
        pose_root=Vector((-.31,.49,.033)) if rig==boss else Vector((0,0,0))
        if rig==boss:
            arm[1]=((.279,-.28,.423),(.271,-.173,.325))
        rig.pose(f,pose_root,.19,.12,arm,seated_legs if rig==boss else legs,"rest",head_yaw=-.11)
        k.studio_pose_hands(rig,f)
        if rig==boss:mug_grip(mug,boss,f,pose_root,.19,.12,0)
        camera_at(camera,f,stage,(-.32,-1.65,1.38) if f==503 else (-.30,-1.35,1.4) if f!=504 else (.31,-.85,1.25),
                  (-.10,.32,1.18) if f==503 else (0,0,1.16) if f!=504 else (.13,-.015,1.12),26)
    for start,name in ((1,"Intelligence desk"),(117,"Orbit"),(279,"Illustrated cross section"),(379,"Coffee payoff")):
        scene.timeline_markers.new(name,frame=start)
    for stage,expr in ((room,"(116 < frame < 379) or (frame > 455 and frame != 503)"),
                       (space,"not (117 <= frame <= 278)"),(desert,"not (279 <= frame <= 378)"),
                       (kportrait,"frame != 501 and frame != 504"),(eportrait,"frame != 502")):
        activate(stage,expr)
    for actor in (boss,kalam,engineer):actor.finish_bake()
    for action in bpy.data.actions:
        for curve in action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation="CONSTANT" if "hide_" in curve.data_path or curve.data_path=="lens" else "LINEAR"
    scene.frame_set(1);scene.render.filepath="//frame_"
    bpy.context.preferences.filepaths.save_version=0
    import json
    assert min(d["leg_clearance_behind_panel_m"] for d in contacts.values())>.07
    (OUT/"desk_contacts.json").write_text(json.dumps(contacts,indent=2))
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"pokhran_part1_v01b.blend"))

if __name__=="__main__":
    build()
