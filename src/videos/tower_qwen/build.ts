// Three sets for "Tower Qwen", all sharing one origin (world.ts toggles them per shot):
//   bridge - the full-size 1952 Tower Bridge over the Thames: two Portland-stone towers at x = +-6.4 with corner
//            turrets, the high-level walkway between them carrying the "TOWER BRIDGE" board, fixed spans out to the
//            embankments, and the two bascule LEAVES as live groups hinged at +-6.4 (rotation.z = +-tilt), plus the
//            red double-decker climbing the rising left leaf, the watchman's stone podium and a cruising tug.
//   cab    - the bus's cutaway driving cab: floor, front bulkhead with the windscreen opening, the header panel with
//            the "6 FT GAP AHEAD" plate hanging from it, dash + steering column, and a brass pedestal carrying a live
//            gauge needle and the vertical throttle lever whose knob world.ts pins under the driver's 2D fist.
//   jump   - the south-bank plaza: paving, lamp posts, the A-frame "SAFE LANDING" chalkboard and, across the water,
//            a 0.42 miniature of the same bridge (leaves parked at 26 deg) that the 3D bus arcs between.
// Every surface goes through shade.ts twoTone; all textures are procedural (paint.ts).
import * as THREE from "three";
import { twoTone } from "./shade";
import { water, stone, asphalt, quay, towerSign, gapSign, chalkBoard, busSide, busEnd, brassPanel, cabPaint } from "./paint";
import { BRIDGE, CAB, SET3, TILT1 } from "./story";

const MATS = new Map<string, THREE.Material>();
const lam = (key: string, make: () => THREE.MeshLambertMaterialParameters) => {
  const hit = MATS.get(key);
  if (hit) return hit as THREE.MeshLambertMaterial;
  const m = twoTone(new THREE.MeshLambertMaterial(make()));
  MATS.set(key, m);
  return m;
};
const lit = (key: string, color: THREE.ColorRepresentation, k = 1, flat = false) =>
  lam(key, () => ({ color: new THREE.Color(color).multiplyScalar(k), flatShading: flat }));

const TEX = new Map<string, THREE.Texture>();
const tx = (key: string, make: () => THREE.Texture) => { let t = TEX.get(key); if (!t) { t = make(); TEX.set(key, t); } return t; };

export type Sets = { root: THREE.Group; sets: Record<string, THREE.Group>; props: Record<string, unknown> };
type V3 = [number, number, number];

// ---------------- primitives ----------------
const mesh = (parent: THREE.Object3D, g: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) => {
  const o = new THREE.Mesh(g, m);
  o.position.set(x, y, z); o.rotation.set(rx, ry, rz);
  o.castShadow = true; o.receiveShadow = true;
  parent.add(o);
  return o;
};
const box = (p: THREE.Object3D, w: number, h: number, d: number, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) =>
  mesh(p, new THREE.BoxGeometry(w, h, d), m, x, y, z, ry, rx, rz);
const cyl = (p: THREE.Object3D, r0: number, r1: number, h: number, m: THREE.Material, x: number, y: number, z: number, seg = 16, rx = 0, ry = 0, rz = 0) =>
  mesh(p, new THREE.CylinderGeometry(r0, r1, h, seg), m, x, y, z, ry, rx, rz);
const plane = (p: THREE.Object3D, w: number, h: number, m: THREE.Material, x: number, y: number, z: number, rx = -Math.PI / 2, ry = 0) =>
  mesh(p, new THREE.PlaneGeometry(w, h), m, x, y, z, ry, rx);
const sph = (p: THREE.Object3D, r: number, x: number, y: number, z: number, m: THREE.Material) => {
  const o = new THREE.Mesh(new THREE.SphereGeometry(r, 12, 8), m);
  o.position.set(x, y, z); o.castShadow = true; o.receiveShadow = true;
  p.add(o);
  return o;
};
const UP = new THREE.Vector3(0, 1, 0);
/** cylinder between two points */
const strut = (p: THREE.Object3D, a: V3, b: V3, r: number, m: THREE.Material, seg = 8) => {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A), L = d.length();
  const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, seg), m);
  o.position.copy(A).addScaledVector(d, 0.5);
  o.quaternion.setFromUnitVectors(UP, d.normalize());
  o.castShadow = true; o.receiveShadow = true;
  p.add(o);
  return o;
};

const M = {
  stone: () => lam("stone", () => ({ map: tx("stone", () => stone([2, 3])) })),
  stoneD: () => lit("stoneD", "#b8ab8c"),
  trim: () => lit("trim", "#efe7d2"),
  road: () => lam("road", () => ({ map: tx("asphalt", () => asphalt([3, 1])) })),
  quay: () => lam("quay", () => ({ map: tx("quay", () => quay([16, 16])) })),
  steel: () => lit("steel", "#5f6c7a"),
  steelPale: () => lit("steelPale", "#93a2b0"),
  brass: () => lam("brass", () => ({ map: tx("brass", () => brassPanel()) })),
  gold: () => lit("gold", "#d9b23c"),
  ink: () => lit("ink", "#241f22"),
  cream: () => lit("cream", "#f2e8d0"),
  red: () => lit("red", "#c0392b"),
  white: () => lit("white", "#f6f4ee"),
  wood: () => lit("wood", "#8a5a34"),
  frame: () => lit("chalkFrame", "#6b4a2c"),
  glass: () => lit("glass", "#31596f"),
};
const BLDG = (i: number) => lit("bldg" + (i % 3), ["#c9bda6", "#aba493", "#d8cdb6"][i % 3]);
const hash = (i: number) => { const v = Math.sin(i * 91.7 + 17.3) * 43758.5453; return v - Math.floor(v); };

/** red/white barrier run along a road edge */
const barriers = (p: THREE.Object3D, x0: number, x1: number, z: number, y: number) => {
  const L = x1 - x0, n = Math.max(2, Math.round(Math.abs(L) / 1.1));
  for (let i = 0; i <= n; i++) {
    const x = x0 + (L * i) / n;
    box(p, 0.09, BRIDGE.barH, 0.09, M.steelPale(), x, y + BRIDGE.barH / 2, z);
  }
  for (let i = 0; i < n; i++) {
    const x = x0 + (L * (i + 0.5)) / n;
    box(p, Math.abs(L) / n - 0.12, 0.1, 0.07, i % 2 ? M.white() : M.red(), x, y + BRIDGE.barH - 0.07, z);
  }
};

const lampPost = (p: THREE.Object3D, x: number, y: number, z: number, s = 1) => {
  cyl(p, 0.07 * s, 0.11 * s, 3.1 * s, M.steel(), x, y + 1.55 * s, z, 8);
  box(p, 0.34 * s, 0.3 * s, 0.34 * s, M.steel(), x, y + 3.15 * s, z);
  const head = sph(p, 0.19 * s, x, y + 3.44 * s, z, lit("lampGlow", "#ffe9a8", 2.6, true));
  head.castShadow = false;
};

// ---------------- the bridge ----------------
export type BridgeParts = { leftLeaf: THREE.Group; rightLeaf: THREE.Group };

/** one Gothic tower straddling the carriageway: two legs, a portal, corner turrets and capped crowns */
const tower = (p: THREE.Object3D, tx0: number, detail: boolean) => {
  const g = new THREE.Group(); g.position.x = tx0; p.add(g);
  const h = BRIDGE.towerH, w = BRIDGE.towerW, lz = BRIDGE.legZ;
  box(g, w + 1.4, 2.4, lz * 2 + 1.4, M.stoneD(), 0, 0.5, 0);                    // the pier it stands on
  for (const s of [-1, 1]) {
    box(g, w, h - 1.0, 1.4, M.stone(), 0, 1.0 + (h - 1.0) / 2, s * lz);
    if (detail) {
      for (let i = 0; i < 4; i++) box(g, 0.3, 1.2, 0.14, M.glass(), 0, 3.7 + i * 2.05, s * (lz + 0.7));
      box(g, w + 0.3, 0.34, 1.7, M.trim(), 0, 6.9, s * lz);
      box(g, w + 0.34, 0.4, 1.84, M.trim(), 0, 10.55, s * lz);
    }
    for (const zs of [-1, 1]) {                                                 // corner turrets
      const cx = (w / 2 - 0.3) * zs, cz = s * (lz + 0.6);
      cyl(g, 0.5, 0.56, 2.8, M.stone(), cx, 11.4, cz, 10);
      mesh(g, new THREE.ConeGeometry(0.68, 1.6, 10), M.stoneD(), cx, 13.6, cz);
      if (detail) cyl(g, 0.07, 0.07, 0.8, M.gold(), cx, 14.7, cz, 6);
    }
  }
  box(g, w + 0.2, 1.6, lz * 2 + 1.4, M.stone(), 0, h - 0.5, 0);                 // portal lintel over the road
  if (detail) {
    for (const s of [-1, 1]) box(g, w, 0.9, 0.24, M.trim(), 0, 2.7, s * (BRIDGE.roadW / 2 + 0.4));
    for (const s of [-1, 1]) box(g, 0.24, 3.2, 0.2, M.glass(), 0, 4.8, s * (lz + 0.72));
  }
  return g;
};

/** one bascule leaf, built in leaf-local space from the hinge (x 0) toward its tip and posed by rotation.z */
const leaf = (p: THREE.Object3D, side: 1 | -1, detail: boolean) => {
  const g = new THREE.Group(); g.position.set(side * BRIDGE.hinge, BRIDGE.deckY, 0); p.add(g);
  const L = BRIDGE.leafL, W = BRIDGE.roadW, f = -side;                          // the left leaf grows toward +x
  const cx = (f * L) / 2;
  box(g, L, 0.55, W + 0.6, M.stoneD(), cx, -0.3, 0);
  plane(g, L, W + 0.3, M.road(), cx, 0.01, 0);
  if (detail) {
    for (const s of [-1, 1]) {
      box(g, L - 0.5, 0.4, 0.26, M.steel(), cx, -0.74, s * (W / 2 - 0.1));
      box(g, 0.32, 0.72, W + 0.5, M.steel(), f * L * 0.36, -0.78, 0);
      box(g, 0.32, 0.72, W + 0.5, M.steel(), f * L * 0.74, -0.78, 0);
      barriers(g, Math.min(0, f * L), Math.max(0, f * L), s * (W / 2 + 0.28), 0);
    }
    box(g, 0.36, 0.36, W + 0.6, M.steelPale(), f * (L - 0.14), 0.17, 0);        // the tip lip the bus noses against
    box(g, 0.22, 0.5, W + 0.6, M.steel(), f * 0.16, -0.5, 0);
  }
  return g;
};

/** the bridge structure itself, bridge-local: road along x, river centre x = 0, water surface y = 0 */
const addBridge = (parent: THREE.Object3D, detail: boolean): BridgeParts => {
  const g = new THREE.Group(); parent.add(g);
  for (const s of [-1, 1]) tower(g, s * BRIDGE.hinge, detail);
  const wy0 = BRIDGE.walkY0, wy1 = BRIDGE.walkY1;
  box(g, BRIDGE.hinge * 2 + 1.0, wy1 - wy0, 3.0, M.stone(), 0, (wy0 + wy1) / 2, 0);
  box(g, BRIDGE.hinge * 2 + 1.0, 0.22, 3.3, M.trim(), 0, wy0 - 0.12, 0);
  box(g, BRIDGE.hinge * 2 + 1.0, 0.22, 3.3, M.trim(), 0, wy1 + 0.12, 0);
  if (detail) {
    for (let i = -2; i <= 2; i++) box(g, 0.22, wy1 - wy0 - 0.3, 0.22, M.stoneD(), i * 2.6, (wy0 + wy1) / 2, 1.53);
    const sign = plane(g, BRIDGE.signW, BRIDGE.signH, lam("towerSign", () => ({ map: tx("towerSign", towerSign) })), 0, BRIDGE.signY, BRIDGE.signZ + 0.04, 0);
    sign.castShadow = false;
  }
  const leftLeaf = leaf(g, -1, detail), rightLeaf = leaf(g, 1, detail);
  for (const s of [-1, 1]) {
    const x0 = s * (BRIDGE.hinge + BRIDGE.towerW / 2), x1 = s * 22, w = Math.abs(x1 - x0);
    box(g, w, 0.8, BRIDGE.roadW + 1.8, M.stoneD(), (x0 + x1) / 2, BRIDGE.deckY - 0.45, 0);
    plane(g, w, BRIDGE.roadW, M.road(), (x0 + x1) / 2, BRIDGE.deckY + 0.01, 0);
    plane(g, w, 1.5, M.quay(), (x0 + x1) / 2, BRIDGE.deckY + 0.02, s * (BRIDGE.roadW / 2 + 1.0));
    box(g, 1.9, BRIDGE.deckY + 1.4, BRIDGE.roadW + 2.8, M.stone(), s * 22.8, (BRIDGE.deckY + 1.4) / 2 - 0.7, 0);
    if (detail) {
      barriers(g, Math.min(x0, x1), Math.max(x0, x1), BRIDGE.roadW / 2 + 0.3, BRIDGE.deckY);
      barriers(g, Math.min(x0, x1), Math.max(x0, x1), -(BRIDGE.roadW / 2 + 0.3), BRIDGE.deckY);
      for (let i = 0; i < 4; i++) lampPost(g, s * (10.5 + i * 4), BRIDGE.deckY + 0.02, BRIDGE.roadW / 2 + 1.6, 0.85);
      for (let i = 0; i < 3; i++) box(g, 0.9, 1.2, 0.9, M.stoneD(), s * (13 + i * 3.6), BRIDGE.deckY + 0.6, -(BRIDGE.roadW / 2 + 1.0));
    }
  }
  return { leftLeaf, rightLeaf };
};

/** the north and south embankments with a skyline, the river plate between them, and a few moored boats */
const addBanks = (parent: THREE.Object3D, waterKey: string): { river: THREE.Mesh } => {
  const g = new THREE.Group(); parent.add(g);
  const river = plane(g, 60, 520, lam("water" + waterKey, () => ({ map: tx("water" + waterKey, () => water([34, 34])) })), 0, -0.02, -60);
  river.castShadow = false;
  for (const s of [-1, 1]) {
    box(g, 3.2, 3.6, 520, M.stoneD(), s * 23.6, 0.1, -60);                  // the quay wall down to the water
    plane(g, 220, 520, M.quay(), s * 134, 1.84, -60);                       // the embankment road behind it
    for (let i = 0; i < 14; i++) {
      const z = -210 + i * 30 + hash(i + s * 3) * 8, h = 7 + hash(i * 3 + s) * 15;
      const bx = s * (37 + hash(i * 5) * 12);
      box(g, 9 + hash(i) * 5, h, 13, BLDG(i), bx, h / 2, z);
      box(g, 5, h * 0.55, 8, BLDG(i + 1), bx + s * 3, h * 0.7, z + 9);
      for (let k = 0; k < 4; k++) box(g, 0.2, 1.4, 0.7, M.glass(), bx - s * (4.6 + hash(i) * 2.5), 3.2 + k * 2.9, z - 3 + k * 2.2);
      box(g, 9 + hash(i) * 5, 0.5, 13, M.stoneD(), bx, h + 0.25, z);
    }
    for (let i = 0; i < 5; i++) lampPost(g, s * 25.6, 1.84, -60 + i * 26, 0.9);
  }
  // two barges moored off the towers
  for (const [x, z, r] of [[-15, 16, 0.3], [14.5, -22, -0.5]] as const) {
    const b = new THREE.Group(); b.position.set(x, 0, z); b.rotation.y = r; g.add(b);
    box(b, 7, 0.9, 2.4, lit("barge", "#4a3b34"), 0, 0.35, 0);
    box(b, 2.2, 1.2, 2.0, M.cream(), -1.8, 1.3, 0);
  }
  return { river };
};

// ---------------- the bus ----------------
/** a red RT-style double-decker, origin at ground contact, nose along +x */
export const addBus = (parent: THREE.Object3D, tag: string): THREE.Group => {
  const g = new THREE.Group(); g.name = tag; parent.add(g);
  const { len: L, wide: W, tall: H } = BRIDGE.bus;
  const side = lam("busSide_" + tag, () => ({ map: tx("busSide_" + tag, busSide) }));
  const front = lam("busFront_" + tag, () => ({ map: tx("busFront_" + tag, () => busEnd(false)) }));
  const rear = lam("busRear_" + tag, () => ({ map: tx("busRear_" + tag, () => busEnd(true)) }));
  const skirt = lit("busSkirt_" + tag, "#9c1f1f");
  const y0 = 0.36, bodyH = H - y0;
  const body = new THREE.Mesh(new THREE.BoxGeometry(L, bodyH, W), [front, rear, skirt, skirt, side, side] as THREE.Material[]);
  body.position.set(0, y0 + bodyH / 2, 0);
  body.castShadow = true; body.receiveShadow = true;
  g.add(body);
  box(g, L + 0.08, 0.14, W + 0.1, M.cream(), 0, H + 0.05, 0);                 // upper roof
  for (const s of [-1, 1]) box(g, 0.1, 0.16, W + 0.14, M.cream(), s * (L / 2 - 0.34), y0 + bodyH * 0.5, 0);
  box(g, 0.34, 0.26, W * 0.92, M.steel(), L / 2 - 0.06, 0.46, 0);             // front bumper
  box(g, 0.3, 0.24, W * 0.92, M.steel(), -(L / 2 - 0.06), 0.5, 0);            // rear bumper
  for (const s of [-1, 1]) {
    for (const xw of [-1, 1]) {
      cyl(g, 0.27, 0.27, 0.22, M.ink(), xw * (L / 2 - 0.46), 0.27, s * (W / 2 - 0.08), 12, Math.PI / 2);
      cyl(g, 0.1, 0.1, 0.24, M.steelPale(), xw * (L / 2 - 0.46), 0.27, s * (W / 2 - 0.02), 8, Math.PI / 2);
    }
    box(g, 0.14, 0.44, 0.09, M.steel(), L / 2 + 0.03, H * 0.62, s * (W / 2 - 0.08));   // mirrors
  }
  return g;
};

// ---------------- shot 1 ----------------
const setBridge = (g: THREE.Group): Record<string, unknown> => {
  const props: Record<string, unknown> = {};
  props.river1 = addBanks(g, "A").river;
  const { leftLeaf, rightLeaf } = addBridge(g, true);
  props.leftLeaf = leftLeaf; props.rightLeaf = rightLeaf;
  // the watchman's signal podium: a stone pier standing in the river just ahead of the span, railed, with a
  // bollard, a red flag and a crate of lamp oil
  const pod = new THREE.Group(); pod.position.set(...[1.9, 0, 5.5] as V3); g.add(pod);
  cyl(pod, 1.45, 1.95, 1.95, M.stoneD(), 0, 0.98, 0, 12);
  cyl(pod, 1.62, 1.62, 0.22, M.trim(), 0, 1.93, 0, 12);
  for (let i = 0; i < 11; i++) {
    const a = (i / 11) * Math.PI * 2;
    cyl(pod, 0.06, 0.06, 0.62, M.steelPale(), Math.cos(a) * 1.3, 2.34, Math.sin(a) * 1.3, 6);
  }
  const rail = new THREE.Mesh(new THREE.TorusGeometry(1.3, 0.055, 6, 22), M.steelPale());
  rail.rotation.x = Math.PI / 2; rail.position.y = 2.6; rail.castShadow = true;
  pod.add(rail);
  cyl(pod, 0.17, 0.14, 0.3, M.ink(), -0.95, 2.12, 0.3, 8);
  sph(pod, 0.11, -0.95, 2.3, 0.3, M.steelPale());
  box(pod, 0.7, 0.55, 0.7, M.wood(), 0.9, 2.28, -0.35, 0.5);
  cyl(pod, 0.11, 0.11, 0.4, lit("oil", "#c9962a"), 0.9, 2.6, -0.35, 8);
  // a tug puttering down the river (posed by world.ts) and a pair of buoys
  const tug = new THREE.Group(); g.add(tug);
  box(tug, 4.4, 0.85, 1.6, lit("tugHull", "#3a2b26"), 0, 0.36, 0);
  box(tug, 1.7, 1.05, 1.25, M.cream(), -0.5, 1.25, 0);
  cyl(tug, 0.22, 0.27, 1.5, M.ink(), 0.55, 2.0, 0, 10);
  box(tug, 0.45, 0.45, 0.45, M.brass(), -0.5, 2.1, 0);
  props.tug = tug;
  for (const [x, z] of [[-10, 9], [11, 7.5], [-4, 13]] as const) {
    const b = sph(g, 0.24, x, 0.1, z, M.red());
    b.castShadow = false;
  }
  props.bus1 = addBus(g, "main");
  return props;
};

// ---------------- shot 2 ----------------
const setCab = (g: THREE.Group): Record<string, unknown> => {
  const props: Record<string, unknown> = {};
  const floor = lam("cabFloor", () => ({ map: tx("cabPaint", cabPaint) }));
  box(g, 3.5, 0.18, 3.6, M.steel(), 0, -0.1, 0.85);
  plane(g, 3.4, 3.4, floor, 0, 0.005, 0.85);
  // the front bulkhead, cut around the windscreen
  const bz = CAB.winZ, wy0 = CAB.winY0, wy1 = CAB.winY1, whw = CAB.winHalfW, top = 2.95;
  box(g, 3.5, wy0, 0.24, M.cream(), 0, wy0 / 2, bz);
  box(g, 3.5, top - wy1, 0.24, M.cream(), 0, (top + wy1) / 2, bz);
  for (const s of [-1, 1]) box(g, 1.75 - whw, wy1 - wy0, 0.24, M.cream(), s * (whw + (1.75 - whw) / 2), (wy0 + wy1) / 2, bz);
  box(g, 2 * whw + 0.24, 0.12, 0.34, M.steel(), 0, wy1 + 0.06, bz);
  box(g, 2 * whw + 0.24, 0.1, 0.1, M.brass(), 0, wy0 - 0.05, bz + 0.16);
  // "6 FT GAP AHEAD" bolted to the windscreen header
  const sign = plane(g, CAB.signW, CAB.signH, lam("gapSign", () => ({ map: tx("gapSign", gapSign) })), CAB.sign[0], CAB.sign[1], CAB.sign[2], 0);
  sign.receiveShadow = false;
  props.gapSign = sign;
  // dash and binnacle; no steering wheel - it sat exactly on the pinned fist and swallowed the throttle action
  box(g, 2.1, 0.46, 0.62, lit("dash", "#4a3b32"), -0.1, 1.0, bz + 0.44);
  box(g, 0.52, 0.18, 0.5, M.brass(), -0.42, 1.3, bz + 0.5);
  box(g, 0.34, 0.3, 0.34, M.steel(), -0.42, 0.62, bz + 0.34);
  // the brass pedestal: box, dial face, a needle that lives off leverP, and the vertical throttle the fist owns
  box(g, 0.52, 0.52, 0.52, M.brass(), CAB.boxTop[0], 0.26, CAB.boxTop[2]);
  box(g, 0.6, 0.09, 0.6, lit("pedTop", "#a87c1e"), CAB.boxTop[0], CAB.boxTop[1] + 0.02, CAB.boxTop[2]);
  // the dial goes on the pedestal's front face, low: on the top plate it sat exactly under the pinned fist
  cyl(g, 0.13, 0.13, 0.05, M.cream(), CAB.boxTop[0], 0.3, CAB.boxTop[2] + 0.27, 16, Math.PI / 2);
  cyl(g, 0.15, 0.15, 0.04, M.ink(), CAB.boxTop[0], 0.3, CAB.boxTop[2] + 0.25, 16, Math.PI / 2);
  const needle = new THREE.Group();
  needle.position.set(CAB.boxTop[0], 0.3, CAB.boxTop[2] + 0.3);
  g.add(needle);
  box(needle, 0.02, 0.11, 0.02, M.ink(), 0, 0.055, 0);
  props.needle = needle;
  const pivot = new THREE.Group();
  pivot.position.set(...CAB.boxTop);
  g.add(pivot);
  cyl(pivot, 0.05, 0.062, 0.11, M.ink(), 0, 0.045, 0, 10);                       // the lever's collar
  const shaft = new THREE.Mesh(new THREE.CylinderGeometry(0.026, 0.032, 1, 10), M.steelPale());
  shaft.castShadow = true;
  g.add(shaft);
  const knob = new THREE.Mesh(new THREE.SphereGeometry(0.055, 14, 10), lit("knob", "#f0c445", 1.05));
  knob.castShadow = true;
  g.add(knob);
  props.lever = { pivot, shaft, knob };
  // the cab sides, far enough out to keep the shot reading as a cutaway
  for (const s of [-1, 1]) {
    box(g, 0.18, 2.5, 3.4, M.red(), s * 1.78, 1.25, 0.9);
    box(g, 0.1, 0.62, 0.9, M.glass(), s * 1.7, 1.9, 0.2);
    box(g, 0.12, 0.2, 3.4, M.cream(), s * 1.74, 2.4, 0.9);
  }
  // the world through the windscreen: the same bridge at 0.24, leaves already up, and a stretch of river
  const bg = new THREE.Group();
  bg.position.set(...CAB.bg); bg.scale.setScalar(CAB.bgScale);
  g.add(bg);
  const bgWater = plane(bg, 60, 300, lam("waterB", () => ({ map: tx("waterB", () => water([30, 30])) })), 0, -0.02, -70);
  bgWater.castShadow = false;
  const b = addBridge(bg, false);
  b.leftLeaf.rotation.z = (Math.PI / 180) * TILT1;
  b.rightLeaf.rotation.z = -(Math.PI / 180) * TILT1;
  for (const s of [-1, 1]) {
    box(bg, 3.2, 3.6, 300, M.stoneD(), s * 23.6, 0.1, -80);
    plane(bg, 120, 300, M.quay(), s * 84, 1.84, -80);
    for (let i = 0; i < 7; i++) box(bg, 10, 8 + hash(i * 3 + s) * 10, 12, BLDG(i), s * (40 + hash(i) * 12), 4, -30 - i * 26);
  }
  props.cabBg = { group: bg, water: bgWater };
  return props;
};

// ---------------- shot 3 ----------------
const setJump = (g: THREE.Group): Record<string, unknown> => {
  const props: Record<string, unknown> = {};
  // the plaza the driver stands on, then a low quay wall, then the water the miniature bridge crosses
  plane(g, 60, 34, M.quay(), 0, 0, 9);
  box(g, 60, 0.44, 1.4, M.stoneD(), 0, 0.05, -7.4);
  const river = plane(g, 46, 60, lam("waterC", () => ({ map: tx("waterC", () => water([20, 20])) })), 0, 0.13, -38);
  river.castShadow = false;
  props.river3 = river;
  for (const s of [-1, 1]) {
    box(g, 26, 0.9, 60, M.stoneD(), s * 35, 0.3, -38);
    for (let i = 0; i < 4; i++) box(g, 8, 6 + hash(i * 3 + s) * 7, 9, BLDG(i), s * (17 + i * 9), 3.5, -20 - i * 11);
  }
  const bg = new THREE.Group();
  bg.position.set(...SET3.bg); bg.scale.setScalar(SET3.bgScale);
  g.add(bg);
  const b = addBridge(bg, true);
  b.leftLeaf.rotation.z = (Math.PI / 180) * TILT1;
  b.rightLeaf.rotation.z = -(Math.PI / 180) * TILT1;
  props.bgBridge = bg;
  props.bus3 = addBus(bg, "mini");
  // plaza dressing: lamps, bollards, crates, a coil of rope and two mooring bits
  for (const s of [-1, 1]) lampPost(g, s * 4.6, 0, 8.6, 1);
  for (const x of [-5.2, -3.3, 3.3, 5.2]) cyl(g, 0.13, 0.16, 0.6, M.ink(), x, 0.3, 11.2, 8);
  box(g, 1.2, 0.85, 1.2, M.wood(), 3.4, 0.42, 5.6, 0.4);
  box(g, 1.0, 0.7, 1.0, M.wood(), 4.3, 0.35, 4.6, -0.9);
  box(g, 0.9, 0.6, 0.9, M.wood(), 3.9, 1.1, 5.3, 0.2);
  const coil = new THREE.Mesh(new THREE.TorusGeometry(0.42, 0.09, 6, 18), lit("rope", "#c8a86a"));
  coil.rotation.x = Math.PI / 2; coil.position.set(-3.1, 0.1, 5.2);
  coil.castShadow = true;
  g.add(coil);
  // the A-frame chalkboard: two legs, a raked slate facing the lens, a chalk tray
  const e = new THREE.Group();
  e.position.set(...SET3.easel); g.add(e);
  const W = SET3.boardW, H = SET3.boardH, cy = SET3.boardY;
  for (const s of [-1, 1]) {
    const lx = W / 2 + 0.07;
    strut(e, [s * lx, 0, 0.5], [s * lx, cy - H * 0.3, -0.16], 0.05, M.frame());
    strut(e, [s * lx, 0, -0.52], [s * lx, cy + H * 0.3, -0.12], 0.045, M.frame());
  }
  const board = plane(e, W, H, lam("chalk", () => ({ map: tx("chalk", chalkBoard) })), 0, cy, -0.1, -0.12);
  board.receiveShadow = true;
  plane(e, W, H, lam("chalkBack", () => ({ map: tx("chalkBack", cabPaint) })), 0, cy, 0.16, Math.PI + 0.12);
  box(e, W + 0.14, 0.09, 0.24, M.frame(), 0, cy - H / 2 - 0.06, -0.14);
  sph(e, 0.045, -0.2, cy - H / 2 + 0.02, -0.06, M.white());
  props.board = board;
  return props;
};

// ---------------- assembly ----------------
export const buildSets = (): Sets => {
  const root = new THREE.Group();
  const sets: Record<string, THREE.Group> = {};
  const props: Record<string, unknown> = {};
  for (const [name, build] of [["bridge", setBridge], ["cab", setCab], ["jump", setJump]] as const) {
    const g = new THREE.Group();
    g.name = name;
    Object.assign(props, build(g));
    root.add(g);
    sets[name] = g;
  }
  return { root, sets, props };
};
