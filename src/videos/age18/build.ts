// The eight age18 sets as three.js geometry: birthday dining room, clinic lab, street with the moving van,
// night living room, bathroom, bank counter, golden lakeside dock and the night window. Hand-painted textures
// come from paint.ts; every surface material goes through shade.ts twoTone so it takes the scene light.
// Volumetric-style spotlight cones are additive, unlit shells on the NOINK layer.
import * as THREE from "three";
import { twoTone } from "./shade";
import { NOINK } from "./ink";
import {
  woodFloor, tileFloor, wallPaint, wallpaperDots, bunting, lawn, driveway, siding, lake, tvScreen, ecgScreen,
  skeletonPoster, bankSign, tellerSign, clock300, windowNight, mirrorTex, rugTex,
} from "./paint";
import { CLINIC, CLINIC5, LIVING, BATH, BANK, DOCK, WINDOW, DINING, STREET } from "./story";

const MATS = new Map<string, THREE.Material>();
export const lam = (key: string, make: () => THREE.MeshLambertMaterialParameters) => {
  const hit = MATS.get(key);
  if (hit) return hit as THREE.MeshLambertMaterial;
  const m = twoTone(new THREE.MeshLambertMaterial(make()));
  MATS.set(key, m);
  return m;
};
export const lit = (key: string, color: THREE.ColorRepresentation, k = 1) => lam(key, () => ({ color: new THREE.Color(color).multiplyScalar(k) }));

/** HDR-ish unlit screen: the bloom pass picks up anything above the 1.0 threshold */
export const screenMat = (key: string, map: THREE.Texture, k = 2.2, toneMapped = true) => {
  const m = new THREE.MeshBasicMaterial({ map, color: new THREE.Color(k, k, k), toneMapped });
  m.name = key;
  return m;
};

const textureCache = new Map<string, THREE.Texture>();
const tx = (key: string, make: () => THREE.Texture) => {
  const hit = textureCache.get(key);
  if (hit) return hit;
  const t = make();
  textureCache.set(key, t);
  return t;
};

export type Sets = {
  root: THREE.Group;
  sets: Record<string, THREE.Group>;
  props: Record<string, THREE.Object3D>;
};

const mesh = (parent: THREE.Object3D, g: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) => {
  const o = new THREE.Mesh(g, m);
  o.position.set(x, y, z);
  o.rotation.set(rx, ry, rz);
  o.castShadow = true; o.receiveShadow = true;
  parent.add(o);
  return o;
};
const box = (p: THREE.Object3D, w: number, h: number, d: number, m: THREE.Material, x: number, y: number, z: number, ry = 0) =>
  mesh(p, new THREE.BoxGeometry(w, h, d), m, x, y, z, ry);
const plane = (p: THREE.Object3D, w: number, h: number, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0) =>
  mesh(p, new THREE.PlaneGeometry(w, h), m, x, y, z, ry, rx);
const cyl = (p: THREE.Object3D, r0: number, r1: number, h: number, m: THREE.Material, x: number, y: number, z: number, seg = 20) =>
  mesh(p, new THREE.CylinderGeometry(r0, r1, h, seg), m, x, y, z);

const beamTex = (() => {
  let t: THREE.Texture | null = null;
  return () => {
    if (t) return t;
    const c = document.createElement("canvas"); c.width = 64; c.height = 256;
    const g = c.getContext("2d")!;
    const gr = g.createLinearGradient(0, 0, 0, 256);
    gr.addColorStop(0, "rgba(255,255,255,0.9)"); gr.addColorStop(0.55, "rgba(255,255,255,0.45)"); gr.addColorStop(1, "rgba(255,255,255,0)");
    g.fillStyle = gr; g.fillRect(0, 0, 64, 256);
    const im = g.getImageData(0, 0, 64, 256);
    for (let y = 0; y < 256; y++) for (let x = 0; x < 64; x++) {
      const edge = Math.min(x, 63 - x) / 32;
      im.data[(y * 64 + x) * 4 + 3] *= Math.min(1, edge * 1.6);
    }
    g.putImageData(im, 0, 0);
    t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    return t;
  };
})();

/** volumetric-style cone from a fixture apex down to a surface */
const beam = (p: THREE.Object3D, from: THREE.Vector3, to: THREE.Vector3, rBase: number, color: string, opacity: number) => {
  const d = new THREE.Vector3().subVectors(from, to);
  const h = d.length();
  const geo = new THREE.ConeGeometry(rBase, h, 24, 1, true);
  const m = new THREE.MeshBasicMaterial({ map: beamTex(), color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending, fog: false, toneMapped: false });
  const o = new THREE.Mesh(geo, m);
  o.position.copy(to).addScaledVector(d, 0.5);
  o.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.normalize());
  o.layers.set(NOINK);
  o.renderOrder = 2;
  p.add(o);
  return o;
};

const glowBall = (p: THREE.Object3D, x: number, y: number, z: number, r: number, color: string) => {
  const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(2.6), fog: false, toneMapped: true });
  const o = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), m);
  o.position.set(x, y, z);
  o.layers.set(NOINK);
  p.add(o);
  return o;
};

/** wallpapered/wainscoted room: floor, back wall, two side walls, ceiling (no front wall: the camera enters) */
const room = (g: THREE.Group, w: number, back: number, front: number, h: number, floorMat: THREE.Material, wallMat: THREE.Material, opt: { wainscot?: string; side?: boolean } = {}) => {
  const d = back - front;
  const f = plane(g, w, d, floorMat, 0, 0, (back + front) / 2, 0, -Math.PI / 2);
  f.receiveShadow = true;
  plane(g, w, h, wallMat, 0, h / 2, back, Math.PI);
  // ceiling: closes the sky wedge above the open-top set, no shadow so the key light still enters
  const ceil = plane(g, w, d, lit("ceiling", "#cfc8bc"), 0, h, (back + front) / 2, 0, Math.PI / 2);
  ceil.castShadow = false; ceil.receiveShadow = false;
  if (opt.side !== false) {
    plane(g, d, h, wallMat, -w / 2, h / 2, (back + front) / 2, Math.PI / 2);
    plane(g, d, h, wallMat, w / 2, h / 2, (back + front) / 2, -Math.PI / 2);
  }
  if (opt.wainscot) {
    const wm = lit("wainscot", opt.wainscot);
    box(g, w, 1.0, 0.06, wm, 0, 0.5, back - 0.03);
    box(g, 0.06, 1.0, d, wm, -w / 2 + 0.03, 0.5, (back + front) / 2);
    box(g, 0.06, 1.0, d, wm, w / 2 - 0.03, 0.5, (back + front) / 2);
    box(g, w, 0.07, 0.09, lit("wainscotRail", "#f2e2c4"), 0, 1.02, back - 0.04);
  }
};

// ---------------- dining room ----------------
const dining = (g: THREE.Group, props: Record<string, THREE.Object3D>) => {
  room(g, 6.4, 3.0, -5.5, 3.1,
    lam("diningFloor", () => ({ map: tx("diningFloor", () => woodFloor("#9a6238", "#5e3820")) })),
    lam("diningWall", () => ({ map: tx("diningWall", () => wallPaint("#e7cfa8", "#c8a878")) })),
    { wainscot: "#8a5230" });
  // bunting across the back wall
  const bm = new THREE.MeshLambertMaterial({ map: tx("bunting", bunting), transparent: true, alphaTest: 0.4, side: THREE.DoubleSide });
  const b = plane(g, 5.2, 1.3, bm, 0, 2.35, 2.93);
  b.castShadow = false;
  // rug
  const rm = new THREE.MeshLambertMaterial({ map: tx("rug", rugTex), transparent: true, alphaTest: 0.3, side: THREE.DoubleSide });
  plane(g, 3.4, 2.4, rm, 0, 0.012, 0.25, 0, -Math.PI / 2).castShadow = false;
  // table + chairs
  const wood = lit("tableWood", "#7a4a2a");
  const cloth = lit("tableCloth", "#f2e6cc");
  box(g, 2.2, 0.09, 1.05, cloth, 0, 0.78, 0.15);
  box(g, 2.0, 0.06, 0.9, wood, 0, 0.72, 0.15);
  for (const [x, z] of [[-0.9, -0.2], [0.9, -0.2], [-0.9, 0.52], [0.9, 0.52]]) cyl(g, 0.045, 0.05, 0.72, wood, x, 0.36, z + 0.15);
  const chairs = new THREE.Group();
  const drawChair = (x: number, z: number, ry: number) => {
    const c = new THREE.Group();
    box(c, 0.48, 0.07, 0.48, wood, 0, 0.46, 0);
    for (const [dx, dz] of [[-0.19, -0.19], [0.19, -0.19], [-0.19, 0.19], [0.19, 0.19]]) cyl(c, 0.025, 0.028, 0.46, lit("chairWood", "#5e3820"), dx, 0.23, dz);
    box(c, 0.48, 0.55, 0.06, lit("chairBack", "#8a5230"), 0, 0.78, -0.21);
    c.position.set(x, 0, z); c.rotation.y = ry;
    chairs.add(c);
  };
  drawChair(-1.6, 0.3, Math.PI / 2 - 0.25);
  drawChair(1.5, 0.55, -Math.PI / 2 + 0.3);
  for (const c of chairs.children) { c.traverse((o) => { const mm = o as THREE.Mesh; if (mm.isMesh) { mm.castShadow = true; mm.receiveShadow = true; } }); }
  g.add(chairs);
  props.diningChairs = chairs;
  // sideboard on the left wall
  box(g, 0.5, 1.0, 1.8, lit("sideboard", "#6a3e24"), -2.7, 0.5, 0.6);
  box(g, 0.55, 0.06, 1.9, lit("sideboardTop", "#8a5230"), -2.7, 1.03, 0.6);
  // pendant lamp: cord, warm shade, glowing bulb, cone. Set off the hero's face axis so the additive
  // cone shells do not wash the card black into brown.
  cyl(g, 0.012, 0.012, 0.75, lit("cord", "#2a2226"), 0.85, 2.72, 0.15, 6);
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.38, 0.32, 24, 1, true), lit("pendantShade", "#2f6e74"));
  shade.position.set(0.85, 2.26, 0.15); shade.rotation.x = Math.PI;
  shade.castShadow = true; g.add(shade);
  glowBall(g, 0.85, 2.12, 0.15, 0.09, "#ffd9a0");
  props.diningBeam = beam(g, new THREE.Vector3(0.85, 2.12, 0.15), new THREE.Vector3(0.85, 0.84, 0.15), 0.8, "#ffcf88", 0.2);
  // framed picture right wall
  box(g, 0.06, 0.8, 1.1, lit("frameGold", "#8a6a3a"), 3.16, 1.9, 0.4);
  box(g, 0.02, 0.66, 0.96, lit("picture", "#6a8a86"), 3.12, 1.9, 0.4);
};

// ---------------- clinic ----------------
const clinic = (g: THREE.Group, props: Record<string, THREE.Object3D>) => {
  room(g, 6.0, 2.8, -5.2, 3.0,
    lam("clinicFloor", () => ({ map: tx("clinicFloor", () => tileFloor("#e6eef0", "#cfdce2", 6)) })),
    lam("clinicWall", () => ({ map: tx("clinicWall", () => wallPaint("#dceaf0", "#c4d8e0")) })),
    { wainscot: "#a8c8d0", side: true });
  // exam bed
  const bed = new THREE.Group();
  box(bed, 1.25, 0.12, 2.0, lit("bedBase", "#8c98a4"), -1.75, 0.5, 0.62);
  box(bed, 1.3, 0.16, 2.05, lit("bedMattress", "#f0f2ee"), -1.75, 0.64, 0.62);
  box(bed, 1.0, 0.14, 0.46, lit("bedPillow", "#ffffff"), -1.75, 0.78, 1.42);
  for (const [x, z] of [[-2.35, -0.3], [-1.15, -0.3], [-2.35, 1.5], [-1.15, 1.5]]) cyl(bed, 0.035, 0.035, 0.5, lit("bedLeg", "#5c6670"), x, 0.25, z);
  box(bed, 1.35, 0.05, 0.06, lit("bedRail", "#5c6670"), -1.75, 0.86, -0.36);
  g.add(bed);
  // skeleton poster
  const poster = new THREE.MeshLambertMaterial({ map: tx("skeleton", skeletonPoster) });
  plane(g, 0.9, 1.24, poster, CLINIC.poster[0], CLINIC.poster[1], CLINIC.poster[2] + 0.02);
  box(g, 0.98, 0.05, 0.05, lit("posterFrame", "#5c6670"), CLINIC.poster[0], CLINIC.poster[1] + 0.66, CLINIC.poster[2]);
  box(g, 0.98, 0.05, 0.05, lit("posterFrame", "#5c6670"), CLINIC.poster[0], CLINIC.poster[1] - 0.66, CLINIC.poster[2]);
  // ECG monitor on a stand
  box(g, 0.5, 0.62, 0.34, lit("ecgBody", "#d8dde0"), CLINIC.ecg[0], 1.42, CLINIC.ecg[2]);
  const ecg = new THREE.MeshBasicMaterial({ map: tx("ecg", () => ecgScreen(72)), color: new THREE.Color(1.5, 1.5, 1.5), toneMapped: true });
  plane(g, 0.42, 0.4, ecg, CLINIC.ecg[0], 1.46, CLINIC.ecg[2] - 0.18, Math.PI);
  cyl(g, 0.03, 0.03, 1.1, lit("ecgPole", "#9aa4ac"), CLINIC.ecg[0], 0.55, CLINIC.ecg[2]);
  box(g, 0.5, 0.05, 0.4, lit("ecgFoot", "#7c868e"), CLINIC.ecg[0], 0.03, CLINIC.ecg[2]);
  // cabinets on the back wall
  for (let i = 0; i < 2; i++) {
    box(g, 1.05, 1.7, 0.42, lit("cabinet", "#b9c8ce"), 1.3 + i * 1.12, 0.85, 2.56);
    box(g, 0.9, 0.03, 0.02, lit("cabinetSeam", "#7c8c94"), 1.3 + i * 1.12, 0.85, 2.34);
    box(g, 0.05, 0.18, 0.05, lit("cabinetHandle", "#5c6670"), 1.08 + i * 1.12, 0.95, 2.33);
  }
  // instrument cart by the bed
  box(g, 0.5, 0.06, 0.4, lit("cartTop", "#c8d2d8"), -2.55, 0.86, 1.4);
  for (const [x, z] of [[-2.76, 1.24], [-2.34, 1.24], [-2.76, 1.56], [-2.34, 1.56]]) cyl(g, 0.02, 0.02, 0.84, lit("cartLeg", "#8c98a4"), x, 0.42, z);
  box(g, 0.34, 0.18, 0.26, lit("tray", "#e8eef0"), -2.55, 0.98, 1.4);
  // ceiling light panel + cone over the bed
  box(g, 2.0, 0.06, 0.5, lit("ceilPanel", "#f8fbff"), 0, 2.95, 0.4);
  glowBall(g, 0, 2.88, 0.4, 0.12, "#eaf6ff");
  beam(g, new THREE.Vector3(0, 2.9, 0.4), new THREE.Vector3(0, 0.6, 0.6), 1.5, "#dcefff", 0.07);
  // small window with blinds on the right wall
  box(g, 0.05, 1.0, 1.3, lit("blind", "#eef4f6"), 2.96, 1.8, 0.8);
  for (let i = 0; i < 7; i++) box(g, 0.06, 0.02, 1.24, lit("blindSlat", "#c8d8de"), 2.92, 1.4 + i * 0.12, 0.8);
};

// ---------------- street ----------------
const street = (g: THREE.Group) => {
  const lawnM = lam("lawn", () => ({ map: tx("lawn", lawn) }));
  const ground = plane(g, 40, 34, lawnM, 0, 0, 1.5, 0, -Math.PI / 2);
  ground.receiveShadow = true;
  const driveM = lam("drive", () => ({ map: tx("drive", driveway) }));
  const dv = plane(g, 9, 3.4, driveM, 1.6, 0.008, 0.55, 0, -Math.PI / 2);
  dv.receiveShadow = true;
  // house facade
  const sid = lam("siding", () => ({ map: tx("siding", siding) }));
  box(g, 15, 4.4, 0.4, sid, 0, 2.2, 4.4);
  box(g, 15.6, 0.3, 0.8, lit("roofEdge", "#6a4a34"), 0, 4.5, 4.2);
  for (const [x, w] of [[-4.6, 1.4], [2.9, 1.4]]) {
    box(g, w + 0.2, 1.5, 0.08, lit("winFrame", "#f4f1e8"), x, 2.2, 4.18);
    box(g, w - 0.1, 1.3, 0.06, lit("winGlass", "#a8cce0"), x, 2.2, 4.16);
    box(g, 0.05, 1.3, 0.08, lit("winMullion", "#f4f1e8"), x, 2.2, 4.14);
    box(g, w - 0.1, 0.05, 0.08, lit("winMullion", "#f4f1e8"), x, 2.2, 4.14);
  }
  // door + steps
  box(g, 1.15, 2.2, 0.1, lit("doorFrame", "#c8b896"), -1.25, 1.1, 4.17);
  box(g, 1.0, 2.05, 0.08, lit("door", "#6e4a30"), -1.25, 1.03, 4.15);
  box(g, 0.06, 0.06, 0.06, lit("knob", "#d8b45a"), -0.86, 1.05, 4.1);
  box(g, 1.6, 0.14, 0.7, lit("step", "#b0a894"), -1.25, 0.07, 3.9);
  // van: box body, cab, wheels, windows, orange stripe
  const van = new THREE.Group();
  box(van, 2.7, 1.55, 1.75, lit("vanBody", "#e2e9ec"), 0, 1.25, 0);
  // side windows + stripe so the panel we see from the yard reads as a van, not a white wall
  for (const z of [0.89, -0.89]) {
    box(van, 1.05, 0.42, 0.05, lit("vanWin", "#2f4658"), 0.2, 1.62, z);
    box(van, 2.5, 0.11, 0.05, lit("vanStripe", "#e08a30"), 0.08, 0.98, z);
  }
  box(van, 1.1, 1.2, 1.68, lit("vanCab", "#e4e8e6"), -1.85, 0.98, 0);
  box(van, 1.05, 0.1, 1.7, lit("vanStripe", "#e08a30"), -1.85, 1.42, 0);
  box(van, 0.6, 0.5, 1.5, lit("vanGlass", "#2a3e50"), -1.9, 1.28, 0);
  box(van, 0.06, 0.42, 0.9, lit("vanGlass", "#2a3e50"), -1.36, 1.35, 0);
  for (const [x, z] of [[-1.65, -0.86], [-1.65, 0.86], [0.72, -0.86], [0.72, 0.86]]) {
    mesh(van, new THREE.CylinderGeometry(0.38, 0.38, 0.24, 18), lit("tyre", "#242428"), x, 0.38, z, 0, Math.PI / 2);
    // small dark hubs only: a lighter disc read as a helmet floating in the gap under Theo's arm
    mesh(van, new THREE.CylinderGeometry(0.12, 0.12, 0.26, 12), lit("hub", "#30343a"), x, 0.38, z, 0, Math.PI / 2);
  }
  // dark underbody skirt ties the wheels into the body so no isolated disc shows under the arms
  box(van, 2.5, 0.26, 1.5, lit("vanUnder", "#2c3034"), 0.1, 0.56, 0);
  box(van, 1.7, 0.06, 1.6, lit("vanRoof", "#d8dedb"), 0.1, 2.05, 0);
  van.position.set(STREET.van[0], 0, STREET.van[2]);
  van.rotation.y = 2.55;
  g.add(van);
  // boxes by the door
  const card = lit("cardboard", "#b98a52");
  box(g, 0.62, 0.56, 0.58, card, 0.55, 0.28, 1.0, 0.18);
  box(g, 0.5, 0.44, 0.5, card, 1.05, 0.22, 1.2, -0.12);
  box(g, 0.46, 0.4, 0.46, card, 0.68, 0.72, 1.03, 0.3);
  // two trees framing the street
  for (const [x, z, s] of [[-5.4, 2.2, 1], [5.8, 2.8, 1.15]] as const) {
    cyl(g, 0.16 * s, 0.22 * s, 2.0 * s, lit("trunk", "#6a4a30"), x, 1.0 * s, z);
    const foliage = lit("foliage", "#4e7a3c");
    for (const [dx, dy, dz, r] of [[0, 2.6, 0, 1.15], [-0.6, 2.3, 0.2, 0.8], [0.55, 2.4, -0.15, 0.85]] as const) {
      const sp = new THREE.Mesh(new THREE.SphereGeometry(r * s, 16, 12), foliage);
      sp.position.set(x + dx * s, dy * s, z + dz * s); sp.castShadow = true; g.add(sp);
    }
  }
  // kerb + road strip behind camera for depth
  box(g, 16, 0.12, 2.6, lit("road", "#6a6a6e"), 0, 0.02, -3.4);
};

// ---------------- living room ----------------
const living = (g: THREE.Group, props: Record<string, THREE.Object3D>) => {
  room(g, 6.2, 3.0, -5.2, 3.0,
    lam("livingFloor", () => ({ map: tx("livingFloor", () => woodFloor("#8a6038", "#4e301c")) })),
    lam("livingWall", () => ({ map: tx("livingWall", () => wallpaperDots("#46506e")) })),
    { wainscot: "#323a52", side: true });
  // rug + sofa
  const rm = new THREE.MeshLambertMaterial({ map: tx("rug2", rugTex), transparent: true, alphaTest: 0.3, side: THREE.DoubleSide });
  plane(g, 3.8, 2.6, rm, 0, 0.012, 0.6, 0, -Math.PI / 2).castShadow = false;
  const sofa = new THREE.Group();
  const fab = lit("sofa", "#4a6e7a");
  const fabD = lit("sofaDark", "#385664");
  // seat top at 0.53 so the seated cards (hip 0.46) sit on the cushions instead of inside them
  box(sofa, 2.5, 0.34, 0.95, fab, 0, 0.28, 0);
  box(sofa, 2.5, 0.5, 0.3, fabD, 0, 0.6, 0.34);
  for (const x of [-1.25, 1.25]) box(sofa, 0.28, 0.5, 0.95, fabD, x, 0.5, 0);
  for (const x of [-0.62, 0.62]) box(sofa, 1.14, 0.12, 0.82, lit("sofaSeat", "#5a8290"), x, 0.47, -0.02);
  for (const [x, z] of [[-1.05, -0.35], [1.05, -0.35], [-1.05, 0.35], [1.05, 0.35]]) cyl(sofa, 0.035, 0.04, 0.2, lit("sofaLeg", "#3a2a20"), x, 0.1, z);
  sofa.position.set(0, 0, 0.82);
  g.add(sofa);
  // coffee table + pizza box
  box(g, 1.4, 0.08, 0.8, lit("coffeeTop", "#8a5a34"), 0.15, 0.42, -0.35);
  for (const [x, z] of [[-0.5, -0.62], [0.8, -0.62], [-0.5, -0.08], [0.8, -0.08]]) cyl(g, 0.03, 0.035, 0.4, lit("coffeeLeg", "#5a3a22"), 0.15 + x, 0.2, -0.35 + z);
  // TV on a low stand, screen toward the sofa
  const tv = new THREE.Group();
  box(tv, 1.7, 0.5, 0.45, lit("tvStand", "#3a2f34"), 0, 0.25, 0);
  box(tv, 1.55, 0.95, 0.1, lit("tvBody", "#1c1a20"), 0, 0.98, 0);
  const scr = new THREE.MeshBasicMaterial({ map: tx("tv", tvScreen), color: new THREE.Color(2.1, 2.1, 2.1), toneMapped: true });
  plane(tv, 1.4, 0.82, scr, 0, 0.98, -0.055, Math.PI);
  tv.position.set(LIVING.tv[0], LIVING.tv[1] - 0.5, LIVING.tv[2]);
  g.add(tv);
  props.livingTv = tv;
  // short TV spill cone in the back corner; it stays behind the sofa so it never tints the faces
  beam(g, new THREE.Vector3(LIVING.tv[0], 1.3, LIVING.tv[2] - 0.1), new THREE.Vector3(LIVING.tv[0] - 0.15, 0.35, LIVING.tv[2] - 0.7), 0.8, "#7fb4ff", 0.09);
  // wall clock 3:00
  box(g, 0.9, 0.46, 0.08, lit("clockBody", "#181418"), LIVING.clock[0], LIVING.clock[1], LIVING.clock[2] - 0.04);
  const cm = new THREE.MeshBasicMaterial({ map: tx("clock", clock300), color: new THREE.Color(2.4, 1.1, 1.1), toneMapped: true });
  plane(g, 0.78, 0.38, cm, LIVING.clock[0], LIVING.clock[1], LIVING.clock[2] - 0.09, Math.PI);
  // floor lamp (twilight shot): pole + shade + warm cone
  const lamp = new THREE.Group();
  cyl(lamp, 0.02, 0.02, 1.5, lit("lampPole", "#2a2226"), 0, 0.75, 0);
  cyl(lamp, 0.16, 0.2, 0.06, lit("lampFoot", "#2a2226"), 0, 0.03, 0);
  const shade = new THREE.Mesh(new THREE.CylinderGeometry(0.18, 0.28, 0.32, 20, 1, true), lit("lampShade", "#c8a86a"));
  shade.position.set(0, 1.55, 0); lamp.add(shade);
  glowBall(lamp, 0, 1.48, 0, 0.07, "#ffcf88");
  lamp.position.set(-1.35, 0, 1.9);
  g.add(lamp);
  props.livingLamp = lamp;
  beam(g, new THREE.Vector3(-1.35, 1.48, 1.9), new THREE.Vector3(-1.15, 0.9, 1.55), 0.8, "#ffcf88", 0.1);
  // shelf + plant
  box(g, 1.4, 0.06, 0.36, lit("shelf", "#6a4a30"), -2.5, 1.6, 2.2);
  box(g, 0.4, 0.5, 0.3, lit("shelfBook", "#b34a4a"), -2.8, 1.88, 2.2);
  cyl(g, 0.18, 0.14, 0.34, lit("pot", "#b06a4a"), -2.2, 0.17, 2.45);
  for (let i = 0; i < 5; i++) {
    const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.16, 10, 8), lit("leaf", "#4e8a4a"));
    leaf.scale.set(0.7, 1.5, 0.7);
    leaf.position.set(-2.2 + (i - 2) * 0.12, 0.5 + (i % 2) * 0.14, 2.45);
    g.add(leaf);
  }
};

// ---------------- bathroom ----------------
const bathroom = (g: THREE.Group) => {
  room(g, 3.6, 2.3, -4.2, 2.8,
    lam("bathFloor", () => ({ map: tx("bathFloor", () => tileFloor("#dfeef0", "#b8d4da", 8)) })),
    lam("bathWall", () => ({ map: tx("bathWall", () => wallPaint("#dceef0", "#bcd8de")) })),
    { wainscot: "#a8c8cc", side: true });
  // tile band above the wainscot
  for (let i = 0; i < 26; i++) {
    const x = -1.7 + (i % 13) * 0.28, y = 1.18 + Math.floor(i / 13) * 0.24;
    box(g, 0.24, 0.2, 0.03, lit(i % 2 ? "bathTile2" : "bathTile1", i % 2 ? "#eaf4f4" : "#d0e4e6"), x, y, 2.27);
  }
  // vanity + basin: pushed flat against the wall so nothing crosses the hero card
  box(g, 1.35, 0.12, 0.62, lit("vanityTop", "#eef2f0"), BATH.sink[0], 0.92, BATH.sink[2]);
  box(g, 1.25, 0.82, 0.56, lit("vanity", "#7a5a44"), BATH.sink[0], 0.46, BATH.sink[2]);
  box(g, 0.6, 0.1, 0.05, lit("vanityDoor", "#8a6a50"), BATH.sink[0], 0.55, BATH.sink[2] - 0.305);
  cyl(g, 0.22, 0.18, 0.14, lit("basin", "#f4f8f6"), BATH.sink[0], 0.99, BATH.sink[2] - 0.05);
  cyl(g, 0.018, 0.018, 0.28, lit("faucet", "#c8d0d4"), BATH.sink[0] + 0.3, 1.1, BATH.sink[2] - 0.14);
  box(g, 0.05, 0.05, 0.18, lit("faucet", "#c8d0d4"), BATH.sink[0] + 0.3, 1.24, BATH.sink[2] - 0.22);
  // mirror + frame + soft wash light
  box(g, 1.0, 1.15, 0.06, lit("mirrorFrame", "#6a7880"), BATH.mirror[0], BATH.mirror[1], BATH.mirror[2]);
  const mr = new THREE.MeshLambertMaterial({ map: tx("mirror", mirrorTex) });
  plane(g, 0.88, 1.02, mr, BATH.mirror[0], BATH.mirror[1], BATH.mirror[2] - 0.04, Math.PI);
  box(g, 1.2, 0.06, 0.1, lit("mirrorLight", "#f4f8f8"), BATH.mirror[0], BATH.mirror[1] + 0.65, BATH.mirror[2] - 0.06);
  glowBall(g, BATH.mirror[0], BATH.mirror[1] + 0.62, BATH.mirror[2] - 0.1, 0.06, "#f0fbff");
  beam(g, new THREE.Vector3(BATH.mirror[0], BATH.mirror[1] + 0.62, BATH.mirror[2] - 0.1), new THREE.Vector3(BATH.mirror[0], 0.95, BATH.sink[2] - 0.3), 0.8, "#eaf6ff", 0.1);
  // towel rail
  cyl(g, 0.015, 0.015, 0.9, lit("rail", "#b8c4c8"), 1.55, 1.35, 2.24, 8).rotation.z = Math.PI / 2;
  box(g, 0.5, 0.7, 0.04, lit("towel", "#7ab0c0"), 1.4, 1.0, 2.2);
  // toilet at the left edge
  box(g, 0.46, 0.42, 0.6, lit("toilet", "#eef2f0"), -1.5, 0.21, 1.7);
  box(g, 0.46, 0.5, 0.16, lit("toilet", "#eef2f0"), -1.5, 0.52, 1.98);
};

// ---------------- bank ----------------
const bankSet = (g: THREE.Group) => {
  room(g, 8.0, 3.2, -5.0, 3.2,
    lam("bankFloor", () => ({ map: tx("bankFloor", () => tileFloor("#e8e2d6", "#d4ccbc", 5)) })),
    lam("bankWall", () => ({ map: tx("bankWall", () => wallPaint("#d8c9b0", "#c0ac90")) })),
    { wainscot: "#8a6a4a", side: true });
  // long counter
  const counter = new THREE.Group();
  box(counter, 5.2, 1.02, 0.7, lit("counterFront", "#6a4a32"), 0.35, 0.51, 1.35);
  box(counter, 5.4, 0.1, 0.9, lit("counterTop", "#3a2a20"), 0.35, 1.11, 1.32);
  for (let i = 0; i < 5; i++) box(counter, 0.9, 0.5, 0.05, lit("counterPanel", "#7c5838"), -1.8 + i * 1.08, 0.5, 1.0);
  // low glass screens with brass posts (visual only, no sorting drama)
  for (const x of [-2.0, -0.6, 0.9, 2.4]) cyl(counter, 0.035, 0.035, 0.55, lit("brass", "#c8a050"), x, 1.42, 1.15, 10);
  g.add(counter);
  // bank sign
  const bs = new THREE.MeshBasicMaterial({ map: tx("bankSign", bankSign), color: new THREE.Color(1.15, 1.15, 1.15), toneMapped: true });
  plane(g, 2.6, 0.65, bs, 0.3, 2.35, 3.16, Math.PI);
  // teller sign on the counter
  const ts = new THREE.MeshLambertMaterial({ map: tx("tellerSign", tellerSign) });
  plane(g, 0.55, 0.27, ts, 0.05, 1.3, 1.22, Math.PI);
  box(g, 0.5, 0.04, 0.16, lit("signStand", "#c8a050"), 0.05, 1.18, 1.28);
  // monitor standing on the counter, screen above the counter lip so the frozen card is never cut off
  box(g, 0.9, 0.56, 0.06, lit("monitorBody", "#1a181e"), BANK.monitor[0], BANK.monitor[1] + 0.02, BANK.monitor[2] + 0.04);
  box(g, 0.12, 0.16, 0.12, lit("monitorNeck", "#2a2830"), BANK.monitor[0], BANK.monitor[1] - 0.25, BANK.monitor[2] + 0.02);
  box(g, 0.36, 0.04, 0.28, lit("monitorFoot", "#1a181e"), BANK.monitor[0], BANK.monitor[1] - 0.32, BANK.monitor[2]);
  // ceiling strip lights
  for (const x of [-2.0, 1.8]) {
    box(g, 1.8, 0.05, 0.28, lit("ceilBar", "#f8fbff"), x, 3.1, 0.8);
    glowBall(g, x, 3.04, 0.8, 0.1, "#eaf6ff");
  }
  beam(g, new THREE.Vector3(-2.0, 3.0, 0.8), new THREE.Vector3(-2.0, 0.8, 0.9), 1.3, "#eaf4ff", 0.08);
  beam(g, new THREE.Vector3(1.8, 3.0, 0.8), new THREE.Vector3(1.8, 0.8, 0.9), 1.3, "#eaf4ff", 0.08);
  // queue posts in front of the counter
  for (const x of [-2.4, 2.8]) {
    cyl(g, 0.05, 0.06, 1.0, lit("queuePost", "#3a3a44"), x, 0.5, -0.35);
    glowBall(g, x, 1.02, -0.35, 0.05, "#3a3a44");
  }
};

// ---------------- dock ----------------
const dockSet = (g: THREE.Group) => {
  const planks = lam("dockFloor", () => ({ map: tx("dockFloor", () => woodFloor("#9a7048", "#6a4a30")) }));
  const d = plane(g, 8, 9, planks, 0, 0, -1.2, 0, -Math.PI / 2);
  d.receiveShadow = true;
  // lake
  // water and the far shore keep their own colour: fog already washes the whole frame to cream
  const wm = new THREE.MeshBasicMaterial({ map: tx("lake", () => lake(true)), color: new THREE.Color(1, 1, 1), toneMapped: true, fog: false });
  const water = plane(g, 240, 220, wm, 0, -0.42, 112, 0, -Math.PI / 2);
  water.castShadow = false; water.receiveShadow = false;
  // dock edge posts + rail behind the bench
  for (const x of [-3.6, 3.6]) cyl(g, 0.1, 0.12, 0.9, lit("post", "#5a3a24"), x, 0.45, 1.4);
  // distant shore
  const shoreM = twoTone(new THREE.MeshLambertMaterial({ color: new THREE.Color("#3a4a4c"), fog: false }));
  box(g, 200, 1.6, 6, shoreM, 0, 0.1, 95).castShadow = false;
  // bench: seat slats, back slats, legs, arms
  const bench = new THREE.Group();
  const slat = lit("benchSlat", "#8a5a34");
  for (let i = 0; i < 3; i++) box(bench, 2.6, 0.06, 0.16, slat, 0, 0.46, -0.18 + i * 0.18);
  for (let i = 0; i < 3; i++) box(bench, 2.6, 0.16, 0.06, slat, 0, 0.62 + i * 0.2, 0.3);
  for (const x of [-1.15, 1.15]) {
    box(bench, 0.08, 0.46, 0.5, lit("benchLeg", "#4a3020"), x, 0.23, 0.02);
    box(bench, 0.08, 0.5, 0.08, lit("benchLeg", "#4a3020"), x, 0.7, 0.3);
    box(bench, 0.08, 0.06, 0.62, lit("benchArm", "#6a4428"), x, 0.7, 0.08);
  }
  bench.position.set(DOCK.bench[0], 0, DOCK.bench[2]);
  g.add(bench);
  // a small jetty rail at the right
  for (const z of [0.2, 1.1]) cyl(g, 0.06, 0.07, 0.9, lit("railPost", "#5a3a24"), 3.4, 0.45, z);
  cyl(g, 0.03, 0.03, 0.95, lit("railPost", "#5a3a24"), 3.4, 0.9, 0.65, 8).rotation.x = Math.PI / 2;
};

// ---------------- night window ----------------
const windowSet = (g: THREE.Group) => {
  room(g, 3.8, 2.4, -4.0, 2.9,
    lam("winFloor", () => ({ map: tx("winFloor", () => woodFloor("#7a5534", "#462a18")) })),
    lam("winWall", () => ({ map: tx("winWall", () => wallPaint("#5a4a5c", "#3e3242")) })),
    { wainscot: "#3a2c34", side: true });
  // window: frame, night glass, mullions, sill
  box(g, 1.45, 1.62, 0.1, lit("nightFrame", "#3a3038"), WINDOW.win[0], WINDOW.win[1], WINDOW.win[2]);
  const nm = new THREE.MeshBasicMaterial({ map: tx("windowNight", windowNight), color: new THREE.Color(1.25, 1.25, 1.3), toneMapped: true });
  plane(g, 1.28, 1.44, nm, WINDOW.win[0], WINDOW.win[1], WINDOW.win[2] - 0.06, Math.PI);
  box(g, 0.05, 1.44, 0.06, lit("nightMullion", "#3a3038"), WINDOW.win[0], WINDOW.win[1], WINDOW.win[2] - 0.08);
  box(g, 1.28, 0.05, 0.06, lit("nightMullion", "#3a3038"), WINDOW.win[0], WINDOW.win[1], WINDOW.win[2] - 0.08);
  box(g, 1.6, 0.09, 0.24, lit("windowSill", "#4a3c44"), WINDOW.win[0], WINDOW.win[1] - 0.83, WINDOW.win[2] - 0.1);
  // curtains
  for (const x of [-0.75, 0.75]) box(g, 0.18, 2.0, 0.16, lit("curtain", "#4a3a5a"), WINDOW.win[0] + x, 1.35, WINDOW.win[2] - 0.18);
  cyl(g, 0.025, 0.025, 1.9, lit("curtainRod", "#2a2228"), WINDOW.win[0], 2.45, WINDOW.win[2] - 0.2, 8).rotation.z = Math.PI / 2;
  // moonbeam through the window
  beam(g, new THREE.Vector3(WINDOW.win[0], WINDOW.win[1], WINDOW.win[2] - 0.2), new THREE.Vector3(WINDOW.win[0] - 0.4, 0.1, 0.4), 1.15, "#9ab8ff", 0.1);
  // a bare side table with a small clock
  box(g, 0.7, 0.06, 0.7, lit("sideTable", "#4a3a30"), -1.5, 0.72, 1.6);
  for (const [x, z] of [[-1.78, 1.32], [-1.22, 1.32], [-1.78, 1.88], [-1.22, 1.88]]) cyl(g, 0.025, 0.03, 0.7, lit("sideLeg", "#3a2c24"), x, 0.36, z);
};

export const buildSets = (): Sets => {
  const root = new THREE.Group();
  const sets: Record<string, THREE.Group> = {};
  const props: Record<string, THREE.Object3D> = {};
  const add = (name: string, fn: (g: THREE.Group) => void) => { const g = new THREE.Group(); g.name = name; fn(g); root.add(g); sets[name] = g; };
  add("dining", (g) => dining(g, props));
  add("clinic", (g) => clinic(g, props));
  add("street", street);
  add("living", (g) => living(g, props));
  add("bath", bathroom);
  add("bank", bankSet);
  add("dock", dockSet);
  add("window", windowSet);
  // the two extra hero spots are only used by the cast; keep the references alive for world.ts
  void DINING; void CLINIC5;
  return { root, sets, props };
};
