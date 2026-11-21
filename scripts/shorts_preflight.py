"""Opt-in pre-render gates for Blender 4.2. No changes on import.

All scene mutations must target a new scene/working copy. A benchmark needs
the repository GPU lock held by its launcher; this library never steals it.
"""
import json
import math
import subprocess
import threading
import time
from pathlib import Path


def visible_triangles(scene):
    """Count evaluated visible instances, including modifier output."""
    import bpy
    if scene != bpy.context.scene:
        raise ValueError('Make the validated scene active before evaluating its geometry')
    deps = bpy.context.evaluated_depsgraph_get()
    total = 0
    for instance in deps.object_instances:
        obj = instance.object
        if obj.type != 'MESH' or obj.hide_render or not instance.show_self:
            continue
        # Collection visibility is represented by the evaluated instance list.
        mesh = obj.to_mesh()
        try:
            mesh.calc_loop_triangles()
            total += len(mesh.loop_triangles)
        finally:
            obj.to_mesh_clear()
    return total


def sanitize_assets(scene, objects, hero_objects=(), target_tris=150000):
    """Sanitize ONLY explicit imported assets, without writing source textures.

    Copies materials/images before scaling. Role 'hero_set' or hero_objects
    selects 1024px; every other imported texture is capped at 512px. Unlinked
    image nodes are removed from copies. Decimation excludes tagged actors.
    Run before rigging and before calibration; inspect the resulting meshes.
    """
    objects = list(objects)
    heroes = {o.name for o in hero_objects}
    images, materials, groups, removed = {}, {}, {}, 0
    def sanitize_tree(tree, cap):
        nonlocal removed
        for node in list(tree.nodes):
            if node.type == 'GROUP' and node.node_tree:
                group_key = (node.node_tree.as_pointer(), cap)
                if group_key not in groups:
                    group = node.node_tree.copy()
                    groups[group_key] = group
                    sanitize_tree(group, cap)
                node.node_tree = groups[group_key]
            if node.type != 'TEX_IMAGE' or not node.image:
                continue
            if not any(output.is_linked for output in node.outputs):
                tree.nodes.remove(node); removed += 1; continue
            imkey = (node.image.as_pointer(), cap)
            if imkey not in images:
                image = node.image.copy()
                w, h = image.size
                if w <= 0 or h <= 0:
                    raise ValueError(f'Missing texture data: {image.name}')
                if max(w, h) > cap:
                    factor = cap/max(w, h)
                    image.scale(max(1, round(w*factor)), max(1, round(h*factor)))
                # Pack capped copies so reopening cannot reload the 4K originals.
                image.pack()
                images[imkey] = image
            node.image = images[imkey]
    for obj in objects:
        if obj.type != 'MESH':
            continue
        obj.data = obj.data.copy()
        cap = 1024 if obj.name in heroes or obj.get('ricks_role') == 'hero_set' else 512
        for slot in obj.material_slots:
            old = slot.material
            if not old:
                continue
            key = (old.as_pointer(), cap)
            if key not in materials:
                mat = old.copy()
                materials[key] = mat
                if mat.use_nodes:
                    sanitize_tree(mat.node_tree, cap)
            slot.material = materials[key]
    before = visible_triangles(scene)
    if before > target_tris:
        candidates = [o for o in objects if o.type == 'MESH' and o.get('ricks_role') not in {'actor', 'ink'}]
        if not candidates:
            raise ValueError('Triangle budget exceeded with no imported meshes eligible for decimation')
        for _ in range(4):
            count = visible_triangles(scene)
            if count <= target_tris:
                break
            for obj in candidates:
                dec = obj.modifiers.get('Pipeline asset budget') or obj.modifiers.new('Pipeline asset budget', 'DECIMATE')
                dec.ratio *= max(.05, min(.95, .92*target_tris/count))
            import bpy
            bpy.context.view_layer.update()
    after = visible_triangles(scene)
    return {'triangles_before': before, 'triangles_after': after, 'target': target_tris,
            'hard_limit': 200000, 'pass': after < 200000,
            'capped_images': len(images), 'unused_image_nodes_removed': removed}


def validate_resources(scene):
    tris = visible_triangles(scene)
    # Pre-render evaluation is a viewport depsgraph. Do not certify an
    # undercount when render-only visibility/modifiers are absent from it.
    mismatches = []
    def collections(collection):
        if collection.hide_viewport and not collection.hide_render:
            mismatches.append('render-only collection: '+collection.name)
        for child in collection.children:
            collections(child)
    collections(scene.collection)
    for obj in scene.objects:
        if obj.hide_render:
            continue
        if obj.hide_viewport or obj.hide_get():
            mismatches.append('render-only object: '+obj.name)
        for mod in obj.modifiers:
            if mod.show_render and (not mod.show_viewport or
                                   (mod.type == 'SUBSURF' and mod.render_levels > mod.levels)):
                mismatches.append('render-only modifier detail: '+obj.name+'/'+mod.name)
    shadowed = [o.name for o in scene.objects if o.type == 'LIGHT' and o.data.type == 'SUN'
                and o.data.use_shadow and not o.hide_render]
    return {'pass': tris < 200000 and len(shadowed) <= 1 and not mismatches,
            'visible_triangles': tris, 'target_exceeded': tris >= 150000, 'shadowed_suns': shadowed,
            'render_evaluation_mismatches': mismatches}


def validate_camera_path(scene, update, obstacles, subjects=(), cuts=(), min_clearance=.30,
                         max_step=1., max_angle=20., max_focus_step=2.):
    """Sample EVERY frame after story update(frame). Diagnostic, not pixel QA.

    Obstacles must include every porch/rail/prop. Rebuild evaluated BVHs each
    frame so moving props are tested too. Exclude intentional cut destinations
    only via explicit 1-based cuts. Subjects are (object, start, end) inclusive;
    omit intentionally cropped subjects, documenting them in the shot manifest.
    Review speed thresholds per shot; a fast authored whip can trigger a flag.
    """
    import bpy
    from mathutils.bvhtree import BVHTree
    from bpy_extras.object_utils import world_to_camera_view
    if scene != bpy.context.scene:
        raise ValueError('Make the validated scene active before checking its camera')
    obstacles, subjects, cuts = list(obstacles), list(subjects), set(cuts)
    if not obstacles:
        return {'status': 'UNVERIFIED', 'reason': 'No collision meshes declared'}
    original, issues, previous = scene.frame_current, [], None
    try:
        for frame in range(scene.frame_start, scene.frame_end+1):
            scene.frame_set(frame); update(frame); bpy.context.view_layer.update()
            deps = bpy.context.evaluated_depsgraph_get()
            cam = scene.camera.evaluated_get(deps)
            position = cam.matrix_world.translation.copy()
            focus = cam.data.dof.focus_object
            focus_distance = ((focus.matrix_world.translation-position).length if focus else cam.data.dof.focus_distance)
            state = (position, cam.matrix_world.to_quaternion(), cam.data.lens, focus_distance)
            if previous and frame not in cuts:
                delta = (position-previous[0]).length
                angle = math.degrees(state[1].rotation_difference(previous[1]).angle)
                if delta > max_step or angle > max_angle or abs(state[2]-previous[2]) > .01 or abs(state[3]-previous[3]) > max_focus_step:
                    issues.append({'frame': frame, 'kind': 'continuity', 'step_m': delta, 'angle_deg': angle,
                                   'lens_delta': state[2]-previous[2], 'focus_delta': state[3]-previous[3]})
            previous = state
            trees = []
            for obstacle in obstacles:
                if obstacle.hide_render:
                    continue
                evaluated = obstacle.evaluated_get(deps)
                mesh = evaluated.to_mesh()
                try:
                    verts = [evaluated.matrix_world @ v.co for v in mesh.vertices]
                    faces = [tuple(p.vertices) for p in mesh.polygons]
                    if faces:
                        trees.append((obstacle.name, BVHTree.FromPolygons(verts, faces)))
                finally:
                    evaluated.to_mesh_clear()
            for name, tree in trees:
                nearest = tree.find_nearest(position)
                # Signed nearest distance also catches a camera deep INSIDE a
                # closed outward-facing obstacle, not just near its surface.
                inside = nearest[0] is not None and (position-nearest[0]).dot(nearest[1]) < -1e-6
                if nearest[0] is not None and (nearest[3] < min_clearance or inside):
                    issues.append({'frame': frame, 'kind': 'camera_clearance', 'object': name,
                                   'distance_m': nearest[3], 'inside': inside})
            for obj, start, end in subjects:
                if not start <= frame <= end:
                    continue
                evaluated = obj.evaluated_get(deps)
                bounds = [world_to_camera_view(scene, cam, evaluated.matrix_world @ __import__('mathutils').Vector(v))
                          for v in evaluated.bound_box]
                if any(p.z <= 0 or not (0 <= p.x <= 1 and 0 <= p.y <= 1) for p in bounds):
                    issues.append({'frame': frame, 'kind': 'subject_out_of_frame', 'object': obj.name})
                target = evaluated.matrix_world.translation
                ray = target-position
                for name, tree in trees:
                    hit = tree.ray_cast(position, ray.normalized(), max(0, ray.length-.05))
                    if hit[0] is not None:
                        issues.append({'frame': frame, 'kind': 'subject_occlusion', 'object': obj.name, 'occluder': name})
    finally:
        scene.frame_set(original); update(original)
    return {'status': 'PASS' if not issues else 'REVIEW', 'frames_checked': scene.frame_end-scene.frame_start+1,
            'clearance_m': min_clearance, 'issues': issues}


def benchmark(scene, frames, output_dir, update=lambda frame: None, *,
              resolution=(1080, 1920, 100), p95_limit=1.8, max_limit=2.0):
    """12 DISTINCT native frames, one warmup, wall time + sampled BOARD VRAM.

    Caller owns GPU lock. Whole-board memory is conservative; unknown telemetry
    fails verification. Samples can miss brief peaks: this is a sampled gate,
    not proof of a hard allocation ceiling. Do not substitute faster retries.
    """
    import bpy
    frames = sorted(set(frames))
    if len(frames) != 12 or frames[0] < scene.frame_start or frames[-1] > scene.frame_end:
        raise ValueError('Exactly 12 distinct in-range frames required')
    if (scene.render.resolution_x, scene.render.resolution_y, scene.render.resolution_percentage) != tuple(resolution):
        raise ValueError(f'Benchmark requires Blender resolution settings {resolution}')
    output = Path(output_dir)
    output.mkdir(parents=True, exist_ok=True)
    if any(output.iterdir()):
        raise ValueError('Use a fresh benchmark directory; never replace previous measurements')
    memory, errors, stop = [], [], threading.Event()
    def poll():
        while not stop.is_set():
            try:
                result = subprocess.run(['nvidia-smi', '--query-gpu=memory.used', '--format=csv,noheader,nounits'],
                                        capture_output=True, text=True, check=True, timeout=3,
                                        creationflags=getattr(subprocess, 'CREATE_NO_WINDOW', 0))
                memory.append(max(float(x) for x in result.stdout.splitlines())/1024)
            except (OSError, ValueError, subprocess.SubprocessError) as exc:
                errors.append(str(exc)); return
            stop.wait(.2)
    settings = scene.frame_current, scene.render.filepath, scene.render.image_settings.file_format
    thread = threading.Thread(target=poll, daemon=True); thread.start()
    timings = []
    try:
        scene.render.image_settings.file_format = 'PNG'
        scene.frame_set(frames[0]); update(frames[0]); bpy.ops.render.render(write_still=False)
        for frame in frames:
            start = time.perf_counter()
            scene.frame_set(frame); update(frame)
            scene.render.filepath = str(output/f'frame_{frame:04d}.png')
            bpy.ops.render.render(write_still=True)
            timings.append({'frame': frame, 'seconds': time.perf_counter()-start})
    finally:
        stop.set(); thread.join(timeout=4)
        scene.frame_set(settings[0]); update(settings[0])
        scene.render.filepath, scene.render.image_settings.file_format = settings[1:]
    values = sorted(x['seconds'] for x in timings)
    rank = .95*(len(values)-1)
    lo, hi = math.floor(rank), math.ceil(rank)
    p95, maximum = values[lo]+(values[hi]-values[lo])*(rank-lo), max(values)
    peak = max(memory) if memory else None
    report = {'status': 'PASS' if p95 <= p95_limit and maximum <= max_limit and peak is not None and peak <= 3.3 else 'FAIL',
              'timings': timings, 'p95_seconds': p95, 'p95_method': 'linear', 'max_seconds': maximum,
              'sampled_board_peak_gib': peak, 'telemetry_samples': len(memory), 'telemetry_errors': errors,
              'resources': validate_resources(scene), 'resolution': [size * resolution[2] // 100 for size in resolution[:2]],
              'limits': {'p95_seconds': p95_limit, 'max_seconds': max_limit, 'sampled_board_gib': 3.3}}
    if not report['resources']['pass']:
        report['status'] = 'FAIL'
    (output/'benchmark.json').write_text(json.dumps(report, indent=2), encoding='utf-8')
    return report
