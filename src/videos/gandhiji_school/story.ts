import type {Cam, V3, PlayerShot} from "../../engine";

export const FPS = 30, TOTAL = 525;
export const CAL_FRAMES = [30, 80, 150, 225, 285, 335, 410, 500];
export const SCALE = 0.85;
export const SPEAKER: V3 = [-0.25, -0.042228, 0.35];
export const STUDENT: V3 = [0.55, -0.042228, -0.85];
export const PODIUM: V3 = [-0.35, 0, 0.4];
export const DESK: V3 = [0.55, 0, -0.9];
export const PODIUM_TOP = 0.94, DESK_TOP = 0.82, SEAT_TOP = 0.52;
export const clamp01 = (x: number) => Math.max(0, Math.min(1, x));
export const ease = (f: number, a: number, b: number) => 1 - (1 - clamp01((f-a)/(b-a))) ** 3;
const mix = (a: V3, b: V3, p: number): V3 => a.map((x,i) => x+(b[i]-x)*p) as V3;
export const SHOTS: PlayerShot[] = [
  {id: 1, a: 0, b: 54, grade: "warm"},
  {id: 2, a: 54, b: 105, grade: "warm"},
  {id: 3, a: 105, b: 186, grade: "night"},
  {id: 4, a: 186, b: 264, grade: "night"},
  {id: 5, a: 264, b: 303, grade: "clinic"},
  {id: 6, a: 303, b: 363, grade: "clinic"},
  {id: 7, a: 363, b: 435, grade: "vivid"},
  {id: 8, a: 435, b: TOTAL, grade: "vivid"},
];
export const shotAt = (f: number) => SHOTS.find(s => f>=s.a && f<s.b)!;
const CAMS: Record<number, {from: V3; to: V3; look: V3; roll?: number; end?: number}> = {
  1: {from: [0.1,1.5,4.7], to: [0.1,1.5,4.45], look: [0.1,1.08,0.1]},
  2: {from: [-0.45,1.18,3.48], to: [-0.45,1.18,3.38], look: [-0.45,1.31,0.35]},
  3: {from: [-0.15,1.4,3.3], to: [-0.15,1.4,3.2], look: [-0.15,1.3,0.35], roll: 5*Math.PI/180},
  4: {from: [0.6,1.32,1.85], to: [0.6,1.32,1.65], look: [0.55,1.04,-0.85]},
  5: {from: [-0.25,1.38,1.84], to: [-0.25,1.38,1.84], look: [-0.25,1.36,0.35]},
  6: {from: [-0.25,1.38,1.84], to: [-0.25,1.38,1.84], look: [-0.25,1.36,0.35]},
  7: {from: [0.1,1.65,4.75], to: [0.1,1.65,4.55], look: [0.1,0.98,-0.1]},
  8: {from: [-0.25,1.05,3.85], to: [-0.25,1.05,3.75], look: [-0.25,1.18,0.35], end: 476},
};
export const camAt = (f: number): Cam => {
  const shot = shotAt(f), c = CAMS[shot.id];
  const p = ease(f, shot.a, c.end ?? shot.b-1);
  const pos = mix(c.from,c.to,p), look = [...c.look] as V3;
  for (const [at, duration, gain] of [[304,7,0.027],[402,6,0.017],[485,6,0.034]]) {
    const n=f-at;
    if(n>=0 && n<duration) {
      const k=gain*(1-n/duration)**2*(n%2 ? -1 : 1);
      pos[0]+=k; pos[1]+=k*0.6;
    }
  }
  return {pos,look,fov: 45,roll:c.roll ?? 0};
};
export const dofAt = (f: number) => {
  const c=camAt(f), s=shotAt(f), subject=s.id===4 ? [0.55,1.15,-0.85] : [-0.25,1.35,0.35];
  const d=c.look.map((v,i)=>v-c.pos[i]), n=Math.hypot(...d);
  return {focus:subject.reduce((a,v,i)=>a+(v-c.pos[i])*d[i]/n,0),cInf:s.id===7 ? 9 : 22};
};
export const speechAt = (f: number) => (f<264 || (f>=303 && f<=350) || (f>=363 && f<476));
export const actingAt = (f: number) => {
  const glasses=ease(f,56,72)*(1-ease(f,95,103));
  const chin=ease(f,108,118)*(1-ease(f,178,185));
  const temples=ease(f,189,203)*(1-ease(f,390,400));
  const plant=f<402 ? ease(f,393,402) : 1-0.12*(1-ease(f,403,408));
  const point=ease(f,368,382);
  return {glasses,chin,temples,plant:f<393?0:plant,point,
    smile:ease(f,363,371), serious:f<264?1:0, stress:ease(f,186,196)*(1-ease(f,363,373)),
    dizzy:ease(f,390,398), turn: f>=105&&f<186 ? 0.73*ease(f,108,116) : 0,
    gleam: f>=68&&f<=86 ? (f-68)/18 : -1,
    tear:f>=264&&f<363 ? 0.15+0.85*ease(f,305,355) : -1,
    wag:f>=435&&f<476 ? Math.sin((f-435)/8)*ease(f,435,443)*(1-ease(f,468,476)) : 0,
  };
};
export const lightAt = (f: number) => f<105 ? "warm" : f<264 ? "mystery" : f<363 ? "clinical" : "vivid";
export const hudAt = (f: number) => {
  const title=f<105 ? "UPSC IAS INTERVIEW RIDDLE: 99% FAIL" : f<264 ? "DEEP HISTORICAL MYSTERY... OR STRICT AHIMSA?" : f<363 ? "THE ACTUAL ANSWER: ZERO IQ REQUIRED" : "REALITY CHECK: CLOSE REELS & OPEN YOUR BOOKS!";
  const secondary=f>=105&&f<264 ? "THEORIES: 1947 HISTORY | SATYAGRAHA | AHIMSA RULES" : f>=312&&f<363 ? "[100% FACTUAL: PASSED AWAY IN 1948]" : f>=485 ? "CLOSE REELS -> START STUDYING!" : "";
  const hit=f>=485?ease(f,485,491):f>=312&&f<363?ease(f,312,318):1;
  return {title,secondary,stamp:f>=312&&f<363,cta:f>=485,scale:1+0.14*(1-hit)};
};
