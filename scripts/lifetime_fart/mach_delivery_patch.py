"""Delivery correction for the Mach shot, identified by the first master audit."""
import bpy, json, traceback
from mathutils import Vector
from pathlib import Path
from studio_overhaul import emission, stroke, vis, key
BASE=Path('D:/remotionshorts')
O=BASE/'out/lifetime_fart'
scene=bpy.context.scene;cam=scene.camera
cones=[o for o in scene.objects if o.name.startswith('ST_MachCone_')]
samples={}
for f in range(1426,1585):
 scene.frame_set(f);samples[f]=(cam.location.copy(),[(o.location.copy(),o.scale.copy()) for o in cones])
for f,(p,items) in samples.items():
 t=(f-1426)/158
 cam.location=p+Vector((.085*t,-.22*t,-.025*t));key(cam,'location',f)
 for i,(o,(pos,scale)) in enumerate(zip(cones,items)):
  o.location=pos+Vector((0,(.27+i*.11)*t,-(.73+i*.15)*t));key(o,'location',f)
  o.scale=(scale.x*(1+.24*t),scale.y*(1+.24*t),scale.z*(1+.08*t));key(o,'scale',f)
# Fast, intermittent air streaks track the real ascent through the set.
mat=emission('Mach receding air streak','b6dcff',1.1,.43)
col=bpy.data.collections['SET_STRATOSPHERE'];root=bpy.data.objects['ROOT_STRATOSPHERE']
for i in range(9):
 side=1 if i%2 else -1
 ob=stroke('Mach wake air streak',[(0,0,0),(.01,0,.28),(.032,0,.59)],.012,mat,root,col)
 vis(ob,[(1426,1584)])
 for f in range(1426,1585):
  t=((f-1426+i*8)%45)/45
  ob.location=(side*(.39+.083*i+.20*t),1.17+.09*i,3.2-4.65*t)
  k=(.56+.052*i)*(max(.001,4*t*(1-t)))**.4
  ob.scale=(k,k,k);key(ob,'location',f);key(ob,'scale',f)
scene.frame_set(100)
scene.render.filepath=str(O/'master_silent.mp4')
bpy.ops.wm.save_as_mainfile(filepath=str(BASE/'output/blender/lifetime_fart_full.blend'))
state=O/'mach_patch_progress.json'
state.write_text(json.dumps({'status':'queued'}))
def job():
 try:
  scene.frame_set(1504);scene.render.resolution_percentage=34
  scene.render.image_settings.file_format='PNG';scene.render.filepath=str(O/'cal_v5/1504.png')
  bpy.ops.render.render(write_still=True,scene=scene.name)
  scene.frame_start=1426;scene.frame_end=1584;scene.render.resolution_percentage=100
  scene.render.image_settings.file_format='FFMPEG'
  scene.render.ffmpeg.format='MPEG4';scene.render.ffmpeg.codec='H264'
  scene.render.ffmpeg.constant_rate_factor='HIGH';scene.render.ffmpeg.audio_codec='NONE'
  scene.render.filepath=str(O/'mach_patch.mp4')
  state.write_text(json.dumps({'status':'rendering'}));bpy.ops.render.render(animation=True,scene=scene.name)
  scene.frame_start=1;scene.frame_end=2715;scene.frame_set(100);scene.render.filepath=str(O/'master_silent.mp4')
  state.write_text(json.dumps({'status':'complete'}))
 except Exception:state.write_text(json.dumps({'status':'failed','error':traceback.format_exc()}))
 return None
bpy.app.timers.register(job,first_interval=.5)

