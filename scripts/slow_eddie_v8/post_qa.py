from pathlib import Path
import subprocess,json,hashlib,statistics
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v8';movie=P/'slow_eddie_v8_1080p.mp4'
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,nb_read_frames:format=duration','-of','json',str(movie)]));v=next(x for x in p['streams'] if x['codec_type']=='video');assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(1080,1920,'30/1',300);assert abs(float(p['format']['duration'])-10)<.001
(P/'delivery_specs.json').write_text(json.dumps(p,indent=2))
# Independently verify native PNG dimensions and freshness after the frozen final source.
source_stamp=(P/'source_hash.json').stat().st_mtime
for f in range(1,301):
 frame=P/f'frames/frame_{f:04d}.png'
 assert frame.stat().st_mtime>=source_stamp
 with Image.open(frame) as check:assert check.size==(1080,1920)
report=P/'qa/report.md';report_text=report.read_text(encoding='utf8')
if report_text.startswith('NONE\n'):report.write_text(report_text.replace('NONE\n','SPECS1080x1920 / 30fps / 300frames / 10.000s; audio:none (silent benchmark)\n',1),encoding='utf8')
frozen=json.loads((P/'source_hash.json').read_text());assert hashlib.sha256((P/'slow_eddie_v8.blend').read_bytes()).hexdigest()==frozen['sha256'];assert hashlib.sha256((R/'scripts/slow_eddie_v8/runtime.py').read_bytes()).hexdigest()==frozen['runtime_sha256']
def sheet(frames,name):
 w=216;h=384;cols=min(4,len(frames));rows=(len(frames)+cols-1)//cols;im=Image.new('RGB',(w*cols,(h+22)*rows),'#182332');d=ImageDraw.Draw(im)
 for i,f in enumerate(frames):
  x=i%cols*w;y=i//cols*(h+22);im.paste(Image.open(P/f'frames/frame_{f:04d}.png').convert('RGB').resize((w,h)),(x,y+22));d.text((x+5,y+5),f'Frame {f}',fill='white')
 im.save(P/name,quality=94)
for n,frames in [('recoil',[28,30,31,34,35,37]),('chase_arrival',[37,60,82,84,85,90,96,105]),('reverse',[106,120,135,140,148,155,160,161]),('push',[204,205,215,222,230,245,246]),('acting',[165,195,249,252,255,268,280,292])]:sheet(frames,'motion_'+n+'.jpg')
b=json.loads((P/'benchmark.json').read_text());a=json.loads((P/'audit.json').read_text());tm=json.loads((P/'full_timing.json').read_text());data={'native_specs':p,'benchmark_max_seconds':max(x['seconds'] for x in b),'benchmark_mean_seconds':statistics.mean(x['seconds'] for x in b),'full_render_seconds':tm['seconds'],'full_render_seconds_per_frame':tm['seconds']/300,'sha256_mp4':hashlib.sha256(movie.read_bytes()).hexdigest()};(P/'delivery_summary.json').write_text(json.dumps(data,indent=2))
readme=f"""# Slow Eddie V8

Native1080x1920/30fps/300frames/10.000seconds; silent benchmark clip, no subtitles. Input ../slow_eddie_v7/slow_eddie_v7.blend remains intact. Output slow_eddie_v8.blend and slow_eddie_v8_1080p.mp4. Hashes freeze the source/runtime, every native PNG is checked for1080x1920 dimensions and freshness after the frozen source, the full MP4 is decode-tested and counted independently.

V7 town geometry/transforms, rough head contour, pressure ink, hats, leg/sole proportions and camera DOF are retained. Before/after geometry hashes in town_preservation.json prove town and head/hat/leg preservation. Torso cross-section depth is gently increased22%, with Shade Smooth and baked Weighted Normal adjustments; striped artwork is refitted to the surface. Belt/buckle depths are refitted to keep the waist contiguous. Eddie's old folded V-shaped polygons are replaced by closed curved beveled lapels with rounded hems and smooth piping. The ivory grip has procedural nacre grain, soft chamfered/rounded ends, an actual steel seat and a -50degree up-left angle.

Lighting: golden Sun5.5/#FFE6B5 from front-right with approximately50degree cross-angle, broad controlled #7C94C8 fill850W, and distinct cool cel shadow stops. Physical hat-brim shadows remain enabled. The original gradient sky is subtly cooled; Z-depth haze mixes #DFCEB4 over distances18-63m with maximum45%. A camera-far-clip mask excludes the sky from haze, avoiding a grey veil. Existing Fog Glow remains restrained at15%; low-resolution glow quality is used for speed. Standard/None/exposure-0.15. EEVEE_NEXT12samples, ray tracing off, simplify retained; six native timings confirm the budget after a16-sample draft missed it. Actual DOF optics remain f/2 opening/chase, f/2.8 hip, f/1.8 hero.

The rigid orange cone is replaced by a translucent irregular multi-lobed amber flame with an HDR hot core, three moving spark streaks and separately fading smoke. A small projectile visibly exits the real barrel at34-36; the chase uses the inherited enlarged hero scale. The projectile is rebuilt as a smooth copper-jacketed ogive with a short chamfered brass rim and small recessed primer, replacing the oversized yellow disk. Axial spin preserves its approximately13degree downward presentation at60 and level arrival88-96. The aiming wrist/weapon is raised toward chin height with a shorter tense tooth-grid grin. Reverse camera height/pitch keeps the Stetson below the top border at135; the hollow tumbleweed has50% thicker opaque contrasting twigs over160-205. Push-in starts205 and is past Challenger by222; there is no static ghost overlay.

Six-frame benchmark mean {statistics.mean(x['seconds'] for x in b):.3f}s, maximum {max(x['seconds'] for x in b):.3f}s. Final300-frame render including PNG saves {tm['seconds']:.3f}s / {tm['seconds']/300:.3f}s per frame. Exclusive shared GPU lock is acquired per owned Blender process and released afterward; no Chromium render is run alongside Blender.

Numerical checks: hand/gun anchor max error {a['grip_max_error_m']:.9f}m; bullet separating-plane clearance at least {min(a['arrival_clearance_m'].values()):.6f}m through85-105; hat crown top at135 remains below viewport top; Challenger is behind the camera at222; bullet pitch is checked at60 and90. Evaluated scene triangles including instances {a['evaluated_triangles_including_instances']}; image maps at most {a['packed_image_max']}px. The same10 timestamps15/31/60/90/96/135/165/195/222/280 are compared with the supplied RicksClips clip before rendering and from native final frames afterward. Native action/boundary strips and all-frame automated QA are recorded. These are visual/technical checks, not a claim of an exact match or knowledge of the reference creator's internal rig; interactive playback has not been independently certified.

Existing asset credits remain in ../slow_eddie_v5/README.md and ../slow_eddie/README.md: Saloon by Poly by Google (CC BY3.0, https://poly.pizza/m/82JBTSsWag4); Quaternius Wooden Barrel and Cube Crate (CC0), plus the original revolver/cactus sources. Reference https://www.youtube.com/shorts/LC8hYwUZ-kU is a locally saved360x640 clip; its subtitles remain in comparison screenshots only.
"""
(P/'README.md').write_text(readme,encoding='utf8');print('VERIFIED',data)
