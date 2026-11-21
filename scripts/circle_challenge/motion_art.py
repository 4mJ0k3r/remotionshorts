"""Generate the separate body and facial plates used by the motion pass."""
import array
import json
import math
import subprocess
from assets import OUT, draw_actor

assets = OUT/'motion_assets'
assets.mkdir(exist_ok=True)
actors = {
    'you': ['happy','belly','shock','panic','squat','smug','phone','shout','hug'],
    'host': ['happy','sniff','run','shock'],
    'rival': ['happy','cry','run'],
    'mom': ['raise','hug','smug'],
    'operator': ['press','shock'],
    'extra': ['choke','sniff'],
}
for who, poses in actors.items():
    for pose in poses:
        body, head = draw_actor(who,pose,motion=True)
        body.save(assets/f'{who}_{pose}_body.png')
        head.save(assets/f'{who}_{pose}_head.png')
        for name, opts in [('blink',{'blink':True}),('left',{'turn':-32}),('right',{'turn':32})]:
            draw_actor(who,pose,motion=True,**opts)[1].save(assets/f'{who}_{pose}_{name}.png')
for who, pose in [('rival','cry'),('you','shout'),('you','phone')]:
    for index, height in enumerate((8,23,48,76,110)):
        draw_actor(who,pose,motion=True,mouth=height)[1].save(assets/f'{who}_{pose}_mouth{index}.png')

audio = 'C:/Users/lavis/Downloads/ElevenLabs_2026-11-10T20_54_05_Viraj - Rich, Confident and Expressive_pvc_s40_sim75_v4.mp3'
samples = array.array('h',subprocess.check_output(['ffmpeg','-v','error','-i',audio,'-ac','1','-ar','12000','-f','s16le','-']))
rms = [math.sqrt(sum(v*v for v in samples[i:i+400])/400) for i in range(0,len(samples),400)]
(assets/'speech.json').write_text(json.dumps(rms))
