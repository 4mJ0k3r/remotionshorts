"""The café-to-midnight chapters of November, with a single global edit clock."""
import json
import math

import bpy
from mathutils import Vector

import ricks_v2_kit as k
from build_scene import camera, glide, move, restrict, shot, smooth, stage
from cast import REST, STAND, figure, key, pose, world_arm
from feature_sets import cafe, door, earth, mug, office, pads, room, safe, satellite, space, street, truck
from sets import ART, box, cylinder, palette, phone, print_on_plane, stroke, text
from timing import BOUNDARIES


def take(a, b, p, q, target, lens=26, *, end=None, focus=None, stop=1.2):
    return ((a, b, p, q, target, target if end is None else end, lens), focus or target, stop)


def actor(col, name, costume=None, supporting=False):
    rig = figure(col, name, "hero" if costume is None else "bro")
    if costume is not None:
        for obj in rig.root.children_recursive:
            if obj.type == "MESH" and ("graphic pill torso" in obj.name or "baseball cap" in obj.name
                                      or "visor" in obj.name or "peak patch" in obj.name):
                obj.data.materials[0] = k.make_cel_character_material(name + " fabric", costume)
            if obj.type == "MESH" and "conformed costume art" in obj.name:
                bpy.data.objects.remove(obj, do_unlink=True)
                continue
            if obj.type == "MESH" and len(obj.data.polygons) >= 230 and (supporting or not len(obj.modifiers)):
                mod = obj.modifiers.new("Background cast mesh budget", "DECIMATE")
                mod.ratio = .43 if supporting else .53
    return rig


def face(col, rig):
    return k.empty("Focus at eye plane", col, (0, -.166, .021), rig.head)


def grip(target, root, side=1, yaw=0, tilt=0):
    return world_arm(target, root, yaw, tilt, (side*.244, -.116, .23))


def seats(width=.205, foot=-.17):
    return tuple(((s*width, -.33, foot), (s*width, -.24, foot+.225)) for s in (-1, 1))


def coffee(col, m):
    cafe(col, m)
    barista = actor(col, "Oak-apron barista", "#865938")
    hero = actor(col, "Hero at the café")
    cup = mug(col, m)
    table = k.empty("Table sliding away from the fabric padding", col, (1.42, -.96, 0))
    cylinder(col, "Round scalloped café tabletop", (0, 0, .63), .346, .080, m["wood"], table, segments=40)
    cylinder(col, "Curved wooden table apron", (0, 0, .553), .300, .088, m["wood"], table, segments=38)
    cylinder(col, "Slim café pedestal", (0, 0, .307), .064, .62, m["metal"], table)
    cylinder(col, "Weighted café table base", (0, 0, .032), .21, .052, m["metal"], table)
    box(col, "Upholstered café chair cushion", (1.25, -.34, .526), (.39, .39, .072), m["turf"], bevel=.035)
    box(col, "Bentwood café chair back", (1.25, -.145, .832), (.39,.052,.343), m["wood"], bevel=.027)
    for x in (1.10,1.40):
        for y in (-.47,-.20):
            box(col,"Thin chair support",(x,y,.243),(.035,.035,.49),m["metal"])
    pads(col, m, .32, (1.25, -.625, .386))
    box(col,"Raised café service platform",(-.28,.79,.055),(1.18,.59,.11),m["wood"])
    hero_face = face(col, hero)
    token = k.empty("Focus at the printed token", col, (0, -.128, .054), cup)

    def action(f, t):
        motion = smooth(t, 25.25, 25.52)
        tabletop = (1.42+.30*motion, -.96-.12*motion, 0)
        move(table, f, tabletop)
        p = glide(t, 22.49, 23.94, (-.23, .255, 1.068), (.13, .056, 1.069))
        if t >= 24.90:
            p = Vector((tabletop[0]-.08, tabletop[1]+.023, .75))
        move(cup, f, p)
        bar = (-.34, .73, .11)
        serve=grip(p+Vector((-.095,.012,.046)),bar) if t<24.9 else REST[1]
        pose(barista, f, bar, "grin", arms=(REST[0],serve))
        root = (2.75, -.34, .12) if t<24.9 else (1.25, -.34, .12)
        aim = glide(t, 25.0, 25.38, (1.34, -.75, .71), (1.58, -.79, .74))
        pose(hero, f, root, "strain" if t > 25.23 else "hope", yaw=.24,
             tilt=.19*motion, arms=(REST[0], grip(aim, root, yaw=.24, tilt=.19*motion) if t>=24.9 else REST[1]),
             legs=seats(.20,-.092))

    return action, (
        take(22.0,24.20,(.18,-1.86,1.48),(.22,-1.41,1.43),(0,.28,1.26),focus=face(col,barista)),
        take(24.20,24.90,(.13,-.61,1.25),(.13,-.55,1.22),(.13,-.08,1.118),49,focus=token,stop=2.8),
        take(24.90,27.70,(.42,-2.30,1.28),(.54,-2.25,1.24),(1.46,-.58,.91),focus=hero_face),
    )


def meeting(col, m):
    office(col,m)
    hero=actor(col,"Hero on the twin yoga balls")
    hr=actor(col,"Purple-blazer HR manager","#9560a8")
    witness=actor(col,"Teal cubicle coworker","#466d74",supporting=True)
    witness2=actor(col,"Rose cubicle coworker","#a65863",supporting=True)
    for x in (-.105,.105):
        stroke(col,"Deep plum rectangular glasses",
               [(x+dx,-.204,z+.017) for dx,z in ((-.074,.049),(.074,.049),(.074,-.04),(-.074,-.04),(-.074,.049))],
               .006,m["ink"],hr.head)
    stroke(col,"Glasses bridge",[(-.052,-.213,-.021),(.052,-.213,-.021)],.009,m["ink"],hr.head)
    pads(col,m,.64,(-.33,.095,.32))
    board=k.empty("HR ergonomic assessment",col)
    box(col,"Walnut clipboard",(0,0,0),(.442,.038,.305),m["wood"],board,bevel=.017)
    box(col,"White ergonomic assessment sheet",(0,-.024,.007),(.403,.012,.27),m["cream"],board)
    box(col,"Small brass clipboard clip",(0,-.036,.14),(.15,.025,.04),m["gold"],board)
    text(col,"ERGONOMIC",(0,-.034,.018),.056,m["ink"],board)
    stroke(col,"Green approval check",[(-.029,-.039,-.058),(-.009,-.040,-.077),(.034,-.040,-.031)],.008,m["turf"],board)
    for z in (-.113,.095):
        stroke(col,"Fine ruled assessment line",[(-.159,-.033,z),(.161,-.033,z)],.006,m["metal"],board)
    board_focus=k.empty("Focus on HR clipboard",col,(0,-.035,.025),board)

    def action(f,t):
        reveal=smooth(t,30.23,30.62)
        relax=smooth(t,31.29,31.64)
        root=(-.45,.115,.110-.022*relax)
        relaxed=((- .36,-.23,.11),(-.27,-.09,.29))
        pose(hero,f,root,"grin",tilt=-.10-.10*relax,sway=-.06-.08*relax,
             legs=seats(.26,.028-root[2]),arms=(relaxed,REST[1]))
        h=(.58,.32,0)
        board_p=(.57,.03,.65+.31*reveal)
        move(board,f,board_p,(-.03,0,-.06))
        pose(hr,f,h,"grin",arms=tuple(grip((board_p[0]+s*.218,.02,board_p[2]-.042),h,s) for s in (-1,1)))
        pose(witness,f,(-1.08,.68,0),"shock",yaw=.40)
        pose(witness2,f,(1.35,.67,0),"shock",yaw=-.36)

    return action, (
        take(27.70,31.00,(-.44,-3.74,1.72),(-.52,-3.44,1.67),(.03,.29,.91),focus=face(col,hero),stop=1.28),
        take(31.00,31.67,(.52,-.92,1.13),(.57,-.79,1.10),(.57,0,.97),37,focus=board_focus,stop=2.55),
        take(31.67,33.50,(1.57,-3.27,1.66),(1.51,-3.02,1.62),(.12,.24,.92),focus=face(col,hero)),
    )


def doorway(col,m):
    door(col,m)
    hero=actor(col,"Hero at the wedged apartment door")
    left=actor(col,"Green sweater neighbor","#709275")
    right=actor(col,"Rose sweater neighbor","#ad6662")
    forms=pads(col,m,2.56,(0,-.41,1.28),spacing=.76)
    for s in (-1,1):
        text(col,str(104 if s<0 else 105),(s*1.37,.341,1.93),.13,m["gold"])

    def action(f,t):
        surge=smooth(t,36.62,36.81)
        land=smooth(t,36.81,37.27)
        y=-.47-.66*surge+.14*land
        z=1.28+.17*surge-.17*land
        move(forms,f,(0,y,z))
        pose(hero,f,(0,y,2.205+.17*surge-.17*land),"shock" if t>36.55 else "strain",
             tilt=-.09+.25*surge, arms=(((-.36,-.08,.30),(-.25,-.09,.21)),((.36,-.08,.31),(.25,-.08,.22))),
             legs=seats(.236,-.06))
        pushing=.084*math.sin((t-33.5)*math.tau*2.0)*(1-surge)
        for s,rig in ((-1,left),(1,right)):
            base=(s*(1.49+.59*surge),-1.98-.26*surge,0)
            yaw=s*-.43
            lean=-.17*(1-surge)+pushing
            hands=[]
            for h in (-1,1):
                x=s*(1.43+.59*surge)+h*.12
                hand_z=.91+.084*pushing
                skin=math.sqrt(max(0,1.28**2-(x-s*.973)**2-(hand_z-z)**2))
                hands.append(grip((x,y-skin-.033+.26*surge,hand_z),base,h,yaw,lean))
            arms=tuple(hands)
            pose(rig,f,base,"strain" if t<36.79 else "shock",yaw=yaw,tilt=lean,arms=arms)

    return action, (
        take(33.50,36.52,(-.21,-7.25,3.18),(-.26,-7.02,3.06),(0,-.40,1.78),focus=(0,-.65,1.86),stop=1.28),
        take(36.52,37.80,(.96,-7.10,3.00),(.82,-7.30,2.96),(0,-.67,1.75),focus=(0,-.76,1.85),stop=1.28),
    )


def rooftop(col,m):
    street(col,m)
    pads(col,m,10.2,(0,.83,5.10),spacing=.82)
    engine,ladder=truck(col,m)
    hero=actor(col,"Hero above three-story apartments")
    fire=actor(col,"Firefighter","#d95245")
    torso=bpy.data.objects["Firefighter | graphic pill torso"]
    torso.data.materials[0]=k.make_cel_character_material("Bright yellow firefighter jacket","#ffd65b")
    for z in (.167,.258):
        stroke(col,"Pale reflective stripe on turnout coat",
               [(-.100,-.057,z),(-.052,-.083,z),(0,-.090,z),(.052,-.083,z),(.100,-.057,z)],
               .012,m["cream"],fire.body)
    bag=k.empty("Paper grocery hand-off",col)
    box(col,"Folded brown grocery bag",(0,0,0),(.25,.193,.315),m["cork"],bag,bevel=.021)
    stroke(col,"Grocery bag loop",[(-.08,-.051,.140),(-.054,-.051,.220),(.047,-.051,.220),(.077,-.051,.140)],
           .014,m["gold"],bag)
    cylinder(col,"Leek stem peeking out",(-.068,.02,.181),.026,.155,m["turf"],bag)
    k.ball("Red apple peeking out",col,(.065,.012,.148),(.06,)*3,m["red"],bag,16,12)

    def action(f,t):
        arrive=smooth(t,39.02,41.10)
        move(engine,f,(10.12+6.5*(1-arrive),-4.19,.005))
        bend=smooth(t,41.22,42.14)
        ladder.rotation_euler.x=-.39*bend
        ladder.rotation_euler.y=-.37*bend
        ladder.scale.z=1.27*smooth(t,41.05,42.14)+.18
        key(ladder,f,"rotation_euler","scale")
        lift=smooth(t,41.36,42.23)
        root=(6.22,-.21,9.13)
        crew=(7.51+2.83*(1-lift),-.48-3.00*(1-lift),9.62-6.5*(1-lift))
        bag_p=glide(t,42.27,42.92,(7.37,-.66,10.47),(6.54,-.55,9.92))
        bag_p+=Vector((2.83,-3.00,-6.5))*(1-lift)
        move(bag,f,bag_p)
        pose(hero,f,root,"hope" if t>42.46 else "deadpan",yaw=.31,legs=seats(.20,-.06),
             arms=(REST[0],grip(bag_p+Vector((-.115,.015,.095)),root,yaw=.31) if t>=42.27 else REST[1]))
        pose(fire,f,crew,"grin",yaw=-.36,
             arms=(grip(bag_p+Vector((.115,.014,.095)),crew,-1,-.36) if t<43.05 else REST[0],REST[1]))

    return action, (
        take(37.80,40.57,(-11.6,-31.9,2.88),(-10.6,-29.7,2.9),(0,2.0,5.45),focus=(0,-.45,4.3)),
        take(40.57,42.20,(12.65,-16.8,3.63),(12.38,-15.3,4.02),(9.30,-2.5,4.50),focus=(9.3,-3,4.3)),
        take(42.20,44.46,(5.62,-3.53,10.90),(5.74,-3.18,10.84),(6.78,-.20,10.30),focus=face(col,hero)),
    )


def lockbox(col,m,ending=False):
    room(col,m,"safe")
    hero=actor(col,"Hero at midnight" if ending else "Hero locking away the phone")
    root,lid,dial=safe(col,m)
    bolt=box(col,"Sliding timer lock bolt",(.177,-.170,.282),(.103,.040,.026),m["gold"],root,bevel=.012)
    prop,_=phone(col,m)
    height=.20 if ending else 0
    box(col,"Thick wood safe table",(0,-.13,.563-height),(1.55,.72,.115),m["wood"],bevel=.049)
    for x in (-.62,.62):
        box(col,"Wood safe-table legs",(x,-.11,.274-height*.5),(.13,.49,.55-height),m["wood"],bevel=.024)
    focus=k.empty("Focus inside glass safe",col,(0,-.08,.16),root)
    victory=None
    if ending:
        victory=print_on_plane(col,"Full-frame phone victory lockscreen","victory.png",(0,-2,1.40),(.61,1.084))
        box(col,"Midnight chair seat",(0,.227,.485),(.435,.354,.063),m["turf"],bevel=.038)
        for x in (-.18,.18):
            box(col,"Midnight chair legs",(x,.235,.23),(.045,.26,.48),m["wood"],bevel=.010)
        bevel=k.emission("Soft burnished midnight brass","#d6aa7d",.93)
        for z in (1.02,1.12,1.42,1.68,2.23,2.36,2.48):
            stroke(col,"Dim warm wall wainscot inlay",[(-3,2.79,z),(3,2.79,z)],.012,bevel)
        for inset in (.00,.04,.08,.12):
            x=.705-inset
            y=.18-inset
            front=-.442+inset
            stroke(col,"Tabletop perimeter cut inlay",[(-x,y,.425),(-x,front,.425),
                   (x,front,.425),(x,y,.425)],.005,bevel)

    def action(f,t):
        close=smooth(t,45.82,46.07)
        open_late=smooth(t,59.12,59.43) if ending else 0
        base=(.043,-.270,.623-height)
        move(root,f,base)
        lid.rotation_euler.x=(-2.42*open_late if ending else -1.43*(1-close))
        dial.rotation_euler.y=-1.93*smooth(t,46.44,46.88)
        latched=1-open_late if ending else smooth(t,47.61,47.76)
        bolt.location.x=.130+.079*latched
        key(bolt,f,"location")
        key(lid,f,"rotation_euler")
        key(dial,f,"rotation_euler")
        raised=smooth(t,45.00,45.58)
        lock_time=smooth(t,45.52,45.83)
        p=Vector((base[0]-.065,base[1],base[2]+.13)) if ending else glide(
            t,45.19,45.80,(.147,-.19,1.205),(base[0]-.065,base[1],base[2]+.13))
        tilt=-math.pi*.5*(1 if ending else lock_time)
        move(prop,f,p,(tilt,0,0),.66)
        floor=(0,.16,0)
        lhs=grip((-.19,-.26,.814-height),floor,-1)
        rhs=grip((.266,-.473,.723-height),floor)
        if not ending and raised<.98:
            rhs=grip(p+Vector((.063,-.006,-.04)),floor)
        elif not ending and t<46.28:
            rhs=grip((.203,-.40,.938+.21*(1-close)),floor)
        pose(hero,f,floor,"deadpan" if ending else "shock",tilt=.055 if ending else -.08,
             head=(0 if ending else .11,0),arms=(lhs,rhs),legs=seats(.17,.028) if ending else STAND,
             sweat=None if ending else smooth(t,44.46,47.74))

    if ending:
        return action, (
            take(56.00,59.15,(.39,-1.89,1.50),(.22,-1.62,1.44),(.00,-.04,1.06),focus=face(col,hero)),
            take(59.15,60.58,(.15,-1.35,.98),(.12,-1.24,.89),(.043,-.25,.66),40,focus=focus,stop=2.4),
            take(60.58,61.78,(0,-3.385,1.40),(0,-3.385,1.40),(0,-2,1.40),45,focus=victory,stop=3.6),
            take(61.78,64.10,(.13,-1.67,1.42),(.08,-1.49,1.36),(0,-.08,1.04),focus=face(col,hero)),
            take(64.10,64.94,(.08,-1.49,1.36),(.08,-1.49,1.36),(0,-.08,1.04),focus=face(col,hero)),
        )
    return action, (
        take(44.46,45.72,(.43,-1.81,1.53),(.26,-1.59,1.47),(.02,-.10,1.03),focus=face(col,hero)),
        take(45.72,46.38,(.19,-1.18,1.17),(.16,-1.12,1.13),(.04,-.25,.82),37,focus=focus,stop=2.9),
        take(46.38,48.84,(.11,-1.29,1.01),(.10,-1.21,.98),(.043,-.34,.78),37,focus=focus,stop=3.2),
    )


def orbit(col,m):
    space(col,m)
    pads(col,m,3.15,(0,.5,.43))
    globe=earth(col,m,(-2.30,-.17,-1.97))
    ship=satellite(col,m)
    hero=actor(col,"Tiny Hero in orbit")
    hero.root.scale=(.25,)*3
    title=k.emission("Bright warm orbit pointer labels","#fbe7bd",1.66)
    text(col,"YOU",(1.93,-.49,2.69),.31,title)
    stroke(col,"Pointer to tiny Hero",[(1.76,-.45,2.58),(1.29,-.45,2.35),(1.06,-.45,2.13)],.016,title)
    text(col,"EARTH",(-.93,-.71,-1.90),.25,title)
    stroke(col,"Pointer to Earth",[(-1.05,-.65,-1.74),(-1.48,-.65,-1.69),(-1.64,-.65,-1.76)],.015,title)

    def action(f,t):
        pose(hero,f,(.98,-.18,1.82),"deadpan",legs=seats())
        sweep=smooth(t,51.42,55.78)
        steer=math.sin(sweep*math.pi)**1.8
        move(ship,f,(4.77-9.81*sweep,-1.37-2.71*steer,2.93-2.42*sweep),
             (.19,-.65*steer,.31+.64*steer),.63)
        globe.rotation_euler.z=.145*(t-48.83)
        key(globe,f,"rotation_euler")

    return action, (
        take(48.83,51.56,(1.78,-11.23,2.44),(.92,-10.47,2.12),(-.36,.27,.23),focus=(0,-.40,.35)),
        take(51.56,54.84,(.60,-10.3,1.70),(-.29,-10.7,1.62),(-.21,.16,.28),focus=(0,-.75,.43)),
        take(54.84,56.00,(-.16,-9.56,1.93),(-.19,-9.19,1.93),(-.30,.18,.74),focus=face(col,hero)),
    )


LAYOUT = {2:(coffee,meeting,doorway), 3:(rooftop,lockbox), 4:(orbit,lambda col,m:lockbox(col,m,True))}
HUD = {2:((22,3),(27.70,4),(33.50,6)),3:((37.80,8),),
       4:((48.83,30),(55.8667,"turn0"),(55.9333,"turn1"),
          (56.0,"turn2"),(56.0667,"turn3"),(56.1333,"december"))}
CHECKS = {
    2:(22.28,23.61,24.47,25.35,26.48,27.96,29.67,31.19,32.39,33.86,36.44,37.31),
    3:(37.86,38.70,39.53,40.87,41.87,42.91,43.69,44.64,45.25,45.94,46.68,48.13),
    4:(48.93,49.52,50.62,51.88,53.33,54.38,55.29,56.58,58.75,59.42,61.08,64.47),
}


def hud(scene,part,frame):
    tree=scene.node_tree
    out=next(n for n in tree.nodes if n.type=="COMPOSITE")
    stream=out.inputs[0].links[0].from_socket
    slots=HUD[part]
    for i,(start,day) in enumerate(slots):
        art=tree.nodes.new("CompositorNodeImage")
        art.image=bpy.data.images.load(str(ART/f"hud_{day}.png"),check_existing=True)
        scale=tree.nodes.new("CompositorNodeScale")
        scale.space="RENDER_SIZE"
        scale.frame_method="STRETCH"
        tree.links.new(art.outputs["Image"],scale.inputs[0])
        over=tree.nodes.new("CompositorNodeAlphaOver")
        tree.links.new(stream,over.inputs[1])
        tree.links.new(scale.outputs[0],over.inputs[2])
        stop=slots[i+1][0] if i+1<len(slots) else 80
        values={1:0,frame(start):1,frame(stop):0}
        if day=="december":
            values.update({frame(60.58):0,frame(61.78):1})
        for f,value in sorted(values.items()):
            over.inputs[0].default_value=value
            over.inputs[0].keyframe_insert("default_value",frame=f)
        stream=over.outputs[0]
    tree.links.new(stream,out.inputs[0])


def build(part,out,path):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene=bpy.context.scene
    start,end=BOUNDARIES[part-1:part+1]
    frame=lambda t:max(1,round(t*30)-start+1)
    k.configure_ricks_scene(scene,frame_end=end-start,samples=6)
    scene.world=bpy.data.worlds.new("Dim cool November world fill")
    scene.world.use_nodes=True
    bg=scene.world.node_tree.nodes["Background"]
    bg.inputs[0].default_value=k.look.rgba("#786b85")
    bg.inputs[1].default_value=.24
    m=palette()
    cuts=[]
    for i,builder in enumerate(LAYOUT[part]):
        label=builder.__name__ if builder.__name__!="<lambda>" else "Midnight"
        col=stage(scene,label.title())
        action,takes=builder(col,m)
        a=frame(takes[0][0][0])
        b=min(scene.frame_end,frame(takes[-1][0][1])-1)
        for j,(span,target,stop) in enumerate(takes):
            f_start=frame(span[0])
            f_end=min(scene.frame_end,frame(span[1])-1)
            if hasattr(target,"type"):
                focus=target
            else:
                focus=k.empty("Locked prop or wide focus",col,target)
            cam=camera(scene,f"{label} take {j+1}",span[-1],focus,stop)
            marker=scene.timeline_markers.new(cam.name,frame=f_start)
            marker.camera=cam
            if scene.camera is None:
                scene.camera=cam
            cuts.append(f_start)
            for f in range(f_start,f_end+1):
                t=(start+f-1)/30
                shot(cam,f,t,span,i*90)
        for f in range(a,b+1):
            action(f,(start+f-1)/30)
        for obj in tuple(col.objects):
            if obj.type=="EMPTY" and obj.name.startswith("Hero ") and obj.parent is None:
                head=next((child for child in obj.children_recursive if child.name.endswith(" | head control")),None)
                if head:
                    k.setup_hero_portrait_lighting(head,bg_dim=.68)
        restrict(col,a,b,i*90)
    k.setup_ricks_compositor(scene,camera=scene.camera)
    hud(scene,part,frame)
    if scene.node_tree.animation_data:
        for track in scene.node_tree.animation_data.action.fcurves:
            for point in track.keyframe_points:
                point.interpolation="CONSTANT"
    for action in bpy.data.actions:
        if action==scene.node_tree.animation_data.action:
            continue
        for track in action.fcurves:
            discrete="hide_" in track.data_path or track.data_path=="lens"
            for point in track.keyframe_points:
                point.interpolation="CONSTANT" if discrete else "LINEAR"
    scene.frame_set(1)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    (out/"shots.json").write_text(json.dumps({"cuts":[f-1 for f in cuts[1:]],"proof_frames":[frame(t) for t in CHECKS[part]]},indent=2))
