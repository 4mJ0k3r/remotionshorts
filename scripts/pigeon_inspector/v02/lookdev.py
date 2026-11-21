"""Pigeon Inspector v02. Copy v01 and change only its shading and lighting."""
import hashlib
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import time
from uuid import uuid4


ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "renders/pigeon_inspector"
SOURCE = BASE / "v01/pigeon_inspector_v01.blend"
OUT = BASE / "v02"
SCENE = OUT / "pigeon_inspector_v02.blend"
FRAMES = (1, 105, 147)


def timeline(scene, bpy):
    """Fingerprint the edit, key values, interpolation, and action bindings."""
    def owner_action(owner):
        return owner.animation_data.action if owner and owner.animation_data else None

    owners = (list(bpy.data.objects) + list(bpy.data.cameras) +
              list(bpy.data.curves) + [scene, scene.node_tree])
    bindings = sorted((owner.bl_rna.identifier, owner.name, owner_action(owner).name)
                      for owner in owners if owner_action(owner))
    actions = {}
    for action in bpy.data.actions:
        curves = {}
        for curve in action.fcurves:
            curves[(curve.data_path, curve.array_index)] = (
                curve.extrapolation,
                [(tuple(p.co), tuple(p.handle_left), tuple(p.handle_right),
                  p.interpolation, p.handle_left_type, p.handle_right_type)
                 for p in curve.keyframe_points],
            )
        actions[action.name] = sorted(curves.items())
    state = (scene.frame_start, scene.frame_end, scene.render.fps, scene.render.fps_base,
             sorted((m.frame,m.name,m.camera.name if m.camera else None) for m in scene.timeline_markers),
             scene.camera.name, scene.camera.data.name, scene.camera.data.dof.focus_object.name,
             bindings, sorted(actions.items()))
    return hashlib.sha256(repr(state).encode()).hexdigest()


def ramp(tree, signal, name, stops):
    node = tree.nodes.new("ShaderNodeValToRGB")
    node.label = name
    palette = node.color_ramp
    palette.elements.remove(palette.elements[1])
    for index, (position, color) in enumerate(stops):
        entry = palette.elements[0] if index == 0 else palette.elements.new(position)
        entry.position, entry.color = position,color
    tree.links.new(signal, node.inputs[0])
    return node.outputs["Color"]


def noise(tree, vector, scale, detail, label):
    node = tree.nodes.new("ShaderNodeTexNoise")
    node.label = label
    node.inputs["Scale"].default_value = scale
    node.inputs["Detail"].default_value = detail
    tree.links.new(vector, node.inputs["Vector"])
    return node.outputs["Fac"]


def number(tree, op, a, b):
    node = tree.nodes.new("ShaderNodeMath")
    node.operation = op
    for socket, value in zip(node.inputs, (a,b)):
        if isinstance(value,(int,float)):
            socket.default_value = value
        else:
            tree.links.new(value,socket)
    return node.outputs[0]


def anisotropy(tree, vector, factors):
    node = tree.nodes.new("ShaderNodeVectorMath")
    node.operation = "MULTIPLY"
    tree.links.new(vector,node.inputs[0])
    node.inputs[1].default_value = factors
    return node.outputs["Vector"]


def bump(tree, surface, detail, strength, distance):
    node = tree.nodes.new("ShaderNodeBump")
    node.inputs["Strength"].default_value = strength
    node.inputs["Distance"].default_value = distance
    tree.links.new(detail,node.inputs["Height"])
    tree.links.new(node.outputs["Normal"],surface.inputs["Normal"])


def principled(material):
    return next(n for n in material.node_tree.nodes if n.type == "BSDF_PRINCIPLED")


def replace_slot(obj, material):
    obj.data.materials[0] = material


def station_materials(bpy, kit):
    def pigment(color):
        return kit.look.rgba(color)

    wood = kit.surface("v02 | Worn longitudinal timber", "#7A4B35", .67)
    tree = wood.node_tree
    surface = principled(wood)
    local = tree.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    scaled = anisotropy(tree,local,(2.4,90,108))
    family = tree.nodes.new("ShaderNodeObjectInfo")
    offset = tree.nodes.new("ShaderNodeVectorMath")
    offset.operation = "ADD"
    tree.links.new(scaled,offset.inputs[0])
    tree.links.new(family.outputs["Random"],offset.inputs[1])
    fiber = noise(tree,offset.outputs["Vector"],1,2,"Long fibers run along local X")
    grain = ramp(tree,fiber,"Oiled latewood and faded raised fibers",[
        (.19,pigment("#4A302A")),(.37,pigment("#654035")),
        (.61,pigment("#8F6047")),(.81,pigment("#A97A56")),
    ])
    tree.links.new(grain,surface.inputs["Base Color"])
    tree.links.new(number(tree,"ADD",.56,number(tree,"MULTIPLY",fiber,.26)),surface.inputs["Roughness"])
    bump(tree,surface,fiber,.16,.006)

    paint = kit.surface("v02 | Teal enamel with rubbed cast edges","#2E4D51",.57,.08)
    tree = paint.node_tree
    surface = principled(paint)
    tex = tree.nodes.new("ShaderNodeTexCoord")
    split = tree.nodes.new("ShaderNodeSeparateXYZ")
    tree.links.new(tex.outputs["Generated"],split.inputs[0])
    offsets = [number(tree,"MINIMUM",component,number(tree,"SUBTRACT",1,component))
               for component in split.outputs]
    x,y,z = offsets
    corner = number(tree,"MINIMUM",number(tree,"MAXIMUM",x,y),
                    number(tree,"MINIMUM",number(tree,"MAXIMUM",y,z),number(tree,"MAXIMUM",x,z)))
    edge = number(tree,"SUBTRACT",.095,corner)
    edge = number(tree,"MINIMUM",1,number(tree,"MAXIMUM",0,number(tree,"MULTIPLY",edge,12)))
    grain = noise(tree,tex.outputs["Object"],76,2,"Fine scratches and oxide variation")
    rub = number(tree,"MULTIPLY",edge,grain)
    tone = ramp(tree,rub,"Paint to dark rubbed metal",[
        (0,pigment("#243E42")),(.26,pigment("#315156")),
        (.64,pigment("#647473")),(.96,pigment("#A09888")),
    ])
    tree.links.new(tone,surface.inputs["Base Color"])
    tree.links.new(number(tree,"ADD",.08,number(tree,"MULTIPLY",rub,.59)),surface.inputs["Metallic"])
    tree.links.new(number(tree,"SUBTRACT",.62,number(tree,"MULTIPLY",rub,.33)),surface.inputs["Roughness"])
    bump(tree,surface,grain,.10,.002)

    bolts = kit.surface("v02 | Warm oxidized fasteners","#84705A",.53,.58)
    tree = bolts.node_tree
    surface = principled(bolts)
    local = tree.nodes.new("ShaderNodeTexCoord").outputs["Object"]
    patina = noise(tree,local,211,2,"Patina along the bolt heads")
    tree.links.new(ramp(tree,patina,"Oxide and rubbed brass",[
        (.23,pigment("#4A423B")),(.6,pigment("#877053")),(.81,pigment("#AD9873")),
    ]),surface.inputs["Base Color"])
    tree.links.new(number(tree,"ADD",.36,number(tree,"MULTIPLY",patina,.32)),surface.inputs["Roughness"])

    for obj in bpy.data.objects:
        if obj.name.startswith(("Bench oiled seat slat","Bench backrest slat")):
            replace_slot(obj,wood)
        elif obj.name.startswith(("Bench cast leg","Bench anchor foot","Seat bearer",
                                  "Bench upright","Curled bench arm")):
            replace_slot(obj,paint)
        elif obj.name.startswith(("Bench anchor bolt","Flush slat screw")):
            replace_slot(obj,bolts)

    palettes = (
        ("#424D58","#566471","#63707B"),("#414C56","#52616A","#606D74"),
        ("#48525B","#5D6770","#6C757B"),("#3F4B58","#536172","#607083"),
    )
    for i,(dark,base,light) in enumerate(palettes):
        material = bpy.data.materials[f"Vitrified slate {i}"]
        tree = material.node_tree
        tree.nodes.clear()
        surface = tree.nodes.new("ShaderNodeBsdfPrincipled")
        surface.inputs["Specular IOR Level"].default_value = .28
        out = tree.nodes.new("ShaderNodeOutputMaterial")
        tree.links.new(surface.outputs[0],out.inputs["Surface"])
        tex = tree.nodes.new("ShaderNodeTexCoord")
        coarse = noise(tree,tex.outputs["Object"],19,2,"Quiet mottling in the pressed stone")
        fine = noise(tree,tex.outputs["Object"],154,1,"Fine aggregate modulates roughness")
        tone = ramp(tree,coarse,"Restrained paving variation",[
            (.12,pigment(dark)),(.5,pigment(base)),(.88,pigment(light)),
        ])
        tree.links.new(tone,surface.inputs["Base Color"])
        rough = number(tree,"ADD",.64+i*.024,number(tree,"MULTIPLY",fine,.16))
        tree.links.new(rough,surface.inputs["Roughness"])
        bump(tree,surface,fine,.12,.003)

    stock = kit.surface("v02 | Matte warm cream ticket stock","#FFF0CE",.91,glow=.23)
    principled(stock).inputs["Specular IOR Level"].default_value = .15
    for obj in bpy.data.objects:
        if obj.name in {"Ticket | pierced paper with open cut edge","Ticket | removable chad"}:
            replace_slot(obj,stock)


def station_light(scene, bpy, kit):
    col = bpy.data.collections.new("05 | v02 practical lighting")
    scene.collection.children.link(col)
    for name in ("Warm morning across the tracks","Cool station fill","Rake under bench"):
        bpy.data.objects[name].data.energy = 0

    def place(name, origin, target, color, watts, size, **kwargs):
        obj = kit.make_ricks_light(name,col,origin,target,color,watts,size,**kwargs)
        obj.data.use_shadow_jitter = True
        return obj.data

    place("Open platform | cool sky",(.25,-2.62,3.29),(.50,-.06,.25),"#B5D6F6",275,4.5)
    for x, target in ((-2.16,-.91),(2.95,1.68)):
        canopy = place("Frosted canopy pendant | cool-white pool",(x,.41,2.775),
                       (target,-.14,.19),"#DFECFF",83,.34,kind="SPOT",angle=66)
        canopy.spot_blend = .82

    for j,(x,aim_x,aim_y,energy) in enumerate(((-1.8,-1.06,.31,1600),(.3,.31,.44,1490),
                                              (2.4,1.52,.46,1710)),1):
        source = (x,4.685,1.59)
        window = place(f"Opposite window bay {j} | warm spill",source,
                       (aim_x,aim_y,.038),"#FFBC78",energy,.30,kind="SPOT",angle=25)
        window.spot_blend = .48
        trim = place(f"Opposite window bay {j} | mullion bounce",
                     (x,4.48,1.66),(x,4.95,1.56),"#FFB570",26,.65)
        trim.shape,trim.size_y="RECTANGLE",.78

    for name, colors, strength in (
        ("Morning light through frosted panes",("#BD7450","#E6A36B"),1.05),
        ("Warm high panes",("#D09662","#F6D7A4"),1.14),
    ):
        material = bpy.data.materials[name]
        tree = material.node_tree
        tex = tree.nodes.new("ShaderNodeTexCoord")
        split = tree.nodes.new("ShaderNodeSeparateXYZ")
        tree.links.new(tex.outputs["Generated"],split.inputs[0])
        color = ramp(tree,split.outputs["Z"],"Frosted glass warms toward the header",[
            (.03,kit.look.rgba(colors[0])),(.96,kit.look.rgba(colors[1])),
        ])
        light = next(n for n in tree.nodes if n.type=="EMISSION")
        tree.links.new(color,light.inputs["Color"])
        light.inputs["Strength"].default_value = strength

    scene.eevee.taa_render_samples = 32
    scene.eevee.shadow_ray_count = 3
    scene.eevee.shadow_step_count = 6


def graphic_finish(scene, bpy):
    hair = bpy.data.objects["Commuter | shaped hair cap"].data.materials[0]
    for node in hair.node_tree.nodes:
        if node.type == "VALTORGB":
            stops = node.color_ramp.elements
            base = tuple(stops[1].color)
            stops[0].color = tuple(c*.84 for c in base[:3])+(1,)
            stops[-1].color = tuple(c*1.30 for c in base[:3])+(1,)
    saturation = scene.node_tree.nodes["Cinema | Saturation 1.12"]
    saturation.inputs["Saturation"].default_value = 1.05
    saturation.label = "Cinema | restrained saturation"
    for node in scene.node_tree.nodes:
        if node.type == "MIX_RGB" and node.blend_type=="ADD" and node.name.startswith("Mix"):
            node.inputs[0].default_value = .16


def worker(candidate):
    import bpy
    sys.path.insert(0,str(ROOT/"scripts"))
    import ricks_v2_kit as kit
    import shorts_preflight

    scene = bpy.context.scene
    before = timeline(scene,bpy)
    station_materials(bpy,kit)
    station_light(scene,bpy,kit)
    graphic_finish(scene,bpy)
    if timeline(scene,bpy) != before:
        raise RuntimeError("Look development changed the source edit or animation.")
    scene.name = "The Pigeon Inspector | v02 look development"
    scene.render.filepath = "//stills/frame_"
    scene.frame_set(1)
    bpy.context.preferences.filepaths.save_version = 0
    bpy.ops.wm.save_as_mainfile(filepath=str(SCENE))
    bpy.ops.wm.open_mainfile(filepath=str(SCENE))
    scene = bpy.context.scene
    if timeline(scene,bpy) != before:
        raise RuntimeError("Saved edit or animation differs from v01.")
    folder = OUT/candidate
    folder.mkdir(exist_ok=True)
    checks = {}
    for frame in FRAMES:
        scene.frame_set(frame)
        resources = shorts_preflight.validate_resources(scene)
        if not resources["pass"] or resources["target_exceeded"]:
            raise RuntimeError(f"Frame {frame} exceeds geometry gates: {resources}")
        scene.render.filepath = str(folder/f"frame_{frame:04d}.png")
        started = time.perf_counter()
        bpy.ops.render.render(write_still=True)
        checks[str(frame)] = {"elapsed_seconds":round(time.perf_counter()-started,3),**resources}
    data = {"animation_fingerprint_v01_and_v02":before,"render_size":[540,960],"fps":30,
            "source_sha256": hashlib.file_digest(SOURCE.open("rb"),"sha256").hexdigest(),
            "stills":checks}
    (OUT/"verification.json").write_text(json.dumps(data,indent=2),encoding="utf-8")


def main():
    candidate = sys.argv[1] if len(sys.argv)>1 else "stills"
    if Path(candidate).name != candidate or candidate in {".","..",""}:
        raise SystemExit("Enter a stills folder name within the v02 folder.")
    OUT.mkdir(parents=True,exist_ok=True)
    lock, owner = ROOT/".blender_gpu.lock",uuid4().hex
    try:
        with lock.open("x",encoding="utf-8") as handle:
            json.dump({"project":"pigeon_inspector/v02","owner":owner,"pid":os.getpid()},handle)
    except FileExistsError:
        raise SystemExit("The Blender GPU lock is held by another job.")
    try:
        blender = os.environ.get("BLENDER_EXE",r"D:\tools\Blender\4.2.23\blender.exe")
        with (OUT/f"{candidate}.log").open("w",encoding="utf-8") as log:
            subprocess.run([blender,"-b","--factory-startup",str(SOURCE),"--python-exit-code","1",
                            "--python",str(Path(__file__).resolve()),"--",candidate],
                           cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,check=True)
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner")==owner:
            lock.unlink()


if __name__=="__main__":
    if "--" in sys.argv:
        worker(sys.argv[sys.argv.index("--")+1])
    else:
        main()
