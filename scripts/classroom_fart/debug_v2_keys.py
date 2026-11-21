import bpy,json
s=bpy.data.scenes['Classroom_Master'];bpy.context.window.scene=s
for f in [300,1007,1360,1446,1466,1484,1635]:
    s.frame_set(f);s.view_layers[0].update();dg=bpy.context.evaluated_depsgraph_get()
    for name in ['you oval grounded foot -1','char_you glossy royal-blue pelvis']:
        o=bpy.data.objects[name];print('KEYDEBUG',f,name,'local',list(o.location),'world',list(o.matrix_world.translation),'eval',list(o.evaluated_get(dg).matrix_world.translation),'curve',[(fc.array_index,fc.evaluate(f)) for fc in o.animation_data.action.fcurves if fc.data_path=='location'],flush=True)
