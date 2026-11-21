"""Cinematic light projection, world backdrops, and transition timing."""
import math

import bpy
from mathutils import Matrix, Quaternion, Vector, geometry

from sets import rgb
from shots import WHIP_CUTS

SUN_POSITION=(-5.45,-3.55,5.45)
SHADOW_AXIS=Vector((.78,.59))/math.tan(math.radians(40))


def projected_material(g):
    key='Daytime projected shadow'
    if key not in g.materials:
        mat=bpy.data.materials.new(key);mat.use_nodes=True;mat.surface_render_method='BLENDED';mat.use_transparency_overlap=False
        nodes=mat.node_tree.nodes;links=mat.node_tree.links;nodes.clear()
        out=nodes.new('ShaderNodeOutputMaterial');mix=nodes.new('ShaderNodeMixShader');mix.inputs[0].default_value=.45
        transparent=nodes.new('ShaderNodeBsdfTransparent');ink=nodes.new('ShaderNodeEmission');ink.inputs[0].default_value=(*rgb('161421'),1)
        links.new(transparent.outputs[0],mix.inputs[1]);links.new(ink.outputs[0],mix.inputs[2]);links.new(mix.outputs[0],out.inputs[0]);g.materials[key]=mat
    return g.materials[key]


def footprint(points, z):
    projected=[Vector((p[0],p[1]))+SHADOW_AXIS*max(0,p[2]-z) for p in points]
    return [projected[i] for i in geometry.convex_hull_2d(projected)]


def clip(poly, axis, limit, sign):
    output=[]
    for a,b in zip(poly,poly[1:]+poly[:1]):
        u=(a[axis]-limit)*sign;v=(b[axis]-limit)*sign
        if u>=0:output.append(a)
        if (u>=0)!=(v>=0):output.append(a.lerp(b,u/(u-v)))
    return output


def projection_mesh(g, root, name, groups, wedding=False):
    vertices=[];faces=[]
    def add(poly,z):
        if len(poly)<3:return
        index=len(vertices);vertices.extend((p.x,p.y,z) for p in poly);faces.append(tuple(range(index,index+len(poly))))
    for points in groups:
        add(footprint(points,0),.006)
        if wedding:
            poly=footprint(points,.0365)
            for axis,limit,sign in ((0,-.739,1),(0,.739,-1),(1,-5.198,1),(1,3.798,-1)):
                poly=clip(poly,axis,limit,sign)
            add(poly,.040)
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(vertices,[],faces);mesh.update();mesh.materials.append(projected_material(g))
    return g.link(name,mesh,root)


def stage_shadows(g, root, wedding=False):
    groups=[]
    for obj in root.children:
        name=obj.name
        if name.startswith('Bentwood wedding arch'):
            points=[Vector(p.co[:3])+obj.location for p in obj.data.splines[0].points]
            for a,b in zip(points,points[1:]):
                groups.append([p+Vector((x,y,z)) for p in (a,b) for x in (-.079,.079) for y in (-.048,.048) for z in (-.05,.05)])
        if obj.type!='MESH' or not name.startswith(('Eiffel','Park tree','Park crown','White guest chair','Guest chair leg','Wedding arch leaf')):
            continue
        transform=Matrix.LocRotScale(obj.location,obj.rotation_euler.to_quaternion(),obj.scale)
        vertices=obj.data.vertices
        stride=max(1,len(vertices)//220)
        groups.append([transform@vertices[i].co for i in range(0,len(vertices),stride)])
    projection_mesh(g,root,'Sun projected landmark and prop silhouettes',groups,wedding)


def actor_shadow(g, root, actor, wedding):
    x,y,z=actor.base.location
    top=z+actor.head.location.z
    # Squat and standing silhouettes follow the same receiver and solar projection.
    points=lambda cx,cy,cz,rx,ry,rz:[(cx+sx*rx,cy+sy*ry,cz+sz*rz) for sx in (-1,1) for sy in (-1,1) for sz in (-1,1)]
    groups=[points(x,y,top,.24,.065,.23),points(x,y,z+actor.body.location.z,.22,.06,.23)]
    groups.extend([points(x+side*.13,y,max(.12,z+.20),.085,.062,.19)+points(x+side*.15,y,.048,.085,.055,.05) for side in (-1,1)])
    return projection_mesh(g,root,'Sun projected actor silhouette',groups,wedding)


def setup_world(scene):
    world=bpy.data.worlds.new('Indigo and sunset world');world.use_nodes=True;scene.world=world
    n,l=world.node_tree.nodes,world.node_tree.links;n.clear()
    out=n.new('ShaderNodeOutputWorld');ambient=n.new('ShaderNodeBackground');ambient.inputs['Strength'].default_value=.45
    visual=n.new('ShaderNodeBackground');visual.inputs['Strength'].default_value=.93
    tex=n.new('ShaderNodeTexCoord');axis=n.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Normal'],axis.inputs[0])
    absolute=n.new('ShaderNodeMath');absolute.operation='ABSOLUTE';l.new(axis.outputs['Z'],absolute.inputs[0])
    elev=n.new('ShaderNodeMapRange');elev.inputs['From Max'].default_value=.60;l.new(absolute.outputs[0],elev.inputs[0])
    sky=n.new('ShaderNodeValToRGB');l.new(elev.outputs[0],sky.inputs[0]);l.new(sky.outputs[0],ambient.inputs['Color'])
    starfield=n.new('ShaderNodeTexVoronoi');starfield.inputs['Scale'].default_value=78;l.new(tex.outputs['Normal'],starfield.inputs['Vector'])
    size=n.new('ShaderNodeMapRange');size.inputs['From Max'].default_value=.068;size.inputs['To Min'].default_value=.62;size.inputs['To Max'].default_value=0
    l.new(starfield.outputs['Distance'],size.inputs['Value'])
    stars=n.new('ShaderNodeMath');stars.operation='MULTIPLY';l.new(size.outputs[0],stars.inputs[0]);stars.inputs[1].default_value=0
    tint=n.new('ShaderNodeMixRGB');tint.blend_type='ADD';tint.inputs[2].default_value=(*rgb('b4b9d6'),1)
    l.new(stars.outputs[0],tint.inputs[0]);l.new(sky.outputs[0],tint.inputs[1]);l.new(tint.outputs[0],visual.inputs['Color'])
    ray=n.new('ShaderNodeLightPath');mix=n.new('ShaderNodeMixShader');l.new(ray.outputs['Is Camera Ray'],mix.inputs[0]);l.new(ambient.outputs[0],mix.inputs[1]);l.new(visual.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
    return sky,ambient.inputs['Strength'],stars.inputs[1]


def camera_rotation(camera_position, target, frame, start, end):
    rotation=(target-camera_position).to_track_quat('-Z','Y')
    yaw=0
    if start in WHIP_CUTS and frame<=start+3:
        yaw=-30*(1-(frame-start)/3)**2
    if end+1 in WHIP_CUTS and frame>=end-2:
        yaw=30*((frame-(end-2))/3)**2
    return rotation@Quaternion((0,1,0),math.radians(yaw))
