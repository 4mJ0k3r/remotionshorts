"""Build and bake the standalone 300-frame Blender scene. Run under the GPU lock."""
import math
import sys
from pathlib import Path
from random import Random

import bpy
from mathutils import Euler, Vector

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
OUT = ROOT / "renders/ricks_benchmark_10s/v01c"
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
    flash.name = "Portal | additive warm-gold flash"
    flash.blend_type = "ADD"
    flash.inputs[2].default_value = (18.0,10.0,4.6,1)
    l.new(mult.outputs[0],flash.inputs[1])
    l.new(flash.outputs[0],output.inputs[0])
    for f,value in ((1,0),(124,0),(125,.035),(126,.48),(127,.82),(128,1),
                    (129,1),(130,1),(131,.28),(132,.028),(133,0),(300,0)):
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
        # The pawn stall is sheltered, including the camera-to-counter sight line.
        if y>1.11 and abs(x)<1.65:
            continue
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
                              (67,(.033,-.10,.827)),(83,(.014,-.215,.917)),(88,(.014,-.215,.926)),
                              (96,(.014,-.213,1.050)),
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
        if side < 0:
            high = (-.31,-.155,.562+.041*ramp(f,23,31))
            raised_elbow = (-.209,-.074,.428)
            excitement_arm = pop(f,20,4)*(1-ramp(f,48,60))
        else:
            high = (.307,-.236,.449+.075*ramp(f,24,32))
            raised_elbow = (.223,-.108,.366)
            excitement_arm = pop(f,22,6)*(1-ramp(f,48,60))
        mid = vec(resting,high,excitement_arm)
        des = vec((side*.193,-.124,.232),raised_elbow,excitement_arm)
        if side < 0:
            # The arm-tip tracks the physical card edge until the portal lift.
            grip = position + ticket.rotation_euler.to_matrix() @ Vector((-.144,0,-.082))
            release = ramp(f,96,105)
            grip += Vector((-.10,.106,-.154))*release
            basis = Euler((pitch,0,0)).to_matrix()
            root_basis = Euler((0,0,-yaw)).to_matrix()
            grip = basis.inverted() @ (root_basis @ (grip - Vector(HERO_A)) - Vector((0,0,.59+bounce)))
            mid = vec(mid,grip,ramp(f,49,59))
            mid = vec(mid,resting,ramp(f,102,110))
            des = vec(des,(-.20,-.28,.255),ramp(f,49,64)*(1-ramp(f,96,109)))
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


def route(f):
    x = HERO_B_X+.50*(1-ramp(f,135,162))-.095*ramp(f,210,219)+.145*ramp(f,225,234)
    return Vector((OFFSET+x,run_y(f)+.136*ramp(f,225,234),0))


def runner_foot(f, side, yaw, root):
    """Build each stance in world space and solve backward into the turning rig."""
    first = 139 if side < 0 else 134
    step = first + 10*math.floor((f-first)/10)
    phase = f-step

    def anchor(strike):
        plant = route(min(max(strike+2,137),219))
        return plant+Vector((-side*.103,.032,.017))

    toe_off = max(0.,(phase-4)/6)
    stride_lift = .165*(1-.64*ramp(step,208,220))
    center = vec(anchor(step),anchor(step+10),smooth(toe_off))
    center.z += stride_lift*math.sin(math.pi*toe_off)**1.3 if step<219 else 0
    settle_start = 224 if side > 0 else 229
    settle = ramp(f,settle_start,settle_start+5)
    center += Vector((.145*settle,.136*settle,.085*math.sin(math.pi*settle)))
    inverse = Euler((0,0,-yaw)).to_matrix()
    ankle = inverse @ (center-root)
    foot = ankle+Vector((0,.021,.010))
    lift = max(0,center.z-.017)
    knee = (lerp(side*.095,foot.x,.32),min(-.059,foot.y*.42)-.70*lift,.318+.43*lift)
    return foot,knee


def alley_pose(f, hero, broker, cube, bulb, cube_light):
    root = route(f)
    walk = ramp(f,136,142)*(1-ramp(f,209,220))
    q = (f-139)*math.tau/10
    skid = math.sin(math.pi*ramp(f,210,222))
    terror = pop(f,266)
    yaw = math.pi-.21*(1-ramp(f,199,220)) + .14*terror
    roll = .332*walk-.15*skid-.15*terror
    arms, legs = [], []
    for side in (-1,1):
        stride = q + (math.pi if side>0 else 0)
        swing = math.cos(stride)*walk
        legs.append(runner_foot(f,side,yaw,root))
        low_arm = ramp(f,217,226)*(1-ramp(f,245,252))
        everyday = vec((side*.156,-.075+.244*swing,.082+.098*max(0,-swing)),
                       (side*.052,-.117,-.052),low_arm)
        elbow = vec((side*.179,.042+.128*swing,.237+.044*swing),
                    (side*.090,-.093,.119),low_arm)
        tremble = ramp(f,266,272)*(.011*math.sin(f*2.05+side)+.003*math.sin(f*2.61-side))
        arms.append((vec(everyday,(side*.231+tremble,-.078,.655+.62*tremble),terror),
                     vec(elbow,(side*.240,-.03,.390),terror)))
    bob = .060*walk*(.5-.5*math.cos(2*q))**1.18
    hero.pose(f,root,yaw,roll,arms,legs,
              "shock_terror" if f>=266 else "sneaky",bounce=bob-.035*terror,
              head_tilt=.12*walk-.17*terror,head_yaw=-.25*walk-.21*terror,
              squash=1-.069*terror,sweat=ramp(f,268,294) if f>=268 else None)
    lean = ramp(f,244,252)
    push = ramp(f,244,260)
    cube.location = (OFFSET+.24+.12*push,2.895-.435*push,.9895)
    cube.rotation_euler.z = .1+.36*push
    cube.keyframe_insert("location",frame=f)
    cube.keyframe_insert("rotation_euler",frame=f)
    cube_light.location = cube.location + Vector((0,-.025,.07))
    cube_light.keyframe_insert("location",frame=f)
    bulb.location.x = OFFSET-.12+.034*math.sin((f-134)*.093)
    bulb.keyframe_insert("location",frame=f)
    left = ((-.17,-.37,.36),(-.24,-.17,.29))
    pos = cube.location-Vector(BROKER_B)
    grip = pos+cube.rotation_euler.to_matrix() @ Vector((.072,.008,.015))
    grip = Euler((0,0,.09)).to_matrix() @ grip
    body_angle = .10*lean
    grip = Euler((body_angle,0,0)).to_matrix().inverted() @ (grip-Vector((0,0,.59)))
    broker.pose(f,BROKER_B,-.09,body_angle,
                [left,(vec((.16,-.23,.37),grip,ramp(f,239,244)),(.235,-.164,.305))],
                ambient_legs(f),"broker_creepy_grin" if f>=244 else "broker_neutral",
                head_tilt=.18*lean,head_yaw=-.075*lean)


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
        root = route(frame)
        y = root.y
        stage = ramp(frame,139,178)
        finish = ramp(frame,195,225)
        p = Vector((OFFSET+lerp(.82,1.49,stage)-.25*finish,
                    y+lerp(-1.59,1.00,stage)-.76*finish,
                    lerp(1.00,.78,stage)+.52*finish))
        if frame<=139:
            p += Vector((.04,-.32,.10))*(1-ramp(frame,130,139))
        entry = ramp(frame,135,153)
        t = Vector((lerp(OFFSET+.03,root.x,entry),lerp(2.55,y-.01,entry)+.24*finish,
                    lerp(1.28,.807,entry)+.20*finish))
        q = vec((OFFSET,2.65,1.19),(root.x,y,.95),entry)
        whip = ramp(frame,218,226)
        p = vec(p,(OFFSET+.06,.67,1.51),whip)
        t = vec(t,(OFFSET+.18,3.03,1.21),whip)
        q = vec(q,(OFFSET+.18,3.02,1.24),whip)
        lens = lerp(35,43,whip)
    elif frame < 265:
        p = interpolate(frame,[(226,(OFFSET+.06,.67,1.51)),(234,(OFFSET+.12,.94,1.49)),
                               (246,(OFFSET+.53,1.57,1.40)),
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
        root = route(frame)
        t = Vector((root.x-.003,root.y+lerp(.13,.025,reaction),1.22-.136*reaction))
        p = t + Vector((radius*math.sin(angle),radius*math.cos(angle),.10-.062*u))
        # Feather the eye point forward of the counter's rear shelf.
        cap, margin = 3.33,.07
        p.y = min(p.y,cap)-max(0.,margin-abs(p.y-cap))**2/(4*margin)
        shake = {267:(.005,0,.006),268:(-.008,0,-.007),269:(.003,0,.003)}
        if frame in shake:
            p += Vector(shake[frame])
        q = t + Vector((.01,.09,.045))
        lens = 43+5.6*ramp(frame,266,270)*(1-ramp(frame,275,285))
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
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT / "ricks_benchmark_v01c.blend"))


if __name__ == "__main__":
    main()
