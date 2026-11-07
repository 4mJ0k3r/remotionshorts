// 3D Set building for HotelLiftShort (SKILL.md Section 4 & Hard Rule 8):
// Three strictly isolated sets:
// 1. SET_HOTEL_EXTERIOR (Shot 1): 1860s Chicago street, boardwalk, 4-story Tremont Hotel with
//    facade banner, timber shoring crib and row of rotating 3D iron jackscrews.
// 2. SET_JACK_TRENCH (Shot 2): Strictly isolated floor at y = 0, heavy oak shoring gallery,
//    "5,000 JACKSCREWS" painted sign on upper left, 3D iron jackscrew with wrench lever and knob.
// 3. SET_RAISED_PLAZA (Shot 3): Boardwalk plaza with chalkboard easel ("RAISED 6 FEET / 0 BROKEN WINDOWS"),
//    massive 4-story Tremont Hotel filling upper frame (v = 10%..55%) on new brick piers.
import * as THREE from "three";
import { twoTone } from "./shade";
import {
  makeBrickTexture,
  makeWoodPlankTexture,
  makeTremontBannerTexture,
  makeJackSignTexture,
  makeEaselBoardTexture,
} from "./paint";

export type Set1Refs = {
  root: THREE.Group;
  hotelLiftRoot: THREE.Group;
  jacks: THREE.Group[];
};

export type Set2Refs = {
  root: THREE.Group;
  leverBar: THREE.Mesh;
  leverKnob: THREE.Mesh;
  collar: THREE.Mesh;
  liftBeam: THREE.Mesh;
  pedestalPos: [number, number, number];
};

export type Set3Refs = {
  root: THREE.Group;
  hotelLiftRoot: THREE.Group;
  easel: THREE.Group;
};

export type WorldSets = {
  set1: Set1Refs;
  set2: Set2Refs;
  set3: Set3Refs;
};

// ---------------- SHOT 1: HOTEL EXTERIOR ----------------
function buildSet1(brickTex: THREE.Texture, woodTex: THREE.Texture, bannerTex: THREE.Texture): Set1Refs {
  const root = new THREE.Group();
  root.name = "SET1_HOTEL_EXTERIOR";

  // Base materials with twoTone shader
  const woodMat = twoTone(new THREE.MeshLambertMaterial({ map: woodTex }));
  const brickMat = twoTone(new THREE.MeshLambertMaterial({ map: brickTex }));
  const stoneTrimMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f2ece4" }));
  const darkRoofMat = twoTone(new THREE.MeshLambertMaterial({ color: "#32353a" }));
  const glassMat = twoTone(new THREE.MeshLambertMaterial({ color: "#283845" }));
  const greenAwningMat = twoTone(new THREE.MeshLambertMaterial({ color: "#2c5d3f" }));
  const ironMat = twoTone(new THREE.MeshLambertMaterial({ color: "#2c2f33" }));
  const bannerMat = twoTone(new THREE.MeshLambertMaterial({ map: bannerTex }));
  const streetDirtMat = twoTone(new THREE.MeshLambertMaterial({ color: "#544638" }));

  // 1. Street and Wooden Boardwalk
  // Dirt road in front of hotel
  const streetGeo = new THREE.PlaneGeometry(36, 24);
  const streetMesh = new THREE.Mesh(streetGeo, streetDirtMat);
  streetMesh.rotation.x = -Math.PI / 2;
  streetMesh.position.set(0, -0.05, 4.0);
  streetMesh.receiveShadow = true;
  root.add(streetMesh);

  // Right wooden boardwalk / sidewalk platform for Guest (x: 0.5..2.5, y: 0, z: 1.8..5.8)
  const walkGeo = new THREE.BoxGeometry(2.4, 0.15, 4.0);
  const walkMesh = new THREE.Mesh(walkGeo, woodMat);
  walkMesh.position.set(1.5, 0.0, 3.8);
  walkMesh.receiveShadow = true;
  root.add(walkMesh);

  // Cutaway timber crib trench under hotel (stationary foundation trench)
  const trenchGeo = new THREE.BoxGeometry(13.0, 1.2, 7.0);
  const trenchMat = twoTone(new THREE.MeshLambertMaterial({ color: "#38291a" }));
  const trenchMesh = new THREE.Mesh(trenchGeo, trenchMat);
  trenchMesh.position.set(0, -0.65, 0);
  root.add(trenchMesh);

  // Stationary bottom timber sills
  for (let x = -5.5; x <= 5.5; x += 1.8) {
    const sillGeo = new THREE.BoxGeometry(0.35, 0.35, 6.5);
    const sillMesh = new THREE.Mesh(sillGeo, woodMat);
    sillMesh.position.set(x, -0.15, 0);
    root.add(sillMesh);
  }

  // Row of 3D Jackscrews along the front foundation
  const jacks: THREE.Group[] = [];
  const jackCount = 7;
  for (let i = 0; i < jackCount; i++) {
    const jg = new THREE.Group();
    const jx = -4.8 + i * 1.6;
    jg.position.set(jx, 0.0, 3.1);

    // Jack base block
    const baseGeo = new THREE.CylinderGeometry(0.22, 0.26, 0.25, 12);
    const baseMesh = new THREE.Mesh(baseGeo, ironMat);
    baseMesh.position.y = 0.125;
    jg.add(baseMesh);

    // Threaded screw shaft (rises with lift)
    const screwGeo = new THREE.CylinderGeometry(0.12, 0.12, 1.8, 12);
    const screwMesh = new THREE.Mesh(screwGeo, ironMat);
    screwMesh.position.y = 0.9;
    jg.add(screwMesh);

    // Jack collar ring
    const collarGeo = new THREE.TorusGeometry(0.16, 0.05, 8, 16);
    const collarMesh = new THREE.Mesh(collarGeo, stoneTrimMat);
    collarMesh.rotation.x = Math.PI / 2;
    collarMesh.position.y = 0.85;
    jg.add(collarMesh);

    jacks.push(jg);
    root.add(jg);
  }

  // 2. Liftable Tremont Hotel Root
  const hotelLiftRoot = new THREE.Group();
  hotelLiftRoot.name = "HOTEL_LIFT_ROOT";
  hotelLiftRoot.position.set(0, 0, 0);

  // Heavy Oak Needle Beams directly supporting the brick foundation
  for (let x = -5.6; x <= 5.6; x += 1.4) {
    const needleGeo = new THREE.BoxGeometry(0.32, 0.4, 6.8);
    const needleMesh = new THREE.Mesh(needleGeo, woodMat);
    needleMesh.position.set(x, 0.45, 0);
    hotelLiftRoot.add(needleMesh);
  }
  // Cross beam header along facade
  const headerGeo = new THREE.BoxGeometry(11.8, 0.4, 0.45);
  const headerMesh = new THREE.Mesh(headerGeo, woodMat);
  headerMesh.position.set(0, 0.65, 3.15);
  hotelLiftRoot.add(headerMesh);

  // Main 4-story Red Brick Hotel Building (width ~ 7.2m, height ~ 8.0m, depth ~ 5.2m)
  const hotelBodyGeo = new THREE.BoxGeometry(7.2, 7.8, 5.0);
  const hotelBodyMesh = new THREE.Mesh(hotelBodyGeo, brickMat);
  hotelBodyMesh.position.set(0, 4.5, 0);
  hotelBodyMesh.castShadow = true;
  hotelBodyMesh.receiveShadow = true;
  hotelLiftRoot.add(hotelBodyMesh);

  // Facade Grand Banner: "TREMONT HOTEL"
  const bannerGeo = new THREE.PlaneGeometry(5.6, 1.35);
  const bannerMesh = new THREE.Mesh(bannerGeo, bannerMat);
  bannerMesh.position.set(0, 7.1, 2.52);
  hotelLiftRoot.add(bannerMesh);

  // Windows, White Stone Trim & Green Awnings (4 stories)
  const floorHeights = [1.8, 3.6, 5.4, 7.0];
  const winCols = [-2.6, -1.6, -0.6, 0.6, 1.6, 2.6];

  for (let fi = 0; fi < floorHeights.length; fi++) {
    const wy = floorHeights[fi];
    for (const wx of winCols) {
      if (fi === 0 && Math.abs(wx) < 1.0) continue;

      const winGeo = new THREE.PlaneGeometry(0.68, 1.0);
      const winMesh = new THREE.Mesh(winGeo, glassMat);
      winMesh.position.set(wx, wy, 2.52);
      hotelLiftRoot.add(winMesh);

      const sillGeo = new THREE.BoxGeometry(0.82, 0.1, 0.14);
      const sillMesh = new THREE.Mesh(sillGeo, stoneTrimMat);
      sillMesh.position.set(wx, wy - 0.55, 2.54);
      hotelLiftRoot.add(sillMesh);

      const headGeo = new THREE.BoxGeometry(0.82, 0.12, 0.14);
      const headMesh = new THREE.Mesh(headGeo, stoneTrimMat);
      headMesh.position.set(wx, wy + 0.55, 2.54);
      hotelLiftRoot.add(headMesh);

      if (fi <= 1) {
        const awnGeo = new THREE.BoxGeometry(0.82, 0.28, 0.42);
        const awnMesh = new THREE.Mesh(awnGeo, greenAwningMat);
        awnMesh.position.set(wx, wy + 0.58, 2.7);
        hotelLiftRoot.add(awnMesh);
      }
    }
  }

  // Grand Hotel Entrance Portico
  const porticoGeo = new THREE.BoxGeometry(2.0, 1.7, 0.6);
  const porticoMesh = new THREE.Mesh(porticoGeo, stoneTrimMat);
  porticoMesh.position.set(0, 1.7, 2.8);
  hotelLiftRoot.add(porticoMesh);

  // Roof Cornice & Decorative Parapet
  const corniceGeo = new THREE.BoxGeometry(7.8, 0.45, 5.4);
  const corniceMesh = new THREE.Mesh(corniceGeo, stoneTrimMat);
  corniceMesh.position.set(0, 8.65, 0);
  hotelLiftRoot.add(corniceMesh);

  const roofGeo = new THREE.BoxGeometry(7.5, 0.35, 5.1);
  const roofMesh = new THREE.Mesh(roofGeo, darkRoofMat);
  roofMesh.position.set(0, 8.95, 0);
  hotelLiftRoot.add(roofMesh);

  root.add(hotelLiftRoot);
  return { root, hotelLiftRoot, jacks };
}

// ---------------- SHOT 2: TIMBER SHORING TRENCH (Strictly Isolated Floor at y = 0) ----------------
function buildSet2(brickTex: THREE.Texture, woodTex: THREE.Texture, signTex: THREE.Texture): Set2Refs {
  const root = new THREE.Group();
  root.name = "SET2_JACK_TRENCH";

  const woodMat = twoTone(new THREE.MeshLambertMaterial({ map: woodTex }));
  const brickMat = twoTone(new THREE.MeshLambertMaterial({ map: brickTex }));
  const ironMat = twoTone(new THREE.MeshLambertMaterial({ color: "#26292e" }));
  const brassMat = twoTone(new THREE.MeshLambertMaterial({ color: "#d8a436" }));
  const signMat = twoTone(new THREE.MeshLambertMaterial({ map: signTex }));

  // 1. Strictly Isolated Wooden Floor at y = 0 (ZERO mud/water above y = 0!)
  const floorGeo = new THREE.BoxGeometry(14, 0.2, 12);
  const floorMesh = new THREE.Mesh(floorGeo, woodMat);
  floorMesh.position.set(0, -0.1, 1.0);
  floorMesh.receiveShadow = true;
  root.add(floorMesh);

  // 2. Brick Arch Backdrop behind gallery
  const backArchGeo = new THREE.BoxGeometry(12, 4.0, 0.6);
  const backArchMesh = new THREE.Mesh(backArchGeo, brickMat);
  backArchMesh.position.set(0, 2.0, -1.8);
  root.add(backArchMesh);

  // 3. Heavy Oak Shoring Pillars and Gallery Structure
  // Left pillar column (x ~ -1.1)
  const pillarL = new THREE.Mesh(new THREE.BoxGeometry(0.45, 3.2, 0.45), woodMat);
  pillarL.position.set(-1.1, 1.6, 0.6);
  root.add(pillarL);

  // Right pillar column (x ~ 1.6)
  const pillarR = new THREE.Mesh(new THREE.BoxGeometry(0.45, 3.2, 0.45), woodMat);
  pillarR.position.set(1.6, 1.6, 0.6);
  root.add(pillarR);

  // Upper Timber Sign: "5,000 JACKSCREWS" on upper-left support beam
  // Positioned clearly to the left of jackscrew & Engineer so it is 100% unobstructed!
  const signGeo = new THREE.PlaneGeometry(0.42, 0.24);
  const signMesh = new THREE.Mesh(signGeo, signMat);
  signMesh.position.set(-0.52, 1.95, 0.85);
  root.add(signMesh);

  // Liftable Overhead Oak Needle Beam (overhead at y = 2.35m, clear of head!)
  const liftBeam = new THREE.Mesh(new THREE.BoxGeometry(3.6, 0.35, 0.45), woodMat);
  liftBeam.position.set(0.0, 2.35, 0.8);
  root.add(liftBeam);

  // 4. Heavy 3D Cast-Iron Jackscrew Pedestal on timber crib block
  const pedestalPos: [number, number, number] = [-0.28, 0.0, 0.8];
  const cribBlock = new THREE.Mesh(new THREE.BoxGeometry(0.48, 0.35, 0.48), woodMat);
  cribBlock.position.set(pedestalPos[0], 0.175, pedestalPos[2]);
  root.add(cribBlock);

  // Iron base cone
  const jackBase = new THREE.Mesh(new THREE.CylinderGeometry(0.12, 0.18, 0.35, 16), ironMat);
  jackBase.position.set(pedestalPos[0], 0.525, pedestalPos[2]);
  root.add(jackBase);

  // Threaded screw shaft rising toward overhead beam (y = 0.525..2.35)
  const screwShaft = new THREE.Mesh(new THREE.CylinderGeometry(0.045, 0.045, 1.8, 16), ironMat);
  screwShaft.position.set(pedestalPos[0], 1.45, pedestalPos[2]);
  root.add(screwShaft);

  // Threaded collar that turns with wrench
  const collar = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.12, 16), brassMat);
  collar.position.set(pedestalPos[0], 0.88, pedestalPos[2]);
  root.add(collar);

  // 5. Wrench Lever Bar and Brass Knob
  // Lever bar connects collar at pedestal to 2D fist (unit height 1.0 for setCable scaling)
  const leverBar = new THREE.Mesh(new THREE.CylinderGeometry(0.016, 0.016, 1.0, 12), ironMat);
  root.add(leverBar);

  // Brass Grip Knob at the tip
  const leverKnob = new THREE.Mesh(new THREE.SphereGeometry(0.045, 14, 14), brassMat);
  leverKnob.position.set(pedestalPos[0] + 0.35, 0.88, pedestalPos[2]);
  root.add(leverKnob);

  return { root, leverBar, leverKnob, collar, liftBeam, pedestalPos };
}

// ---------------- SHOT 3: RAISED PLAZA ----------------
function buildSet3(brickTex: THREE.Texture, woodTex: THREE.Texture, bannerTex: THREE.Texture, easelTex: THREE.Texture): Set3Refs {
  const root = new THREE.Group();
  root.name = "SET3_RAISED_PLAZA";

  const woodMat = twoTone(new THREE.MeshLambertMaterial({ map: woodTex }));
  const brickMat = twoTone(new THREE.MeshLambertMaterial({ map: brickTex }));
  const stoneTrimMat = twoTone(new THREE.MeshLambertMaterial({ color: "#f2ece4" }));
  const darkRoofMat = twoTone(new THREE.MeshLambertMaterial({ color: "#32353a" }));
  const glassMat = twoTone(new THREE.MeshLambertMaterial({ color: "#283845" }));
  const greenAwningMat = twoTone(new THREE.MeshLambertMaterial({ color: "#2c5d3f" }));
  const bannerMat = twoTone(new THREE.MeshLambertMaterial({ map: bannerTex }));
  const easelMat = twoTone(new THREE.MeshLambertMaterial({ map: easelTex }));

  // 1. Foreground Boardwalk Plaza (y = 0, z = 0..6)
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
  legL.rotation.z = -0.08;
  easel.add(legL);

  const legR = new THREE.Mesh(legGeo, woodMat);
  legR.position.set(0.45, 0.85, 0);
  legR.rotation.z = 0.08;
  easel.add(legR);

  const legBack = new THREE.Mesh(legGeo, woodMat);
  legBack.position.set(0, 0.85, -0.35);
  legBack.rotation.x = 0.25;
  easel.add(legBack);

  // Chalkboard face
  const boardGeo = new THREE.PlaneGeometry(0.85, 1.05);
  const boardMesh = new THREE.Mesh(boardGeo, easelMat);
  boardMesh.position.set(0, 1.05, 0.04);
  easel.add(boardMesh);

  root.add(easel);

  // 3. Background Grand 4-Story Red-Brick Tremont Hotel (z ~ -12.5)
  // Scaled & positioned so it fills upper half of frame (v = 10%..55%)
  const hotelLiftRoot = new THREE.Group();
  hotelLiftRoot.name = "HOTEL_SET3_LIFT";
  hotelLiftRoot.position.set(0, 0, -12.5);

  // Raised Brick & Timber Foundation Piers under hotel (elevated by 6 feet = 1.83m!)
  for (let px = -5.5; px <= 5.5; px += 2.0) {
    const pierGeo = new THREE.BoxGeometry(0.85, 2.2, 1.8);
    const pierMesh = new THREE.Mesh(pierGeo, brickMat);
    pierMesh.position.set(px, 1.1, 0);
    hotelLiftRoot.add(pierMesh);

    // Stone pier cap
    const capGeo = new THREE.BoxGeometry(1.0, 0.18, 1.9);
    const capMesh = new THREE.Mesh(capGeo, stoneTrimMat);
    capMesh.position.set(px, 2.2, 0);
    hotelLiftRoot.add(capMesh);
  }

  // Oak needle beams atop piers
  for (let px = -5.5; px <= 5.5; px += 1.6) {
    const beamGeo = new THREE.BoxGeometry(0.32, 0.4, 7.5);
    const beamMesh = new THREE.Mesh(beamGeo, woodMat);
    beamMesh.position.set(px, 2.5, 0);
    hotelLiftRoot.add(beamMesh);
  }

  // 4-Story Brick Hotel superstructure (width ~ 12.5m, height ~ 8.0m, depth ~ 6.0m)
  const hotelBodyGeo = new THREE.BoxGeometry(12.2, 7.8, 5.8);
  const hotelBodyMesh = new THREE.Mesh(hotelBodyGeo, brickMat);
  hotelBodyMesh.position.set(0, 6.4, 0);
  hotelLiftRoot.add(hotelBodyMesh);

  // Grand Facade Banner: "TREMONT HOTEL"
  const bannerGeo = new THREE.PlaneGeometry(8.0, 1.8);
  const bannerMesh = new THREE.Mesh(bannerGeo, bannerMat);
  bannerMesh.position.set(0, 7.6, 2.92);
  hotelLiftRoot.add(bannerMesh);

  // Windows grid across 4 stories
  const floorYs = [3.8, 5.4, 7.0, 8.6];
  const winXs = [-4.5, -2.7, -0.9, 0.9, 2.7, 4.5];
  for (const wy of floorYs) {
    for (const wx of winXs) {
      const winGeo = new THREE.PlaneGeometry(0.9, 1.2);
      const winMesh = new THREE.Mesh(winGeo, glassMat);
      winMesh.position.set(wx, wy, 2.92);
      hotelLiftRoot.add(winMesh);

      const sillGeo = new THREE.BoxGeometry(1.05, 0.12, 0.16);
      const sillMesh = new THREE.Mesh(sillGeo, stoneTrimMat);
      sillMesh.position.set(wx, wy - 0.65, 2.94);
      hotelLiftRoot.add(sillMesh);

      const headGeo = new THREE.BoxGeometry(1.05, 0.14, 0.16);
      const headMesh = new THREE.Mesh(headGeo, stoneTrimMat);
      headMesh.position.set(wx, wy + 0.65, 2.94);
      hotelLiftRoot.add(headMesh);
    }
  }

  // Roof cornice & parapet
  const corniceGeo = new THREE.BoxGeometry(12.8, 0.5, 6.4);
  const corniceMesh = new THREE.Mesh(corniceGeo, stoneTrimMat);
  corniceMesh.position.set(0, 10.45, 0);
  hotelLiftRoot.add(corniceMesh);

  const roofGeo = new THREE.BoxGeometry(12.4, 0.4, 6.0);
  const roofMesh = new THREE.Mesh(roofGeo, darkRoofMat);
  roofMesh.position.set(0, 10.85, 0);
  hotelLiftRoot.add(roofMesh);

  root.add(hotelLiftRoot);
  return { root, hotelLiftRoot, easel };
}

// ---------------- MAIN EXPORT ----------------
export function buildSets(): WorldSets {
  const brickTex = makeBrickTexture();
  const woodTex = makeWoodPlankTexture();
  const bannerTex = makeTremontBannerTexture();
  const jackSignTex = makeJackSignTexture();
  const easelTex = makeEaselBoardTexture();

  return {
    set1: buildSet1(brickTex, woodTex, bannerTex),
    set2: buildSet2(brickTex, woodTex, jackSignTex),
    set3: buildSet3(brickTex, woodTex, bannerTex, easelTex),
  };
}
