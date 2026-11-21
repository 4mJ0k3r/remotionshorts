"""Create a separate render pipeline; old review exports remain intact."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
replacements=[('calibration_approved.json','calibration_v2_approved.json'),("OUT/'frames'","OUT/'v2_full_frames'"),('frames/%04d.png','v2_full_frames/%04d.png'),("OUT/'qa'","OUT/'qa_v2_full'"),('classroom_fart_preview.mp4','classroom_fart_v2_full.mp4'),('shots.json','shots_v2.json'),('chunk_{','v2_chunk_{'),('render_preview.py','render_v2.py'),('finish_preview.py','finish_v2.py')]
for old,new in [('render_preview.py','render_v2.py'),('finish_preview.py','finish_v2.py'),('queue_preview.py','queue_v2.py')]:
    text=(HERE/old).read_text()
    for a,b in replacements:text=text.replace(a,b)
    (HERE/new).write_text(text)
