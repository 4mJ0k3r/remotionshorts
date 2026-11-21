import bpy,math,sys,json,ast
from pathlib import Path
from mathutils import Vector as V,Matrix
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v12';s=bpy.context.scene;O=bpy.data.objects;bpy.app.handlers.frame_change_post.clear();bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v12.blend'))
sys.path.insert(0,str(R/'tools/V9_Parity_Packet/V9_Parity_Packet'));import v9_patch_helpers as H
sys.path.insert(0,str(R/'scripts/washroom_experiment'));from sets import rgb
ink=bpy.data.materials['V7 thin warm ink'];black=bpy.data.materials['V7 matte limb ink'];brown=bpy.data.materials['V7 dark hatband']
tree=ast.parse((R/'scripts/slow_eddie_v7/build.py').read_text());exec(compile(ast.Module(body=[x for x in tree.body if isinstance(x,ast.FunctionDef)],type_ignores=[]),'constructors','exec'))
# Preserve face/brim material, exposure, lighting and existing cast-shadow band.
s.view_settings.exposure=0
ramp=next(n for n in s.world.node_tree.nodes if n.type=='VALTORGB').color_ramp
for e in list(ramp.elements)[1:-1]:ramp.elements.remove(e)
ramp.elements[0].position=0;ramp.elements[0].color=H.rgba('#BEE1FF');ramp.elements[1].position=.72;ramp.elements[1].color=H.rgba('#2D93FB');ramp.elements.new(.36).color=H.rgba('#6DBCFD')
nt=s.world.node_tree;rp=next(n for n in nt.nodes if n.type=='VALTORGB');src=rp.inputs[0].links[0].from_socket;mr=nt.nodes.new('ShaderNodeMapRange');mr.name='V12 sky elevation calibration';mr.inputs['From Min'].default_value=.05;mr.inputs['From Max'].default_value=.35;mr.inputs['To Min'].default_value=0;mr.inputs['To Max'].default_value=.72;nt.links.new(src,mr.inputs['Value']);nt.links.new(mr.outputs[0],rp.inputs[0])
road=O['Dusty Main Street'].data.materials[0];nt=road.node_tree;l=nt.links;rp=next(n for n in nt.nodes if n.type=='VALTORGB')
c=rp.color_ramp.elements[-1].color;rp.color_ramp.elements[-1].color=(c[0]*1.22,c[1]*1.19,c[2]*.98,c[3])
for name,color in [('V9 teal','#47B0AC'),('V9 vest','#BE9462')]:
 if name in bpy.data.materials:
  for n in bpy.data.materials[name].node_tree.nodes:
   if n.type=='VALTORGB':n.color_ramp.elements[-1].color=H.rgba(color)
for o in O:
 if o.name.startswith('V9 chest cartridge'):o.location.z=0
 if o.name.startswith('V7 eddie') and 'skull' in o.name:
  # Remove only added procedural displacement; retain authored base contour.
  for m in list(o.modifiers):
   if m.type=='DISPLACE':o.modifiers.remove(m)
for name in ['V7 challenger skull','V7 challenger skull ink']:
 if name in O:
  for m in list(O[name].modifiers):
   if m.type=='DISPLACE':O[name].modifiers.remove(m)
# One continuous hanging five-lobe moustache replaces the bead chain.
for o in list(O):
 if 'mustache lobe' in o.name or 'moustache' in o.name:bpy.data.objects.remove(o,do_unlink=True)
coords=[(-.14,-.085),(-.10,-.074),(-.05,-.078),(0,-.074),(.05,-.078),(.1,-.074),(.14,-.085)]
for j in range(4,-1,-1):
 for k in range(17):
  a=math.pi*k/16;coords.append(((j-2)*.056+.028*math.cos(a),-.10-.035*math.sin(a)))
cu=bpy.data.curves.new('V12 five-lobe continuous curve','CURVE');cu.dimensions='2D';cu.fill_mode='BOTH';cu.extrude=.004;cu.bevel_depth=.003;cu.bevel_resolution=2;sp=cu.splines.new('POLY');sp.points.add(len(coords)-1)
for p,(x,z) in zip(sp.points,coords):p.co=(x,z,0,1)
sp.use_cyclic_u=True;o=bpy.data.objects.new('V12 continuous hanging moustache',cu);s.collection.objects.link(o);o.parent=O['V7 eddie head pivot'];o.rotation_euler.x=math.pi/2;o.location.y=-.31;cu.materials.append(brown)
st=O['V7 eddie mouth straw'];sp=st.data.splines[0]
if len(sp.points)>=4:sp.points[-1].co.z=sp.points[-2].co.z-.06*math.tan(math.radians(12))
for m in bpy.data.materials:
 if m.name.startswith('V11 faint wisps'):
  for n in m.node_tree.nodes:
   if n.type=='MIX_SHADER':n.inputs[0].default_value=.045
for i in range(3):
 o=O['V7 smoke '+str(i)]
 for v in o.data.vertices:v.co.x*=.4;v.co.z*=.6*(1+.12*math.sin(v.co.x*33))
g=O['V7 pearl revolver butt'];g.rotation_euler.y=math.radians(-12);g.location.x-=.025
# Recover side-on aspect through geometry/projection, never by crabbing the nose.
for o in [O['Copper_bullet']]+list(O['Copper_bullet'].children):
 if o.type=='MESH':
  for v in o.data.vertices:v.co.y*=2
text=bpy.data.texts.new('slow_eddie_v12_runtime.py');text.from_string((R/'scripts/slow_eddie_v12/runtime.py').read_text());exec(compile(text.as_string(),text.name,'exec'))
# Freeze the physical endpoint using measured projected surface clearance.
s.frame_set(91);update(s);b=O['Copper_bullet'];b.rotation_quaternion=(cam.matrix_world.to_quaternion()@V((1,0,0))).to_track_quat('Y','Z');b.scale=(1.2,)*3;b.location=(-.6,18.7,.76);bpy.context.view_layer.update()
right=cam.matrix_world.to_quaternion()@V((1,0,0));grip=O['V7 pearl revolver butt']
for solve in range(3):
 bpy.context.view_layer.update();edge=min(project(s,cam,grip.matrix_world@V(c)).x for c in grip.bound_box);tip=max(project(s,cam,b.matrix_world@v.co).x for v in b.data.vertices);b.location+=right*.01;bpy.context.view_layer.update();probe=max(project(s,cam,b.matrix_world@v.co).x for v in b.data.vertices);b.location-=right*.01;b.location+=right*((edge-20/360-tip)/((probe-tip)/.01))
end=b.location.copy()
flight=json.loads(bpy.data.texts['V11 flight.json'].as_string());start=V(flight['70']);c1=start+V((0,.5,.15));c2=end-right*.5
for f in range(71,91):
 u=(f-70)/20;flight[str(f)]=list((1-u)**3*start+3*(1-u)**2*u*c1+3*(1-u)*u*u*c2+u**3*end)
flight['91']=list(end+right*.0001)
ft=bpy.data.texts.new('V12 flight.json');ft.from_string(json.dumps(flight));globals().pop('_flight12',None);globals().pop('_flight',None);exec(compile(text.as_string(),text.name,'exec'));s.frame_set(1);update(s);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v12.blend'))
