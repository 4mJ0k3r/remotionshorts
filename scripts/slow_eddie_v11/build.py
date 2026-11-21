import bpy,math,sys,json,ast
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v11';s=bpy.context.scene;O=bpy.data.objects;bpy.app.handlers.frame_change_post.clear()
bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v11.blend'))
sys.path.insert(0,str(R/'tools/V9_Parity_Packet/V9_Parity_Packet'));import v9_patch_helpers as H
s.eevee.shadow_pool_size='512';s.eevee.shadow_ray_count=2
for o in O:
 if o.type=='LIGHT' and hasattr(o.data,'shadow_maximum_resolution'):o.data.shadow_maximum_resolution=.025;o.data.use_shadow_jitter=False
 if o.get('v7_outline') or any(k in o.name.lower() for k in [' ink','cloud','smoke','wind ribbon','mesa','sandstone']):o.visible_shadow=False
# Copper remains warm with RT off, rather than reflecting the blue street as pewter.
copper=H.metal('V11 vivid copper','#E88B4A',.25,.24);bs=copper.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=H.rgba('#E88B4A');bs.inputs['Emission Strength'].default_value=.28
O['Copper_bullet'].data.materials.clear();O['Copper_bullet'].data.materials.append(copper)
sm=bpy.data.materials.new('V11 faint wisps');sm.use_nodes=True;sm.surface_render_method='BLENDED';nt=sm.node_tree;nt.nodes.clear();tr=nt.nodes.new('ShaderNodeBsdfTransparent');em=nt.nodes.new('ShaderNodeEmission');em.inputs[0].default_value=H.rgba('#B9B2A9');mx=nt.nodes.new('ShaderNodeMixShader');mx.inputs[0].default_value=.16;out=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(tr.outputs[0],mx.inputs[1]);nt.links.new(em.outputs[0],mx.inputs[2]);nt.links.new(mx.outputs[0],out.inputs[0])
for o in O:
 if 'smoke' in o.name.lower() and o.type=='MESH':o.data.materials.clear();o.data.materials.append(sm);o.scale.x*=.4
black=H.metal('V11 glove','#2B2438',0,.85)
for o in O:
 if 'hand' in o.name.lower() or 'finger' in o.name.lower() or o.name=='V8 revolver grip seat':
  if o.type=='MESH' and not o.get('v7_outline'):o.data.materials.clear();o.data.materials.append(black)
 if o.name.startswith('V9 chest cartridge'):o.location.z-=.48
for name in ['V7 eddie curved brim','V7 eddie curved brim ink']:
 if name in O:
  for v in O[name].data.vertices:v.co.x*=1.14
O['V7 pearl revolver butt'].scale=(.68,.8,1)
# Slanted brows and waist loops preserve the existing drawn shapes.
for o in O:
 if o.name.startswith('V7 challenger') and 'brow' in o.name.lower():o.rotation_euler.y+=math.radians(8 if '001' in o.name else -8)
# Runtime includes all frame-addressable staging before trajectory capture.
t=bpy.data.texts.new('slow_eddie_v11_runtime.py');t.from_string((R/'scripts/slow_eddie_v11/runtime.py').read_text());exec(compile(t.as_string(),t.name,'exec'))
flight={}
for f in range(25,92):s.frame_set(f);update(s);flight[str(f)]=list(O['Copper_bullet'].location)
start=V(flight['55']);end=V(flight['90']);right=cam.matrix_world.to_quaternion()@V((1,0,0));c1=start+V((0,1.5,.45));c2=end-right*.65
for f in range(56,91):
 u=(f-55)/35;flight[str(f)]=list((1-u)**3*start+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end)
flight['91']=list(end+right*.015)
ft=bpy.data.texts.new('V11 flight.json');ft.from_string(json.dumps(flight));(P/'flight.json').write_text(json.dumps(flight,indent=2))
exec(compile(t.as_string(),t.name,'exec'));s.frame_set(1);update(s)
bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v11.blend'))
(P/'shadow_settings.json').write_text(json.dumps({'pool':s.eevee.shadow_pool_size,'rays':s.eevee.shadow_ray_count,'jitter':False,'max_resolution':.025},indent=2))
