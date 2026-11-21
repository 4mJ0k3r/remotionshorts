"""One consolidated geometric framing pass, before calibration. No rendering."""
import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
from bpy_extras.object_utils import world_to_camera_view
OUT=Path(r'D:\remotionshorts\renders\hair_sensor');rows=json.loads((OUT/'shots_v3.json').read_text())['shots'];report=[]
for row in rows:
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;c=bpy.data.objects[row['camera']];s.camera=c
    heads=[o for o in s.objects if 'cream shaded head and stylized hair' in o.name]
    drones=[o for o in s.objects if o.name.startswith('V3_Drone')]
    heads=[o for o in heads if not o.hide_render]
    def bounds(frame):
        s.frame_set(frame+1);s.frame_set(frame);s.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get();dg.update();ce=c.evaluated_get(dg);pts=[]
        for head in heads:
            # Visible ink silhouette within the transparent raster card.
            for x in (-.49,.49):
                    for y in (-.52,.51):pts.append(head.evaluated_get(dg).matrix_world@V((x,y,0)))
        for drone in drones:
            for ob in drone.children_recursive:
                if ob.type!='MESH':continue
                if row['kind'] in ('beauty','home') and 'PCB' not in ob.name and 'electrode' not in ob.name.lower():continue
                ev=ob.evaluated_get(dg);pts.extend(ev.matrix_world@V(v) for v in ev.bound_box)
        uv=[world_to_camera_view(s,ce,p) for p in pts]
        return [min(p.x for p in uv),max(p.x for p in uv),min(p.y for p in uv),max(p.y for p in uv)] if uv else None
    samples=[row['start_frame'],row['sample'],row['end_frame']]
    original=[bounds(f) for f in samples];valid=[v for v in original if v]
    factor=1
    if valid:
        factor=max(1,max(max(abs(v[0]-.5),abs(v[1]-.5))/.44 for v in valid),max(max(abs(v[2]-.5),abs(v[3]-.5))/.37 for v in valid))
        if factor>3:raise RuntimeError('Invalid projection state: '+row['shot']+' '+str(factor))
        if factor>1.01:
            factor*=1.03
            for f in range(row['start_frame'],row['end_frame']+1):
                s.frame_set(f);q=c.rotation_euler.to_quaternion();d=c.data.dof.focus_distance;target=c.location+q@V((0,0,-d));c.location=target+(c.location-target)*factor;c.keyframe_insert('location',frame=f);c.data.dof.focus_distance=d*factor;c.data.keyframe_insert('dof.focus_distance',frame=f)
    report.append({'shot':row['shot'],'camera_pullback_factor':round(factor,3),'before':original,'after':[bounds(f) for f in samples],'fast_gi_method':s.eevee.fast_gi_method,'fast_gi_distance':s.eevee.fast_gi_distance,'raytracing':s.eevee.use_raytracing})
    print('PREFLIGHT',row['shot'],round(factor,3),flush=True)
(OUT/'v3_projection.json').write_text(json.dumps(report,indent=2));bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v3.blend'));print('V3 geometric preflight complete',flush=True)
