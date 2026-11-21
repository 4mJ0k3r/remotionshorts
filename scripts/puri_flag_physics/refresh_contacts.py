"""Invalidate only owned rendered frames whose shoulder geometry was corrected."""
import json
from timeline import OUT

folder=(OUT/'frames_preview').resolve()
assert folder.is_relative_to(OUT.resolve())
changed=[]
for frame in range(356,555):
    path=folder/f'f{frame:04}.png'
    assert path.resolve().is_relative_to(folder)
    if path.exists():path.unlink();changed.append(frame)
(OUT/'contact_correction.json').write_text(json.dumps({
    'reason':'Overlap arm roots beneath the painted shoulder contour',
    'invalidated_frames':changed,
    'preserved_frames':'1..355',
    'future_frames':'555..2211 rendered from corrected rig',
    'method':'Resume rendering existing completed frames; atomically publish new PNGs after writing'
},indent=2))
print(f'Invalidated {len(changed)} affected frames; temple renders retained')
