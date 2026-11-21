import bpy,json,hashlib
from pathlib import Path
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v12';s=bpy.context.scene;t=bpy.data.texts['slow_eddie_v12_runtime.py'];old=t.as_string();new=(R/'scripts/slow_eddie_v12/runtime.py').read_text();assert old.replace('b.hide_render=not 24<=f<=126','b.hide_render=not 31<=f<=126')==new
original=json.loads((P/'source_hash.json').read_text())['sha256'];t.from_string(new);exec(compile(t.as_string(),t.name,'exec'));s.frame_set(1);update(s);bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v12.blend'));sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(P/'launch_patch_manifest.json').write_text(json.dumps({'original_source_sha256':original,'patched_source_sha256':sha(P/'slow_eddie_v12.blend'),'changed_runtime_only':'bullet visibility starts31 instead24; all other runtime bytes identical','affected_frames':[24,25,26,27,28,29,30],'unchanged_ranges':[[1,23],[31,300]],'original_runtime_sha256':sha(R/'scripts/slow_eddie_v12/runtime_before_launch_patch.py'),'patched_runtime_sha256':sha(R/'scripts/slow_eddie_v12/runtime.py')},indent=2))
s.render.resolution_percentage=100
for f in range(24,31):
 s.frame_set(f);update(s);s.render.filepath=str(P/f'frames/frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
