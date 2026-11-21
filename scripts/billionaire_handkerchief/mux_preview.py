"""Assemble complete preview cuts, mux Hindi narration, and audit the MP4."""
import json
import subprocess
from fractions import Fraction
from pathlib import Path

HERE=Path(__file__).resolve().parent
OUT=HERE.parents[1]/'renders'/HERE.name
WORK=OUT/'preview_work_540p'
CUTS=json.loads((HERE/'cuts.json').read_text(encoding='utf-8'))
FINAL=OUT/'billionaire_handkerchief_preview_540p.mp4'


def probe(path,count=False):
    args=['ffprobe','-v','error','-show_streams','-show_format','-of','json']
    if count:args.append('-count_frames')
    return json.loads(subprocess.check_output([*args,str(path)]))


def check_video(stream,frames,path,size=(540,960)):
    assert (stream['codec_name'],stream['width'],stream['height'])==('h264',*size),path
    assert Fraction(stream['avg_frame_rate'])==30,path
    assert int(stream.get('nb_read_frames',stream.get('nb_frames',0)))==frames,(path,frames,stream.get('nb_frames'))
    assert abs(float(stream['duration'])-frames/30)<.001,path


def decoded_duplicate_frames(path):
    result=subprocess.check_output(['ffmpeg','-v','error','-i',str(path),'-map','0:v:0','-f','framemd5','-'],text=True)
    hashes=[line.rsplit(',',1)[1].strip() for line in result.splitlines() if line and not line.startswith('#')]
    assert len(hashes)==3270,len(hashes)
    return [index for index,(previous,current) in enumerate(zip(hashes,hashes[1:]),2) if previous==current]


def mux():
    progress=json.loads((WORK/'progress.json').read_text())
    assert progress['state']=='complete' and progress['cuts_done']==list(range(1,43)),progress
    entries=[]
    for cut in CUTS:
        number=cut['id'];path=WORK/'parts'/f'cut_{number:02d}.mp4'
        count=cut['end']-cut['start']+int(number==42)
        streams=probe(path)['streams']
        assert len(streams)==1 and streams[0]['codec_type']=='video',path
        check_video(streams[0],count,path)
        entries.extend((f"file 'parts/{path.name}'",f'duration {count/30:.9f}'))
    playlist=WORK/'concat.txt';playlist.write_text('\n'.join(entries)+'\n',encoding='ascii')
    temporary=WORK/'muxing.mp4'
    source=OUT/'narration.mp3';source_duration=float(probe(source)['format']['duration'])
    subprocess.run([
        'ffmpeg','-hide_banner','-loglevel','error','-y','-f','concat','-safe','1','-i',str(playlist),'-i',str(source),
        '-map','0:v:0','-map','1:a:0','-c:v','copy','-c:a','aac','-b:a','192k','-af','apad=whole_dur=109',
        '-metadata:s:a:0','language=hin','-t','109.000','-movflags','+faststart',str(temporary),
    ],check=True)
    result=probe(temporary,count=True)
    videos=[s for s in result['streams'] if s['codec_type']=='video'];audios=[s for s in result['streams'] if s['codec_type']=='audio']
    assert len(videos)==len(audios)==1 and len(result['streams'])==2
    check_video(videos[0],3270,temporary)
    assert abs(float(result['format']['duration'])-109)<.001,result['format']
    assert abs(float(audios[0]['duration'])-109)<.002 and abs(float(audios[0]['start_time']))<.001,audios[0]
    duplicates=decoded_duplicate_frames(temporary)
    report={'frames':3270,'fps':30,'size':[540,960],'duration':109,'narration_source_seconds':source_duration,
            'narration_padding_seconds':round(109-source_duration,3),'identical_adjacent_decoded_frames':duplicates}
    (WORK/'preview_checks.json').write_text(json.dumps(report,indent=2))
    temporary.replace(FINAL)
    print(json.dumps(report));print(FINAL)


if __name__=='__main__':
    mux()
