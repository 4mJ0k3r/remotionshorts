"""Replace the Mach shot at the original H.264 keyframes and verify the join."""
import json
import subprocess
import sys
from delivery import OUT,ROOT,probe,sheet

original=OUT/'lifetime_fart_master_1080p.mp4'
backup=OUT/'master_chunks/master_before_mach_patch.mp4'
patch=OUT/'mach_patch.mp4'
prefix=OUT/'master_chunks/mach_prefix.mp4'
suffix=OUT/'master_chunks/mach_suffix.mp4'
temp=OUT/'master_chunks/master_patched.mp4'
if not backup.exists():
 import shutil
 shutil.copy2(original,backup)
def ff(*args):
 subprocess.run(['ffmpeg','-v','error','-y',*map(str,args)],check=True)
def count(p):
 return int(probe(p)['streams'][0]['nb_frames'])
assert count(patch)==159
ff('-i',backup,'-map','0:v:0','-frames:v',1425,'-c','copy',prefix)
ff('-ss','52.8','-i',backup,'-map','0:v:0','-c','copy',suffix)
assert (count(prefix),count(suffix))==(1425,1131)
manifest=OUT/'master_chunks/mach_concat.txt'
manifest.write_text(''.join(f"file '{p.as_posix()}'\nduration {d}\n" for p,d in [(prefix,47.5),(patch,5.3),(suffix,37.7)]))
ff('-f','concat','-safe',0,'-i',manifest,'-i',backup,'-map','0:v:0','-map','1:a:0','-c','copy','-movflags','+faststart',temp)
assert count(temp)==2715
def hashes(p):
 args=['ffmpeg','-v','error','-i',str(p),'-map','0:v:0','-an','-f','framemd5','-']
 return [line.rsplit(',',1)[1].strip() for line in subprocess.check_output(args,text=True).splitlines() if line and not line.startswith('#')]
old=hashes(backup);new=hashes(temp)
assert new[:1425]==old[:1425] and new[1584:]==old[1584:]
assert new[1425:1584]==hashes(patch)
def audio(p):
 return subprocess.check_output(['ffmpeg','-v','error','-i',str(p),'-map','0:a:0','-c','copy','-f','md5','-'])
assert audio(temp)==audio(backup)
temp.replace(original)
sheet(5)
subprocess.run([sys.executable,str(ROOT/'scripts/short_qa.py'),str(original),str(OUT/'qa_master'),str(OUT/'master_shots.json')],check=True)
report=OUT/'OVERRUN_MASTER_REPORT.md'
prior=report.read_text(encoding='utf8').split('## Export diagnostics')[0]
report.write_text(prior+
 "## Delivery correction\n\n"
 "The first master audit found repeated static spans during the Mach sequence. Frames 1426–1584 were re-rendered with receding shock cones, a slow camera push and directional air streaks. Both joins occur on the original keyframes. Decoded frame hashes confirm that all other video frames and the encoded narration payload are identical to the first master.\n\n"
 "## Final export diagnostics\n\n"
 +(OUT/'qa_master/report.md').read_text(encoding='utf8'),encoding='utf8')

