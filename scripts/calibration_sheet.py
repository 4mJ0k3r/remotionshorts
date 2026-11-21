"""Shared calibration plan and sheet builder; no Blender or project dependency.

Metadata is zero-based; Blender/source PNG filenames are one-based. Normalized
crops use top-left origin. Missing images fail rather than silently disappearing.
"""
import argparse
import json
import math
import subprocess
import tempfile
from pathlib import Path
from PIL import Image, ImageDraw, ImageOps

try:
    from .shorts_qa_checks import region_pixels
except ImportError:
    from shorts_qa_checks import region_pixels


def build_plan(meta, frame_count):
    if frame_count <= 0:
        raise ValueError('Positive frame count required')
    frames = {}
    def add(frame, label):
        if 0 <= frame < frame_count:
            frames.setdefault(frame, set()).add(label)
    shots = meta.get('shots') or [{'id': 'all', 'a': 0, 'b': frame_count}]
    for shot in shots:
        a, b = shot['a'], shot['b']
        for frame in (a, (a+b-1)//2, b-1):
            add(frame, f"shot {shot['id']}")
    junctions = set(meta.get('cuts', [])) | set(meta.get('continuous_junctions', []))
    # Even older manifests receive boundary-neighbor inspection frames.
    junctions.update(s['a'] for s in shots[1:])
    for frame in junctions:
        for offset in (-2, -1, 0, 1, 2):
            add(frame+offset, 'junction')
    for a, b in meta.get('transitions', []) + meta.get('xfade', []):
        for frame in {a, b, round(a+(b-a)*.25), round((a+b)/2), round(a+(b-a)*.75)}:
            for offset in (-1, 0, 1):
                add(frame+offset, 'transition')
    for frame in meta.get('calibration_frames', []):
        add(frame, 'action/extreme')
    crops = []
    for crop in meta.get('closeups', []):
        frame = crop['frame']
        if not 0 <= frame < frame_count:
            raise ValueError('Close-up frame is out of range')
        region_pixels(crop['region'], 360, 640)
        crops.append(dict(crop))
        add(frame, crop.get('kind', 'closeup'))
    missing = sorted({'hat_brim', 'hand_prop'}-{c.get('kind') for c in crops})
    return {'frame_indices': sorted(frames), 'blender_frames': [f+1 for f in sorted(frames)],
            'panels': [{'frame': f, 'label': ', '.join(sorted(frames[f]))} for f in sorted(frames)],
            'closeups': crops, 'closeup_status': 'UNVERIFIED' if missing else 'DECLARED',
            'missing_closeup_kinds': missing}


def make_sheet(load_frame, plan, output, columns=6, cell=(180, 348)):
    panels = plan['panels'] + [dict(c, crop=True) for c in plan['closeups']]
    sheet = Image.new('RGB', (columns*cell[0], math.ceil(len(panels)/columns)*cell[1]), '#181820')
    draw = ImageDraw.Draw(sheet)
    for i, panel in enumerate(panels):
        im = load_frame(panel['frame']).convert('RGB')
        if panel.get('crop'):
            im = im.crop(region_pixels(panel['region'], *im.size))
        image = ImageOps.contain(im, (cell[0]-8, cell[1]-35))
        x, y = i % columns*cell[0], i//columns*cell[1]
        sheet.paste(image, (x+(cell[0]-image.width)//2, y+31))
        label = panel.get('label', panel.get('kind', 'crop'))
        draw.text((x+4, y+2), f"f{panel['frame']+1} / index {panel['frame']}", fill='white')
        draw.text((x+4, y+16), label[:27], fill='#EBC87A')
    output = Path(output)
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    output.with_suffix('.plan.json').write_text(json.dumps(plan, indent=2), encoding='utf-8')


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--meta', required=True); p.add_argument('--frame-count', type=int, required=True)
    p.add_argument('--output', required=True); p.add_argument('--frames-dir'); p.add_argument('--video')
    p.add_argument('--pattern', default='frame_%04d.png')
    p.add_argument('--plan-only', action='store_true'); p.add_argument('--strict', action='store_true')
    args = p.parse_args()
    plan = build_plan(json.loads(Path(args.meta).read_text(encoding='utf-8')), args.frame_count)
    if args.strict and 'cuts' not in json.loads(Path(args.meta).read_text(encoding='utf-8')):
        p.error('Strict new-build manifests must declare cuts, including []')
    if args.strict and plan['missing_closeup_kinds']:
        p.error('Declare hat_brim and hand_prop closeups before production calibration')
    if args.plan_only:
        Path(args.output).parent.mkdir(parents=True, exist_ok=True)
        Path(args.output).write_text(json.dumps(plan, indent=2), encoding='utf-8'); return
    if bool(args.frames_dir) == bool(args.video):
        p.error('Choose exactly one of --frames-dir or --video')
    if args.frames_dir:
        def load(f):
            with Image.open(Path(args.frames_dir)/(args.pattern % (f+1))) as im:
                return im.copy()
        make_sheet(load, plan, args.output)
    else:
        with tempfile.TemporaryDirectory(prefix='shorts_calibration_') as tmp:
            select = '+'.join(f'eq(n\\,{f})' for f in plan['frame_indices'])
            subprocess.run(['ffmpeg', '-v', 'error', '-i', args.video, '-vf', 'select='+select,
                            '-vsync', '0', str(Path(tmp)/'%05d.png')], check=True)
            mapping = {f: Path(tmp)/f'{i+1:05d}.png' for i, f in enumerate(plan['frame_indices'])}
            def load(f):
                with Image.open(mapping[f]) as im:
                    return im.copy()
            make_sheet(load, plan, args.output)
    print(f"Calibration sheet: {args.output}; closeups {plan['closeup_status']}")


if __name__ == '__main__':
    main()
