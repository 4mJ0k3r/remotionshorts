import bpy,math,sys,json,ast,hashlib
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v13';s=bpy.context.scene;O=bpy.data.objects;bpy.app.handlers.frame_change_post.clear()
exec(compile(bpy.data.texts['slow_eddie_v12_runtime.py'].as_string(),'locked_v12','exec'))
def cameras():
 rows=[]
 for f in range(1,301):
  s.frame_current=f;plan(s);rows.append([f,list(cam.location),list(cam.rotation_quaternion),cam.data.lens,cam.data.shift_x,cam.data.shift_y,cam.data.dof.aperture_fstop,list(O['V7 hero focus'].location)])
 return rows
before=cameras();states={}
for f in range(24,34):
 s.frame_set(f);update(s);g=O['Challenger_revolver'];m=g.matrix_world@V((.35,0,.23));pos=m+V((.65,-1.15,.15));aim(pos,m+V((.20,0,0)),42);states[str(f)]={'position':list(cam.location),'rotation':list(cam.rotation_quaternion),'lens':42,'focus_distance':(m-cam.location).length,'muzzle':list(m)}
cache=bpy.data.texts.new('V13 locked editorial.json');cache.from_string(json.dumps(states))
sys.path.insert(0,str(R/'tools/V9_Parity_Packet/V9_Parity_Packet'));import v9_patch_helpers as H
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb
ink=bpy.data.materials['V7 thin warm ink'];black=bpy.data.materials['V7 matte limb ink'];cream=bpy.data.materials['V9 skin']
tree=ast.parse((R/'scripts/slow_eddie_v7/build.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'constructors','exec'))
# Quantize received hat shadow only on the upper forehead. Lower face is protected warm cream.
skull=O['V7 eddie rough skull'];skin=skull.data.materials[0].copy();skin.name='V13 Eddie brim receiver';skull.data.materials[0]=skin;nt=skin.node_tree;l=nt.links;rp=next(n for n in nt.nodes if n.type=='VALTORGB');rp.color_ramp.interpolation='LINEAR'
while len(rp.color_ramp.elements)>2:rp.color_ramp.elements.remove(rp.color_ramp.elements[-1])
rp.color_ramp.elements[0].position=.44;rp.color_ramp.elements[0].color=H.rgba('#C4C8EA');rp.color_ramp.elements[1].position=.46;rp.color_ramp.elements[1].color=H.rgba('#FDF5EF')
tex=nt.nodes.new('ShaderNodeTexCoord');sep=nt.nodes.new('ShaderNodeSeparateXYZ');l.new(tex.outputs['Generated'],sep.inputs[0]);mask=nt.nodes.new('ShaderNodeMapRange');mask.clamp=True;mask.inputs['From Min'].default_value=.547;mask.inputs['From Max'].default_value=.553;l.new(sep.outputs['Z'],mask.inputs['Value']);mix=nt.nodes.new('ShaderNodeMixRGB');mix.inputs[1].default_value=H.rgba('#FDF5EF');l.new(mask.outputs[0],mix.inputs[0]);l.new(rp.outputs[0],mix.inputs[2]);em=next(n for n in nt.nodes if n.type=='EMISSION');l.new(mix.outputs[0],em.inputs[0])
# Keep the real felt brim opaque and shadow-casting.
brim=O['V7 eddie curved brim'];brim.visible_shadow=True
for v in brim.data.vertices:
 if v.co.y<-.10:v.co.z-=.012
# Closed copper slug: dark flat rear base, tiny groove, no recessed pale primer cup.
b=O['Copper_bullet']
for c in list(b.children_recursive):bpy.data.objects.remove(c,do_unlink=True)
jacket=H.metal('V13 copper jacket','#E5A16B',.25,.29);bs=jacket.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=H.rgba('#E5A16B');bs.inputs['Emission Strength'].default_value=.20
base=H.metal('V13 solid bronze base','#9E6238',.15,.48)
profile=[(-.092,.019),(-.090,.021),(-.085,.021),(-.082,.0198),(-.078,.021),(.015,.021),(.04,.019),(.07,.014),(.09,.007),(.102,.0004)];n=40;vs=[];fs=[]
for y,r in profile:
 for j in range(n):a=j*math.tau/n;vs.append((r*math.cos(a),y,r*math.sin(a)))
for i in range(len(profile)-1):
 for j in range(n):a=i*n+j;c=i*n+(j+1)%n;fs.append((a,c,c+n,a+n))
fs.append(tuple(reversed(range(n))));fs.append(tuple(range((len(profile)-1)*n,len(profile)*n)))
me=bpy.data.meshes.new('V13 closed ogive');me.from_pydata(vs,[],fs);me.materials.append(jacket);me.materials.append(base);b.data=me
import bmesh
bm=bmesh.new();bm.from_mesh(me);bmesh.ops.recalc_face_normals(bm,faces=list(bm.faces));bm.to_mesh(me);bm.free();me.update()
for p in me.polygons:p.use_smooth=len(p.vertices)==4;p.material_index=1 if p.center.y<-.086 else 0
me.update()
for p in me.polygons:
 if sum(me.vertices[i].co.y for i in p.vertices)/len(p.vertices)<-.086:p.material_index=1
outline(b,.0015)
# Properly seated upward handle; retain crosshatching and remove the waist-level oval placement.
g=O['V7 pearl revolver butt'];g.location=(-.20,-.19,.915);g.rotation_euler.y=math.radians(-35);g.scale=(.65,.8,1.0)
for o in O:
 if ('hand' in o.name.lower() or 'finger' in o.name.lower()) and o.type=='MESH' and not o.get('v7_outline'):
  o.data.materials.clear();o.data.materials.append(H.metal('V13 dark glove '+o.name,'#2B2438',0,.9))
# Confident opening lid strokes and an asymmetric single smirk.
for o in O:
 if o.name.startswith('V7 challenger') and 'brow' in o.name.lower():
  o.rotation_euler.y=0
lidmat=bpy.data.materials.new('V13 eyelid cream');lidmat.use_nodes=True;nn=lidmat.node_tree.nodes;nn.clear();ee=nn.new('ShaderNodeEmission');ee.inputs[0].default_value=H.rgba('#FDF5EF');oo=nn.new('ShaderNodeOutputMaterial');lidmat.node_tree.links.new(ee.outputs[0],oo.inputs[0])
for x in [-.131,.121]:
 points=[(x+.033*math.cos(a),.036+.025*math.sin(a)) for a in [i*math.pi/24 for i in range(25)]];patch('V13 smirk lid mask',points,lidmat,O['V7 challenger head pivot'],.008)
 faceline('V13 smirk lid',[(x-.032,.039),(x,.036),(x+.032,.033)],.0035,O['V7 challenger head pivot'])
# Increase twig readability without changing any camera.
weedmat=bpy.data.materials.new('V13 dry brown twigs');weedmat.use_nodes=True;nt=weedmat.node_tree;nt.nodes.clear();e=nt.nodes.new('ShaderNodeEmission');e.inputs[0].default_value=H.rgba('#9B714A');out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(e.outputs[0],out.inputs[0])
for o in O['Rolling_tumbleweed'].children:
 if o.type=='CURVE':o.data.bevel_depth=.014;o.data.materials.clear();o.data.materials.append(weedmat)
# Metallic medallion and drawn glints over the existing twelve-lobe plate.
gold=H.metal('V13 polished buckle','#E9C777',.6,.18);silver=H.metal('V13 silver glint','#FFF5D7',.65,.12);bs=silver.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=H.rgba('#FFF5D7');bs.inputs['Emission Strength'].default_value=.45
bs=gold.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=H.rgba('#E9C777');bs.inputs['Emission Strength'].default_value=.12
O['V9 eddie medallion'].data.materials[0]=gold
curve('V13 dark buckle ring',[(.031*math.cos(i*math.tau/64),-.275,.94+.031*math.sin(i*math.tau/64)) for i in range(65)],.0028,black,O['V7 eddie torso'])
curve('V13 buckle specular arc',[(.045*math.cos(a),-.276,.94+.045*math.sin(a)) for a in [math.pi*.55+i*math.pi*.3/16 for i in range(17)]],.002,silver,O['V7 eddie torso'])
text=bpy.data.texts.new('slow_eddie_v13_runtime.py');text.from_string((R/'scripts/slow_eddie_v13/runtime.py').read_text());exec(compile(text.as_string(),text.name,'exec'));globals().pop('_wide_shift',None);after=cameras();assert before==after,'Locked camera changed'
(P/'camera_lock.json').write_text(json.dumps({'all_300_camera_lens_focus_states_identical':True,'v12_states':before,'editorial_states':states},indent=2));s.frame_set(1);update(s);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v13.blend'))
