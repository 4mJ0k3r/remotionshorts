import bpy
from pathlib import Path
s=bpy.context.scene;m=bpy.data.materials['V13 copper jacket'];nt=m.node_tree;l=nt.links;bs=nt.nodes.get('Principled BSDF');out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');rgb=nt.nodes.new('ShaderNodeShaderToRGB');mult=nt.nodes.new('ShaderNodeVectorMath');mult.operation='MULTIPLY';mult.inputs[1].default_value=(1.24,.70,.33);em=nt.nodes.new('ShaderNodeEmission');l.new(bs.outputs[0],rgb.inputs[0]);l.new(rgb.outputs[0],mult.inputs[0]);l.new(mult.outputs[0],em.inputs[0]);l.new(em.outputs[0],out.inputs[0])
bs=bpy.data.materials['V13 polished buckle'].node_tree.nodes.get('Principled BSDF');bs.inputs['Metallic'].default_value=.4;bs.inputs['Emission Strength'].default_value=.35
bpy.ops.wm.save_as_mainfile(filepath='D:/remotionshorts/renders/slow_eddie_v13/slow_eddie_v13.blend')
