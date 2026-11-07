// Three outdoor sets for "Coaster", all sharing one origin (world.ts toggles them per shot), plus a shared land
// group (grass ground, rolling hills, low-poly trees, clouds) that is always on.
//   loop  - elevated work platform (y 3.2) in front of a 7.5 m red steel loop on two A-frame towers. The loop is
//           a live mesh: setBend(0..1) morphs the circle into a kinked, dented polygon.
//   deck  - wooden scaffolding tower with pulley, a curved drop track that runs into the (bent) loop in the
//           background, the red cart that rides it, and the builder's red/cream deck at y 3.0.
//   rival - gleaming white copy of the loop with its top arch hanging from a yellow tower crane, a Ferris wheel,
//           the "FRANK'S LOOP" blueprint easel and a golden winch on a dirt patch.
// Every surface goes through shade.ts twoTone; textures come from paint.ts.
import * as THREE from "three";
import { twoTone } from "./shade";
import { grass, dirt, planks, deckPlanks, concrete, blueprint, banner, crateLabel } from "./paint";
import { LOOP, DECK, RIVAL, V3 } from "./story";

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

export type Sets = { root: THREE.Group; sets: Record<string, THREE.Group>; props: Record<string, unknown> };

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
const cyl = (p: THREE.Object3D, r0: number, r1: number, h: number, m: THREE.Material, x: number, y: number, z: number, seg = 16) =>
  mesh(p, new THREE.CylinderGeometry(r0, r1, h, seg), m, x, y, z);
const UP = new THREE.Vector3(0, 1, 0);
/** cylinder (or square strut) between two points */
const strut = (p: THREE.Object3D, a: V3, b: V3, r: number, m: THREE.Material, seg = 8) => {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A), L = d.length();
  const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, seg), m);
  o.position.copy(A).addScaledVector(d, 0.5);
  o.quaternion.setFromUnitVectors(UP, d.normalize());
  o.castShadow = true; o.receiveShadow = true;
  p.add(o);
  return o;
};
const beamBox = (p: THREE.Object3D, a: V3, b: V3, w: number, m: THREE.Material) => {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A), L = d.length();
  const o = new THREE.Mesh(new THREE.BoxGeometry(w, L, w), m);
  o.position.copy(A).addScaledVector(d, 0.5);
  o.quaternion.setFromUnitVectors(UP, d.normalize());
  o.castShadow = true; o.receiveShadow = true;
  p.add(o);
  return o;
};

const wood = () => lam("wood", () => ({ map: tx("wood", () => planks("#c08850", "#a8723e", 6)) }));
const woodDark = () => lit("woodDark", "#8a5a34");

// ---------------- shared land ----------------
const hash = (i: number) => { const v = Math.sin(i * 91.7 + 17.3) * 43758.5453; return v - Math.floor(v); };
const TREE_G = ["#3d9a3a", "#58b04a", "#2f8a3a", "#6cbf4f", "#469e3c"];
const tree = (p: THREE.Object3D, x: number, y: number, z: number, s: number, seed: number) => {
  const g = new THREE.Group(); g.position.set(x, y, z); g.rotation.y = hash(seed) * 6.28; p.add(g);
  const trunk = lit("trunk", "#7a4a2a");
  const crown = lit("crown" + (seed % TREE_G.length), TREE_G[seed % TREE_G.length], 1, true);
  if (hash(seed + 3) < 0.3) {
    cyl(g, 0.12 * s, 0.18 * s, 1.0 * s, trunk, 0, 0.5 * s, 0, 7);
    mesh(g, new THREE.ConeGeometry(0.95 * s, 1.9 * s, 7), crown, 0, 1.75 * s, 0);
    mesh(g, new THREE.ConeGeometry(0.7 * s, 1.5 * s, 7), crown, 0, 2.6 * s, 0);
  } else {
    cyl(g, 0.13 * s, 0.2 * s, 1.4 * s, trunk, 0, 0.7 * s, 0, 7);
    mesh(g, new THREE.IcosahedronGeometry(1.0 * s, 0), crown, 0, 2.0 * s, 0);
    mesh(g, new THREE.IcosahedronGeometry(0.7 * s, 0), crown, 0.55 * s, 1.7 * s, 0.25 * s);
    mesh(g, new THREE.IcosahedronGeometry(0.62 * s, 0), crown, -0.5 * s, 1.75 * s, -0.2 * s);
  }
  return g;
};
type Hill = [number, number, number, number, number, string];
const HILLS: Hill[] = [
  [-62, -112, 58, 20, 32, "#4da83b"], [12, -150, 78, 27, 36, "#56b043"], [84, -104, 52, 18, 30, "#4aa23a"],
  [-128, -66, 44, 15, 40, "#5ab448"], [134, -58, 46, 14, 40, "#52aa40"], [-30, -74, 30, 10.5, 20, "#5cb848"],
  [42, -78, 36, 11.5, 22, "#4fa83d"], [-90, -160, 60, 26, 30, "#47a038"], [-4, -96, 22, 7.5, 14, "#62bc4c"],
];
const hillY = (h: Hill, x: number, z: number) => {
  const u = 1 - ((x - h[0]) / h[2]) ** 2 - ((z - h[1]) / h[4]) ** 2;
  return u > 0 ? h[3] * Math.sqrt(u) : -1;
};
const land = (g: THREE.Group) => {
  const gm = lam("grass", () => ({ map: tx("grass", () => grass("#4da83b", [90, 90])) }));
  const ground = mesh(g, new THREE.PlaneGeometry(900, 900), gm, 0, 0, -100, 0, -Math.PI / 2);
  ground.castShadow = false;
  for (const h of HILLS) {
    const m = mesh(g, new THREE.SphereGeometry(1, 28, 14, 0, Math.PI * 2, 0, Math.PI / 2), lit("hill" + h[5], h[5]), h[0], -0.2, h[1]);
    m.scale.set(h[2], h[3], h[4]); m.castShadow = false;
    // trees scattered over the hill top
    for (let i = 0; i < 9; i++) {
      const x = h[0] + (hash(i * 13 + h[0]) - 0.5) * h[2] * 1.2, z = h[1] + (hash(i * 7 + h[1]) - 0.5) * h[4] * 1.1;
      const y = hillY(h, x, z);
      if (y > 1) tree(g, x, y - 0.3, z, 3.2 + hash(i + h[2]) * 2.2, i + Math.round(Math.abs(h[0])));
    }
  }
  // tree groves on the flats, kept clear of every camera path and set piece
  let k = 0;
  for (let i = 0; i < 70; i++) {
    const x = (hash(i * 3.1) - 0.5) * 120, z = -28 - hash(i * 5.7) * 50;
    if (Math.abs(x) < 3 && z > -40) continue;
    if (x > 1 && x < 18 && z > -36) continue; // Ferris wheel lot
    tree(g, x, 0, z, 1.6 + hash(i * 1.7) * 1.4, k++);
  }
  for (let i = 0; i < 36; i++) {
    const side = i % 2 ? 1 : -1, x = side * (14 + hash(i * 2.3) * 26), z = 14 - hash(i * 4.1) * 40;
    tree(g, x, 0, z, 1.5 + hash(i * 3.9) * 1.2, k++);
  }
  // clouds: puffy low-poly clusters far behind the hills
  const cm = lit("cloud", "#ffffff", 1.15, true);
  for (let i = 0; i < 9; i++) {
    const cx = -170 + i * 44 + hash(i) * 20, cy = 46 + hash(i + 9) * 34, cz = -260 - hash(i + 4) * 60;
    const cg = new THREE.Group(); cg.position.set(cx, cy, cz); g.add(cg);
    for (let j = 0; j < 5; j++) {
      const r = 7 + hash(i * 5 + j) * 6;
      const o = mesh(cg, new THREE.IcosahedronGeometry(r, 1), cm, (j - 2) * 7.5, (hash(j + i) - 0.3) * 4, 0);
      o.castShadow = false; o.receiveShadow = false; o.scale.y = 0.72;
    }
  }
};

/** a stack of planks: `n` layers of `m` boards, crosswise */
const plankStack = (p: THREE.Object3D, x: number, z: number, ry: number, n = 3, m = 5, L = 3) => {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
  const w = wood();
  for (let l = 0; l < n; l++) for (let i = 0; i < m; i++)
    box(g, L, 0.12, 0.26, w, 0, 0.06 + l * 0.13, (i - (m - 1) / 2) * 0.3, l % 2 ? 0.04 : -0.03);
  box(g, 0.14, 0.14 * n + 0.1, 0.12, woodDark(), L / 2 - 0.2, (0.14 * n) / 2, (m / 2) * 0.3 + 0.08);
  return g;
};
const crate = (p: THREE.Object3D, x: number, z: number, s: number, ry: number, label?: string) => {
  const m = label ? lam("crate" + label, () => ({ map: tx("crate" + label, () => crateLabel(label)) })) : lam("crate", () => ({ map: tx("crateW", () => planks("#d2a46a", "#c09058", 4)) }));
  return box(p, s, s, s, m, x, s / 2, z, ry);
};
const dirtDisc = (p: THREE.Object3D, x: number, z: number, r: number, key = "dirtA", y = 0.012) => {
  const m = lam(key, () => ({ map: tx(key, () => dirt("#b86b43", [Math.max(1, r / 2), Math.max(1, r / 2)])), polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }));
  const o = mesh(p, new THREE.CircleGeometry(r, 40), m, x, y, z, 0, -Math.PI / 2);
  o.castShadow = false;
  return o;
};
const dirtPath = (p: THREE.Object3D, pts: [number, number][], w: number) => {
  // ribbon through the points on the ground
  const curve = new THREE.CatmullRomCurve3(pts.map(([x, z]) => new THREE.Vector3(x, 0, z)));
  const N = 80, pos: number[] = [], uv: number[] = [], idx: number[] = [];
  for (let i = 0; i <= N; i++) {
    const t = i / N, c = curve.getPointAt(t), d = curve.getTangentAt(t), n = new THREE.Vector3(-d.z, 0, d.x).normalize();
    const ww = w * (0.85 + 0.15 * Math.sin(i * 0.7));
    for (const s of [-1, 1]) { pos.push(c.x + n.x * ww * s * 0.5, 0.014, c.z + n.z * ww * s * 0.5); uv.push(s < 0 ? 0 : 1, t * curve.getLength() / 3); }
    if (i < N) { const a = i * 2; idx.push(a, a + 2, a + 1, a + 1, a + 2, a + 3); }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute(uv, 2));
  g.setIndex(idx); g.computeVertexNormals();
  const m = lam("dirtPath", () => ({ map: tx("dirtPath", () => dirt("#b86b43", [1, 1])), polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1, side: THREE.DoubleSide }));
  const o = new THREE.Mesh(g, m); o.receiveShadow = true; p.add(o);
  return o;
};

// ---------------- coaster loop (live, bendable) ----------------
const TAU = Math.PI * 2;
const wrapD = (a: number, b: number) => { let d = (a - b) % TAU; if (d > Math.PI) d -= TAU; if (d < -Math.PI) d += TAU; return d; };
const bump = (a: number, a0: number, s: number) => Math.exp(-(wrapD(a, a0) ** 2) / s);
export type LoopSpec = { c: V3; R: number; spiral: number; gauge: number };
// The bent loop is an upright, crooked OCTAGON: a flat face across the top and the bottom, straight sides with
// sharp kinks at the 8 joints. Vertex radii / angles are jittered asymmetrically left vs right, never caved in at
// the top. Vertex k sits at pi/2 + pi/8 + k*pi/4 (k0 top-left ... k7 top-right).
const OCT: [number, number][] = [ // [radius factor, angle jitter (rad)]
  [1.03, -0.03], [1.09, 0.07], [0.95, -0.05], [1.0, 0], [1.0, 0], [1.05, 0.05], [0.92, -0.09], [1.01, 0.03],
];
const octVerts = OCT.map(([rk, da], k) => { const a = Math.PI / 2 + Math.PI / 8 + (k * Math.PI) / 4 + da; return [rk * Math.cos(a), rk * Math.sin(a)] as [number, number]; });
/** distance from the centre to the unit octagon along angle a */
const octRadius = (a: number) => {
  const dx = Math.cos(a), dy = Math.sin(a);
  for (let k = 0; k < 8; k++) {
    const [ax, ay] = octVerts[k], [bx, by] = octVerts[(k + 1) % 8];
    const ex = bx - ax, ey = by - ay, den = dx * ey - dy * ex;
    if (Math.abs(den) < 1e-9) continue;
    const t = (ax * ey - ay * ex) / den, s = (ax * dy - ay * dx) / den;
    if (t > 0 && s >= -1e-6 && s <= 1 + 1e-6) return t;
  }
  return 1;
};
/** radius of the loop at angle a (a = -pi/2 is the bottom) for a bend amount 0..1 */
const loopRadius = (a: number, R: number, bend: number) => {
  if (bend <= 0) return R;
  // the bottom stays on the lead track: the octagon is blended back to the circle around a = -pi/2
  const keep = 1 - bump(a, -Math.PI / 2, 0.18);
  return R + bend * (R * octRadius(a) - R) * keep;
};
export const loopPoint = (L: LoopSpec, a: number, bend: number, radial: number, zOff: number, out = new THREE.Vector3()) => {
  const r = loopRadius(a, L.R, bend) + radial, keep = 1 - bump(a, -Math.PI / 2, 0.35);
  const sx = r * Math.cos(a), sy = r * Math.sin(a);
  return out.set(
    L.c[0] + sx + bend * 0.05 * sy * keep,
    L.c[1] + sy,
    L.c[2] + L.spiral * ((a + Math.PI / 2) / TAU - 0.5) + zOff + bend * 0.35 * Math.sin(2 * a) * keep,
  );
};
class FnCurve extends THREE.Curve<THREE.Vector3> {
  constructor(private fn: (t: number, out: THREE.Vector3) => THREE.Vector3) { super(); }
  override getPoint(t: number, out = new THREE.Vector3()) { return this.fn(t, out); }
}
type LoopMats = { rail: THREE.Material; spine: THREE.Material; tie: THREE.Material };
/** one arc of a loop (a0..a1) with two rails, an outside spine, ties and struts; setBend rebuilds the tubes */
export class LoopArc {
  group = new THREE.Group();
  private rails: THREE.Mesh[] = []; private spine: THREE.Mesh; private ties: THREE.Mesh[] = []; private struts: THREE.Mesh[] = [];
  private cache = new Map<string, THREE.BufferGeometry[]>();
  private bend = -1;
  constructor(private L: LoopSpec, private a0: number, private a1: number, m: LoopMats, private nTies = 56) {
    for (let i = 0; i < 2; i++) { const o = new THREE.Mesh(new THREE.BufferGeometry(), m.rail); o.castShadow = o.receiveShadow = true; this.rails.push(o); this.group.add(o); }
    this.spine = new THREE.Mesh(new THREE.BufferGeometry(), m.spine); this.spine.castShadow = this.spine.receiveShadow = true; this.group.add(this.spine);
    const tg = new THREE.BoxGeometry(0.16, 0.12, L.gauge + 0.3), sg = new THREE.BoxGeometry(0.09, 1, 0.09);
    for (let i = 0; i < nTies; i++) {
      const t = new THREE.Mesh(tg, m.tie); t.castShadow = true; this.ties.push(t); this.group.add(t);
      if (i % 2 === 0) { const s = new THREE.Mesh(sg, m.tie); s.castShadow = true; this.struts.push(s); this.group.add(s); }
    }
    this.setBend(0);
  }
  setBend(b: number) {
    const bq = Math.round(b * 1000) / 1000;
    if (bq === this.bend) return;
    this.bend = bq;
    const { L, a0, a1 } = this, key = bq.toFixed(3);
    let geos = this.cache.get(key);
    if (!geos) {
      const at = (t: number) => a0 + (a1 - a0) * t;
      const segs = Math.max(24, Math.round(((a1 - a0) / TAU) * 360));
      geos = [
        new THREE.TubeGeometry(new FnCurve((t, o) => loopPoint(L, at(t), bq, 0, -L.gauge / 2, o)), segs, 0.075, 8, false),
        new THREE.TubeGeometry(new FnCurve((t, o) => loopPoint(L, at(t), bq, 0, L.gauge / 2, o)), segs, 0.075, 8, false),
        new THREE.TubeGeometry(new FnCurve((t, o) => loopPoint(L, at(t), bq, 0.46, 0, o)), segs, 0.17, 10, false),
      ];
      this.cache.set(key, geos);
    }
    this.rails[0].geometry = geos[0]; this.rails[1].geometry = geos[1]; this.spine.geometry = geos[2];
    const p = new THREE.Vector3(), q = new THREE.Vector3(), s = new THREE.Vector3();
    this.ties.forEach((t, i) => {
      const a = a0 + ((a1 - a0) * (i + 0.5)) / this.nTies;
      loopPoint(L, a, bq, -0.02, 0, p); loopPoint(L, a + 0.01, bq, -0.02, 0, q);
      t.position.copy(p); t.rotation.set(0, 0, Math.atan2(q.y - p.y, q.x - p.x));
      if (i % 2 === 0) {
        const st = this.struts[i / 2];
        loopPoint(L, a, bq, 0.46, 0, s);
        const d = s.clone().sub(p), len = d.length();
        st.position.copy(p).addScaledVector(d, 0.5); st.scale.set(1, len, 1);
        st.quaternion.setFromUnitVectors(UP, d.normalize());
      }
    });
  }
}
/** straight lead-in / lead-out track at the loop's bottom, with posts down to the ground */
const leadTrack = (p: THREE.Object3D, L: LoopSpec, from: number, to: number, z: number, m: LoopMats) => {
  const y = L.c[1] - L.R;
  for (const s of [-1, 1]) strut(p, [from, y, z + (s * L.gauge) / 2], [to, y, z + (s * L.gauge) / 2], 0.075, m.rail, 8);
  strut(p, [from, y - 0.46, z], [to, y - 0.46, z], 0.17, m.spine, 10);
  const n = Math.max(2, Math.round(Math.abs(to - from) / 1.2));
  for (let i = 0; i <= n; i++) {
    const x = from + ((to - from) * i) / n;
    box(p, 0.16, 0.12, L.gauge + 0.3, m.tie, x, y - 0.02, z);
    if (i % 2 === 0 && y - 0.46 > 0.2) {
      box(p, 0.16, y - 0.46, 0.16, m.tie, x, (y - 0.46) / 2, z);
      box(p, 0.5, 0.12, 0.5, lam("concrete", () => ({ map: tx("concrete", concrete) })), x, 0.06, z);
    }
  }
};
/** A-frame steel tower under the loop's side at angle a, on concrete footers */
const aFrame = (p: THREE.Object3D, L: LoopSpec, a: number, m: THREE.Material) => {
  const top = loopPoint(L, a, 0, 0.46, 0);
  const conc = lam("concrete", () => ({ map: tx("concrete", concrete) }));
  const spread = 2.4;
  for (const s of [-1, 1]) {
    strut(p, [top.x, 0.4, top.z + s * spread], [top.x, top.y - 0.2, top.z + s * 0.25], 0.16, m, 10);
    box(p, 0.9, 0.5, 0.9, conc, top.x, 0.25, top.z + s * spread);
  }
  for (let h = 0.3; h < 0.9; h += 0.28) {
    const y = 0.4 + (top.y - 0.6) * h, w = spread * (1 - h) + 0.25 * h;
    strut(p, [top.x, y, top.z - w], [top.x, y, top.z + w], 0.07, m, 6);
  }
  box(p, 0.5, 0.3, 0.9, m, top.x, top.y - 0.15, top.z);
};

// ---------------- SET_LOOP ----------------
const setLoop = (g: THREE.Group, props: Record<string, unknown>) => {
  const L: LoopSpec = { c: LOOP.center, R: LOOP.R, spiral: 0.9, gauge: 1.1 };
  // weathered charcoal steel rails + backbone, rusty-brown cross-ties (v2: no candy stripes on Frank's loop)
  const mats: LoopMats = { rail: lit("railCharcoal", "#3d3532"), spine: lit("spineCharcoal", "#4a403c"), tie: lit("tieRust", "#7a4928") };
  const arc = new LoopArc(L, -Math.PI / 2, 1.5 * Math.PI, mats, 64);
  g.add(arc.group);
  props.loopArc = arc;
  leadTrack(g, L, -22, L.c[0], L.c[2] - L.spiral / 2, mats);
  leadTrack(g, L, L.c[0], 22, L.c[2] + L.spiral / 2, mats);
  aFrame(g, L, 0, mats.tie); aFrame(g, L, Math.PI, mats.tie);
  dirtDisc(g, 0, -4, 11, "dirtLoop");
  dirtPath(g, [[0.4, 30], [-1.2, 18], [0.8, 8], [0, 2], [-0.5, -4]], 3.2);
  // elevated work platform: deck top at y 3.2, x -2..2, z -0.5..3.0; rails on the back and the sides only
  const Y = LOOP.platformY, w = wood();
  const top = lam("platTop", () => ({ map: tx("platTop", () => planks("#c99158", "#b67d46", 7)) }));
  box(g, 4.0, 0.22, 3.5, top, 0, Y - 0.11, 1.25);
  for (const x of [-1.85, 1.85]) for (const z of [-0.35, 2.85]) box(g, 0.2, Y - 0.22, 0.2, woodDark(), x, (Y - 0.22) / 2, z);
  for (const x of [-1.85, 1.85]) {
    beamBox(g, [x, 0.3, -0.35], [x, Y - 0.4, 2.85], 0.1, woodDark());
    beamBox(g, [x, 0.3, 2.85], [x, Y - 0.4, -0.35], 0.1, woodDark());
  }
  beamBox(g, [-1.85, 0.4, -0.35], [1.85, Y - 0.4, -0.35], 0.1, woodDark());
  const rail = (a: V3, b: V3) => { beamBox(g, [a[0], Y + 1.0, a[2]], [b[0], Y + 1.0, b[2]], 0.09, w); beamBox(g, [a[0], Y + 0.5, a[2]], [b[0], Y + 0.5, b[2]], 0.06, w); };
  rail([-1.9, 0, -0.45], [1.9, 0, -0.45]); rail([-1.9, 0, -0.45], [-1.9, 0, 2.2]); rail([1.9, 0, -0.45], [1.9, 0, 2.2]);
  for (const [x, z] of [[-1.9, -0.45], [0, -0.45], [1.9, -0.45], [-1.9, 1.0], [1.9, 1.0], [-1.9, 2.2], [1.9, 2.2]] as const) box(g, 0.1, 1.05, 0.1, w, x, Y + 0.52, z);
  // ladder up the right side
  for (const s of [-1, 1]) beamBox(g, [2.3, 0, 1.2 + s * 0.3], [2.05, Y + 0.6, 1.2 + s * 0.3], 0.08, woodDark());
  for (let i = 1; i < 9; i++) { const k = i / 9; box(g, 0.06, 0.06, 0.6, w, 2.3 - 0.25 * k * (Y + 0.6) / (Y + 0.6), k * (Y + 0.6), 1.2); }
  // a length of the loop's own steel track laid across the platform right in front of the builder: the near rail
  // (z PLAT_RAIL_Z, centre y 3.25) is what the hammer head comes down on at f14; the far rail runs behind his feet
  for (const z of [LOOP.railZ, LOOP.railZ - 0.72]) strut(g, [-2.05, LOOP.railY, z], [2.05, LOOP.railY, z], 0.06, mats.rail, 10);
  for (let x = -1.8; x <= 1.81; x += 0.45) box(g, 0.14, 0.05, 1.0, mats.tie, x, Y + 0.025, LOOP.railZ - 0.36);
  // toolbox + paint can on the deck, clear of the builder's swing (he stands at x 0, z 2.5)
  box(g, 0.55, 0.28, 0.3, lit("toolbox", "#d23a2e"), -1.35, Y + 0.14, 0.1);
  cyl(g, 0.14, 0.14, 0.3, lit("paintcan", "#3b6ea5"), 1.4, Y + 0.15, 0.05);
  // plank stacks and crates around the loop base
  plankStack(g, -4.6, 0.6, 0.3); plankStack(g, 4.4, 1.8, -0.4, 4); plankStack(g, -9.5, -1.5, 1.2); plankStack(g, 6.5, -8, 0.8);
  crate(g, -3.2, 2.6, 0.8, 0.3, "BOLTS"); crate(g, -2.6, 3.4, 0.6, -0.2); crate(g, 3.4, 3.8, 0.7, 0.5, "TRACK");
  for (let i = 0; i < 4; i++) tree(g, -12 - i * 3.2, 0, -10 - hash(i) * 8, 2.2 + hash(i + 2), 30 + i);
  for (let i = 0; i < 4; i++) tree(g, 12 + i * 3.4, 0, -9 - hash(i + 7) * 8, 2.1 + hash(i + 5), 40 + i);
};

// ---------------- SET_DECK ----------------
/** track along an arbitrary 3D curve: rails offset sideways (horizontal binormal), spine below, ties, posts */
const curveTrack = (p: THREE.Object3D, curve: THREE.Curve<THREE.Vector3>, gauge: number, m: LoopMats) => {
  const side = (t: number, s: number, down: number, o: THREE.Vector3) => {
    const c = curve.getPointAt(t), d = curve.getTangentAt(t), n = new THREE.Vector3(-d.z, 0, d.x).normalize();
    return o.copy(c).addScaledVector(n, s * gauge / 2).add(new THREE.Vector3(0, -down, 0));
  };
  const N = 220;
  for (const s of [-1, 1]) mesh(p, new THREE.TubeGeometry(new FnCurve((t, o) => side(t, s, 0, o)), N, 0.075, 8, false), m.rail, 0, 0, 0);
  mesh(p, new THREE.TubeGeometry(new FnCurve((t, o) => side(t, 0, 0.46, o)), N, 0.17, 10, false), m.spine, 0, 0, 0);
  const len = curve.getLength(), n = Math.round(len / 0.9);
  for (let i = 0; i <= n; i++) {
    const t = i / n, c = curve.getPointAt(t), d = curve.getTangentAt(t);
    const tie = box(p, 0.16, 0.12, gauge + 0.3, m.tie, c.x, c.y - 0.02, c.z);
    tie.rotation.set(0, Math.atan2(-d.z, d.x), Math.asin(THREE.MathUtils.clamp(d.y, -1, 1)), "YXZ");
    if (i % 3 === 0 && c.y > 1.0) {
      box(p, 0.16, c.y - 0.46, 0.16, m.tie, c.x, (c.y - 0.46) / 2, c.z);
      box(p, 0.5, 0.12, 0.5, lam("concrete", () => ({ map: tx("concrete", concrete) })), c.x, 0.06, c.z);
    }
  }
};
const CART_S = 1.35; // v2: the cart reads 1.35x larger
const makeCart = () => {
  const outer = new THREE.Group(), g = new THREE.Group();
  g.scale.setScalar(CART_S); outer.add(g);
  const red = lit("cartRed", "#e03a2c"), dark = lit("cartSeat", "#3a2a2e"), steel = lit("cartWheel", "#2a2426");
  const ban = lam("banner", () => ({ map: tx("banner", banner) }));
  // dark undercarriage: chassis rail, axle blocks, bumper
  box(g, 2.0, 0.14, 0.86, lit("chassis", "#2a2224"), 0, 0.26, 0);
  for (const x of [-0.65, 0.65]) box(g, 0.34, 0.2, 1.0, lit("chassis", "#2a2224"), x, 0.22, 0);
  box(g, 0.12, 0.22, 0.9, lit("chassis", "#2a2224"), -1.02, 0.42, 0);
  // body along +x (the direction of travel), sitting on the rails
  box(g, 1.9, 0.62, 1.12, red, 0, 0.62, 0);
  const nose = box(g, 0.5, 0.5, 1.12, red, 1.05, 0.55, 0); nose.rotation.z = -0.35;
  box(g, 1.92, 0.08, 1.16, lit("cartTrim", "#f4e8cc"), 0, 0.95, 0);
  for (const s of [-1, 1]) {
    const b = mesh(g, new THREE.PlaneGeometry(1.5, 0.34), ban, -0.05, 0.62, s * 0.565, s > 0 ? 0 : Math.PI);
    b.castShadow = false;
  }
  for (const x of [-0.45, 0.35]) { box(g, 0.42, 0.5, 0.9, dark, x, 1.12, 0); box(g, 0.14, 0.5, 0.9, dark, x - 0.24, 1.3, 0); }
  // lap bars
  for (const x of [-0.2, 0.6]) strut(g, [x, 1.25, -0.42], [x, 1.25, 0.42], 0.04, lit("barYellow", "#f2c230"), 6);
  for (const x of [-0.65, 0.65]) for (const s of [-1, 1]) {
    const w = mesh(g, new THREE.CylinderGeometry(0.16, 0.16, 0.12, 14), steel, x, 0.22, s * 0.55); w.rotation.x = Math.PI / 2;
  }
  return outer;
};
const setDeck = (g: THREE.Group, props: Record<string, unknown>) => {
  // same weathered steel as Frank's bent loop in shot 1, so the drop and the background loop read as his track
  const mats: LoopMats = { rail: lit("railCharcoal", "#3d3532"), spine: lit("spineCharcoal", "#4a403c"), tie: lit("tieRust", "#7a4928") };
  const w = wood(), wd = woodDark();
  // scaffolding tower
  const [sx, , sz] = DECK.scaffold, H = DECK.scaffoldH, hw = 0.9;
  for (const dx of [-hw, hw]) for (const dz of [-hw, hw]) box(g, 0.16, H, 0.16, wd, sx + dx, H / 2, sz + dz);
  for (let y = 1.4; y < H; y += 1.4) {
    for (const dz of [-hw, hw]) box(g, 2 * hw + 0.2, 0.12, 0.12, w, sx, y, sz + dz);
    for (const dx of [-hw, hw]) box(g, 0.12, 0.12, 2 * hw + 0.2, w, sx + dx, y, sz);
  }
  for (let y = 0; y < H - 1.4; y += 1.4) {
    beamBox(g, [sx - hw, y + 0.1, sz + hw], [sx + hw, y + 1.3, sz + hw], 0.08, w);
    beamBox(g, [sx + hw, y + 0.1, sz - hw], [sx + hw, y + 1.3, sz + hw], 0.08, w);
  }
  box(g, 2.4, 0.16, 2.4, lam("platTop", () => ({ map: tx("platTop", () => planks("#c99158", "#b67d46", 7)) })), sx, H, sz);
  // pulley gantry with a hoisted cable and a crate of bolts
  beamBox(g, [sx - hw, H, sz + hw], [sx - hw, H + 1.6, sz + hw], 0.14, wd);
  beamBox(g, [sx - hw, H + 1.6, sz + hw], [sx - hw - 1.4, H + 1.6, sz + hw], 0.14, wd);
  const wheel = mesh(g, new THREE.TorusGeometry(0.24, 0.06, 8, 18), lit("pulley", "#5a6270"), sx - hw - 1.3, H + 1.35, sz + hw);
  wheel.rotation.y = Math.PI / 2;
  strut(g, [sx - hw - 1.3 - 0.02, H + 1.15, sz + hw], [sx - hw - 1.3 - 0.02, 4.6, sz + hw], 0.025, lit("rope", "#3a2a22"), 5);
  strut(g, [sx - hw - 1.06, H + 1.3, sz + hw], [sx - hw + 0.1, 0.9, sz + hw + 0.2], 0.025, lit("rope", "#3a2a22"), 5);
  box(g, 0.6, 0.5, 0.6, lam("crateBOLTS", () => ({ map: tx("crateBOLTS", () => crateLabel("BOLTS")) })), sx - hw - 1.3, 4.35, sz + hw);
  // the drop: off the top of the scaffolding, curving down and away into the bent loop in the background
  const bg: LoopSpec = { c: DECK.bgLoop, R: DECK.bgR, spiral: 0.9, gauge: 1.1 };
  const entry = loopPoint(bg, -Math.PI / 2, 1, 0, -bg.spiral / 2);
  const drop = new THREE.CatmullRomCurve3([
    new THREE.Vector3(sx - 0.6, H + 0.55, sz + 0.2), new THREE.Vector3(sx + 0.6, H + 0.55, sz - 0.4),
    new THREE.Vector3(sx + 1.8, H + 0.1, sz - 1.9), new THREE.Vector3(sx + 3.2, 5.0, sz - 5.2),
    new THREE.Vector3(sx + 4.6, 1.6, sz - 8.6), new THREE.Vector3(entry.x - 4.0, entry.y, entry.z + 3.2),
    new THREE.Vector3(entry.x - 0.4, entry.y, entry.z),
  ], false, "centripetal", 0.5);
  curveTrack(g, drop, 1.1, mats);
  props.dropCurve = drop;
  const arc = new LoopArc(bg, -Math.PI / 2, 1.5 * Math.PI, mats, 48); arc.setBend(1); g.add(arc.group);
  leadTrack(g, bg, bg.c[0], bg.c[0] + 18, bg.c[2] + bg.spiral / 2, mats);
  aFrame(g, bg, 0, mats.tie); aFrame(g, bg, Math.PI, mats.tie);
  const cart = makeCart(); g.add(cart); props.cart = cart;
  // the builder's deck: top y 3.0, x -0.4..2.6, z -0.3..2.6; red/cream boards, railing back + sides, stair right
  const Y = DECK.deckY;
  box(g, 3.0, 0.2, 2.9, w, 1.1, Y - 0.1, 1.15);
  const top = mesh(g, new THREE.PlaneGeometry(3.0, 2.9), lam("deckTop", () => ({ map: tx("deckTop", deckPlanks), polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 })), 1.1, Y + 0.002, 1.15, 0, -Math.PI / 2);
  top.castShadow = false;
  for (const x of [-0.3, 2.5]) for (const z of [-0.2, 2.5]) box(g, 0.2, Y - 0.2, 0.2, wd, x, (Y - 0.2) / 2, z);
  for (const x of [-0.3, 2.5]) { beamBox(g, [x, 0.3, -0.2], [x, Y - 0.35, 2.5], 0.1, wd); beamBox(g, [x, 0.3, 2.5], [x, Y - 0.35, -0.2], 0.1, wd); }
  const rl = (a: [number, number], b: [number, number]) => {
    beamBox(g, [a[0], Y + 1.0, a[1]], [b[0], Y + 1.0, b[1]], 0.09, w);
    beamBox(g, [a[0], Y + 0.5, a[1]], [b[0], Y + 0.5, b[1]], 0.06, w);
  };
  rl([-0.35, -0.25], [2.55, -0.25]); rl([-0.35, -0.25], [-0.35, 1.9]); rl([2.55, -0.25], [2.55, 1.3]);
  for (const [x, z] of [[-0.35, -0.25], [1.1, -0.25], [2.55, -0.25], [-0.35, 0.8], [-0.35, 1.9], [2.55, 0.6], [2.55, 1.3]] as const) box(g, 0.1, 1.05, 0.1, w, x, Y + 0.52, z);
  for (let i = 0; i < 10; i++) box(g, 0.9, 0.08, 0.3, w, 3.1, Y - 0.3 - i * 0.3, 1.9 + i * 0.3 * 0.9);
  for (const s of [2.65, 3.55]) beamBox(g, [s, Y, 1.8], [s, 0, 4.6], 0.08, wd);
  plankStack(g, 4.8, -0.5, 0.5, 3); crate(g, -1.0, 1.6, 0.7, 0.2, "TRACK"); crate(g, 4.3, 2.0, 0.6, -0.3);
  dirtPath(g, [[-2, 18], [0.5, 8], [1.5, 2], [3.0, -6], [6, -16]], 3.0);
};

// ---------------- SET_RIVAL ----------------
const lattice = (p: THREE.Object3D, a: V3, b: V3, w: number, m: THREE.Material, step = 1.6) => {
  // square lattice boom from a to b: 4 chords + zig-zag braces
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A), L = d.length(); d.normalize();
  const u = Math.abs(d.y) > 0.9 ? new THREE.Vector3(1, 0, 0) : new THREE.Vector3(0, 1, 0);
  const s1 = new THREE.Vector3().crossVectors(d, u).normalize().multiplyScalar(w / 2), s2 = new THREE.Vector3().crossVectors(d, s1).normalize().multiplyScalar(w / 2);
  const corners = [s1.clone().add(s2), s1.clone().sub(s2), s1.clone().negate().sub(s2), s1.clone().negate().add(s2)];
  const v = (o: THREE.Vector3, t: number) => A.clone().addScaledVector(d, t).add(o).toArray() as V3;
  for (const c of corners) strut(p, v(c, 0), v(c, L), 0.06, m, 6);
  const n = Math.max(1, Math.round(L / step));
  for (let i = 0; i < n; i++) for (let k = 0; k < 4; k++) {
    const c0 = corners[k], c1 = corners[(k + 1) % 4];
    strut(p, v(c0, (i * L) / n), v(c1, ((i + 1) * L) / n), 0.035, m, 5);
  }
};
const setRival = (g: THREE.Group, props: Record<string, unknown>) => {
  const white: LoopMats = { rail: lit("railWhite", "#f6f6f2"), spine: lit("spineWhite", "#e8ecf0"), tie: lit("steelLight", "#aab6c4") };
  const L: LoopSpec = { c: RIVAL.loop, R: RIVAL.R, spiral: 0.9, gauge: 1.1 };
  // the loop is still under construction: a ~35 degree gap stays open at the very top, and the missing arch piece
  // hangs above it from the crane (world.ts lifts it by archLiftAt: +2.2 m -> +1.1 m over the shot)
  const GAP = THREE.MathUtils.degToRad(35) / 2;
  const gapA = Math.PI / 2 - GAP, gapB = Math.PI / 2 + GAP;
  const low = new LoopArc(L, -Math.PI / 2, gapA, white, 30); g.add(low.group);
  const high = new LoopArc(L, gapB, 1.5 * Math.PI, white, 30); g.add(high.group);
  const arch = new LoopArc(L, gapA + 0.015, gapB - 0.015, white, 10);
  const archG = new THREE.Group(); archG.add(arch.group); g.add(archG); props.arch = archG;
  leadTrack(g, L, -20, L.c[0], L.c[2] - L.spiral / 2, white);
  leadTrack(g, L, L.c[0], 20, L.c[2] + L.spiral / 2, white);
  aFrame(g, L, 0, white.tie); aFrame(g, L, Math.PI, white.tie);
  // tower crane: mast on the left, jib reaching diagonally over the loop's top gap
  const yel = lit("craneYellow", "#f2c230"), [cx, , cz] = RIVAL.crane, H = RIVAL.craneH;
  box(g, 3.2, 0.8, 3.2, lam("concrete", () => ({ map: tx("concrete", concrete) })), cx, 0.4, cz);
  lattice(g, [cx, 0.8, cz], [cx, H, cz], 1.3, yel, 1.5);
  const tgt = new THREE.Vector3(L.c[0], 0, L.c[2]), dir = tgt.clone().sub(new THREE.Vector3(cx, 0, cz)); const reach = dir.length(); dir.normalize();
  const tip: V3 = [cx + dir.x * (reach + 3), H + 0.6, cz + dir.z * (reach + 3)], back: V3 = [cx - dir.x * 6, H + 0.6, cz - dir.z * 6];
  lattice(g, [cx, H + 0.6, cz], tip, 1.0, yel, 1.6);
  lattice(g, [cx, H + 0.6, cz], back, 1.0, yel, 1.6);
  const ry = Math.atan2(-dir.z, dir.x);
  box(g, 1.6, 1.4, 1.6, lit("cab", "#f2c230"), cx + dir.x * 1.2, H - 0.3, cz + dir.z * 1.2, ry);
  box(g, 1.2, 0.8, 1.66, lit("cabGlass", "#6fa8d0"), cx + dir.x * 1.2, H - 0.15, cz + dir.z * 1.2, ry);
  box(g, 1.8, 1.6, 1.4, lam("concrete", () => ({ map: tx("concrete", concrete) })), back[0], H - 0.4, back[2], ry);
  strut(g, [cx, H + 3.2, cz], tip, 0.04, lit("cable", "#3a3438"), 5);
  strut(g, [cx, H + 3.2, cz], back, 0.04, lit("cable", "#3a3438"), 5);
  lattice(g, [cx, H + 0.6, cz], [cx, H + 3.4, cz], 0.8, yel, 1.4);
  box(g, 0.9, 0.4, 1.1, lit("trolley", "#d8a020"), tgt.x, H + 0.1, tgt.z, ry);
  // hook cable + slings, scaled by world.ts as the arch is lowered
  const hook = new THREE.Group(); g.add(hook); props.hook = hook;
  const cable = mesh(hook, new THREE.CylinderGeometry(0.035, 0.035, 1, 6), lit("cable", "#3a3438"), 0, 0, 0); props.hookCable = cable;
  const hb = mesh(hook, new THREE.BoxGeometry(0.35, 0.5, 0.35), lit("hookRed", "#d23a2e"), 0, 0, 0); props.hookBlock = hb;
  const slings: THREE.Mesh[] = [];
  for (let i = 0; i < 2; i++) slings.push(mesh(hook, new THREE.CylinderGeometry(0.025, 0.025, 1, 5), lit("cable", "#3a3438"), 0, 0, 0));
  props.slings = slings; props.craneTop = new THREE.Vector3(tgt.x, H - 0.1, tgt.z);
  props.archEnds = [loopPoint(L, gapA + 0.06, 0, 0.5, 0), loopPoint(L, gapB - 0.06, 0, 0.5, 0)];
  // Ferris wheel behind on the right
  const [fx, fy, fz] = RIVAL.ferris, FR = RIVAL.ferrisR;
  const fw = new THREE.Group(); fw.position.set(fx, fy, fz); g.add(fw); props.ferris = fw;
  const rimM = lit("ferrisRim", "#f4f0e6"), spokeM = lit("ferrisSpoke", "#e04a4a");
  for (const s of [-0.45, 0.45]) { const r = mesh(fw, new THREE.TorusGeometry(FR, 0.13, 8, 64), rimM, 0, 0, s); r.castShadow = false; }
  const NS = 12;
  for (let i = 0; i < NS; i++) {
    const a = (i / NS) * TAU;
    for (const s of [-0.45, 0.45]) strut(fw, [0, 0, s], [Math.cos(a) * FR, Math.sin(a) * FR, s], 0.05, spokeM, 5);
    strut(fw, [Math.cos(a) * FR, Math.sin(a) * FR, -0.45], [Math.cos(a) * FR, Math.sin(a) * FR, 0.45], 0.05, rimM, 5);
  }
  const hub = mesh(fw, new THREE.CylinderGeometry(0.6, 0.6, 1.3, 16), lit("hub", "#f2c230"), 0, 0, 0); hub.rotation.x = Math.PI / 2;
  const GC = ["#e8443a", "#3b6ea5", "#f2c230", "#4da83b", "#e87ab0", "#f08a2c"];
  const gond: THREE.Group[] = [];
  for (let i = 0; i < NS; i++) {
    const gg = new THREE.Group(); fw.add(gg); gond.push(gg);
    const m = lit("gond" + (i % GC.length), GC[i % GC.length]);
    box(gg, 0.9, 0.7, 0.9, m, 0, -0.75, 0); box(gg, 1.0, 0.12, 1.0, lit("gondRoof", "#f4f0e6"), 0, -0.3, 0);
    strut(gg, [0, 0, 0], [0, -0.3, 0], 0.04, rimM, 4);
  }
  props.gondolas = gond;
  for (const s of [-1.3, 1.3]) for (const d of [-1, 1]) {
    strut(g, [fx + d * 4.2, 0, fz + s * 1.6], [fx, fy, fz + s * 0.6], 0.16, lit("ferrisLeg", "#7d8ea3"), 8);
  }
  // dirt patch around the rival + easel + winch
  dirtDisc(g, 0.15, 2.0, 2.7, "dirtRival");
  dirtPath(g, [[0.2, 2], [0.4, -2], [0, -6], [0, -9]], 2.4);
  const [ex, , ez] = RIVAL.easel, ery = Math.atan2(0.1 - ex, 5.2 - ez);
  const easel = new THREE.Group(); easel.position.set(ex, 0, ez); easel.rotation.y = ery; g.add(easel);
  const ew = lit("easelWood", "#b47a44");
  for (const s of [-1, 1]) beamBox(easel, [s * 0.42, 0, 0.18], [s * 0.18, 1.85, -0.02], 0.055, ew);
  beamBox(easel, [0, 0, -0.62], [0, 1.75, -0.06], 0.05, ew);
  box(easel, 1.1, 0.06, 0.12, ew, 0, 0.8, 0.12);
  const board = new THREE.Group(); board.position.set(0, 1.24, 0.1); board.rotation.x = -0.1; easel.add(board);
  box(board, 1.08, 0.84, 0.05, lit("boardFrame", "#2a2226"), 0, 0, -0.02);
  const bt = mesh(board, new THREE.PlaneGeometry(1.02, 0.78), lam("blueprint", () => ({ map: tx("blueprint", blueprint) })), 0, 0, 0.006);
  bt.castShadow = false;
  const [wx, , wz] = RIVAL.winch, gold = lit("gold", "#e8b830"), wbase = lit("winchBase", "#f4f0e6");
  const winch = new THREE.Group(); winch.position.set(wx, 0, wz); winch.rotation.y = RIVAL.winchYaw; g.add(winch);
  box(winch, 0.94, 0.26, 0.5, wbase, 0, 0.13, 0); // long enough on the right to carry the lever pivot
  for (const s of [-1, 1]) box(winch, 0.06, 0.5, 0.44, gold, s * 0.3, 0.5, 0);
  const drum = mesh(winch, new THREE.CylinderGeometry(0.17, 0.17, 0.54, 18), gold, 0, 0.55, 0); drum.rotation.z = Math.PI / 2;
  const coil = mesh(winch, new THREE.CylinderGeometry(0.2, 0.2, 0.4, 18), lit("rope", "#3a2a22"), 0, 0.55, 0); coil.rotation.z = Math.PI / 2;
  const gear = mesh(winch, new THREE.CylinderGeometry(0.27, 0.27, 0.05, 14), gold, 0.36, 0.55, 0); gear.rotation.z = Math.PI / 2;
  // v2.1: the old side crank (dark peg) is gone. A vertical brass control lever stands on the right end of the
  // winch base; world.ts aims its shaft so the round gold knob sits exactly inside the rival's 2D fist every frame.
  const brass = lit("brass", "#d9a62e");
  const leverPivot = mesh(g, new THREE.CylinderGeometry(0.075, 0.09, 0.08, 14), gold, 0, 0, 0);
  const leverShaft = mesh(g, new THREE.CylinderGeometry(0.022, 0.026, 1, 10), brass, 0, 0, 0);
  const leverKnob = mesh(g, new THREE.SphereGeometry(0.05, 16, 12), gold, 0, 0, 0);
  props.lever = { pivot: leverPivot, shaft: leverShaft, knob: leverKnob };
  // spare track pieces, cones and planks lying about
  plankStack(g, 3.4, -1.4, -0.5, 2); crate(g, -2.6, -0.6, 0.7, 0.4, "BOLTS");
  for (const [x, z] of [[2.2, 3.4], [-2.2, 3.6], [3.6, 1.0]] as const) {
    cyl(g, 0.02, 0.18, 0.5, lit("cone", "#f08a2c"), x, 0.25, z, 10);
    box(g, 0.4, 0.04, 0.4, lit("coneBase", "#2a2226"), x, 0.02, z);
  }
};

export const buildSets = (): Sets => {
  const root = new THREE.Group();
  const sets: Record<string, THREE.Group> = {};
  const props: Record<string, unknown> = {};
  const common = new THREE.Group(); land(common); root.add(common);
  for (const [name, fn] of [["loop", setLoop], ["deck", setDeck], ["rival", setRival]] as const) {
    const g = new THREE.Group(); g.name = name; fn(g, props); sets[name] = g; root.add(g);
  }
  return { root, sets, props };
};
