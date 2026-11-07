// The pardon location as one three.js scene: grass valley, cobbled market square with the PARDONS booth and a clock
// tower, the dirt road out of town, forest both sides, clouds, sun haze, the covered cart (posed per frame with its
// gold chest) and the cast. update(id, f, camera) poses everything for shot `id` at frame f (pure function of id + f).
import * as THREE from "three";
import { GLTFLoader } from "three/examples/jsm/loaders/GLTFLoader.js";
import { staticFile } from "remotion";
import { buildPardon, V, lam, Kit, Ray } from "./build";
import { beamHD, cloudHD, grassHD } from "./paint";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, twoTone, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage } from "./cast";
import { FPS, D0, SHOTS, cartX, camAt, STRIKE, knight4, knightPayoff, clamp01 } from "./story";

// ---------------- assets ----------------
const KENNEY = ["tree_oak", "tree_default", "tree_detailed", "tree_fat", "tree_cone", "tree-high-round", "tree", "plant_bushLarge",
  "plant_bushDetailed", "plant_bush", "hedge", "flower_redA", "flower_yellowA", "flower_purpleA", "grass_large", "grass", "lantern", "cart",
  "stall-red", "stall-green", "stall-bench", "banner-red", "banner-green", "windmill"];
let kitP: Promise<Kit> | null = null;
export const loadKit = () => {
  if (!kitP) {
    const loader = new GLTFLoader();
    kitP = Promise.all(KENNEY.map((n) => loader.loadAsync(staticFile(`bridge/kenney/${n}.glb`)).then((g) => [n, g.scene] as const).catch(() => [n, null] as const)))
      .then((list) => Object.fromEntries(list.filter((e) => e[1]).map(([n, s]) => [n, s!])) as Kit);
  }
  return kitP;
};

// ---------------- sun / sky helpers ----------------
/** per-shot camera-relative sun: +az = toward screen right, el = elevation. Both acts put the sun BEHIND the camera's
 *  right shoulder (az ~150) so the sides we see - booth front, robes, cart boards, faces - are the lit ones; the long
 *  golden shadows then run away from the lens across the road. */
const SUN_SHOT: Record<number, { az?: number; el?: number }> = {
  1: { az: 146, el: 42 }, 2: { az: 150, el: 40 }, 3: { az: 150, el: 38 },
  4: { az: 148, el: 12 }, 5: { az: 150, el: 10 }, 6: { az: 155, el: 9 },
};
const discTex = () => {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d")!;
  const gr = g.createRadialGradient(64, 64, 58, 64, 64, 64);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(1, "rgba(255,255,255,0)");
  g.fillStyle = gr; g.fillRect(0, 0, 128, 128);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
};
const haloTex = () => {
  const S = 256, c = document.createElement("canvas"); c.width = c.height = S;
  const g = c.getContext("2d")!, im = g.createImageData(S, S);
  for (let y = 0; y < S; y++) for (let x = 0; x < S; x++) {
    const u = Math.hypot(x - 127.5, y - 127.5) / 128;
    const a = (0.55 * Math.exp(-((u / 0.25) ** 2)) + 0.35 * Math.exp(-((u / 0.6) ** 2))) * (1 - Math.min(1, Math.max(0, (u - 0.8) / 0.2)));
    const i = (y * S + x) * 4; im.data[i] = im.data[i + 1] = im.data[i + 2] = 255; im.data[i + 3] = Math.round(255 * Math.min(1, a));
  }
  g.putImageData(im, 0, 0);
  const t = new THREE.CanvasTexture(c); t.colorSpace = THREE.SRGBColorSpace; return t;
};
/** flat ground quad; ux/uz = texture repeats */
const quadUp = (x0: number, x1: number, z0: number, z1: number, ux: number, uz: number, y: number) => {
  const g = new THREE.BufferGeometry();
  g.setAttribute("position", new THREE.Float32BufferAttribute([x0, y, z1, x1, y, z1, x1, y, z0, x0, y, z0], 3));
  g.setAttribute("normal", new THREE.Float32BufferAttribute([0, 1, 0, 0, 1, 0, 0, 1, 0, 0, 1, 0], 3));
  g.setAttribute("uv", new THREE.Float32BufferAttribute([0, uz, ux, uz, ux, 0, 0, 0], 2));
  g.setIndex([0, 1, 2, 0, 2, 3]);
  return g;
};
/** every lens position of the film looking at its subject: centre, sides and top of frame (houses / trees there are left out) */
const sightLines = (): Ray[] => {
  const out: Ray[] = [];
  for (const s of SHOTS) for (let f = s.a - 6; f < s.b + 6; f += 2) {
    const c = camAt(s.id, Math.max(0, f)), o = V(...c.pos), look = V(...c.look);
    const fw = look.clone().sub(o), len = fw.length();
    fw.normalize();
    const rt = fw.clone().cross(V(0, 1, 0)).normalize(), up = rt.clone().cross(fw);
    const ty = Math.tan((c.fov * Math.PI) / 360), tx = ty * (9 / 16);
    for (const [sx, sy] of [[0, 0], [-0.6, 0], [0.6, 0], [0, 0.6], [0, -0.4]])
      out.push({ o, d: fw.clone().addScaledVector(rt, sx * tx).addScaledVector(up, sy * ty), len, core: sx === 0 && sy === 0 });
  }
  return out;
};

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight; private fill: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#bccbec", 25, 320);
  private sunDisc: THREE.Sprite; private sunHalo: THREE.Sprite;
  private sunCache = new Map<number, THREE.Vector3>();
  private cloudMaps: Record<"day" | "golden", THREE.Texture[]>;
  private clouds: THREE.Mesh[] = [];
  private cart = new THREE.Group();
  private wheels: THREE.Object3D[] = [];
  private chest = new THREE.Group();
  private chestLid = new THREE.Group();
  private frustum = new THREE.Frustum();
  private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();

  constructor(kit: Kit) {
    const R = this.root;
    // ---- sky: 5 colour stops by elevation (tone-map-inverted), plus a warm lobe toward the sun ----
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() },
        c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() },
        uSun: { value: new THREE.Vector3(0, 1, 0) }, uGlow: { value: new THREE.Color() }, uGlowK: { value: 0 } },
      vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: `uniform vec3 c0, c1, c2, c3, c4, uGlow; uniform vec4 e; uniform vec3 uSun; uniform float uGlowK; varying vec3 vP;
        void main(){ vec3 d = normalize(vP); float el = asin(clamp(d.y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el));
          c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el));
          c = mix(c, c4, smoothstep(e.z, e.w, el));
          float g = pow(max(dot(d, uSun), 0.0), 6.0);
          c = mix(c, uGlow, g * uGlowK);
          gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(1100, 48, 24), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK);
    R.add(this.sky);
    this.sunDisc = new THREE.Sprite(new THREE.SpriteMaterial({ map: discTex(), color: new THREE.Color(6.0, 4.4, 2.4), fog: false, depthWrite: false }));
    this.sunHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex(), color: new THREE.Color(1, 1, 1), fog: false, depthWrite: false, depthTest: true,
      transparent: true, blending: THREE.AdditiveBlending }));
    this.sunDisc.renderOrder = -0.5; this.sunHalo.renderOrder = 5;
    for (const m of [this.sunDisc, this.sunHalo]) { m.frustumCulled = false; m.layers.set(NOINK); R.add(m); }
    this.hemi = new THREE.HemisphereLight("#cfe6ff", "#6c5c8c", 1.1);
    this.sun = new THREE.DirectionalLight("#fff0d6", 2.6);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(4096, 4096);
    this.fill = new THREE.DirectionalLight("#9fb8ff", 0.35);
    R.add(this.hemi, this.sun, this.sun.target, this.fill, this.fill.target);
    this.cloudMaps = { day: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.day.cloud)), golden: [0, 1, 2, 3].map((k) => cloudHD(k, LOOK.golden.cloud)) };
    for (let i = 0; i < 9; i++) {
      const a = (i / 9) * Math.PI * 2 + 0.3, d = 560 + (i % 3) * 60;
      const m = new THREE.Mesh(new THREE.PlaneGeometry(1, 1), new THREE.MeshBasicMaterial({ map: this.cloudMaps.day[i % 4], color: new THREE.Color(1.1, 1.1, 1.1), transparent: true, depthWrite: false, fog: false }));
      const w = 150 + (i % 4) * 34;
      m.position.set(Math.cos(a) * d, 120 + (i % 4) * 38, Math.sin(a) * d); m.scale.set(w, w / 2, 1);
      m.layers.set(NOINK);
      this.clouds.push(m); R.add(m);
    }

    // ---- ground + the static place ----
    const grass = new THREE.Mesh(quadUp(-420, 420, -420, 420, 210, 210, D0 - 0.004), lam("grassHD", () => ({ map: grassHD() })));
    grass.receiveShadow = true;
    R.add(grass);
    buildPardon(R, kit, sightLines());

    this.buildCart();
    this.buildChest();
    R.add(this.cart, this.chest);
  }

  // ---------------- the cart ----------------
  private buildCart() {
    const G = this.cart;
    const wood = lam("cartWood", () => ({ map: beamHD() }));
    const woodD = lam("cartWoodD", () => ({ color: "#6e482c" }));
    const iron = lam("cartIron", () => ({ color: "#4b4a52" }));
    const put = (g: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, ry = 0, rz = 0) => {
      const mesh = new THREE.Mesh(g, m);
      mesh.position.set(x, y, z); mesh.rotation.set(0, ry, rz);
      mesh.castShadow = true; mesh.receiveShadow = true;
      G.add(mesh);
      return mesh;
    };
    put(new THREE.BoxGeometry(1.9, 0.12, 0.9), woodD, 0, 0.62, 0);
    put(new THREE.BoxGeometry(2.1, 0.10, 1.24), wood, 0, 0.93, 0);
    for (const z of [-0.635, 0.635]) put(new THREE.BoxGeometry(2.1, 0.30, 0.07), wood, 0, 1.13, z);
    for (const x of [-1.05, 1.05]) put(new THREE.BoxGeometry(0.07, 0.30, 1.2), wood, x, 1.13, 0);
    for (const x of [-1.02, 1.02]) for (const z of [-0.6, 0.6]) put(new THREE.BoxGeometry(0.09, 0.42, 0.09), woodD, x, 1.19, z);
    for (const x of [-0.62, 0.62]) {
      const axle = new THREE.CylinderGeometry(0.045, 0.045, 1.5, 10);
      axle.rotateX(Math.PI / 2);
      put(axle, iron, x, 0.47, 0);
    }
    for (const x of [-0.62, 0.62]) for (const z of [-0.68, 0.68]) {
      const wheel = new THREE.Group();
      const rim = new THREE.Mesh(new THREE.TorusGeometry(0.44, 0.055, 8, 22), woodD);
      const hub = new THREE.Mesh(new THREE.CylinderGeometry(0.075, 0.075, 0.14, 10).rotateX(Math.PI / 2), iron);
      rim.castShadow = hub.castShadow = true; rim.receiveShadow = hub.receiveShadow = true;
      wheel.add(rim, hub);
      for (let k = 0; k < 6; k++) {
        const sp = new THREE.Mesh(new THREE.BoxGeometry(0.05, 0.80, 0.05), wood);
        sp.rotation.z = (k * Math.PI) / 6; sp.castShadow = true; sp.receiveShadow = true;
        wheel.add(sp);
      }
      wheel.position.set(x, 0.46, z);
      G.add(wheel); this.wheels.push(wheel);
    }
    // shafts, angled down toward the puller
    for (const z of [-0.42, 0.42]) {
      const a = V(1.04, 0.74, z), c = V(2.06, 0.42, z);
      const len = a.distanceTo(c);
      const beam = new THREE.Mesh(new THREE.BoxGeometry(0.07, len, 0.07), woodD);
      beam.position.copy(a.clone().add(c).multiplyScalar(0.5));
      beam.quaternion.setFromUnitVectors(V(0, 1, 0), c.clone().sub(a).normalize());
      beam.castShadow = beam.receiveShadow = true;
      G.add(beam);
    }
  }

  // ---------------- the gold chest ----------------
  private buildChest() {
    const C = this.chest;
    // textured planks: the flat colour read as a single untextured brown slab on the cart
    const wood = lam("chestWoodM", () => ({ map: beamHD() }));
    const dark = lam("chestDarkM", () => ({ color: "#3a2417" }));
    const band = lam("chestBandM", () => ({ color: "#53505a" }));
    const gold = twoTone(new THREE.MeshPhongMaterial({ color: "#d8a92e", specular: "#ffe6a0", shininess: 90 }), 0.2);
    const put = (g: THREE.BufferGeometry, m: THREE.Material, x: number, y: number, z: number, parent: THREE.Object3D = C) => {
      const mesh = new THREE.Mesh(g, m);
      mesh.position.set(x, y, z); mesh.castShadow = true; mesh.receiveShadow = true;
      parent.add(mesh);
      return mesh;
    };
    put(new THREE.BoxGeometry(0.66, 0.32, 0.46), wood, 0, 0.16, 0);
    put(new THREE.BoxGeometry(0.58, 0.01, 0.38), dark, 0, 0.315, 0);
    for (const x of [-0.19, 0.19]) put(new THREE.BoxGeometry(0.09, 0.34, 0.48), band, x, 0.17, 0);
    const goldPile = [[0, 0.28, 0, 0.13], [-0.19, 0.29, 0.06, 0.10], [0.2, 0.28, -0.05, 0.11], [0.05, 0.3, 0.12, 0.09], [-0.08, 0.29, -0.12, 0.10], [0.24, 0.28, 0.1, 0.075]];
    for (const [x, y, z, rad] of goldPile) put(new THREE.SphereGeometry(rad, 12, 9), gold, x, y, z);
    for (const [x, z] of [[-0.28, -0.14], [0.3, 0.08], [0.14, -0.18]]) put(new THREE.CylinderGeometry(0.055, 0.055, 0.02, 10), gold, x, 0.335, z);
    this.chestLid.position.set(0, 0.32, 0.23);
    put(new THREE.BoxGeometry(0.66, 0.10, 0.46), wood, 0, 0.05, -0.23, this.chestLid);
    for (const x of [-0.19, 0.19]) put(new THREE.BoxGeometry(0.09, 0.11, 0.48), band, x, 0.05, -0.23, this.chestLid);
    put(new THREE.BoxGeometry(0.09, 0.11, 0.06), gold, 0, 0.14, -0.23, this.chestLid);
    C.add(this.chestLid);
    C.rotation.order = "YXZ";
    C.scale.setScalar(1.35); // the loot still reads over the cart's 1.28 m side boards
  }

  /** camera-relative sun, frozen per shot: the shot's mean view direction turned by az toward screen right, lifted by el */
  private shotSun(id: number, L: LightPreset, light: "day" | "golden") {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1];
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 3) {
      const c = camAt(id, f), x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(SUN_SHOT[id]?.az ?? L.az), el = THREE.MathUtils.degToRad(SUN_SHOT[id]?.el ?? L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az); // screen right = (-fz, fx)
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    void light;
    this.sunCache.set(id, v);
    return v;
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], L = LIGHTS[s.light];
    // ---- camera ----
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.2; cam.far = 1500; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = V(...c.look), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    // ---- light rig: camera-relative sun frozen per shot, two-tone uniforms, shadow fit ----
    const K = LOOK[s.light], sunDir = this.shotSun(id, L, s.light);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    let Rr = THREE.MathUtils.clamp(dist * 1.15 + 7, 12, 95);
    if (s.light === "golden") Rr = Math.max(Rr, 30);
    this.sun.position.copy(focus).addScaledVector(sunDir, 220); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 20; sc.far = 480; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    this.sun.shadow.radius = s.light === "golden" ? 11 : 5;
    this.fill.intensity = 0;
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term;
    TONE.uBounce.value.set(...LOOK[s.light].bounce); TONE.uSat.value = LOOK[s.light].sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    // ---- sky, fog, sun haze, clouds ----
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    (su.uSun.value as THREE.Vector3).copy(sunDir);
    untone(s.light === "golden" ? "#ffdca6" : "#fff3da", su.uGlow.value as THREE.Color);
    su.uGlowK.value = s.light === "golden" ? 0.5 : 0.22;
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog; scene.background = null;
    const showSun = s.light === "golden";
    this.sunDisc.visible = this.sunHalo.visible = showSun;
    if (showSun) {
      this.sunDisc.position.copy(cam.position).addScaledVector(sunDir, 900);
      this.sunDisc.scale.setScalar(2 * 900 * Math.tan(THREE.MathUtils.degToRad(1.7)));
      this.sunHalo.position.copy(this.sunDisc.position); this.sunHalo.scale.setScalar(2 * 900 * Math.tan(THREE.MathUtils.degToRad(24)));
      (this.sunHalo.material as THREE.SpriteMaterial).color.set(L.sunDisc).multiplyScalar(1.25);
    }
    for (let i = 0; i < this.clouds.length; i++) {
      const m = this.clouds[i], mat = m.material as THREE.MeshBasicMaterial;
      m.lookAt(cam.position.x, m.position.y, cam.position.z);
      mat.map = this.cloudMaps[s.light][i % 4];
    }
    // ---- cart + chest ----
    const cx = cartX(id, f);
    this.cart.visible = id >= 3;
    this.cart.position.set(cx, D0, id === 6 ? 4.4 : 1.6); // the stopped cart has been pulled onto the south verge
    for (const w of this.wheels) w.rotation.z = -cx / 0.46;
    this.poseChest(id, f, cx);
    // ---- cast + effects ----
    const right = V(0, 0, 0).setFromMatrixColumn(cam.matrixWorld, 0);
    const st = stage(id, t, { pos: cam.position, right, sun: sunDir });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0;
    const used: Actor[] = [];
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y + 1.1 * sc2, p.z), 3.5))) continue;
      const a = this.actor(ai++);
      const [w, h, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true;
      a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(p.mirror ? -sc2 : sc2, sc2, sc2);
      a.mesh.castShadow = L.actorShadow;
      used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0;
    const fused: Fx[] = [];
    for (const p of st.fx) {
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y, p.z), Math.max(p.w, p.h)))) continue;
      const fx = this.fx(fi++);
      fx.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      fx.use(!!p.soft);
      fx.mesh.visible = true;
      fx.mesh.position.set(p.x, p.y, p.z);
      if (p.flat) fx.mesh.rotation.set(-Math.PI / 2, 0, p.rot ?? 0);
      else { fx.mesh.quaternion.copy(cam.quaternion); fx.mesh.rotateZ(p.rot ?? 0); }
      fx.mesh.scale.set(p.w, p.h, 1);
      fused.push(fx);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const fx of fused) fx.bind();
    return focus;
  }

  /** chest on the cart bed, yanked into the knight's arm at the strike, on the ground in the receipt, carried in the payoff */
  private poseChest(id: number, f: number, cx: number) {
    const C = this.chest, t = f / FPS;
    if (id <= 2) { C.visible = false; return; }
    C.visible = true;
    // On the cart the chest only has to clear the 1.28 m side boards; carried, it shrinks to a waist prop so the lid
    // tops out below 1 m and the knight's face and helmet stay fully readable above it.
    // On the cart the lid is open and out of the way: swinging it down over the near side covered the boards
    const onCart = (x: number) => {
      C.scale.setScalar(1.35);
      C.position.set(x + 0.42, 0.98, 1.6); C.rotation.y = 0.12; this.chestLid.visible = false;
    };
    if (id === 3) onCart(cx);
    else if (id === 4) {
      const k = knight4(t);
      if (t < STRIKE + 0.12) onCart(cartX(4, f));
      else {
        const u = clamp01((t - STRIKE - 0.12) / 0.22);
        const fx0 = cartX(4, STRIKE) + 0.42, fy0 = 0.98, fz0 = 1.6;
        const tx = k.x - 0.24, ty = 0.66, tz = k.z - 0.14; // waist height, at his side on the camera flank
        C.scale.setScalar(1.35 + (0.7 - 1.35) * u);
        C.position.set(fx0 + (tx - fx0) * u, fy0 + (ty - fy0) * u + 0.24 * Math.sin(Math.PI * u), fz0 + (tz - fz0) * u);
        C.rotation.y = 0.12 + 0.55 * u;
        this.chestLid.visible = true; this.chestLid.rotation.x = 0;
      }
    } else if (id === 5) {
      C.scale.setScalar(1.35);
      this.chestLid.visible = true; this.chestLid.rotation.x = 0;
      C.position.set(64.12, 0, 2.5); C.rotation.y = 0.62;
    } else {
      C.scale.setScalar(0.75);
      this.chestLid.visible = true; this.chestLid.rotation.x = 0;
      const k = knightPayoff(f);
      C.position.set(k.x + 0.12, 0.64, k.z + 0.2); C.rotation.y = 0.2;
    }
  }
}
