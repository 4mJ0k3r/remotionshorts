// GPU check: protected character pixels must be unchanged by both DOF passes.
import {build} from 'esbuild';
import {openBrowser} from '@remotion/renderer';
const {outputFiles}=await build({bundle:true,write:false,format:'iife',platform:'browser',stdin:{resolveDir:process.cwd(),contents:`
import * as THREE from 'three';
import {EffectComposer,RenderPass,EffectPass} from 'postprocessing';
import {InkPass} from './src/engine/shaders/ink';
import {LensBlur} from './src/engine/shaders/lensblur';
import {handEllPts} from './src/engine/shaders/pen';
import {handWorldPos,worldToCardPoint} from './src/engine/pool';
import {DOF_CLOSE,DOF_MEDIUM} from './src/engine/camera';
import {CARD_K} from './src/engine/shaders/cardshade';
import {cameraAt,focusPointAt,engineDofAt,actorsAt} from './src/videos/elevator_crush/story';
const check=(ok,message)=>{if(!ok)throw Error(message)};
const shape=handEllPts(0,0,145,145);
const radii=shape.map(p=>Math.hypot(...p));
check(Math.max(...radii)-Math.min(...radii)>6,'organic skull harmonic variation');
check(JSON.stringify(shape)===JSON.stringify(handEllPts(0,0,145,145)),'stable contour across frames');
check(CARD_K.uGradK.value===2.4&&CARD_K.uGradKB.value===0.9&&CARD_K.uGain.value===1.12,'vivid card preset');
for(const f of [100,320,500,800,1050,1380,1720,1950,2350,2700,3150]){
 const c=cameraAt(f),p=focusPointAt(f),d=engineDofAt(f),forward=new THREE.Vector3(...c.look).sub(new THREE.Vector3(...c.pos)).normalize();
 const expected=new THREE.Vector3(...p).sub(new THREE.Vector3(...c.pos)).dot(forward);
 check(Math.abs(expected-d.focus)<1e-8,'foreground focus projection');
 check([DOF_CLOSE,DOF_MEDIUM].includes(d.cInf),'close/medium DOF strength');
 const a=actorsAt(f<2196?8:f<2466?9:10,f);
 for(let i=0;i<2;i++){
   const cam=new THREE.Vector3(...c.pos),target=handWorldPos(cam,a[1-i].pos,a[1-i].scale,i===0?230:380,435,0);
   const pt=worldToCardPoint(cam,a[i].pos,a[i].scale,target);
   const mapped=handWorldPos(cam,a[i].pos,a[i].scale,...pt,0);
   const dir1=target.clone().sub(cam).normalize(),dir2=mapped.sub(cam).normalize();
   check(dir1.distanceTo(dir2)<1e-8,'partner contact projection');
 }
}
const renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true});renderer.setSize(270,480);
renderer.debug.onShaderError=(gl,p,v,f)=>{throw Error('GLSL: '+gl.getProgramInfoLog(p)+' '+gl.getShaderInfoLog(f));};
const scene=new THREE.Scene(),cam=new THREE.PerspectiveCamera(45,270/480,0.2,100);cam.position.set(0,0,5);cam.lookAt(0,0,0);
const texture=(color)=>{const c=document.createElement('canvas');c.width=c.height=128;const g=c.getContext('2d');
 for(let y=0;y<128;y+=4)for(let x=0;x<128;x+=4){g.fillStyle=((x+y)/4)%2?'#1f2440':color;g.fillRect(x,y,4,4);}
 const t=new THREE.CanvasTexture(c);t.colorSpace=THREE.SRGBColorSpace;t.magFilter=THREE.NearestFilter;t.minFilter=THREE.NearestFilter;return t;};
const back=new THREE.Mesh(new THREE.PlaneGeometry(20,20),new THREE.MeshBasicMaterial({map:texture('#e0c882')}));back.position.z=-2;scene.add(back);
const card=new THREE.Mesh(new THREE.PlaneGeometry(1,1),new THREE.MeshBasicMaterial({map:texture('#ff617b')}));card.position.z=1;card.layers.set(3);scene.add(card);
const composer=new EffectComposer(renderer,{multisampling:0});composer.addPass(new RenderPass(scene,cam));
const ink=new InkPass(scene,cam,{strength:0});composer.addPass(ink);
const lens=new LensBlur({maxCoC:12,nearScale:1,minBackgroundCoC:3,backgroundMaxCoC:6});lens.sharpDepth=ink.worldDepthTexture;lens.focus=4;
composer.addPass(new EffectPass(cam,lens.pre));composer.addPass(new EffectPass(cam,lens.main));
const gl=renderer.getContext(),pixels=()=>{const p=new Uint8Array(270*480*4);gl.readPixels(0,0,270,480,gl.RGBA,gl.UNSIGNED_BYTE,p);return p;};
lens.cInf=0;composer.render(0);const sharp=pixels();lens.cInf=9.5;composer.render(0);const blurred=pixels();
let characterMaxDifference=0,backgroundDifference=0,n=0;
for(let y=210;y<270;y++)for(let x=105;x<165;x++)for(let k=0;k<3;k++)characterMaxDifference=Math.max(characterMaxDifference,Math.abs(sharp[(y*270+x)*4+k]-blurred[(y*270+x)*4+k]));
for(let y=120;y<200;y++)for(let x=10;x<50;x++)for(let k=0;k<3;k++){backgroundDifference+=Math.abs(sharp[(y*270+x)*4+k]-blurred[(y*270+x)*4+k]);n++;}
check(characterMaxDifference===0,'DOF modified protected character pixels: '+characterMaxDifference);
check(backgroundDifference/n>2,'background blur did not alter high-frequency detail');
check(gl.getError()===gl.NO_ERROR,'WebGL render error');
window.visualCheck={characterMaxDifference,backgroundMeanDifference:backgroundDifference/n,headRadiusRange:[Math.min(...radii),Math.max(...radii)]};
composer.dispose();renderer.dispose();
`}});
const browser=await openBrowser('chrome',{browserExecutable:'C:/Program Files/Google/Chrome/Application/chrome.exe',chromiumOptions:{gl:'angle'}});
try{
 const page=await browser.newPage({context:{},logLevel:'error',indent:false,pageIndex:0,onBrowserLog:null,onLog:()=>{}});
 await page.evaluate(code=>new Function(code)(),outputFiles[0].text);
 console.log('PASS:',JSON.stringify(await page.evaluate(()=>window.visualCheck)));
}finally{await browser.close({silent:true});}
