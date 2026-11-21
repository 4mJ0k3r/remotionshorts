"""Blender-only construction regression checks; NEVER renders/saves production."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]/'scripts'))
import bpy
from mathutils import Vector
import ricks_lookdev as look
import shorts_preflight as gate

s = look.setup_scene(bpy.context.scene, frame_end=3)
assert bpy.data.objects['Light'].hide_render, 'Factory point light polluted 4:1 rig'
bpy.data.objects.remove(bpy.data.objects['Cube'], do_unlink=True)
bpy.ops.mesh.primitive_cube_add(location=(8, 0, 1))
wall = bpy.context.object
wall.name = 'Test collision cube'
mat = bpy.data.materials.new('Imported material'); mat.use_nodes = True
node = mat.node_tree.nodes.new('ShaderNodeTexImage')
source_image = bpy.data.images.new('Original 2K source', width=2048, height=1024)
node.image = source_image
mat.node_tree.links.new(node.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
wall.data.materials.append(mat)
loose = mat.node_tree.nodes.new('ShaderNodeTexImage'); loose.image = source_image
count = gate.visible_triangles(s)
assert count == 12, count
report = gate.sanitize_assets(s, [wall])
assert report['pass'] and report['unused_image_nodes_removed'] == 1
copy = next(n.image for n in wall.data.materials[0].node_tree.nodes if n.type == 'TEX_IMAGE')
assert tuple(copy.size) == (512, 256) and copy.packed_file
assert tuple(source_image.size) == (2048, 1024), 'Source image changed'
# Nested imported shader groups must be copied/capped too, including hero caps.
group = bpy.data.node_groups.new('Imported shader group', 'ShaderNodeTree')
group.interface.new_socket(name='Color', in_out='OUTPUT', socket_type='NodeSocketColor')
image_node = group.nodes.new('ShaderNodeTexImage'); image_node.image = source_image
group_out = group.nodes.new('NodeGroupOutput')
group.links.new(image_node.outputs['Color'], group_out.inputs['Color'])
group_node = mat.node_tree.nodes.new('ShaderNodeGroup'); group_node.node_tree = group
mat.node_tree.links.new(group_node.outputs['Color'], mat.node_tree.nodes.get('Principled BSDF').inputs['Base Color'])
bpy.ops.mesh.primitive_cube_add(location=(14, 0, 0)); hero = bpy.context.object
hero.data.materials.append(mat)
gate.sanitize_assets(s, [hero], hero_objects=[hero])
new_group = next(n.node_tree for n in hero.data.materials[0].node_tree.nodes if n.type == 'GROUP')
assert new_group != group and tuple(new_group.nodes.get(image_node.name).image.size) == (1024, 512)
assert tuple(group.nodes.get(image_node.name).image.size) == (2048, 1024)
# A second eligible asset exercises the decimation branch; never decimate actors.
bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, location=(12, 0, 0))
asset = bpy.context.object
report = gate.sanitize_assets(s, [asset], target_tris=1000)
assert report['triangles_after'] <= 1000, report
assert gate.validate_resources(s)['pass']
asset.hide_viewport = True
assert not gate.validate_resources(s)['pass'], 'Render-only mesh undercount was certified'
asset.hide_viewport = False

def safe(frame):
    s.camera.location = (0, -6, 2)
    s.camera.rotation_euler = (Vector((0, 0, 1))-s.camera.location).to_track_quat('-Z', 'Y').to_euler()
    s.camera.data.lens = 50
    s.camera.data.dof.focus_distance = 6

assert gate.validate_camera_path(s, safe, [wall])['status'] == 'PASS'
def collision(frame):
    safe(frame)
    if frame == 2: s.camera.location = (8, 0, 1)
report = gate.validate_camera_path(s, collision, [wall])
assert any(x['kind'] == 'camera_clearance' and x['frame'] == 2 and x['inside'] for x in report['issues'])
assert any(x['kind'] == 'continuity' and x['frame'] == 2 for x in report['issues'])
report = gate.validate_camera_path(s, collision, [wall], cuts=[2, 3])
assert any(x['kind'] == 'camera_clearance' for x in report['issues'])
assert not any(x['kind'] == 'continuity' for x in report['issues'])
assert gate.validate_camera_path(s, safe, [])['status'] == 'UNVERIFIED'
# Live tag policy catches meshes introduced AFTER setup and preserves hats.
look.mark_role(asset, 'horizon'); asset.visible_shadow = True
s.frame_set(2)
assert not asset.visible_shadow
# Velocity alignment remains correct beneath rotated/nonuniform parent bases.
parent = bpy.data.objects.new('Projectile parent', None); s.collection.objects.link(parent)
parent.rotation_euler.z = .7; parent.scale = (2, 1, 1)
projectile = bpy.data.objects.new('Projectile', None); s.collection.objects.link(projectile); projectile.parent = parent
bpy.context.view_layer.update()
tangent = look.align_to_velocity_tangent(projectile, lambda f: (f, f*.2, .1*f), 1, spin=.6)
bpy.context.view_layer.update()
assert (projectile.matrix_world.to_3x3() @ Vector((0, 1, 0))).normalized().dot(tangent) > .99999
# An existing foreign compositor must never be silently replaced.
s['ricks_post'] = False
try:
    look.install_post(s)
except ValueError:
    pass
else:
    raise AssertionError('Foreign compositor silently replaced')
print('BLENDER_PIPELINE_FIXTURES_OK NO_RENDER_NO_SAVED_BLEND')
