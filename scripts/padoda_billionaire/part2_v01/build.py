"""Build and bake the approved-format childhood sequence for stills review."""
import json
import math
from pathlib import Path
import sys

import bpy
from mathutils import Euler, Vector

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/padoda_billionaire/part2_v01"
sys.path[:0]=[str(HERE),str(ROOT/"scripts"),str(ROOT/"scripts/bb_shark_slipper_reel/v01d")]
import ricks_v2_kit as k
from bedroom import BED_TOP, bedroom

END=json.loads((OUT/"audio_cut.json").read_text())["frames"]
CAL=(10,72,134,168,192,212,235,272)
BENCH=(*CAL,1,151,181,262)


def ease(f,a,b):
    return k.look.ease5((f-a)/(b-a))


def lerp(a,b,t):
    return Vector(a).lerp(Vector(b),t)


def key(obj,frame,*properties):
    for prop in properties:
        obj.keyframe_insert(prop,frame=frame)


def haze(name,color,energy,opacity):
    material=k.emission(name,color,energy)
    material.surface_render_method="BLENDED"
    material.use_transparency_overlap=False
    nodes,links=material.node_tree.nodes,material.node_tree.links
    output=next(n for n in nodes if n.type=="OUTPUT_MATERIAL")
    glow=next(n for n in nodes if n.type=="EMISSION")
    angle=nodes.new("ShaderNodeLayerWeight")
    ramp=nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color=(opacity,opacity,opacity,1)
    ramp.color_ramp.elements[1].color=(0,0,0,1)
    ramp.color_ramp.interpolation="EASE"
    mix=nodes.new("ShaderNodeMixShader")
    links.new(angle.outputs["Facing"],ramp.inputs[0])
    links.new(ramp.outputs[0],mix.inputs[0])
    links.new(nodes.new("ShaderNodeBsdfTransparent").outputs[0],mix.inputs[1])
    links.new(glow.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs[0])
    return material


def insect(c,index,mats):
    slate,ink,ivory,rose,wingmat=mats
    root=k.empty(f"Mosquito {index+1}",c)
    def globe(label,place,scale,mat):
        return k.ball(label,c,place,scale,mat,root,segments=16,rings=10)
    for label,place,scale in (("Slate abdomen",(0,.078,-.033),(.084,.14,.072)),
                              ("Slate face",(0,-.023,.021),(.096,.083,.082))):
        obj=globe(label,place,scale,slate)
        k.apply_character_ink(obj,c)
    k.tube("Pointed proboscis",c,[(0,-.074,-.019),(0,-.165,-.034),(0,-.24,-.054)],.009,ink,root)
    wings=[]
    for sign in (-1,1):
        for j in range(3):
            x=sign*(.075+.022*(j==1))
            k.tube("Bent stick mosquito leg",c,[(sign*.047,-.005+j*.057,-.043),
                   (x*1.48,-.07+j*.085,-.114),(x*1.79,-.094+j*.104,-.15)],.0045,ink,root)
        joint=k.empty("Fluttering wing pivot",c,(sign*.047,.053,.046),root)
        wing=k.ball("Translucent comic wing",c,(sign*.092,.041,.008),(.127,.045,.011),wingmat,joint,
                    segments=14,rings=9)
        wing.rotation_euler.z=sign*.17
        wings.append(joint)
    faces=[]
    for state in ("annoying_smirk","gas_shock_O","fainted_XX"):
        face=k.empty(state,c,parent=root)
        faces.append(face)
        for sign in (-1,1):
            x=sign*.047
            wide=state=="gas_shock_O"
            for radius,y,material in ((.047,-.102,ink),(.039,-.113,ivory)):
                k.ball("Round 2D eye",c,(x,y,.034),(radius,.010,radius*(1 if wide else .88)),material,
                       face,segments=16,rings=8)
            if state=="fainted_XX":
                for slope in (-1,1):
                    k.tube("Marker X eye",c,[(x-.021,-.125,.034-slope*.018),(x+.021,-.125,.034+slope*.018)],
                           .005,ink,face)
            else:
                k.ball("Pupil",c,(x+(.009 if not wide else 0),-.126,.034),(.011,.005,.014),ink,face,
                       segments=12,rings=8)
            if state=="annoying_smirk":
                k.tube("Mosquito cocked brow",c,[(x-.028,-.12,.078),(x,-.12,.09),(x+.028,-.12,.081)],.005,ink,face)
        if state=="gas_shock_O":
            k.ball("Tiny O gasp",c,(0,-.105,-.027),(.019,.008,.019),ink,face,segments=12,rings=8)
        elif state=="fainted_XX":
            k.ball("Sideways pink tongue",c,(.034,-.112,-.038),(.029,.009,.016),rose,face,segments=12,rings=8)
        else:
            k.tube("Cocky mosquito smirk",c,[(-.027,-.103,-.021),(0,-.113,-.028),(.026,-.103,-.015)],.005,ink,face)
    return root,wings,faces


def build():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    k.configure_ricks_scene(scene,frame_end=END,samples=6)
    scene.render.image_settings.file_format="PNG"
    scene.render.image_settings.compression=0
    scene.world=bpy.data.worlds.new("Childhood indigo air")
    scene.world.use_nodes=True
    bg=next(n for n in scene.world.node_tree.nodes if n.type=="BACKGROUND")
    bg.inputs[0].default_value=k.look.rgba("#202e58")
    bg.inputs[1].default_value=.27
    c=bpy.data.collections.new("Childhood bedroom and mosquito cast")
    scene.collection.children.link(c)
    mattress,curtains,spill=bedroom(c)
    assets=HERE/"art"
    names=[*(f"kid_annoyed_track_{i}" for i in range(5)),"kid_mischievous","kid_intense_strain","kid_smug_shrug"]
    saved_ring=k.RING
    k.RING=28
    rig=k.build_ricks_character("Kid-Hero",c,costume_image=assets/"striped_tee.png",
                 expression_images={name:assets/(name+".png") for name in names},face_shadow="#9EB2D6")
    k.RING=saved_ring
    rig.root.scale=(.82,)*3
    rig.head.scale=(1.14,)*3
    rig.head.location.z-=.025
    torso=bpy.data.objects["Kid-Hero | graphic pill torso"]
    torso.data.materials[0]=k.make_cel_character_material("Teal striped tee backing","#238C9E")
    lengths=rig.measure_leg_lengths()
    mats=(k.make_cel_character_material("Mosquito two-step smoke slate","#364560"),
          k.emission("Mosquito ink","#070911"),k.emission("Round cream mosquito eyes","#fff9f0",1.33),
          k.emission("Tiny coral tongue","#e78197"),haze("Translucent white wings","#dcecff",1.15,.66))
    insects=[insect(c,i,mats) for i in range(4)]
    gas=haze("Wispy translucent neon-lime gas","#6BFF4E",1.60,.49)
    wisps=[k.ball("Lime translucent wisp",c,(0,0,0),(.28,.13,.12),gas,segments=18,rings=12) for _ in range(5)]
    lime=k.emission("Bent chartreuse motion strokes","#adf84b",1.6)
    waves=[k.tube("Wavy comic stink line",c,[(i*.047,.025*math.sin(i*.61),.029*math.sin(i*.73))
              for i in range(14)],.009,lime) for _ in range(3)]
    ochre=haze("Small warm dust puff","#d39b63",1.05,.49)
    dust=[k.ball("Small impact dust lobe",c,(0,0,0),(.054,.037,.034),ochre,segments=12,rings=8) for _ in range(8)]
    starink=k.emission("Pale gold dizzy stars","#ffd172",1.8)
    stars=[k.mesh("Impact star",c,[(math.sin(i*math.tau/10)*(.037 if i%2==0 else .015),0,
                math.cos(i*math.tau/10)*(.037 if i%2==0 else .015)) for i in range(10)],
                [tuple(range(10))],starink) for _ in range(4)]
    camera=k.put(bpy.data.objects.new("Part 2 delivery camera",bpy.data.cameras.new("Vertical lens")),c)
    scene.camera=camera
    k.setup_ricks_compositor(scene,camera=camera,portal_flash_keys=((1,0),(END,0)))
    camera.data.dof.aperture_fstop=2.85
    ring=k.tube("Soft amber story ring",c,[(.53*math.cos(i*math.tau/48),0,.53*math.sin(i*math.tau/48))
             for i in range(49)],.007,k.emission("Nostalgic gold ring","#ffb655",1.3))
    ring_strength=next(n for n in ring.data.materials[0].node_tree.nodes if n.type=="EMISSION").inputs["Strength"]
    base_y=.024
    palm_errors=[]
    last_face=None
    for f in range(1,END+1):
        swat=ease(f,17,22)*(1-ease(f,24,32))
        shift=ease(f,4,20)*(1-ease(f,24,42))
        brace=ease(f,36,63)*(1-ease(f,138,154))
        strain=ease(f,87,115)*(1-ease(f,126,147))
        burst=ease(f,117,123)*(1-ease(f,125,138))
        shrug=ease(f,240,259)
        seat=Vector((-.15+.069*shift,base_y,BED_TOP+.016-.032*strain))
        pitch=.07+.09*shift+.17*strain-.22*burst+.195*shrug
        roll=.09*shift-.083*swat+.04*shrug
        yaw=.03+.13*ease(f,8,31)+.20*ease(f,85,99)-.27*ease(f,145,155)
        bounce=-.28
        body=Euler((pitch,roll,0)).to_matrix()
        basis=Euler((0,0,yaw)).to_matrix()
        root=seat-.82*(basis@(body@Vector((0,0,.07))+Vector((0,0,.59+bounce))))
        head_yaw=-.28+.55*ease(f,4,24)-.19*ease(f,30,63)-.19*shrug
        head_tilt=-.04+.13*strain-.13*burst-.09*shrug
        limbs=[]
        for sign in (-1,1):
            arm=Vector((sign*.188,-.14,.17))
            elbow=Vector((sign*.23,-.087,.24))
            if sign==1:
                arm=arm.lerp(Vector((.37,-.30,.59)),swat)
            contact=Vector((seat.x+sign*.257,.090,BED_TOP-.027*strain+.011))
            local=body.transposed()@(basis.transposed()@((contact-root)/.82)-Vector((0,0,.59+bounce)))
            local-=(local-elbow).normalized()*.016
            arm=arm.lerp(local,brace).lerp(Vector((sign*.33,-.12,.36+.052*(sign==1))),shrug)
            limbs.append((arm,elbow))
        ankles=[]
        for sign in (-1,1):
            ankle=basis.transposed()@((Vector((-.15+sign*.130,-.205,.162))-root)/.82)
            ankles.append((ankle,ankle.lerp(Vector((sign*.146,-.58,.23)),.61)))
        face=(f"kid_annoyed_track_{min(4,(f-1)//6)}" if f<=28 else
              "kid_intense_strain" if 87<=f<=143 else "kid_smug_shrug" if f>=245 else "kid_mischievous")
        rig.body.rotation_euler.y=roll
        rig.pose(f,root,yaw,pitch,limbs,ankles,face if face!=last_face else None,bounce=bounce,
                 head_tilt=head_tilt,head_yaw=head_yaw,leg_lengths=lengths,sweat=strain if 94<=f<=138 else None)
        last_face=face
        if f in (66,105,116):
            for sign,(arm,elbow) in zip((-1,1),limbs):
                tip=arm+(arm-elbow).normalized()*.016
                point=root+.82*(basis@(body@tip+Vector((0,0,.59+bounce))))
                palm_errors.append(abs(point.z-(BED_TOP-.027*strain+.011)))
        mattress.scale.z=1-.32*strain
        mattress.location.z=.475-.008*strain
        key(mattress,f,"location","scale")
        # The mattress ink hull inherits its compression from the mattress.
        spill.data.energy=148*ease(f,119,132)*(1-.80*ease(f,146,250))
        key(spill.data,f,"energy")
        for i, curtain in enumerate(curtains):
            curtain.location.y=.017*math.sin(f*.082+i*1.3)
            key(curtain,f,"location")
        for i,(bug,wings,faces) in enumerate(insects):
            x=(-.255,-.012,.225,.388)[i]
            flutter=.037*math.sin(f*.27+i*1.77)
            if i==0 and f<151:
                fly=ease(f,3,23)
                position=Vector((-.49+.94*fly+.09*math.sin(f*.14)*ease(f,24,39),-.20-.14*swat,
                                 1.178+.071*math.sin(f*.26)+.097*swat))
            else:
                position=Vector((x+flutter,-.59+.08*(i%2)+.04*math.sin(f*.24+i),
                                 1.57+.105*(i%2)+.042*math.sin(f*.21+i)+.015*(i>=2)))
                if f<151:
                    position.y+=.69*(1-ease(f,127,150))
                    position.x+=(.29 if i%2 else -.26)*(1-ease(f,128,150))
                if 151<=f<197 and i>=2:
                    position.x+=.34
                    position.y+=.30
            if i==0 and 133<=f<151:
                position=position.lerp(Vector((x,-.59,1.57)),ease(f,133,149))
            fall_start=197+i
            hit=(226,231,235,235)[i]
            progress=max(0,min(1,(f-fall_start)/(hit-fall_start)))
            dropped=progress**1.55
            floor=Vector((x*1.58-.034,-.87+.095*i,.088))
            if f>=fall_start:
                # Start the fall from a fixed hover point and settle exactly on the floor.
                position=Vector((x,-.59+.08*(i%2),1.57+.105*(i%2))).lerp(floor,dropped)
                position.x+=math.sin(progress*math.tau*1.45+i)*.10*math.sin(math.pi*progress)
                position.z+=.051*math.sin(math.pi*ease(f,hit,hit+6))
            bug.location=position
            tip=ease(f,180+i,193+i)
            bug.rotation_euler=(.09*math.sin(f*.27+i)*(1-tip),
                                math.pi*tip+math.tau*progress,
                                .13*math.sin(f*.16+i)*(1-progress)+.11*i)
            bug.scale=((.94 if i<2 else .69),)*3
            key(bug,f,"location","rotation_euler","scale")
            state=0 if f<164+i else 1 if f<181+i else 2
            for j,parent in enumerate(faces):
                for obj in parent.children:
                    obj.hide_render=obj.hide_viewport=j!=state
                    key(obj,f,"hide_render","hide_viewport")
            for sign,wing in zip((-1,1),wings):
                wing.rotation_euler.y=(1-tip)*.86*math.sin(f*2.11+i)*sign+.39*tip*sign
                key(wing,f,"rotation_euler")
            star=stars[i]
            impact=ease(f,hit,hit+2)*(1-ease(f,hit+4,hit+11))
            star.location=floor+Vector((.072+.081*impact,-.068,.119+.073*impact))
            star.rotation_euler.y=.23*f
            star.scale=(max(.001,impact),)*3
            key(star,f,"location","rotation_euler","scale")
            for j in range(2):
                puff=dust[i*2+j]
                puff.location=floor+Vector(((-1 if j else 1)*(.089+.09*impact),-.041,.038+.029*impact))
                puff.scale=(max(.001,impact),)*3
                key(puff,f,"location","scale")
        for i,wisp in enumerate(wisps):
            u=ease(f,118,147)
            v=ease(f,151,178)
            wisp.location=(-.41+1.4*u+.21*math.sin(i*1.6),.42-.96*u+.15*math.sin(i*2.1),
                           .59+.56*u+.14*math.cos(i*1.4))
            if f>=151:
                wisp.location=(-.67+1.31*v+.09*i,-.42-.023*i,1.58+.10*math.sin(i*1.5))
            wisp.scale=((.4+1.18*u)*(1.40 if f>=151 else 1),.81,.55+.48*u)
            wisp.rotation_euler.y=.33*math.cos(i*1.45)+.11
            wisp.hide_render=wisp.hide_viewport=not 119<=f<=183
            key(wisp,f,"location","scale","rotation_euler","hide_render","hide_viewport")
        for i,wave in enumerate(waves):
            wave.location=(-.25+1.12*ease(f,123,151),-.03+.14*i,.73+.096*i+.31*ease(f,120,150))
            wave.rotation_euler.y=-.25+.14*i
            wave.hide_render=wave.hide_viewport=not 124+i<=f<=148+i
            key(wave,f,"location","rotation_euler","hide_render","hide_viewport")
        if f<=84:
            t=ease(f,1,84)
            p=lerp((-.13,-3.48,1.17),(-.10,-3.18,1.13),t)
            aim=Vector((.018,.24,.94));focus=Vector((-.13,.05,1.13));lens=38
        elif f<=150:
            t=ease(f,85,150)
            shake=.042*math.sin(f*2.9)*(1-ease(f,123,126)) if f>=121 else 0
            p=lerp((1.46,-3.13,.99),(1.24,-2.80,1),t)+Vector((shake,0,shake*.42))
            aim=Vector((.03,.38,.93));focus=Vector((-.12,.00,1.10));lens=36
        elif f<=198:
            t=ease(f,151,198)
            p=lerp((-.16,-1.99,1.44),(-.13,-2.04,1.45),t)
            aim=Vector((-.132,-.53,1.65));focus=Vector((-.13,-.53,1.61));lens=55
        elif f<=237:
            t=ease(f,199,231)
            p=lerp((-.45,-2.75,1.34),(-.4,-2.94,.68),t)
            aim=lerp((-.063,-.63,1.37),(-.127,-.84,.29),t)
            focus=aim.copy();lens=36
        else:
            t=ease(f,238,264)
            p=lerp((1.43,-3.16,1.16),(1.32,-2.97,1.11),t)
            aim=Vector((-.118,.13,.70));focus=Vector((-.10,.04,1.08));lens=34
        forward=(aim-p).normalized()
        facing=forward.to_track_quat("-Z","Y")
        camera.location=p
        camera.rotation_mode="QUATERNION"
        camera.rotation_quaternion=facing
        camera.data.lens=lens
        camera.data.dof.focus_distance=(focus-p).dot(forward)
        key(camera,f,"location","rotation_quaternion")
        key(camera.data,f,"lens","dof.focus_distance")
        if f<=3:
            ring.location=p+forward*1.68
            ring.rotation_mode="QUATERNION"
            ring.rotation_quaternion=facing@Euler((math.pi/2,0,0)).to_quaternion()
            ring_strength.default_value=(1.25,.52,0)[f-1]
            key(ring_strength,f,"default_value")
        ring.hide_render=ring.hide_viewport=f>2
        key(ring,f,"hide_render","hide_viewport")
        for hull in rig.ink_modifiers:
            hull.strength=-min(.013,k.look.ink_width((focus-p).length,lens,3))
            key(hull,f,"strength")
    rig.finish_bake()
    for action in bpy.data.actions:
        for curve in action.fcurves:
            for entry in curve.keyframe_points:
                entry.interpolation="CONSTANT" if curve.data_path.startswith("hide_") else "LINEAR"
    for f,label in ((1,"Amber childhood handoff"),(22,"Swat misses"),(65,"Palms planted"),(85,"Three-quarter brace"),
                    (123,"Lime eruption"),(151,"Mosquito macro"),(168,"Shock"),(186,"Faint"),
                    (199,"Downward track"),(226,"First plop"),(238,"Storyteller shrug")):
        scene.timeline_markers.new(label,frame=f)
    (OUT/"contact_check.json").write_text(json.dumps({"standing_leg_lengths":lengths,
                                                     "palm_vertical_errors_m":palm_errors},indent=2))
    scene.frame_set(1)
    scene.render.filepath="//frame_"
    bpy.context.preferences.filepaths.save_version=0
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/"padoda_part2_v01.blend"))


if __name__=="__main__":
    build()
