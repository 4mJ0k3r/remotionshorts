import {build} from 'esbuild';
import {openBrowser} from '@remotion/renderer';
import fs from 'node:fs/promises';
const {outputFiles}=await build({bundle:true,write:false,format:'iife',platform:'browser',stdin:{resolveDir:process.cwd(),contents:`
import * as THREE from 'three';
import {EffectComposer,RenderPass,EffectPass,BloomEffect,ToneMappingEffect,ToneMappingMode,BlendFunction} from 'postprocessing';
import {InkPass,noInkFallback} from './src/engine/shaders/ink';
import {LensBlur} from './src/engine/shaders/lensblur';
import {GradeEffect,GRADES,gradeFor} from './src/engine/shaders/grade';
import {World} from './src/videos/crush_bathroom/world';
import {cameraAt,dofAt,shotAt,CALIBRATION,SHOTS} from './src/videos/crush_bathroom/story';
const renderer=new THREE.WebGLRenderer({antialias:false,preserveDrawingBuffer:true,powerPreference:'high-performance'});renderer.setSize(540,960);renderer.localClippingEnabled=true;
renderer.debug.onShaderError=(gl,p,v,f)=>{throw Error(gl.getProgramInfoLog(p)+' '+gl.getShaderInfoLog(f));};
const gl=renderer.getContext(),debug=gl.getExtension('WEBGL_debug_renderer_info'),gpu=debug?gl.getParameter(debug.UNMASKED_RENDERER_WEBGL):'unknown';
const scene=new THREE.Scene(),cam=new THREE.PerspectiveCamera(45,540/960,.2,1500),world=new World();scene.add(world.root);
const composer=new EffectComposer(renderer,{multisampling:4});composer.addPass(new RenderPass(scene,cam));const ink=new InkPass(scene,cam);composer.addPass(ink);
const lens=new LensBlur({maxCoC:14,nearScale:1,minBackgroundCoC:6,backgroundMaxCoC:10});lens.sharpDepth=ink.worldDepthTexture;
const bloom=new BloomEffect({blendFunction:BlendFunction.ADD,intensity:.4,luminanceThreshold:1,mipmapBlur:true}),tone=new ToneMappingEffect({mode:ToneMappingMode.NEUTRAL}),grade=new GradeEffect(GRADES.day,1);
composer.addPass(new EffectPass(cam,lens.pre));composer.addPass(new EffectPass(cam,lens.main));composer.addPass(new EffectPass(cam,bloom,tone,grade));
const frame=f=>{const c=cameraAt(f);cam.position.set(...c.pos);cam.up.set(0,1,0);cam.lookAt(...c.look);cam.rotateZ(c.roll);cam.fov=c.fov;cam.updateProjectionMatrix();cam.updateMatrixWorld();world.update(shotAt(f).id,f,cam,scene);noInkFallback(world.root);const d=dofAt(f);lens.focus=d.focus;lens.cInf=d.cInf;gradeFor(grade,shotAt(f).grade);composer.render(0);gl.finish();};
const pixels=()=>{const out=new Uint8Array(540*960*4);gl.readPixels(0,0,540,960,gl.RGBA,gl.UNSIGNED_BYTE,out);return out;};
const rows=[];
for(const f of [...new Set([...CALIBRATION,...SHOTS.flatMap(s=>[s.a+2,s.b-3])])]){frame(f);const a=pixels();frame(f+1);const b=pixels();let sum=0,n=0,luma=0;for(let y=0;y<960;y+=3)for(let x=0;x<540;x+=3){const j=(y*540+x)*4;for(let k=0;k<3;k++){sum+=Math.abs(a[j+k]-b[j+k]);n++;}luma+=a[j]*.2126+a[j+1]*.7152+a[j+2]*.0722;}
 rows.push({f,motion:sum/n,luma:luma/(540/3*960/3*255)});
 const visible=['bathroom','bowl','science','hall'].filter(name=>world.root.getObjectByName('cb-'+name).visible);if(visible.length!==1)throw Error('set visibility isolation failed');}
for(let f=2700;f<2705;f++)frame(f);const t=performance.now();for(let f=2705;f<2725;f++)frame(f);const fps=20/((performance.now()-t)/1000);
window.result={gpu,framesPerMinute:fps*60,rows,glError:gl.getError()};world.dispose();composer.dispose();renderer.dispose();
`}});
const browser=await openBrowser('chrome',{browserExecutable:'C:/Program Files/Google/Chrome/Application/chrome.exe',chromiumOptions:{gl:'angle'}});
try{const page=await browser.newPage({context:{},logLevel:'error',indent:false,pageIndex:0,onBrowserLog:null,onLog:()=>{}});await page.evaluate(code=>new Function(code)(),outputFiles[0].text);const result=await page.evaluate(()=>window.result);await fs.writeFile('out/crush_bathroom/gpu_preflight.json',JSON.stringify(result,null,2));console.log(JSON.stringify(result));}finally{await browser.close({silent:true});}
