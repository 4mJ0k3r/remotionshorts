"""Geometry-only screen-space world contours for lit EEVEE scenes.

Tag selected meshes with obj['set_ink'] = True. Texture normals and grout
never enter this pass. Silhouettes and hard creases share camera-pixel units.
The quads remain in world depth, so receivers, cel cards, and DOF occlude them.
"""
import bpy
import math
from mathutils import Vector


class SetInk:
    def __init__(self, scene):
        self.scene = scene
        self.sources = []
        graph = bpy.context.evaluated_depsgraph_get()
        for obj in scene.objects:
            if obj.type != 'MESH' or not obj.get('set_ink'):
                continue
            evaluated = obj.evaluated_get(graph)
            mesh = evaluated.to_mesh()
            vertices = [vertex.co.copy() for vertex in mesh.vertices]
            faces = [polygon.normal.copy() for polygon in mesh.polygons]
            adjacency = {}
            for polygon in mesh.polygons:
                for edge in polygon.edge_keys:
                    adjacency.setdefault(tuple(sorted(edge)), []).append(polygon.index)
            edges = [(edge, adjacent) for edge, adjacent in adjacency.items()]
            self.sources.append((obj, vertices, faces, edges))
            evaluated.to_mesh_clear()
        self.mesh = bpy.data.meshes.get('Studio set contour mesh')
        if not self.mesh:
            self.mesh = bpy.data.meshes.new('Studio set contour mesh')
        self.output = scene.objects.get('WORLD_INK_PASS')
        if not self.output:
            self.output = bpy.data.objects.new('WORLD_INK_PASS', self.mesh)
            scene.collection.objects.link(self.output)
        material = bpy.data.materials.get('Warm marker / depth faded set contours')
        if not material:
            material = bpy.data.materials.new('Warm marker / depth faded set contours')
            material.use_nodes = True
            material.surface_render_method = 'BLENDED'
            nodes = material.node_tree.nodes
            nodes.clear()
            links = material.node_tree.links
            output = nodes.new('ShaderNodeOutputMaterial')
            emission = nodes.new('ShaderNodeEmission')
            emission.inputs[0].default_value = (.0331, .0116, .006, 1)
            transparent = nodes.new('ShaderNodeBsdfTransparent')
            attribute = nodes.new('ShaderNodeAttribute')
            attribute.attribute_name = 'ink_opacity'
            mix = nodes.new('ShaderNodeMixShader')
            links.new(attribute.outputs['Fac'], mix.inputs[0])
            links.new(transparent.outputs[0], mix.inputs[1])
            links.new(emission.outputs[0], mix.inputs[2])
            links.new(mix.outputs[0], output.inputs[0])
        if not self.mesh.materials:
            self.mesh.materials.append(material)

    def update(self):
        camera = self.scene.camera
        rotation = camera.matrix_world.to_quaternion()
        inverse_rotation = rotation.inverted()
        forward = rotation @ Vector((0, 0, -1))
        camera_position = camera.matrix_world.translation
        sensor_ratio = camera.data.sensor_width / camera.data.lens
        vertices, faces, opacities = [], [], []
        crease_cosine = math.cos(math.radians(38))
        for obj, local_vertices, local_normals, edges in self.sources:
            if obj.hide_render:
                continue
            matrix = obj.matrix_world
            normal_matrix = matrix.to_3x3().inverted().transposed()
            world_vertices = [matrix @ point for point in local_vertices]
            normals = [(normal_matrix @ normal).normalized() for normal in local_normals]
            for (index_a, index_b), adjacent in edges:
                a, b = world_vertices[index_a], world_vertices[index_b]
                center = (a + b) * .5
                view = (camera_position - center).normalized()
                facing = [normals[index].dot(view) for index in adjacent]
                silhouette = len(adjacent) == 1 or min(facing) < 0 < max(facing)
                crease = len(adjacent) == 2 and normals[adjacent[0]].dot(normals[adjacent[1]]) < crease_cosine and max(facing) > .025
                if not silhouette and not crease:
                    continue
                if max(facing) < -.005:
                    continue
                depth_a = (a - camera_position).dot(forward)
                depth_b = (b - camera_position).dot(forward)
                if min(depth_a, depth_b) < .025:
                    continue
                tangent = b - a
                if tangent.length < .00001:
                    continue
                transverse = tangent.cross(view).normalized()
                # A full width of .0035 of frame width, and half for creases.
                half_width = .0035 * (.5 if silhouette else .25)
                # The camera-side epsilon avoids coplanar depth fights without
                # drawing hidden edges through foreground geometry.
                offset = view * .0007
                a = a + offset
                b = b + offset
                local_axis = inverse_rotation @ transverse
                def projected_half_width(point):
                    local_point = inverse_rotation @ (point-camera_position)
                    depth = -local_point.z
                    dx = local_axis.x*depth + local_point.x*local_axis.z
                    dy = local_axis.y*depth + local_point.y*local_axis.z
                    derivative = math.hypot(dx,dy)
                    return half_width*sensor_ratio*depth*depth/max(.000001,derivative)
                width_a = projected_half_width(a)
                width_b = projected_half_width(b)
                start = len(vertices)
                vertices.extend([a-transverse*width_a,a+transverse*width_a,b+transverse*width_b,b-transverse*width_b])
                faces.append((start,start+1,start+2,start+3))
                focus = camera.data.dof.focus_distance
                for depth in [depth_a,depth_a,depth_b,depth_b]:
                    fade = max(.20, 1 - max(0,depth-focus)*.21)
                    opacities.append(.88*fade)
        self.mesh.clear_geometry()
        self.mesh.from_pydata(vertices, [], faces)
        attribute = self.mesh.attributes.get('ink_opacity')
        if attribute:
            self.mesh.attributes.remove(attribute)
        attribute = self.mesh.attributes.new('ink_opacity','FLOAT','POINT')
        attribute.data.foreach_set('value',opacities)
        self.mesh.update()
