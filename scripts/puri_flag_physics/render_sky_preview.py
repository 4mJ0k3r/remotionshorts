"""Sky revision: separate 360p/8-sample first-20-second review only."""
import sys
import time
from pathlib import Path
import bpy

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import build_puri_flag_physics as scene
from timeline import OUT

def make_scene():
    sc=scene.build()
    # A fixed, emission-lit backdrop keeps the existing lighting and shadows.
    sky=scene.card('Open sky behind mandir',300,300,scene.card_material(OUT/'sprites'/'sky_v2.png',False))
    sky.location=(0,40,17.5);sky.rotation_euler=(scene.pi/2,0,0)
    for loop,uv in zip(sky.data.uv_layers.active.data,((.5-150/140,.5-150/105),(.5+150/140,.5-150/105),(.5+150/140,.5+150/105),(.5-150/140,.5+150/105))):loop.uv=uv
    for node in sky.data.materials[0].node_tree.nodes:
        if node.type=='TEX_IMAGE':node.extension='EXTEND'
    # Limit the old diagnostic stage to the actual courtyard; it must not
    # create a black horizon halfway up the new sky in crown close-ups.
    ground=bpy.data.objects['Ground support']
    for vertex in ground.data.vertices:
        vertex.co.x*=.20;vertex.co.y*=.20
    sc['revision']='Sky background; English graphics disabled in video assembly'
    sc.render.resolution_percentage=100
    sc.render.resolution_x=360;sc.render.resolution_y=640
    sc.eevee.taa_render_samples=8
    sc.frame_set(80)
    for image in bpy.data.images:
        if image.source=='FILE':image.pack()
    scene.embed_runtime(sc)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'puri_flag_physics_sky_v2.blend'))
    return sc

phase=sys.argv[sys.argv.index('--')+1]
sc=make_scene()
folder=OUT/'frames_sky_v2_360p';folder.mkdir(exist_ok=True)
sc.render.image_settings.file_format='PNG';sc.render.image_settings.color_mode='RGB';sc.render.image_settings.compression=6
frames=(80,450) if phase=='sheet' else range(1,601)
start=time.time()
for f in frames:
    final=folder/f'f{f:04}.png'
    if phase=='preview' and final.exists():continue
    partial=folder/f'f{f:04}.part.png'
    sc.frame_set(f);sc.render.filepath=str(partial)
    bpy.ops.render.render(write_still=True);partial.replace(final)
    if phase=='sheet' or f%30==0:print(f'PROBE sky review frame={f}/600 elapsed={time.time()-start:.1f}s',flush=True)
