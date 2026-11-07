// 3D Set building for MolassesTankShort (SKILL.md Section 4 & Hard Rule 8):
// Three strictly isolated sets:
// 1. SET_TANK_STREET (Shot 1): Boston cobblestone street, boardwalk platform, massive 50-ft cylindrical
//    riveted steel tank with "PURITY DISTILLING / 2,000,000 GAL" banner, reactive bulging belly.
// 2. SET_CAB_BRAKE (Shot 2): Strictly isolated floor at y = 0, open streetcar cab platform,
//    "DANGER: 35 MPH WAVE" warning sign on upper left, 3D brass emergency brake lever and knob.
// 3. SET_AFTERMATH_PLAZA (Shot 3): Boardwalk plaza with chalkboard easel ("BOSTON HARBOR 1919 / 25 FT TALL / 35 MPH SYRUP WAVE"),
//    background elevated train trestle with tracks, red transit car, and surging 3D molasses wave.
import * as THREE from "three";
import { twoTone } from "./shade";
import {
  makeRivetedSteelTexture,
  makePurityDistillingBanner,
  makeCabWarningSign,
  makeEaselBoardTexture,
  makeCobblestoneTexture,
  makeWoodPlankTexture,
  makeTrainCarTexture,
} from "./paint";

export type Set1Refs = {
  root: THREE.Group;
  tankBulgeMesh: THREE.Mesh;
};

export type Set2Refs = {
  root: THREE.Group;
  leverBar: THREE.Mesh;
  leverKnob: THREE.Mesh;
  collar: THREE.Mesh;
  pedestalPos: [number, number, number];
};

export type Set3Refs = {
  root: THREE.Group;
  easel: THREE.Group;
  trainCar: THREE.Group;
  waveMesh: THREE.Object3D;
};

export type WorldSets = {
  set1: Set1Refs;
  set2: Set2Refs;
  set3: Set3Refs;
};

// ---------------- SHOT 1: TANK STREET ----------------
function buildSet1(
  steelTex: THREE.Texture,
  bannerTex: THREE.Texture,
  cobbleTex: THREE.Texture,
  woodTex: THREE.Texture
): Set1Refs {
  const root = new THREE.Group();
  root.name = "SET1_TANK_STREET";

  const cobbleMat = twoTone(new THREE.MeshLambertMaterial({ map: cobbleTex }));
  const woodMat = twoTone(new THREE.MeshLambertMaterial({ map: woodTex }));
  const steelMat = twoTone(new THREE.MeshLambertMaterial({ map: steelTex }));
  const bannerMat = twoTone(new THREE.MeshLambertMaterial({ map: bannerTex }));
  const darkSteelMat = twoTone(new THREE.MeshLambertMaterial({ color: "#22252a" }));
  const ironTrimMat = twoTone(new THREE.MeshLambertMaterial({ color: "#16181b" }));

  // 1. Cobblestone street ground plane
  const streetGeo = new THREE.PlaneGeometry(36, 28);
  const streetMesh = new THREE.Mesh(streetGeo, cobbleMat);
  streetMesh.rotation.x = -Math.PI / 2;
  streetMesh.position.set(0, -0.05, 4.0);
  streetMesh.receiveShadow = true;
  root.add(streetMesh);

  // 2. Right wooden boardwalk platform for Inspector (x ~ 1.4, z ~ 3.8, y = 0)
  const walkGeo = new THREE.BoxGeometry(2.4, 0.15, 4.0);
  const walkMesh = new THREE.Mesh(walkGeo, woodMat);
  walkMesh.position.set(1.4, 0.0, 3.8);
  walkMesh.receiveShadow = true;
  root.add(walkMesh);

  // 3. Massive Cylindrical Riveted Steel Storage Tank (radius ~ 3.6m, height ~ 8.5m)
  // Base concrete / granite foundation ring
  const fndGeo = new THREE.CylinderGeometry(3.75, 3.85, 0.6, 32);
  const fndMesh = new THREE.Mesh(fndGeo, ironTrimMat);
  fndMesh.position.set(0, 0.3, 0);
  root.add(fndMesh);

  // Main lower cylinder body (y: 0.6..2.5)
  const lowerGeo = new THREE.CylinderGeometry(3.6, 3.6, 2.0, 32);
  const lowerMesh = new THREE.Mesh(lowerGeo, steelMat);
  lowerMesh.position.set(0, 1.6, 0);
  root.add(lowerMesh);

  // Reactive Bulging Belly Segment (y: 2.5..5.5) — scales outward when pressure builds
  const bulgeGeo = new THREE.CylinderGeometry(3.62, 3.62, 3.0, 32);
  const tankBulgeMesh = new THREE.Mesh(bulgeGeo, steelMat);
  tankBulgeMesh.position.set(0, 4.1, 0);
  root.add(tankBulgeMesh);

  // Upper cylinder body (y: 5.5..8.5)
  const upperGeo = new THREE.CylinderGeometry(3.6, 3.6, 3.0, 32);
  const upperMesh = new THREE.Mesh(upperGeo, steelMat);
  upperMesh.position.set(0, 7.0, 0);
  root.add(upperMesh);

  // Reinforcing horizontal steel ring ribs
  for (const ry of [1.6, 2.6, 5.6, 7.0, 8.4]) {
    const ringGeo = new THREE.TorusGeometry(3.63, 0.045, 8, 32);
    const ringMesh = new THREE.Mesh(ringGeo, ironTrimMat);
    ringMesh.rotation.x = Math.PI / 2;
    ringMesh.position.set(0, ry, 0);
    root.add(ringMesh);
  }

  // Upper Sign Banner: "PURITY DISTILLING / 2,000,000 GAL"
  // Mounted cleanly on front curve facing camera (+z), curved or angled slightly
  const signGeo = new THREE.PlaneGeometry(5.4, 0.95);
  const signMesh = new THREE.Mesh(signGeo, bannerMat);
  signMesh.position.set(0, 7.1, 3.66);
  root.add(signMesh);

  // Conical steel roof (height 1.2m, radius 3.65m)
  const roofGeo = new THREE.ConeGeometry(3.7, 1.2, 32);
  const roofMesh = new THREE.Mesh(roofGeo, darkSteelMat);
  roofMesh.position.set(0, 9.1, 0);
  root.add(roofMesh);

  // Top roof ventilator / cap
  const ventGeo = new THREE.CylinderGeometry(0.35, 0.35, 0.6, 16);
  const ventMesh = new THREE.Mesh(ventGeo, ironTrimMat);
  ventMesh.position.set(0, 9.9, 0);
  root.add(ventMesh);

  // Exterior steel access ladder on left side (x ~ -3.6)
  const ladderGeo = new THREE.BoxGeometry(0.12, 8.5, 0.45);
  const ladderMesh = new THREE.Mesh(ladderGeo, ironTrimMat);
  ladderMesh.position.set(-3.65, 4.5, 0);
  root.add(ladderMesh);

  return { root, tankBulgeMesh };
}

// ---------------- SHOT 2: CAB BRAKE PLATFORM ----------------
function buildSet2(
  woodTex: THREE.Texture,
  signTex: THREE.Texture
): Set2Refs {
  const root = new THREE.Group();
  root.name = "SET2_CAB_BRAKE";

  const woodMat = twoTone(new THREE.MeshLambertMaterial({ map: woodTex }));
  const darkCabMat = twoTone(new THREE.MeshLambertMaterial({ color: "#252b33" }));
  const brassMat = twoTone(new THREE.MeshLambertMaterial({ color: "#d8a436" }));
  const ironMat = twoTone(new THREE.MeshLambertMaterial({ color: "#26292e" }));
  const signMat = twoTone(new THREE.MeshLambertMaterial({ map: signTex }));

  // 1. Strictly Isolated Streetcar Cab Floor at y = 0
  const floorGeo = new THREE.BoxGeometry(10, 0.2, 8);
  const floorMesh = new THREE.Mesh(floorGeo, woodMat);
  floorMesh.position.set(0, -0.1, 1.0);
  floorMesh.receiveShadow = true;
  root.add(floorMesh);

  // 2. Rear Cab Bulkhead / Door
  const rearWallGeo = new THREE.BoxGeometry(8, 3.5, 0.4);
  const rearWallMesh = new THREE.Mesh(rearWallGeo, darkCabMat);
  rearWallMesh.position.set(0, 1.75, -1.2);
  root.add(rearWallMesh);

  // 3. Left Cab Frame and Warning Sign
  const leftPillar = new THREE.Mesh(new THREE.BoxGeometry(0.3, 3.0, 0.3), darkCabMat);
  leftPillar.position.set(-0.9, 1.5, 0.8);
  root.add(leftPillar);

  // Warning Sign: "DANGER: 35 MPH WAVE" on upper left cab pillar
  // Positioned clearly to the left of the brake lever and Conductor
  const signGeo = new THREE.PlaneGeometry(0.48, 0.26);
  const signMesh = new THREE.Mesh(signGeo, signMat);
  signMesh.position.set(-0.42, 1.80, 0.82);
  root.add(signMesh);

  // Front Dash Rail / Control Console at waist height (y ~ 0.95m)
  const dashGeo = new THREE.BoxGeometry(2.6, 0.12, 0.25);
  const dashMesh = new THREE.Mesh(dashGeo, darkCabMat);
  dashMesh.position.set(0.0, 0.95, 0.8);
  root.add(dashMesh);

  // 4. Heavy Brass Emergency Brake Pedestal & Lever
  const pedestalPos: [number, number, number] = [-0.28, 0.0, 0.8];

  // Cast iron pedestal column
  const baseCol = new THREE.Mesh(new THREE.CylinderGeometry(0.07, 0.11, 0.65, 16), ironMat);
  baseCol.position.set(pedestalPos[0], 0.325, pedestalPos[2]);
  root.add(baseCol);

  // Rotating brass ratchet collar / hub at y = 0.65m
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.08, 0.08, 0.12, 16), brassMat);
  collar.position.set(pedestalPos[0], 0.65, pedestalPos[2]);
  root.add(collar);

  // 5. Articulated Lever Bar and Brass Knob
  // Lever bar connects collar to 2D fist (unit height 1.0 for setCable scaling)
  const leverBar = new THREE.Mesh(new THREE.CylinderGeometry(0.018, 0.018, 1.0, 12), brassMat);
  root.add(leverBar);

  // Brass Emergency Grip Knob at the tip
  const leverKnob = new THREE.Mesh(new THREE.SphereGeometry(0.048, 16, 16), brassMat);
  leverKnob.position.set(pedestalPos[0] + 0.32, 0.775, pedestalPos[2]);
  root.add(leverKnob);

  return { root, leverBar, leverKnob, collar, pedestalPos };
}

// ---------------- SHOT 3: AFTERMATH PLAZA ----------------
function buildSet3(
  woodTex: THREE.Texture,
  easelTex: THREE.Texture,
  trainTex: THREE.Texture
): Set3Refs {
  const root = new THREE.Group();
  root.name = "SET3_AFTERMATH_PLAZA";

  const woodMat = twoTone(new THREE.MeshLambertMaterial({ map: woodTex }));
  const easelMat = twoTone(new THREE.MeshLambertMaterial({ map: easelTex }));
  const trainMat = twoTone(new THREE.MeshLambertMaterial({ map: trainTex }));
  const trestleSteelMat = twoTone(new THREE.MeshLambertMaterial({ color: "#282c33" }));
  const railMat = twoTone(new THREE.MeshLambertMaterial({ color: "#181a1e" }));
  const syrupWaveMat = twoTone(new THREE.MeshLambertMaterial({ color: "#421b08" }));

  // 1. Foreground Boardwalk Plaza Floor at y = 0 (z = 0..6)
  const plazaGeo = new THREE.BoxGeometry(16, 0.2, 10);
  const plazaMesh = new THREE.Mesh(plazaGeo, woodMat);
  plazaMesh.position.set(0, -0.1, 2.5);
  plazaMesh.receiveShadow = true;
  root.add(plazaMesh);

  // 2. Wooden A-frame Chalkboard Easel on left (x ~ -0.75, y = 0, z = 2.0)
  const easel = new THREE.Group();
  easel.name = "CHALKBOARD_EASEL";
  easel.position.set(-0.75, 0.0, 2.0);

  // Timber legs
  const legGeo = new THREE.BoxGeometry(0.06, 1.8, 0.06);
  const legL = new THREE.Mesh(legGeo, woodMat);
  legL.position.set(-0.45, 0.85, 0);
  easel.add(legL);

  const legR = new THREE.Mesh(legGeo, woodMat);
  legR.position.set(0.45, 0.85, 0);
  easel.add(legR);

  // Chalkboard panel: "BOSTON HARBOR 1919 / 25 FT TALL / 35 MPH SYRUP WAVE"
  const boardGeo = new THREE.PlaneGeometry(0.88, 1.05);
  const boardMesh = new THREE.Mesh(boardGeo, easelMat);
  boardMesh.position.set(0, 1.10, 0.04);
  easel.add(boardMesh);

  root.add(easel);

  // 3. Background Steel Elevated Train Trestle Bridge (at z = -12.5m)
  // Lattice columns extending upward to track deck at y ~ 4.2m
  const colGeo = new THREE.BoxGeometry(0.4, 4.2, 0.4);
  for (const cx of [-3.5, 0.0, 3.5]) {
    const colMesh = new THREE.Mesh(colGeo, trestleSteelMat);
    colMesh.position.set(cx, 2.1, -12.5);
    root.add(colMesh);
  }

  // Cross-girders & longitudinal track deck
  const deckGeo = new THREE.BoxGeometry(12.0, 0.4, 2.4);
  const deckMesh = new THREE.Mesh(deckGeo, trestleSteelMat);
  deckMesh.position.set(0, 4.3, -12.5);
  root.add(deckMesh);

  // Iron rails
  for (const rz of [-12.8, -12.2]) {
    const railGeo = new THREE.BoxGeometry(12.0, 0.1, 0.08);
    const railMesh = new THREE.Mesh(railGeo, railMat);
    railMesh.position.set(0, 4.55, rz);
    root.add(railMesh);
  }

  // 4. Red Elevated Train Car (pivots & tilts when molasses wave hits)
  const trainCar = new THREE.Group();
  trainCar.name = "ELEVATED_TRAIN_CAR";
  trainCar.position.set(0.5, 4.55, -12.5);

  const carBodyGeo = new THREE.BoxGeometry(5.2, 1.9, 1.8);
  const carBodyMesh = new THREE.Mesh(carBodyGeo, trainMat);
  carBodyMesh.position.set(0, 0.95, 0);
  trainCar.add(carBodyMesh);

  // Roof curved hood
  const carRoofGeo = new THREE.CylinderGeometry(0.9, 0.9, 5.2, 16, 1, false, 0, Math.PI);
  const carRoofMesh = new THREE.Mesh(carRoofGeo, trestleSteelMat);
  carRoofMesh.rotation.z = Math.PI / 2;
  carRoofMesh.rotation.y = Math.PI / 2;
  carRoofMesh.position.set(0, 1.9, 0);
  trainCar.add(carRoofMesh);

  root.add(trainCar);

  // 5. Surging 3D Molasses Wave Mesh
  // Horizontal fluid syrup crest rolling beneath the trestle deck
  const waveMesh = new THREE.Group();
  waveMesh.name = "MOLASSES_WAVE_SURGE";

  // Base rolling surge bar spanning across trestle
  const surgeGeo = new THREE.CylinderGeometry(0.7, 1.4, 13.0, 24);
  const surgeBar = new THREE.Mesh(surgeGeo, syrupWaveMat);
  surgeBar.rotation.z = Math.PI / 2;
  surgeBar.position.set(0, 0.7, 0);
  waveMesh.add(surgeBar);

  // Left cresting surge mound that curls up to hit the train's left truck
  const crestGeo = new THREE.SphereGeometry(1.6, 24, 16);
  crestGeo.scale(1.8, 1.1, 1.2);
  const crestMesh = new THREE.Mesh(crestGeo, syrupWaveMat);
  crestMesh.position.set(-1.2, 1.2, 0.2);
  waveMesh.add(crestMesh);

  waveMesh.position.set(0, 0.5, -12.2);
  root.add(waveMesh);

  return { root, easel, trainCar, waveMesh };
}

// ---------------- MASTER WORLD BUILDER ----------------
export function buildWorldSets(): WorldSets {
  const steelTex = makeRivetedSteelTexture();
  const bannerTex = makePurityDistillingBanner();
  const warningTex = makeCabWarningSign();
  const easelTex = makeEaselBoardTexture();
  const cobbleTex = makeCobblestoneTexture();
  const woodTex = makeWoodPlankTexture();
  const trainTex = makeTrainCarTexture();

  return {
    set1: buildSet1(steelTex, bannerTex, cobbleTex, woodTex),
    set2: buildSet2(woodTex, warningTex),
    set3: buildSet3(woodTex, easelTex, trainTex),
  };
}
