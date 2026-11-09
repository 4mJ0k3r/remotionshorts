// Project the exact shared story state. Run at most twice; fixed 15/85 main and 5/95 secondary limits.
import {build} from 'esbuild';
import * as THREE from 'three';
import fs from 'node:fs';
const {outputFiles}=await build({entryPoints:['src/videos/crush_bathroom/story.ts'],bundle:true,write:false,platform:'node',format:'esm'});
const S=await import('data:text/javascript;base64,'+Buffer.from(outputFiles[0].text).toString('base64'));
const rows=[];let worst=0,bad=0,held=0;
for(const f of S.CALIBRATION){
 const s=S.shotAt(f),c=S.cameraAt(f),cam=new THREE.PerspectiveCamera(c.fov,1080/1920,.2,100);cam.position.set(...c.pos);cam.lookAt(...c.look);cam.rotateZ(c.roll);cam.updateMatrixWorld();
 const points=[];
 for(const [i,a]of S.castAt(f).entries()){
  const seated=['toiletSit','pressFlush','sofaPhone'].includes(a.opts.mode),hy=seated?420:235;
  if(s.id===20&&i===1)continue; // intentionally occluded head peeks through the physical door gap
  const yaw=Math.atan2(c.pos[0]-a.pos[0],c.pos[2]-a.pos[2]);
  for(const [label,dx,dy]of [['top',300,hy-153],['left',147,hy],['right',453,hy],['chin',300,hy+151]]){
   const x=(dx-300)*.00216*a.scale;points.push([`${a.opts.kind}.${label}`,new THREE.Vector3(a.pos[0]+Math.cos(yaw)*x,a.pos[1]+(975-dy)*.00216*a.scale,a.pos[2]-Math.sin(yaw)*x)]);
  }
 }
 if(s.set==='bowl')points.push(['mountain',new THREE.Vector3(0,2.25,0)],['water',new THREE.Vector3(0,1.18,0)]);
 if(s.set==='science')points.push(['arrowL',new THREE.Vector3(-1,1.15,0)],['arrowR',new THREE.Vector3(1,1.15,0)],['gas',new THREE.Vector3(0,1.05,0)]);
 if(s.id===19)points.push(['handle',new THREE.Vector3(1.6,1.04,-1.48)]);
 if(s.id===22)points.push(['mug',new THREE.Vector3(.9,.83,.5)],['bucketL',new THREE.Vector3(.58,.35,.5)],['bucketR',new THREE.Vector3(1.22,.35,.5)]);
 const flags=[];
 for(const[name,p]of points){p.project(cam);const u=(p.x+1)*50,v=(1-p.y)*50,g=Math.max(15-u,u-85,15-v,v-85,0);worst=Math.max(worst,g);if(g>0)flags.push(`${name}:${u.toFixed(1)}/${v.toFixed(1)} (${g.toFixed(1)}%)`);if(g>5)bad++;}
 const row=`f${f} shot${s.id} ${s.set} ${flags.join(' | ')||'PASS'}`;console.log(row);rows.push(row);
}
for(const s of S.SHOTS)for(let f=s.a+1;f<s.b;f++){const a=S.cameraAt(f-1),b=S.cameraAt(f);if(a.pos.every((v,i)=>v===b.pos[i]))held++;}
fs.writeFileSync(process.argv[2]??'out/crush_bathroom/framing_1.json',JSON.stringify({rows,worstGraze:worst,violationsOver5:bad,heldTransforms:held},null,2));
console.log('Worst graze',worst.toFixed(2),'over-5 violations',bad,'held transforms',held);process.exitCode=bad?1:0;
