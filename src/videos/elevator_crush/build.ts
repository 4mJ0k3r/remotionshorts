// 3D sets for ElevatorCrushShort (SKILL.md Section 4 & Hard Rule 8). Two strictly isolated THREE.Groups:
//  SET_CORRIDOR_LIFT  (shot 2)        : lift cabin with OPEN sliding doors looking out into the coaching-centre corridor,
//                                       whose far wall holds a big rain-streaked monsoon window (animated texture).
//  SET_ELEVATOR_CABIN (shots 1, 3-11) : brushed-steel + warm-wood cabin (4.6 w x 3.8 h, front doors wall at z = -1.8),
//                                       red LED "FLOOR 4 / STUCK" indicator at y = 2.95, brushed-brass control panel with
//                                       floor buttons 4,3,2,1,G,FAN (the FAN knob is pinned to the hero's fist, Rule B),
//                                       ceiling light panels and an openable cable-shaft grate revealing hoist cables.
// Clean architecture only — no easels / poster boards (Rule 6). Cut-away: the camera side is open and the side walls,
// floor and ceiling run past the cameras (z = 5.6) so set edges never show.
import * as THREE from "three";
import { twoTone } from "./shade";
import {
  tex, makeSteelTexture, makeWoodTrimTexture, makeBrassTexture, makeRainWindowTexture,
  makeLEDTexture, makePanelLabelTexture, makeCableTexture,
} from "./paint";

export const CAB = { W: 4.6, H: 3.8, FRONT_Z: -1.8, WALL_FACE_Z: -1.72, BACK_Z: 5.6 };
export const HATCH = { x0: -0.5, x1: 0.5, z0: 0.1, z1: 0.9 };
export const PANEL = { w: 0.34, h: 0.95, btnX: 0.07, rowY: (i: number) => 0.95 * (0.5 - (48 + 78 * i) / 512) };
export const KNOB_ROW = 5; // "FAN" row = the pinned knob

export type CabinRefs = {
  root: THREE.Group;
  doorL: THREE.Mesh;
  doorR: THREE.Mesh;
  led: { tex: THREE.CanvasTexture; redraw: (text: string, flash: boolean) => void; last: string };
  ceilLights: THREE.MeshBasicMaterial[];
  emLamp: THREE.MeshBasicMaterial;
  panel: THREE.Group;
  buttons: THREE.MeshBasicMaterial[];
  knob: THREE.Mesh;
  stem: THREE.Mesh;
  hatch: THREE.Group;
  cables: THREE.Mesh[];
  shaft: THREE.Group;
  rainTex?: THREE.CanvasTexture;
};

export type WorldSets = { cabin: CabinRefs; corridor: CabinRefs };

const box = (w: number, h: number, d: number, m: THREE.Material, x: number, y: number, z: number, parent: THREE.Object3D) => {
  const me = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  me.position.set(x, y, z);
  me.receiveShadow = true;
  parent.add(me);
  return me;
};

const makeFloorSign = () => tex(512, 160, (g, w, h) => {
  g.fillStyle = "#1f4f5c";
  g.fillRect(0, 0, w, h);
  g.strokeStyle = "#f2e2b8";
  g.lineWidth = 8;
  g.strokeRect(10, 10, w - 20, h - 20);
  g.fillStyle = "#f2e2b8";
  g.textAlign = "center";
  g.textBaseline = "middle";
  g.font = "900 64px 'Arial Black', sans-serif";
  g.fillText("FLOOR 4", w / 2, h / 2 - 18);
  g.font = "900 30px 'Arial Black', sans-serif";
  g.fillText("COACHING CLASSES", w / 2, h / 2 + 38);
});

function buildCabin(kind: "cabin" | "corridor"): CabinRefs {
  const root = new THREE.Group();
  root.name = kind === "cabin" ? "SET_ELEVATOR_CABIN" : "SET_CORRIDOR_LIFT";

  const steelTex = makeSteelTexture();
  steelTex.repeat.set(2, 1);
  const woodTex = makeWoodTrimTexture();
  const brassTex = makeBrassTexture();
  const cableTex = makeCableTexture();

  const steel = twoTone(new THREE.MeshLambertMaterial({ map: steelTex, color: "#d8dde2" }));
  const steelDark = twoTone(new THREE.MeshLambertMaterial({ color: "#6c7178" }));
  const doorMat = twoTone(new THREE.MeshLambertMaterial({ map: steelTex, color: "#e6eaee" }));
  const wood = twoTone(new THREE.MeshLambertMaterial({ map: woodTex }));
  const floorMat = twoTone(new THREE.MeshLambertMaterial({ map: woodTex, color: "#a07e62" }));
  const brass = twoTone(new THREE.MeshLambertMaterial({ map: brassTex }));
  const ceilMat = twoTone(new THREE.MeshLambertMaterial({ color: "#cfc6b8" }));
  const shaftMat = twoTone(new THREE.MeshLambertMaterial({ color: "#5a5560" }));
  const cableMat = twoTone(new THREE.MeshLambertMaterial({ map: cableTex }));

  const { W, H, FRONT_Z, BACK_Z } = CAB;
  const len = BACK_Z - FRONT_Z;
  const midZ = (BACK_Z + FRONT_Z) / 2;

  // ---- floor ----
  box(W, 0.1, len, floorMat, 0, -0.05, midZ, root);
  // ---- side walls (steel) with wood wainscot + handrails + panel seams ----
  for (const s of [-1, 1]) {
    box(0.1, H, len, steel, s * (W / 2 + 0.05), H / 2, midZ, root);
    box(0.04, 0.9, len, wood, s * (W / 2 - 0.02), 0.45, midZ, root);
    const rail = new THREE.Mesh(new THREE.CylinderGeometry(0.03, 0.03, len, 10), wood);
    rail.rotation.x = Math.PI / 2;
    rail.position.set(s * (W / 2 - 0.08), 0.98, midZ);
    root.add(rail);
    for (let z = FRONT_Z + 1.1; z < BACK_Z; z += 1.1) box(0.02, H - 0.9, 0.025, steelDark, s * (W / 2 - 0.005), 0.9 + (H - 0.9) / 2, z, root);
    // wood ceiling trim band
    box(0.05, 0.16, len, wood, s * (W / 2 - 0.02), H - 0.08, midZ, root);
  }
  // ---- ceiling with hatch hole ----
  const cy = H + 0.04;
  const { x0, x1, z0, z1 } = HATCH;
  box(x0 + W / 2, 0.08, len, ceilMat, (-W / 2 + x0) / 2, cy, midZ, root);
  box(W / 2 - x1, 0.08, len, ceilMat, (W / 2 + x1) / 2, cy, midZ, root);
  box(x1 - x0, 0.08, z0 - FRONT_Z, ceilMat, 0, cy, (FRONT_Z + z0) / 2, root);
  box(x1 - x0, 0.08, BACK_Z - z1, ceilMat, 0, cy, (BACK_Z + z1) / 2, root);
  // hatch frame (wood)
  box(x1 - x0 + 0.12, 0.05, 0.06, wood, 0, H - 0.01, z0 - 0.03, root);
  box(x1 - x0 + 0.12, 0.05, 0.06, wood, 0, H - 0.01, z1 + 0.03, root);

  // ---- ceiling light panels ----
  const ceilLights: THREE.MeshBasicMaterial[] = [];
  for (const [lx, lz] of [[-1.3, 0.5], [1.3, 0.5], [-1.3, 3.2], [1.3, 3.2]]) {
    const m = new THREE.MeshBasicMaterial({ color: "#fff1d6" });
    const pl = new THREE.Mesh(new THREE.PlaneGeometry(1.2, 1.8), m);
    pl.rotation.x = Math.PI / 2;
    pl.position.set(lx, H - 0.005, lz);
    root.add(pl);
    box(1.3, 0.03, 1.9, wood, lx, H + 0.005, lz, root);
    ceilLights.push(m);
  }

  // ---- front wall with door opening (x -0.85..0.85, y 0..2.45) ----
  const fz = FRONT_Z + 0.015; // wall centre (z -1.85..-1.72)
  box(W / 2 - 0.85, H, 0.13, steel, -(W / 2 + 0.85) / 2, H / 2, fz, root);
  box(W / 2 - 0.85, H, 0.13, steel, (W / 2 + 0.85) / 2, H / 2, fz, root);
  box(1.7, H - 2.45, 0.13, steel, 0, 2.45 + (H - 2.45) / 2, fz, root);
  // wood wainscot on front wall
  box(W / 2 - 0.85, 0.9, 0.03, wood, -(W / 2 + 0.85) / 2, 0.45, CAB.WALL_FACE_Z + 0.01, root);
  box(W / 2 - 0.85, 0.9, 0.03, wood, (W / 2 + 0.85) / 2, 0.45, CAB.WALL_FACE_Z + 0.01, root);
  // door trim (dark steel jambs + head)
  box(0.1, 2.55, 0.17, steelDark, -0.9, 1.275, fz, root);
  box(0.1, 2.55, 0.17, steelDark, 0.9, 1.275, fz, root);
  box(1.9, 0.1, 0.17, steelDark, 0, 2.5, fz, root);
  // threshold
  box(1.7, 0.03, 0.25, steelDark, 0, 0.015, FRONT_Z - 0.05, root);

  // sliding doors (behind the wall face, slide into the pockets)
  const doorGeo = new THREE.BoxGeometry(0.86, 2.45, 0.04);
  const doorL = new THREE.Mesh(doorGeo, doorMat);
  const doorR = new THREE.Mesh(doorGeo, doorMat);
  doorL.position.set(-0.43, 1.225, FRONT_Z - 0.12);
  doorR.position.set(0.43, 1.225, FRONT_Z - 0.12);
  root.add(doorL, doorR);

  // ---- LED indicator above doors ----
  const ledT = makeLEDTexture();
  box(1.12, 0.46, 0.04, steelDark, 0, 2.95, CAB.WALL_FACE_Z + 0.02, root);
  const ledMesh = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.375), new THREE.MeshBasicMaterial({ map: ledT.tex }));
  ledMesh.position.set(0, 2.95, CAB.WALL_FACE_Z + 0.045);
  root.add(ledMesh);

  // ---- emergency lamp (front-left, high) ----
  const emLamp = new THREE.MeshBasicMaterial({ color: "#5a1010" });
  box(0.3, 0.14, 0.06, steelDark, -1.6, 3.3, CAB.WALL_FACE_Z + 0.03, root);
  const em = new THREE.Mesh(new THREE.BoxGeometry(0.24, 0.09, 0.04), emLamp);
  em.position.set(-1.6, 3.3, CAB.WALL_FACE_Z + 0.07);
  root.add(em);

  // ---- brushed-brass control panel (position set by world.ts so the FAN row meets the hero's fist) ----
  const panel = new THREE.Group();
  const plate = new THREE.Mesh(new THREE.BoxGeometry(PANEL.w + 0.06, PANEL.h + 0.06, 0.025), brass);
  panel.add(plate);
  const label = new THREE.Mesh(new THREE.PlaneGeometry(PANEL.w, PANEL.h), new THREE.MeshLambertMaterial({ map: makePanelLabelTexture() }));
  label.position.z = 0.0135;
  panel.add(label);
  const buttons: THREE.MeshBasicMaterial[] = [];
  const btnGeo = new THREE.CylinderGeometry(0.03, 0.03, 0.025, 16);
  for (let i = 0; i < KNOB_ROW; i++) {
    const m = new THREE.MeshBasicMaterial({ color: "#ffd98a" });
    const b = new THREE.Mesh(btnGeo, m);
    b.rotation.x = Math.PI / 2;
    b.position.set(PANEL.btnX, PANEL.rowY(i), 0.02);
    panel.add(b);
    buttons.push(m);
  }
  panel.position.set(1.22, 1.135, CAB.WALL_FACE_Z + 0.0125);
  root.add(panel);
  // pinned FAN knob + stem (world coordinates, placed every frame in world.ts)
  const knob = new THREE.Mesh(new THREE.SphereGeometry(0.03, 16, 12), new THREE.MeshBasicMaterial({ color: "#ffcf56" }));
  const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.014, 0.014, 1, 10), brass);
  root.add(knob, stem);

  // ---- cable shaft above the hatch ----
  const shaft = new THREE.Group();
  shaft.position.y = H;
  root.add(shaft);
  const sw = 1.6, sd = 1.4, sh = 4.0, scz = (z0 + z1) / 2;
  for (const s of [-1, 1]) {
    box(0.05, sh, sd, shaftMat, s * sw / 2, sh / 2, scz, shaft);
    box(sw, sh, 0.05, shaftMat, 0, sh / 2, scz + s * sd / 2, shaft);
  }
  box(sw, 0.05, sd, shaftMat, 0, sh, scz, shaft);
  // guide rails & floor-level marks inside shaft (they slide when the cabin drops)
  for (let y = 0.4; y < sh; y += 0.9) box(sw - 0.1, 0.06, 0.06, steelDark, 0, y, scz - sd / 2 + 0.06, shaft);
  // crosshead + cables belong to the cabin
  box(1.0, 0.16, 0.22, steelDark, 0, H + 0.45, scz, root);
  const cables: THREE.Mesh[] = [];
  for (const cx of [-0.18, 0, 0.18]) {
    const c = new THREE.Mesh(new THREE.CylinderGeometry(0.028, 0.028, 3.4, 10), cableMat);
    c.position.set(cx, H + 0.5 + 1.7, scz);
    root.add(c);
    cables.push(c);
  }

  // ---- hatch grate (hinged on its x0 edge) ----
  const hatch = new THREE.Group();
  hatch.position.set(x0, H - 0.02, scz);
  const hw = x1 - x0, hd = z1 - z0;
  box(hw, 0.035, 0.05, steelDark, hw / 2, 0, -hd / 2 + 0.025, hatch);
  box(hw, 0.035, 0.05, steelDark, hw / 2, 0, hd / 2 - 0.025, hatch);
  box(0.05, 0.035, hd, steelDark, 0.025, 0, 0, hatch);
  box(0.05, 0.035, hd, steelDark, hw - 0.025, 0, 0, hatch);
  for (let i = 1; i < 6; i++) box(0.025, 0.03, hd - 0.05, steelDark, (i * hw) / 6, 0, 0, hatch);
  root.add(hatch);

  // ---- outside the doors: corridor ----
  const wallPaint = twoTone(new THREE.MeshLambertMaterial({ color: kind === "corridor" ? "#7f9fb4" : "#c9a77a" }));
  const corFloor = twoTone(new THREE.MeshLambertMaterial({ color: "#8c8378" }));
  box(7, 0.1, 3.0, corFloor, 0, -0.05, -3.4, root);
  box(7, 3.6, 0.1, wallPaint, 0, 1.8, -4.8, root);
  for (const s of [-1, 1]) box(0.1, 3.6, 3.0, wallPaint, s * 3.0, 1.8, -3.4, root);
  box(7, 0.1, 3.0, ceilMat, 0, 3.4, -3.4, root);
  const corLamp = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.4), new THREE.MeshBasicMaterial({ color: "#ffe9b8" }));
  corLamp.rotation.x = Math.PI / 2;
  corLamp.position.set(0, 3.34, -3.4);
  root.add(corLamp);

  let rainTex: THREE.CanvasTexture | undefined;
  if (kind === "corridor") {
    rainTex = makeRainWindowTexture();
    const win = new THREE.Mesh(new THREE.PlaneGeometry(2.8, 1.9), new THREE.MeshBasicMaterial({ map: rainTex }));
    win.position.set(0, 1.75, -4.74);
    root.add(win);
    const frame = twoTone(new THREE.MeshLambertMaterial({ color: "#e8e2d6" }));
    box(3.0, 0.1, 0.08, frame, 0, 0.75, -4.72, root);
    box(3.0, 0.1, 0.08, frame, 0, 2.75, -4.72, root);
    for (const x of [-1.45, 0, 1.45]) box(0.08, 2.0, 0.08, frame, x, 1.75, -4.72, root);
    box(3.0, 0.06, 0.08, frame, 0, 1.75, -4.72, root);
  } else {
    const sign = new THREE.Mesh(new THREE.PlaneGeometry(1.4, 0.44), new THREE.MeshLambertMaterial({ map: makeFloorSign() }));
    sign.position.set(0, 1.9, -4.74);
    root.add(sign);
  }

  return { root, doorL, doorR, led: { ...ledT, last: "" }, ceilLights, emLamp, panel, buttons, knob, stem, hatch, cables, shaft, rainTex };
}

export function buildSets(): WorldSets {
  return { cabin: buildCabin("cabin"), corridor: buildCabin("corridor") };
}
