// 3D sets for InstantSkillShort (SKILL.md Section 4 + Hard Rules 8 and 9).
// Eight strictly isolated THREE.Group sets — a shot can never see a mesh belonging to another set, because world.ts
// publishes exactly one `root.visible = true` per shot id. Every coordinate the camera framing check needs lives in
// story.ts (SKATE / CHESS / CABIN / POKER / SNOW / HIGHWAY / BRAIN / ROAD); this file only builds meshes AT those
// coordinates.
//
//   SET_SKATE    shots 1-3   twilight city skatepark: lit apartment skyline, concrete stair set + steel rails,
//                            launch ramp, bench, three streetlamps with warm pools, four dark trees
//   SET_CHESS    shots 4-6   night chess lounge: the 14 m window band over the skyline is this set's luma, one
//                            canted tournament table, 3D board with the pinned black king, pendant over the felt
//   SET_CABIN    shot  7     night cabin: a 13.6 m fuselage tube the aisle camera stands INSIDE, two seats per side
//   SET_POKER    shot  8     high-stakes lounge: round felt under a low pendant, night window on the right flank,
//                            lit bar shelf exactly where the crane's top edge points
//   -- act 2/3 ---------------------------------------------------------------------------------------------
//   SET_SNOW     shots 11,
//                20-22       high-noon alpine basin: five real mountain masses ring a fog-carved piste because the
//                            four snow cameras face four different ways; a monstrous chunky avalanche wall traverses
//                            the +z face, the takeoff lip carries the launch line, the mound buries his friend
//   SET_HWY      shots 12-13 last light on 16 m of desert highway: an open-wheel car read from 42 cm off the tarmac
//                            AND from 2.25 m above, both guardrails, tyre stacks, four distant lit-window clusters
//   SET_BRAIN    shots 14-16 windowless neon chamber: one faceted soma is the only bright thing in the room, ten
//                            bent dendrites reach out of it, three memory screens hang angled in on the back wall
//   SET_ROAD     shots 23-25 suburban street at 02:14: a lit-window facade with a hinged door, one sodium lamp, an
//                            ordinary hatchback arriving off-frame left, then a disc and its beam in the dark
//
// v2 art direction: every easel, signboard, banner, scoreboard and placard is deleted. The stat readouts are HTML
// pills in InstantSkill.tsx, so the only text left in the picture is the subtitle line, and each set's brightness
// comes from lit windows and practical lamps instead of from painted white boards. There is no legible word or
// number on any mesh in this file: the painted plates from paint.ts carry window grids, seams, dials, waveforms and
// glyph-shaped stems, and every numeric readout the audience is meant to parse is an HTML pill.
import * as THREE from "three";
import { twoTone } from "./shade";
import { NOINK } from "./ink";
import { BRAIN, CABIN, CHESS, HIGHWAY, POKER, ROAD, SKATE, SNOW, type V3 } from "./story";
import {
  makeAngleReadTexture, makeAsphaltTexture, makeAvalancheTexture, makeBeamTexture, makeCabinWallTexture,
  makeCarPaintTexture, makeCashBandTexture, makeChessBoardTexture, makeConcreteTexture, makeDashTexture,
  makeFacadeTexture, makeGlowTexture, makeGreenFeltTexture, makeGlyphPlateTexture, makeHouseFrontTexture,
  makeLabFloorTexture, makeLoungeWallTexture, makeMembraneTexture, makeNeonPanelTexture, makeNightCityTexture,
  makePlasterTexture, makeRampStripeTexture, makeRidgeTexture, makeScreenTexture, makeSeatFabricTexture,
  makeSnowTexture, makeSprayTexture, makeStreakTexture, makeTileTexture, makeWoodFloorTexture,
} from "./paint";

type PieceKind = "king" | "pawn" | "rook";

const tex = (c: HTMLCanvasElement, rx = 1, ry = 1, aniso = 8) => {
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = THREE.SRGBColorSpace;
  t.wrapS = t.wrapT = THREE.RepeatWrapping;
  t.repeat.set(rx, ry);
  t.anisotropy = aniso;
  return t;
};
const mat = (t: THREE.Texture) => twoTone(new THREE.MeshLambertMaterial({ map: t }));
const solid = (col: string) => twoTone(new THREE.MeshLambertMaterial({ color: col }));
/** a practical lamp: lit glass the bloom pass can catch, emissive so it never goes dusk-dark with the sun */
const glowGlass = (col: string, glow: string, k = 1.8) => twoTone(new THREE.MeshLambertMaterial({
  color: col, emissive: new THREE.Color(glow), emissiveIntensity: k,
}));

type BoxOpts = { cast?: boolean; recv?: boolean };
const box = (w: number, h: number, d: number, m: THREE.Material, x: number, y: number, z: number, o: BoxOpts = {}) => {
  const g = new THREE.Mesh(new THREE.BoxGeometry(w, h, d), m);
  g.position.set(x, y, z);
  g.castShadow = o.cast ?? true;
  g.receiveShadow = o.recv ?? true;
  return g;
};
const plane = (w: number, h: number, m: THREE.Material, x: number, y: number, z: number, rx = 0, ry = 0) => {
  const g = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
  g.position.set(x, y, z);
  g.rotation.set(rx, ry, 0);
  g.receiveShadow = true;
  return g;
};
const cyl = (r: number, h: number, m: THREE.Material, x: number, y: number, z: number, seg = 20) => {
  const g = new THREE.Mesh(new THREE.CylinderGeometry(r, r, h, seg), m);
  g.position.set(x, y, z);
  g.castShadow = true; g.receiveShadow = true;
  return g;
};
const ball = (m: THREE.Material, r: number, x: number, y: number, z: number) => {
  const g = new THREE.Mesh(new THREE.SphereGeometry(r, 16, 12), m);
  g.position.set(x, y, z);
  g.castShadow = true;
  return g;
};

/**
 * Additive light pool — the golden circle under a streetlamp, the pendant's throw onto the felt. These are what
 * make "night with the lamps on" readable, and they sit on NOINK because the ink pass traces silhouette edges and
 * a soft quad has four of them: an inked glow pool draws a visible box on the ground.
 */
const glowPool = (rgb: string, w: number, h: number, x: number, y: number, z: number, opacity = 0.5, core = 0.7) => {
  const m = new THREE.MeshBasicMaterial({
    map: tex(makeGlowTexture(rgb, core)), transparent: true, opacity,
    blending: THREE.AdditiveBlending, depthWrite: false,
  });
  const g = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
  g.rotation.x = -Math.PI / 2;
  g.position.set(x, y, z);
  g.castShadow = false; g.receiveShadow = false;
  g.renderOrder = 4;
  g.layers.set(NOINK);
  return g;
};

/** two crossed planes, so a lamp head keeps its halo from every camera azimuth without needing to billboard */
const haloCross = (rgb: string, size: number, at: V3, opacity = 0.7) => {
  const g = new THREE.Group();
  const m = new THREE.MeshBasicMaterial({
    map: tex(makeGlowTexture(rgb, 0.85)), transparent: true, opacity,
    blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
  });
  for (const ry of [0, Math.PI / 2]) {
    const p = new THREE.Mesh(new THREE.PlaneGeometry(size, size), m);
    p.rotation.y = ry;
    p.renderOrder = 5;
    p.layers.set(NOINK);
    g.add(p);
  }
  g.position.set(at[0], at[1], at[2]);
  return g;
};

// ---------------- SET 1: TWILIGHT CITY SKATEPARK (shots 1-3) ----------------
export type SkateRefs = {
  root: THREE.Group;
  /** world.ts flexes this deck the frame the board pops off it */
  ramp: THREE.Group;
  /** the download pool under the hero: world.ts drives .material.opacity, so it has to stay one mesh */
  glow: THREE.Mesh;
};

/**
 * One apartment block: dark mass, a lit-window plate on the camera-facing (+z) wall, pale parapet coping. The
 * coping is the line that tells the audience where the roof is against the violet sky, which is the whole read
 * that v1's brick wall-to-wall background was missing.
 */
function cityBlock(b: { c: V3; w: number; h: number; d: number }, i: number, far: boolean) {
  const g = new THREE.Group();
  const wall = far ? "#241d38" : "#3b3050";
  const faceM = twoTone(new THREE.MeshLambertMaterial({
    map: tex(makeFacadeTexture({
      wall, glass: far ? "#171226" : "#221b33", lit: far ? "#ffd47a" : "#ffcf56",
      cols: Math.max(3, Math.round(b.w / (far ? 2.6 : 1.02))),
      rows: Math.max(2, Math.round(b.h / (far ? 3.4 : 1.42))),
      seed: 11 + i * 7,
    })),
  }));
  // the return walls get a plain windowless slab: only the +z face is ever seen, and a repeated facade there would
  // tile the same lit pattern around the corner
  const sideM = mat(tex(makeFacadeTexture({ wall, glass: wall, lit: wall, cols: 2, rows: 2, seed: 90 + i })));
  g.add(box(b.w, b.h, b.d, sideM, 0, b.h / 2, 0));
  const face = plane(b.w * 0.94, b.h * 0.94, faceM, 0, b.h / 2, b.d / 2 + 0.02);
  face.castShadow = false;
  g.add(face);
  g.add(box(b.w + 0.3, 0.26, b.d + 0.3, solid(far ? "#372c50" : "#4a3f63"), 0, b.h + 0.02, 0));
  if (!far) {
    g.add(box(0.9, 0.7, 0.9, solid("#332b46"), -b.w * 0.22, b.h + 0.48, -b.d * 0.2));
    g.add(box(0.06, 1.1, 0.06, solid("#5a5170"), b.w * 0.26, b.h + 0.58, b.d * 0.1));
  }
  g.position.set(b.c[0], 0, b.c[2]);
  return g;
}

function nightTree(p: V3, tilt: number) {
  const g = new THREE.Group();
  g.add(cyl(0.1, 1.85, solid("#2c2334"), 0, 0.92, 0, 8));
  const leaf = solid("#25373a");
  for (const [x, y, z, r] of [[0, 2.16, 0, 0.8], [0.4, 2.48, -0.16, 0.6], [-0.34, 2.62, 0.2, 0.54]] as [number, number, number, number][]) {
    const m = new THREE.Mesh(new THREE.IcosahedronGeometry(r, 1), leaf);
    m.position.set(x, y, z);
    m.castShadow = true;
    g.add(m);
  }
  g.position.set(p[0], 0, p[2]);
  g.rotation.z = tilt;
  return g;
}

/** post + reach-over arm + caged head, aimed at the pad so the pool of light falls where the action is */
function streetLamp(p: V3, aim: V3) {
  const g = new THREE.Group();
  const iron = solid("#33303c");
  g.add(cyl(0.24, 0.16, iron, 0, 0.08, 0, 14));
  g.add(cyl(0.085, 4.4, iron, 0, 2.2, 0, 10));
  g.add(box(0.075, 0.075, 0.95, iron, 0, 4.34, 0.46, { cast: false }));
  g.add(box(0.46, 0.14, 0.66, iron, 0, 4.26, 0.92));
  g.add(box(0.36, 0.05, 0.5, glowGlass("#fff2d2", "#ffc661", 2.2), 0, 4.18, 0.92, { cast: false }));
  g.add(haloCross("rgb(255,205,120)", 1.15, [0, 4.16, 0.92], 0.65));
  g.add(glowPool("rgb(255,190,105)", 3.9, 4.6, 0, 0.014, 1.5, 0.42, 0.6));
  g.position.set(p[0], 0, p[2]);
  g.rotation.y = Math.atan2(aim[0] - p[0], aim[2] - p[2]);
  return g;
}

function buildSkate(): SkateRefs {
  const root = new THREE.Group();
  root.name = "SET_SKATE";
  const S = SKATE;

  const conc = makeConcreteTexture("#c3bfb5", "#8b8579");
  const concreteM = mat(tex(conc, 10, 10));
  const stepM = mat(tex(conc, 2, 1));
  const asphaltM = mat(tex(makeAsphaltTexture(), 18, 18));
  const steel = solid("#7f7b88");
  const iron = solid("#3a3644");

  // ground: poured pad inside an asphalt apron, big enough that no camera ever finds the edge of the world
  root.add(plane(60, 60, asphaltM, 0, -0.02, 2, -Math.PI / 2));
  root.add(plane(15, 13, concreteM, 0.4, 0, 0.4, -Math.PI / 2));

  // skyline: six walk-ups at 12-16 m, three towers at 58-72 m, heights authored so every roofline keeps a strip of
  // sky above it inside a fov-45 vertical frame (see the SKATE.city comment in story.ts)
  S.city.forEach((b, i) => root.add(cityBlock(b, i, b.c[2] < -30)));

  // the stair set: two ledges plus a landing deck. SKATE.skater y 0.25 is the top of the first ledge, so the
  // onlooker is grounded on poured concrete rather than floating in front of it
  root.add(box(3.0, 0.25, 1.25, stepM, 0.55, 0.125, -1.55));
  root.add(box(3.0, 0.50, 0.90, stepM, 0.55, 0.25, -2.65));
  root.add(box(3.0, 0.75, 0.85, stepM, 0.55, 0.375, -3.52));
  // steel handrails down both flanks. rotation.x is POSITIVE because a +x rotation drops the +z end, i.e. the rail
  // rises as it recedes, which is what a stair rail has to do
  for (const rx of [-1.1, 2.2]) {
    const rail = box(0.06, 0.06, 3.09, steel, rx, 1.325, -2.4, { cast: false });
    rail.rotation.x = 0.245;
    root.add(rail);
    for (const [z, top, base] of [[-0.9, 0.95, 0.25], [-2.4, 1.325, 0.5], [-3.9, 1.7, 0.75]] as [number, number, number][]) {
      root.add(cyl(0.032, top - base, steel, rx, (top + base) / 2, z, 8));
    }
  }

  // launch ramp: canted deck, metal coping, striped face, turned away from the bench so the two never fuse
  const ramp = new THREE.Group();
  const deckM = mat(tex(makeRampStripeTexture(), 1, 1));
  const deck = plane(1.45, 1.95, deckM, 0, 0.6, 0.36);
  deck.rotation.x = -Math.PI / 2 + 0.86;
  ramp.add(deck);
  ramp.add(box(1.45, 0.9, 0.72, stepM, 0, 0.45, -0.3));
  ramp.add(box(1.45, 1.9, 0.1, stepM, 0, 0.45, 0.86, { cast: false }));
  const lip = cyl(0.05, 1.5, steel, 0, 1.1, -0.06, 10);
  lip.rotation.z = Math.PI / 2;
  ramp.add(lip);
  ramp.position.set(...S.ramp);
  ramp.rotation.y = -0.42;
  root.add(ramp);

  // bench
  const benchM = mat(tex(makeWoodFloorTexture("#6a5a4a", "#443a30"), 2, 1));
  root.add(box(1.6, 0.09, 0.44, benchM, S.bench[0], 0.46, S.bench[2]));
  root.add(box(1.6, 0.42, 0.08, benchM, S.bench[0], 0.72, S.bench[2] - 0.19, { cast: false }));
  for (const s of [-1, 1]) root.add(box(0.09, 0.46, 0.38, iron, S.bench[0] + s * 0.62, 0.23, S.bench[2]));

  for (const p of S.lamps) root.add(streetLamp(p, [0.2, 0, 1.2]));
  S.trees.forEach((p, i) => root.add(nightTree(p, i % 2 ? 0.05 : -0.05)));

  // the download pool: cyan because it is the SKILL lighting him up, not the street
  const glow = new THREE.Mesh(new THREE.PlaneGeometry(2.7, 2.4), new THREE.MeshBasicMaterial({
    map: tex(makeGlowTexture("rgb(86,226,255)", 0.6)), transparent: true, opacity: 0,
    blending: THREE.AdditiveBlending, depthWrite: false,
  }));
  glow.rotation.x = -Math.PI / 2;
  glow.position.set(S.hero[0], 0.016, S.hero[2] + 0.1);
  glow.renderOrder = 4;
  glow.layers.set(NOINK);
  root.add(glow);

  return { root, ramp, glow };
}

// ---------------- SET 2: CHESS LOUNGE (shots 4-6) ----------------
export type ChessRefs = {
  root: THREE.Group;
  /** origin sits at the piece's BASE so world.ts can hinge the tip-over */
  king: THREE.Group;
  cubeScrambled: THREE.Mesh;
  cubeSolved: THREE.Mesh;
  clockHand: THREE.Mesh;
  /** world.ts swings this pendant a hair while the clock runs, so the hall is never dead still */
  pendant: THREE.Group;
};

function makePiece(kind: PieceKind, col: string, h: number) {
  const g = new THREE.Group();
  const m = solid(col);
  g.add(cyl(0.042, 0.02, m, 0, 0.01, 0, 24));
  g.add(cyl(0.03, h * 0.62, m, 0, 0.02 + (h * 0.62) / 2, 0, 20));
  g.add(cyl(0.038, h * 0.1, m, 0, 0.02 + h * 0.62 + h * 0.05, 0, 20));
  if (kind === "king") {
    g.add(cyl(0.026, h * 0.16, m, 0, 0.02 + h * 0.72 + h * 0.08, 0, 18));
    g.add(box(0.012, h * 0.13, 0.012, m, 0, 0.02 + h * 0.9 + 0.01, 0));
    g.add(box(0.05, 0.012, 0.012, m, 0, 0.02 + h * 0.9 + 0.02, 0));
  } else if (kind === "rook") {
    for (let i = 0; i < 4; i++) {
      const a = (i / 4) * Math.PI * 2;
      g.add(box(0.014, h * 0.1, 0.014, m, Math.cos(a) * 0.026, 0.02 + h * 0.78, Math.sin(a) * 0.026));
    }
  } else {
    g.add(new THREE.Mesh(new THREE.SphereGeometry(0.026, 18, 14), m).translateY(0.02 + h * 0.72));
  }
  g.traverse((o) => { if ((o as THREE.Mesh).isMesh) { o.castShadow = true; o.receiveShadow = true; } });
  return g;
}

function buildChess(): ChessRefs {
  const root = new THREE.Group();
  root.name = "SET_CHESS";
  const C = CHESS;

  const floorM = mat(tex(makeWoodFloorTexture("#5f4526", "#3c2a16"), 6, 6));
  const plasterM = mat(tex(makePlasterTexture("#4c4258"), 4, 2));
  const panelM = mat(tex(makeWoodFloorTexture("#463022", "#2a1b12"), 1, 1));
  const brass = solid("#a8873f");

  root.add(plane(20, 20, floorM, 0, 0, 2.2, -Math.PI / 2));
  // back wall, and the window band 6 cm in front of it. With the banners deleted this plate IS the set's luma:
  // it runs 14 m wide because shot 4's view axis exits the wall at x -3.8 and shot 6's at x -1, and neither may
  // find a dark void at its frame edge.
  root.add(plane(20, 4.7, plasterM, 0, 2.35, -1.42));
  const band = plane(C.windowBand.hw * 2, C.windowBand.hh * 2,
    twoTone(new THREE.MeshLambertMaterial({ map: tex(makeNightCityTexture(5)) })), C.windowBand.c[0], C.windowBand.c[1], -1.36);
  band.castShadow = false;
  root.add(band);
  for (let i = -7; i <= 5; i++) {
    root.add(box(0.08, C.windowBand.hh * 2, 0.07, panelM, i * 1.16, C.windowBand.c[1], -1.3, { cast: false }));
  }
  for (const s of [1, -1]) {
    root.add(box(C.windowBand.hw * 2, 0.16, 0.09, panelM, C.windowBand.c[0], C.windowBand.c[1] + s * (C.windowBand.hh + 0.08), -1.3, { cast: false }));
  }
  // side walls far enough out that shot 4's camera at x 3.3 still stands inside the room
  for (const s of [-1, 1]) {
    const w = plane(15, 4.7, plasterM, s * 4.6, 2.35, 2.4);
    w.rotation.y = -s * Math.PI / 2;
    root.add(w);
    root.add(box(2.2, 2.7, 0.1, panelM, s * 4.5, 1.5, 3.4, { cast: false }));
  }
  root.add(plane(9.4, 15, plasterM, 0, 4.6, 2.4, -Math.PI / 2));
  root.add(box(20, 0.95, 0.08, panelM, 0, 0.47, -1.36, { cast: false }));
  root.add(box(3.6, 0.02, 2.6, mat(tex(makeGreenFeltTexture(), 2, 2)), -0.1, 0.011, 1.72, { cast: false }));

  // tournament table, canted 18 degrees so the three players read in depth instead of across. The 1.75 m width is
  // what keeps the 0.6 m board, the cube and the clock inside the rotated top.
  const [tw, td] = C.tableSize;
  const table = new THREE.Group();
  table.add(box(tw, 0.09, td, mat(tex(makeWoodFloorTexture("#6b4520", "#3d2612"), 2, 2)), 0, C.tableC[1] - 0.045, 0));
  for (const sx of [-1, 1]) for (const sz of [-1, 1]) {
    table.add(box(0.1, C.tableC[1] - 0.09, 0.1, panelM, sx * (tw / 2 - 0.14), (C.tableC[1] - 0.09) / 2, sz * (td / 2 - 0.14)));
  }
  table.add(box(tw * 0.88, 0.014, td * 0.34, mat(tex(makeGreenFeltTexture(), 3, 1)), 0, C.tableC[1] + 0.007, -0.3, { cast: false }));
  table.position.set(C.tableC[0], 0, C.tableC[2]);
  table.rotation.y = C.tableRot;
  root.add(table);

  const board = new THREE.Mesh(new THREE.BoxGeometry(0.6, 0.018, 0.6), mat(tex(makeChessBoardTexture())));
  board.position.set(C.board[0], C.board[1] + 0.009, C.board[2]);
  board.receiveShadow = true;
  root.add(board);

  const white = "#e8e2ce", black = "#1f1a20";
  const scatter: [PieceKind, string, number, number][] = [
    ["pawn", white, -0.18, -0.12], ["pawn", white, -0.06, -0.24], ["rook", white, -0.24, -0.24],
    ["pawn", black, 0.16, 0.1], ["pawn", black, 0.26, 0.02], ["rook", black, 0.28, 0.22],
  ];
  for (const [kind, col, ox, oz] of scatter) {
    const pc = makePiece(kind, col, kind === "pawn" ? 0.14 : 0.19);
    pc.position.set(C.board[0] + ox, C.board[1] + 0.018, C.board[2] + oz);
    root.add(pc);
  }

  const king = makePiece("king", black, 0.24);
  king.position.set(...C.king);
  root.add(king);

  const clockG = new THREE.Group();
  clockG.add(box(0.22, 0.09, 0.14, solid("#241f26"), 0, 0.045, 0));
  for (const s of [-1, 1]) {
    clockG.add(cyl(0.05, 0.02, solid("#e6dfd0"), s * 0.055, 0.1, 0, 20));
    const hand = box(0.008, 0.038, 0.008, brass, s * 0.055, 0.118, 0, { cast: false });
    if (s > 0) clockG.userData.hand = hand;
    clockG.add(hand);
  }
  clockG.position.set(...C.clock);
  root.add(clockG);
  const clockHand = (clockG.userData.hand as THREE.Mesh) ?? new THREE.Mesh();

  // the solved cube only appears once the 2D slam lands, so the two cubes never double up
  const cubeMats = (solved: boolean) => {
    const order = solved ? [0, 1, 2, 3, 4, 5] : [3, 0, 5, 2, 1, 4];
    const cols = ["#f4f0e4", "#e8b62c", "#c03a44", "#2a8a3c", "#2f5fae", "#d9741a"];
    return order.map((i) => solid(cols[i]));
  };
  const cubeGeo = new THREE.BoxGeometry(0.085, 0.085, 0.085);
  const cubeScrambled = new THREE.Mesh(cubeGeo, cubeMats(false));
  cubeScrambled.position.set(C.cubeRest[0], C.cubeRest[1], C.cubeRest[2]);
  cubeScrambled.rotation.y = 0.5;
  cubeScrambled.castShadow = true;
  cubeScrambled.visible = false;
  const cubeSolved = new THREE.Mesh(cubeGeo, cubeMats(true));
  cubeSolved.position.set(...C.cubeRest);
  cubeSolved.rotation.y = -0.32;
  cubeSolved.castShadow = true;
  cubeSolved.visible = false;
  root.add(cubeScrambled, cubeSolved);

  // pendant over the board. The group origin is the ceiling attach, so world.ts can swing it about the cord.
  const pendant = new THREE.Group();
  pendant.add(cyl(0.012, 2.1, brass, 0, -1.05, 0, 8));
  const shade = new THREE.Mesh(new THREE.ConeGeometry(0.32, 0.28, 22, 1, true),
    twoTone(new THREE.MeshLambertMaterial({ color: "#332c22", side: THREE.DoubleSide })));
  shade.position.y = -2.28;
  shade.castShadow = true;
  pendant.add(shade);
  pendant.add(ball(glowGlass("#fff0cc", "#ffbe6a", 1.9), 0.085, 0, -2.38, 0));
  pendant.add(haloCross("rgb(255,200,130)", 0.9, [0, -2.38, 0], 0.5));
  pendant.position.set(C.pendant[0], C.pendant[1] + 2.38, C.pendant[2]);
  root.add(pendant);
  root.add(glowPool("rgb(255,196,116)", 2.4, 2.4, C.tableC[0], C.tableC[1] + 0.055, C.tableC[2] + 0.1, 0.38, 0.66));

  return { root, king, cubeScrambled, cubeSolved, clockHand, pendant };
}

// ---------------- SET 3: NIGHT CABIN (shot 7) ----------------
export type CabinRefs = {
  root: THREE.Group;
  /** world.ts breathes this strip so the ceiling light is never dead flat */
  aisleLight: THREE.Mesh;
};

/** one economy seat. The pan sits 12 cm BEHIND the card plane it belongs to, so no seat lip ever draws across a
 *  2D figure's shins - a billboard card and a 3D seat at the same depth are a z-fight waiting to happen. */
function seatBlock(seatM: THREE.Material, shellM: THREE.Material, x: number, z: number, yaw: number) {
  const g = new THREE.Group();
  g.add(box(0.62, 0.12, 0.5, seatM, 0, 0.4, -0.12));
  g.add(box(0.62, 0.72, 0.12, seatM, 0, 0.82, -0.36));
  g.add(box(0.055, 0.3, 0.44, shellM, 0.31, 0.6, -0.1));
  g.add(box(0.055, 0.3, 0.44, shellM, -0.31, 0.6, -0.1));
  g.position.set(x, 0, z);
  g.rotation.y = yaw;
  return g;
}

function buildCabin(): CabinRefs {
  const root = new THREE.Group();
  root.name = "SET_CABIN";
  const B = CABIN;

  const panelM = mat(tex(makeCabinWallTexture(), 2, 2));
  const shellM = solid("#8f94a4");
  const ceilM = solid("#9aa0ae");
  const floorM = mat(tex(makeTileTexture("#5c6072", "#3d4152"), 4, 4));
  const seatM = mat(tex(makeSeatFabricTexture("#2f5f96"), 2, 2));
  const binM = solid("#7f8694");

  // the aisle lens stands at z 6.6, so the tube runs from the rear bulkhead at -2.6 all the way to 8.2: a camera
  // outside the fuselage would shoot straight through the ceiling and the shot would read as a cardboard box.
  root.add(plane(5.0, 13.6, floorM, 0, 0, 3.0, -Math.PI / 2));
  for (const s of [-1, 1]) {
    const w = plane(13.6, 2.9, panelM, s * 1.62, 1.35, 3.0);
    w.rotation.y = -s * Math.PI / 2;
    w.rotation.z = s * 0.05;
    root.add(w);
    for (let i = 0; i < 9; i++) {
      const z = 6.30 - i * 1.05;
      const win = plane(0.42, 0.56, twoTone(new THREE.MeshLambertMaterial({ map: tex(makeNightCityTexture(2 + i)) })), s * 1.56, 1.52, z);
      win.rotation.y = -s * Math.PI / 2;
      win.castShadow = false;
      root.add(win);
      const frame = new THREE.Mesh(new THREE.TorusGeometry(0.28, 0.035, 8, 20), shellM);
      frame.position.set(s * 1.53, 1.52, z);
      frame.rotation.y = Math.PI / 2;
      root.add(frame);
    }
    root.add(box(0.44, 0.38, 10.4, binM, s * 1.32, 2.12, 2.6));
    root.add(box(0.05, 0.05, 10.2, glowGlass("#f2f6ff", "#cfd9f2", 0.6), s * 1.06, 1.96, 2.6, { cast: false }));
  }
  root.add(plane(3.4, 13.6, ceilM, 0, 2.72, 3.0, -Math.PI / 2));
  root.add(box(3.4, 0.16, 13.6, shellM, 0, 2.66, 3.0, { cast: false }));

  // rear bulkhead, wider than the tube: at 9 m down the aisle a fov-46 frame is 4.4 m across, so a body-width
  // bulkhead would leave the frame corners looking through the aircraft into the sky
  root.add(plane(B.backWall.hw * 2, 2.9, panelM, B.backWall.c[0], 1.45, -2.62));
  root.add(box(3.2, 0.9, 0.45, binM, 0, 0.45, -2.4, { cast: false }));
  root.add(box(0.9, 1.5, 0.4, solid("#6d6350"), -1.9, 0.75, -2.4));

  const aisleLight = new THREE.Mesh(new THREE.BoxGeometry(0.18, 0.035, 9.4), glowGlass("#fffaf0", "#ffe2ab", 1.5));
  aisleLight.position.set(B.ceilStrip[0], B.ceilStrip[1], B.ceilStrip[2]);
  root.add(aisleLight);
  root.add(glowPool("rgb(255,226,176)", 1.5, 9.0, 0, 0.012, 1.4, 0.28, 0.55));

  // two seats per side on a 0.78 m pitch. Three slots are skipped: the hero's own seat, the passenger's, and the
  // one foreground seat that would otherwise stand between the lens and the hero's hands and eat the book fan.
  for (const r of [-1, 0, 1, 2, 3, 4]) for (const s of [-1, 1]) for (const col of [0.5, 1.3]) {
    if (col === 0.5 && ((r === -1 && s > 0) || (r === 0 && s > 0) || (r === 1 && s < 0))) continue;
    root.add(seatBlock(seatM, shellM, s * col, 1.62 - r * 0.78, s < 0 ? 0.05 : -0.05));
  }

  const heroSeat = seatBlock(seatM, shellM, B.hero[0], B.hero[2], -0.05);
  heroSeat.add(box(0.52, 0.05, 0.34, panelM, 0.02, 0.72, 0.2));
  root.add(heroSeat);
  const passSeat = seatBlock(seatM, shellM, B.passenger[0], B.passenger[2], 0.12);
  passSeat.add(cyl(0.16, 0.1, solid("#4a4e60"), 0, 0.52, 0.28, 12));
  root.add(passSeat);

  return { root, aisleLight };
}

// ---------------- SET 4: POKER LOUNGE (shot 8) ----------------
export type PokerRefs = {
  root: THREE.Group;
  cash: THREE.Mesh[];
  cards: THREE.Group;
  /** hung at K.lamp[1] (2.30) after the crane path was re-measured: at the old 1.62 the cone's silhouette landed on
   *  the far hero's face and read as a hat. 2.30 keeps the shade in frame for the whole crane with zero overlap on
   *  any of the three heads. */
  lamp: THREE.Mesh;
};

function buildPoker(): PokerRefs {
  const root = new THREE.Group();
  root.name = "SET_POKER";
  const K = POKER;

  const wallM = mat(tex(makeLoungeWallTexture(), 2, 1));
  const floorM = mat(tex(makeWoodFloorTexture("#4a3120", "#2c1c10"), 5, 5));
  const feltM = mat(tex(makeGreenFeltTexture(), 2, 2));
  const railM = solid("#37241a");
  const brass = solid("#a8873f");

  // the crane lens rises to 3.5 m at z 7.2, so the room is 18 m deep and 4 m tall or the move leaves the building
  root.add(plane(14, 18, floorM, 0.1, 0, 1.5, -Math.PI / 2));
  root.add(plane(8.2, 4.0, wallM, 0.1, 2.0, -3.5));
  for (const s of [-1, 1]) {
    const w = plane(18, 4.0, wallM, 0.1 + s * 3.34, 2.0, 1.5);
    w.rotation.y = -s * Math.PI / 2;
    root.add(w);
  }
  root.add(plane(6.8, 18, wallM, 0.1, 4.0, 1.5, -Math.PI / 2));

  // night window on the right flank, the cool vertical the crane's upper frame picks up
  const win = plane(K.windowBand.hw * 2, K.windowBand.hh * 2,
    twoTone(new THREE.MeshLambertMaterial({ map: tex(makeNightCityTexture(9)) })),
    K.windowBand.c[0], K.windowBand.c[1], K.windowBand.c[2]);
  win.rotation.y = -Math.PI / 2;
  win.castShadow = false;
  root.add(win);
  for (let i = -1; i <= 1; i++) {
    root.add(box(0.07, K.windowBand.hh * 2, 0.06, railM, K.windowBand.c[0] - 0.05, K.windowBand.c[1], K.windowBand.c[2] + i * 0.84, { cast: false }));
  }

  // bar shelf down the back wall, where the crane's top edge points: bottles plus a cove strip over them
  root.add(box(6.4, 0.86, 0.1, railM, 0.1, 0.43, -3.44, { cast: false }));
  root.add(box(3.4, 0.08, 0.34, brass, -1.5, 1.42, -3.3, { cast: false }));
  for (let i = 0; i < 8; i++) {
    const b = new THREE.Mesh(new THREE.CylinderGeometry(0.05, 0.062, 0.32, 12), solid(i % 2 ? "#7a4a20" : "#2f5d3a"));
    b.position.set(-2.9 + i * 0.4, 1.62, -3.3);
    b.castShadow = true;
    root.add(b);
  }
  root.add(box(3.6, 0.05, 0.09, glowGlass("#ffe3ac", "#ffb84e", 2.0), -1.5, 1.86, -3.32, { cast: false }));
  root.add(haloCross("rgb(255,190,110)", 1.5, [-1.5, 1.8, -3.2], 0.4));

  const table = new THREE.Group();
  const top = new THREE.Mesh(new THREE.CylinderGeometry(K.tableR, K.tableR, 0.1, 44), feltM);
  top.position.y = K.tableC[1] - 0.05;
  top.receiveShadow = true;
  table.add(top);
  const rail = new THREE.Mesh(new THREE.TorusGeometry(K.tableR - 0.03, 0.08, 10, 44), railM);
  rail.rotation.x = Math.PI / 2;
  rail.position.y = K.tableC[1] + 0.01;
  rail.castShadow = true;
  table.add(rail);
  table.add(cyl(0.17, K.tableC[1] - 0.1, railM, 0, (K.tableC[1] - 0.1) / 2, 0, 16));
  table.add(box(0.9, 0.07, 0.6, railM, 0, 0.035, 0, { cast: false }));
  table.position.set(K.tableC[0], 0, K.tableC[2]);
  root.add(table);

  const cards = new THREE.Group();
  const cardM = solid("#f2ece0");
  const backM = solid("#7e2130");
  for (let i = 0; i < 5; i++) {
    const c = new THREE.Mesh(new THREE.BoxGeometry(0.11, 0.006, 0.16), i % 2 ? cardM : backM);
    c.position.set(-0.3 + i * 0.15, 0, 0);
    c.rotation.y = (i - 2) * 0.06;
    c.castShadow = true;
    cards.add(c);
  }
  cards.position.set(K.cardRow[0], K.cardRow[1], K.cardRow[2]);
  root.add(cards);

  // six cash bundles whose tops world.ts raises out of the felt as the win lands
  const bandM = mat(tex(makeCashBandTexture(), 1, 1));
  const cash: THREE.Mesh[] = [];
  for (let i = 0; i < 6; i++) {
    const b = new THREE.Mesh(new THREE.BoxGeometry(0.2, 0.075, 0.13), bandM);
    const a = -0.62 + i * 0.25;
    b.position.set(K.cashRow[0] + a, K.cashRow[1] - 0.075, K.cashRow[2]);
    b.rotation.y = (i % 3 - 1) * 0.16;
    b.userData.slot = i;
    b.userData.x = K.cashRow[0] + a;
    b.userData.rot = b.rotation.y;
    cash.push(b);
    root.add(b);
  }

  // one chip stack in front of each of the three seats, for scale
  for (const [cx, cz] of [[K.hero[0], 0.85], [K.oppL[0], 1.92], [K.oppR[0], 1.88]] as [number, number][]) {
    for (let i = 0; i < 5; i++) {
      root.add(cyl(0.055, 0.022, solid(i % 2 ? "#b8302c" : "#e6dcc6"), cx, K.tableC[1] + 0.011 + i * 0.023, cz, 16));
    }
  }
  for (const [sx, sz] of K.snacks) {
    root.add(cyl(0.13, 0.03, solid("#d8cdb6"), sx, K.tableC[1] + 0.015, sz, 16));
    root.add(ball(solid("#c8641f"), 0.055, sx, K.tableC[1] + 0.09, sz));
  }

  // the pendant hangs from the ceiling (y 4.02) down to K.lamp[1]; the cord length is derived, never authored, so
  // raising the shade in story.ts cannot leave the cord floating or buried in the ceiling.
  const shadeTop = K.lamp[1] + 0.11;
  root.add(cyl(0.012, 4.02 - shadeTop, brass, K.lamp[0], (4.02 + shadeTop) / 2, K.lamp[2], 8));
  const lamp = new THREE.Mesh(new THREE.ConeGeometry(0.3, 0.22, 24, 1, true),
    twoTone(new THREE.MeshLambertMaterial({ color: "#2a2018", side: THREE.DoubleSide })));
  lamp.position.set(K.lamp[0], K.lamp[1], K.lamp[2]);
  lamp.castShadow = true;
  root.add(lamp);
  root.add(ball(glowGlass("#fff0cc", "#ffc06a", 2.1), 0.09, K.lamp[0], K.lamp[1] - 0.13, K.lamp[2]));
  root.add(glowPool("rgb(255,196,116)", 2.5, 2.5, K.tableC[0], K.tableC[1] + 0.055, K.tableC[2], 0.46, 0.66));

  return { root, cash, cards, lamp };
}

// ---------------- SET 5: HIGH-NOON ALPINE SNOW BASIN (shots 11, 20-22) ----------------
export type SnowRefs = {
  root: THREE.Group;
  /** THE avalanche, and it has to stay one mesh: world.ts slides the wall down the face by writing
   *  `aval.position.z` from SNOW.avalStartZ to SNOW.avalEndZ, so every tooth, crown lump and sheet of powder that
   *  must travel with it is a CHILD of this box rather than a sibling that would be left standing at the top of
   *  the face. The box is exactly SNOW.avalSize [40, 5.2, 5.0] because that is the cover quad the frame checker
   *  measures, centred on SNOW.avalY 2.6 so the rising piste buries its underside and the wall comes out of the
   *  slope it is sliding down instead of hovering in front of it. */
  aval: THREE.Mesh;
  /** the snow over the buried friend. Own origin is the authored SNOW.mound centre, because world.ts scales THIS
   *  at BREAK_AT and the cut has to open where the card is standing, not where the group happens to sit. About
   *  1.7 m across, crest just under 0.53, and a deliberate hollow in the middle so the drawn glove and the
   *  friend's head come UP out of it rather than through a wall of white. */
  mound: THREE.Group;
  /** eight ridgelines, one material apiece, in SNOW.ridges order: the ridge shot 20 reads straight up the +z face
   *  is not the ridge shot 11 looks past down the piste, and the checker measures a different silhouette out of
   *  each of them. Each entry is that ridge's ±z flank plate, the face every snow camera actually frames. */
  ridgeMats: THREE.Material[];
  /** additive powder sheets, ordered [wall-left, wall-right, wall-centre, landing]. Never share a material,
   *  because world.ts fades each sheet's own `material.opacity` - and the fourth is the puff he kicks up on the
   *  pad, authored at 0 so the landing zone stays clean until that frame. */
  spray: THREE.Mesh[];
};

/**
 * Deterministic value noise for scatter. Nothing in this file may use Math.random: Remotion shards frames across
 * worker processes and SKILL.md requires every frame to be a pure function of f, so a set that rebuilt itself
 * differently in shard 3 would move a rock between two renders of the same frame.
 */
const hash = (i: number, k = 0) => {
  const s = Math.sin(i * 127.1 + k * 311.7) * 43758.5453;
  return s - Math.floor(s);
};

/** one unit sphere, reused by every soft mass in the film (drift, mound, tooth, crown, outcrop). */
const LUMP_GEO = new THREE.SphereGeometry(1, 18, 12);
/** an ellipsoid at (x,y,z) with its three AXLE RADII given directly, so "1.7 m across" is two numbers you can read */
const lump = (m: THREE.Material, x: number, y: number, z: number, rx: number, ry: number, rz: number) => {
  const g = new THREE.Mesh(LUMP_GEO, m);
  g.position.set(x, y, z);
  g.scale.set(rx, ry, rz);
  g.castShadow = true;
  g.receiveShadow = true;
  return g;
};

/** an additive light sheet (spray, plume, hologram). Soft quads go on NOINK by hand: the ink pass traces silhouette
 *  edges, and a glow rectangle has four of them. */
const softSheet = (m: THREE.Material, w: number, h: number, x: number, y: number, z: number, order = 4) => {
  const g = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
  g.position.set(x, y, z);
  g.castShadow = false;
  g.receiveShadow = false;
  g.renderOrder = order;
  g.layers.set(NOINK);
  return g;
};
const addMap = (t: THREE.Texture, opacity: number, col = "#eef6ff") => new THREE.MeshBasicMaterial({
  map: t, color: col, transparent: true, opacity, blending: THREE.AdditiveBlending,
  depthWrite: false, side: THREE.DoubleSide,
});

/**
 * The basin's surface. Flat from -z up to 0.6 m past SNOW.landPad, which is the whole rescue band: shot 21's hero
 * stands at z 1.6 and lands at z 1.6, so his boots meet snow and never slope. Beyond it the face climbs toward +z
 * on a power curve that tops out at 8.5 m, so (a) the avalanche's authored underside is buried where it starts,
 * (b) the eight ridge boxes lose their sawn-off bottoms, and (c) shot 20, looking UP the face, sees a wall of snow
 * arriving instead of a board leaning on the sky.
 */
const snowRise = (z: number) => Math.min(8.5, Math.pow(Math.max(0, z - (SNOW.landPad[2] + 0.6)), 1.34) * 0.052);
/** snowRise' - the steepness of the face at z, uncapped, which is what a slab sitting ON the curve leans by */
const snowSlope = (z: number) => 1.34 * 0.052 * Math.pow(Math.max(0.001, z - (SNOW.landPad[2] + 0.6)), 0.34);

function buildSnow(): SnowRefs {
  const root = new THREE.Group();
  root.name = "SET_SNOW";
  const S = SNOW;

  const snowCv = makeSnowTexture("#f7faff", "#bad2ee");
  const fieldM = mat(tex(snowCv, 34, 34));          // 5 m tiles across the 170 m piste
  const driftM = mat(tex(snowCv, 1.6, 1.6));        // one ball, one drift: the uv covers the whole plate
  const paleM = solid("#f2f7fd");                    // the freshly blown crest line, the brightest thing on screen
  const rockM = solid("#645e70");
  const barkM = solid("#2c2630");
  const needleM = solid("#2e4a48");
  // dense old ice in the wall's crown: emissive by a hair, so it keeps its blue-white even on the shade side
  const iceM = twoTone(new THREE.MeshLambertMaterial({
    color: "#dceaf8", emissive: new THREE.Color("#7fa6c6"), emissiveIntensity: 0.22,
  }));

  // ---- the surface, and a valley floor under it so no lens ever finds the edge of the world ----
  const pisteGeo = new THREE.PlaneGeometry(170, 170, 44, 44).rotateX(-Math.PI / 2);
  const pa = pisteGeo.getAttribute("position") as THREE.BufferAttribute;
  for (let i = 0; i < pa.count; i++) pa.setY(i, snowRise(pa.getZ(i)));
  pisteGeo.computeVertexNormals();
  const piste = new THREE.Mesh(pisteGeo, fieldM);
  piste.receiveShadow = true;
  root.add(piste);
  root.add(plane(320, 320, driftM, 0, -0.12, 0, -Math.PI / 2));

  // ---- eight ridgelines, as real masses ----
  // A BoxGeometry's four side faces all run their uv v along world +y, and makeRidgeTexture paints v=1 as the
  // skyline parapet, v~0.85 as torn snow and v=0 as the apron - so one plate does the whole job: rock-streaked
  // snow up the flank, a bright band exactly where the ridge meets the sky, and a soft foot where it meets the
  // basin. The repeats are solved per face (rx = w/h keeps the canvas square on the wide faces) and clamped to
  // integers so no tile edge ever lands on a skyline. NOTHING here may stand above c[1]+h/2: that number is the
  // roofline scripts/is_frame.mjs measures for shots 11 and 20-22.
  const ridgeMats: THREE.Material[] = [];
  S.ridges.forEach((r, i) => {
    const cv = makeRidgeTexture({ rock: i % 2 ? "#6a6376" : "#77707f", snow: "#eff4fc", seed: 5 + i * 13 });
    const rx = Math.max(2, Math.round(r.w / r.h));
    const rz = Math.max(2, Math.round(r.d / r.h));
    const wide = mat(tex(cv, rx, 1));
    const deep = mat(tex(cv, rz, 1));
    const cap = mat(tex(cv, rx, rz));
    const mass = new THREE.Mesh(new THREE.BoxGeometry(r.w, r.h, r.d), [deep, deep, cap, deep, wide, wide]);
    mass.position.set(r.c[0], r.c[1], r.c[2]);
    mass.castShadow = false;
    mass.receiveShadow = false;
    root.add(mass);
    ridgeMats.push(wide);

    const top = r.c[1] + r.h / 2;
    for (const s of [-1, 1]) {
      // a protruding pale coping exactly at the skyline: this is the line that says "mountain", not "grey box"
      root.add(box(r.w + 0.5, 0.34, 0.46, paleM, r.c[0], top - 0.17, r.c[2] + s * (r.d / 2 - 0.12), { cast: false }));
      root.add(box(0.46, 0.34, r.d + 0.5, paleM, r.c[0] + s * (r.w / 2 - 0.12), top - 0.17, r.c[2], { cast: false }));
    }
    for (let k = 0; k < 4; k++) {
      const rr = 0.9 + hash(i * 17 + k, 3) * 1.5;
      // outcrops that stop short of the box top, so the authored silhouette is never exceeded
      root.add(lump(rockM,
        r.c[0] + (hash(i * 17 + k, 7) - 0.5) * r.w * 0.82,
        top - 0.06 - rr * (0.5 + hash(i * 17 + k, 11) * 2.4),
        r.c[2] + (hash(i * 17 + k, 13) - 0.5) * r.d * 0.7,
        rr * 1.35, rr * 0.62, rr));
    }
    // a bergschrund bank along all four foot lines, each lump sat ON snowRise so it is grounded where it stands:
    // this is what stops a 32 m mountain from ending in a sawn straight edge against the basin
    for (const s of [-1, 1]) {
      for (let k = 0; k < 4; k++) {
        const u = (k + 0.5) / 4;
        const bz = r.c[2] + s * (r.d / 2 + 0.3);
        root.add(lump(driftM, r.c[0] - r.w / 2 + u * r.w, snowRise(bz) + 0.08, bz,
          r.w / 8 + hash(i * 9 + k, 5) * 0.9, 0.62 + hash(i * 9 + k, 9) * 0.4, 1.5));
        const bx = r.c[0] + s * (r.w / 2 + 0.3);
        root.add(lump(driftM, bx, snowRise(r.c[2]) + 0.06, r.c[2] - r.d / 2 + u * r.d,
          1.5, 0.58 + hash(i * 9 + k, 2) * 0.4, r.d / 8 + hash(i * 9 + k, 6) * 0.8));
      }
    }
  });

  // ---- the avalanche ----
  const [aw, ah, ad] = S.avalSize;
  const avalCv = makeAvalancheTexture({ base: "#e9f2fd", core: "#9cc2e6", seed: 17 });
  // the leading face is 40 x 5.2 and the plate is 2:1, so four tiles of 10 m keeps the fluting near square
  const faceM = mat(tex(avalCv, 4, 1));
  const flankM = mat(tex(avalCv, 1, 1));
  // box material order is [+x, -x, +y, -y, +z, -z]: the crown and the leading edge carry the fluted face, because
  // those are the two surfaces every one of the four snow lenses is looking at.
  const aval = new THREE.Mesh(new THREE.BoxGeometry(aw, ah, ad),
    [flankM, flankM, faceM, flankM, flankM, faceM]);
  aval.position.set(S.hero[0], S.avalY, S.avalStartZ);   // world.ts takes z from SNOW.avalPos(f) every frame
  // A 40 m slab of snow casts a shadow the sun never reaches anyway - world.ts's shadow camera is a 24 m box
  // around the origin and this wall stands 26 m up the face - so castShadow stays off and the frame pays for the
  // teeth's silhouettes instead of for a shadow that lands outside every frustum in the shot.
  aval.castShadow = false;
  aval.receiveShadow = false;
  // the face is a curve, not a plane, so the slab leans by the slope ANGLE under its own foot. Without the lean an
  // axis-aligned box stands out of a 3.6 m deep cut with a visible step where the snow passes behind it; +x puts
  // the top back UPSLOPE, toward the mountain it broke from, which is also how a slab actually travels.
  aval.rotation.order = "ZXY";                            // yaw-pitch-roll, the same discipline as every vehicle
  aval.rotation.x = Math.atan(snowSlope(S.avalStartZ));
  aval.rotation.z = 0.07;                                 // 4 deg, so the leading edge is not dead parallel to the
  root.add(aval);                                         // crest line behind it (that fuse is the flat-wall look)
  for (let i = 0; i < 11; i++) {
    // chunky overlapping teeth across the front: a slab that broke into blocks on the way down, not a wall plane
    const tw = (aw / 11) * (0.74 + hash(i, 2) * 0.5);
    const th = ah * (0.42 + hash(i, 5) * 0.5);
    const td = 0.8 + hash(i, 8) * 1.3;
    const tx = -aw / 2 + (i + 0.5) * (aw / 11);
    const tooth = box(tw, th, td, faceM, tx, -ah / 2 + th / 2, -ad / 2 - td * 0.36);
    tooth.rotation.z = (hash(i, 12) - 0.5) * 0.09;
    tooth.rotation.y = (hash(i, 15) - 0.5) * 0.12;
    tooth.castShadow = false;
    aval.add(tooth);
    // the debris rumble riding in front of the foot, kept inside the authored height so the box still IS the quad
    aval.add(lump(driftM, tx + 1.2, -ah / 2 + 0.3, -ad / 2 - td - 0.3, tw * 0.7, 0.42, td * 0.55));
  }
  for (let i = 0; i < 7; i++) {
    // the crown: a torn lip of translucent ice standing over the face, and the hard highlight under it
    const cx = -aw / 2 + (i + 0.5) * (aw / 7);
    aval.add(lump(iceM, cx, ah / 2 - 0.2, -ad / 2 - 0.35, aw / 7 * 0.72, 0.55, 1.15));
  }
  aval.add(box(aw, 0.3, 0.5, paleM, 0, ah / 2 - 0.15, -ad / 2 - 0.2, { cast: false }));
  aval.add(softSheet(addMap(tex(makeGlowTexture("rgb(215,235,255)", 0.5)), 0.26), aw * 0.72, 3.4,
    0, ah / 2 - 0.5, -ad / 2 - 1.6, 4));

  // ---- the takeoff lip ----
  // The deck is one rotated box whose TOP plane contains the origin, and the group origin is SNOW.launch, so the
  // launch line is the surface he actually leaves from: centre = -u*(len/2) - n*(t/2) with u along the ramp and
  // n its up-normal. The run is 0.92 m, so the crest meets the ground exactly where shot 11's quad ends.
  const kicker = new THREE.Group();
  const kRun = 0.92;
  const kTh = Math.atan2(S.launch[1], kRun);
  const kLen = Math.hypot(S.launch[1], kRun) + 0.1;
  const kT = 0.36;
  const deck = box(kLen, kT, 2.7, driftM,
    -(kLen / 2) * Math.cos(kTh) + (kT / 2) * Math.sin(kTh),
    -(kLen / 2) * Math.sin(kTh) - (kT / 2) * Math.cos(kTh), 0);
  deck.rotation.z = kTh;
  kicker.add(deck);
  for (let i = 0; i < 3; i++) {
    const u = 0.2 + i * 0.3;
    kicker.add(lump(driftM, -u * kLen, -S.launch[1] * (1 - u) * 0.5 - 0.2, (i - 1) * 0.7,
      0.62, 0.42 + i * 0.1, 0.9));
  }
  // the rolled lip, its top exactly on the launch line, and the drop face behind it so the wedge has a shoulder
  const lip = cyl(0.075, 2.74, paleM, 0, -0.075, 0, 12);
  lip.rotation.x = Math.PI / 2;
  kicker.add(lip);
  kicker.add(box(0.1, S.launch[1] + 0.1, 2.7, driftM, 0.07, -S.launch[1] / 2 - 0.05, 0, { cast: false }));
  kicker.position.set(...S.launch);
  root.add(kicker);

  // ---- the conifers ----
  // One group for the whole stand so a sway is a single .rotation.z. SNOW.pines' authored y is the CANOPY BASE,
  // which is why each trunk length is solved from the piste rather than taken from the number.
  const pines = new THREE.Group();
  S.pines.forEach((p, i) => {
    const base = snowRise(p[2]);
    const trunk = Math.max(0.5, p[1] - base);
    const g = new THREE.Group();
    g.add(cyl(0.13, trunk, barkM, 0, base + trunk / 2, 0, 8));
    const tiers: [number, number, number][] = [[p[1] + 0.34, 0.95, 1.3], [p[1] + 1.06, 0.72, 1.1], [p[1] + 1.7, 0.45, 0.92]];
    for (const [cy, cr, ch] of tiers) {
      const cone = new THREE.Mesh(new THREE.ConeGeometry(cr, ch, 9), needleM);
      cone.position.set(0, cy + ch / 2, 0);
      cone.castShadow = true;
      g.add(cone);
      g.add(lump(paleM, 0, cy + ch * 0.14, 0, cr * 0.9, ch * 0.12, cr * 0.9));   // snow sitting on the branch skirt
    }
    g.position.set(p[0], 0, p[2]);
    g.rotation.y = hash(i, 4) * Math.PI * 2;
    pines.add(g);
    // A stationary skirt in `root`, OUTSIDE the swaying group: one .rotation.z on pines walks a tree at z 13.4 by
    // 26 cm, and a drift that does not move with it keeps the trunk foot covered either way.
    root.add(lump(driftM, p[0], base + 0.02, p[2], 1.1, 0.34, 0.95));
  });
  root.add(pines);

  // ---- the mound over his friend ----
  // five lumps, crest under 0.53 m and a deliberate hollow at the centre: the friend card is authored exactly on
  // this axis and sunk to SNOW.friendSunk, so what has to come through the snow is his drawn glove, not a wall of
  // white in front of it.
  const mound = new THREE.Group();
  mound.add(lump(driftM, 0, -0.24, 0, 0.84, 0.26, 0.84));
  mound.add(lump(driftM, -0.40, -0.02, -0.20, 0.44, 0.30, 0.40));
  mound.add(lump(driftM, 0.30, -0.06, -0.38, 0.42, 0.28, 0.38));
  mound.add(lump(driftM, 0.40, 0.0, 0.24, 0.42, 0.32, 0.38));
  mound.add(lump(driftM, -0.26, -0.04, 0.36, 0.40, 0.28, 0.36));
  mound.add(lump(driftM, 0.02, 0.0, 0.02, 0.30, 0.12, 0.30));   // the hollow's floor, sat 0.2 m below the crest
  mound.position.set(...S.mound);
  root.add(mound);

  // ---- spray: four sheets, one material each, in the order world.ts fades them ----
  const sprayCv = makeSprayTexture();
  const spray: THREE.Mesh[] = [];
  const plume = (w: number, h: number, x: number, y: number, z: number, tilt: number, op: number) => {
    const g = softSheet(addMap(tex(sprayCv), op), w, h, x, y, z, 4);
    g.rotation.x = tilt;
    spray.push(g);
    root.add(g);
    return g;
  };
  // the wall's own front throws 2-3 m of powder ahead of the teeth. The plumes are parked just downstage of
  // SNOW.avalEndZ, where the traverse finishes, so they read as the storm's leading edge in every frame of shot 20.
  plume(11.0, 4.4, -7.4, 1.7, S.avalEndZ + 1.5, -0.42, 0.24);
  plume(12.0, 4.8, 8.2, 1.9, S.avalEndZ + 2.1, -0.38, 0.24);
  plume(22.0, 5.6, 0.0, 1.5, S.avalEndZ + 0.7, -0.30, 0.2);
  plume(6.4, 2.6, S.landPad[0], 0.9, S.landPad[2] + 1.0, -0.2, 0);   // the puff he lands, driven at SNOW_LAND_AT

  // ---- the snow-angle read ----
  // Beside the mound, not over it: shot 22 tracks across the slope from az 40, and at 0.87 m off both card axes
  // this lands in the right third of the frame without ever standing in front of a drawn figure. Geometry only -
  // makeAngleReadTexture is an arc, a failure wedge, a tick ring and a hair cross, so the plate carries no word and
  // no number: the number the audience reads is the HTML pill over it.
  const angleRead = softSheet(addMap(tex(makeAngleReadTexture()), 0.62, "#bff2ff"), 0.66, 0.66,
    S.mound[0] - 0.86, S.mound[1] + 0.95, S.mound[2] + 0.2, 5);
  angleRead.rotation.y = 0.62;                       // turned to shot 22's azimuth band
  root.add(angleRead);

  return { root, aval, mound, ridgeMats, spray };
}

// ---------------- SET 6: DESERT HIGHWAY AT LAST LIGHT (shots 12-13) ----------------
export type HighwayRefs = {
  root: THREE.Group;
  /** the whole car. Its origin is the REAR AXLE on the ground plane and the group is authored at HIGHWAY.car with
   *  the nose toward +z: the dashes scroll toward -z, HIGHWAY.lights is the city he is driving AWAY from, and both
   *  race lenses (shot 12 at (3.02,0.42,5.48), shot 13 at (-1.71,2.25,5.46)) stand on the +z side, looking back at
   *  the front wing and down into the cockpit. So +z is forward. The cockpit tub, the steering rim and the four
   *  tyres are all children of THIS group, so world.ts's lean-in pitch/roll carries the driver with the chassis -
   *  order is the usual ZXY, because a roll written into a default XYZ Euler would tilt the pitch axis. */
  car: THREE.Group;
  /** the four road tyres, rear-left, rear-right, front-left, front-right. Each mesh carries NO rotation of its own:
   *  the axle is baked into the geometry (rotateZ 90 turns a cylinder's +y into +x), which is the only way
   *  `wheels[i].rotation.x` is an in-place spin. A mesh that had its axle baked as a .rotation.z instead would
   *  precess the tyre around the car's x axis - a steer, not a spin. Rims and spokes are children of their own
   *  tyre, so one write per wheel turns rubber and metal together. */
  wheels: THREE.Mesh[];
  /** the centre-line scroll: one mesh, one material, one texture instance, because world.ts writes
   *  `dash.material.map.offset.y` and a second material would have to be found and written too.
   *  makeDashTexture is exactly ONE HIGHWAY.stripeZ period painted along v and plane() lays v along world z, so
   *  repeat.y = length / stripeZ and the modulo the offset is taken under can never show a seam. */
  dash: THREE.Mesh;
  /** the motion streaks. There are four sheets, near to far, but they all share this mesh's material by design:
   *  `speed.material.opacity` is one write that brings the whole set up together, and the nearest sheet is the
   *  handle because it is the one that crosses the lens in shot 12. */
  speed: THREE.Mesh;
};

/** a flat additive sheet whose texture's U axis runs along world z: streaks are painted long in u, so the plain
 *  rotateX(-90) every other ground plane in this file uses would lay them ACROSS the road instead of down it. */
const flatLong = (m: THREE.Material, len: number, wide: number, x: number, y: number, z: number, order = 4) => {
  const g = new THREE.Mesh(new THREE.PlaneGeometry(len, wide).rotateZ(-Math.PI / 2), m);
  g.rotation.x = -Math.PI / 2;
  g.position.set(x, y, z);
  g.castShadow = false;
  g.receiveShadow = false;
  g.renderOrder = order;
  g.layers.set(NOINK);
  return g;
};

function buildHighway(): HighwayRefs {
  const root = new THREE.Group();
  root.name = "SET_HWY";
  const H = HIGHWAY;

  const asphaltM = mat(tex(makeAsphaltTexture(), 4, 44));
  const gritM = mat(tex(makeConcreteTexture("#a89276", "#7c6650"), 20, 40));
  const steelM = solid("#8d8a94");
  const railM = solid("#c9c4bb");
  const rubberM = solid("#1b1b22");
  const alloyM = solid("#9aa2ae");
  const bodyM = mat(tex(makeCarPaintTexture({ base: "#c8391f", accent: "#f4efe2", dark: "#7d2412" }), 1, 1));
  const carbonM = solid("#22242c");

  // 16 m of open road, and nothing within 40 m of it but desert. The tarmac sits 2 cm under zero so the dash
  // decal keeps its own plane even if world.ts writes the whole position vector every frame.
  root.add(plane((H.guardR - H.guardL) + 1.2, 92, asphaltM, 0, -0.02, 4, -Math.PI / 2));
  for (const s of [-1, 1]) {
    root.add(plane(26, 92, gritM, s * (H.guardR + 13.4), -0.04, 4, -Math.PI / 2));
    // a low mesa wall 24 m out, so the two race lenses never see the tarmac stop in mid-air
    root.add(box(9, 2.6, 74, gritM, s * 28.5, 1.2, 2, { cast: false }));
  }

  // ---- the scroll: one mesh, one material, one texture instance ----
  // repeat.x = 2 puts one column of dashes in each lane line, at +/- laneW/2, which is where the hero's card axis
  // sits between them. alphaTest rather than transparency: a blended ground plane sorted behind 92 m of tarmac is
  // a flicker waiting to happen, and a dash edge wants a hard cut anyway.
  const dashM = twoTone(new THREE.MeshLambertMaterial({ map: tex(makeDashTexture(), 2, 22), alphaTest: 0.5 }));
  const dash = plane(H.laneW * 2, 88, dashM, 0, 0.006, 4, -Math.PI / 2);
  dash.castShadow = false;
  root.add(dash);

  // ---- guardrails, tyre stacks, shoulder ----
  // guardL / guardR are authored, not eyeballed, and the rails run the full 88 m because shot 12's lens stands
  // 42 cm off the tarmac at z 5.48: a rail that ended before the frame edge would read as a painted line.
  const guard = new THREE.Group();
  for (const s of [-1, 1]) {
    for (const ry of [0.56, 0.84]) {
      guard.add(box(0.13, 0.13, 88, railM, s * H.guardR, ry, 2, { cast: false }));
    }
    guard.add(box(0.1, 0.16, 88, carbonM, s * H.guardR, 0.7, 2, { cast: false }));
    for (let i = -14; i <= 14; i++) {
      guard.add(box(0.09, 0.86, 0.09, steelM, s * H.guardR, 0.43, 2 + i * 3.1, { cast: false }));
    }
    // runoff: five tyre stacks a side, four high, on the far shoulder
    for (let k = 0; k < 5; k++) {
      const zz = -22 + k * 11;
      for (let t = 0; t < 4; t++) {
        const t2 = cyl(0.42, 0.3, rubberM, s * (H.guardR + 1.5), 0.15 + t * 0.31, zz, 16);
        t2.castShadow = false;
        guard.add(t2);
        guard.add(cyl(0.24, 0.32, solid("#2c2c36"), s * (H.guardR + 1.5), 0.15 + t * 0.31, zz, 12));
      }
    }
  }
  root.add(guard);

  // ---- the far city he is leaving ----
  // Four clusters at HIGHWAY.lights, each centred on its authored point so that y is the cluster's own mid-height:
  // the strip of glass sits low on the horizon, and at last light it is the only luma this shot has left.
  const cityLights = new THREE.Group();
  H.lights.forEach((p, i) => {
    const g = new THREE.Group();
    const cv = makeFacadeTexture({
      wall: "#241d33", glass: "#161225", lit: i % 2 ? "#ffcf56" : "#ffd47a",
      cols: 4 + i, rows: Math.max(2, Math.round(p[1] / 0.9)), seed: 31 + i * 6,
    });
    const glassM = mat(tex(cv, 1, 1));
    const sideM = solid("#1d1829");
    for (let k = 0; k < 3; k++) {
      const bw = 1.6 + hash(i * 7 + k, 2) * 2.4;
      const bh = p[1] * (1.2 + hash(i * 7 + k, 5) * 1.1);
      const bx = (k - 1) * (1.6 + hash(i * 7 + k, 9) * 1.2);
      g.add(box(bw, bh, bw * 0.8, sideM, bx, 0, 0));
      const face = plane(bw * 0.94, bh * 0.94, glassM, bx, 0, bw * 0.4 + 0.02);
      face.castShadow = false;
      g.add(face);
      g.add(box(bw + 0.2, 0.22, bw * 0.8 + 0.2, solid("#2f2743"), bx, bh / 2 - 0.1, 0, { cast: false }));
    }
    g.position.set(p[0], p[1], p[2]);
    cityLights.add(g);
  });
  root.add(cityLights);

  // ---- the car ----
  // Readable from 42 cm off the tarmac (shot 12, skimming the front wing) and from 2.25 m above (shot 13, looking
  // down into the tub), so the bodywork is layered in y: a wide flat floor, fat sidepods, a narrow engine cover
  // that steps up, and a wing at each end that reads against the road on its own.
  const car = new THREE.Group();
  const WB = 2.62;                       // wheelbase: the front axle lands under the nose, behind the front wing
  const TRACK = 1.62;
  car.add(box(0.9, 0.1, 2.5, carbonM, 0, 0.09, WB * 0.42));                    // floor / plank
  car.add(box(0.62, 0.3, 0.92, bodyM, 0, 0.4, 1.1));                           // nose
  car.add(box(0.34, 0.16, 0.62, bodyM, 0, 0.26, 1.9));                         // the cone tip ahead of the front axle
  car.add(box(1.66, 0.06, 0.5, bodyM, 0, 0.2, 2.42));                          // front wing main plane
  for (const s of [-1, 1]) {
    car.add(box(0.07, 0.3, 0.46, bodyM, s * 0.8, 0.3, 2.42));                  // endplate
    car.add(box(0.05, 0.24, 0.42, carbonM, s * 0.44, 0.32, 2.4, { cast: false }));
  }
  car.add(box(1.66, 0.05, 0.36, bodyM, 0, 0.44, 2.36, { cast: false }));       // wing flap
  for (const s of [-1, 1]) {
    car.add(box(0.44, 0.34, 1.06, bodyM, s * 0.6, 0.38, 0.16));                // sidepods
    car.add(box(0.36, 0.12, 0.3, carbonM, s * 0.6, 0.58, 0.5, { cast: false })); // intake
    // Dropped to 0.26..0.44, not 0.49..0.75. Shot 12 stands 42 cm up and 3.9 m ahead of the card, so the sight line
    // to the drawn fists passes this z band at y 0.47-0.49; at the old height the board lay exactly on it and, being
    // 0.9 m long along the view axis, it projected as a diagonal alloy streak across the driver's chest instead of a
    // fin beside the front wing. Below 0.44 it stays in the skim frame and out of the figure.
    car.add(box(0.06, 0.18, 0.9, alloyM, s * 0.85, 0.35, 0.9, { cast: false })); // barge board
    for (const sz of [0, WB]) {
      car.add(box(0.34, 0.06, 0.06, steelM, s * 0.55, 0.3, sz + 0.14, { cast: false }));
      car.add(box(0.06, 0.06, 0.5, steelM, s * 0.6, 0.36, sz - 0.1, { cast: false }));
    }
  }
  // 1.2 m deep ending at local z 0.05, so its forward face is 7 cm BEHIND the card axis at 0.12. At 1.3 it reached
  // 0.15 and its top-front corner therefore drew over the seated torso from both race lenses.
  car.add(box(0.46, 0.5, 1.2, bodyM, 0, 0.52, -0.55));                          // engine cover / gearbox
  car.add(box(0.34, 0.34, 0.42, bodyM, 0, 0.86, -0.26));                        // airbox behind the helmet
  car.add(box(1.5, 0.06, 0.44, bodyM, 0, 0.86, -1.0));                          // rear wing plane
  for (const s of [-1, 1]) car.add(box(0.06, 0.42, 0.5, bodyM, s * 0.74, 0.68, -1.0));
  car.add(box(0.7, 0.05, 0.2, carbonM, 0, 0.52, -1.06, { cast: false }));        // beam wing
  car.add(box(0.16, 0.5, 0.16, glowGlass("#ff7a5f", "#ff3a22", 2.0), 0, 0.62, -1.12, { cast: false })); // rain light
  // the roll hoop stands BEHIND the authored card axis, so from either race lens the card is in front of it and the
  // driver's helmet is never capped by 3D steel
  car.add(box(0.12, 0.14, 0.62, carbonM, 0, 1.06, -0.42));
  for (const s of [-1, 1]) car.add(box(0.1, 0.42, 0.1, carbonM, s * 0.3, 0.85, -0.6));
  car.position.set(...H.car);
  car.rotation.order = "ZXY";
  root.add(car);

  // ---- the four road tyres ----
  const axleGeo = (r: number, wide: number) => new THREE.CylinderGeometry(r, r, wide, 22).rotateZ(Math.PI / 2);
  const wheels: THREE.Mesh[] = [];
  for (const [sx, sz, r] of [[-1, 0, 0.35], [1, 0, 0.35], [-1, WB, 0.32], [1, WB, 0.32]] as [number, number, number][]) {
    const w = new THREE.Mesh(axleGeo(r, 0.3), rubberM);
    w.position.set(sx * (TRACK / 2), r, sz);
    w.castShadow = true;
    // outboard of the 0.30 m section by a hair, so the metal is actually seen and the spin is legible: a hub
    // buried inside the rubber would let the tyre turn with nothing in the frame proving it.
    const hub = new THREE.Mesh(axleGeo(r * 0.5, 0.05), alloyM);
    hub.position.x = sx * 0.155;
    hub.castShadow = false;
    w.add(hub);
    for (let k = 0; k < 5; k++) {
      const spoke = box(0.03, r * 0.86, 0.05, alloyM, sx * 0.15, 0, 0, { cast: false });
      spoke.rotation.x = (k / 5) * Math.PI;      // fanned in the wheel's own y-z plane, the plane at right angles
      w.add(spoke);                               // to the baked x axle
    }
    car.add(w);
    wheels.push(w);
  }

  // the rim he grips: authored at HIGHWAY.wheel, i.e. 0.46 m toward -z of his own card axis. That is deliberate -
  // under Rule A the fists are DRAWN, and at both race azimuths (38 deg and -24 deg) the rim lands 0.36-0.42 m
  // BEHIND the card plane, so the painted hands cover its hub and only the arcs peek past his silhouette.
  const rim = new THREE.Group();
  rim.add(new THREE.Mesh(new THREE.TorusGeometry(0.235, 0.032, 10, 26), carbonM));
  rim.add(cyl(0.055, 0.09, carbonM, 0, 0, 0.06, 14).rotateX(Math.PI / 2));
  for (const a of [0, Math.PI / 2, Math.PI / 4, -Math.PI / 4]) {
    const sp = box(0.36, 0.03, 0.03, alloyM, 0, 0, 0.02, { cast: false });
    sp.rotation.z = a;
    rim.add(sp);
  }
  for (const s of [-1, 1]) rim.add(box(0.07, 0.11, 0.05, solid("#2b2f3a"), s * 0.18, 0.16, 0.03, { cast: false }));
  rim.position.set(0, H.wheel[1], H.wheel[2] - H.car[2]);
  rim.rotation.y = Math.PI / 2;
  car.add(rim);

  // ---- the cockpit tub, on its authored seat plane ----
  // Built as a rim of walls, not a box: everything that could stand where the card is (x +/-0.29, y 0.30..2.1, the
  // swept slab between the two lenses' azimuths) is simply absent, and what is left is the floor he sits on, the
  // side walls outboard of his shoulders, the breastplate in front of the opening and the bulkhead behind it. The
  // opening stays visibly empty, which is the whole gag of shot 13: the body has given out mid-cockpit.
  // It lives INSIDE `car`, offset by hero - car, so the lean-in pitches the seat with the chassis and his feet
  // plane never slides out from under a card that world.ts is still pinning to HIGHWAY.hero.
  // The lip tops out at 0.57 m, not at the old 0.80, on purpose. seatDrop puts his hips on the 0.43 cushion, which
  // leaves the drawn fists at 0.61 and the shoulders at 0.80; a rim at 0.80 therefore hid the whole torso, the
  // wheel and the arms, and both race lenses rendered a helmet floating over the deck with nothing under it.
  const tub = new THREE.Group();
  tub.add(box(0.86, 0.06, 1.0, carbonM, 0, -0.03, 0));                  // floor = the authored seat plane
  for (const s of [-1, 1]) {
    tub.add(box(0.11, 0.26, 1.0, bodyM, s * 0.5, 0.1, 0));              // side walls, outboard of the card
    tub.add(box(0.13, 0.07, 1.02, alloyM, s * 0.5, 0.235, 0, { cast: false }));
  }
  tub.add(box(0.94, 0.24, 0.12, bodyM, 0, 0.09, 0.52));                  // breastplate, 0.5 m ahead of his hips
  tub.add(box(0.2, 0.14, 0.1, glowGlass("#d8f2ff", "#7fd8f0", 1.6), 0, 0.2, 0.46, { cast: false }));
  tub.add(box(0.9, 0.5, 0.1, carbonM, 0, 0.28, -0.5));                    // bulkhead behind the opening
  for (const s of [-1, 1]) tub.add(box(0.3, 0.16, 0.5, solid("#2b2f3a"), s * 0.28, 0.09, -0.32, { cast: false }));
  tub.position.set(0, H.hero[1], H.hero[2] - H.car[2]);
  car.add(tub);

  // ---- speed ----
  // Four sheets, near to far, all above the tarmac and all clear of the car's authored 0.95 m quad. The nearest
  // one is deliberately in front of the nose (z 4.1 against the front wing at z 3.9) because at 42 cm off the
  // ground the only thing that reads as 300 km/h is something crossing the lens.
  const streakCv = makeStreakTexture();
  const speedM = addMap(tex(streakCv), 0.42, "rgb(255,226,190)");   // ONE material, shared by every sheet
  const sheets: THREE.Mesh[] = [];
  for (const [z, y, w, len] of [[4.1, 0.16, 1.9, 26], [2.4, 0.1, 1.4, 22], [-1.4, 0.09, 1.2, 20],
    [-6.2, 0.12, 1.6, 24]] as [number, number, number, number][]) {
    const g = flatLong(speedM, len, w, 0, y, z, 5);
    sheets.push(g);
    root.add(g);
  }

  return { root, car, wheels, dash, speed: sheets[0] };
}
// ---------------- SET 7: WINDOWLESS NEURAL CHAMBER (shots 14-16) ----------------
export type BrainRefs = {
  root: THREE.Group;
  /** world.ts pulses this and turns it red at the overheat beat, so the body and its emissive channel stay one
   *  mesh. Emissive is written out here rather than going through mat(): a MeshLambertMaterial has the channel but
   *  ships at intensity 1, and that would blow the membrane map to white on frame 1. */
  core: THREE.Mesh;
  /** ten dendrites bent at a mid-joint, reaching from the soma out to dendriteR. A merged group, deliberately:
   *  nothing in here animates on its own, and every arm needs its own quaternion to be laid along its vector. */
  dendrites: THREE.Group;
  /** three memory screens, each on its OWN material and its own texture instance, because world.ts turns them on
   *  one at a time and a shared material would light them as a pair. */
  screens: THREE.Mesh[];
};

function buildBrain(): BrainRefs {
  const root = new THREE.Group();
  root.name = "SET_BRAIN";
  const B = BRAIN;
  const [rw, rh, rd] = B.roomSize;
  // The chamber is positioned off its FRONT face, not off the core: shot 14's pull-back rigs out to z 7.8, so the
  // floor and ceiling have to reach past that or the move starts the lens outside the room. Anchoring the front at
  // 8.2 and letting the authored 13.2 m depth run back puts the -z end at -5.0, one metre short of BRAIN.wall at
  // -6.0 - which is what lets that 16 x 9 plate BE the room's back face instead of a second coplanar wall behind it.
  const zc = 8.2 - rd / 2;

  const membraneM = mat(tex(makeMembraneTexture(), 5, 3));
  const frameM = solid("#232b3c");

  root.add(plane(rw, rd, mat(tex(makeLabFloorTexture(), 5, 5)), 0, B.floorY, zc, -Math.PI / 2));
  root.add(plane(rw, rd, solid("#161c2a"), 0, rh, zc, Math.PI / 2));
  // THREE faces, not four: the +z face is left open the way the cabin tube is left open for its aisle lens, because
  // shot 14 stands at (1.60, 2.55, 7.80) and shot 16 at (6.28, 2.60, 5.34). Any +z wall at all is a wall in front
  // of the camera, and a FrontSide-only one just hides the room from the side that is looking in.
  for (const s of [-1, 1]) {
    const wall = new THREE.Mesh(new THREE.PlaneGeometry(rd, rh), membraneM);
    wall.position.set(s * rw / 2, rh / 2, zc);
    wall.rotation.y = -s * Math.PI / 2;
    wall.receiveShadow = true;
    root.add(wall);
  }
  // BRAIN.wall. The only thing that may stand behind the hero in a room with no windows is more room. DoubleSide
  // because shot 16's lens grazes the 6.6 m side wall on its way into frame and would otherwise see the plate's
  // backface culled, i.e. void in the top corner.
  const backM = mat(tex(makeMembraneTexture(), 6, 4));
  backM.side = THREE.DoubleSide;
  const back = plane(B.wall.hw * 2, B.wall.hh * 2, backM, B.wall.c[0], B.wall.c[1], B.wall.c[2]);
  back.castShadow = false;
  root.add(back);
  for (let i = -3; i <= 3; i++) root.add(box(0.16, 4.0, 0.12, frameM, i * 2.3, 1.2, B.wall.c[2] + 0.13));

  // THE SOMA: the authored radius, low-poly on purpose. A 32-segment sphere reads as a ball; eight segments plus
  // flat shading reads as a faceted cell body, which is the one thing in this room that is not a plane.
  const core = new THREE.Mesh(new THREE.SphereGeometry(B.coreR, 9, 7), twoTone(new THREE.MeshLambertMaterial({
    map: tex(makeMembraneTexture(), 2, 1), flatShading: true,
    emissive: new THREE.Color("#1f6f86"), emissiveIntensity: 0.42,
  })));
  core.position.set(...B.core);
  core.castShadow = true;
  root.add(core);
  root.add(glowPool("rgb(126,226,244)", 6.6, 6.0, B.core[0], 0.016, B.core[2], 0.34, 0.5));

  // dendrites: two tapered lengths per arm with a kink at the joint, so ten of them read as growth rather than as
  // ten struts. The cylinder grows along +y, so the quaternion always comes from +y and never from the vector.
  const dendrites = new THREE.Group();
  const armM = mat(tex(makeMembraneTexture(), 1, 1));
  const dirs = [[0.0, 0.42, -1.0], [0.9, 0.32, -0.5], [-0.85, 0.4, -0.45], [0.25, -0.55, -0.8], [1.0, 0.05, 0.35],
    [-1.0, 0.1, 0.3], [0.4, 0.9, 0.2], [-0.4, 0.85, 0.3], [0.7, -0.42, 0.55], [-0.7, -0.4, 0.5]] as [number, number, number][];
  const up = new THREE.Vector3(0, 1, 0);
  dirs.forEach((d, i) => {
    const v = new THREE.Vector3(...d).normalize();
    const kink = new THREE.Vector3(d[0] + (i % 2 ? 0.55 : -0.55), d[1] + 0.3, d[2]).normalize();
    const len1 = B.dendriteR - B.coreR * 0.55 - (i % 3) * 0.42;
    const seg: [THREE.Vector3, number, number, number][] = [[v, 0.125, 0.07, len1 * 0.62], [kink, 0.07, 0.026, len1 * 0.38]];
    let at = new THREE.Vector3(...B.core).addScaledVector(v, -0.1);
    for (const [dir, r0, r1, len] of seg) {
      const arm = new THREE.Mesh(new THREE.CylinderGeometry(r1, r0, len, 9), armM);
      arm.quaternion.setFromUnitVectors(up, dir);
      arm.position.copy(at).addScaledVector(dir, len / 2);
      arm.castShadow = true;
      dendrites.add(arm);
      at = at.clone().addScaledVector(dir, len);
    }
    dendrites.add(ball(armM, 0.055, at.x, at.y, at.z));
  });
  root.add(dendrites);

  // three memory screens on their authored centres and yaws, HUNG from the ceiling on two rods each. They cannot be
  // wall mounts: the authored z of -3.35 is 1.65 m in front of the room's -5.0 back face, so a plate flush with the
  // wall would sit inside it.
  const screens: THREE.Mesh[] = [];
  for (const [i, sc] of B.screens.entries()) {
    const scrM = mat(tex(makeScreenTexture(i), 1, 1));
    scrM.side = THREE.DoubleSide;
    const scr = plane(sc.w, sc.h, scrM, sc.c[0], sc.c[1], sc.c[2]);
    scr.rotation.y = sc.rot;
    scr.castShadow = false;
    screens.push(scr);
    root.add(scr);
    root.add(box(sc.w + 0.24, sc.h + 0.24, 0.1, frameM, sc.c[0], sc.c[1], sc.c[2] - 0.07).rotateY(sc.rot));
    for (const o of [-1, 1]) {
      const top = rh - (rh - sc.c[1] - sc.h / 2);
      root.add(cyl(0.018, rh - sc.c[1] - sc.h / 2, frameM,
        sc.c[0] + o * (sc.w / 2 - 0.08) * Math.cos(sc.rot), sc.c[1] + sc.h / 2 + top / 2,
        sc.c[0] - o * (sc.w / 2 - 0.08) * Math.sin(sc.rot) - 0.02, 6));
    }
  }

  // a windowless room still has to carry luma, and the only honest sources left are the strips themselves. A camera
  // at 2.4-2.6 m inside a 6 m ceiling puts the wall-to-ceiling junction in the top third of every one of these
  // frames, so that third is either lit structure or it is black.
  for (const s of [-1, 1]) {
    root.add(box(0.09, 0.09, rd - 0.6, glowGlass("#dff4ff", "#8fd8ee", 2.1), s * (rw / 2 - 0.24), rh - 0.3, zc, { cast: false }));
    const strip = plane(rd - 1.0, 0.3, mat(tex(makeNeonPanelTexture(), 7, 1)), s * (rw / 2 - 0.2), rh - 0.34, zc);
    strip.rotation.y = -s * Math.PI / 2;
    strip.castShadow = false;
    root.add(strip);
  }
  root.add(box(rw - 0.6, 0.09, 0.09, glowGlass("#dff4ff", "#8fd8ee", 2.1), 0, rh - 0.3, zc - rd / 2 + 0.24, { cast: false }));
  root.add(haloCross("rgb(150,220,240)", 2.6, [B.core[0], B.core[1] + 0.1, B.core[2]], 0.4));

  return { root, core, dendrites, screens };
}

// ---------------- SET 8: SUBURBAN STREET, THEN THE BEAM (shots 23-25) ----------------
export type RoadRefs = {
  root: THREE.Group;
  /** the empty hatchback, built as a group that STARTS at ROAD.carIn. world.ts drives position and yaw through the
   *  arrival and parks it at carRest, so this stays a group and its wheels stay children of it. */
  car: THREE.Group;
  /** a squat disc of ROAD.ufoR with a lit dome and five rim lights. Its own y is what world.ts animates. */
  ufo: THREE.Group;
  /** THE curtain from the disc to the pavement: ONE transparent additive column, because world.ts rides ONE
   *  opacity through the whole abduction. */
  beam: THREE.Mesh;
  /** THE ground ellipse under it, centred on ROAD.beam, which is the point the hero stands in. */
  pool: THREE.Mesh;
  /** the sodium lamp's own bloom, separate from pool because the streetlight is ON from frame 0 and the beam is not */
  lampGlow: THREE.Mesh;
};

function buildRoad(): RoadRefs {
  const root = new THREE.Group();
  root.name = "SET_ROAD";
  const R = ROAD;

  const asphalt = mat(tex(makeAsphaltTexture(), 34, 34));
  const footway = mat(tex(makeConcreteTexture("#787686", "#4a4856"), 12, 12));
  const houseBody = mat(tex(makeConcreteTexture("#3a3340", "#241f28"), 3, 2));
  const trim = solid("#2b2530");

  root.add(plane(46, 46, asphalt, 0, 0, -1, -Math.PI / 2));
  for (const s of [-1, 1]) {
    root.add(box(7.0, 0.14, 46, footway, s * 7.4, 0.07, -1));
    // 30 cm is the height the beam foot and the car sill both have to clear, so the kerb is built to it exactly
    root.add(box(0.34, 0.3, 46, footway, s * 4.05, 0.15, -1));
    for (let i = -10; i <= 10; i++) root.add(box(0.34, 0.3, 0.14, trim, s * 4.05, 0.15, -1 + i * 2.2, { cast: false }));
  }

  // ONE house box at the authored centre and size. makeHouseFrontTexture paints window grids and lit panes and no
  // lettering of any kind, so it goes on the camera-facing +z wall only; the mass itself stays a plain slab,
  // because tiling the same lit bay pattern around the corner reads as a repeating backdrop.
  const [hw, hh, hd] = R.houseSize;
  const house = new THREE.Group();
  house.add(box(hw, hh, hd, houseBody, 0, hh / 2, 0));
  const front = plane(hw * 0.96, hh * 0.94, mat(tex(makeHouseFrontTexture({ base: "#443a44", board: "#2f2833", trim: "#8e8496" }), 1, 1)),
    0, hh / 2, hd / 2 + 0.02);
  front.castShadow = false;
  house.add(front);
  for (const s of [-1, 1]) {
    house.add(box(0.12, hh + 0.34, 0.12, trim, s * (hw / 2 + 0.06), (hh + 0.34) / 2, hd / 2 + 0.06));
    house.add(box(0.14, 0.14, hd + 0.2, trim, s * (hw / 2 + 0.04), hh + 0.06, 0));
  }
  // roof massing that is cropped by a metre at the top of shot 23's frame, which is the intended read: the lens
  // rigs to d 7.6 at az -64 and a 48 degree box is only 8.9 m tall at the house's 9.9 m distance, so a gable that
  // stayed inside the frame would push the facade down into the hero's head band. The pitch is not authored - it is
  // atan(rise / half-span) - and the rafter length is the hypotenuse, so the ridge meets the eaves at the corner
  // instead of overshooting the wall by 30 cm.
  const rise = 1.55;
  const halfSpan = hw / 4;
  const pitch = Math.atan(rise / halfSpan);
  const raftLen = Math.hypot(rise, halfSpan) + 0.34;
  const eaves = hh + 0.05;
  for (const s of [-1, 1]) {
    const raft = box(0.2, raftLen, hd + 0.7, trim, s * halfSpan, eaves + (raftLen / 2) * Math.cos(pitch), 0);
    raft.rotation.order = "ZXY";
    raft.rotation.z = s * pitch;
    house.add(raft);
  }
  house.add(box(0.22, 0.2, hd + 0.5, trim, 0, eaves + rise * Math.cos(pitch) + 0.1, 0));
  house.add(box(0.16, 0.62, 0.16, trim, -hw * 0.26, hh + 1.05, -hd * 0.2));
  // HINGED door: the slab is offset half its width inside its own group, so the group's origin is the hinge line
  // and a 2D card or a swing can be hung on it without the door sliding sideways off the facade.
  const door = new THREE.Group();
  door.add(box(0.98, 2.1, 0.14, solid("#5a3a2c"), 0.49, 1.05, 0));
  door.add(box(0.1, 0.1, 0.1, glowGlass("#ffe6b4", "#ffcf7a", 2.2), 0.86, 1.02, 0.09));
  door.position.set(R.door[0] - R.house[0], 0, R.door[2] - R.house[2] + 0.09);
  door.rotation.y = -0.12;
  house.add(door);
  house.add(box(1.24, 0.09, 0.5, footway, door.position.x + 0.5, 0.045, door.position.z + 0.3));
  house.position.set(...R.house);
  root.add(house);

  root.add(streetLamp(R.lamp, R.hero));
  // The lamp head is not at the post: streetLamp builds its reach arm along local +z and then yaws the whole group
  // toward the aim point, so the fadeable glow has to ride that same arm or it blooms 0.92 m off the wrong side of
  // the post. 4.16 is the head height the helper itself uses.
  const lampYaw = Math.atan2(R.hero[0] - R.lamp[0], R.hero[2] - R.lamp[2]);
  const lampGlow = plane(1.6, 1.6, new THREE.MeshBasicMaterial({
    map: tex(makeGlowTexture("rgb(255,205,120)", 0.8)), transparent: true, opacity: 0,
    blending: THREE.AdditiveBlending, depthWrite: false, side: THREE.DoubleSide,
  }), R.lamp[0] + 0.92 * Math.sin(lampYaw), 4.16, R.lamp[2] + 0.92 * Math.cos(lampYaw));
  lampGlow.renderOrder = 5;
  lampGlow.layers.set(NOINK);
  root.add(lampGlow);

  // EMPTY HATCHBACK. The arrival is authored as a straight line from carIn to carRest, so one yaw puts the nose on
  // it: dx 11.15, dz -2.85. Parked it ends up 2.35 m left of and 1.15 m behind the hero's own plane, which is the
  // point - it frames his back without ever sharing his silhouette column.
  const car = new THREE.Group();
  const paint = mat(tex(makeCarPaintTexture({ base: "#2b3550", accent: "#c9d3e4", dark: "#161c28" }), 1, 1));
  car.add(box(1.74, 0.52, 3.5, paint, 0, 0.5, 0));
  car.add(box(1.62, 0.42, 1.9, paint, 0, 0.96, -0.18));
  car.add(box(1.5, 0.34, 0.1, solid("#0f1420"), 0, 0.98, 0.86));
  car.add(box(1.5, 0.34, 0.1, solid("#0f1420"), 0, 0.97, -1.16));
  car.add(box(1.6, 0.14, 0.9, solid("#151a26"), 0, 1.22, -0.18));
  car.add(box(1.66, 0.18, 0.2, solid("#22252e"), 0, 0.36, 1.72));
  car.add(box(1.66, 0.18, 0.2, solid("#22252e"), 0, 0.36, -1.78));
  for (const [sx, sz] of [[-1, 1.14], [1, 1.14], [-1, -1.2], [1, -1.2]] as [number, number][]) {
    const w = cyl(0.31, 0.22, solid("#14141c"), sx * 0.78, 0.31, sz, 20);
    w.rotation.order = "ZXY";
    w.rotation.z = Math.PI / 2;
    car.add(w);
    car.add(cyl(0.13, 0.23, solid("#6b6f7c"), sx * 0.78, 0.31, sz, 12).rotateX(Math.PI / 2));
  }
  for (const s of [-1, 1]) {
    car.add(box(0.05, 0.5, 2.0, solid("#11141c"), s * 0.86, 0.5, 0, { cast: false }));
    car.add(box(0.1, 0.12, 0.32, paint, s * 0.92, 0.72, 0.6, { cast: false }));
    // door gap lines and nothing else: the crease is what makes the flank read as a car body rather than a capsule,
    // and there is no plate, decal or number anywhere on this car for the world to accidentally spell
    for (const sz of [-0.96, 0.26]) {
      car.add(box(0.05, 0.5, 0.03, solid("#10131a"), s * 0.875, 0.52, sz, { cast: false }));
    }
    car.add(box(0.28, 0.1, 0.06, glowGlass("#fff4dc", "#ffe6a8", 2.2), s * 0.6, 0.62, 1.78, { cast: false }));
    car.add(box(0.26, 0.12, 0.06, glowGlass("#ff6b5a", "#ff3a2a", 2.2), s * 0.62, 0.66, -1.86, { cast: false }));
  }
  car.position.set(...R.carIn);
  car.rotation.order = "ZXY";
  car.rotation.y = Math.atan2(R.carRest[0] - R.carIn[0], R.carRest[2] - R.carIn[2]);
  root.add(car);

  const ufo = new THREE.Group();
  const hullM = mat(tex(makeCarPaintTexture({ base: "#39404f", accent: "#8fa0b6", dark: "#191d27" }), 1, 1));
  ufo.add(cyl(R.ufoR, 0.5, hullM, 0, 0, 0, 40));
  ufo.add(cyl(R.ufoR * 0.86, 0.16, hullM, 0, -0.3, 0, 40));
  ufo.add(cyl(R.ufoR * 0.52, 0.42, twoTone(new THREE.MeshLambertMaterial({ color: "#101c24", side: THREE.DoubleSide })), 0, 0.42, 0, 28));
  const dome = ball(glowGlass("#c8f4ff", "#7fe6f8", 2.4), R.ufoR * 0.44, 0, 0.36, 0);
  dome.scale.y = 0.7;
  ufo.add(dome);
  for (let i = 0; i < 5; i++) {
    const a = (i / 5) * Math.PI * 2;
    ufo.add(ball(glowGlass("#dff6ff", "#8feaf8", 2.6), 0.13, Math.cos(a) * R.ufoR * 0.9, -0.24, Math.sin(a) * R.ufoR * 0.9));
  }
  ufo.position.set(...R.ufo);
  root.add(ufo);

  // THE BEAM: a truncated column, 0.34 m wide where it leaves the hull and 1.22 m where it reaches the pavement, on
  // ONE material because world.ts rides ONE opacity through the whole abduction. NOINK, because the ink pass traces
  // silhouette edges and an inked column draws a solid grey traffic cone. The 30 cm inset off the hull and the
  // 34 cm floor are both the kerb problem: the beam foot lands between the kerb line at |x| 4.2 and the far
  // footway, so a column that reached y 0 would bury its bottom rim in a 0.3 m slab and the flare would read as a
  // hole in the pavement instead of as light lying on it.
  const beamLow = 0.34;
  const beamHigh = R.ufo[1] - 0.3;
  const beamLen = beamHigh - beamLow;
  const beam = new THREE.Mesh(new THREE.CylinderGeometry(0.34, 1.22, beamLen, 26, 1, true), new THREE.MeshBasicMaterial({
    map: tex(makeBeamTexture(), 1, 1), transparent: true, opacity: 0, blending: THREE.AdditiveBlending,
    depthWrite: false, side: THREE.DoubleSide,
  }));
  beam.position.set(R.beam[0], beamLow + beamLen / 2, R.beam[2]);
  // no tilt anywhere in this column: the disc is built level, so the shaft drops straight onto ROAD.beam, and
  // ROAD.beam is the ground point the hero stands in. A lean would put the bright foot of the beam where he is not.
  beam.renderOrder = 5;
  beam.layers.set(NOINK);
  root.add(beam);
  // THE POOL under it. core 0.5 instead of the helper's 0.7: makeBeamTexture already bottoms out at 0.26 alpha, so
  // a hard centre would stack the two into a white dot at his feet.
  const pool = glowPool("rgb(226,244,255)", 3.1, 2.7, R.beam[0], 0.36, R.beam[2], 0, 0.5);
  root.add(pool);

  return { root, car, ufo, beam, pool, lampGlow };
}

// ---------------- assembly ----------------
export type WorldSets = {
  skate: SkateRefs; chess: ChessRefs; cabin: CabinRefs; poker: PokerRefs;
  snow: SnowRefs; highway: HighwayRefs; brain: BrainRefs; road: RoadRefs;
};

export function buildSets(): WorldSets {
  return {
    skate: buildSkate(), chess: buildChess(), cabin: buildCabin(), poker: buildPoker(),
    snow: buildSnow(), highway: buildHighway(), brain: buildBrain(), road: buildRoad(),
  };
}
