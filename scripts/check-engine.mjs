// Browser canvas and pure-math regression checks for the shared studio engine.
// Run: node scripts/check-engine.mjs. No movie render or public asset copy.
import {build} from "esbuild";
import {openBrowser} from "@remotion/renderer";
import fs from "node:fs/promises";
const {outputFiles} = await build({bundle: true, write: false, format: "iife", platform: "browser", stdin: {
  resolveDir: process.cwd(), contents: `
import * as THREE from 'three';
import {makeShotCam} from './src/engine/camera';
import {Pen, drawKid, elbowOf} from './src/engine/character';
import {Pool, makeChar, lidAt, talkAt, tier, handWorldPos} from './src/engine/pool';
import * as paint from './src/engine/shaders/paint';
import * as kit from './src/engine/kit3d';
import {AUDIO_ENV} from './src/videos/elevator_crush/audioEnv';
const check = (ok, message) => {if (!ok) throw Error(message);};
const near = (a,b) => Math.abs(a-b) < 1e-8;
let cameraFrames = 0;
for (const stationary of [false,true]) {
  const camera = makeShotCam({a: 12,b: 312,from: [-1,1.5,5],to: stationary ? [-1,1.5,5] : [1,1.4,3],look: [0,1.2,0],fov: 100,focus: f => [Math.sin(f/30),1.2,0]});
  let last;
  for (let f=12;f<=312;f++) {
    const c = camera.camAt(f), d = camera.dofAt(f);
    check(c.fov>=38 && c.fov<=50,'FOV constraint');
    if (last) check(new THREE.Vector3(...c.pos).distanceTo(new THREE.Vector3(...last.pos))>0,'held camera frame');
    const expected = new THREE.Vector3(Math.sin(f/30),1.2,0).sub(new THREE.Vector3(...c.pos)).dot(new THREE.Vector3(...c.look).sub(new THREE.Vector3(...c.pos)).normalize());
    check(near(expected,d.focus),'view-axis DOF projection'); last=c; cameraFrames++;
  }
}
for (let a=0;a<Math.PI*2;a+=0.25) {
  const cam=new THREE.Vector3(Math.sin(a)*4,1.5,Math.cos(a)*4), pos=[0,0,0], sc=0.85;
  const point=handWorldPos(cam,pos,sc,145,565), yaw=Math.atan2(cam.x,cam.z);
  const local=point.clone().applyAxisAngle(new THREE.Vector3(0,1,0),-yaw);
  check(near(local.x,(145-300)*0.00216*sc)&&near(local.y,(975-565)*0.00216*sc)&&near(local.z,-0.08),'Rule B pinning');
}
for (const side of [-1,1]) for (let y=400;y<=680;y+=20) {
  const s=[300+side*70,397], h=[300+side*100,y], away=[300,485];
  const e=elbowOf(s,h,142,142,away);
  check(near(Math.hypot(e[0]-s[0],e[1]-s[1]),142),'upper arm bone');
  if(Math.hypot(h[0]-s[0],h[1]-s[1])<=284) check(near(Math.hypot(e[0]-h[0],e[1]-h[1]),142),'forearm bone');
  check(e[0]*side >= s[0]*side,'outward elbow');
}
check(tier(2)[0]===1800&&tier(2)[1]===3000,'close-up tier');
check(talkAt(2,[0,0.19,0.61,2])===0.6 && talkAt(99,[0,2])===1 && talkAt(0,[])===0,'talk envelope');
check(lidAt(8000,3)===lidAt(8000,3),'seekable blink');
const pool=new Pool(); let calls=0;
const a=pool.req('same',60,100,0.1,()=>calls++), b=pool.req('same',60,100,0.1,()=>calls++);pool.flush();
check(calls===1&&a.tex===b.tex,'texture sharing');
pool.req('same',60,100,0.2,()=>calls++);pool.flush();check(calls===2,'drawing scale participates in cache key');pool.dispose();
const cam={pos:new THREE.Vector3(0,1,3),right:new THREE.Vector3(1,0,0)};
const place=makeChar(cam,0,0,0,{kind:'studentHero',expr:'neutral',mode:'phone',phoneP:0.333,talk:0.31});
check(place.key.includes('"phoneP":0.34')&&place.key.includes('"talk":0.4'),'draw/key quantization');
const cabin=kit.buildElevatorCabin();
check(cabin.width===4.6&&cabin.depth===4.2&&cabin.height===3.8,'default cabin dimensions');
check(Object.keys(cabin.buttons).sort().join(',')==='1,2,3,4,FAN,G','six illuminated control buttons');
cabin.setDoorGap(0);check(near(cabin.doors[0].position.x,-0.5)&&near(cabin.doors[1].position.x,0.5),'closed doors');
cabin.setDoorGap(1);check(near(cabin.doors[0].position.x,-1.5)&&near(cabin.doors[1].position.x,1.5),'open doors');
cabin.root.position.set(3,0,-2);cabin.root.rotation.y=0.4;
const pin=new THREE.Vector3(3.1,1.2,-0.8);cabin.pinButton('FAN',pin);
check(cabin.buttonWorldPosition('FAN').distanceTo(pin)<1e-8,'transformed cabin Rule B pin');
cabin.dispose();
const corridor=kit.buildRainCorridor();corridor.redrawRain(7);const rain=corridor.rain.image.toDataURL();corridor.redrawRain(7);check(rain===corridor.rain.image.toDataURL(),'seekable corridor rain');corridor.dispose();
check(AUDIO_ENV.length===3345&&AUDIO_ENV.every(x=>Number.isFinite(x)&&x>=0&&x<=1)&&AUDIO_ENV.some(x=>x===0)&&AUDIO_ENV.some(x=>x>0.8),'real normalized audio envelope');
const t1=paint.makeSteelTexture();paint.makeBrassTexture();const t2=paint.makeSteelTexture();
check(t1.image.toDataURL()===t2.image.toDataURL(),'order-independent procedural textures');t1.dispose();t2.dispose();
const kinds=['builder','rival','studentHero','crush','plaidHero','mom'];
const modes=['stand','walk','run','sit','hug','wave','swing','hammerHold','wallet','point','phone','fixHair','stomachGrowl','comfort','writePalm','palmShow','prayer','kissPalm','toiletSit','pressFlush','sofaPhone','knockDoor','peekDoor','liftMug'];
const exprs=['neutral','happyProud','strainGrin','brokeSad','evilSmirk','panicShock','shyBlush','gentleConcern','warmMusic','emotionalTears','prayerUp','flirtyWink','blissKiss'];
const cv=document.createElement('canvas');cv.width=600;cv.height=1000;const ctx=cv.getContext('2d'), pen=new Pen(ctx);
let draws=0;
for(const kind of kinds) for(const mode of modes) for(const actionP of [0,0.5,1]) {
  ctx.clearRect(0,0,600,1000);drawKid(pen,{kind,mode,expr:'neutral',actionP,walkP:actionP,runP:actionP,swingP:actionP,walletP:actionP});draws++;
}
for(const expr of exprs) for(const talk of [0,0.2,0.6,1]) for(const blink of [0,0.5,1]) {
  ctx.clearRect(0,0,600,1000);drawKid(pen,{kind:'crush',mode:'stand',expr,talk,blink});draws++;
}
const sheet=document.createElement('canvas');sheet.width=1200;sheet.height=1530;const g=sheet.getContext('2d');g.fillStyle='#a9b8bd';g.fillRect(0,0,1200,1530);
for(let row=0;row<3;row++)for(let col=0;col<4;col++){
  ctx.clearRect(0,0,600,1000);drawKid(pen,{kind:kinds[col],mode:['stand','sit','prayer'][row],expr:['happyProud','shyBlush','prayerUp'][row]});
  g.drawImage(cv,col*300,row*510,300,500);g.fillStyle='#351f22';g.font='16px Arial';g.fillText(kinds[col]+' / '+['stand','sit','prayer'][row],col*300+12,row*510+505);
}
window.engineCheck={cameraFrames,draws,image:sheet.toDataURL('image/png')};
`}});
const browser = await openBrowser("chrome", {browserExecutable: "C:/Program Files/Google/Chrome/Application/chrome.exe", chromiumOptions: {gl: "angle"}});
try {
  const page = await browser.newPage({context: {},logLevel: "error",indent: false,pageIndex: 0,onBrowserLog: null,onLog: ()=>{}});
  await page.evaluate(code => { new Function(code)(); }, outputFiles[0].text);
  const result = await page.evaluate(() => window.engineCheck);
  await fs.mkdir("out/engine",{recursive:true});
  const preview = `out/engine/characters_${Date.now()}.png`;
  await fs.writeFile(preview,Buffer.from(result.image.split(",")[1],"base64"));
  console.log(`PASS: ${result.cameraFrames} camera samples, ${result.draws} character drawings; IK, cabin doors, transformed control pinning, corridor rain, audio envelopes, pooling and deterministic textures. Preview: ${preview}`);
} finally {await browser.close({silent: true});}
