// Four deep school zones as three.js geometry: the classroom (5 rows of desks, 4 ceiling fans, tall windows onto a
// 40 m courtyard), the 45 m locker hallway (neon floor line, hologram, stairs), the chemistry lab (black-marble
// benches, glass beakers, vent duct) and the 80 m plaza (two-storey facade, steps, police cars, news vans, heli).
// Hand-painted textures come from paint.ts; every surface material goes through shade.ts twoTone.
import * as THREE from "three";
import { twoTone } from "./shade";
import { NOINK } from "./ink";
import {
  woodFloor, tileFloor, wallPaint, blackboard, lockers, marble, asphalt, pavers, facade,
  periodic, sciencePoster, schoolSign, ceiling,
} from "./paint";
import { CLASS, HALL, LAB, COURT } from "./story";

const MATS = new Map<string, THREE.Material>();
export const lam = (key: string, make: () => THREE.MeshLambertMaterialParameters) => {
  const hit = MATS.get(key);
  if (hit) return hit as THREE.MeshLambertMaterial;
  const m = twoTone(new THREE.MeshLambertMaterial(make()));
  MATS.set(key, m);
  return m;
};
export const lit = (key: string, color: THREE.ColorRepresentation, k = 1) => lam(key, () => ({ color: new THREE.Color(color).multiplyScalar(k) }));

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
  props: Record<string, unknown>;
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
    gr.addColorStop(0, "rgba(255,255,255,0.9)"); gr.addColorStop(0.55, "rgba(255,255,255,0.4)"); gr.addColorStop(1, "rgba(255,255,255,0)");
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

const beam = (p: THREE.Object3D, from: THREE.Vector3, to: THREE.Vector3, rBase: number, color: string, opacity: number) => {
  const d = new THREE.Vector3().subVectors(from, to);
  const h = d.length();
  const geo = new THREE.ConeGeometry(rBase, h, 24, 1, true);
  const m = new THREE.MeshBasicMaterial({ map: beamTex(), color, transparent: true, opacity, depthWrite: false, side: THREE.DoubleSide,
    blending: THREE.AdditiveBlending, fog: false, toneMapped: false });
  const o = new THREE.Mesh(geo, m);
  o.position.copy(to).addScaledVector(d, 0.5);
  o.quaternion.setFromUnitVectors(new THREE.Vector3(0, 1, 0), d.clone().normalize());
  o.layers.set(NOINK);
  o.renderOrder = 2;
  p.add(o);
  return o;
};

const glowBall = (p: THREE.Object3D, x: number, y: number, z: number, r: number, color: string, k = 2.6) => {
  const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(color).multiplyScalar(k), fog: false, toneMapped: true });
  const o = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), m);
  o.position.set(x, y, z);
  o.layers.set(NOINK);
  p.add(o);
  return o;
};

const ceilingPlane = (g: THREE.Group, w: number, d: number, z0: number, y: number) => {
  const m = lam("ceilingTex", () => ({ map: tx("ceiling", () => ceiling("#d8d4cc")) }));
  const c = plane(g, w, d, m, 0, y, z0, 0, Math.PI / 2);
  c.castShadow = false; c.receiveShadow = false;
  return c;
};

// =====================================================================================
// CLASSROOM 14 x 24 x 5, windows on the left onto the courtyard
// =====================================================================================
const classroom = (g: THREE.Group, props: Record<string, unknown>) => {
  const floorM = lam("classFloor", () => ({ map: tx("classFloor", () => woodFloor("#9a7248", "#5e4028")) }));
  const f = plane(g, 14, 24, floorM, 0, 0, 12, 0, -Math.PI / 2);
  f.receiveShadow = true;
  ceilingPlane(g, 14, 24, 12, 5);
  // ceiling fixtures + cross beams so the top of frame reads as a real 3D ceiling
  const lampM = new THREE.MeshBasicMaterial({ color: new THREE.Color("#fff3d2"), toneMapped: true });
  for (let z = 3.0; z <= 21.0; z += 4.5) for (const x of [-3.3, 3.3]) {
    box(g, 3.4, 0.12, 0.46, lit("ceilFixture", "#e6e8e0"), x, 4.87, z);
    box(g, 3.2, 0.05, 0.34, lampM, x, 4.79, z);
  }
  for (const z of [6.6, 12.6, 18.6]) box(g, 14, 0.24, 0.34, lit("ceilBeam", "#cfc2a4"), 0, 4.8, z);
  const wallM = lam("classWall", () => ({ map: tx("classWall", () => wallPaint("#e8dcc0", "#cdbf9e")) }));
  // back wall + blackboard
  plane(g, 14, 5, wallM, 0, 2.5, 23.9, Math.PI);
  box(g, 7.4, 0.12, 0.14, lit("boardFrame", "#6a4a2c"), -0.6, 2.62, 23.74);
  box(g, 7.0, 2.5, 0.06, lit("board", "#203a30"), -0.6, 1.9, 23.7);
  plane(g, 6.9, 2.4, screenMat("boardTex", tx("boardTex", blackboard), 1.1), -0.6, 1.9, 23.66, Math.PI);
  // chalk tray + clock + speaker
  box(g, 7.0, 0.08, 0.2, lit("chalkTray", "#8a6a44"), -0.6, 0.62, 23.62);
  box(g, 0.9, 0.46, 0.08, lit("clockBody", "#181418"), 5.6, 3.7, 23.84);
  plane(g, 0.78, 0.38, screenMat("clockFace", tx("clockFace", () => {
    const c = document.createElement("canvas"); c.width = 256; c.height = 128; const q = c.getContext("2d")!;
    q.fillStyle = "#121418"; q.fillRect(0, 0, 256, 128);
    q.fillStyle = "#7fe4ff"; q.font = "700 76px 'Courier New', monospace"; q.textAlign = "center"; q.textBaseline = "middle"; q.fillText("09:41", 128, 68);
    const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
  }), 2.0), 5.6, 3.7, 23.78, Math.PI);
  // right wall with cabinets and the door opening
  const rw = plane(g, 24, 5, wallM, 7, 2.5, 12, -Math.PI / 2);
  rw.receiveShadow = true;
  for (let i = 0; i < 3; i++) {
    box(g, 0.42, 1.9, 2.6, lit("classCab", "#c8b48c"), 6.72, 0.95, 13 + i * 3.1);
    box(g, 0.05, 0.12, 0.4, lit("classCabHandle", "#7c6a4a"), 6.48, 1.1, 13 + i * 3.1);
  }
  // door frame + hinged leaf (world swings it on the lockdown kick)
  box(g, 0.16, 2.45, 0.18, lit("doorFrame", "#7a5a38"), 6.92, 1.22, 2.28);
  box(g, 0.16, 2.45, 0.18, lit("doorFrame", "#7a5a38"), 6.92, 1.22, 4.52);
  box(g, 0.16, 0.18, 2.4, lit("doorFrame", "#7a5a38"), 6.92, 2.42, 3.4);
  const doorPivot = new THREE.Group();
  doorPivot.position.set(6.86, 0, 2.36);
  const leafM = lam("classDoor", () => ({ color: new THREE.Color("#8a6a44") }));
  box(doorPivot, 0.1, 2.3, 1.05, leafM, 0, 1.16, 0.53);
  plane(doorPivot, 0.8, 1.0, lit("doorGlass", "#a8cce0"), 0.06, 1.6, 0.53, Math.PI / 2);
  box(doorPivot, 0.06, 0.06, 0.2, lit("doorKnob", "#d8b45a"), 0.08, 1.05, 0.95);
  g.add(doorPivot);
  props.classDoor = doorPivot;
  // left window wall: pillars + sills + glass; 5 tall windows
  const glassM = new THREE.MeshLambertMaterial({ color: new THREE.Color("#cfe6f2"), transparent: true, opacity: 0.22, side: THREE.DoubleSide });
  glassM.name = "windowGlass";
  const winZ = [3.0, 7.2, 11.4, 15.6, 19.8];
  for (let i = 0; i < winZ.length; i++) {
    const z = winZ[i];
    box(g, 0.25, 1.0, 3.4, wallM, -6.95, 0.5, z);
    box(g, 0.25, 0.8, 3.4, wallM, -6.95, 4.6, z);
    plane(g, 3.2, 3.2, glassM, -6.9, 2.6, z, Math.PI / 2);
    box(g, 0.12, 3.2, 0.1, lit("winMullion", "#f2ead8"), -6.84, 2.6, z);
    box(g, 0.12, 0.1, 3.2, lit("winMullion", "#f2ead8"), -6.84, 2.6, z);
    box(g, 0.5, 0.14, 3.6, lit("blindBox", "#e8e2d2"), -6.7, 4.28, z);
    for (let k = 0; k < 4; k++) box(g, 0.06, 0.05, 3.4, lit("blindSlat", "#d8d2c2"), -6.68, 3.95 + k * 0.1, z);
  }
  // wall bands below and between the windows close the left wall
  box(g, 0.26, 1.0, 26, wallM, -6.95, 0.5, 11.5);
  for (const zz of [5.1, 9.3, 13.5, 17.7, 21.9]) box(g, 0.26, 3.2, 0.9, wallM, -6.95, 2.6, zz);
  plane(g, 24, 0.8, wallM, -6.95, 4.6, 12, Math.PI / 2);
  // door-side wall segment (front) closes the frame behind the camera zone
  plane(g, 14, 5, wallM, 0, 2.5, 0.1, 0);
  // the beat-2/3 lens looks at this corner, so it carries the room's dressing: a board on the front wall and the
  // noticeboard + extinguisher cabinet on the wall beside the door. Without them the shot is a blank pink plane.
  box(g, 5.4, 0.12, 0.14, lit("boardFrame", "#6a4a2c"), 1.2, 2.62, 0.16);
  box(g, 5.0, 2.1, 0.06, lit("board", "#203a30"), 1.2, 1.95, 0.2);
  plane(g, 4.9, 2.0, screenMat("boardTexF", tx("boardTexF", blackboard), 1.1), 1.2, 1.95, 0.24, 0);
  box(g, 5.0, 0.08, 0.2, lit("chalkTray", "#8a6a44"), 1.2, 0.72, 0.32);
  // Two tall windows on the front wall, in the corner the beat-2/3 lens looks into, so the door shots finally have the
  // daylight-and-blur background the brief asks for. They are emissive panels set into the wall rather than real
  // openings: a real one means rebuilding this wall as sills and pillars, and the lens only ever sees it at a grazing
  // angle behind defocused cards.
  const dayM = new THREE.MeshBasicMaterial({ color: new THREE.Color("#e8f3ff") });
  dayM.name = "frontDay";
  for (const wx of [4.35, 6.05]) {
    plane(g, 1.5, 3.0, dayM, wx, 2.35, 0.14, 0);
    plane(g, 1.5, 3.0, glassM, wx, 2.35, 0.19, 0);
    box(g, 1.72, 0.12, 0.12, lit("winFrameF", "#f2ead8"), wx, 3.86, 0.22);
    box(g, 1.72, 0.14, 0.34, lit("winSillF", "#e8e2d2"), wx, 0.82, 0.3);
    box(g, 0.12, 3.1, 0.12, lit("winFrameF", "#f2ead8"), wx - 0.8, 2.35, 0.22);
    box(g, 0.12, 3.1, 0.12, lit("winFrameF", "#f2ead8"), wx + 0.8, 2.35, 0.22);
    box(g, 0.07, 3.0, 0.07, lit("winMullion", "#f2ead8"), wx, 2.35, 0.24);
    box(g, 1.5, 0.07, 0.07, lit("winMullion", "#f2ead8"), wx, 2.9, 0.24);
    box(g, 1.6, 0.14, 0.26, lit("blindBox", "#e8e2d2"), wx, 3.62, 0.3);
    for (let k = 0; k < 3; k++) box(g, 1.5, 0.05, 0.05, lit("blindSlat", "#d8d2c2"), wx, 3.34 + k * 0.1, 0.3);
  }
  // the stretch of right wall the door lens actually sees is z 0.3-3.9, so the noticeboard and the extinguisher
  // cabinet have to live there - at z 6.4/8.0 they sat behind the lens and never appeared in a single frame.
  plane(g, 1.5, 1.1, screenMat("noticeB", tx("noticeB", sciencePoster), 1.0), 6.8, 2.15, 1.35, -Math.PI / 2);
  box(g, 0.06, 1.2, 1.6, lit("noticeFrame", "#7c6a4a"), 6.83, 2.15, 1.35);
  box(g, 0.16, 1.0, 0.7, lit("extCab", "#c0392b"), 6.78, 1.35, 0.55);
  box(g, 0.04, 0.8, 0.55, lit("extCabGlass", "#d8e8f0"), 6.68, 1.35, 0.55);
  // -------- outside courtyard seen through the windows --------
  const lawn = lam("courtLawn", () => ({ map: tx("courtLawn", () => pavers()) }));
  const out = plane(g, 40, 56, lawn, -27, -0.02, 12, 0, -Math.PI / 2);
  out.receiveShadow = true;
  // far wing at 40 m with windows and columns
  const farM = lam("farWall", () => ({ map: tx("farWall", () => facade("#d8c8a8", "#b8a078")) }));
  box(g, 0.5, 9, 50, farM, -46, 4.5, 12);
  for (let i = 0; i < 10; i++) {
    box(g, 0.3, 1.6, 2.0, lit("farWin", "#8fb8d0"), -45.7, 5.2, -8 + i * 4.2);
    box(g, 0.34, 0.5, 2.3, lit("farWinFrame", "#f0e8d4"), -45.65, 6.2, -8 + i * 4.2);
  }
  for (let i = 0; i < 6; i++) cyl(g, 0.28, 0.34, 5.4, lit("farColumn", "#e8dcc4"), -43.4, 2.7, -6 + i * 7.2, 10);
  // trees + hedges outside
  for (const [x, z, s] of [[-17, 4, 1], [-24, 15, 1.2], [-33, 8, 0.9], [-20, 24, 1.1], [-36, 22, 1.3]] as const) {
    cyl(g, 0.22 * s, 0.3 * s, 2.4 * s, lit("outerTrunk", "#6a4a30"), x, 1.2 * s, z);
    for (const [dx, dy, dz, r] of [[0, 3.2, 0, 1.4], [-0.7, 2.8, 0.3, 1.0], [0.7, 2.9, -0.2, 1.0]] as const) {
      const sp = new THREE.Mesh(new THREE.SphereGeometry(r * s, 14, 10), lit("outerLeaf", "#4e7a3c"));
      sp.position.set(x + dx * s, dy * s, z + dz * s); sp.castShadow = true; g.add(sp);
    }
  }
  // hedges along the far walk
  box(g, 2.0, 0.9, 34, lit("hedge", "#3e6a34"), -40, 0.45, 12);
  // -------- desks: 5 rows x 4, hero desk row 2 --------
  const deskM = lam("deskTop", () => ({ map: tx("deskTop", () => woodFloor("#a87a4a", "#6a4828")) }));
  const legM = lit("deskLeg", "#4a4a52");
  const rowZ = [4.8, 7.7, 10.6, 13.5, 16.4];
  const colX = [-4.4, -1.5, 1.4, 4.3];
  const chairs: THREE.Group[] = [];
  for (let r = 0; r < rowZ.length; r++) for (let c = 0; c < colX.length; c++) {
    const x = colX[c], z = rowZ[r];
    box(g, 1.4, 0.06, 0.62, deskM, x, 0.76, z);
    for (const [dx, dz] of [[-0.62, -0.24], [0.62, -0.24], [-0.62, 0.24], [0.62, 0.24]] as const) cyl(g, 0.022, 0.026, 0.74, legM, x + dx, 0.37, z + dz);
    box(g, 0.5, 0.06, 0.46, deskM, x, 0.44, z + 0.05);
    // chair behind the desk
    const ch = new THREE.Group();
    box(ch, 0.46, 0.06, 0.46, lit("chairSeat", "#b06a32"), 0, 0.44, 0);
    // the sitter faces the desk (toward -z), so the back has to be on the +z side of the seat; at -0.21 it stood
    // between the desk and the card and cut the seated hero off at the chest
    box(ch, 0.46, 0.5, 0.06, lit("chairBack", "#8a4e26"), 0, 0.7, 0.21);
    for (const [dx, dz] of [[-0.18, -0.18], [0.18, -0.18], [-0.18, 0.18], [0.18, 0.18]] as const) cyl(ch, 0.02, 0.024, 0.44, legM, dx, 0.22, dz);
    ch.position.set(x, 0, z + 0.62);
    ch.traverse((o) => { const mm = o as THREE.Mesh; if (mm.isMesh) { mm.castShadow = true; mm.receiveShadow = true; } });
    g.add(ch);
    chairs.push(ch);
  }
  props.classChairs = chairs;
  // chairs[5] is the hero's own seat (desk -1.5, 7.7): it stays in the grid because the chair he lifts and slams
  // is drawn on his 2D hands, so there is no mesh to animate out of the row.
  // teacher desk + shelf
  box(g, 2.4, 0.9, 0.8, lit("teacherDesk", "#7a5a38"), -2.2, 0.45, 21.6);
  box(g, 2.5, 0.06, 0.9, lit("teacherDeskTop", "#9a7248"), -2.2, 0.92, 21.6);
  box(g, 0.7, 0.06, 0.5, lit("teacherBook", "#c84a4a"), -2.6, 0.98, 21.5);
  for (const x of [-2.9, -2.5]) box(g, 0.28, 1.9, 0.32, lit("bookStack", "#4a6a9a"), x, 0.95, 22.6);
  // posters + pipes along the right wall
  plane(g, 0.9, 1.2, lam("posterMat", () => ({ map: tx("poster", sciencePoster) })), 6.82, 2.3, 8.0, -Math.PI / 2);
  plane(g, 0.9, 1.2, lam("posterMat", () => ({ map: tx("poster", sciencePoster) })), 6.82, 2.3, 17.0, -Math.PI / 2);
  cyl(g, 0.06, 0.06, 14, lit("pipe", "#9aa4ac"), 6.85, 4.7, 12);
  // foreground furniture near the lens (blurred): a chair back in the aisle, a desk corner on the left
  // the aisle chair sits at x 2.0 z 5.55 - at 4.6/1.9 it stood straight behind the beat-2/3 actors and ate a
  // quarter of their ink; here it only ever enters the bottom band of the frame.
  const fg = new THREE.Group();
  box(fg, 0.5, 0.7, 0.5, lit("fgChair", "#8a4e26"), 2.0, 0.35, 5.55);
  box(fg, 1.3, 0.06, 0.6, deskM, -3.6, 0.76, 2.1);
  box(fg, 0.2, 3.6, 0.2, lit("fgPillar", "#d8c8a8"), -6.1, 1.8, 1.2);
  g.add(fg);
  // -------- ceiling fans --------
  const fans: THREE.Group[] = [];
  for (const z of [5.0, 10.0, 15.0, 20.0]) {
    const fan = new THREE.Group();
    fan.position.set(0, 4.35, z);
    cyl(fan, 0.03, 0.03, 0.7, lit("fanRod", "#7a7a80"), 0, 0.35, 0);
    const rotor = new THREE.Group();
    for (let i = 0; i < 4; i++) {
      const b = box(rotor, 1.5, 0.04, 0.22, lit("fanBlade", "#b8b0a0"), 0.8, 0, 0);
      b.rotation.y = (i * Math.PI) / 2;
    }
    cyl(rotor, 0.16, 0.13, 0.18, lit("fanHub", "#8a8a90"), 0, 0, 0);
    fan.add(rotor);
    rotor.userData.rotor = true;
    g.add(fan);
    fans.push(rotor);
  }
  props.fans = fans;
  // -------- alarm strobes (4 red globes + cones) --------
  const strobeGlows: THREE.Mesh[] = [];
  const strobeBeams: THREE.Mesh[] = [];
  for (const [x, z] of [[-5.8, 5.5], [5.8, 5.5], [-5.8, 14.5], [5.8, 14.5]] as const) {
    cyl(g, 0.16, 0.2, 0.18, lit("strobeBase", "#7a2028"), x, 4.86, z);
    const glow = glowBall(g, x, 4.74, z, 0.16, "#ff2a2a");
    glow.visible = false;
    strobeGlows.push(glow);
    const bm = beam(g, new THREE.Vector3(x, 4.7, z), new THREE.Vector3(x * 0.6, 1.0, z + 1.2), 1.9, "#ff2020", 0.16);
    bm.visible = false;
    strobeBeams.push(bm);
  }
  props.strobeGlows = strobeGlows;
  props.strobeBeams = strobeBeams;
  // red point light for the alarm (one, cheap)
  const red = new THREE.PointLight("#ff3a30", 0, 9);
  red.position.set(0, 4.2, 8);
  g.add(red);
  props.alarmLight = red;
  // school sign above the door
  plane(g, 2.4, 0.6, screenMat("schoolSign", tx("schoolSign", schoolSign), 1.0), 6.8, 3.4, 3.4, -Math.PI / 2);
};

// =====================================================================================
// HALLWAY 9 x 46: lockers, neon floor line, ceiling panels, stairs, hologram
// =====================================================================================
const hallway = (g: THREE.Group, props: Record<string, unknown>) => {
  const floorM = lam("hallFloor", () => ({ map: tx("hallFloor", () => tileFloor("#2a3446", "#222c3c", 8)) }));
  const f = plane(g, 9, 48, floorM, 0, 0, 20, 0, -Math.PI / 2);
  f.receiveShadow = true;
  ceilingPlane(g, 9, 48, 20, 4.4);
  const wallM = lam("hallWall", () => ({ map: tx("hallWall", () => wallPaint("#3a4658", "#28323f")) }));
  plane(g, 9, 4.4, wallM, 0, 2.2, 43.8, Math.PI);
  plane(g, 9, 4.4, wallM, 0, 2.2, -3.8, 0);
  // locker banks along both walls
  const lockMat = lam("lockers", () => ({ map: tx("lockers", () => lockers("#3f6a86", "#7fa8c0")) }));
  for (const s of [-1, 1]) {
    const b = box(g, 0.34, 2.2, 36, lockMat, s * 4.28, 1.1, 18);
    b.castShadow = false;
    for (let z = 2; z < 36; z += 6) box(g, 0.4, 0.1, 6, lit("lockerTrim", "#6f98b0"), s * 4.24, 2.2, z);
  }
  // benches + plants break the walls
  for (const z of [7, 15, 25]) {
    box(g, 0.5, 0.08, 2.2, lit("hallBench", "#5a4630"), -3.9, 0.48, z);
    for (const dz of [-0.9, 0.9]) box(g, 0.1, 0.48, 0.1, lit("hallBenchLeg", "#3a3020"), -3.9, 0.24, z + dz);
  }
  for (const [x, z] of [[3.6, 3.0], [-3.6, 11.0], [3.6, 28.0]] as const) {
    cyl(g, 0.34, 0.28, 0.5, lit("hallPot", "#8a5a40"), x, 0.25, z);
    for (let i = 0; i < 5; i++) {
      const leaf = new THREE.Mesh(new THREE.SphereGeometry(0.26, 10, 8), lit("hallLeaf", "#3e7a4a"));
      leaf.scale.set(0.7, 1.5, 0.7);
      leaf.position.set(x + (i - 2) * 0.14, 0.66 + (i % 2) * 0.16, z);
      g.add(leaf);
    }
  }
  // neon floor line + soft reflection
  const neon = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.4, 2.2, 3.0), toneMapped: true, fog: false });
  neon.name = "neon";
  for (const x of [-0.5, 0.5]) {
    const strip = plane(g, 0.06, 46, neon, x, 0.012, 20, 0, -Math.PI / 2);
    strip.castShadow = false;
    const glow = new THREE.MeshBasicMaterial({ color: new THREE.Color(0.25, 1.2, 1.9), transparent: true, opacity: 0.22, blending: THREE.AdditiveBlending, depthWrite: false, fog: false });
    const gp = plane(g, 0.7, 46, glow, x, 0.02, 20, 0, -Math.PI / 2);
    gp.layers.set(NOINK);
  }
  props.neon = neon;
  // receding ceiling panels
  for (let z = 1; z < 42; z += 3.2) {
    const m = new THREE.MeshBasicMaterial({ color: new THREE.Color(1.9, 1.8, 2.6), toneMapped: true, fog: false });
    plane(g, 1.1, 0.16, m, 0, 4.34, z, 0, Math.PI / 2);
  }
  // hologram pedestal + wireframe school
  const base = new THREE.Group();
  base.position.set(HALL.holoBase[0], 0, HALL.holoBase[2]);
  cyl(base, 0.62, 0.78, 0.3, lit("holoBase", "#1c2a3a"), 0, 0.15, 0, 24);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.72, 0.035, 8, 32), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.6, 2.4, 3.0), fog: false }));
  ring.rotation.x = Math.PI / 2; ring.position.y = 0.32; base.add(ring);
  const holo = new THREE.Group();
  holo.position.y = 1.85;
  const lineMat = new THREE.LineBasicMaterial({ color: new THREE.Color(0.5, 2.4, 3.2), transparent: true, opacity: 0.95, fog: false });
  const edgePts: number[] = [];
  const addBoxEdges = (cx: number, cy: number, cz: number, w: number, h: number, d: number) => {
    const e = new THREE.EdgesGeometry(new THREE.BoxGeometry(w, h, d));
    const pos = e.attributes.position;
    for (let i = 0; i < pos.count; i++) edgePts.push(pos.getX(i) + cx, pos.getY(i) + cy, pos.getZ(i) + cz);
    e.dispose();
  };
  addBoxEdges(0, 0, 0, 2.4, 1.5, 1.8);
  addBoxEdges(-0.9, 0.95, 0.2, 0.6, 0.5, 0.6);
  addBoxEdges(0.4, 1.05, -0.2, 0.9, 0.7, 0.9);
  addBoxEdges(0, -0.95, 0, 3.0, 0.12, 2.4);
  const geo = new THREE.BufferGeometry();
  geo.setAttribute("position", new THREE.Float32BufferAttribute(edgePts, 3));
  const lines = new THREE.LineSegments(geo, lineMat);
  lines.layers.set(NOINK);
  holo.add(lines);
  for (let i = 0; i < 3; i++) {
    const r = new THREE.Mesh(new THREE.TorusGeometry(1.6 + i * 0.22, 0.015, 6, 40), new THREE.MeshBasicMaterial({ color: new THREE.Color(0.4, 1.8, 2.6), transparent: true, opacity: 0.5, fog: false }));
    r.rotation.x = Math.PI / 2; r.position.y = -0.9 + i * 0.9; holo.add(r);
  }
  base.add(holo);
  props.holo = holo;
  g.add(base);
  // a cone of light above the hologram + glow
  beam(g, new THREE.Vector3(HALL.holoBase[0], 4.3, HALL.holoBase[2]), new THREE.Vector3(HALL.holoBase[0], 0.4, HALL.holoBase[2]), 1.5, "#40d8ff", 0.08);
  glowBall(g, HALL.holoBase[0], 3.2, HALL.holoBase[2], 0.12, "#6fe8ff", 2.0);
  // trophy case + noticeboard
  box(g, 1.2, 1.8, 0.3, lit("trophyCase", "#2a3a4a"), 4.1, 0.9, 21.0);
  glowBall(g, 4.0, 1.4, 20.9, 0.09, "#ffd88a", 1.6);
  plane(g, 1.6, 1.1, lit("notice", "#d8c8a0"), -4.1, 2.2, 24.0, Math.PI / 2);
  // stairs at the far end: 12 steps to a landing
  const stepM = lit("stepM", "#8a8e94");
  for (let i = 0; i < 12; i++) {
    box(g, 5.6, 0.2, 0.62, stepM, 0.6, 0.1 + i * 0.2, 33.2 + i * 0.62);
  }
  box(g, 5.6, 0.24, 3.0, stepM, 0.6, 2.5, 41.0);
  for (const s of [-1, 1]) {
    for (let i = 0; i < 12; i++) box(g, 0.08, 0.9, 0.08, lit("railPost", "#c8c4b8"), s * 2.8 + 0.6, 0.65 + i * 0.2, 33.2 + i * 0.62);
    box(g, 0.1, 0.1, 7.6, lit("rail", "#d8d4c8"), s * 2.8 + 0.6, 3.0, 37.0);
  }
  // upstairs balcony edges so the stairs read deep
  box(g, 9, 0.2, 0.4, lit("balcony", "#3a4658"), 0, 3.7, 43.2);
  // foreground locker corner + fire extinguisher near the lens
  box(g, 0.4, 2.4, 1.8, lockMat, -4.0, 1.2, 0.2);
  cyl(g, 0.14, 0.14, 0.7, lit("extBody", "#c02a2a"), 3.6, 0.35, 0.4);
  box(g, 0.24, 0.06, 0.24, lit("extTop", "#2a2a30"), 3.6, 0.72, 0.4);
};

// =====================================================================================
// LAB 14 x 26: black marble benches, beakers, vent duct, frost station
// =====================================================================================
const labSet = (g: THREE.Group, props: Record<string, unknown>) => {
  const floorM = lam("labFloor", () => ({ map: tx("labFloor", () => tileFloor("#c4d2d4", "#a6babd", 10)) }));
  const f = plane(g, 14, 26, floorM, 0, 0, 12, 0, -Math.PI / 2);
  f.receiveShadow = true;
  ceilingPlane(g, 14, 26, 12, 5.5);
  const wallM = lam("labWall", () => ({ map: tx("labWall", () => wallPaint("#c2d2d4", "#a2b6ba")) }));
  plane(g, 14, 5.5, wallM, 0, 2.75, 25.9, Math.PI);
  plane(g, 26, 5.5, wallM, -6.9, 2.75, 12, Math.PI / 2);
  plane(g, 26, 5.5, wallM, 6.9, 2.75, 12, -Math.PI / 2);
  plane(g, 14, 5.5, wallM, 0, 2.75, -1.9, 0);
  // ceiling strip lights flanking the ventilation duct
  const labLampM = new THREE.MeshBasicMaterial({ color: new THREE.Color("#e8fbff"), toneMapped: true });
  for (const z of [8, 14, 20]) for (const x of [-4.5, 4.5]) {
    box(g, 2.4, 0.1, 0.4, lit("labFixture", "#cfdadd"), x, 5.38, z);
    box(g, 2.2, 0.05, 0.3, labLampM, x, 5.31, z);
  }
  // periodic table + posters + shelves
  plane(g, 5.0, 2.4, screenMat("periodic", tx("periodic", periodic), 1.0), 0.2, 3.5, 25.8, Math.PI);
  plane(g, 0.9, 1.2, lam("posterMat2", () => ({ map: tx("poster2", sciencePoster) })), -5.0, 2.2, 25.8, Math.PI);
  box(g, 4.4, 0.08, 0.5, lit("labShelf", "#8a969c"), -3.2, 3.0, 23.4);
  for (let i = 0; i < 6; i++) box(g, 0.3, 0.5, 0.32, lit("labJar", "#c8d8d8"), -4.8 + i * 0.66, 3.3, 23.4);
  // fume hoods along the back
  for (const x of [-5.0, 4.6]) {
    box(g, 2.4, 2.6, 1.4, lit("hoodBody", "#b8c4c8"), x, 1.3, 24.0);
    box(g, 2.2, 1.2, 0.06, lit("hoodGlass", "#8fb8c8"), x, 1.9, 23.28);
    box(g, 2.2, 1.0, 1.1, lit("hoodBase", "#8a969c"), x, 0.5, 23.9);
  }
  // black-marble benches: three rows, split around the centre aisle
  const marbleM = lam("marble", () => ({ map: tx("marble", () => marble("#20242a", "#c8d0d8")) }));
  const legM = lit("labLeg", "#4a5258");
  for (const z of [6.0, 11.0, 16.0, 21.0]) {
    for (const x of [-3.4, 3.4]) {
      box(g, 5.2, 0.12, 1.2, marbleM, x, 0.92, z);
      box(g, 4.8, 0.06, 1.0, lit("benchUnder", "#2a3036"), x, 0.84, z);
      for (const dx of [-2.2, 2.2]) for (const dz of [-0.42, 0.42]) cyl(g, 0.05, 0.05, 0.9, legM, x + dx, 0.45, z + dz);
      // beakers + liquid
      for (let i = 0; i < 3; i++) {
        const bx = x - 1.5 + i * 1.4, bz = z + (i % 2 ? 0.18 : -0.12);
        const glass = new THREE.Mesh(new THREE.CylinderGeometry(0.11, 0.13, 0.34, 12, 1, true), new THREE.MeshLambertMaterial({
          color: new THREE.Color("#d8f2f6"), transparent: true, opacity: 0.35, side: THREE.DoubleSide }));
        glass.position.set(bx, 1.15, bz); g.add(glass);
        const liq = new THREE.Mesh(new THREE.CylinderGeometry(0.1, 0.12, 0.2, 12), new THREE.MeshBasicMaterial({
          color: new THREE.Color().setHSL(0.45 + i * 0.16, 0.75, 0.45).multiplyScalar(0.9), toneMapped: true }));
        liq.position.set(bx, 1.06, bz); g.add(liq);
      }
      // faucet + tray
      cyl(g, 0.03, 0.03, 0.4, lit("faucet", "#c8d4d8"), x + 1.9, 1.2, z);
      box(g, 0.5, 0.3, 0.4, lit("tray", "#a8b4b8"), x + 1.2, 1.14, z + 0.2);
    }
    // stools in the aisle
    for (const x of [-4.6, -2.2, 2.2, 4.6]) {
      cyl(g, 0.22, 0.2, 0.06, lit("stoolSeat", "#3a4248"), x, 0.7, z);
      cyl(g, 0.035, 0.035, 0.7, lit("stoolLeg", "#6a7478"), x, 0.35, z);
    }
  }
  // ventilation duct running the length of the ceiling, with the vent panel above the drop
  box(g, 1.1, 0.5, 24, lit("duct", "#9aa8ac"), 0, 5.05, 12);
  for (let z = 2; z < 24; z += 2) box(g, 1.2, 0.06, 1.0, lit("ductSeam", "#78888c"), 0, 5.32, z);
  const ventPivot = new THREE.Group();
  ventPivot.position.set(LAB.vent[0], 5.02, LAB.vent[2] - 0.55);
  box(ventPivot, 0.95, 0.06, 1.05, lit("ventPanel", "#c8d4d6"), 0, 0, 0.52);
  for (let i = 0; i < 5; i++) box(ventPivot, 0.8, 0.02, 0.05, lit("ventSlat", "#8a969c"), 0, -0.04, 0.16 + i * 0.18);
  g.add(ventPivot);
  props.ventPanel = ventPivot;
  // frost station: two blue tanks + a hose reel
  for (const x of [-5.6, 5.6]) {
    cyl(g, 0.36, 0.4, 1.6, lit("frostTank", "#5a9ab8"), x, 0.8, 3.0, 18);
    cyl(g, 0.1, 0.1, 0.16, lit("frostTop", "#c8e8f4"), x, 1.66, 3.0);
    glowBall(g, x, 1.5, 3.0, 0.08, "#9fe8ff", 1.4);
  }
  // wall poster clocks, emergency shower
  cyl(g, 0.03, 0.03, 1.1, lit("showerPipe", "#a8b4b8"), -6.6, 3.3, 19.0);
  cyl(g, 0.22, 0.22, 0.08, lit("showerHead", "#8a969c"), -6.3, 3.8, 19.0);
  // foreground bench end near the lens
  box(g, 1.0, 0.9, 0.8, marbleM, -5.4, 0.45, 4.0);
  cyl(g, 0.14, 0.14, 0.34, lit("fgBeaker", "#d8eef2"), -5.2, 1.06, 3.9);
};

// =====================================================================================
// COURTYARD 80 m: facade, steps, police, news, SWAT van, trees, helicopter
// =====================================================================================
const car = (g: THREE.Group, props: Record<string, unknown>, x: number, z: number, ry: number, body: string) => {
  const c = new THREE.Group();
  c.position.set(x, 0, z); c.rotation.y = ry;
  box(c, 4.2, 0.5, 1.9, lit("carBody" + body, body), 0, 0.72, 0);
  box(c, 1.9, 0.55, 1.75, lit("carCab" + body, body), -0.25, 1.22, 0);
  box(c, 1.6, 0.36, 1.78, lit("carGlass", "#1e2c3c"), -0.25, 1.28, 0);
  for (const [dx, dz] of [[-1.35, -0.95], [-1.35, 0.95], [1.3, -0.95], [1.3, 0.95]] as const) {
    mesh(c, new THREE.CylinderGeometry(0.34, 0.34, 0.22, 16), lit("tyre", "#1a1a1e"), dx, 0.34, dz, 0, Math.PI / 2);
  }
  const barR = box(c, 0.5, 0.14, 0.2, new THREE.MeshBasicMaterial({ color: new THREE.Color(3.0, 0.2, 0.2), toneMapped: true }), -0.25, 1.58, 0.45);
  const barB = box(c, 0.5, 0.14, 0.2, new THREE.MeshBasicMaterial({ color: new THREE.Color(0.2, 0.4, 3.0), toneMapped: true }), -0.25, 1.58, -0.45);
  barR.layers.set(NOINK); barB.layers.set(NOINK);
  (props.carBars as THREE.Mesh[]).push(barR, barB);
  // door stripe + light bar base
  box(c, 0.6, 0.32, 1.92, lit("carStripe", "#203048"), -0.4, 0.72, 0);
  box(c, 0.6, 0.12, 1.7, lit("carBarBase", "#2a2e34"), -0.25, 1.52, 0);
  g.add(c);
  return c;
};
const van = (g: THREE.Group, x: number, z: number, ry: number, color: string, dish: boolean) => {
  const v = new THREE.Group();
  v.position.set(x, 0, z); v.rotation.y = ry;
  box(v, 5.2, 2.1, 2.2, lit("vanBody" + color, color), 0, 1.35, 0);
  box(v, 1.4, 1.2, 2.14, lit("vanCab" + color, color), -2.9, 1.0, 0);
  box(v, 1.2, 0.6, 2.16, lit("vanGlass", "#26384a"), -3.0, 1.35, 0);
  for (const [dx, dz] of [[-2.8, -1.05], [-2.8, 1.05], [1.4, -1.05], [1.4, 1.05]] as const) {
    mesh(v, new THREE.CylinderGeometry(0.4, 0.4, 0.24, 16), lit("vanTyre", "#1a1a1e"), dx, 0.4, dz, 0, Math.PI / 2);
  }
  if (dish) {
    cyl(v, 0.06, 0.06, 0.8, lit("dishPole", "#c8ccd0"), 0.4, 2.8, 0);
    const d = new THREE.Mesh(new THREE.SphereGeometry(0.55, 16, 10, 0, Math.PI * 2, 0, Math.PI / 2), lit("dish", "#e8eaec"));
    d.rotation.x = -1.2; d.position.set(0.4, 3.2, 0.25); v.add(d);
  }
  g.add(v);
  return v;
};
const heli = (g: THREE.Group, props: Record<string, unknown>) => {
  const h = new THREE.Group();
  h.position.set(13, 11.5, 42);
  box(h, 3.2, 1.2, 1.3, lit("heliBody", "#203040"), 0, 0, 0);
  box(h, 1.2, 0.9, 1.1, lit("heliGlass", "#7fd8f0"), -1.5, 0.15, 0);
  box(h, 5.0, 0.22, 0.22, lit("heliTail", "#203040"), 3.2, 0.1, 0);
  box(h, 0.8, 1.0, 0.12, lit("heliFin", "#203040"), 5.4, 0.4, 0);
  for (const s of [-1, 1]) box(h, 2.6, 0.1, 0.1, lit("heliSkid", "#2a3a44"), 0, -0.75, s * 0.7);
  const rotor = new THREE.Group();
  rotor.position.set(0, 0.78, 0);
  for (let i = 0; i < 2; i++) { const b = box(rotor, 5.6, 0.05, 0.24, lit("heliRotor", "#181c22"), 0, 0, 0); b.rotation.y = (i * Math.PI) / 2; }
  h.add(rotor);
  const tail = new THREE.Group(); tail.position.set(5.4, 0.55, 0);
  for (let i = 0; i < 2; i++) { const b = box(tail, 0.05, 1.7, 0.16, lit("heliRotor", "#181c22"), 0, 0, 0); b.rotation.x = (i * Math.PI) / 2; }
  h.add(tail);
  props.heli = h; props.heliRotor = rotor; props.heliTail = tail;
  g.add(h);
};
const courtyard = (g: THREE.Group, props: Record<string, unknown>) => {
  const ground = lam("plaza", () => ({ map: tx("plaza", pavers) }));
  const f = plane(g, 90, 70, ground, 0, 0, 8, 0, -Math.PI / 2);
  f.receiveShadow = true;
  // driveway strip across the front
  plane(g, 90, 9, lam("asphalt", () => ({ map: tx("asphalt", asphalt) })), 0, 0.01, 9.5, 0, -Math.PI / 2);
  // facade: two storeys, 60 m wide, with projecting wings
  const facM = lam("facade", () => ({ map: tx("facade", () => facade("#d8c8a8", "#a88858")) }));
  box(g, 62, 11, 1.0, facM, 0, 5.5, 22.5);
  box(g, 64, 0.5, 1.6, lit("cornice", "#e8dcc0"), 0, 11.0, 22.0);
  for (const s of [-1, 1]) box(g, 12, 10, 6.0, facM, s * 24, 5.0, 20.0);
  // window grid
  for (let fx of [-26, -18, -10, 10, 18, 26]) for (let fy of [3.0, 7.3]) {
    box(g, 3.0, 2.2, 0.2, lit("cWinFrame", "#f0e8d4"), fx, fy, 21.9);
    box(g, 2.7, 1.9, 0.16, lit("cWinGlass", "#8fb8d0"), fx, fy, 21.8);
    box(g, 0.08, 1.9, 0.2, lit("cWinFrame", "#f0e8d4"), fx, fy, 21.7);
  }
  // main double doors + steps
  box(g, 7.4, 5.2, 0.5, lit("courtDoorFrame", "#e0d4bc"), 0, 2.6, 21.9);
  const doorL = new THREE.Group(); doorL.position.set(-3.4, 0, 21.6);
  const doorR = new THREE.Group(); doorR.position.set(3.4, 0, 21.6);
  for (const [dg, sx] of [[doorL, 1], [doorR, -1]] as const) {
    box(dg, 3.3, 4.6, 0.22, lit("courtDoor", "#4a6a7a"), sx * 1.65, 2.3, 0);
    box(dg, 1.8, 1.4, 0.06, lit("courtDoorGlass", "#a8d8e8"), sx * 1.65, 3.0, 0.14);
    g.add(dg);
  }
  props.courtDoorL = doorL; props.courtDoorR = doorR;
  for (let i = 0; i < 5; i++) box(g, 16 - i * 1.6, 0.18, 1.0, lit("steps", "#c8bca8"), 0, 0.09 + i * 0.18, 17.4 + i * 0.85);
  // columns framing the entrance
  for (const x of [-5.2, 5.2]) { cyl(g, 0.35, 0.42, 5.4, lit("courtCol", "#e8dcc4"), x, 2.7, 19.4, 12); box(g, 1.1, 0.25, 1.1, lit("courtCap", "#e8dcc4"), x, 5.5, 19.4); }
  // flagpole + school sign
  cyl(g, 0.1, 0.12, 9, lit("flagPole", "#c8ccd0"), -17, 4.5, 16, 10);
  plane(g, 2.4, 0.6, screenMat("courtSign", tx("courtSign", schoolSign), 1.1), 0, 6.4, 21.7, Math.PI);
  // trees around the plaza
  for (const [x, z, s] of [[-20, 12, 1.1], [20, 13, 1.2], [-28, 8, 1.0], [28, 7, 1.15], [-14, 20, 0.9], [15, 21, 1.0]] as const) {
    cyl(g, 0.24 * s, 0.32 * s, 2.6 * s, lit("courtTrunk", "#6a4a30"), x, 1.3 * s, z);
    for (const [dx, dy, dz, r] of [[0, 3.4, 0, 1.6], [-0.8, 3.0, 0.3, 1.1], [0.8, 3.1, -0.2, 1.1]] as const) {
      const sp = new THREE.Mesh(new THREE.SphereGeometry(r * s, 14, 10), lit("courtLeaf", "#4e7a3c"));
      sp.position.set(x + dx * s, dy * s, z + dz * s); sp.castShadow = true; g.add(sp);
    }
  }
  // police cars + lightbars
  props.carBars = [];
  car(g, props, COURT.carA[0], COURT.carA[2], 0.35, "#e8eef2");
  car(g, props, COURT.carB[0], COURT.carB[2], -0.45, "#e8eef2");
  // news vans
  van(g, COURT.vanA[0], COURT.vanA[2], 0.5, "#d8dce0", true);
  van(g, COURT.vanB[0], COURT.vanB[2], -0.4, "#c03a3a", true);
  // SWAT van
  van(g, 15.5, 16.5, -0.2, "#20242a", false);
  // barriers + kiosk
  for (const [x, z, r] of [[-4.6, 6.0, 0.1], [4.8, 5.6, -0.08], [-12, 5.0, 0.05]] as const) {
    box(g, 2.6, 1.0, 0.16, lit("barrier", "#d8dce0"), x, 0.55, z, r);
    for (const dx of [-1.0, 1.0]) box(g, 0.14, 0.55, 0.4, lit("barrierLeg", "#a8b0b8"), x + dx, 0.28, z, r);
  }
  // foreground barrier + traffic cone near the lens
  box(g, 3.2, 1.0, 0.18, lit("fgBarrier", "#e8ecf0"), -5.4, 0.55, 4.6, 0.2);
  for (const [x, z] of [[3.8, 4.2], [4.4, 4.6]] as const) {
    mesh(g, new THREE.ConeGeometry(0.22, 0.6, 12), lit("cone", "#e07a30"), x, 0.3, z);
    box(g, 0.4, 0.05, 0.4, lit("coneBase", "#20242a"), x, 0.025, z);
  }
  heli(g, props);
};

export const buildSets = (): Sets => {
  const root = new THREE.Group();
  const sets: Record<string, THREE.Group> = {};
  const props: Record<string, unknown> = {};
  const add = (name: string, fn: (g: THREE.Group, props: Record<string, unknown>) => void) => { const g = new THREE.Group(); g.name = name; fn(g, props); root.add(g); sets[name] = g; };
  add("classroom", classroom);
  add("hall", hallway);
  add("lab", labSet);
  add("court", courtyard);
  void CLASS; void LAB;
  return { root, sets, props };
};
