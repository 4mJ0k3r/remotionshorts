// Generates the low-poly props missing from the Kenney nature mirror (town/pirate kit items).
// Names match KENNEY in src/videos/bridge/world.ts; materials reuse build.ts RECOLOR keys where possible.
// usage: node scripts/generate-kenney-glb.mjs [outDir]
import fs from "node:fs";
import path from "node:path";
import * as THREE from "three";
import { GLTFExporter } from "three/examples/jsm/exporters/GLTFExporter.js";

// GLTFExporter's binary path reads a Blob with FileReader, which Node only has in browsers
if (typeof globalThis.FileReader === "undefined") {
  globalThis.FileReader = class {
    readAsArrayBuffer(blob) {
      blob.arrayBuffer().then((buf) => { this.result = buf; this.onloadend?.(); });
    }
  };
}

const outDir = path.resolve(process.argv[2] || "public/bridge/kenney");
fs.mkdirSync(outDir, { recursive: true });

const mat = (name, color, opts = {}) => new THREE.MeshStandardMaterial({ name, color: new THREE.Color(color), roughness: 0.9, metalness: 0, ...opts });
const M = {
  wood: mat("wood", "#a8724a"),
  woodDark: mat("woodDark", "#7a4f33"),
  woodInner: mat("woodInner", "#e8cfa4"),
  leafsGreen: mat("leafsGreen", "#62ae4c"),
  stone: mat("stone", "#b7b4ad"),
  red: mat("red", "#c0392b"),
  green: mat("green", "#2f7d4f"),
  canvas: mat("canvas", "#e8dcc0"),
  glow: mat("lanternGlow", "#ffd27a", { emissive: new THREE.Color("#ffb347"), emissiveIntensity: 0.6 }),
};

const mesh = (geo, m, x = 0, y = 0, z = 0, rx = 0, ry = 0, rz = 0) => {
  const o = new THREE.Mesh(geo, m);
  o.position.set(x, y, z); o.rotation.set(rx, ry, rz);
  return o;
};
const cyl = (rt, rb, h, seg = 8) => new THREE.CylinderGeometry(rt, rb, h, seg);
const box = (w, h, d) => new THREE.BoxGeometry(w, h, d);
const cone = (r, h, seg = 8) => new THREE.ConeGeometry(r, h, seg);
const sphere = (r, ws = 10, hs = 8) => new THREE.SphereGeometry(r, ws, hs);

const build = {
  hedge: () => {
    const g = new THREE.Group();
    g.add(mesh(box(1.7, 0.55, 0.55), M.leafsGreen, 0, 0.275, 0));
    g.add(mesh(sphere(0.32), M.leafsGreen, -0.55, 0.55, 0));
    g.add(mesh(sphere(0.34), M.leafsGreen, 0.05, 0.6, 0));
    g.add(mesh(sphere(0.3), M.leafsGreen, 0.6, 0.52, 0));
    return g;
  },
  lily_large: () => {
    const g = new THREE.Group();
    g.add(mesh(cyl(0.42, 0.44, 0.04, 12), M.leafsGreen, 0, 0.02, 0));
    const flower = new THREE.Group();
    for (let i = 0; i < 6; i++) {
      const a = (i / 6) * Math.PI * 2;
      flower.add(mesh(sphere(0.06), mat("flowerPink", "#e88bb0"), Math.cos(a) * 0.08, 0.07, Math.sin(a) * 0.08));
    }
    flower.add(mesh(sphere(0.04), mat("flowerGold", "#ffd257"), 0, 0.09, 0));
    g.add(flower);
    return g;
  },
  lantern: () => {
    const g = new THREE.Group();
    g.add(mesh(cyl(0.06, 0.08, 1.7, 6), M.woodDark, 0, 0.85, 0));
    g.add(mesh(cyl(0.14, 0.14, 0.28, 6), M.glow, 0, 1.78, 0));
    g.add(mesh(cyl(0.18, 0.2, 0.06, 6), M.woodDark, 0, 1.95, 0));
    g.add(mesh(cone(0.2, 0.16, 6), M.woodDark, 0, 2.05, 0));
    return g;
  },
  cart: () => {
    const g = new THREE.Group();
    g.add(mesh(box(1.2, 0.42, 0.7), M.wood, 0, 0.62, 0));
    g.add(mesh(box(1.24, 0.06, 0.74), M.woodInner, 0, 0.86, 0));
    for (const [x, z] of [[-0.42, 0.38], [0.42, 0.38], [-0.42, -0.38], [0.42, -0.38]])
      g.add(mesh(cyl(0.26, 0.26, 0.09, 10), M.woodDark, x, 0.28, z, Math.PI / 2, 0, 0));
    g.add(mesh(cyl(0.045, 0.045, 1.0, 6), M.woodDark, 0.75, 0.5, 0.18, 0, 0, -0.9));
    g.add(mesh(cyl(0.045, 0.045, 1.0, 6), M.woodDark, 0.75, 0.5, -0.18, 0, 0, -0.9));
    return g;
  },
  "stall-red": () => stall(M.red),
  "stall-green": () => stall(M.green),
  "stall-bench": () => {
    const g = new THREE.Group();
    g.add(mesh(box(1.5, 0.08, 0.4), M.wood, 0, 0.46, 0));
    g.add(mesh(box(1.5, 0.35, 0.06), M.wood, 0, 0.75, -0.2, -0.15, 0, 0));
    for (const x of [-0.62, 0.62]) for (const z of [-0.14, 0.14])
      g.add(mesh(box(0.07, 0.46, 0.07), M.woodDark, x, 0.23, z));
    return g;
  },
  "banner-red": () => banner(M.red),
  "banner-green": () => banner(M.green),
  windmill: () => {
    const g = new THREE.Group();
    g.add(mesh(cyl(0.42, 0.62, 2.1, 8), M.woodInner, 0, 1.05, 0));
    g.add(mesh(cone(0.58, 0.55, 8), M.woodDark, 0, 2.35, 0));
    g.add(mesh(cyl(0.09, 0.09, 0.3, 6), M.woodDark, 0, 1.9, 0.5, Math.PI / 2, 0, 0));
    const hub = new THREE.Group(); hub.position.set(0, 1.9, 0.68);
    for (let i = 0; i < 4; i++) hub.add(mesh(box(0.18, 1.15, 0.04), M.canvas, 0, 0.6, 0, 0, 0, (i * Math.PI) / 2));
    g.add(hub);
    g.add(mesh(box(0.32, 0.55, 0.06), M.woodDark, 0, 0.35, 0.5));
    return g;
  },
  canoe: () => {
    const g = new THREE.Group();
    const hull = new THREE.Mesh(sphere(0.5, 12, 8), M.wood);
    hull.scale.set(2.3, 0.42, 0.62); hull.position.y = 0.2;
    g.add(hull);
    g.add(mesh(box(1.5, 0.05, 0.5), M.woodInner, 0, 0.34, 0));
    for (const x of [-0.55, 0.55]) g.add(mesh(box(0.12, 0.06, 0.6), M.woodDark, x, 0.42, 0));
    return g;
  },
};

function stall(colorMat) {
  const g = new THREE.Group();
  g.add(mesh(box(1.7, 0.75, 0.8), M.wood, 0, 0.375, 0));
  g.add(mesh(box(1.7, 0.08, 0.85), M.woodInner, 0, 0.79, 0));
  for (const x of [-0.74, 0.74]) for (const z of [-0.32, 0.32])
    g.add(mesh(box(0.08, 1.75, 0.08), M.woodDark, x, 0.875, z));
  g.add(mesh(box(1.85, 0.08, 1.05), colorMat, 0, 1.78, 0, 0.08, 0, 0));
  g.add(mesh(box(1.75, 0.5, 0.05), colorMat, 0, 1.5, -0.34));
  return g;
}

function banner(colorMat) {
  const g = new THREE.Group();
  g.add(mesh(cyl(0.05, 0.06, 2.3, 6), M.woodDark, 0, 1.15, 0));
  g.add(mesh(sphere(0.09), mat("gold", "#d8b04a"), 0, 2.32, 0));
  g.add(mesh(box(0.72, 1.05, 0.03), colorMat, 0.38, 1.72, 0));
  g.add(mesh(box(0.06, 0.06, 0.06), M.woodDark, 0.74, 1.72, 0));
  return g;
}

const exporter = new GLTFExporter();
for (const [name, fn] of Object.entries(build)) {
  const scene = new THREE.Scene();
  scene.name = name;
  scene.add(fn());
  const glb = await exporter.parseAsync(scene, { binary: true, onlyVisible: true });
  fs.writeFileSync(path.join(outDir, `${name}.glb`), Buffer.from(glb));
  console.log("wrote", `${name}.glb`, glb.byteLength, "bytes");
}
