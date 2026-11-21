import bpy,json,hashlib
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v3');s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear()
for o in s.objects:
 if o.name=='Challenger_revolver' or o.name.startswith('Grip finger'):
  for i,m in enumerate(list(o.data.materials)):
   m=m.copy();o.data.materials[i]=m;m.use_nodes=True;nt=m.node_tree;out=next(n for n in nt.nodes if n.type=='OUTPUT_MATERIAL');source=out.inputs['Surface'].links[0].from_socket;tr=nt.nodes.new('ShaderNodeBsdfTransparent');mix=nt.nodes.new('ShaderNodeMixShader');mix.name='V3 prop fade';mix.inputs[0].default_value=1;nt.links.new(tr.outputs[0],mix.inputs[1]);nt.links.new(source,mix.inputs[2]);nt.links.new(mix.outputs[0],out.inputs[0])
t=bpy.data.texts['slow_eddie_v3_runtime.py'];t.clear();t.write(Path('D:/remotionshorts/scripts/slow_eddie_v3/runtime.py').read_text());exec(compile(t.as_string(),'runtime','exec'));s.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v3.blend'))
d=json.loads((P/'patch_mapping.json').read_text());d['additional_patch']={'frames':[210,218],'reason':'Gun/fingers opacity follows shoulder fade'};d['final_source_sha256']=hashlib.sha256((P/'slow_eddie_v3.blend').read_bytes()).hexdigest();d['unchanged_frames']=[[1,209],[219,271],[293,300]];(P/'patch_mapping.json').write_text(json.dumps(d,indent=2))
s.frame_set(216);update(s);s.render.resolution_percentage=50;s.render.filepath=str(P/'patch_cal_216.png');bpy.ops.render.render(write_still=True)
