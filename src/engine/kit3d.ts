/** Reusable two-tone 3D primitives and cutaway environments. Units are metres. */
import * as THREE from "three";
import {twoTone} from "./shaders/shade";
import {grass,dirt,planks,concrete,crateLabel,makeSteelTexture,makeWoodTrimTexture,makeBrassTexture,makeRainWindowTexture,redrawRainWindow,makeLEDTexture,makeCableTexture,tex} from "./shaders/paint";
import type {V3} from "./camera";
const MATS = new Map<string, THREE.Material>();
export const lam = (key: string, make: () => THREE.MeshLambertMaterialParameters) => {
  const hit = MATS.get(key);
  if (hit) return hit as THREE.MeshLambertMaterial;
  const m = twoTone(new THREE.MeshLambertMaterial(make()));
  MATS.set(key, m);
  return m;
};
export const lit = (key: string, color: THREE.ColorRepresentation, k = 1, flat = false) =>
  lam(`${key}|${new THREE.Color(color).getHexString()}|${k}|${flat}`, () => ({ color: new THREE.Color(color).multiplyScalar(k), flatShading: flat }));

const TEX = new Map<string, THREE.Texture>();
export const tx = (key: string, make: () => THREE.Texture) => { let t = TEX.get(key); if (!t) { t = make(); TEX.set(key, t); } return t; };

export type Sets = { root: THREE.Group; sets: Record<string, THREE.Group>; props: Record<string, unknown> };

// ---------------- primitives ----------------
export const mesh = (parent: THREE.Object3D, g: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) => {
  const o = new THREE.Mesh(g, m);
  o.position.set(x, y, z); o.rotation.set(rx, ry, rz);
  o.castShadow = true; o.receiveShadow = true;
  parent.add(o);
  return o;
};
export const box = (p: THREE.Object3D, w: number, h: number, d: number, m: THREE.Material, x: number, y: number, z: number, ry = 0, rx = 0, rz = 0) =>
  mesh(p, new THREE.BoxGeometry(w, h, d), m, x, y, z, ry, rx, rz);
export const cyl = (p: THREE.Object3D, r0: number, r1: number, h: number, m: THREE.Material, x: number, y: number, z: number, seg = 16) =>
  mesh(p, new THREE.CylinderGeometry(r0, r1, h, seg), m, x, y, z);
const UP = new THREE.Vector3(0, 1, 0);
/** Dispose instance-owned geometry; cached materials/textures remain shared. */
export const disposeGeometry = (root: THREE.Object3D) => {
  const seen = new Set<THREE.BufferGeometry>();
  root.traverse(o => {if (o instanceof THREE.Mesh && !seen.has(o.geometry)) {seen.add(o.geometry);o.geometry.dispose();}});
};
/** cylinder (or square strut) between two points */
export const strut = (p: THREE.Object3D, a: V3, b: V3, r: number, m: THREE.Material, seg = 8) => {
  const A = new THREE.Vector3(...a), B = new THREE.Vector3(...b), d = B.clone().sub(A), L = d.length();
  const o = new THREE.Mesh(new THREE.CylinderGeometry(r, r, L, seg), m);
  o.position.copy(A).addScaledVector(d, 0.5);
  o.quaternion.setFromUnitVectors(UP, d.normalize());
  o.castShadow = true; o.receiveShadow = true;
  p.add(o);
  return o;
};
export const beamBox = (p: THREE.Object3D, a: V3, b: V3, w: number, m: THREE.Material) => {
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
export const tree = (p: THREE.Object3D, x: number, y: number, z: number, s: number, seed: number) => {
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
/** a stack of planks: `n` layers of `m` boards, crosswise */
export const plankStack = (p: THREE.Object3D, x: number, z: number, ry: number, n = 3, m = 5, L = 3) => {
  const g = new THREE.Group(); g.position.set(x, 0, z); g.rotation.y = ry; p.add(g);
  const w = wood();
  for (let l = 0; l < n; l++) for (let i = 0; i < m; i++)
    box(g, L, 0.12, 0.26, w, 0, 0.06 + l * 0.13, (i - (m - 1) / 2) * 0.3, l % 2 ? 0.04 : -0.03);
  box(g, 0.14, 0.14 * n + 0.1, 0.12, woodDark(), L / 2 - 0.2, (0.14 * n) / 2, (m / 2) * 0.3 + 0.08);
  return g;
};
export const crate = (p: THREE.Object3D, x: number, z: number, s: number, ry: number, label?: string) => {
  const m = label ? lam("crate" + label, () => ({ map: tx("crate" + label, () => crateLabel(label)) })) : lam("crate", () => ({ map: tx("crateW", () => planks("#d2a46a", "#c09058", 4)) }));
  return box(p, s, s, s, m, x, s / 2, z, ry);
};
export const dirtDisc = (p: THREE.Object3D, x: number, z: number, r: number, key = "dirtA", y = 0.012) => {
  const m = lam(key, () => ({ map: tx(key, () => dirt("#b86b43", [Math.max(1, r / 2), Math.max(1, r / 2)])), polygonOffset: true, polygonOffsetFactor: -1, polygonOffsetUnits: -1 }));
  const o = mesh(p, new THREE.CircleGeometry(r, 40), m, x, y, z, 0, -Math.PI / 2);
  o.castShadow = false;
  return o;
};
export const dirtPath = (p: THREE.Object3D, pts: [number, number][], w: number) => {
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

export const lattice = (p: THREE.Object3D, a: V3, b: V3, w: number, m: THREE.Material, step = 1.6) => {
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

export type LandOptions = {size?: number; seed?: number; trees?: number; hills?: number; color?: string};
/** A deterministic landscape wholly contained by its owning set group. */
export const land = (parent: THREE.Object3D, opts: LandOptions = {}) => {
  const group = new THREE.Group(); parent.add(group);
  const size = opts.size ?? 80, seed = opts.seed ?? 1, color = opts.color ?? "#4da83b";
  const ground = mesh(group,new THREE.PlaneGeometry(size,size),lam(`land:${color}:${size}`,()=>({map:tx(`grass:${color}`,()=>grass(color,[20,20]))})),0,0,0,0,-Math.PI/2);
  ground.castShadow=false;
  for(let i=0;i<(opts.hills??7);i++) {
    const h=3+hash(i+seed)*9, r=4+hash(i+seed+90)*10;
    mesh(group,new THREE.ConeGeometry(r,h,9),lit(`hill:${i}`,color,0.85+hash(i)*0.2,true),(hash(i+seed+4)-0.5)*size*0.8,h/2-0.1,-size*0.2-hash(i+seed+8)*size*0.3);
  }
  for(let i=0;i<(opts.trees??24);i++)tree(group,(hash(i+seed+70)-0.5)*size*0.85,0,(hash(i+seed+110)-0.5)*size*0.85,0.8+hash(i+seed)*1.3,i+seed);
  return group;
};
/** General A-frame support with configurable apex, spread and footing height. */
export const aFrame = (p: THREE.Object3D, top: V3, material: THREE.Material, spread=2.4, groundY=0) => {
  const group=new THREE.Group();p.add(group);
  const foot=lam("kit:concrete",()=>({map:tx("kit:concrete",concrete)}));
  for(const side of [-1,1]){
    strut(group,[top[0],groundY+0.4,top[2]+side*spread],[top[0],top[1]-0.2,top[2]+side*0.25],0.16,material,10);
    box(group,0.9,0.5,0.9,foot,top[0],groundY+0.25,top[2]+side*spread);
  }
  for(const t of [0.3,0.58,0.86]){const y=groundY+0.4+(top[1]-groundY-0.6)*t,w=spread*(1-t)+0.25*t;strut(group,[top[0],y,top[2]-w],[top[0],y,top[2]+w],0.07,material,6);}
  return group;
};
export type CabinOptions = {width?:number;depth?:number;height?:number;doorGap?:number;header?:string;parent?:THREE.Object3D};
export type ButtonName = "1"|"2"|"3"|"4"|"G"|"FAN";
/** Doors face +Z; the +Z fourth wall is removed for camera coverage. */
export const buildElevatorCabin = (opts: CabinOptions = {}) => {
  const width=opts.width??4.6,depth=opts.depth??4.2,height=opts.height??3.8;
  if(width<3||depth<2||height<2.5)throw new Error("Cabin dimensions must accommodate doors and controls");
  const root=new THREE.Group();root.name="elevator-cabin";opts.parent?.add(root);
  const back=-depth/2,side=width/2;
  const steel=lam("kit:steel",()=>({map:tx("kit:steel",makeSteelTexture)}));
  const trim=lam("kit:wood",()=>({map:tx("kit:wood",makeWoodTrimTexture)}));
  const brass=lam("kit:brass",()=>({map:tx("kit:brass",makeBrassTexture)}));
  const floor=lit("kit:floor","#888891");
  box(root,width,0.16,depth,floor,0,-0.08,0);
  // A low apron extends the cutaway floor to keep the camera from seeing an artificial floor edge.
  box(root,30,0.08,30,floor,0,-0.042,0);
  for(const s of [-1,1]){
    box(root,0.12,height,depth,steel,s*side,height/2,0);
    box(root,0.14,0.94,depth,trim,s*(side-0.025),0.5,0);
    for(let z=back+0.5;z<depth/2;z+=0.7)box(root,0.025,height-1.1,0.025,brass,s*(side-0.08),2.25,z);
    strut(root,[s*(side-0.2),1.12,back+0.25],[s*(side-0.2),1.12,depth/2-0.2],0.035,brass,12);
  }
  box(root,width,0.98,0.15,trim,0,0.49,back);
  box(root,width,height-0.98,0.14,steel,0,0.98+(height-0.98)/2,back);
  // Recessed 2.0 m doorway, stainless surround and jambs.
  const doorWidth=2, doorHeight=2.6;
  box(root,2.25,2.82,0.15,lit("kit:door-recess","#343e50"),0,1.41,back+0.12);
  for(const s of [-1,1])box(root,0.12,2.75,0.22,brass,s*1.09,1.375,back+0.23);
  box(root,2.3,0.12,0.22,brass,0,2.78,back+0.23);
  const doors=[-1,1].map(s=>box(root,doorWidth/2,doorHeight,0.085,steel,s*doorWidth/4,doorHeight/2,back+0.25));
  const setDoorGap=(gap:number)=>{const g=Math.max(0,Math.min(1,gap));doors.forEach((d,i)=>d.position.x=(i?1:-1)*(doorWidth/4+g*doorWidth/2));};
  setDoorGap(opts.doorGap??0);
  const led=makeLEDTexture();led.redraw(opts.header??"FLOOR 4 / STUCK",false);
  box(root,2.25,0.43,0.12,lit("kit:led-bezel","#283243"),0,3.07,back+0.2);
  const ledMat=new THREE.MeshBasicMaterial({map:led.tex,toneMapped:false});
  mesh(root,new THREE.PlaneGeometry(2.05,0.34),ledMat,0,3.07,back+0.27);
  const panel=new THREE.Group();panel.position.set(side-0.38,0,back+0.34);root.add(panel);
  box(panel,0.54,1.75,0.12,brass,0,1.58,0);
  const buttons={} as Record<ButtonName,THREE.Mesh>;
  const names:ButtonName[]=["4","3","2","1","G","FAN"];
  names.forEach((name,i)=>{
    const y=2.22-i*0.26;
    const m=new THREE.MeshLambertMaterial({color:"#fff4c9",emissive:"#f4b942",emissiveIntensity:0.45});
    const b=cyl(panel,0.065,0.065,0.05,m,0.115,y,0.09,20);b.rotation.x=Math.PI/2;buttons[name]=b;
    const label=tex(128,80,g=>{g.clearRect(0,0,128,80);g.fillStyle="#271f26";g.font="900 46px Arial";g.textAlign="center";g.textBaseline="middle";g.fillText(name,64,40);});
    mesh(panel,new THREE.PlaneGeometry(0.22,0.14),new THREE.MeshBasicMaterial({map:label,transparent:true}),-0.105,y,0.071);
  });
  strut(root,[-side+0.2,1.12,back+0.2],[side-0.8,1.12,back+0.2],0.035,brass,12);
  // Open ceiling frame; grated shaft remains visible in low-angle coverage.
  for(const s of [-1,1])box(root,0.16,0.14,depth,trim,s*(side-0.1),height,0);
  const grate=new THREE.Group();grate.position.set(0,height-0.16,-0.25);root.add(grate);
  const cableMat=lam("kit:cable",()=>({map:tx("kit:cable",makeCableTexture)}));
  for(let x=-0.8;x<=0.81;x+=0.16)box(grate,0.035,0.055,1.15,steel,x,0,0);
  for(const z of [-0.57,0.57])box(grate,1.75,0.07,0.065,brass,0,0,z);
  const cables=[-0.45,0,0.45].map(x=>strut(root,[x,height-0.1,-0.25],[x,height+0.65,-0.25],0.028,cableMat,8));
  const ceilingMat=new THREE.MeshBasicMaterial({color:new THREE.Color("#fff0c2").multiplyScalar(1.4)});
  box(root,1.7,0.06,0.45,ceilingMat,0,height-0.04,0.85);
  return {root,width,depth,height,doors,setDoorGap,led,panel,buttons,grate,cables,ceilingMat,
    buttonWorldPosition:(name:ButtonName,out=new THREE.Vector3())=>{root.updateMatrixWorld(true);return buttons[name].getWorldPosition(out);},
    pinButton:(name:ButtonName,world:THREE.Vector3)=>{root.updateMatrixWorld(true);buttons[name].position.copy(panel.worldToLocal(world.clone()));},
    dispose:()=>{disposeGeometry(root);led.tex.dispose();ledMat.dispose();ceilingMat.dispose();Object.values(buttons).forEach(b=>(b.material as THREE.Material).dispose());panel.traverse(o=>{if(o instanceof THREE.Mesh&&o.material instanceof THREE.MeshBasicMaterial){o.material.map?.dispose();o.material.dispose();}});},
  };
};
export type CorridorOptions={width?:number;depth?:number;height?:number;parent?:THREE.Object3D};
export const buildRainCorridor = (opts:CorridorOptions={}) => {
  const width=opts.width??6.8,depth=opts.depth??5.5,height=opts.height??3.8;
  const root=new THREE.Group();root.name="rain-corridor";opts.parent?.add(root);
  const plaster=lit("corridor:plaster","#ad9d91"),trim=lit("corridor:trim","#65586c");
  box(root,30,0.12,30,lit("corridor:floor","#8f8b99"),0,-0.1,0);
  box(root,width,height,0.18,plaster,0,height/2,-depth/2);
  for(const s of [-1,1])box(root,0.15,height,depth,plaster,s*width/2,height/2,0);
  const rain=makeRainWindowTexture();
  box(root,2.25,2.3,0.12,trim,-2.0,1.95,-depth/2+0.14);
  const rainMat=new THREE.MeshBasicMaterial({map:rain});
  mesh(root,new THREE.PlaneGeometry(2.05,2.1),rainMat,-2.0,1.95,-depth/2+0.22);
  for(const x of [-2.66,-2,-1.34])box(root,0.04,2.1,0.04,trim,x,1.95,-depth/2+0.25);
  box(root,2.1,0.045,0.04,trim,-2,1.95,-depth/2+0.25);
  const doorway=new THREE.Group();doorway.position.x=0.65;root.add(doorway);
  const steel=lam("kit:steel",()=>({map:tx("kit:steel",makeSteelTexture)}));
  box(doorway,2.4,2.85,0.12,trim,0,1.425,-depth/2+0.14);
  box(doorway,2.1,2.65,0.14,lit("corridor:lift-interior","#5d6b7e"),0,1.325,-depth/2+0.22);
  for(const s of [-1,1]){box(doorway,0.16,2.8,0.35,steel,s*1.13,1.4,-depth/2+0.3);box(doorway,0.45,2.62,0.06,steel,s*0.96,1.31,-depth/2+0.35);}
  box(doorway,2.45,0.18,0.3,steel,0,2.86,-depth/2+0.3);
  const sconces:THREE.PointLight[]=[];
  for(const x of [-3.05,2.65]){
    box(root,0.22,0.5,0.17,trim,x,2.45,-depth/2+0.2);
    box(root,0.15,0.38,0.18,new THREE.MeshBasicMaterial({color:new THREE.Color("#ffd19a").multiplyScalar(1.6)}),x,2.45,-depth/2+0.3);
    const light=new THREE.PointLight("#ffc47c",1.6,5);light.position.set(x,2.45,-depth/2+0.65);root.add(light);sconces.push(light);
  }
  return {root,rain,doorway,sconces,redrawRain:(seed:number)=>redrawRainWindow(rain,seed),dispose:()=>{disposeGeometry(root);rain.dispose();rainMat.dispose();}};
};
