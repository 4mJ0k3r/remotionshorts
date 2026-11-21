"""Apply the approved portrait treatment to fresh copies of the four locked edits."""
from shutil import copy2

import bpy
from mathutils import Vector

import ricks_v2_kit as kit
from timing import ROOT


# Intervals are zero-based, half-open picture frames in the local Blender file.
PORTRAITS = {
    1: ((0, 230, "Red Cap at the toilet"), (248, 392, "Red Cap at the toilet"),
        (392, 763, "Red Cap at his desk"), (763, 837, "Stern teacher")),
    2: ((282, 503, "Red-Cap Boy hanging onto the strap"),
        (503, 558, "Red-Cap walking past the flowers"),
        (558, 661, "Florist with red and white apron"),
        (661, 772, "Red-Cap walking past the flowers")),
    3: ((341, 616, "Red-Cap Boy leading the dog parade"),),
    4: ((0, 153, "Dejected Red-Cap on the bed"),
        (206, 259, "Red-Cap Boy facing the cupboard")),
}


def visibility(obj, ranges):
    gate = " or ".join(f"({start+1} <= frame < {end+1})" for start,end in ranges)
    for attr in ("hide_render", "hide_viewport"):
        obj.driver_add(attr).driver.expression = "not (" + (gate or "False") + ")"


def build(part, out, path):
    version = "v02" if part == 1 else "v01"
    name = f"part{part}_{version}"
    source = ROOT/"renders"/"one_year_no_wipe"/name
    bpy.ops.wm.open_mainfile(filepath=str(source/f"{name}.blend"))
    scene = bpy.context.scene
    camera = scene.camera
    starts = PORTRAITS[part]
    heads = {}
    for a, _, name in starts:
        scene.frame_set(a+1)
        heads[name] = scene.objects[name+" | head control"]
    proxy = kit.empty("v6 active face or original macro focus",scene.collection)
    tracks = camera.data.animation_data.action.fcurves
    aperture = tracks.find("dof.aperture_fstop")
    records = []
    needs_sun = []
    old_suns = [obj for obj in scene.objects if obj.type=="LIGHT" and obj.data.type=="SUN" and obj.data.use_shadow]
    for f in range(1,scene.frame_end+1):
        scene.frame_set(f)
        name = next((n for a,b,n in starts if a <= f-1 < b),None)
        head = heads.get(name)
        if head:
            proxy.location = head.matrix_world @ Vector((0,-.166,.021))
            stop = 1.6
        else:
            proxy.location = camera.matrix_world @ Vector((0,0,-camera.data.dof.focus_distance))
            stop = camera.data.dof.aperture_fstop
        records.append((f,stop))
        proxy.keyframe_insert("location",frame=f)
        if not any(not light.hide_render for light in old_suns):
            if needs_sun and needs_sun[-1][1]==f-1:
                needs_sun[-1][1]=f
            else:
                needs_sun.append([f-1,f])
    if aperture:
        tracks.remove(aperture)
    kit.apply_portrait_dof(camera,proxy)
    for f,stop in records:
        camera.data.dof.aperture_fstop=stop
        camera.data.keyframe_insert("dof.aperture_fstop",frame=f)
    for name,head in heads.items():
        intervals=[(a,b) for a,b,n in starts if n==name]
        scene.frame_set(intervals[0][0]+1)
        for light in kit.setup_hero_portrait_lighting(head,bg_dim=.68):
            visibility(light,intervals)
    added_suns=[obj for obj in scene.objects if obj.get("ricks_portrait_light")=="Sun"]
    if added_suns:
        visibility(added_suns[0],needs_sun)
    for sun in added_suns[1:]:
        bpy.data.objects.remove(sun,do_unlink=True)
    kit.setup_ricks_compositor(scene,replace=True)
    scene.frame_set(1)
    scene.render.resolution_percentage=100
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(path))
    copy2(source/"shots.json",out/"shots.json")
