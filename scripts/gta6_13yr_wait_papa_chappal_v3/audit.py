"""Audit the complete narrative timeline without saving or rendering the master."""
import hashlib
import json
import math
from collections import Counter
from pathlib import Path

import bpy
import numpy as np
from bpy_extras.object_utils import world_to_camera_view
from mathutils import Vector
from mathutils.bvhtree import BVHTree

import shorts_preflight

MIN_CAMERA_GAP = .30
CONTACT_TOLERANCE = .003
GEOMETRY_TYPES = {'MESH', 'CURVE', 'FONT', 'SURFACE', 'META', 'CURVES', 'POINTCLOUD', 'VOLUME'}
# Runtime changes spline points on limbs, not merely the transform of the curve.
LIVE_CURVES = {
    f'{actor} {part} {side}'
    for actor in ('Pawn Gamer', 'Gamer', 'Papa', 'Beach walker')
    for part in ('arm', 'leg', 'sleeve', 'cuff')
    for side in (-1, 1)
}

def curve_bounds(obj):
    """A POLY curve's bevel tube fits inside the control bounds plus radius."""
    data = obj.data
    if data.bevel_object or data.taper_object or data.extrude or data.offset:
        return None
    if not data.splines or any(spline.type != 'POLY' for spline in data.splines):
        return None
    points = []
    radius = data.bevel_depth
    triangle_bound = 0
    # Circle segments are bounded conservatively for the simple round bevel.
    sides = 4 + 4*data.bevel_resolution
    for spline in data.splines:
        points.extend(point.co[:3] for point in spline.points)
        radius = max(radius, data.bevel_depth*max((point.radius for point in spline.points), default=1))
        spans = len(spline.points) - int(not spline.use_cyclic_u)
        triangle_bound += max(0, spans)*2*sides
        if data.use_fill_caps and not spline.use_cyclic_u:
            triangle_bound += 2*max(0, sides-2)
    if not points:
        return None
    coordinates = np.asarray(points, dtype=np.float64)
    return coordinates.min(axis=0)-radius, coordinates.max(axis=0)+radius, triangle_bound

def local_geometry(obj, deps):
    if obj.type == 'CURVE' and not obj.modifiers:
        poly_geometry = curve_bounds(obj)
        if poly_geometry is not None:
            return poly_geometry
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    try:
        if mesh is None or not mesh.vertices:
            return None
        coordinates = np.empty(len(mesh.vertices)*3, dtype=np.float32)
        mesh.vertices.foreach_get('co', coordinates)
        coordinates = coordinates.reshape(-1, 3)
        mesh.calc_loop_triangles()
        return coordinates.min(axis=0), coordinates.max(axis=0), len(mesh.loop_triangles)
    finally:
        evaluated.to_mesh_clear()

def inside_closed_mesh(tree, faces, point):
    edges = Counter()
    for face in faces:
        edges.update(tuple(sorted((a,b))) for a,b in zip(face, (*face[1:],face[0])))
    if not edges or any(total != 2 for total in edges.values()):
        return False
    direction = Vector((.98314,.13211,.12539)).normalized()
    hits = 0
    travel = 0.0
    limit = 80.0  # Both physical sets fit inside this distance from any camera.
    while travel < limit:
        location, _, _, distance = tree.ray_cast(point+direction*travel, direction, limit-travel)
        if location is None:
            break
        hits += 1
        travel += distance+.00005
    return hits % 2 == 1

def exact_camera_gap(obj, deps, point, within_bbox):
    evaluated = obj.evaluated_get(deps)
    mesh = evaluated.to_mesh()
    try:
        if mesh is None or not mesh.polygons:
            return None, False
        matrix = evaluated.matrix_world
        vertices = [matrix@vertex.co for vertex in mesh.vertices]
        faces = [tuple(face.vertices) for face in mesh.polygons]
        tree = BVHTree.FromPolygons(vertices,faces)
        location, _, _, distance = tree.find_nearest(point)
        if location is None:
            return None, False
        return distance, within_bbox and inside_closed_mesh(tree,faces,point)
    finally:
        evaluated.to_mesh_clear()

def contact_anchor(shot,actor,side,frame,objects,deps):
    """Resolve authored semantic fixtures independently of the solved hand."""
    if actor == 'Pawn Gamer':
        if side == 1:
            time=(frame-1)/30
            if time<7.8:return fixture_world(objects,deps,'Cooler handle anchor')
            if time<9.0:return fixture_world(objects,deps,'Old cracked phone',(.057,-.014,.042))
            return fixture_world(objects,deps,'Mothers bangles',(.081,-.008,.061))
    if actor == 'Gamer':
        if shot == 'latch':
            return fixture_world(objects,deps,'Door hand latch anchor')
        if shot == 'chips':
            return fixture_world(objects,deps,'Bag left seam grip' if side == -1 else 'Bag right seam grip')
        if shot in ('start','beach','keys'):
            if side == -1:
                return fixture_world(objects,deps,'RGB mouse grip',(0,-.002,.055))
            if shot != 'keys':
                return fixture_world(objects,deps,'Enter key',(0,0,.044))
            _,left=fixture_world(objects,deps,'ALT key',(0,0,.044))
            _,right=fixture_world(objects,deps,'TAB key',(0,0,.041))
            blend=.5+.5*math.sin(((frame-1)/30-40.36)*38)
            return 'ALT/TAB key cluster',left.lerp(right,blend)
    if actor == 'Papa' and side == -1:
        return fixture_world(objects,deps,'Papa right chappal hand seat')
    return None

def fixture_world(objects,deps,name,local=(0,0,0)):
    return name,objects[name].evaluated_get(deps).matrix_world@Vector(local)

def register_receiver(scene, cam, deps):
    """Register an upper stucco patch away from flying calendar pages."""
    corners = [Vector((-22+x,2.149,z)) for x in (-1.06,-.87) for z in (2.70,2.88)]
    for target in corners:
        origin = cam.matrix_world.translation
        ray = target-origin
        result, _, _, _, hit, _ = scene.ray_cast(deps,origin,ray.normalized(),distance=ray.length+.01)
        if not result or hit.name != 'Pawn rear stucco':
            return None
    points=[world_to_camera_view(scene,cam,point) for point in corners]
    rectangle=[min(p.x for p in points),1-max(p.y for p in points),
               max(p.x for p in points),1-min(p.y for p in points)]
    if min(p.z for p in points) <= 0 or not all(0 <= a <= 1 for a in rectangle):
        return None
    if rectangle[2]-rectangle[0] < .035 or rectangle[3]-rectangle[1] < .025:
        return None
    return rectangle

def run(runtime, output, source):
    """Check evaluated world clearance, cut continuity, semantic grips and budget."""
    scene=bpy.context.scene
    output=Path(output)
    source=Path(source)
    manifest=json.loads((output/'shots.json').read_text(encoding='utf-8-sig'))
    is_cut={f+1 for f in manifest['cuts'] if f not in manifest.get('continuous_junctions', [])}
    objects={obj.name:obj for obj in scene.objects}
    obstacles=[o for o in objects.values() if o.type in GEOMETRY_TYPES]
    animated={o.name for o in obstacles if o.name in LIVE_CURVES or o.modifiers
              or getattr(o.data,'shape_keys',None)}
    bounds_cache={}
    issues=[]
    issue_counts=Counter()
    closest=float('inf')
    tightest=[]
    max_tris=0
    max_mesh_only=0
    max_grip_delta=0
    reach_peak={}
    contact_counts=Counter()
    max_deltas={'distance_m':0.0,'rotation_deg':0.0,'focus_m':0.0}
    previous=None
    shadow_regions={}
    exact_tests=0
    initial_frame=scene.frame_current
    render_only=set()
    excessive_suns=[]
    camera_grip_frames=Counter()
    out_of_frame_grips=Counter()

    def flag(kind, frame, **evidence):
        issue_counts[kind]+=1
        if len(issues)<300:
            issues.append({'kind':kind,'frame':frame,**evidence})

    for frame in range(scene.frame_start, scene.frame_end+1):
        scene.frame_set(frame)
        runtime.update(frame)
        bpy.context.view_layer.update()
        deps=bpy.context.evaluated_depsgraph_get()
        camera=scene.camera.evaluated_get(deps)
        point=camera.matrix_world.translation
        orientation=camera.matrix_world.to_quaternion()
        focus=camera.data.dof.focus_object
        focus_distance=(focus.matrix_world.translation-point).length if focus else camera.data.dof.focus_distance
        shot=str(scene['shot'])
        state=(point,orientation,camera.data.lens,focus_distance)
        if previous and frame not in is_cut:
            move=(point-previous[0]).length
            turn=math.degrees(orientation.rotation_difference(previous[1]).angle)
            turn=min(turn,abs(360.0-turn))
            focus_move=abs(focus_distance-previous[3])
            lens_jump=abs(state[2]-previous[2])
            max_deltas['distance_m']=max(move,max_deltas['distance_m'])
            max_deltas['rotation_deg']=max(turn,max_deltas['rotation_deg'])
            max_deltas['focus_m']=max(focus_move,max_deltas['focus_m'])
            if move>.50 or turn>12. or focus_move>.70 or lens_jump>.01:
                flag('camera_continuity',frame,shot=shot,distance_m=move,angle_deg=turn,focus_delta_m=focus_move,lens_delta=lens_jump)
        previous=state
        active=[]
        centers=[]
        extents=[]
        transforms=[]
        total=0
        mesh_total=0
        for obj in obstacles:
            if obj.hide_render:
                continue
            if obj.hide_viewport or obj.hide_get():
                render_only.add(obj.name)
                continue
            name=obj.name
            if name in bounds_cache and name not in animated:
                geometry=bounds_cache[name]
            else:
                geometry=local_geometry(obj,deps)
                if name not in animated:
                    bounds_cache[name]=geometry
            if geometry is None:
                flag('missing_visible_geometry',frame,shot=shot,object=name,type=obj.type)
                continue
            lower,upper,triangles=geometry
            total+=triangles
            if obj.type=='MESH':
                mesh_total+=triangles
            active.append(obj)
            centers.append((lower+upper)*.5)
            extents.append((upper-lower)*.5)
            transforms.append(np.asarray(obj.matrix_world,dtype=np.float64))
        if not active:
            flag('empty_visible_geometry',frame,shot=shot)
            continue
        max_tris=max(total,max_tris)
        max_mesh_only=max(mesh_total,max_mesh_only)
        matrices=np.stack(transforms)
        center=np.einsum('nij,nj->ni',matrices[:,:3,:3],np.asarray(centers))+matrices[:,:3,3]
        radius=np.einsum('nij,nj->ni',np.abs(matrices[:,:3,:3]),np.asarray(extents))
        rel=np.abs(np.asarray(point)-center)-radius
        distances=np.linalg.norm(rel.clip(min=0),axis=1)
        for i in np.nonzero(distances<MIN_CAMERA_GAP)[0]:
            obj=active[i]
            exact_tests+=1
            exact,inside=exact_camera_gap(obj,deps,point,bool((rel[i]<=0).all()))
            if exact is None:
                flag('camera_bounds_unresolved',frame,shot=shot,object=obj.name,bound_m=float(distances[i]))
                continue
            distances[i]=exact
            if inside or exact+1e-6 < MIN_CAMERA_GAP:
                flag('camera_clearance',frame,shot=shot,object=obj.name,distance_m=exact,camera_inside=inside)
        i=int(distances.argmin())
        gap=float(distances[i])
        closest=min(gap,closest)
        tightest.append((gap,frame,shot,active[i].name))
        for key, requested in runtime.CONTACTS.items():
            actor,side=key
            hand=objects[f'{actor} hand {side}']
            arm=objects[f'{actor} arm {side}']
            if hand.hide_render:
                continue
            expected=contact_anchor(shot,actor,side,frame,objects,deps)
            if expected is None:
                # Additional runtime contacts remain measurable even when they
                # do not carry an independently named fixture in this version.
                point_ref=Vector(requested)
                fixture='runtime-only target'
                local_check=False
            else:
                fixture,point_ref=expected
                local_check=True
            actual=hand.evaluated_get(deps).matrix_world.translation
            matrix=arm.evaluated_get(deps).matrix_world
            points=arm.data.splines[0].points
            arm_end=matrix@Vector(points[-1].co[:3])
            shoulder=matrix@Vector(points[0].co[:3])
            error=max((actual-point_ref).length,(arm_end-actual).length)
            max_grip_delta=max(error,max_grip_delta)
            label=f'{shot}:{actor} {side}:{fixture}'
            contact_counts[label]+=1
            reach_peak[label]=max((actual-shoulder).length,reach_peak.get(label,0))
            if error>CONTACT_TOLERANCE:
                flag('grip_contact',frame,shot=shot,actor=actor,hand=side,fixture=fixture,error_m=error,
                     independent_fixture_check=local_check)
            if shot in ('latch','chips','keys','shoe','boss'):
                uv=world_to_camera_view(scene,camera,actual)
                camera_grip_frames[label]+=1
                if not (.02 <= uv.x <= .98 and .02 <= uv.y <= .98 and uv.z > 0):
                    out_of_frame_grips[label]+=1
        shadow_lights=sum(1 for o in objects.values()
                          if o.type=='LIGHT' and not o.hide_render and o.data.type=='SUN' and o.data.use_shadow)
        if shadow_lights>1:
            excessive_suns.append(frame)
        if frame<=11 and shot=='wait':
            crop=register_receiver(scene,camera,deps)
            if crop is not None:
                shadow_regions[str(frame-1)]=[crop]
        if frame%150==0 or frame==scene.frame_end:
            print(f'AUDIT_FRAME {frame}/{scene.frame_end}; closest {closest:.3f}m; flags {dict(issue_counts)}',
                  flush=True)

    for name in sorted(render_only):
        flag('viewport_render_visibility_mismatch',None,object=name)
    if excessive_suns:
        flag('shadowed_sun_budget',excessive_suns[0],affected_frames=len(excessive_suns))
    if max_tris>=200_000:
        flag('triangle_budget',None,visible_triangle_upper_bound=max_tris)
    images={}
    for image in bpy.data.images:
        if image.type in ('RENDER_RESULT','COMPOSITING') or image.users==0:
            continue
        w,h=image.size[:]
        images[image.name]=[w,h]
        # This production has authored fixtures rather than imported hero maps.
        if not (0<w<=512 and 0<h<=512):
            flag('texture_budget',None,image=image.name,size=[w,h])

    examples=[]
    seen=set()
    for distance,frame,shot,obj in sorted(tightest):
        if (shot,obj) in seen:
            continue
        seen.add((shot,obj))
        examples.append(dict(distance_m=distance,frame=frame,shot=shot,object=obj))
        if len(examples)>=12:
            break
    if len(shadow_regions)==11:
        manifest['shadow_checks']=[{'name':'Opening upper pawn stucco before calendar motion',
             'start':0,'end':11,'registration':'tracked','regions_by_frame':shadow_regions,
             'max_adjacent_luma':1.0}]
        (output/'shots.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')

    resource=shorts_preflight.validate_resources(scene)
    if not resource['pass']:
        flag('resource_validation',scene.frame_current,report=resource)
    report={'pass':not issue_counts,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'frames_checked':scene.frame_end-scene.frame_start+1,'minimum_camera_clearance_m':closest,
        'camera_clearance_budget_m':MIN_CAMERA_GAP,'camera_clearance_samples':examples,
        'camera_geometry_method':'Conservative active-object world AABB; evaluated triangle BVH for near bounds',
        'exact_bvh_tests':exact_tests,'maximum_uncut_camera_deltas':max_deltas,
        'maximum_visible_triangle_upper_bound':max_tris,'maximum_visible_mesh_triangles':max_mesh_only,
        'texture_budget_context':'No imported hero or prop texture in this procedural scene',
        'image_dimensions':images,'contact_frames_by_fixture':dict(contact_counts),'maximum_grip_error_m':max_grip_delta,
        'maximum_reach_m_by_fixture':reach_peak,'grip_crop_review':dict(out_of_frame_grips),
        'grip_projected_frames':dict(camera_grip_frames),
        'shadow_registered_frames':len(shadow_regions),'issue_counts':dict(issue_counts),'issues':issues}
    (output/'audit.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
    scene.frame_set(initial_frame)
    runtime.update(initial_frame)
    return report
