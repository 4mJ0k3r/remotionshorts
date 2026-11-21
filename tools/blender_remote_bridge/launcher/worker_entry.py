"""Load callbacks in a real module, independent of Blender's __main__ cleanup."""
import importlib.util
import os
from pathlib import Path
import sys
import bpy

# Suppress the welcome dialog for this launch through Blender's supported API.
# Do not persistently alter the user's saved preferences.
bpy.context.preferences.view.show_splash = False

module_name = '_launcher_blender_worker'
previous = sys.modules.get(module_name)
if previous:
    if bpy.app.timers.is_registered(previous.tick):
        bpy.app.timers.unregister(previous.tick)
# Windows Store's launcher can execute scripts without a useful __file__.
# The session path is supplied explicitly by our parent process.
session = Path(os.environ['BLENDER_BRIDGE_SESSION'])
path = session.parent.parent / 'worker_runtime.py'
spec = importlib.util.spec_from_file_location(module_name, path)
worker = importlib.util.module_from_spec(spec)
sys.modules[module_name] = worker
spec.loader.exec_module(worker)
worker.start()
