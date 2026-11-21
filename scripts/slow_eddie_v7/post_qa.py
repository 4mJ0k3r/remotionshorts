from pathlib import Path
import subprocess,json,hashlib,statistics
from PIL import Image,ImageDraw,ImageFont
R=Path('D:/remotionshorts');P=R/'renders/slow_eddie_v7';movie=P/'slow_eddie_v7_1080p.mp4'
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
frozen=json.loads((P/'source_hash.json').read_text());assert hashlib.sha256((P/'slow_eddie_v7.blend').read_bytes()).hexdigest()==frozen['sha256'];assert hashlib.sha256((R/'scripts/slow_eddie_v7/runtime.py').read_bytes()).hexdigest()==frozen['runtime_sha256']
def sheet(frames,name):
 w=216;h=384;cols=min(4,len(frames));rows=(len(frames)+cols-1)//cols;im=Image.new('RGB',(w*cols,(h+22)*rows),'#182332');d=ImageDraw.Draw(im)
 for i,f in enumerate(frames):
  x=i%cols*w;y=i//cols*(h+22);im.paste(Image.open(P/f'frames/frame_{f:04d}.png').convert('RGB').resize((w,h)),(x,y+22));d.text((x+5,y+5),f'Frame {f}',fill='white')
 im.save(P/name,quality=94)
for n,frames in [('recoil',[28,30,31,32,34,36]),('chase_arrival',[37,60,82,84,85,90,96,105]),('reverse',[106,120,135,140,148,155,160,161]),('push',[215,216,222,230,239,245,246]),('acting',[165,195,249,252,255,268,280,292])]:sheet(frames,'motion_'+n+'.jpg')
b=json.loads((P/'benchmark.json').read_text());a=json.loads((P/'audit.json').read_text());tm=json.loads((P/'full_timing.json').read_text());data={'native_specs':p,'benchmark_max_seconds':max(x['seconds'] for x in b),'benchmark_mean_seconds':statistics.mean(x['seconds'] for x in b),'full_render_seconds':tm['seconds'],'full_render_seconds_per_frame':tm['seconds']/300,'sha256_mp4':hashlib.sha256(movie.read_bytes()).hexdigest()};(P/'delivery_summary.json').write_text(json.dumps(data,indent=2))
readme=f'''# Slow Eddie V7

Native1080x1920/30fps/300frames/10.000seconds, silent/no subtitles. Source: ../slow_eddie_v6/slow_eddie_v6.blend, preserved. Output: slow_eddie_v7.blend + slow_eddie_v7_1080p.mp4. Full encode was decode-tested and independently frame-counted; source/runtime hashes frozen in source_hash.json.

## User-approved design override and subsequent correction
The current user explicitly authorized dimensional 3D/2.5D characters instead of the flat-plane cast requirement, then clarified that V6 character identity must be retained. The initial generic thin-outlined spherical design was superseded before the final render. V7 now transfers the exact V6 harmonic rough-head contour formula, pressure-weighted warm #352329 boundary, cream #FDFAF2, feature anchors, half-lidded pupils/glints, moustache, clenched tooth-grid, wardrobe palette, brass medallion and compact hat/proportions into closed lit meshes. The organic contour is stable, not animated noise. Full skin depth and curved facial decal geometry preserve dimensional shading; the face is not an unlit image card. Head ink width varies by angle, approximately .0155-.0361m, taken from the V6 art recipe. Torso/neck/hip placement and slender continuous limbs match V6 scale. Hat crowns/brims, vest panels, belt/buckle, contoured stitched sheath and pearl butt have depth and real material highlights.

## Lighting and optics
Standard / None, exposure -0.15; actual World normal-based vertical gradient #D9E4EC horizon to #3876DC zenith plus warm sun lobe. Sun5.1/#FFF0D0, broad cool fill, cast shadow maps. Inverted ink hulls cull backfaces for both camera and shadow rays so they do not blanket-shadow the skin. Three softly interpolated cel light stops respond to EEVEE diffuse illumination and real received shadows, mixed with a small Principled component. Road keeps its actual procedural dirt/rut variation and cast shadows, mapping shade to indigo #687DA8 and Sun to gold #EBD09B. Compositor Fog Glow is added at15%, not baked into screenshots. EEVEE_NEXT16samples, ray tracing off, simplify enabled. Focus tracks face, bullet or hip as appropriate; macro f/2.8, hero f/1.8.

## Coverage and acting
Aim1-36: low-angle Challenger left, downloaded beveled metallic revolver, hand/grip solved together, stepped breathing/blink, recoil30-34, orange/yellow blast with translucent smoke. Forward chase37-84: diagonal foreground-left copper/brass bullet, avenue depth and Eddie ahead. Hip insert85-105: waist/upper-thigh, stitched leather, curved pearl grip, buckle and bullet. Reverse106-160: Eddie giant foreground-right, Challenger distant down the street. Wide161-215: foreground-left Challenger, attached sweat, hollow rolling/hopping tumbleweed. Push216-245: real continuous camera move, Challenger exits left; obsolete ghost overlay deleted. Hero246-300: thigh-to-hat composition, blink249-254, real head/hat nod268-292 and mouth-bound straw follows.

Six-frame native benchmark mean {statistics.mean(x['seconds'] for x in b):.3f}s, maximum {max(x['seconds'] for x in b):.3f}s. Full render including PNG saving {tm['seconds']:.3f}s, mean {tm['seconds']/300:.3f}s/frame. Exclusive owner-checked shared GPU lock used; no Chromium render was run alongside Blender.

## Verification and assets
10 timestamp-matched reference panels15/31/60/90/96/135/165/195/222/280 plus shot/joint extremes inspected before render; final native comparison and motion strips produced afterward. Numerical grip max error {a['grip_max_error_m']:.9f}m, separating-plane bullet clearance >= {min(a['arrival_clearance_m'].values()):.6f}m across85-105. Evaluated triangles including instances {a['evaluated_triangles_including_instances']}; images max {a['packed_image_max']}px. Town geometry and transforms have equal before/after hashes; V7 changes shading, actors, FX and camera, not the town layout. Geometry/anchor checks complement image review, and do not certify every silhouette or an exact match to the reference. Native sampled action strips and all-frame automated QA are recorded; interactive playback is not independently certified.

Existing asset licenses remain in ../slow_eddie_v5/README.md and ../slow_eddie/README.md: Saloon by Poly by Google (CC BY3.0, https://poly.pizza/m/82JBTSsWag4), Wooden Barrel and Cube Crate by Quaternius (CC0), and original revolver/cactus sources. Reference video: https://www.youtube.com/shorts/LC8hYwUZ-kU, saved360x640 clip; reference screenshots retain original subtitles, V7 remains subtitle-free. No claim is made about the original creator's internal rig or shaders.
'''
(P/'README.md').write_text(readme,encoding='utf8');print('VERIFIED',data)

with (P/'README.md').open('a',encoding='utf8') as out:
 out.write('\nOne preliminary full pass was superseded after the native review to restore V6-thin sole profiles and tighten the hip framing. Its timing is preserved in first_pass_timing.json; all300 delivered native frames were rerendered from the final frozen source, with dimensions and file freshness checked independently. No old-pass frames remain in the final encode.\n')
