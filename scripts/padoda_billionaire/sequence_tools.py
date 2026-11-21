"""Shared staging, illustration and geometry for the remaining modular parts."""
import math
from pathlib import Path
import sys

import bpy
from mathutils import Euler, Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(ROOT/"scripts"),str(ROOT/"scripts/bb_shark_slipper_reel/v01d")]
import ricks_v2_kit as k
from courtyard import box, tapered_between as rod

ART=Path(__file__).parent/"v04/art"

def step(f,a,b):
    return k.look.ease5((f-a)/(b-a))

def vec(value):
    return Vector(value)

def key(obj,f,*props):
    for prop in props:
        obj.keyframe_insert(prop,frame=f)

def collection(scene,name,offset=0):
    c=bpy.data.collections.new(name)
    scene.collection.children.link(c)
    return c,offset

def stage(group,first,last):
    c,offset=group
    root=k.empty(c.name+" placement",c)
    for obj in tuple(c.objects):
        if obj!=root and obj.parent is None:
            obj.parent=root
    root.location.x=offset
    for obj in c.objects:
        if obj==root:
            continue
        for prop in ("hide_render","hide_viewport"):
            action=obj.animation_data.action if obj.animation_data else None
            track=action.fcurves.find(prop) if action else None
            driver=obj.driver_add(prop).driver
            driver.expression=f"frame < {first} or frame > {last}"
            if track:
                channel="pose_"+prop
                obj[channel]=bool(getattr(obj,prop))
                track.data_path=f'["{channel}"]'
                variable=driver.variables.new()
                variable.name="hidden"
                variable.type="SINGLE_PROP"
                variable.targets[0].id=obj
                variable.targets[0].data_path=track.data_path
                driver.expression+=" or hidden > .5"

def visible(obj,value,f):
    obj.hide_render=obj.hide_viewport=not value
    key(obj,f,"hide_render","hide_viewport")

def scene_setup(end,flash):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    s=bpy.context.scene
    k.configure_ricks_scene(s,frame_end=end,samples=5)
    s.render.image_settings.file_format="PNG"
    s.render.image_settings.compression=0
    s.world=bpy.data.worlds.new("Low indigo ambient")
    s.world.use_nodes=True
    bg=next(n for n in s.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#172344")
    bg.inputs[1].default_value=.30
    camera=bpy.data.objects.new("Native delivery camera",bpy.data.cameras.new("Portrait lens"))
    s.collection.objects.link(camera)
    s.camera=camera
    k.setup_ricks_compositor(s,camera=camera,portal_flash_keys=flash)
    return s,camera

def camera_pose(camera,group,f,p,aim,lens,focus=None):
    p,aim=vec(p),vec(aim)
    direction=(aim-p).normalized()
    camera.location=p+vec((group[1],0,0))
    camera.rotation_mode="QUATERNION"
    camera.rotation_quaternion=direction.to_track_quat("-Z","Y")
    camera.data.lens=lens
    camera.data.dof.focus_distance=max(.12,(vec(focus if focus is not None else aim)-p).dot(direction))
    key(camera,f,"location","rotation_quaternion")
    key(camera.data,f,"lens","dof.focus_distance")

def finish(scene,output,actors):
    for actor in actors:
        actor.finish_bake()
    for action in bpy.data.actions:
        for curve in action.fcurves:
            for item in curve.keyframe_points:
                item.interpolation=("CONSTANT" if curve.data_path.startswith(("hide_",'["pose_hide_'))
                                    else "LINEAR")
    scene.frame_set(1)
    scene.render.filepath="//frame_"
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(output))

def actor(c,name="Hero",expressions=None,costume=None,base="#238C9E"):
    default={"smug":ART/"smug.png","strain":ART/"strain.png","speak":ART/"story.png",
             "wink":ART/"wink.png","shock":ART/"pop.png"}
    count=k.RING
    k.RING=28
    try:
        rig=k.build_ricks_character(name,c,costume_image=costume or ART/"outfit.png",
            expression_images=expressions or default)
    finally:
        k.RING=count
    torso=bpy.data.objects[name+" | graphic pill torso"]
    torso.data.materials[0]=k.make_cel_character_material(name+" graphic shirt",base)
    return rig

def floor_legs():
    return [((s*.145,-.055,.027),(s*.14,-.13,.31)) for s in (-1,1)]

def idle():
    return [(vec((s*.196,-.108,.145)),vec((s*.255,-.04,.235))) for s in (-1,1)]

def contact(target,root,yaw,tilt,bounce,elbow,roll=0):
    basis=Euler((0,0,yaw)).to_matrix()@Euler((tilt,roll,0)).to_matrix()
    local=basis.transposed()@(vec(target)-vec(root)-vec((0,0,.59+bounce)))
    return local-(local-elbow).normalized()*.016

def measure_contact(arm, root, yaw, tilt, bounce, target, roll=0):
    hand, elbow=arm
    tip=hand+(hand-elbow).normalized()*.016
    basis=Euler((0,0,yaw)).to_matrix()@Euler((tilt,roll,0)).to_matrix()
    return (vec(root)+vec((0,0,.59+bounce))+basis@tip-vec(target)).length

def disk(name,c,xyz,radius,depth,material,parent=None):
    part=k.cylinder(name,c,xyz,radius,depth,material,parent,length_segments=40)
    part.rotation_euler.x=math.pi/2
    return part

def text(c,value,point,size,material,parent=None):
    data=bpy.data.curves.new(value,"FONT")
    data.body=value
    data.align_x="CENTER"
    data.size=size
    data.extrude=.001
    obj=k.put(bpy.data.objects.new(value,data),c,parent,material)
    obj.location=point
    obj.rotation_euler.x=math.pi/2
    return obj

def ring(name,c,center,radius,material,tube=.01):
    return k.tube(name,c,[vec(center)+vec((radius*math.cos(j*math.tau/48),0,radius*math.sin(j*math.tau/48)))
                         for j in range(49)],tube,material)

def transparent(name,color,opacity,glow=1):
    mat=k.emission(name,color,glow)
    mat.surface_render_method="BLENDED"
    mat.use_transparency_overlap=False
    n,l=mat.node_tree.nodes,mat.node_tree.links
    emiss=next(node for node in n if node.type=="EMISSION")
    out=next(node for node in n if node.type=="OUTPUT_MATERIAL")
    facing=n.new("ShaderNodeLayerWeight")
    ramp=n.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color=(opacity,opacity,opacity,1)
    ramp.color_ramp.elements[1].color=(0,0,0,1)
    ramp.color_ramp.interpolation="EASE"
    mix=n.new("ShaderNodeMixShader")
    l.new(facing.outputs["Facing"],ramp.inputs[0])
    l.new(ramp.outputs[0],mix.inputs[0])
    l.new(n.new("ShaderNodeBsdfTransparent").outputs[0],mix.inputs[1])
    l.new(emiss.outputs[0],mix.inputs[2])
    l.new(mix.outputs[0],out.inputs[0])
    return mat

def sparks(c,count,color="#FFD36D"):
    mat=k.emission("Sharp drawn sparks",color,2.8)
    return [k.ball("Transient spark fleck",c,(0,0,0),(.027,.014,.010),mat,segments=8,rings=5)
            for _ in range(count)]

def scatter(objects,f,center,progress,strength=1):
    center=vec(center)
    for i,obj in enumerate(objects):
        a=i*math.tau/len(objects)+.24
        radius=(.045+progress*(.19+.035*(i%4)))*strength
        obj.location=center+vec((math.cos(a)*radius,-.02-.15*progress,math.sin(a)*radius))
        obj.rotation_euler.y=-a
        obj.scale=(max(.01,1-progress),)*3
        key(obj,f,"location","rotation_euler","scale")
        visible(obj,0<progress<1,f)

def room(c,workshop=True):
    wood=k.texture("Satin maple",("#37232c","#80513e","#ae774d"),"wood",(.70,.81))
    wall=k.texture("Navy workshop plaster",("#131C38","#202e50","#3a4664"),"plaster",(.71,.84))
    honey=k.surface("Warm brass fittings","#a66d3e",.72)
    dark=k.surface("Dark iron fittings","#273247",.74)
    blue=k.surface("Blueprint cobalt","#345781",.82)
    white=k.emission("Blueprint graphic ink","#9ccbe3",.58)
    box("Warm timber floorboards",c,(0,0,-.13),(9,9,.25),wood)
    box("Indigo plaster behind set",c,(0,2.44,2.35),(9,.18,4.9),wall)
    box("Maple skirting",c,(0,2.31,.10),(9,.09,.19),wood,.018,True)
    for i in range(17):
        box("Floorboards seam",c,(-4+i*.49,0,.002),(.011,8,.004),wall,0)
    box("Heavy workbench",c,(.75 if workshop else .44,1.29,.64),(2.41,.63,.14),wood,.039,True)
    for x in (-.15,1.76):
        box("Maple bench support",c,(x,1.41,.32),(.10,.10,.62),wood,.026,True)
    for i,x in enumerate((-.75,-.08,.61,1.27)):
        box("Workshop pinned blueprint",c,(x,2.323,1.68+.12*(i%2)),(.45,.02,.64),blue,.008,True)
        for j in range(5):
            z=1.48+.078*j+.12*(i%2)
            k.tube("Drafting schematic",c,[(x-.15,2.306,z),(x+.11,2.306,z),
                       (x+.16,2.306,z+.045)],.004,white)
        disk("Push pin",c,(x,2.30,1.971+.12*(i%2)),.023,.020,honey)
    box("Clutter shelf",c,(0,2.19,1.09),(3.2,.31,.088),wood,.025,True)
    colors=[k.surface("Workshop jar and book inks",color,.79) for color in
            ("#985648","#49807f","#94844e","#69547f")]
    for i in range(13):
        x=-1.51+.23*i
        if i%3:
            box("Shop books tins and crates",c,(x,2.10,1.22),(.146,.18,.23+.03*(i%4)),colors[i%4],.019)
        else:
            k.cylinder("Bench part canister",c,(x,2.10,1.23),.084,.24,colors[i%4],length_segments=12)
    for j in range(9):
        x=-.84+.16*j
        obj=box("Hanging workshop wrench silhouette",c,(x,2.286,1.345),(.037,.025,.19),dark,.011)
        obj.rotation_euler.y=.19*math.sin(j)
        disk("Wrench spanner loop",c,(x,2.28,1.399),.035,.018,honey)
    glow=k.emission("Amber shop practical","#ffc271",3.1)
    for x in (-1.11,1.49):
        k.cylinder("Hanging workshop lamp",c,(x,.75,2.66),.228,.26,honey,r2=.102)
        k.cylinder("Diffuse amber fixture",c,(x,.75,2.521),.198,.025,glow)
        k.make_light_cone("Amber workshop cone",c,(x,.75,2.51),(x+.09,.55,.71),.13,.66,"#FFC379")
    k.make_ricks_light("Amber practical key",c,(-1.22,-.85,2.51),(0,.15,1.22),"#FFB161",192,1.22)
    k.make_ricks_light("Cool painted fill",c,(1.72,-1.29,2.45),(0,.55,1.20),"#8caaff",167,1.38)
    return wood,honey,dark
