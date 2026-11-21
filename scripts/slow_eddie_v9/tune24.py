import bpy
from pathlib import Path
P=Path('D:/remotionshorts/renders/slow_eddie_v9');s=bpy.context.scene;s.eevee.taa_render_samples=24;s.eevee.shadow_pool_size='128';bpy.ops.wm.save_as_mainfile(filepath=str(P/'slow_eddie_v9.blend'))
