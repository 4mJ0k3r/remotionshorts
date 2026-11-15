"""Package only the contiguous, valid rendered prefix after a user stop."""
import json, subprocess, argparse
from pathlib import Path
from PIL import Image
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'renders/sendha_namak_science'
parser=argparse.ArgumentParser();parser.add_argument('--version',type=int,default=2);args=parser.parse_args()
folder=OUT/('v2_frames' if args.version==2 else 'preview_frames')
last=0
for frame in range(1,1729):
    try:
        with Image.open(folder/f'frame_{frame:04}.png') as im:
            assert im.size==(540,960);im.verify()
    except (OSError,AssertionError):break
    last=frame
assert last>0,'No complete frames available'
target=OUT/('sendha_namak_v2_partial_540p.mp4' if args.version==2 else 'sendha_namak_partial_540p.mp4')
subprocess.run(['ffmpeg','-y','-v','error','-framerate','30','-start_number','1','-i',str(folder/'frame_%04d.png'),'-i',str(OUT/'narration.wav'),'-frames:v',str(last),'-t',str(last/30),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(target)],check=True)
probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(target)]))
video=next(s for s in probe['streams'] if s['codec_type']=='video')
assert int(video['nb_frames'])==last and (video['width'],video['height'])==(540,960)
subprocess.run(['ffmpeg','-v','error','-i',str(target),'-f','null','-'],check=True)
status={'state':'stopped_by_user','frames':last,'duration_seconds':last/30,'resolution':[540,960],'output':str(target),'audio':'matching narration prefix','full_preview_complete':False}
(OUT/('v2_partial_delivery.json' if args.version==2 else 'partial_delivery.json')).write_text(json.dumps(status,indent=2));print(json.dumps(status))
