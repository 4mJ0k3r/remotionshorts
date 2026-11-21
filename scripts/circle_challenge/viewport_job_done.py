import bpy,json
from pathlib import Path
s=bpy.context.scene
s.frame_set(330)
area=next(a for a in bpy.context.screen.areas if a.type=='CONSOLE')
area.type='VIEW_3D';area.spaces.active.region_3d.view_perspective='CAMERA'
area.spaces.active.shading.type='MATERIAL'
area.spaces.active.region_3d.view_camera_zoom=5
Path('D:/remotionshorts/renders/circle_challenge/scene_inventory.json').write_text(json.dumps({'objects':len(s.objects),'frames':s.frame_end,'images':len(bpy.data.images),'engine':s.render.engine},indent=2))
