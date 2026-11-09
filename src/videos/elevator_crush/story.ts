import {makeShotCam, type V3} from "../../engine/camera";
import type {KidOpts} from "../../engine/character";
// Single source of truth for ElevatorCrushShort time, beats, 11 shots, camera paths, kicks, DOF.
// Pure math only — no Three.js meshes. 1080x1920 @ 30 fps, TOTAL = 3345 frames (111.5 s).
export const FPS = 30;
export const TOTAL = 3345;

export type LightName =
  | "amberCyan" | "rainy" | "emergency" | "violetRim"
  | "heartbeat" | "goldWarm" | "roseGold" | "neon";

export type ShotDef = {
  id: number;
  a: number; // inclusive start
  b: number; // exclusive end
  light: LightName;
  desc: string;
};

export const SHOTS: ShotDef[] = [
  { id: 1,  a: 0,    b: 210,  light: "amberCyan",  desc: "Hook: trapped 3 hours with crush, doors slide shut" },
  { id: 2,  a: 210,  b: 405,  light: "rainy",      desc: "1 sec before closing in the rain, crush enters" },
  { id: 3,  a: 405,  b: 660,  light: "emergency",  desc: "BHADAAM! power cut stuck at floor 4" },
  { id: 4,  a: 660,  b: 906,  light: "emergency",  desc: "Hour 1: pin-drop silence, zero network" },
  { id: 5,  a: 906,  b: 1170, light: "emergency",  desc: "Fixing hair vs inspecting floor buttons (Rule B)" },
  { id: 6,  a: 1170, b: 1524, light: "emergency",  desc: "Dry throat cough & loud stomach growl" },
  { id: 7,  a: 1524, b: 1818, light: "violetRim",  desc: "Hour 2: cable grinds & 2-foot drop" },
  { id: 8,  a: 1818, b: 2196, light: "heartbeat",  desc: "She hugs you tight + 160 BPM heartbeat" },
  { id: 9,  a: 2196, b: 2466, light: "goldWarm",   desc: "Trembling hands, safety brakes locked" },
  { id: 10, a: 2466, b: 2835, light: "roseGold",   desc: "Dim light returns & eye contact" },
  { id: 11, a: 2835, b: 3345, light: "neon",       desc: "Cliffhanger: secret & mystery number on palm" },
];

export const shotAt = (f: number): ShotDef => {
  for (const s of SHOTS) if (f >= s.a && f < s.b) return s;
  return SHOTS[SHOTS.length - 1];
};

export const layersAt = (f: number): { id: number; alpha: number }[] => {
  const s = shotAt(f);
  return [{ id: s.id, alpha: 1.0 }];
};

// ---- math helpers ----
export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
export const glide = (f: number, a: number, b: number) => {
  const t = clamp01((f - a) / Math.max(1, b - a));
  return t * t * (3 - 2 * t);
};
export const lerp = (v0: number, v1: number, t: number) => v0 + (v1 - v0) * t;
export const v3Lerp = (
  p0: [number, number, number], p1: [number, number, number], t: number
): [number, number, number] => [lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t), lerp(p0[2], p1[2], t)];

/** Subtle continuous drift so held frames <= 2% */
export const pushK = (f: number, a: number, b: number, dist = 0.06) => {
  const t = clamp01((f - a) / Math.max(1, b - a));
  return t * dist;
};

// ---- KEY BEAT FRAMES ----
export const DOORS_AT = 90;      // shot 1 doors fully shut
export const RAIN_IN_AT = 285;   // shot 2 crush steps in
export const RAIN_BURST_AT = 310;// rain droplet sparkle burst
export const BHDAM_AT = 486;      // power cut impact (16.2s)
export const PHONE_AT = 780;     // shot 4 phones raise
export const COUGH_AT = 1248;    // 41.6s cough
export const GROWL_AT = 1355;    // 45.2s stomach growl
export const CABLE_AT = 1665;    // 55.5s cable grind sparks
export const DROP_AT = 1710;     // 57.0s elevator 2-ft drop
export const HUG_AT = 1885;      // crush hugs hero, heart burst
export const HEART_AT = 1980;     // heartbeat rings start
export const LIGHTS_BACK_AT = 2480; // shot 10 dim light returns
export const SPARKLE_AT = 2720;   // shot 10 golden sparkles
export const WRITE_AT = 3020;    // shot 11 palm writing ends
export const PALM_AT = 3150;     // shot 11 cyan eyes + burst
export const END_AT = 3344;

// ---- KICKS (impact camera shakes) ----
export type Kick = { f: number; dur: number; amp: number; freq: number };
export const KICKS: Kick[] = [
  { f: BHDAM_AT, dur: 12, amp: 0.11, freq: 2.0 },  // power cut bhadaam
  { f: GROWL_AT, dur: 10, amp: 0.08, freq: 2.4 },  // stomach growl
  { f: CABLE_AT, dur: 12, amp: 0.09, freq: 2.2 },  // cable grind
  { f: DROP_AT,  dur: 14, amp: 0.13, freq: 1.8 },  // 2-foot drop
];

export const kickOffset = (f: number): [number, number, number] => {
  let ox = 0, oy = 0, oz = 0;
  for (const k of KICKS) {
    if (f >= k.f && f < k.f + k.dur) {
      const u = (f - k.f) / k.dur;
      const decay = (1 - u) * (1 - u);
      const s = Math.sin((f - k.f) * k.freq) * k.amp * decay;
      ox += s * 0.4; oy += s * 1.0; oz += s * 0.3;
    }
  }
  return [ox, oy, oz];
};

// ---- Engine camera coverage: alternating diagonals and moving subject focus. ----
export type CamState={pos:V3;look:V3;fov:number;roll:number};
const CAMS:Record<number,{from:V3;to:V3;look:V3;lookTo?:V3;fov:number}>={
 1:{from:[-1.7,1.6,5.4],to:[-1.4,1.5,4.9],look:[0,1.15,0.4],fov:46},
 2:{from:[1.9,1.65,5.6],to:[1.5,1.5,5.1],look:[0,1.2,0],fov:46},
 3:{from:[-1.7,1.1,5.0],to:[-1.4,1.2,4.5],look:[0,1.3,0.4],fov:48},
 4:{from:[1.8,1.65,5.2],to:[1.5,1.5,4.8],look:[0,1.15,0.25],fov:48},
 5:{from:[-1.3,1.6,6.3],to:[-0.8,1.5,5.8],look:[0.3,1.25,-0.7],lookTo:[0.55,1.22,-0.7],fov:45},
 6:{from:[1.65,1.85,4.5],to:[1.3,1.65,4.1],look:[0.05,1.15,0.4],fov:44},
 7:{from:[-1.9,1.15,6.1],to:[-1.6,1.3,5.6],look:[0,1.85,0],fov:48},
 8:{from:[1.45,1.55,4.4],to:[1.1,1.48,4.0],look:[0,1.18,0.55],fov:43},
 9:{from:[-1.45,1.5,4.2],to:[-1.2,1.45,3.9],look:[0,1.2,0.55],fov:42},
 10:{from:[1.5,1.6,4.45],to:[1.2,1.5,4.15],look:[0,1.2,0.55],fov:42},
 11:{from:[-1.6,1.6,4.9],to:[-1.2,1.48,4.4],look:[0,1.16,0.45],fov:44},
};
const cameras=SHOTS.map(s=>makeShotCam({...s,...CAMS[s.id],kicks:KICKS,
 framing:s.id>=8||s.id===6?"close":"medium",focus:f=>focusPointAt(f)
}));
export const camAt=(id:number,f:number):CamState=>cameras[id-1].camAt(f);
export const cameraAt=(f:number)=>camAt(shotAt(f).id,f);
export const engineDofAt=(f:number)=>cameras[shotAt(f).id-1].dofAt(f);

/** Per-frame light: shot 3 stays in the normal cabin look until the BHADAAM power cut. */
export const lightAt = (id: number, f: number): LightName => {
  if (id === 3 && f < BHDAM_AT) return "amberCyan";
  return SHOTS[id - 1].light;
};

// ---- DOF ----
export type DofSpec = { focus: (f: number) => [number, number, number]; cInf: number };

// Legacy world-point interface follows the same active foreground character as engineDofAt.
export const dofAt = (f: number): DofSpec => ({focus:focusPointAt,cInf:engineDofAt(f).cInf});

export const HERO_SCALE=0.84,CRUSH_SCALE=0.78;
export type ActorState={pos:V3;scale:number;opts:KidOpts};
/** Frame-addressable staging shared by the world and projection checker. */
export const actorsAt=(id:number,f:number):ActorState[]=>{
 const hero:ActorState={pos:[-0.5,0,0.65],scale:HERO_SCALE,opts:{kind:"studentHero",expr:"shyBlush",mode:"stand",gaze:0.6}};
 const crush:ActorState={pos:[0.5,0,0.25],scale:CRUSH_SCALE,opts:{kind:"crush",expr:"shyBlush",mode:"stand",gaze:-0.6}};
 if(id===1){hero.opts.expr="panicShock";crush.opts.expr="gentleConcern";}
 if(id===2){hero.pos=[-0.5,0,0.4];crush.pos=[lerp(1.6,0.5,glide(f,285,322)),0,0.05];crush.opts={...crush.opts,mode:"walk",walkP:(f%30)/30,actionP:1-glide(f,335,365),rainDrops:1};hero.opts.expr="panicShock";}
 if(id===3){const j=0.18*Math.sin(Math.PI*clamp01((f-486)/18));hero.pos[1]=j;crush.pos[1]=j;hero.opts.expr=crush.opts.expr="panicShock";}
 if(id===4){hero.pos=[-0.55,0,0.4];crush.pos=[0.55,0,0.05];hero.opts.mode=crush.opts.mode="phone";hero.opts.phoneP=crush.opts.phoneP=glide(f,770,815);hero.opts.sweat=1;}
 if(id===5){hero.pos=[1.38,0,-1.25];crush.pos=[-0.45,0,-1.0];hero.opts={...hero.opts,mode:"point",pointP:glide(f,920,1000),gripX:145,gripY:565,gaze:0.8};crush.opts={...crush.opts,mode:"fixHair",fixHairP:0.4+0.6*glide(f,906,1050)};}
 if(id===6){hero.pos=[0.12,0,0.65];crush.pos=[-0.9,0,-0.45];hero.opts={...hero.opts,mode:"stomachGrowl",growlP:glide(f,1345,1380),expr:f>=1355?"strainGrin":"shyBlush",sweat:1};crush.opts.expr="gentleConcern";}
 if(id===7){const j=0.24*Math.sin(Math.PI*clamp01((f-1710)/22));hero.pos[1]=crush.pos[1]=j;hero.opts.expr=crush.opts.expr="panicShock";}
 if(id>=8&&id<=10){
  hero.pos=[-0.28,0,0.65];crush.pos=[lerp(0.85,0.3,glide(f,1818,1890)),0,0.55];
  hero.opts={...hero.opts,mode:id===9?"comfort":"hug",comfortP:glide(f,2196,2260),hugP:glide(f,1850,1900),partnerSide:1,expr:id===8?"shyBlush":"gentleConcern",heartBeatP:id===8&&f>=1980?0.4+0.6*Math.sin(f*0.45)**2:0};
  crush.opts={...crush.opts,mode:"hug",hugP:glide(f,1830,1890),partnerSide:-1,expr:id===10?"flirtyWink":"shyBlush"};
 }
 if(id===11){hero.pos=[-0.35,0,0.65];crush.pos=[0.35,0,0.4];
  hero.opts={...hero.opts,mode:f<3206?"palmShow":"wave",palmP:glide(f,2980,3150),palmScale:1.35,palmText:f>=3021?"98XXXXXX??":undefined,expr:f>=3150?"panicShock":"shyBlush",waveP:(f%36)/36};
  crush.opts={...crush.opts,mode:f<3206?"writePalm":"wave",writePalmP:glide(f,2835,3020),waveP:(f%40)/40,expr:"flirtyWink"};
 }
 return [hero,crush];
};

/** Actual foreground plane along the live view axis; look targets may sit on architecture. */
export const focusPointAt=(f:number):V3=>{
 const shot=shotAt(f),a=actorsAt(shot.id,f),c=cameraAt(f);
 const forward=c.look.map((v,i)=>v-c.pos[i]);
 const depth=(v:ActorState)=>v.pos.reduce((sum,x,i)=>sum+(x+(i===1?1.22:0)-c.pos[i])*forward[i],0);
 const focus=shot.id===5||shot.id===6?a[0]:a.reduce((near,x)=>depth(x)<depth(near)?x:near);
 return [focus.pos[0],focus.pos[1]+1.22,focus.pos[2]];
};
