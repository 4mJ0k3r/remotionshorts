// Three outdoor sets for "Tower Jump", toggled per shot by world.ts:
//   wide   - Tower Bridge (BR1, scale 1): two Neo-Gothic stone towers at x +-8.5, blue-and-white upper walkways with
//            the "TOWER BRIDGE" sign, suspension chains, two bascule leaves hinged at x +-6.5 (live tilt), the
//            Thames with drifting foam, the far bank skyline, the No. 78 bus, and the watchman's balcony pier.
//   cab    - the driver's cutaway cab on a plank floor: windscreen frame, dashboard, the red control pedestal with
//            the live brass throttle lever (world.ts pins its knob to the driver's 2D fist), the "6 FT GAP AHEAD"
//            sign, and the rising asphalt leaf ahead against the sky.
//   finish - the riverside plaza (pavers, parapet, street lamp, chalkboard easel, bench, bollards) with a smaller,
//            higher copy of the bridge (BR3) whose leaves stay open at 26 / 12 deg for the jump.
import * as THREE from "three";
import { twoTone } from "./shade";
import { asphalt, stone, slate, water, pavers, stripes, hazard, towerSign, gapSign, routeBoard, fleetName, chalkboard, dial, planks } from "./paint";
import { BR, BR1, BR3, BridgeInst, BUS, TILT3_L, TILT3_R, PEDESTAL, LEVER_PIVOT, GAPSIGN, EASEL, LAMP, WATCH, CAMS, V3 } from "./story";

const MATS = new Map<string, THREE.Material>();
export const lam = (key: string, make: () => THREE.MeshLambertMaterialParameters) => {
  const hit = MATS.get(key);
  if (hit) return hit as THREE.MeshLambertMaterial;
  const m = twoTone(new THREE.MeshLambertMaterial(make()));
  MATS.set(key, m);
  return m;
};
export const lit = (key: string, color: THREE.ColorRepresentation, k = 1, flat = false) =>
  lam(key, () => ({ color: new THREE.Color(color).multiplyScalar(k), flatShading: flat }));
const TEX = new Map<string, THREE.Texture>();
const tx = (key: string, make: () => THREE.Texture) => { let t = TEX.get(key); if (!t) { t = make(); TEX.set(key, t); } return t; };
const texMat = (key: string, make: () => THREE.Texture, extra: THREE.MeshLambertMaterialParameters = {}) => lam(key, () => ({ map: tx(key, make), ...extra }));
export const glow = (color: string, k = 1.6) => new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k), toneMapped: true });

export type Sets = { root: THREE.Group; sets: Record<string, THREE.Group>; props: Record<string, unknown> };

// ---------------- primitives ----------------
const mesh = (p: THREE.Object3D, g: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) => {
  const o = new THREE.Mesh(g, m); o.position.set(x, y, z); o.rotation.set(rx, ry, rz);
  o.castShadow = true; o.receiveShadow = true; p.add(o); return o;
};
const box = (p: THREE.Object3D, w: number, h: number, d: number, m: THREE.Material, x: number, y: number, z: number, ry = 0) =>
  mesh(p, new THREE.BoxGeometry(w, h, d), m, x, y, z, ry);
const cyl = (p: THREE.Object3D, r0: number, r1: number, h: number, m: THREE.Material, x: number, y: number, z: number, seg = 16) =>
  mesh(p, new THREE.CylinderGeometry(r0, r1, h, seg), m, x, y, z);
const plane = (p: THREE.Object3D, w: number, h: number, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0) => {
  const o = mesh(p, new THREE.PlaneGeometry(w, h), m, x, y, z, ry, rx); o.castShadow = false; return o;
};
const UP = new THREE.Vector3(0, 1, 0);
export const strut = (p: THREE.Object3D, a: V3, b: V3, r: number, m: THREE.Material, seg = 8) => {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A), L = d.length();
  const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, seg), m);
  o.position.copy(A).addScaledVector(d, 0.5); o.quaternion.setFromUnitVectors(UP, d.normalize());
  o.castShadow = true; o.receiveShadow = true; p.add(o); return o;
};
const hash = (i: number) => { const v = Math.sin(i * 91.7 + 17.3) * 43758.5453; return v - Math.floor(v); };

const stoneM = () => texMat("stoneWin", () => stone("#cdbf9f", true));
const stonePlain = () => texMat("stonePlain", () => stone("#c4b694"));
const slateM = () => texMat("slate", slate);
const goldM = () => lit("gold", "#e6b93a");
const blueM = () => lit("walkBlue", "#7fa7cf");
const whiteM = () => lit("walkWhite", "#eef0ec");

// ---------------- the No. 78 double-decker (front = +x, wheels on local y 0, pivot = mid-wheelbase) ----------------
export const makeBus = () => {
  const g = new THREE.Group();
  const red = lit("busRed", "#d62828"), cream = texMat("fleetName", fleetName), glass = lit("busGlass", "#2b3a55"),
    dark = lit("busDark", "#1d1d22"), hub = lit("busHub", "#9aa0a8");
  const L = BUS.len, W = BUS.width, hw = W / 2;
  box(g, L, 1.65, W, red, 0, 1.18, 0);                 // lower deck
  box(g, L + 0.04, 0.36, W + 0.04, cream, 0, 2.18, 0); // cream band with the fleet name
  box(g, L - 0.15, 1.5, W, red, -0.05, 3.1, 0);        // upper deck
  box(g, L - 0.35, 0.16, W - 0.12, red, -0.05, 3.92, 0);
  box(g, L - 0.15, 0.1, W + 0.02, dark, -0.05, 0.36, 0); // skirt
  for (const s of [-1, 1]) {
    for (let i = 0; i < 5; i++) box(g, 0.85, 0.62, 0.04, glass, -2.3 + i * 1.02, 1.55, s * (hw + 0.01));
    for (let i = 0; i < 6; i++) box(g, 0.78, 0.7, 0.04, glass, -2.45 + i * 0.92, 3.1, s * (hw + 0.01));
    const rb = plane(g, 0.9, 0.22, texMat("route78", routeBoard), 2.15, 3.62, s * (hw + 0.03), s > 0 ? 0 : Math.PI);
    rb.receiveShadow = false;
    for (const x of [-2.0, 2.0]) {
      const w = mesh(g, new THREE.CylinderGeometry(0.5, 0.5, 0.34, 18), dark, x, 0.5, s * (hw - 0.12)); w.rotation.x = Math.PI / 2;
      const hb = mesh(g, new THREE.CylinderGeometry(0.22, 0.22, 0.36, 12), hub, x, 0.5, s * (hw - 0.11)); hb.rotation.x = Math.PI / 2;
    }
  }
  // front: windscreens, route board, radiator, headlights
  box(g, 0.04, 0.7, W - 0.3, glass, L / 2 + 0.01, 1.6, 0);
  box(g, 0.04, 0.7, W - 0.3, glass, L / 2 - 0.06, 3.1, 0);
  const fb = plane(g, 1.5, 0.3, texMat("route78", routeBoard), L / 2 - 0.05, 3.63, 0, Math.PI / 2); fb.receiveShadow = false;
  box(g, 0.06, 0.55, 0.9, dark, L / 2 + 0.02, 0.8, 0);
  for (const s of [-1, 1]) mesh(g, new THREE.SphereGeometry(0.12, 12, 8), glow("#fff3c8", 1.3), L / 2 + 0.02, 0.85, s * 0.78);
  return g;
};

// ---------------- Tower Bridge (bridge-local, water surface at y 0) ----------------
type Bridge = { group: THREE.Group; leafL: THREE.Group; leafR: THREE.Group; foam: THREE.Mesh[] };
const tower = (p: THREE.Object3D, x: number, deckY: number) => {
  const H = deckY + BR.towerAbove, w = BR.towerW, d = BR.towerD;
  box(p, w + 1.0, deckY + 3, d + 1.2, stonePlain(), x, (deckY - 3) / 2, 0);            // pier from the riverbed
  box(p, w, H - deckY, d, stoneM(), x, (H + deckY) / 2, 0);                              // shaft with gothic windows
  box(p, w + 0.3, 0.35, d + 0.3, stonePlain(), x, deckY + 0.2, 0);                       // string courses
  box(p, w + 0.3, 0.35, d + 0.3, stonePlain(), x, H - 0.2, 0);
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {                                  // corner turrets + spires
    const cx = x + sx * (w / 2), cz = sz * (d / 2);
    cyl(p, 0.42, 0.46, H - deckY + 1.4, stonePlain(), cx, (H + deckY + 1.4) / 2, cz, 10);
    mesh(p, new THREE.ConeGeometry(0.55, 2.2, 8), slateM(), cx, H + 2.5, cz);
    mesh(p, new THREE.SphereGeometry(0.14, 10, 8), goldM(), cx, H + 3.65, cz);
  }
  const roof = mesh(p, new THREE.ConeGeometry(Math.hypot(w, d) / 2 * 0.86, 4.2, 4), slateM(), x, H + 2.1, 0); roof.rotation.y = Math.PI / 4;
  roof.scale.set(w / d * 1.2, 1, 1);
  strut(p, [x, H + 4.1, 0], [x, H + 5.4, 0], 0.07, goldM(), 6);
  mesh(p, new THREE.SphereGeometry(0.18, 10, 8), goldM(), x, H + 5.5, 0);
};
const leaf = (side: -1 | 1, deckY: number) => {
  const g = new THREE.Group(); g.position.set(side * BR.hingeX, deckY, 0);
  const inner = new THREE.Group(); g.add(inner);
  const L = BR.leafLen, dir = -side, cx = (dir * L) / 2;
  box(inner, L, 0.5, BR.roadHalf * 2 + 0.3, lit("girder", "#4a5563"), cx, -0.3, 0);
  box(inner, L, 0.4, BR.roadHalf * 2 - 0.4, lit("girderDark", "#323a46"), cx, -0.72, 0);
  const top = plane(inner, L, BR.roadHalf * 2, texMat("asphaltLane", () => asphalt([1, 1]), { polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }), cx, -0.04, 0, 0, -Math.PI / 2);
  top.receiveShadow = true;
  for (const sz of [-1, 1]) {
    box(inner, L, 0.32, 0.12, texMat("barrier", stripes), cx, 0.42, sz * (BR.roadHalf + 0.05));
    for (let i = 0; i <= 6; i++) box(inner, 0.1, 0.55, 0.1, lit("barrierPost", "#e8e6df"), dir * (0.3 + i * (L - 0.6) / 6), 0.25, sz * (BR.roadHalf + 0.05));
  }
  return g;
};
const chain = (p: THREE.Object3D, x0: number, y0: number, x1: number, y1: number, z: number, sag: number) => {
  const c = new THREE.QuadraticBezierCurve3(new THREE.Vector3(x0, y0, z), new THREE.Vector3((x0 + x1) / 2, Math.min(y0, y1) - sag, z), new THREE.Vector3(x1, y1, z));
  mesh(p, new THREE.TubeGeometry(c, 40, 0.22, 8, false), blueM(), 0, 0, 0);
  for (let i = 1; i < 8; i++) { const q = c.getPoint(i / 8); if (q.y > y1 + 0.4) strut(p, [q.x, q.y, z], [q.x, y1, z], 0.05, whiteM(), 5); }
};
const buildBridge = (b: BridgeInst, key: string): Bridge => {
  const g = new THREE.Group(); g.name = "bridge" + key;
  g.position.set(...b.pos); g.scale.setScalar(b.scale);
  const D = b.deckY;
  // the Thames, drifting foam strips, embankments, approach spans
  const w = plane(g, 900, 900, texMat("water", water), 0, 0, -150, 0, -Math.PI / 2); w.receiveShadow = true;
  const foam: THREE.Mesh[] = [];
  const foamM = new THREE.MeshBasicMaterial({ color: new THREE.Color("#e9fbff").multiplyScalar(1.05), transparent: true, opacity: 0.65, depthWrite: false });
  for (let i = 0; i < 14; i++) {
    const f = new THREE.Mesh(new THREE.PlaneGeometry(1.6 + hash(i) * 2.4, 0.16), foamM);
    f.rotation.x = -Math.PI / 2; f.position.set((hash(i + 7) - 0.5) * 22, 0.03, 0); g.add(f); foam.push(f);
  }
  for (const s of [-1, 1]) {
    tower(g, s * BR.towerX, D);
    // approach span to the bank: flat road on stone arches
    const x0 = s * (BR.towerX + BR.towerW / 2), x1 = s * 40, cx = (x0 + x1) / 2, len = Math.abs(x1 - x0);
    box(g, len, 0.6, BR.roadHalf * 2 + 0.6, lit("girder", "#4a5563"), cx, D - 0.3, 0);
    const ap = plane(g, len, BR.roadHalf * 2, texMat("asphaltLane", () => asphalt([1, 1]), { polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }), cx, D + 0.005, 0, 0, -Math.PI / 2);
    ap.receiveShadow = true;
    for (let k = 1; k < 4; k++) box(g, 1.2, D, 3.6, stonePlain(), x0 + s * k * (len / 4), D / 2 - 0.3, 0);
    for (const sz of [-1, 1]) chain(g, s * BR.towerX, D + BR.towerAbove - 2.5, s * 30, D + 1.0, sz * (BR.towerD / 2 - 0.4), 2.5);
    box(g, 60, 3.2, 40, stonePlain(), s * 62, 1.0, -10);                       // embankment
    box(g, 60, 0.4, 40, lit("bankGrass", "#5fae4a"), s * 62, 2.8, -10);
  }
  // upper walkways (blue / white truss) with the "TOWER BRIDGE" sign under the front one
  const wy = D + BR.towerAbove - 4.6, wx = BR.towerX - BR.towerW / 2;
  for (const sz of [-1, 1]) {
    const z = sz * 1.6;
    box(g, wx * 2, 0.3, 1.0, blueM(), 0, wy + 1.3, z); box(g, wx * 2, 0.3, 1.0, blueM(), 0, wy - 0.1, z);
    for (let i = 0; i <= 12; i++) {
      const x = -wx + (i * 2 * wx) / 12;
      strut(g, [x, wy, z], [x, wy + 1.2, z], 0.07, whiteM(), 6);
      if (i < 12) strut(g, [x, wy, z], [x + (2 * wx) / 12, wy + 1.2, z], 0.05, whiteM(), 5);
    }
  }
  for (const x of [-2.6, 2.6]) strut(g, [x, wy - 0.2, 1.9], [x, wy - 0.75, 1.9], 0.04, lit("rod", "#2a2a30"), 5);
  box(g, 7.0, 1.25, 0.12, lit("signBack", "#173a6a"), 0, wy - 1.35, 1.88);
  plane(g, 6.8, 1.12, texMat("towerSign", towerSign), 0, wy - 1.35, 1.95);
  // the two bascule leaves
  const leafL = leaf(-1, D), leafR = leaf(1, D); g.add(leafL, leafR);
  // far bank skyline: low-poly buildings, a dome, trees
  const BC = ["#c9b79a", "#b9a68a", "#d6c8ae", "#a89a86", "#c2b39c"];
  for (let i = 0; i < 34; i++) {
    const x = -120 + i * 7.2 + hash(i) * 3, h = 6 + hash(i + 3) * 16;
    box(g, 5 + hash(i + 5) * 3, h, 6, lit("bld" + (i % 5), BC[i % 5]), x, h / 2 + 2.8, -70 - hash(i + 9) * 18);
  }
  cyl(g, 6, 6, 8, lit("bld0", BC[0]), -34, 10, -92, 20);
  mesh(g, new THREE.SphereGeometry(6, 20, 12, 0, Math.PI * 2, 0, Math.PI / 2), lit("dome", "#9fb0b8"), -34, 14, -92);
  for (let i = 0; i < 26; i++) {
    const x = (hash(i * 3.3) - 0.5) * 140; if (Math.abs(x) < 18) continue;
    const s = 1.6 + hash(i) * 1.6, c = lit("tree" + (i % 3), ["#3d9a3a", "#58b04a", "#2f8a3a"][i % 3], 1, true);
    cyl(g, 0.15 * s, 0.2 * s, 1.4 * s, lit("trunk", "#7a4a2a"), x, 3.0 + 0.7 * s, -40 - hash(i + 4) * 14, 7);
    mesh(g, new THREE.IcosahedronGeometry(1.1 * s, 0), c, x, 3.0 + 2.0 * s, -40 - hash(i + 4) * 14);
  }
  return { group: g, leafL, leafR, foam };
};

// ---------------- SET wide (shot 1) ----------------
const setWide = (g: THREE.Group, props: Record<string, unknown>) => {
  const br = buildBridge(BR1, "1"); g.add(br.group);
  const bus = makeBus(); br.group.add(bus);
  props.leaves1 = [br.leafL, br.leafR]; props.bus1 = bus; props.foam1 = br.foam;
  // watchman's balcony on its own stone pier in front of the right leaf (top of the boards = y 2.5)
  const [wx, wy, wz] = WATCH;
  box(g, 1.7, wy - 0.12, 1.5, stonePlain(), wx, (wy - 0.12) / 2, wz - 0.1);
  box(g, 2.1, 0.12, 1.8, texMat("balcony", () => planks("#a87648", "#94653c", 6)), wx, wy - 0.06, wz);
  const rail = lit("railWood", "#7a4a2a");
  for (const [x0, z0, x1, z1] of [[-1.0, -0.85, 1.0, -0.85], [-1.0, -0.85, -1.0, 0.85], [1.0, -0.85, 1.0, 0.85]] as const) {
    strut(g, [wx + x0, wy + 1.0, wz + z0], [wx + x1, wy + 1.0, wz + z1], 0.05, rail, 6);
    strut(g, [wx + x0, wy + 0.5, wz + z0], [wx + x1, wy + 0.5, wz + z1], 0.035, rail, 6);
  }
  for (const [x, z] of [[-1, -0.85], [1, -0.85], [-1, 0.85], [1, 0.85], [0, -0.85]] as const) box(g, 0.08, 1.05, 0.08, rail, wx + x, wy + 0.5, wz + z);
  // a little control hut with a lamp at the back of the balcony
  box(g, 0.9, 1.6, 0.5, lit("hut", "#2f5b3a"), wx - 0.4, wy + 0.8, wz - 0.65);
  box(g, 0.5, 0.4, 0.04, lit("hutWin", "#e9dfb0"), wx - 0.4, wy + 1.2, wz - 0.39);
};

// ---------------- SET cab (shot 2) ----------------
const setCab = (g: THREE.Group, props: Record<string, unknown>) => {
  const floorM = texMat("cabFloor", () => planks("#8a5e3a", "#76502f", 10, [1, 1]));
  box(g, 6.0, 0.14, 6.0, floorM, 0, -0.07, 2.4);
  box(g, 6.0, 0.06, 0.2, lit("brassTrim", "#c9973a"), 0, 0.03, 5.38);
  // cutaway cab: red side wall with a window on the left, windscreen frame + dashboard behind the driver
  const red = lit("busRed", "#d62828"), cream = lit("cabCream", "#efe2bd");
  box(g, 0.14, 2.6, 3.4, red, -2.6, 1.3, 1.6);
  box(g, 0.16, 0.8, 1.6, lit("busGlass", "#2b3a55"), -2.6, 1.65, 1.8);
  box(g, 5.4, 0.18, 0.18, cream, 0, 2.62, 0.05);
  // windscreen posts kept clear of the sign (x -1.05..-0.25) and the driver's head (x 0.13..0.77)
  for (const x of [-2.55, -1.5, 1.5, 2.55]) box(g, 0.14, 2.6, 0.14, cream, x, 1.3, 0.05);
  box(g, 5.4, 0.9, 0.35, red, 0, 0.45, -0.05);
  box(g, 5.4, 0.08, 0.5, cream, 0, 0.93, -0.02);
  for (const x of [-1.8, 1.6]) { const d = plane(g, 0.32, 0.32, texMat("dial", dial), x, 0.62, 0.13); d.receiveShadow = false; }
  // the control pedestal + live throttle lever (pivot hub fixed, shaft/knob aimed by world.ts every frame)
  const [px, , pz] = PEDESTAL;
  box(g, 0.5, 0.5, 0.34, red, px, 0.25, pz);
  box(g, 0.56, 0.05, 0.4, lit("brassTrim", "#c9973a"), px, 0.52, pz);
  plane(g, 0.24, 0.24, texMat("dial", dial), px - 0.08, 0.3, pz + 0.175);
  const brass = lit("brass", "#d9a62e");
  const hub = mesh(g, new THREE.CylinderGeometry(0.06, 0.07, 0.07, 14), goldM(), ...LEVER_PIVOT);
  const shaft = mesh(g, new THREE.CylinderGeometry(0.02, 0.024, 1, 10), brass, 0, 0, 0);
  const knob = mesh(g, new THREE.SphereGeometry(0.045, 16, 12), goldM(), 0, 0, 0);
  props.lever = { hub, shaft, knob };
  // "6 FT GAP AHEAD" hangs from the windscreen header on two hazard-striped hangers, high and left of the driver's
  // head, so it stays whole in both the opening medium shot and the close-up (no post crossing the pedestal)
  const [sx, , sz] = GAPSIGN, c0 = CAMS[2][1].s(194).pos, ry = Math.atan2(c0[0] - sx, c0[2] - sz);
  const sg = new THREE.Group(); sg.position.set(sx, 0, sz); sg.rotation.y = ry; g.add(sg);
  for (const x of [-0.24, 0.24]) box(sg, 0.05, 0.36, 0.05, texMat("hazard", hazard), x, 2.5, -0.02);
  box(sg, 0.68, 0.48, 0.05, lit("signBackY", "#2a2226"), 0, 2.18, -0.03);
  plane(sg, 0.64, 0.45, texMat("gapSign", gapSign), 0, 2.18, 0.0);
  // the leaf ahead, already rising: tilted asphalt with barriers, the far tower and the river below
  const ramp = new THREE.Group(); ramp.position.set(0, -0.6, -1.2); ramp.rotation.x = 0.33; g.add(ramp);
  // 26 m long along -z (texture u = along the road, so the lane dashes run away from the lens)
  const rt = plane(ramp, 26, 5.6, texMat("asphaltRamp", () => asphalt([1, 1])), 0, 0.005, -13);
  rt.rotation.set(-Math.PI / 2, 0, Math.PI / 2); rt.receiveShadow = true;
  for (const sx2 of [-1, 1]) box(ramp, 0.14, 0.4, 26, texMat("barrier", stripes), sx2 * 2.85, 0.2, -13);
  box(ramp, 5.8, 0.6, 26, lit("girder", "#4a5563"), 0, -0.32, -13);
  const far = new THREE.Group(); far.position.set(-9, -6, -60); g.add(far); tower(far, 0, 2.8);
  const w = plane(g, 600, 600, texMat("water", water), 0, -14, -120, 0, -Math.PI / 2); w.receiveShadow = false;
};

// ---------------- SET finish (shot 3) ----------------
const setFinish = (g: THREE.Group, props: Record<string, unknown>) => {
  box(g, 60, 0.4, 24, texMat("pavers", () => pavers([16, 7])), 0, -0.2, 10);
  box(g, 60, 0.8, 0.5, stonePlain(), 0, 0.4, -2.0);                       // embankment parapet
  box(g, 60, 0.1, 0.62, lit("coping", "#d9cfb8"), 0, 0.85, -2.0);
  box(g, 60, 1.6, 1.2, stonePlain(), 0, -1.0, -2.6);
  const br = buildBridge(BR3, "3"); g.add(br.group);
  br.leafL.rotation.z = TILT3_L; br.leafR.rotation.z = -TILT3_R;
  const bus = makeBus(); br.group.add(bus);
  props.bus3 = bus; props.foam3 = br.foam;
  // black-and-white London street lamp
  const [lx, , lz] = LAMP, blk = lit("lampBlack", "#1d1d22");
  cyl(g, 0.16, 0.2, 0.5, blk, lx, 0.25, lz, 12);
  cyl(g, 0.06, 0.08, 3.0, blk, lx, 1.9, lz, 10);
  for (let i = 0; i < 3; i++) cyl(g, 0.1, 0.1, 0.06, lit("lampWhite", "#f4f1ea"), lx, 0.9 + i * 0.9, lz, 10);
  box(g, 0.42, 0.5, 0.42, glow("#fff2c4", 1.25), lx, 3.65, lz);
  mesh(g, new THREE.ConeGeometry(0.36, 0.3, 4), blk, lx, 4.05, lz).rotation.y = Math.PI / 4;
  // chalkboard A-frame easel turned to the medium-shot camera
  const [ex, , ez] = EASEL, c1 = CAMS[3][1].s(268).pos, ery = Math.atan2(c1[0] - ex, c1[2] - ez);
  const easel = new THREE.Group(); easel.position.set(ex, 0, ez); easel.rotation.y = ery; g.add(easel);
  const ew = lit("easelWood", "#b47a44");
  for (const s of [-1, 1]) strut(easel, [s * 0.38, 0, 0.16], [s * 0.2, 1.85, 0.0], 0.03, ew, 6);
  strut(easel, [0, 0, -0.55], [0, 1.78, -0.04], 0.028, ew, 6);
  box(easel, 0.9, 0.05, 0.1, ew, 0, 1.0, 0.1);
  const bd = new THREE.Group(); bd.position.set(0, 1.38, 0.1); bd.rotation.x = -0.08; easel.add(bd);
  box(bd, 0.84, 0.7, 0.04, lit("boardBack", "#5a3a22"), 0, 0, -0.025);
  plane(bd, 0.8, 0.667, texMat("chalk", chalkboard), 0, 0, 0.0);
  // a bench and bollards on the plaza
  box(g, 1.6, 0.08, 0.45, lit("benchWood", "#8a5a34"), -3.4, 0.45, 0.6);
  for (const x of [-4.1, -2.7]) box(g, 0.08, 0.45, 0.45, blk, x, 0.22, 0.6);
  for (const x of [-5.5, 3.6, 5.2]) { cyl(g, 0.12, 0.14, 0.75, blk, x, 0.38, 0.0, 10); mesh(g, new THREE.SphereGeometry(0.13, 10, 8), blk, x, 0.78, 0.0); }
};

export const buildSets = (): Sets => {
  const root = new THREE.Group(), sets: Record<string, THREE.Group> = {}, props: Record<string, unknown> = {};
  for (const [name, fn] of [["wide", setWide], ["cab", setCab], ["finish", setFinish]] as const) {
    const g = new THREE.Group(); g.name = name; fn(g, props); sets[name] = g; root.add(g);
  }
  props.waterTex = TEX.get("water");
  return { root, sets, props };
};
