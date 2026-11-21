import bpy
from pathlib import Path
import sys
sys.path.insert(0,'D:/remotionshorts/tools/V9_Parity_Packet/V9_Parity_Packet');import v9_patch_helpers as H
s=bpy.context.scene;nt=bpy.data.objects['Dusty Main Street'].data.materials[0].node_tree;l=nt.links;em=next(n for n in nt.nodes if n.type=='EMISSION');ramp=next(n for n in nt.nodes if n.type=='VALTORGB');noise=next(n for n in nt.nodes if n.type=='MAP_RANGE');mix=nt.nodes.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;l.new(ramp.outputs[0],mix.inputs[1]);l.new(noise.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],em.inputs[0])
m=bpy.data.materials['V9 rosette gold'];bs=m.node_tree.nodes.get('Principled BSDF');bs.inputs['Emission Color'].default_value=H.rgba('#E9C777');bs.inputs['Emission Strength'].default_value=.25
bpy.ops.wm.save_as_mainfile(filepath='D:/remotionshorts/renders/slow_eddie_v9/slow_eddie_v9.blend')
