"""Build and bake the standalone 300-frame Blender scene. Run under the GPU lock."""
import math
import sys
from pathlib import Path
from random import Random

import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "renders/ricks_benchmark_10s/v01"
sys.path[:0] = [str(HERE), str(ROOT / "scripts")]

import ricks_lookdev as look
from cast import Actor, FACE_CENTER
from model import aim, artwork, ball, box, emission, empty, light, mesh, outline
from sets import alley, apartment

OFFSET = 34.
FRAMES = 300
# Initial splash and return use close, consistent camera axes around frame 130.
HERO_A = (.13,.57,0)
HERO_B_X = -.31
BROKER_B = (OFFSET+.19,3.22,0)


def smooth(value):
    return look.ease5(value)


def ramp(f, a, b):
    return smooth((f-a)/(b-a))


def lerp(a, b, t):
    return a+(b-a)*t


def vec(a, b, t):
    return Vector(a).lerp(Vector(b),t)


def pop(f, start, length=5):
    return ramp(f,start,start+length-1)*1.08-.08*ramp(f,start+length-1,start+length+3)


def interpolate(frame, keys):
    for (a, av), (b, bv) in zip(keys, keys[1:]):
        if frame <= b:
            return vec(av,bv,ramp(frame,a,b))
    return Vector(keys[-1][1])


def collection(name, parent):
    c = bpy.data.collections.new(name)
    parent.children.link(c)
    return c


def set_visibility_from_scene(collection, initial):
    # Expression curves are individually animated; the collection gates their
    # render and viewport presence via separate, per-object visibility drivers.
    for obj in collection.all_objects:
        for channel in ("hide_render","hide_viewport"):
            active = obj.animation_data and obj.animation_data.action
            if active and active.fcurves.find(channel):
                prop = "local_" + channel
                obj[prop] = False
                curve = active.fcurves.find(channel)
                curve.data_path = f'["{prop}"]'
            else:
                prop = None
            driver = obj.driver_add(channel).driver
            offstage = "frame >= 130" if initial else "frame < 130"
            driver.expression = offstage
            if prop:
                v = driver.variables.new()
                v.name = "hidden"
                v.type = "SINGLE_PROP"
                v.targets[0].id = obj
                v.targets[0].data_path = f'["{prop}"]'
                driver.expression = offstage + " or hidden > 0.5"


def post(scene):
    scene.use_nodes = True
    n, l = scene.node_tree.nodes, scene.node_tree.links
    n.clear()
    source, output = n.new("CompositorNodeRLayers"), n.new("CompositorNodeComposite")
    glow = n.new("CompositorNodeGlare")
    glow.glare_type, glow.quality, glow.threshold, glow.size, glow.mix = "FOG_GLOW","LOW",.9,7,1
    l.new(source.outputs["Image"],glow.inputs[0])
    add = n.new("CompositorNodeMixRGB")
    add.blend_type, add.inputs[0].default_value = "ADD", .30
    l.new(source.outputs["Image"],add.inputs[1])
    l.new(glow.outputs[0],add.inputs[2])
    # A packed radial mask gives the same soft falloff without computing
    # a large Gaussian blur on every 1080x1920 compositing pass.
    size = 128
    image = bpy.data.images.new("Vignette | radial 20 percent",size,size)
    image.colorspace_settings.name = "Non-Color"
    pixels = []
    for y in range(size):
        for x in range(size):
            radius = math.hypot((2*x+1)/size-1,(2*y+1)/size-1)
            value = 1-.20*smooth((radius-.29)/1.09)
            pixels.extend((value,value,value,1.))
    image.pixels.foreach_set(pixels)
    image.pack()
    mask = n.new("CompositorNodeImage")
    mask.image = image
    scaled = n.new("CompositorNodeScale")
    scaled.space = "RENDER_SIZE"
    scaled.frame_method = "STRETCH"
    l.new(mask.outputs["Image"],scaled.inputs["Image"])
    mult = n.new("CompositorNodeMixRGB")
    mult.blend_type, mult.inputs[0].default_value = "MULTIPLY",1
    l.new(scaled.outputs[0],mult.inputs[2])
    l.new(add.outputs[0],mult.inputs[1])
    flash = n.new("CompositorNodeMixRGB")
    flash.name = "Portal | exposure bridge"
    flash.inputs[2].default_value = (2.5,1.62,.80,1)
    l.new(mult.outputs[0],flash.inputs[1])
    l.new(flash.outputs[0],output.inputs[0])
    for f,value in ((1,0),(121,0),(125,.04),(126,.14),(127,.32),(128,.67),
                    (129,.91),(130,1),(131,.92),(132,.65),(133,.27),(134,.062),(136,.016),(139,0),(300,0)):
        flash.inputs[0].default_value = value
        flash.inputs[0].keyframe_insert("default_value",frame=f)
    return flash


def polaroid(c):
    root = empty("Golden Polaroid | card control",c)
    rim = emission("Polaroid | hot gold fillet","#FFBD58",2.0)
    stock = emission("Polaroid | ivory gold silkscreen","#F7D68E",.66)
    box("Polaroid | rigid paper board",c,(0,0,0),(.290,.023,.405),stock,.008,root,ink=.004)
    box("Polaroid | luminescent window rim",c,(0,-.014,.024),(.254,.005,.325),rim,.004,root)
    mat, plate = artwork("portal_plate",lit=False,glow=1.32)
    panel = mesh("Polaroid | match-view image",c,[(-.120,-.017,-.131),(.120,-.017,-.131),(.120,-.017,.179),(-.120,-.017,.179)],
                 [(0,1,2,3)],mat,root,uv=[(0,0),(1,0),(1,1),(0,1)])
    panel.visible_shadow = False
    return root,plate


def rain(c, ox):
    rng = Random(9)
    mat = emission("Rain | pale indigo streaks","#839CD0",.48)
    n, l = mat.node_tree.nodes, mat.node_tree.links
    e = next(node for node in n if node.type=="EMISSION")
    o = next(node for node in n if node.type=="OUTPUT_MATERIAL")
    t, m = n.new("ShaderNodeBsdfTransparent"), n.new("ShaderNodeMixShader")
    m.inputs[0].default_value = .32
    l.new(t.outputs[0],m.inputs[1]); l.new(e.outputs[0],m.inputs[2]); l.new(m.outputs[0],o.inputs[0])
    mat.surface_render_method = "BLENDED"
    vertices, faces = [], []
    for _ in range(390):
        x,y,z = rng.uniform(-2.35,2.35),rng.uniform(-7,5),rng.uniform(.23,7.2)
        width,length = rng.uniform(.002,.005),rng.uniform(.055,.19)
        i=len(vertices)
        vertices.extend([(x,y,z),(x+width,y,z),(x+width+.024,y,z+length),(x+.024,y,z+length),
                         (x,y+width,z),(x+.024,y+width,z+length)])
        faces.extend([(i,i+1,i+2,i+3),(i,i+4,i+5,i+3)])
    o = mesh("Rain | diagonal fine silver strokes",c,vertices,faces,mat)
    o.visible_shadow = False
    for f in range(129,301):
        travel = ((f-129)%36)*.11
        o.location = (ox-travel*.06,0,-travel)
        o.keyframe_insert("location",frame=f)
    return o


def reflection_paint(c, offset):
    """Baked-looking light breakup paired with real direct wet-surface specular."""
    rng = Random(247)
    for name, color, strength, xpos, ypos, width, length in (
        ("shop amber","#E39158",.34,-1.32,-2.3,1.26,4.9),
        ("display cyan","#4D9CD9",.34,-.67,-3.3,.45,3.1),
        ("awning coral","#B75589",.28,-1.62,-1.3,.47,4.8),
        ("counter amber","#CA8249",.38,.24,1.12,.69,1.75),
        ("warehouse lavender","#5F6CC8",.26,1.12,-.8,.79,5.2),
    ):
        mat = emission("Puddles | "+name,color,strength)
        n, l = mat.node_tree.nodes, mat.node_tree.links
        em = next(node for node in n if node.type=="EMISSION")
        out = next(node for node in n if node.type=="OUTPUT_MATERIAL")
        uv, noise = n.new("ShaderNodeTexCoord"), n.new("ShaderNodeTexNoise")
        scale = n.new("ShaderNodeVectorMath")
        scale.operation = "MULTIPLY"
        scale.inputs[1].default_value = (2,17,1)
        l.new(uv.outputs["UV"],scale.inputs[0]); l.new(scale.outputs[0],noise.inputs["Vector"])
        noise.inputs["Scale"].default_value = 3.1
        dist = n.new("ShaderNodeVectorMath")
        dist.operation = "DISTANCE"
        dist.inputs[1].default_value = (.5,.5,0)
        l.new(uv.outputs["UV"],dist.inputs[0])
        falloff = n.new("ShaderNodeMapRange")
        falloff.inputs["From Min"].default_value, falloff.inputs["From Max"].default_value = .07,.50
        falloff.inputs["To Min"].default_value, falloff.inputs["To Max"].default_value = .64,0
        l.new(dist.outputs["Value"],falloff.inputs[0])
        breakup = n.new("ShaderNodeMath")
        breakup.operation = "MULTIPLY"
        l.new(falloff.outputs[0],breakup.inputs[0]); l.new(noise.outputs["Fac"],breakup.inputs[1])
        mix, clear = n.new("ShaderNodeMixShader"), n.new("ShaderNodeBsdfTransparent")
        l.new(clear.outputs[0],mix.inputs[1]); l.new(em.outputs[0],mix.inputs[2])
        l.new(breakup.outputs[0],mix.inputs[0]); l.new(mix.outputs[0],out.inputs[0])
        mat.surface_render_method = "BLENDED"
        x,y,z=offset+xpos,ypos,.001+rng.uniform(0,.001)
        obj=mesh("Wet sheen | "+name,c,
                 [(x-width/2,y-length/2,z),(x+width/2,y-length/2,z),
                  (x+width/2,y+length/2,z),(x-width/2,y+length/2,z)],
                 [(0,1,2,3)],mat,uv=[(0,0),(1,0),(1,1),(0,1)])
        obj.visible_shadow=False


def ambient_legs(f, width=.098):
    return [((s*width,-.020,.028),(s*.109,-.041,.315)) for s in (-1,1)]


def home_pose(f, hero, ticket, lamp, sparkles):
    lift = ramp(f,59,82)
    rotation = lerp(-math.pi/2, -.045, lift)
    position = interpolate(f,[(1,(.02,-.044,.763)),(57,(.02,-.044,.763)),
                              (67,(.033,-.10,.881)),(83,(.014,-.215,1.047)),(96,(.014,-.213,1.050)),
                              (128,(.014,-.213,1.050))])
    ticket.location, ticket.rotation_euler = position, (rotation, -.04*lift, -.085*lift)
    ticket.keyframe_insert("location",frame=f)
    ticket.keyframe_insert("rotation_euler",frame=f)
    lamp.location = position + Vector((-.03,-.12,.07))
    lamp.data.energy = 5 + 10*ramp(f,55,93)
    lamp.keyframe_insert("location",frame=f)
    lamp.data.keyframe_insert("energy",frame=f)
    for i, spark in enumerate(sparkles):
        a = i*math.tau/len(sparkles) + f*.075
        p = Vector((.17*math.cos(a), -.025+.05*math.sin(2*a), .231*math.sin(a)))
        spark.location = position + ticket.rotation_euler.to_matrix() @ p
        scale = (.32+.68*lift) * (.25+.75*(.5+.5*math.sin(f*.19+i))**2)
        if f < 22:
            scale *= .55
        spark.scale = (scale,)*3
        spark.keyframe_insert("location",frame=f)
        spark.keyframe_insert("scale",frame=f)
    excitement = pop(f,20)*(1-ramp(f,48,60))
    pitch = -.114+.15*excitement+.19*lift
    bounce = excitement*.053
    yaw = .025*(1-lift)
    arm_pack = []
    for side in (-1,1):
        body_rot = Euler((pitch,0,0)).to_matrix()
        resting = body_rot.inverted() @ Vector((side*.20,-.21,.174-bounce))
        high = (side*.286,-.08,.59)
        mid = vec(resting,high,excitement)
        if side < 0:
            # Dot hand rides the physical left short edge throughout pickup.
            grip = position + ticket.rotation_euler.to_matrix() @ Vector((-.144,0,-.082))
            basis = Euler((pitch,0,0)).to_matrix()
            root_basis = Euler((0,0,-yaw)).to_matrix()
            grip = basis.inverted() @ (root_basis @ (grip - Vector(HERO_A)) - Vector((0,0,.59+bounce)))
            mid = vec(mid,grip,ramp(f,49,59))
        des = Vector((side*.193,-.124,.232)).lerp(Vector((side*.228,-.024,.448)),excitement)
        if side < 0:
            des = des.lerp(Vector((-.20,-.33,.255)),ramp(f,49,64))
        arm_pack.append((mid,des))
    expression = "suspicious" if f<20 else "excited_awe" if f<49 else "smug_focus"
    hero.pose(f,HERO_A,yaw,pitch,arm_pack,ambient_legs(f),expression,
              bounce=bounce,head_tilt=.14*(1-excitement)*(1-lift),head_yaw=-.11*(1-excitement))
    return position


def run_y(f):
    # Long middle section at approximately constant speed, softened entry and skid.
    if f < 139:
        return -4.76
    s = min(1.,max(0.,(f-139)/80))
    t = s + .18*math.sin(math.pi*s)**2*math.sin(math.pi*(s-.07))
    return lerp(-4.76,1.91,t)


def runner_foot(f, side, yaw, walk, skid):
    first = 139 if side < 0 else 133
    step = first + 12*math.floor((f-first)/12)
    phase = (f-step)/12
    contact_y = run_y(step+3)
    next_y = run_y(step+15)
    swing = max(0.,2*phase-1)
    world_offset = lerp(contact_y,next_y,smooth(swing))-run_y(f)
    offset = Euler((0,0,-yaw)).to_matrix() @ Vector((0,world_offset,0))
    height = .162*math.sin(math.pi*swing)*walk
    foot = Vector((side*(.097+.023*skid),-.022+.081*skid,.028+height)) + offset*walk
    knee = (side*.101 + offset.x*.35, min(-.061,foot.y*.48)-.12*height/.162,
            .326+height*.42)
    return foot,knee


def alley_pose(f, hero, broker, cube, bulb, cube_light):
    advance = run_y(f)
    walk = ramp(f,137,145)*(1-ramp(f,209,220))
    q = (f-139)*math.tau/12
    skid = math.sin(math.pi*ramp(f,210,222))
    terror = pop(f,266)
    yaw = math.pi-.21*(1-ramp(f,199,220)) + .14*terror
    roll = .232*walk-.15*skid-.15*terror
    arms, legs = [], []
    for side in (-1,1):
        stride = q + (math.pi if side>0 else 0)
        swing = math.sin(stride)*walk
        legs.append(runner_foot(f,side,yaw,walk,skid))
        tremble = .009*math.sin(f*1.75+side)*ramp(f,272,278) if f>=272 else 0
        arms.append((vec((side*.181,-.07-.227*swing,.112+.089*abs(swing)),
                         (side*(.316+tremble),-.09,.590+tremble),terror),
                     vec((side*.197,.102*swing,.251),(side*.273,-.02,.363),terror)))
    hero.pose(f,(OFFSET+HERO_B_X,advance,0),yaw,roll,arms,legs,
              "shock_terror" if f>=266 else "sneaky",bounce=.035*walk*(.5+.5*math.cos(2*q))-.035*terror,
              head_tilt=.12*walk-.17*terror,head_yaw=-.25*walk-.21*terror,
              squash=1-.069*terror,sweat=ramp(f,268,294) if f>=268 else None)
    lean = pop(f,244,4)
    push = ramp(f,245,261)
    cube.location = (OFFSET+.24+.12*push,2.995-.525*push,.9895)
    cube.rotation_euler.z = .1+.36*push
    cube.keyframe_insert("location",frame=f)
    cube.keyframe_insert("rotation_euler",frame=f)
    cube_light.location = cube.location + Vector((0,-.025,.07))
    cube_light.keyframe_insert("location",frame=f)
    bulb.location.x = OFFSET-.12+.034*math.sin((f-134)*.093)
    bulb.keyframe_insert("location",frame=f)
    left = ((-.17,-.37,.36),(-.24,-.17,.29))
    pos = cube.location-Vector(BROKER_B)
    grip = pos+cube.rotation_euler.to_matrix() @ Vector((.077,.008,.015))
    grip = Euler((0,0,.09)).to_matrix() @ grip
    body_angle = -.065*lean
    grip = Euler((body_angle,0,0)).to_matrix().inverted() @ (grip-Vector((0,0,.59)))
    broker.pose(f,BROKER_B,-.09,body_angle,
                [left,(vec((.16,-.23,.37),grip,ramp(f,239,245)),(.235,-.164,.305))],
                ambient_legs(f),"broker_creepy_grin" if f>=244 else "broker_neutral",
                head_tilt=-.16*lean,head_yaw=-.1*lean)


def camera_pose(frame, ticket, camera, focus):
    if frame < 130:
        p = interpolate(frame,[(1,(-.43,-2.79,1.57)),(48,(-.18,-2.01,1.39)),(78,(-.14,-1.49,1.19)),
                               (96,(-.08,-1.07,1.08)),(116,(-.026,-.79,1.077)),
                               (129,(.014,-.309,1.071))])
        t = interpolate(frame,[(1,(-.04,.25,1.14)),(48,(.05,.28,1.13)),(80,(.022,-.115,1.053)),
                               (97,(.014,-.22,1.067)),(129,(.014,-.220,1.073))])
        q = vec((.13,.38,1.21),ticket+Vector((0,-.016,.018)),ramp(frame,48,84))
        lens = 38
    elif frame < 226:
        y = run_y(frame)
        stage = ramp(frame,139,178)
        finish = ramp(frame,195,225)
        p = Vector((OFFSET+lerp(.82,1.49,stage)-.25*finish,
                    y+lerp(-1.59,1.00,stage)-.76*finish,
                    lerp(1.00,.78,stage)+.52*finish))
        if frame<=139:
            p += Vector((.04,-.32,.10))*(1-ramp(frame,130,139))
        t = Vector((OFFSET+lerp(.03,HERO_B_X,stage),lerp(2.55,y-.01,stage)+.24*finish,
                    lerp(1.28,.807,stage)+.20*finish))
        q = Vector((OFFSET+HERO_B_X,y,.95)).lerp(Vector((OFFSET,2.65,1.19)),1-stage)
        whip = ramp(frame,218,226)
        p = vec(p,(OFFSET+.06,.67,1.51),whip)
        t = vec(t,(OFFSET+.18,3.03,1.21),whip)
        q = vec(q,(OFFSET+.18,3.02,1.24),whip)
        lens = lerp(35,43,whip)
    elif frame < 265:
        p = interpolate(frame,[(226,(OFFSET+.06,.67,1.51)),(239,(OFFSET+.52,1.44,1.41)),
                               (264,(OFFSET+.64,1.81,1.37))])
        t = interpolate(frame,[(226,(OFFSET+.18,3.03,1.21)),(239,(OFFSET+.21,3.05,1.219)),
                               (264,(OFFSET+.22,3.02,1.205))])
        q = (OFFSET+.18,3.02,1.24)
        lens = 43
    else:
        u = ramp(frame,265,300)
        angle = lerp(-.30,-.09,u)
        radius = lerp(1.58,1.27,ramp(frame,265,290))-.038*u
        reaction = pop(frame,266)
        t = Vector((OFFSET+HERO_B_X-.003,lerp(2.04,1.935,reaction),1.22-.136*reaction))
        p = t + Vector((radius*math.sin(angle),radius*math.cos(angle),.10-.062*u))
        q = t + Vector((.01,.09,.045))
        lens = 43
    camera.location, camera.data.lens = p,lens
    aim(camera,t)
    # Focus distance is the plane measured along camera forward, not raw range.
    focus.location = q
    camera.data.dof.focus_distance = max(.085,(Vector(q)-p).dot((t-p).normalized()))
    for obj,channels in ((camera,("location","rotation_quaternion")),(focus,("location",)),
                         (camera.data,("lens","dof.focus_distance"))):
        for channel in channels:
            obj.keyframe_insert(channel,frame=frame)


def main():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    look.configure_scene(scene, frame_end=FRAMES, samples=8)
    scene.view_settings.view_transform, scene.view_settings.look = "AgX","AgX - Medium High Contrast"
    scene.eevee.shadow_pool_size = "512"
    scene.eevee.shadow_ray_count, scene.eevee.shadow_step_count = 1,4
    scene.eevee.fast_gi_method = "AMBIENT_OCCLUSION_ONLY"
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.image_settings.color_depth = "8"
    scene.render.image_settings.compression = 0
    scene.world = bpy.data.worlds.new("Slate night")
    scene.world.use_nodes = True
    bg = next(node for node in scene.world.node_tree.nodes if node.type=="BACKGROUND")
    bg.inputs[0].default_value, bg.inputs[1].default_value = look.rgba("#30416D"),.27
    scene.render.film_transparent = False
    flash = post(scene)
    set_a = collection("A • Apartment",scene.collection)
    set_b = collection("B • Neon pawn alley",scene.collection)
    cast_a, cast_b = collection("Apartment rig",set_a),collection("Alley rigs",set_b)
    movie = collection("Camera",scene.collection)
    apartment(set_a)
    bulb, gold, cyan = alley(set_b,OFFSET)
    rain(set_b,OFFSET)
    reflection_paint(set_b,OFFSET)
    hero_a, hero_b, broker = Actor("Hero A",cast_a),Actor("Hero B",cast_b),Actor("Shady Broker",cast_b,True)
    ticket, plate = polaroid(set_a)
    plate_light = light("Polaroid | colored hand bounce",set_a,(0,-.21,.91),(.10,.60,1.1),"#FFB95B",5,.19)
    sparks = [ball("Polaroid | orbiting sun mote",set_a,(0,0,0),(.008,.008,.015),gold,
                  segments=8,rings=6) for _ in range(14)]
    cube = box("Memory cube | glowing chassis",set_b,(OFFSET,3,.98),(.136,)*3,cyan,.017,ink=.005)
    core = emission("Memory cube | inner line","#FFE4A7",3.)
    box("Memory cube | cap gem",set_b,(0,0,.071),(.069,.069,.013),core,.006,cube)
    box("Memory cube | face gem",set_b,(0,-.070,0),(.069,.014,.069),core,.006,cube)
    cube_light = light("Memory cube | practical bounce",set_b,(OFFSET,2.7,1.1),(OFFSET,2.5,.9),"#78DDFF",8,.09)
    camera = bpy.data.objects.new("Delivery camera",bpy.data.cameras.new("Vertical full sensor"))
    movie.objects.link(camera)
    focus = empty("Focus plane target",movie)
    look.configure_camera(camera,None, lens=38,fstop=2.85)
    camera.data.clip_end = 110
    scene.camera = camera
    last_position = None
    for f in range(1,301):
        if f<=129:
            last_position = home_pose(f,hero_a,ticket,plate_light,sparks)
        if f>=130:
            alley_pose(f,hero_b,broker,cube,bulb,cube_light)
        camera_pose(f,last_position,camera,focus)
        for actor in ((hero_a,) if f<130 else (hero_b,broker)):
            height = .99 if actor.name.startswith("Hero") else 1.15
            distance = (actor.root.location+Vector((0,0,height))-camera.location).length
            for mod in actor.ink_modifiers:
                mod.strength = -min(.015,look.ink_width(distance,camera.data.lens,3.)*1.34)
                mod.keyframe_insert("strength",frame=f)
    for frame,name in [(1,"Desk | suspicion"),(20,"Excitement snap"),(49,"Polaroid pickup"),(97,"Portal dive"),
                       (130,"Golden match | live alley"),(139,"Sneak-run"),(212,"Skid"),(226,"Whip to the broker"),
                       (244,"Grin and memory cube"),(265,"Whip reaction"),(266,"Terror snap")]:
        scene.timeline_markers.new(name,frame=frame)
    set_visibility_from_scene(set_a,True)
    set_visibility_from_scene(set_b,False)
    for action in bpy.data.actions:
        for fcurve in action.fcurves:
            constant = fcurve.data_path in ("hide_render","hide_viewport","lens") or '["local_hide_' in fcurve.data_path
            for key in fcurve.keyframe_points:
                key.interpolation = "CONSTANT" if constant else "LINEAR"
    scene.render.filepath = str(OUT / "portal_plate.png")
    scene.render.resolution_percentage = 63
    scene.frame_set(139)
    camera.data.dof.use_dof = False
    bpy.ops.render.render(write_still=True)
    camera.data.dof.use_dof = True
    photo = bpy.data.images.load(str(OUT / "portal_plate.png"))
    photo.pack()
    plate.image = photo
    scene.render.resolution_percentage = 100
    scene.render.filepath = "//frame_"
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=="VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "ricks_benchmark_v01.blend"))


if __name__ == "__main__":
    main()
