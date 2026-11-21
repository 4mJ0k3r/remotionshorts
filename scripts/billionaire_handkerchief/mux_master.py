"""Make the 1080p master from locked EEVEE cut renders and transition handles."""
import json
import subprocess
from fractions import Fraction
from pathlib import Path
from statistics import mean

from PIL import Image, ImageStat

from mux_preview import decoded_duplicate_frames, probe
from shots import DISSOLVE_CUTS, DISSOLVE_LENGTH, WHIP_CUTS

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'renders'/HERE.name
WORK=OUT/'master_work_1080p'
FINAL=OUT/'billionaire_handkerchief_master_1080p.mp4'
CUTS=json.loads((HERE/'cuts.json').read_text(encoding='utf-8'))


def ffmpeg(*args):
    subprocess.run(['ffmpeg','-hide_banner','-loglevel','error','-y',*map(str,args)],check=True)


def check_video(path,count,decoded=False):
    info=probe(path,decoded)
    stream=next(s for s in info['streams'] if s['codec_type']=='video')
    assert (stream['codec_name'],stream['width'],stream['height'])==('h264',1080,1920),path
    assert Fraction(stream['avg_frame_rate'])==30,(path,stream['avg_frame_rate'])
    assert int(stream.get('nb_read_frames',stream.get('nb_frames',0)))==count,(path,count,stream.get('nb_frames'))
    assert abs(float(stream['duration'])-count/30)<.001,(path,stream['duration'])
    return info


def dissolve(source, first, count):
    frames=WORK/'handles'/str(first)
    assert all((frames/f'handle_{i:02d}.png').is_file() for i in range(1,DISSOLVE_LENGTH+1)),frames
    output=source.with_name(f'dissolve_{source.name}')
    pixel_format=next(s['pix_fmt'] for s in probe(source)['streams'] if s['codec_type']=='video')
    assert pixel_format in ('yuv420p','yuv444p'),pixel_format
    # Frames f through f+7 use advancing outgoing camera handles and the true
    # incoming timeline. The middle weights are smoothstep samples 1/9...8/9.
    t=f'(N/{DISSOLVE_LENGTH+1})'
    weight=f'({t}*{t}*(3-2*{t}))'
    filter_graph=(
        f'[0:v]format={pixel_format},split=2[in0][in1];'
        f'[in0]trim=end_frame={DISSOLVE_LENGTH},setpts=PTS-STARTPTS[head];'
        f'[in1]trim=start_frame={DISSOLVE_LENGTH},setpts=PTS-STARTPTS[tail];'
        f'[1:v]format={pixel_format},setpts=PTS-STARTPTS[old];'
        f"[head][old]blend=all_expr='A*{weight}+B*(1-{weight})':shortest=1:repeatlast=0[mix];"
        f'[mix][tail]concat=n=2:v=1:a=0[v]'
    )
    ffmpeg('-i',source,'-framerate','30','-start_number','1','-i',frames/'handle_%02d.png',
           '-filter_complex',filter_graph,'-map','[v]','-r','30','-c:v','libx264','-crf','0',
           '-preset','ultrafast','-pix_fmt',pixel_format,output)
    check_video(output,count)
    return output


def measure_color(path):
    width, height = 540, 960
    frame_bytes = width * height * 3
    measurements = []
    command = ['ffmpeg', '-v', 'error', '-i', str(path), '-vf', 'fps=1,scale=540:960:flags=area',
               '-an', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-']
    with subprocess.Popen(command, stdout=subprocess.PIPE) as decoder:
        while pixels := decoder.stdout.read(frame_bytes):
            assert len(pixels) == frame_bytes, len(pixels)
            frame = Image.frombytes('RGB', (width, height), pixels)
            measurements.append((ImageStat.Stat(frame.convert('L')).mean[0],
                                 ImageStat.Stat(frame.convert('HSV')).mean[1]))
        assert decoder.wait() == 0
    assert len(measurements) == 109, len(measurements)
    luma, saturation = (round(mean(channel), 1) for channel in zip(*measurements))
    return {'sample_count': len(measurements), 'mean_luma': luma, 'mean_hsv_saturation': saturation}


def mux():
    state=json.loads((WORK/'progress.json').read_text())
    assert state['state']=='complete' and state['cuts_done']==list(range(1,len(CUTS)+1)),state
    entries=[];shots=[]
    for cut in CUTS:
        num=cut['id'];first=cut['start'];count=cut['end']-first+int(num==len(CUTS))
        source=WORK/'parts'/f'cut_{num:02d}.mp4'
        check_video(source,count)
        if first in DISSOLVE_CUTS:source=dissolve(source,first,count)
        entries.extend((f"file 'parts/{source.name}'",f'duration {count/30:.9f}'))
        shots.append({'id':cut.get('label',num),'a':first-1,'b':first+count-1})
    manifest=WORK/'qa_shots.json'
    manifest.write_text(json.dumps({'shots':shots,'xfade':[[f-1,f+DISSOLVE_LENGTH-2] for f in DISSOLVE_CUTS],
                                    'planned':[[f-4,f+2] for f in WHIP_CUTS]},indent=2))
    playlist=WORK/'concat.txt';playlist.write_text('\n'.join(entries)+'\n',encoding='ascii')
    temporary=WORK/'muxing_master.mp4';source=OUT/'narration.mp3'
    ffmpeg('-f','concat','-safe','1','-i',playlist,'-i',source,'-map','0:v:0','-map','1:a:0','-c:v','libx264',
           '-crf','15','-preset','fast','-pix_fmt','yuv420p','-c:a','aac','-b:a','256k','-af','apad=whole_dur=109',
           '-metadata:s:a:0','language=hin','-t','109.000','-movflags','+faststart',temporary)
    result=check_video(temporary,3270,decoded=True)
    video=next(s for s in result['streams'] if s['codec_type']=='video')
    audio=next(s for s in result['streams'] if s['codec_type']=='audio')
    assert video['pix_fmt']=='yuv420p' and audio['codec_name']=='aac'
    assert abs(float(audio['start_time']))<.001 and abs(float(audio['duration'])-109)<.002
    assert abs(float(result['format']['duration'])-109)<.001
    duplicates=decoded_duplicate_frames(temporary)
    details={'frames':3270,'duration':109.0,'fps':30,'size':[1080,1920],'encoded_duplicate_frames':duplicates,
             'audio_padding_s':round(109-float(probe(source)['format']['duration']),3),'dissolves':list(DISSOLVE_CUTS),
             'color':measure_color(temporary)}
    (WORK/'master_checks.json').write_text(json.dumps(details,indent=2))
    assert not duplicates,duplicates
    temporary.replace(FINAL)
    print(FINAL);print(json.dumps(details))


if __name__=='__main__':
    mux()
