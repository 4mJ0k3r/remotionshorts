from pathlib import Path
HERE=Path(__file__).resolve().parent
replacements=[('v2_full_frames','v2_1080_frames'),('v2_pending','v2_1080_pending'),('qa_v2_full','qa_v2_1080'),('classroom_fart_v2_full.mp4','classroom_fart_v2_1080p_full.mp4'),('v2_chunk_','v2_1080_chunk_'),('render_v2.py','render_v2_1080.py'),('finish_v2.py','finish_v2_1080.py'),('v2-preview-','v2-1080-')]
for a,b in [('render_v2.py','render_v2_1080.py'),('finish_v2.py','finish_v2_1080.py'),('queue_v2.py','queue_v2_1080.py')]:
    text=(HERE/a).read_text()
    for old,new in replacements:text=text.replace(old,new)
    text=text.replace('resolution_percentage=50','resolution_percentage=100').replace('==(540,960)','==(1080,1920)')
    (HERE/b).write_text(text)
