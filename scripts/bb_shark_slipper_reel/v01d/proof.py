"""Native performance gate and review stills for the saved courtyard scene."""
import hashlib
import json
from pathlib import Path
from uuid import uuid4
import sys

import bpy
from mathutils import Vector
from mathutils.bvhtree import BVHTree
from bpy_extras.object_utils import world_to_camera_view

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/bb_shark_slipper_reel/v01d"
sys.path[:0]=[str(HERE),str(ROOT/"scripts")]
import ricks_v2_kit as k
import shorts_preflight as gate
from build import AIR_GRIP, THIRD, THOUGHT, FLIGHT, TURF_Z, scout_route

CH=json.loads((OUT/"choreography.json").read_text())
CAL=CH["calibration_frames"]
SILENT=CH["silent_start"]
HIT=CH["contact_frame"]
PROOF_IDS=(CAL[0],CAL[2],CAL[4],HIT+18)
CAL_LABELS=("Scheme by the shark","Hood flip","Fake victim shiver","Mask slips",
            "Scout enters","Silent side-eye","Slipper wind-up","Flight tracking",
            "Sole meets face","Hurt and dizzy pullback")


def render_frame(scene,path):
    scene.render.filepath=str(path)
    bpy.ops.render.render(write_still=True)


def contact_check(scene):
    details={}
    scene.frame_set(HIT)
    dg=bpy.context.evaluated_depsgraph_get()
    love=bpy.data.objects["Love | ellipsoid head"].evaluated_get(dg)
    slipper=bpy.data.objects["Flying slipper • tan leather"].evaluated_get(dg)
    face_contact=slipper.matrix_world@Vector(CH["impact_sole_socket_local"])
    obj_loc=love.matrix_world.inverted()@face_contact
    closest,*_=BVHTree.FromObject(love,dg).find_nearest(obj_loc)
    error=(love.matrix_world@closest-face_contact).length
    details["impact_surface_separation_mm"]=round(error*1000,4)
    details["frame"]=HIT
    details["contact_world"]=list(face_contact)
    details["impact_obliquity_degrees"]=CH["impact_obliquity_degrees"]
    hood=bpy.data.objects["Love | draped pointed wool hood"]
    hood_tree=world_bvh(hood,dg)
    details["hood_prop_mesh_intersections"]=sum(
        len(hood_tree.overlap(world_bvh(piece,dg))) for piece in slipper.original.children
        if piece.type in ("MESH","CURVE"))
    grips=[]
    for f in range(SILENT+16,FLIGHT+1):
        scene.frame_set(f)
        dg=bpy.context.evaluated_depsgraph_get()
        arm=bpy.data.objects["Scout | round-tipped arm R"].evaluated_get(dg)
        sandal=bpy.data.objects["Flying slipper • tan leather"].evaluated_get(dg)
        hand=arm.matrix_world@arm.data.splines[0].bezier_points[2].co
        grips.append((hand-sandal.matrix_world@AIR_GRIP).length)
    details["grip_samples"]=len(grips)
    details["max_grip_separation_mm"]=round(max(grips)*1000,4)
    planted=[]
    for f in range(THIRD,THOUGHT):
        scene.frame_set(f)
        dg=bpy.context.evaluated_depsgraph_get()
        w=k.eval_stick_walk_cycle(f,scout_route,0.,start_frame=THIRD-3,
                                 stop_frame=SILENT-6,plant_yaw=-.11)
        for j,side in enumerate(("L","R")):
            if w.planted[j]:
                foot=bpy.data.objects[f"Scout | foot tick {side}"].evaluated_get(dg)
                planted.append((foot.matrix_world.translation-Vector(w.feet_world[j])).length)
    details["planted_foot_samples"]=len(planted)
    details["max_plant_anchor_separation_mm"]=round(max(planted)*1000,4)
    grounded=[]
    pieces=("Love | graphic pill torso","Love | foot tick L","Love | foot tick R")
    for f in (CAL[0],CAL[1],CAL[2],CAL[5],HIT,HIT+18,CAL[-1]):
        scene.frame_set(f)
        dg=bpy.context.evaluated_depsgraph_get()
        offsets={}
        for name in pieces:
            obj=bpy.data.objects[name].evaluated_get(dg)
            offsets[name]=round(1000*(min((obj.matrix_world@v.co).z for v in obj.data.vertices)-TURF_Z),4)
        grounded.append({"frame":f,"bottom_to_turf_mm":offsets})
    details["seating_samples"]=grounded
    margin_frame=CAL[6]
    scene.frame_set(margin_frame)
    dg=bpy.context.evaluated_depsgraph_get()
    airborne=bpy.data.objects["Flying slipper • tan leather"]
    throwing=bpy.data.objects["Scout | round-tipped arm R"]
    projected=[]
    camera=scene.camera.evaluated_get(dg)
    for original in (throwing,*airborne.children_recursive):
        if original.type not in ("MESH","CURVE"):
            continue
        obj=original.evaluated_get(dg)
        mesh=obj.to_mesh()
        try:
            points=[world_to_camera_view(scene,camera,obj.matrix_world@v.co) for v in mesh.vertices]
        finally:
            obj.to_mesh_clear()
        if points:
            projected.extend(points)
    assert all(p.z>0 for p in projected)
    margin=[float(min(p.x for p in projected)),float(1-max(p.x for p in projected)),
            float(min(p.y for p in projected)),float(1-max(p.y for p in projected))]
    details["wind_up_frame"]=margin_frame
    details["wind_up_arm_and_slipper_margins_l_r_b_t"]=margin
    details["status"]="PASS" if (error<.001 and max(grips)<.001 and max(planted)<.001
                                and not details["hood_prop_mesh_intersections"]
                                and min(margin)>=.035
                                and max(abs(v) for row in grounded for v in row["bottom_to_turf_mm"].values())<.5
                               ) else "REVIEW"
    (OUT/"contact_check.json").write_text(json.dumps(details,indent=2))
    print("CONTACT_CHECK",details,flush=True)
    return details


def world_bvh(obj,deps):
    evaluated=obj.evaluated_get(deps)
    mesh=evaluated.to_mesh()
    try:
        return BVHTree.FromPolygons([evaluated.matrix_world@v.co for v in mesh.vertices],
                                    [tuple(p.vertices) for p in mesh.polygons])
    finally:
        evaluated.to_mesh_clear()


def camera_clearance(scene):
    scene.frame_set(1)
    deps=bpy.context.evaluated_depsgraph_get()
    obstacles=[]
    collection=bpy.data.collections["Courtyard • one connected physical set"]
    for obj in collection.objects:
        if obj.type not in {"MESH","CURVE"} or not obj.visible_shadow or " • ink" in obj.name:
            continue
        ev=obj.evaluated_get(deps)
        coords=[ev.matrix_world@Vector(p) for p in ev.bound_box]
        minimum=Vector(tuple(min(p[i] for p in coords) for i in range(3)))
        maximum=Vector(tuple(max(p[i] for p in coords) for i in range(3)))
        obstacles.append((obj.name,ev,minimum,maximum))
    trees={}
    minimum=(float("inf"),None,None)
    for index,pos in CH["camera_positions"].items():
        pos=Vector(pos)
        for name,ev,lo,hi in obstacles:
            bound=(sum(max(lo[i]-pos[i],pos[i]-hi[i],0)**2 for i in range(3)))**.5
            if bound>=min(minimum[0],1.1):
                continue
            if name not in trees:
                mesh=ev.to_mesh()
                try:
                    points=[ev.matrix_world@v.co for v in mesh.vertices]
                    faces=[tuple(face.vertices) for face in mesh.polygons]
                    trees[name]=BVHTree.FromPolygons(points,faces) if faces else None
                finally:
                    ev.to_mesh_clear()
            if trees[name]:
                nearest=trees[name].find_nearest(pos)
                if nearest[0] is not None and nearest[3]<minimum[0]:
                    minimum=(nearest[3],int(index),name)
    result={"status":"PASS" if minimum[0]>=.30 else "REVIEW","frames_checked":scene.frame_end,
            "obstacles":len(obstacles),"minimum_clearance_m":minimum[0],
            "closest_frame":minimum[1],"closest_object":minimum[2]}
    (OUT/"camera_clearance.json").write_text(json.dumps(result,indent=2))
    print("CAMERA_CLEARANCE",result,flush=True)
    return result


def lookdev(scene,out,scale):
    cam=bpy.data.objects.new("Lookdev camera • session only",bpy.data.cameras.new("Lookdev 36 mm"))
    scene.collection.objects.link(cam)
    scene.camera=cam
    scene.render.resolution_percentage=scale
    for i,(name,f,p,t,lens) in enumerate((
        ("love_scheme",PROOF_IDS[0],(-2.15,-2.32,.61),(-1.90,-.34,.49),39),
        ("love_hood",PROOF_IDS[1],(-1.62,-1.88,.57),(-1.91,-.44,.47),41),
        ("scout_walk",PROOF_IDS[2],(1.03,1.46,1.29),(1.60,3.41,1.18),48),
        ("love_dizzy",PROOF_IDS[3],(-1.64,-1.74,.56),(-1.86,-.39,.53),44),
    )):
        scene.frame_set(f)
        p,t=Vector(p),Vector(t)
        k.setup_ricks_camera(cam,lens=lens,fstop=4.4 if i==2 else 3.1)
        cam.location=p
        k.aim(cam,t)
        bpy.context.view_layer.update()
        k.set_ricks_camera_focus(cam,t)
        render_frame(scene,out/(name+".png"))


def main():
    scene=bpy.context.scene
    cast_materials={material for name in ("Love","Scout")
                    for obj in bpy.data.objects[name].children_recursive if obj.type in ("MESH","CURVE")
                    for material in obj.data.materials if material and material.use_nodes}
    cast_principled=[node for mat in cast_materials for node in mat.node_tree.nodes
                     if node.type=="BSDF_PRINCIPLED"]
    assert all(node.inputs["Specular IOR Level"].default_value==0.
               and node.inputs["Roughness"].default_value==1. for node in cast_principled)
    contacts=contact_check(scene)
    clearance=camera_clearance(scene)
    preview=sys.argv[-1]=="preview"
    if preview:
        out=OUT/"preview"
        out.mkdir(exist_ok=True)
        scene.render.resolution_percentage=42
        for f in CAL:
            scene.frame_set(f)
            render_frame(scene,out/f"frame_{f:04}.png")
        lookdev(scene,out,42)
        return
    out=OUT/"benchmark"
    if out.exists():
        out=OUT/f"benchmark_{uuid4().hex[:8]}"
    scene.render.resolution_percentage=100
    all_frames=sorted(set((1,*CAL,HIT+1)))
    if len(all_frames)!=12:
        raise ValueError("Benchmark requires 12 distinct frames")
    counts={}
    for f in all_frames:
        scene.frame_set(f)
        counts[f]=gate.validate_resources(scene)
    max_tri=max(v["visible_triangles"] for v in counts.values())
    print("RESOURCE_TRIANGLE_MAX",max_tri,flush=True)
    report=gate.benchmark(scene,all_frames,out,p95_limit=1.8,max_limit=2.)
    if (max_tri>=150000 or not all(s["pass"] for s in counts.values())
        or clearance["status"]!="PASS" or contacts["status"]!="PASS"):
        report["status"]="FAIL"
    report["resources_per_frame"]=counts
    report["max_evaluated_triangles"]=max_tri
    report["native_stills_dir"]=out.name
    report["matte_cast_principled_shaders"]=len(cast_principled)
    with (OUT/"bb_shark_slipper_v01d.blend").open("rb") as f:
        report["blend_sha256"]=hashlib.file_digest(f,"sha256").hexdigest()
    (OUT/"benchmark.json").write_text(json.dumps(report,indent=2))
    lookdev_path=OUT/"lookdev"
    lookdev_path.mkdir(exist_ok=True)
    lookdev(scene,lookdev_path,72)


main()
