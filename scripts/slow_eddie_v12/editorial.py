import bpy,json
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v12');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_v12_runtime.py'].as_string(),'runtime','exec'));s.render.resolution_percentage=100
# Additional gun-side launch coverage; recorded as a named post-render editorial layer.
for f in range(24,34):
 s.frame_set(f);update(s);g=O['Challenger_revolver'];m=g.matrix_world@V((.35,0,.23));pos=m+V((.65,-1.15,.15));aim(pos,m+V((.20,0,0)),42);cam.data.sensor_fit='VERTICAL';cam.data.dof.focus_object=None;cam.data.dof.focus_distance=(m-cam.location).length;cam.data.dof.aperture_fstop=2;s.render.filepath=str(P/f'launch/frame_{f:04d}.png');bpy.ops.render.render(write_still=True)
(P/'editorial_layers.json').write_text(json.dumps({'launch_overlay':{'frames':[24,33],'dissolve_frames':[24,26],'weights':[0,.5,1]},'hands_dissolve':{'frames':[255,258],'weights':[0,1/3,2/3,1],'background':'frame0254 held for four-frame dissolve'}},indent=2))



