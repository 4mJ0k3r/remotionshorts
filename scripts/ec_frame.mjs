// Engine projection gate. At most TWO invocations per calibration task; never loosen bounds to chase grazes.
import * as THREE from 'three';
import {build} from 'esbuild';
import fs from 'node:fs';
const {outputFiles}=await build({entryPoints:['src/videos/elevator_crush/story.ts'],bundle:true,write:false,platform:'node',format:'esm'});
const S=await import('data:text/javascript;base64,'+Buffer.from(outputFiles[0].text).toString('base64'));
const main=[['hat',300,35],['headL',150,235],['headR',450,235],['chin',300,380]];
const secondary=[['shoeL',240,952],['shoeR',360,952]];
const project=(c,pos,scale,dx,dy)=>{
 const camera=new THREE.PerspectiveCamera(c.fov,1080/1920,0.2,100);
 camera.position.set(...c.pos);camera.lookAt(...c.look);camera.updateMatrixWorld();
 const yaw=Math.atan2(c.pos[0]-pos[0],c.pos[2]-pos[2]),x=(dx-300)*0.00216*scale,y=(975-dy)*0.00216*scale;
 const p=new THREE.Vector3(pos[0]+Math.cos(yaw)*x,pos[1]+y,pos[2]-Math.sin(yaw)*x).project(camera);
 return [(p.x+1)*50,(1-p.y)*50];
};
const frames=(process.argv[2]??'100,320,500,800,1050,1380,1720,1950,2350,2700,3150').split(',').map(Number);
let worst=0,bad=0,held=0,steps=0;const rows=[];
for(const f of frames){
 const shot=S.shotAt(f),c=S.camAt(shot.id,f),actors=S.actorsAt(shot.id,f);const flags=[];let range=[100,0,100,0];
 for(const [i,a] of actors.entries())for(const [name,dx,dy] of [...main,...secondary]){
  const [u,v]=project(c,a.pos,a.scale,dx,dy),isMain=main.some(x=>x[0]===name),lo=isMain?15:5,hi=isMain?85:95;
  const graze=Math.max(lo-u,u-hi,lo-v,v-hi,0);worst=Math.max(worst,graze);
  if(graze>0){flags.push(`${i?'crush':'hero'}.${name} ${u.toFixed(1)}/${v.toFixed(1)} graze${graze.toFixed(1)}%`);if(graze>5)bad++;}
  if(isMain){range=[Math.min(range[0],u),Math.max(range[1],u),Math.min(range[2],v),Math.max(range[3],v)];}
 }
 const row=`f${f} S${shot.id} FOV${c.fov} main u${range[0].toFixed(1)}..${range[1].toFixed(1)} v${range[2].toFixed(1)}..${range[3].toFixed(1)} ${flags.join('; ')||'PASS'}`;
 console.log(row);rows.push(row);
}
for(const shot of S.SHOTS)for(let f=shot.a+1;f<shot.b;f++){
 const a=S.camAt(shot.id,f-1),b=S.camAt(shot.id,f);steps++;
 if(a.pos.every((v,i)=>v===b.pos[i])&&a.look.every((v,i)=>v===b.look[i]))held++;
 if(b.fov<38||b.fov>50)bad++;
}
const result={frames,rows,worstGrazePercent:worst,violationsOver5Percent:bad,heldCameraPercent:100*held/steps};
fs.mkdirSync('out/elevator_crush',{recursive:true});const name=process.argv[3]??'out/elevator_crush/engine_framing_1.json';fs.writeFileSync(name,JSON.stringify(result,null,2));
console.log(`Worst graze ${worst.toFixed(2)}%; >5% violations ${bad}; held camera transforms ${held}/${steps} (${result.heldCameraPercent.toFixed(2)}%)`);
process.exitCode=bad?1:0;
