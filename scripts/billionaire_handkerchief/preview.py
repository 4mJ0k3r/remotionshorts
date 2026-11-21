"""Render and resume a caption-free 540p preview, one Blender cut at a time."""
import hashlib
import json
import os
import sys
import time
import traceback
from pathlib import Path

import bpy
from mathutils import Vector

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from shots import CAMERAS, DISSOLVE_CUTS, DISSOLVE_LENGTH

OUT=HERE.parents[1]/'renders'/HERE.name
MASTER=OUT/'billionaire_handkerchief.blend'
WORK=OUT/'preview_work_540p'
CUTS=json.loads((HERE/'cuts.json').read_text(encoding='utf-8'))


def bounds(cut):
    return cut['start'],cut['end']-int(cut['id']!=len(CUTS))


def verify_animation(scene, groups):
    """Inspect actual camera curves at every frame and focus at each cut midpoint."""
    camera=scene.camera
    focus=camera.data.dof.focus_object
    assert camera.data.dof.use_dof and focus
    assert len(scene.timeline_markers)==len(CUTS)==len(CAMERAS)
    assert not any(n.type in ('ALPHAOVER','IMAGE') for n in scene.node_tree.nodes)
    channels=sorted((fc for fc in camera.animation_data.action.fcurves if fc.data_path=='location'),key=lambda fc:fc.array_index)
    assert len(channels)==3
    previous=None;verified=0;drifts=[];lid_count=0
    for cut,(_,camera_point,target,_) in zip(CUTS,CAMERAS):
        num=cut['id'];first,last=bounds(cut)
        start=Vector(fc.evaluate(first) for fc in channels)
        end=Vector(fc.evaluate(last) for fc in channels)
        travel=(end-start).length/(Vector(target)-Vector(camera_point)).length
        assert .08<=travel<=.15,(num,travel)
        drifts.append(round(travel,5))
        for frame in range(first,last+1):
            position=Vector(fc.evaluate(frame) for fc in channels)
            assert previous is None or (position-previous).length>1e-5,(num,frame)
            previous=position;verified+=1
        scene.frame_set((first+last)//2)
        depsgraph=bpy.context.evaluated_depsgraph_get()
        active=[constraint for constraint in focus.constraints if constraint.influence==1]
        assert len(active)<=1,(num,active)
        target_pos=focus.evaluated_get(depsgraph).matrix_world.translation
        if active:
            expected=active[0].target.evaluated_get(depsgraph).matrix_world.translation
            assert (target_pos-expected).length<.001,(num,target_pos,expected)
        evaluated=camera.evaluated_get(depsgraph)
        direction=evaluated.matrix_world.to_quaternion()@Vector((0,0,-1))
        assert (target_pos-evaluated.matrix_world.translation).dot(direction)>0,num
        for lid in (o for o in groups[num].objects if o.name.startswith('Horizontal lid aperture')):
            curve=next(fc for fc in lid.animation_data.action.fcurves if fc.data_path=='scale' and fc.array_index==1)
            assert min(k.co.y for k in curve.keyframe_points)<.05 and max(k.co.y for k in curve.keyframe_points)>.99,(num,lid.name)
            lid_count+=1
        if num in (14,15,23):
            mouth=next(o for o in groups[num].objects if o.name.startswith('Articulated mouth'))
            curve=next(fc for fc in mouth.animation_data.action.fcurves if fc.data_path=='scale' and fc.array_index==1)
            values=[k.co.y for k in curve.keyframe_points]
            assert max(values)-min(values)>.3,(num,values)
    assert verified==3270
    return {'cuts':len(drifts),'frames_with_camera_motion':verified,'minimum_drift':min(drifts),'maximum_drift':max(drifts),'blink_channels':lid_count,'voiced_cuts':[14,15,23]}


def dissolve_handle(scene, shot_camera, cut, camera_channels, work):
    start,end=bounds(cut)
    boundary=end+1
    folder=work/'handles'/str(boundary);folder.mkdir(parents=True,exist_ok=True)
    if all((folder/f'handle_{i:02d}.png').is_file() for i in range(1,DISSOLVE_LENGTH+1)):return
    scene.frame_set(end)
    camera=shot_camera.copy();camera.data=shot_camera.data.copy()
    camera.animation_data_clear();camera.data.animation_data_clear()
    scene.collection.objects.link(camera);scene.camera=camera
    marker=next(marker for marker in scene.timeline_markers if marker.frame==start)
    original_marker_camera=marker.camera
    marker.camera=camera
    last=shot_camera.location.copy()
    velocity=Vector((channel.evaluate(end)-channel.evaluate(start))/(end-start) for channel in camera_channels)
    settings=scene.render
    file_format=settings.image_settings.file_format;filepath=settings.filepath
    try:
        settings.image_settings.file_format='PNG'
        settings.image_settings.compression=12
        for i in range(1,DISSOLVE_LENGTH+1):
            target=folder/f'handle_{i:02d}.png'
            if target.exists():continue
            camera.location=last+velocity*i
            intermediate=folder/f'partial_{i:02d}.png';settings.filepath=str(intermediate)
            bpy.ops.render.render(write_still=True,scene=scene.name)
            if not intermediate.is_file() or intermediate.stat().st_size<=1024:raise RuntimeError(f'Failed to render dissolve {boundary} handle {i}')
            intermediate.replace(target)
    finally:
        settings.image_settings.file_format=file_format;settings.filepath=filepath
        marker.camera=original_marker_camera
        scene.camera=shot_camera
        data=camera.data;bpy.data.objects.remove(camera,do_unlink=True);bpy.data.cameras.remove(data)


def queue(scene,master=False,background=False):
    work=OUT/'master_work_1080p' if master else WORK
    work.mkdir(exist_ok=True,parents=True)
    parts=work/'parts';parts.mkdir(exist_ok=True)
    temporary=work/'in_progress';temporary.mkdir(exist_ok=True)
    state_path=work/'progress.json'
    with MASTER.open('rb') as source:master_digest=hashlib.file_digest(source,'sha256').hexdigest()
    source_path=work/'master_sha256.txt'
    if source_path.exists() and source_path.read_text().strip()!=master_digest:
        raise RuntimeError('The preview work folder belongs to a different saved master')
    source_path.write_text(master_digest)
    stages=[collection for collection in scene.collection.children if 'bh_stage' in collection]
    groups={int(group['bh_cut']):group for stage in stages for group in stage.children if 'bh_cut' in group}
    assert len(stages)==7 and len(groups)==len(CUTS)
    initial_frame=scene.frame_current
    audit=verify_animation(scene,groups)
    (work/'animation_checks.json').write_text(json.dumps(audit,indent=2))
    shot_camera=scene.camera
    camera_channels=sorted((fc for fc in shot_camera.animation_data.action.fcurves if fc.data_path=='location'),key=lambda fc:fc.array_index)
    settings=scene.render
    original={key:getattr(settings,key) for key in ('frame_map_old','frame_map_new','resolution_percentage','filepath','use_file_extension','compositor_device','compositor_precision')}
    original_format=settings.image_settings.file_format
    original_samples=scene.eevee.taa_render_samples
    original_range=(scene.frame_start,scene.frame_end)
    ffmpeg=settings.ffmpeg
    original_ffmpeg={key:getattr(ffmpeg,key) for key in ('format','codec','constant_rate_factor','ffmpeg_preset','gopsize','audio_codec','use_autosplit')}
    settings.resolution_percentage=100 if master else 50;settings.use_file_extension=True
    scene.eevee.taa_render_samples=32 if master else 16
    if master:assert scene.render.use_motion_blur and abs(scene.render.motion_blur_shutter-.65)<.001
    gpu_compositor=master and os.environ.get('BH_GPU_COMPOSITOR')=='1'
    if gpu_compositor:
        settings.compositor_device='GPU'
        settings.compositor_precision='FULL'
        sample=work/'gpu_compositor_0741.png'
        if not sample.exists():
            num=12;active_stage=CAMERAS[num-1][0]
            for collection in stages:collection.hide_render=int(collection['bh_stage'])!=active_stage
            for number,collection in groups.items():collection.hide_render=number!=num
            scene.frame_set(741)
            settings.image_settings.file_format='PNG'
            settings.filepath=str(sample)
            bpy.ops.render.render(write_still=True,scene=scene.name)
            if not sample.is_file():raise RuntimeError('GPU compositor sample did not render')
            scene.frame_set(initial_frame)
    def configure_video_output():
        settings.image_settings.file_format='FFMPEG'
        ffmpeg.format='MPEG4';ffmpeg.codec='H264';ffmpeg.constant_rate_factor='LOSSLESS' if master else 'HIGH';ffmpeg.ffmpeg_preset='REALTIME'
        ffmpeg.gopsize=30;ffmpeg.audio_codec='NONE';ffmpeg.use_autosplit=False

    compositor_device=settings.compositor_device
    done=[];elapsed_start=time.monotonic();current={}

    def report(state,**info):
        payload={'state':state,'cuts_done':done,'seconds':round(time.monotonic()-elapsed_start,1),
                 'compositor_device':compositor_device,**info}
        temp=state_path.with_suffix('.tmp');temp.write_text(json.dumps(payload));temp.replace(state_path)

    def restore():
        for collection in (*stages,*groups.values()):collection.hide_render=False
        settings.image_settings.file_format=original_format
        for key,value in original.items():setattr(settings,key,value)
        scene.eevee.taa_render_samples=original_samples
        scene.frame_start,scene.frame_end=original_range
        scene.frame_set(initial_frame)
        if written in bpy.app.handlers.render_write:bpy.app.handlers.render_write.remove(written)
        for key,value in original_ffmpeg.items():
            if value!='':setattr(ffmpeg,key,value)

    def written(render_scene):
        if render_scene!=scene or not current:return
        frame=scene.frame_current
        if frame==current['start'] or frame%10==0:
            report('rendering',**current,frame=frame)

    def tick():
        try:
            while len(done)<len(CUTS):
                cut=CUTS[len(done)];num=cut['id'];start,end=bounds(cut)
                destination=parts/f'cut_{num:02d}.mp4'
                active_stage=CAMERAS[num-1][0]
                for collection in stages:collection.hide_render=int(collection['bh_stage'])!=active_stage
                for key,collection in groups.items():collection.hide_render=key!=num
                scene.frame_start=start;scene.frame_end=end
                if destination.is_file() and destination.stat().st_size>1024:
                    if master and end+1 in DISSOLVE_CUTS:dissolve_handle(scene,shot_camera,cut,camera_channels,work)
                    done.append(num)
                    continue
                prefix=f'cut_{num:02d}_'
                for partial in temporary.glob(f'{prefix}*'):
                    if partial.is_file() and partial.suffix in ('.mp4','.mkv'):partial.unlink()
                configure_video_output()
                settings.filepath=str(temporary/prefix)
                current.update(cut=num,start=start,end=end)
                report('rendering',**current,frame=start-1)
                result=bpy.ops.render.render(animation=True,scene=scene.name)
                movies=list(temporary.glob(f'{prefix}*.mp4'))
                if 'FINISHED' not in result or len(movies)!=1 or movies[0].stat().st_size<=1024:
                    raise RuntimeError(f'Cut {num} did not produce one complete MP4: {result}, {movies}')
                movies[0].replace(destination);current.clear()
                if master and end+1 in DISSOLVE_CUTS:
                    report('dissolve handle',cut=num,frame=end)
                    dissolve_handle(scene,shot_camera,cut,camera_channels,work)
                done.append(num)
                report('rendering',frame=end)
                return .12
            try:
                restore()
            except Exception:
                report('complete',frame=3270,restore_error=traceback.format_exc())
            else:
                report('complete',frame=3270)
            return None
        except Exception:
            error=traceback.format_exc()
            try:
                restore()
            except Exception:
                error+='\nRender settings restoration:\n'+traceback.format_exc()
            report('failed',**current,error=error)
            if background:raise
            return None

    bpy.app.handlers.render_write.append(written)
    report('queued',frame=0)
    if background:
        while tick() is not None:pass
    else:bpy.app.timers.register(tick,first_interval=.4)


if __name__=='__main__':
    queue(bpy.context.scene)
