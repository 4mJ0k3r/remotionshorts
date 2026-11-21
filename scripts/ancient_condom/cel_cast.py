"""Flat camera-facing cels and thin ink limbs grounded in the dimensional courtyard."""
import bpy,math
from pathlib import Path
from mathutils import Vector as V
from primitives import image,key
from studio import curve_at,shadow
ART=Path(r'D:\remotionshorts\renders\ancient_condom\assets');CACHE={}
def paint(path):
 if str(path) in CACHE:return CACHE[str(path)]
 m=bpy.data.materials.new('Drawn cel / '+path.stem);m.use_nodes=True;m.surface_render_method='DITHERED';n=m.node_tree.nodes;n.clear();l=m.node_tree.links;t=n.new('ShaderNodeTexImage');t.image=image(path);t.interpolation='Linear';p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=1;p.inputs['Specular IOR Level'].default_value=0
 # Preserve dark ink and saturated paint under the strong courtyard key; cream stays bright.
 bw=n.new('ShaderNodeRGBToBW');l.new(t.outputs['Color'],bw.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.interpolation='CONSTANT';r.color_ramp.elements.remove(r.color_ramp.elements[1]);r.color_ramp.elements[0].position=0;r.color_ramp.elements[0].color=(.18,.18,.18,1);el=r.color_ramp.elements.new(.05);el.color=(.35,.35,.35,1);el=r.color_ramp.elements.new(.55);el.color=(1,1,1,1);l.new(bw.outputs[0],r.inputs[0]);tone=n.new('ShaderNodeMixRGB');tone.blend_type='MULTIPLY';tone.inputs[0].default_value=1;l.new(t.outputs['Color'],tone.inputs[1]);l.new(r.outputs[0],tone.inputs[2]);l.new(tone.outputs[0],p.inputs['Base Color'])
 e=n.new('ShaderNodeEmission');l.new(t.outputs['Color'],e.inputs[0]);e.inputs[1].default_value=1;mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.22;l.new(p.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);tr=n.new('ShaderNodeBsdfTransparent');a=n.new('ShaderNodeMixShader');l.new(t.outputs['Alpha'],a.inputs[0]);l.new(tr.outputs[0],a.inputs[1]);l.new(mix.outputs[0],a.inputs[2]);out=n.new('ShaderNodeOutputMaterial');l.new(a.outputs[0],out.inputs[0]);m.use_transparent_shadow=True;CACHE[str(path)]=m;return m
def ink():
 if 'ink' in CACHE:return CACHE['ink']
 m=bpy.data.materials.new('Flat marker ink limbs');m.use_nodes=True;p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.012,.006,.005,1);p.inputs['Emission Color'].default_value=(.012,.006,.005,1);p.inputs['Emission Strength'].default_value=.4;p.inputs['Roughness'].default_value=1;p.inputs['Specular IOR Level'].default_value=0;CACHE['ink']=m;return m
class CoupleActor:
 def __init__(self,g,who,position):
  self.g=g;self.who=who;self.root=g.obj(who+' illustrated Hanfu actor',xyz=position);self.body=g.obj('Flat Hanfu torso pivot',xyz=(0,0,.76),parent=self.root);g.plane('One outlined drawn Hanfu silhouette',.66,.72,paint(ART/f'cel_{who}_body.png'),parent=self.body)
  self.head=g.obj(who+' independent illustrated head',xyz=(0,0,1.40),parent=self.root);self.faces={p:g.plane('Face decal / drawn '+who+' '+p,.78,.78,paint(ART/f'cel_{who}_{p}.png'),parent=self.head) for p in ['smile','shy','panic','horror','blink']}
  self.arms=[g.curve('Thin ink arm',[(0,0,0)]*3,.014,ink(),self.root) for j in range(2)];self.hands=[g.curve('Small ink grip',[(0,0,0)]*3,.014,ink(),self.root) for j in range(2)];self.legs=[g.curve('Thin ink grounded leg',[(0,0,0)]*3,.014,ink(),self.root) for j in range(2)];self.feet=[g.curve('Ground-contact ink foot',[(0,0,0)]*2,.014,ink(),self.root) for j in range(2)]
  self.drops=[]
  # Painted teardrop silhouette, attached to each temple rather than floating ellipsoids.
  for sign in [-1,1]:
   me=bpy.data.meshes.new('Drawn attached sweat');pts=[(0,.065,0),(-.023,-.015,0),(-.018,-.035,0),(0,-.043,0),(.018,-.035,0),(.023,-.015,0)];me.from_pydata(pts,[],[tuple(range(6))]);m=bpy.data.materials.get('Sweat ink cyan')
   if not m:
    m=ink().copy();m.name='Sweat ink cyan';p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Base Color'].default_value=(.24,.65,.76,1);p.inputs['Emission Color'].default_value=(.24,.65,.76,1)
   me.materials.append(m);self.drops.append(g.obj('Attached illustrated temple sweat',me,(sign*.30,.015,.006),self.head))
  self.contacts=[shadow(g,(sign*.15,0),.06,.04,self.root,z=.002) for sign in [-1,1]]
 def pose(self,f,cam,expression='smile',hands=None,sweat=False):
  q=cam.rotation_euler.to_quaternion();self.head.rotation_euler=q.to_euler();self.body.rotation_euler=q.to_euler();key(self.head,'rotation_euler',f);key(self.body,'rotation_euler',f)
  blink=(f+(19 if self.who=='female' else 0))%103 in [0,1,2]
  for p,o in self.faces.items():o.scale=(1,)*3 if p==('blink' if blink else expression) else (0,)*3;key(o,'scale',f)
  for o in self.drops:o.scale=(1,)*3 if sweat else (0,)*3;key(o,'scale',f)
  right=q@V((1,0,0));up=q@V((0,1,0));front=q@V((0,0,1))
  for j,sign in enumerate([-1,1]):
   shoulder=V((0,0,.76))+q@V((sign*.18,.15,-.008));target=V(hands[j]) if hands else V((0,0,.76))+q@V((sign*.32,-.03,.012));elbow=shoulder+right*(sign*.16)-up*.16;curve_at(self.arms[j],[shoulder,elbow,target],f)
   # Small curled line encloses a gripped stem; never a sculpted fist.
   curve_at(self.hands[j],[target+up*.018,target+right*(sign*.025)+front*.004,target-up*.018],f)
   hip=V((0,0,.76))+q@V((sign*.105,-.27,-.008));foot=V((right.x*sign*.15,right.y*sign*.15,.014));knee=hip.lerp(foot,.53)+front*.018;toe=foot+V((right.x*sign*.055,right.y*sign*.055,0));curve_at(self.legs[j],[hip,knee,foot],f);curve_at(self.feet[j],[foot,toe],f);self.contacts[j].location=(foot.x,foot.y,.002);key(self.contacts[j],'location',f)
