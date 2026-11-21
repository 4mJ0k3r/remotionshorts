import {Pen, handEllPts} from "./shaders/pen";
import {elbowOf, type P2} from "./character";

export type ClassroomCelOpts = {
  role: 'speaker' | 'student'; talk?: number; lid?: number; serious?: number;
  smile?: number; stress?: number; dizzy?: number; turn?: number; gleam?: number;
  tear?: number; plantP?: number; glassesP?: number; chinP?: number;
  templesP?: number; pointP?: number; wagP?: number;
  leftHand?: [number, number]; rightHand?: [number, number];
  layer?: 'body' | 'arms'; shoulders?: [P2, P2]; headPoint?: P2; finalHands?: [P2, P2];
};
const INK = "#161219", CREAM = "#fdfaf2", COOL = "#dce1e4", R = 145;
const unit = (x = 0) => Math.max(0, Math.min(1, Number.isFinite(x) ? x : 0));
const ease = (x = 0) => {const k = unit(x); return k * k * (3 - 2 * k);};
const mix = (a: number, b: number, k: number) => a + (b - a) * k;
const blend = (a: P2, b: P2, k: number): P2 => [mix(a[0], b[0], k), mix(a[1], b[1], k)];
const planted = (o: ClassroomCelOpts) => o.role === "student" ? unit(o.plantP) : 0;
const facePoint = (o: ClassroomCelOpts, head: P2, x: number, y: number): P2 => {
  const a = planted(o) * 70 * Math.PI / 180;
  const turn = Math.max(-1, Math.min(1, o.turn ?? 0));
  const dx = x * (1 - Math.abs(turn) * .18) + turn * R * .22;
  return [head[0] + dx * Math.cos(a) - y * Math.sin(a), head[1] + dx * Math.sin(a) + y * Math.cos(a)];
};

/** Hand overrides set fixture contacts before gesture blending. */
export const classroomPose = (o: ClassroomCelOpts): {
  head: P2; shoulders: [P2, P2]; hips: [P2, P2]; hands: [P2, P2];
  knees: [P2, P2]; feet: [P2, P2];
} => {
  const student = o.role === "student", k = planted(o);
  const head: P2 = o.headPoint ?? (student ? blend([300, 345], [365, 361], k) : [300, 235]);
  const sx = mix(300, 330, k), sy = student ? mix(477, 510, k) : 395;
  const shoulders: [P2, P2] = o.shoulders ?? [[sx - 70, sy], [sx + 70, sy]];
  const hips: [P2, P2] = [[265, student ? 669 : 590], [335, student ? 669 : 590]];
  const knees: [P2, P2] = student ? [[375, 678.6], [455, 679.5]] : [[265, 765], [335, 765]];
  const feet: [P2, P2] = [[knees[0][0], 952], [knees[1][0], 952]];
  let left: P2 = o.leftHand ? [...o.leftHand] : [sx - 105, sy + 145];
  let right: P2 = o.rightHand ? [...o.rightHand] : [sx + 105, sy + 145];
  right = blend(right, facePoint(o, head, 0, 42), ease(o.glassesP));
  right = blend(right, facePoint(o, head, 22, 114), ease(o.chinP));
  const point = ease(o.pointP), wag = Math.max(-1, Math.min(1, o.wagP ?? 0));
  right = blend(right, [sx + 110 + wag * 15, sy + 86], point);
  const temples = student ? ease(o.templesP) : 0;
  left = blend(left, [head[0] - R - 12, head[1] + 8], temples);
  right = blend(right, [head[0] + R + 12, head[1] + 8], temples);
  return {head, shoulders, hips, knees, feet, hands: o.finalHands ?? [left, right]};
};

// Pen's legacy fill outlines use another ink; every classroom outline is explicit.
const shape = (p: Pen, pts: P2[], fill: string | null, width = 16.5) => {
  p.poly(pts, fill, 0);
  if (width) p.stroke([...pts, pts[0]], width, INK);
};
const oval = (p: Pen, x: number, y: number, rx: number, ry: number, fill: string | null, width = 0) =>
  shape(p, handEllPts(x, y, rx, ry), fill, width);
const curve = (p: Pen, a: P2, c: P2, b: P2, width: number, color = INK) => {
  const g = p.g;
  g.beginPath(); g.moveTo(...p.P(...a)); g.quadraticCurveTo(...p.P(...c), ...p.P(...b));
  g.lineWidth = width; g.strokeStyle = color; g.lineCap = "round"; g.stroke();
};
const roundedLimb = (p: Pen, start: P2, joint: P2, end: P2, width: number, color: string) => {
  const g = p.g, before = blend(start, joint, .76), after = blend(joint, end, .24);
  g.beginPath(); g.moveTo(...p.P(...start)); g.lineTo(...p.P(...before));
  g.quadraticCurveTo(...p.P(...joint), ...p.P(...after)); g.lineTo(...p.P(...end));
  g.lineCap = "round"; g.lineJoin = "round"; g.strokeStyle = INK; g.lineWidth = width + 12; g.stroke();
  g.strokeStyle = color; g.lineWidth = width; g.stroke();
};
const torsoPoints = (top: P2, bottom: P2): P2[] => {
  // A sheared pill remains attached to the fixed bench hips during the head plant.
  const pts: P2[] = [];
  for (let cap = 0; cap < 2; cap++) for (let i = 0; i <= 32; i++) {
    const a = (cap === 0 ? Math.PI : 0) + i * Math.PI / 32;
    const y = (cap === 0 ? top[1] + 8 : bottom[1] - 8) + 22 * Math.sin(a);
    const t = unit((y - top[1] - 8) / (bottom[1] - top[1] - 16));
    pts.push([mix(top[0], bottom[0], t) + 78 * Math.cos(a), y]);
  }
  return pts;
};

/** 600x1000 body card, with no head pixels and no root translation. */
export const drawClassroomBody = (p: Pen, o: ClassroomCelOpts) => {
  const saved = p.rot; p.rot = null; const g = p.g; g.save();
  try {
    const pose = classroomPose(o), student = o.role === "student";
    const top: P2 = blend(pose.shoulders[0], pose.shoulders[1], .5);
    const bottom: P2 = blend(pose.hips[0], pose.hips[1], .5);
    const cloth = student ? "#e0a96d" : "#1d2d44";
    if (o.layer !== 'arms') {
    pose.hips.forEach((hip, i) => {
      const foot = pose.feet[i];
      roundedLimb(p, hip, pose.knees[i], [foot[0], 936], 19, INK);
      // Exact sole y=952, rounded black shoes without an external stroke.
      const x = foot[0];
      g.beginPath(); g.moveTo(x - 14, 928); g.lineTo(x + 14, 928);
      g.quadraticCurveTo(x + 26, 928, x + 26, 940); g.quadraticCurveTo(x + 26, 952, x + 14, 952);
      g.lineTo(x - 14, 952); g.quadraticCurveTo(x - 26, 952, x - 26, 940);
      g.quadraticCurveTo(x - 26, 928, x - 14, 928); g.fillStyle = INK; g.fill();
    });
    const torso = torsoPoints(top, bottom);
    shape(p, [[top[0]-18,top[1]+12],[top[0]+18,top[1]+12],[pose.head[0]+18,pose.head[1]+140],[pose.head[0]-18,pose.head[1]+140]], CREAM, 0);
    p.poly(torso, cloth, 0);
    p.clip(torso, () => {
      const tint = g.createLinearGradient(top[0]-78,0,top[0]-45,0);
      tint.addColorStop(0,"rgba(71,88,105,.15)");tint.addColorStop(1,"rgba(71,88,105,0)");
      g.fillStyle=tint;g.fillRect(top[0]-90,top[1]-20,180,bottom[1]-top[1]+50);
    });
    g.save();g.beginPath();torso.forEach(([x,y],i)=>i?g.lineTo(x,y):g.moveTo(x,y));g.closePath();g.clip();
    if (!student) {
      shape(p, [[top[0] - 27, top[1] - 9], [top[0] + 27, top[1] - 9], [top[0], top[1] + 69]], "#ffffff", 5);
      shape(p, [[top[0] - 28, top[1] - 5], [top[0] - 4, top[1] + 24], [top[0] - 40, top[1] + 14]], "#ffffff", 4);
      shape(p, [[top[0] + 28, top[1] - 5], [top[0] + 4, top[1] + 24], [top[0] + 40, top[1] + 14]], "#ffffff", 4);
      shape(p, [[top[0] - 9, top[1] + 14], [top[0] + 9, top[1] + 14], [top[0] + 5, top[1] + 30], [top[0] + 13, top[1] + 80], [top[0], top[1] + 93], [top[0] - 13, top[1] + 80], [top[0] - 5, top[1] + 30]], "#c83940", 4);
      curve(p, [top[0] - 53, top[1] + 22], [top[0] - 19, top[1] + 91], [bottom[0], bottom[1] - 10], 5, "#455470");
      p.dot(bottom[0] + 14, bottom[1] - 32, 4, "#d8b765");
    } else {
      p.arc(top[0], top[1] + 2, 30, 16, 0, 180, 7, INK);
      curve(p, [bottom[0] - 56, bottom[1] - 6], [bottom[0], bottom[1] + 5], [bottom[0] + 56, bottom[1] - 6], 5, "#a77c2c");
    }
    g.restore();p.inkRing(torso,12.5,Math.PI*.75,.25,INK);
    }
    if (o.layer !== 'body') pose.shoulders.forEach((s, i) => {
      const h = pose.hands[i], side = i ? 1 : -1;
      const temples = student ? ease(o.templesP) : 0;
      const gesture = i ? Math.max(ease(o.glassesP), ease(o.chinP), ease(o.pointP), temples) : temples;
      const bone = mix(110, 140, temples);
      let elbow = elbowOf(s, h, bone, bone, top);
      elbow = blend([elbow[0], Math.min(elbow[1], h[1] - 24)], elbow, gesture);
      const outside = pose.head[0] + side * (R * 1.12 + 20);
      elbow = blend(elbow, [side < 0 ? Math.min(elbow[0], outside) : Math.max(elbow[0], outside), elbow[1]], temples);
      elbow[0] = Math.max(30, Math.min(570, elbow[0]));
      // Only arms are clipped; endpoints stay exact for separately composed head/hand contact.
      g.save(); g.beginPath(); g.rect(0, 0, 600, 1000);
      g.moveTo(pose.head[0] + R + 8, pose.head[1]);
      g.arc(pose.head[0], pose.head[1], R + 8, 0, Math.PI * 2); g.clip("evenodd");
      roundedLimb(p, s, elbow, h, 16, INK); g.restore();
      oval(p, h[0], h[1], 20 + (i ? ease(o.pointP) * 8 : 0), 18, INK);
      if (i) {
        const k = ease(o.pointP), wag = Math.max(-1, Math.min(1, o.wagP ?? 0));
        oval(p, h[0], h[1] - 7 * k, 12 + 3 * k, 12 + 3 * k, INK);
        curve(p, [h[0] - 2, h[1] - 7], [h[0] + 4 + wag * 8, h[1] - 20 * k], [h[0] + 5 + wag * 12, h[1] - 42 * k], 11, INK);
      }
    });
  } finally {g.restore(); p.rot = saved;}
};

/** 600x600 independent head card centered on [300,300]. */
export const drawClassroomHead = (p: Pen, o: ClassroomCelOpts) => {
  const saved = p.rot; p.rot = null; const g = p.g; g.save();
  try {
    const head = handEllPts(300, 300, R, R), student = o.role === "student";
    p.poly(head, CREAM, 0);
    // Offset cream disk cuts a cool, approximately 15%-area bottom-left crescent.
    p.clip(head, () => {
      p.poly(head, COOL, 0); p.ell(317, 283, R, R, CREAM, 0);
    });
    g.save(); g.globalAlpha *= student ? unit(o.stress) * .27 : 0;
    p.clip(head, () => {p.ell(300, 334, 130, 94, "#ef9b92", 0);}); g.restore();
    p.inkRing(head, 16.5, Math.PI * .75, .18, INK);
    g.save(); g.translate(300, 300); g.rotate(planted(o) * 70 * Math.PI / 180);
    const turn = Math.max(-1, Math.min(1, o.turn ?? 0));
    g.translate(turn * R * .22, 0); g.scale(1 - Math.abs(turn) * .18, 1); g.translate(-300, -300);
    if (student) {
      shape(p, [[178, 229], [185, 172], [215, 184], [225, 147], [258, 174], [281, 138], [299, 169], [331, 147], [349, 175], [386, 162], [412, 208], [405, 241], [376, 208], [342, 221], [310, 201], [278, 222], [243, 207], [208, 239]], INK, 9);
    } else {
      const tuft: P2[] = [[176, 235], [184, 192], [227, 156], [284, 144], [342, 149], [382, 163], [421, 157], [406, 191], [384, 211], [340, 216], [313, 202], [279, 215], [244, 209], [209, 231]];
      shape(p, tuft, INK, 9);
      curve(p, [213, 190], [290, 150], [382, 180], 5, "#38404a");
      curve(p, [225, 201], [307, 163], [388, 188], 4, "#38404a");
    }
    const serious = unit(o.serious), stress = unit(o.stress), lid = unit(o.lid);
    const dizzy = student ? unit(o.dizzy) : 0, ey = 310;
    for (const side of [-1, 1]) {
      const ex = 300 + side * 53, aperture = (1 - lid) * (1 - serious * .48), hh = 25 * aperture;
      p.clip([[ex - 34, ey - hh], [ex + 34, ey - hh], [ex + 34, ey + hh], [ex - 34, ey + hh]], () => {
        g.save(); g.globalAlpha *= 1 - dizzy; p.ell(ex + turn * 7, ey, 15, 24, INK, 0); g.restore();
        g.save(); g.globalAlpha *= dizzy;
        const spiral: P2[] = [];
        for (let j = 0; j <= 100; j++) {const a = j / 100 * Math.PI * 5, r = 2 + j / 100 * 24; spiral.push([ex + Math.cos(a) * r, ey + Math.sin(a) * r]);}
        p.stroke(spiral, 5, INK); g.restore();
      });
      g.save(); g.globalAlpha *= 1 - aperture;
      p.stroke([[ex - 25, ey - hh], [ex + 25, ey - hh]], 7, INK); g.restore();
      curve(p, [ex - 24, ey - 45 - side * stress * 10], [ex, ey - 48 + serious * 9], [ex + 24, ey - 45 + side * stress * 10], 8, INK);
    }
    const talk = Math.max(unit(o.talk), student ? stress * .9 : 0), smile = unit(o.smile) * (1 - serious), my = 373;
    const mouth: P2[] = [], mw=28+talk*10+smile*22;
    for (let j = 0; j <= 40; j++) {
      const a = j / 40 * Math.PI * 2, x = Math.cos(a) * mw;
      mouth.push([300 + x, my + smile * 14 * (1 - (x / mw) ** 2) + Math.sin(a) * (talk * (19 + 5 * Math.cos(a))+smile*18)]);
    }
    shape(p, mouth, INK, 7);
    p.clip(mouth,()=>{
      if(smile>.01){g.fillStyle="#fdfaf2";g.fillRect(300-mw,my-25,mw*2,20);}
      g.save();g.globalAlpha*=Math.max(talk,smile);oval(p,303,my+14,14*Math.max(talk,smile),5,"#b95c68");g.restore();
    });
    if(!student && (o.tear??-1)>=0){
      const u=unit(o.tear),x=425-10*u,y=248+122*u;
      g.beginPath();g.moveTo(x,y-21);g.bezierCurveTo(x-19,y+3,x-14,y+18,x,y+18);g.bezierCurveTo(x+17,y+18,x+18,y+3,x,y-21);g.fillStyle="#73bede";g.fill();g.strokeStyle=INK;g.lineWidth=3;g.stroke();
    }
    if (!student) {
      for (const side of [-1, 1]) {
        const ex = 300 + side * 53, lens = handEllPts(ex, ey, 38, 34);
        shape(p, lens, null, 4.5);
        // A finite moving diagonal is clipped to each lens, never a pupil dot.
        const u = unit(o.gleam), gx = ex - 55 + u * 110;
        g.save(); g.globalAlpha *= Math.sin(u * Math.PI) ** 2;
        p.clip(lens, () => {
          p.stroke([[gx - 13, ey - 29], [gx + 13, ey + 19]], 9, "#ffffff");
          p.stroke([[gx + 2, ey - 27], [gx + 10, ey - 12]], 2, "#cfdae4");
        }); g.restore();
      }
      curve(p, [285, ey - 4], [300, ey - 15], [315, ey - 4], 4.5, INK);
      p.stroke([[209, ey - 7], [176, ey - 20]], 4, INK);
      p.stroke([[391, ey - 7], [424, ey - 20]], 4, INK);
    } else {
      g.save(); g.globalAlpha *= stress;
      g.beginPath(); g.moveTo(409, 269); g.quadraticCurveTo(434, 301, 412, 317);
      g.quadraticCurveTo(387, 309, 409, 269); g.closePath();
      g.fillStyle = "#78b7d3"; g.fill(); g.strokeStyle = INK; g.lineWidth = 4; g.stroke();
      for (let i = 0; i < 3; i++) p.stroke([[183 + i * 10, 264], [181 + i * 10, 280]], 4, INK);
      g.restore();
    }
    g.restore();
    if (!student) {
      const pose = classroomPose(o), h = pose.hands[1];
      const x = 300 + h[0] - pose.head[0], y = 300 + h[1] - pose.head[1];
      const glasses = ease(o.glassesP), chin = ease(o.chinP);
      g.save(); g.globalAlpha *= Math.max(glasses, chin);
      oval(p, x, y, 18, 15, INK);
      curve(p, [x - 2, y - 5], [x - 3, y - 19], [x - 2, y - 36 * glasses - 13 * chin], 10, INK);
      g.restore();
    }
  } finally {g.restore(); p.rot = saved;}
};
