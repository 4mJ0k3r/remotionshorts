"""Wait for Blender's completed preview, then mux and verify the release file."""
import json
import subprocess
import time
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT/'renders/circle_challenge'
AUDIO = Path('C:/Users/lavis/Downloads/ElevenLabs_2026-11-10T20_54_05_Viraj - Rich, Confident and Expressive_pvc_s40_sim75_v4.mp3')
V2 = len(sys.argv)>1 and sys.argv[1]=='v2'
STEM = 'preview_v2' if V2 else 'preview'
RAW = OUT/('circle_challenge_preview_v2_raw.mp4' if V2 else 'circle_challenge_raw.mp4')
FINAL = OUT/f'circle_challenge_{STEM}_540p.mp4'
TEMP = OUT/f'circle_challenge_{STEM}_muxing.mp4'
SIZE = (540, 960)
if len(sys.argv)>1 and sys.argv[1]=='1080p':
    STEM = 'render_1080p'
    RAW = OUT/'circle_challenge_1080p_raw.mp4'
    FINAL = OUT/'circle_challenge_1080p.mp4'
    TEMP = OUT/'circle_challenge_1080p_muxing.mp4'
    SIZE = (1080, 1920)

def probe(file):
    result = subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(file)])
    return json.loads(result)

def verify_video(info):
    video = next(stream for stream in info['streams'] if stream['codec_type']=='video')
    actual = (video['width'],video['height'],video['r_frame_rate'],int(video['nb_frames']))
    if actual != (*SIZE,'30/1',2205):
        raise RuntimeError(f'Unexpected preview video settings: {actual}')
    if abs(float(info['format']['duration'])-73.5) > .035:
        raise RuntimeError('Unexpected preview duration')

if __name__ == '__main__':
    while not (OUT/f'{STEM}_progress.json').exists():
        time.sleep(5)
    while True:
        info = json.loads((OUT/f'{STEM}_progress.json').read_text())
        if info['status']=='complete':
            break
        if info['status']=='failed':
            raise RuntimeError(f'Blender render failed at frame {info["frame"]}')
        time.sleep(10)
    verify_video(probe(RAW))
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y','-i',str(RAW),'-i',str(AUDIO),
                    '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k',
                    '-metadata:s:a:0','language=hin','-t','73.5','-shortest','-movflags','+faststart',str(TEMP)],check=True)
    info = probe(TEMP)
    verify_video(info)
    assert any(stream['codec_type']=='audio' and stream['codec_name']=='aac' for stream in info['streams'])
    TEMP.replace(FINAL)
    (OUT/f'{STEM}_probe.json').write_text(json.dumps(info,indent=2))
    plan = json.loads((ROOT/'scripts/circle_challenge/plan.json').read_text())
    marks = sorted({a-1 for a,_,_ in plan['cuts']} | {964,1614,1739,1909,2094,2205})
    cuts = {'shots':[{'id':i+1,'a':a,'b':b} for i,(a,b) in enumerate(zip(marks,marks[1:]))]}
    shot_map = OUT/f'{STEM}_shots.json'
    shot_map.write_text(json.dumps(cuts,indent=2))
    subprocess.run(['python',str(ROOT/'scripts/short_qa.py'),str(FINAL),str(OUT/f'{STEM}_qa'),str(shot_map)],check=True)
    print(FINAL)
