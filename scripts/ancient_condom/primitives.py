"""Project-local Blender 4.2 construction helpers; no live Blender connection."""
import bpy, bmesh, math, random, json
from pathlib import Path
from mathutils import Vector, Matrix
V=Vector
ROOT=Path(r'D:\remotionshorts');OUT=ROOT/'renders/ancient_condom';ART=OUT/'assets'
IMAGES={};MATS={}

def rgb(h):
    v=[int(h.lstrip('#')[i:i+2],16)/255 for i in (0,2,4)]
    return tuple(c/12.92 if c<.04045 else ((c+.055)/1.055)**2.4 for c in v)

def image(path):
    p=str(path)
    if p not in IMAGES:
        IMAGES[p]=bpy.data.images.load(p,check_existing=False);IMAGES[p].pack()
    return IMAGES[p]

def key(o,prop,f):o.keyframe_insert(data_path=prop,frame=f)
def linear(o):
    if o.animation_data and o.animation_data.action:
        for fc in o.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'

def mat(h,metal=0,rough=.55,em=0):
    k=(h,metal,rough,em)
    if k in MATS:return MATS[k]
    m=bpy.data.materials.new('Paint '+h);m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF')
    p.inputs['Base Color'].default_value=(*rgb(h),1);p.inputs['Metallic'].default_value=metal;p.inputs['Roughness'].default_value=rough
    p.inputs['Emission Color'].default_value=(*rgb(h),1);p.inputs['Emission Strength'].default_value=em
    MATS[k]=m;return m

def celmat(path):
    k=('cel',str(path))
    if k in MATS:return MATS[k]
    m=bpy.data.materials.new('Scene-lit cel '+Path(path).stem);m.use_nodes=True;m.surface_render_method='DITHERED'
    n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    tex=n.new('ShaderNodeTexImage');tex.image=image(path);tex.interpolation='Linear'
    # Four-frame paint-only ink variation. Alpha/geometry never change.
    bw=n.new('ShaderNodeRGBToBW');l.new(tex.outputs['Color'],bw.inputs[0])
    ink=n.new('ShaderNodeMath');ink.operation='LESS_THAN';ink.inputs[1].default_value=.035;l.new(bw.outputs[0],ink.inputs[0])
    solid=n.new('ShaderNodeMath');solid.operation='GREATER_THAN';solid.inputs[1].default_value=.995;l.new(tex.outputs['Alpha'],solid.inputs[0])
    mask=n.new('ShaderNodeMath');mask.operation='MULTIPLY';l.new(ink.outputs[0],mask.inputs[0]);l.new(solid.outputs[0],mask.inputs[1])
    v=n.new('ShaderNodeValue');v.name='Held paint sample on fours'
    events=[(123,151),(198,218),(266,286),(477,551),(663,724),(735,800),(804,841),(905,933),(971,1022),(1083,1215),(1299,1332),(1410,1476),(1484,1512)]
    for f in range(1,1636,4):
        active=any(a<=f<b for a,b in events);v.outputs[0].default_value=1+.008*math.sin((f//4)*1.71) if active else 1.;v.outputs[0].keyframe_insert('default_value',frame=f)
    if m.node_tree.animation_data and m.node_tree.animation_data.action:
        for fc in m.node_tree.animation_data.action.fcurves:
            for kf in fc.keyframe_points:kf.interpolation='CONSTANT'
    tint=n.new('ShaderNodeMixRGB');tint.blend_type='MULTIPLY';tint.inputs[0].default_value=1;l.new(tex.outputs['Color'],tint.inputs[1]);l.new(v.outputs[0],tint.inputs[2])
    painted=n.new('ShaderNodeMixRGB');l.new(mask.outputs[0],painted.inputs[0]);l.new(tex.outputs['Color'],painted.inputs[1]);l.new(tint.outputs[0],painted.inputs[2])
    p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.55;l.new(painted.outputs[0],p.inputs['Base Color'])
    e=n.new('ShaderNodeEmission');e.inputs[1].default_value=1;l.new(painted.outputs[0],e.inputs[0])
    mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.22;l.new(p.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2])
    t=n.new('ShaderNodeBsdfTransparent');a=n.new('ShaderNodeMixShader');l.new(tex.outputs['Alpha'],a.inputs[0]);l.new(t.outputs[0],a.inputs[1]);l.new(mix.outputs[0],a.inputs[2])
    o=n.new('ShaderNodeOutputMaterial');l.new(a.outputs[0],o.inputs[0]);MATS[k]=m;return m

def alpha_mat(name,h,alpha=.55):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.surface_render_method='BLENDED';n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    t=n.new('ShaderNodeBsdfTransparent');p=n.new('ShaderNodeEmission');p.inputs[0].default_value=(*rgb(h),1)
    mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=alpha;l.new(t.outputs[0],mix.inputs[1]);l.new(p.outputs[0],mix.inputs[2]);o=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],o.inputs[0]);return m

class Stage:
    def __init__(self,s):self.s=s
    def obj(self,name,data=None,xyz=(0,0,0),parent=None):
        o=bpy.data.objects.new(name,data);self.s.collection.objects.link(o);o.location=xyz;o.parent=parent;return o
    def mesh(self,name,bm,m,xyz=(0,0,0),parent=None):
        d=bpy.data.meshes.new(name);bm.to_mesh(d);bm.free();d.update()
        if m:d.materials.append(m)
        return self.obj(name,d,xyz,parent)
    def box(self,name,xyz,dim,m,parent=None,bevel=.025):
        bm=bmesh.new();bmesh.ops.create_cube(bm,size=1);bmesh.ops.scale(bm,verts=list(bm.verts),vec=dim);o=self.mesh(name,bm,m,xyz,parent)
        if bevel:
            mod=o.modifiers.new('Soft edge highlights','BEVEL');mod.width=bevel;mod.segments=2
            o.modifiers.new('Weighted corner normals','WEIGHTED_NORMAL')
        return o
    def ball(self,name,xyz,scale,m,parent=None):
        bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=20,v_segments=12,radius=1);o=self.mesh(name,bm,m,xyz,parent);o.scale=scale
        for p in o.data.polygons:p.use_smooth=True
        return o
    def rod(self,name,a,b,r,m,parent=None):
        a,b=V(a),V(b);delta=b-a;bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=16,radius1=r,radius2=r,depth=delta.length)
        o=self.mesh(name,bm,m,(a+b)/2,parent);o.rotation_euler=delta.to_track_quat('Z','Y').to_euler();return o
    def curve(self,name,pts,r,m,parent=None,closed=False):
        d=bpy.data.curves.new(name,'CURVE');d.dimensions='3D';d.bevel_depth=r;d.bevel_resolution=2;d.resolution_u=12
        sp=d.splines.new('BEZIER');sp.bezier_points.add(len(pts)-1)
        for v,p in zip(sp.bezier_points,pts):v.co=p;v.handle_left_type=v.handle_right_type='AUTO'
        sp.use_cyclic_u=closed;d.materials.append(m);return self.obj(name,d,parent=parent)
    def plane(self,name,w,h,m,xyz=(0,0,0),parent=None,offset_y=0):
        d=bpy.data.meshes.new(name);d.from_pydata([(-w/2,-h/2-offset_y,0),(w/2,-h/2-offset_y,0),(w/2,h/2-offset_y,0),(-w/2,h/2-offset_y,0)],[],[(0,1,2,3)])
        uv=d.uv_layers.new()
        for a,b in zip(uv.data,[(0,0),(1,0),(1,1),(0,1)]):a.uv=b
        d.materials.append(m);return self.obj(name,d,xyz,parent)
    def light(self,name,kind,xyz,target,energy,h):
        d=bpy.data.lights.new(name,kind);d.energy=energy;d.color=rgb(h);o=self.obj(name,d,xyz)
        if kind!='POINT':o.rotation_euler=(V(target)-o.location).to_track_quat('-Z','Y').to_euler()
        if kind=='AREA':d.size=4
        if kind=='SUN':d.angle=math.radians(15)
        if kind=='POINT':d.shadow_soft_size=.15
        return o

def noise_material(name,h1,h2,scale=4,rough=.55,bump=.08,wood=False):
    m=mat(h1,rough=rough).copy();m.name=name;n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF')
    tc=n.new('ShaderNodeTexCoord');mp=n.new('ShaderNodeVectorMath');mp.operation='MULTIPLY';mp.inputs[1].default_value=(1,18,4) if wood else (1,1,1);l.new(tc.outputs['Generated'],mp.inputs[0])
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale;noise.inputs['Detail'].default_value=3;l.new(mp.outputs[0],noise.inputs[0])
    r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(*rgb(h1),1);r.color_ramp.elements[1].color=(*rgb(h2),1);l.new(noise.outputs['Fac'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color'])
    b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=bump;b.inputs['Distance'].default_value=.035;l.new(noise.outputs['Fac'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal']);return m

