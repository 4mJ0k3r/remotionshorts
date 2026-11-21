from pathlib import Path
from PIL import Image,ImageDraw
import subprocess,json,statistics,hashlib
P=Path('D:/remotionshorts/renders/slow_eddie_v6');movie=P/'slow_eddie_v6_1080p.mp4'
pr=json.loads(subprocess.check_output(['ffprobe','-v','error','-count_frames','-show_entries','stream=codec_type,codec_name,width,height,r_frame_rate,nb_frames,nb_read_frames:format=duration','-of','json',str(movie)]))
v=next(s for s in pr['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['r_frame_rate'],int(v['nb_read_frames']))==(1080,1920,'30/1',300);assert abs(float(pr['format']['duration'])-10)<.001
(P/'delivery_specs.json').write_text(json.dumps(pr,indent=2))
def sheet(frames,path,cw=216):
 ch=round(cw*1920/1080);cols=min(4,len(frames));rows=(len(frames)+cols-1)//cols;im=Image.new('RGB',(cw*cols,(ch+22)*rows),'#182332');d=ImageDraw.Draw(im)
 for i,f in enumerate(frames):
  x=i%cols*cw;y=i//cols*(ch+22);im.paste(Image.open(P/f'frames/frame_{f:04d}.png').convert('RGB').resize((cw,ch)),(x,y+22));d.text((x+5,y+5),f'Frame {f}',fill='white')
 im.save(P/path,quality=94)
sheet([15,31,60,90,165,195,253,280],'sheet_final.jpg',270)
for name,frames in [('recoil',[27,29,30,31,32,34]),('chase',[35,45,60,75,88,90]),('drift',[165,180,195,210]),('transition',[215,220,225,230,235,236]),('nod',[248,251,254,268,280,288])]:sheet(frames,'motion_'+name+'.jpg')
timing=json.loads((P/'full_timing.json').read_text());b=json.loads((P/'benchmark.json').read_text());audit=json.loads((P/'anchor_motion_audit.json').read_text());preserved=json.loads((P/'town_preservation.json').read_text());frozen=json.loads((P/'source_hash.json').read_text());assert hashlib.sha256((P/'slow_eddie_v6.blend').read_bytes()).hexdigest()==frozen['sha256']
readme=f'''# Slow Eddie V6 delivery

Native 1080x1920, 30fps, 300 frames, 10.000s, H.264 yuv420p. Silent benchmark clip, no subtitles. The complete encoded movie passed ffmpeg decode and ffprobe frame-count checks.

V5 town meshes, props, placement and character proportions are retained; matching before/after geometry+transform hashes are in town_preservation.json. V6 changes existing facade materials only. All original sources and 540p deliveries remain intact. Imported source credits continue in ../slow_eddie_v5/README.md and ../slow_eddie/README.md, including Saloon by Poly by Google (CC BY 3.0), Quaternius barrel/crate (CC0) and existing revolver/cactus sources.

Standard / None, exposure -0.25; warm Sun and saturated azure world; 16 EEVEE_NEXT samples, ray tracing disabled. Actual f/0.85 optical DOF tracks the face/projectile hero Empty. 38mm low-angle Dutch opening, 60-65mm orbital bullet shot, 65mm Eddie medium. Bullet remains physical 2.5x hero scale with copper/brass Metallic .9 / Roughness .2 and emission assistance to retain warm metal color without ray tracing.

Animation: stepped 12fps breathing and hand tremor; blink14-17; anchored arm/gun squash/recoil29-32, flash29-31 and expanding smoke. Cubic Bezier launch easing and rear-to-side orbital chase, ease into holster88-95. Reverse pullback through160 then continuous drift through214. Lowering/trembling arm, chest/knee motion, downstreet gaze and socket-bound sliding/pulsing sweat; hollow tumbleweed has rotation-aware ground hops. Silhouette push215-235 with twelve-frame actor alpha fade; continuous2% push236-300, blink248-254, head/hat pitch reaches -10degrees at280 then springs back288. Mouth-anchored straw inherits head pitch plus small wiggle.

Raster arm pixels were removed and replaced with continuous flat curved ink meshes and cream hands; no ring shells. The protruding thigh strap cylinder is deleted. Gun/hand anchor maximum positional error {audit['grip_max_error_m']:.9f}m; projected separating-plane clearance bullet-to-holster/gun is >= {min(audit['arrival_clearance_m'].values()):.6f}m over88-95. This numeric check complements the reviewed arrival frame. Nod and drift assertions passed over the300-frame sweep. Audit triangle count is direct visible mesh count, excluding evaluated GN instances; the preserved V5 evaluated scene budget was121436triangles, with only small arm topology changes in V6.

Five-frame native benchmark: mean {statistics.mean(x['seconds'] for x in b):.3f}s, maximum {max(x['seconds'] for x in b):.3f}s. Full300-frame render including PNG saves: {timing['seconds']:.3f}s / {timing['seconds']/300:.3f}s per frame. Cold shader/setup time is separate from warmed benchmark. Exclusive shared GPU lock was used; no browser render ran alongside Blender.

Calibration at15,31,60,90,165,195,253,280 reviewed before final render; final native frames and action strips exported for inspection. Encoded all-frame statistics and contact sheets are under qa/. Automated QA is a diagnostic, not proof of every visual contact or reference match. Sampled native stills and motion strips were inspected; interactive playback has not been independently certified.

Source is frozen by source_hash.json and includes slow_eddie_v6_runtime.py. Runtime is explicitly bootstrapped for repeatable background rendering. Build/calibration/benchmark/render helpers live under D:/remotionshorts/scripts/slow_eddie_v6/.
'''
(P/'README.md').write_text(readme,encoding='utf8');print('SPECS VERIFIED',v,'Full seconds/frame',timing['seconds']/300)
