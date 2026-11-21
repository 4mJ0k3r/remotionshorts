import bpy,json,math
from pathlib import Path
from mathutils import Vector as V
P=Path('D:/remotionshorts/renders/slow_eddie');s=bpy.context.scene
exec(compile(bpy.data.texts['slow_eddie_runtime.py'].as_string(),'runtime','exec'))
(P/'embedded_runtime_review.py').write_text(bpy.data.texts['slow_eddie_runtime.py'].as_string())
