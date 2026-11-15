"""Render an approved versioned preview or native 1080p master with resume."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import time
import wave

from PIL import Image
from run import launch,ROOT,OUT,BLENDER,LOCK


def digest(path):
    with path.open('rb') as file:
        return hashlib.file_digest(file,'sha256').hexdigest()


def valid_frame(frame,version=2,resolution=540):
    tag=f'v{version}' if resolution==540 else f'v{version}_{resolution}p'
    path=OUT/f'{tag}_frames'/f'frame_{frame:04}.png'
    if not path.exists():
        return False
    try:
        with Image.open(path) as image:
            if image.size!=(resolution,resolution*16//9):
                return False
            image.verify()
        return True
    except (OSError,SyntaxError):
        return False


def main(version=2,resolution=540,check_only=False):
    started=time.time()
    tag=f'v{version}' if resolution==540 else f'v{version}_{resolution}p'
    height=resolution*16//9
    frozen=OUT/f'elevator_leak_{tag}_render_source.blend'
    source=frozen if resolution==1080 else ROOT/'elevator_leak.blend'
    audio=OUT/f'narration_{tag}.wav' if resolution==1080 else OUT/'narration.wav'
    manifest_path=OUT/f'{tag}_render_manifest.json'
    if not BLENDER.is_file() or not source.is_file() or not audio.is_file():
        raise RuntimeError('Required Blender source or audio is missing. Prepare the selected preset first.')
    for executable in ['ffmpeg','ffprobe']:
        if not shutil.which(executable):
            raise RuntimeError('Required executable is unavailable: '+executable)
    with wave.open(str(audio)) as narration:
        assert narration.getframerate()==48000
        assert abs(narration.getnframes()/narration.getframerate()-71.5)<.001
    source_hash=digest(source)
    audio_hash=digest(audio)
    if resolution==1080:
        ready=json.loads((OUT/f'{tag}_ready.json').read_text())
        assert ready['source_sha256']==source_hash
        assert ready['audio_sha256']==audio_hash
        assert (ready['width'],ready['height'],ready['fps'],ready['frames'],ready['samples'])==(1080,1920,30,2145,16)
    if check_only:
        print(json.dumps({'state':'ready_not_started','source':str(source),'audio':str(audio),'width':resolution,'height':height,'fps':30,'frames':2145,'samples':16,'frame_folder':str(OUT/f'{tag}_frames'),'movie':str(OUT/f'elevator_leak_{tag}_master.mp4'),'gpu_lock_present':LOCK.exists(),'free_disk_gb':round(shutil.disk_usage(OUT).free/1024**3,1),'existing_frames':len(list((OUT/f'{tag}_frames').glob('frame_*.png')))},indent=2))
        return
    if manifest_path.exists():
        manifest=json.loads(manifest_path.read_text())
        if manifest['source_sha256']!=source_hash:
            raise RuntimeError(f'Source changed after the V{version} render began. Preserve the existing run before starting another version.')
        assert manifest['audio_sha256']==audio_hash
        assert (manifest['width'],manifest['height'],manifest['samples'])==(resolution,height,16)
    else:
        if source.resolve()!=frozen.resolve():
            shutil.copy2(source,frozen)
        manifest={'source':str(frozen),'source_sha256':source_hash,'audio_sha256':audio_hash,'frame_start':1,'frame_end':2145,'fps':30,'width':resolution,'height':height,'samples':16,'started':time.time(),'completed_chunks':[]}
        manifest_path.write_text(json.dumps(manifest,indent=2))
    assert digest(frozen)==manifest['source_sha256']
    manifest['state']='rendering'
    manifest_path.write_text(json.dumps(manifest,indent=2))
    for start in range(1,2146,150):
        end=min(start+149,2145)
        missing=[frame for frame in range(start,end+1) if not valid_frame(frame,version,resolution)]
        if not missing:
            continue
        for attempt in range(3):
            try:
                launch('movie',min(missing),end,version,resolution)
                missing=[frame for frame in range(start,end+1) if not valid_frame(frame,version,resolution)]
                if missing:
                    raise RuntimeError('Incomplete chunk '+str(missing[:5]))
                break
            except RuntimeError:
                if attempt==2:
                    raise
                missing=[frame for frame in range(start,end+1) if not valid_frame(frame,version,resolution)]
                if not missing:
                    break
                print('Retrying our incomplete chunk from frame',min(missing),flush=True)
        manifest['completed_chunks'].append([start,end])
        manifest_path.write_text(json.dumps(manifest,indent=2))
        print(f'CHUNK_VERIFIED {end}/2145; elapsed {time.time()-started:.1f}s',flush=True)
    assert all(valid_frame(frame,version,resolution) for frame in range(1,2146))
    final=OUT/f'elevator_leak_{tag}_master.mp4'
    staging=OUT/f'elevator_leak_{tag}_muxing.mp4'
    subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-start_number','1','-i',str(OUT/f'{tag}_frames'/'frame_%04d.png'),'-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t','71.5','-movflags','+faststart',str(staging)],check=True)
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(staging)],text=True))
    video=next(stream for stream in probe['streams'] if stream['codec_type']=='video')
    audio=next(stream for stream in probe['streams'] if stream['codec_type']=='audio')
    assert (video['width'],video['height'],int(video['nb_frames']),video['r_frame_rate'])==(resolution,height,2145,'30/1')
    assert abs(float(video['duration'])-71.5)<.001
    assert abs(float(audio['duration'])-71.5)<.04
    staging.replace(final)
    (OUT/f'{tag}_delivery_specs.json').write_text(json.dumps(probe,indent=2))
    import ast
    tree=ast.parse((ROOT/'scripts/elevator_leak/runtime.py').read_text())
    cuts=next(ast.literal_eval(node.value) for node in tree.body if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id=='CUTS' for target in node.targets))
    shots={'shots':[{'id':index+1,'a':a-1,'b':b} for index,(a,b,name) in enumerate(cuts)]}
    (OUT/f'{tag}_shots.json').write_text(json.dumps(shots,indent=2))
    subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(final),str(OUT/f'qa_{tag}'),str(OUT/f'{tag}_shots.json')],check=True)
    manifest['state']='complete'
    manifest['finished']=time.time()
    manifest['movie']=str(final)
    manifest_path.write_text(json.dumps(manifest,indent=2))
    (OUT/f'movie_{tag}_progress.json').write_text(json.dumps({'state':'complete','frame':2145,'total':2145,'movie':str(final)}))
    print(f'V{version}_MASTER_READY',final,flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--version',type=int,choices=[2,3],default=2)
    parser.add_argument('--resolution',type=int,choices=[540,1080],default=540)
    parser.add_argument('--check-only',action='store_true')
    arguments=parser.parse_args()
    main(arguments.version,arguments.resolution,arguments.check_only)
