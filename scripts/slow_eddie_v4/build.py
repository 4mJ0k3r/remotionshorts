import bpy,math,sys
from pathlib import Path
from mathutils import Vector as V
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v4';s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear()
sys.path.insert(0,str(R/'scripts/washroom_experiment'));sys.path.insert(0,str(R/'scripts/inside_brain_dog'));from sets import Stage,rgb
from build_inside_brain_dog import cel_material
G=Stage(s)
bpy.data.objects['eddie_body'].data.materials[0]=cel_material('Eddie V4 clean belt cel',P/'art/eddie_body.png')
# One slim, curved leather sheath, rounded rather than a boxy flap.
h=bpy.data.objects['Eddie left black holster'];mesh=bpy.data.meshes.new('V4 contoured leather sheath');pts=[]
def bez(a,b,c,d):
 for i in range(12):
  t=i/12;v=(1-t)**3*V(a)+3*(1-t)**2*t*V(b)+3*(1-t)*t*t*V(c)+t**3*V(d);pts.append(tuple(v))
bez((-.075,.15,0),(-.02,.17,0),(.055,.17,0),(.075,.13,0));bez((.075,.13,0),(.08,-.05,0),(.075,-.20,0),(.02,-.22,0));bez((.02,-.22,0),(-.055,-.23,0),(-.065,-.14,0),(-.075,.15,0))
mesh.from_pydata(pts,[],[tuple(range(len(pts)))]);h.data=mesh;mesh.materials.append(G.mat('291d18',em=.55));G.curve('Holster stitched ink edge',pts,.003,G.mat('352329',em=.5),h,loop=True).data.bevel_resolution=0
# Curved pearl butt integrated onto imported gun grip, preserving actual prop hierarchy.
eg=bpy.data.objects['Eddie_pearl_revolver']
for o in list(s.objects):
 if o.name=='Eddie pearl handle' or o.name.startswith('Pearl ivory grip ink border'):bpy.data.objects.remove(o,do_unlink=True)
rim=G.ball('V4 curved grip dark frame',(-.20,-.029,.10),(.073,.022,.105),G.mat('241b18',em=.3),eg)
pearl=G.ball('Eddie pearl handle',(-.20,-.054,.10),(.063,.017,.093),G.mat('EFE8D5'),eg)
# Emission keeps the ivory color warm through the bright key instead of clipping white.
m=pearl.data.materials[0];nt=m.node_tree;nt.nodes.clear();em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(*rgb('EFE8D5'),1);em.inputs[1].default_value=.92;out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(em.outputs[0],out.inputs[0])
# Unique dark timber BANK corner behind Eddie.
for o in s.objects:
 if o.type=='FONT' and 'PHOTOGRAPHS' in o.data.body and o.location.y>8:o.data=o.data.copy();o.data.body='BANK';o.data.size=.48
 if o.type=='MESH' and o.name.startswith('saloon') and 12<o.location.y<25:
  o.data=o.data.copy()
  for j,m in enumerate(list(o.data.materials)):
   m=m.copy();o.data.materials[j]=m
   if m.use_nodes:
    for n in m.node_tree.nodes:
     if n.type=='BSDF_PRINCIPLED':n.inputs['Base Color'].default_value=(*rgb('573a2b'),1);n.inputs['Emission Color'].default_value=(*rgb('573a2b'),1)
# Tapered two-dimensional streak ribbons with per-vertex tail fade.
for o in list(s.objects):
 if o.name.startswith('Bullet wind streak'):bpy.data.objects.remove(o,do_unlink=True)
m=bpy.data.materials.new('V4 feathered wind');m.use_nodes=True;m.surface_render_method='BLENDED';nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(1,1,1,1);em.inputs[1].default_value=.8;tr=nt.nodes.new('ShaderNodeBsdfTransparent');attr=nt.nodes.new('ShaderNodeAttribute');attr.attribute_name='wind_alpha';mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(attr.outputs['Fac'],mix.inputs[0]);nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(em.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0])
for j in range(3):
 me=bpy.data.meshes.new('Tapered wind ribbon');vs=[]
 for i in range(21):t=i/20;w=.0014*math.sin(math.pi*t);vs.extend([(-w,-.09-.34*t,0),(w,-.09-.34*t,0)])
 me.from_pydata(vs,[],[(i*2,i*2+1,i*2+3,i*2+2) for i in range(20)]);o=G.link('V4 wind ribbon '+str(j),me);me.materials.append(m);a=me.attributes.new('wind_alpha','FLOAT','POINT')
 for i,v in enumerate(a.data):v.value=.16*(1-(i//2)/20)**1.6
# Recognizable camera-space cowboy silhouette, replacing the abstract polygon veil.
ghost=bpy.data.objects['Foreground shoulder silhouette'];mesh=bpy.data.meshes.new('V4 cowboy silhouette card');mesh.from_pydata([(-.275,-.5,0),(.275,-.5,0),(.275,.5,0),(-.275,.5,0)],[],[(0,1,2,3)])
for item,uv in zip(mesh.uv_layers.new().data,[(0,0),(1,0),(1,1),(0,1)]):item.uv=uv
ghost.data=mesh;ghost.location=(-.19,-.04,-1)
m=bpy.data.materials['V3 translucent silhouette'];nt=m.node_tree;nt.nodes.clear();out=nt.nodes.new('ShaderNodeOutputMaterial');tr=nt.nodes.new('ShaderNodeBsdfTransparent');em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=(*rgb('352329'),1);tex=nt.nodes.new('ShaderNodeTexImage');tex.image=bpy.data.images.load(str(P/'art/cowboy_silhouette.png'));tex.image.pack();alpha=nt.nodes.new('ShaderNodeMath');alpha.operation='MULTIPLY';alpha.name='Shoulder alpha';alpha.inputs[0].default_value=0;nt.links.new(tex.outputs['Alpha'],alpha.inputs[1]);mix=nt.nodes.new('ShaderNodeMixShader');nt.links.new(alpha.outputs[0],mix.inputs[0]);nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(em.outputs[0],mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0]);mesh.materials.append(m)
# Conservative distant ink culling retained; 16-sample EEVEE budget.
s.eevee.taa_render_samples=16
for im in bpy.data.images:
 if im.type=='IMAGE' and im.size[0]:im.pack()
txt=bpy.data.texts.load(str(R/'scripts/slow_eddie_v4/runtime.py'));txt.name='slow_eddie_v4_runtime.py';exec(compile(txt.as_string(),txt.name,'exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v4.blend'))
