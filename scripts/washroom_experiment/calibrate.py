"""Render only the fourteen authorized calibration frames."""
import bpy,json,traceback
from build import CUTS,OUT
def queue(scene,only=None):
 p=OUT/'calibration';p.mkdir(exist_ok=True)
 frames=tuple(only) if only is not None else tuple(f for _,_,f,_ in CUTS)
 status={'state':'queued','frames':[]}
 def tick():
  try:
   i=len(status['frames'])
   if i==len(frames):
    scene.render.resolution_percentage=100
    status['state']='complete';(p/'progress.json').write_text(json.dumps(status));return None
   f=frames[i]
   scene.frame_set(f);scene.render.resolution_percentage=50
   scene.render.image_settings.file_format='PNG'
   scene.render.filepath=str(p/f'{f:04d}.png')
   window=bpy.context.window
   previous=window.scene
   try:
    window.scene=scene
    bpy.ops.render.render(write_still=True,scene=scene.name)
   finally:
    window.scene=previous
   status['frames'].append(f);status['state']='rendering'
   (p/'progress.json').write_text(json.dumps(status))
   return .10
  except Exception:
   status.update(state='failed',error=traceback.format_exc())
   (p/'progress.json').write_text(json.dumps(status));return None
 (p/'progress.json').write_text(json.dumps(status))
 bpy.app.timers.register(tick,first_interval=.35)
