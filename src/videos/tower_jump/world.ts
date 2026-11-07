// The three Tower Jump sets as one three.js scene. update(id, f, camera) is a pure function of (shot, frame): set
// visibility, the rising bascule leaves, the bus on its leaf / in its jump, drifting river foam, the throttle lever
// pinned to the driver's 2D fist (SKILL section 3, Rule B), the camera-relative sun frozen per shot, sky, cards, fx.
import * as THREE from "three";
import { buildSets } from "./build";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage, leverAt, SU, PIV } from "./cast";
import { driverFist } from "./toon";
import { FPS, SHOTS, DRV2, LEVER_PIVOT, camAt, tilt1At, busShot1, busShot3, BusPose } from "./story";

const UP = new THREE.Vector3(0, 1, 0);
const span = (m: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3) => {
  const d = b.clone().sub(a), L = d.length();
  m.position.copy(a).addScaledVector(d, 0.5); m.scale.set(1, Math.max(0.01, L), 1); m.quaternion.setFromUnitVectors(UP, d.normalize());
};
const pose = (g: THREE.Object3D, p: BusPose) => { g.position.set(p.x, p.y, 0); g.rotation.set(0, 0, p.pitch); };

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#cfe4f4", 70, 520);
  private sunCache = new Map<number, THREE.Vector3>();
  private sets: ReturnType<typeof buildSets>;
  private frustum = new THREE.Frustum();
  private m4 = new THREE.Matrix4(); private v = new THREE.Vector3(); private sph = new THREE.Sphere();

  constructor() {
    const R = this.root;
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: { c0: { value: new THREE.Color() }, c1: { value: new THREE.Color() }, c2: { value: new THREE.Color() },
        c3: { value: new THREE.Color() }, c4: { value: new THREE.Color() }, e: { value: new THREE.Vector4() },
        uSun: { value: new THREE.Vector3(0, 1, 0) }, uGlow: { value: new THREE.Color() }, uGlowK: { value: 0 } },
      vertexShader: "varying vec3 vP; void main(){ vP = normalize(position); gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0); }",
      fragmentShader: `uniform vec3 c0, c1, c2, c3, c4, uGlow; uniform vec4 e; uniform vec3 uSun; uniform float uGlowK; varying vec3 vP;
        void main(){ vec3 d = normalize(vP); float el = asin(clamp(d.y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el)); c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el)); c = mix(c, c4, smoothstep(e.z, e.w, el));
          c = mix(c, uGlow, pow(max(dot(d, uSun), 0.0), 6.0) * uGlowK); gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(900, 40, 20), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK); R.add(this.sky);
    this.hemi = new THREE.HemisphereLight("#dcecff", "#8fae68", 0.6);
    this.sun = new THREE.DirectionalLight("#fff2dc", 3.0);
    this.sun.castShadow = true; this.sun.shadow.mapSize.set(4096, 4096);
    R.add(this.hemi, this.sun, this.sun.target);
    this.sets = buildSets(); R.add(this.sets.root);
  }
  private pr<T>(name: string) { return this.sets.props[name] as T | undefined; }

  private shotSun(id: number, L: LightPreset) {
    let v = this.sunCache.get(id); if (v) return v;
    const s = SHOTS[id - 1]; let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 3) { const c = camAt(id, f), x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1; fx += x / n; fz += z / n; }
    const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(L.az), el = THREE.MathUtils.degToRad(L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v); return v;
  }
  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  private animateProps(f: number) {
    const t = tilt1At(f), lv = this.pr<THREE.Group[]>("leaves1");
    if (lv) { lv[0].rotation.z = t; lv[1].rotation.z = -t; }
    const b1 = this.pr<THREE.Group>("bus1"); if (b1) pose(b1, busShot1(f));
    const b3 = this.pr<THREE.Group>("bus3"); if (b3) pose(b3, busShot3(f));
    const wt = this.pr<THREE.Texture>("waterTex"); if (wt) wt.offset.set(f * 0.0007, -f * 0.0019);
    for (const key of ["foam1", "foam3"]) (this.pr<THREE.Mesh[]>(key) ?? []).forEach((m, i) => {
      const h = Math.sin(i * 91.7 + 17.3) * 43758.5453, r = h - Math.floor(h);
      m.position.z = ((r * 40 + f * 0.05) % 40) - 28;               // the river flows toward the lens
      m.position.x = (((r * 7.31) % 1) - 0.5) * 22 + Math.sin(f * 0.03 + i) * 0.3; // pure function of f (no accumulation)
    });
  }

  /** SKILL section 3 Rule B: the throttle knob goes to the world point of the driver's 2D fist (dx, dy) on HIS card's
   *  billboard basis, 8 cm behind the card plane (depthOffset -0.08) so the fist covers it; the shaft spans pivot->knob */
  private pinLever(f: number, cam: THREE.PerspectiveCamera) {
    const lv = this.pr<{ shaft: THREE.Mesh; knob: THREE.Mesh }>("lever"); if (!lv) return;
    const [dx, dy] = driverFist(leverAt(f)), [cx, cy, cz] = DRV2;
    const yaw = Math.atan2(cam.position.x - cx, cam.position.z - cz);
    const rightX = Math.cos(yaw), rightZ = -Math.sin(yaw), fwdX = Math.sin(yaw), fwdZ = Math.cos(yaw);
    const localX = (dx - 300) * SU, localY = (PIV - dy) * SU, depthOffset = -0.08;
    const k = new THREE.Vector3(cx + rightX * localX + fwdX * depthOffset, cy + localY, cz + rightZ * localX + fwdZ * depthOffset);
    lv.knob.position.copy(k);
    span(lv.shaft, new THREE.Vector3(...LEVER_PIVOT), k);
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], L = LIGHTS[s.light];
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 1200; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = new THREE.Vector3(...c.look), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    for (const [name, g] of Object.entries(this.sets.sets)) g.visible = name === s.set;
    this.animateProps(f);
    if (s.set === "cab") this.pinLever(f, cam);
    // ---- light rig ----
    const K = LOOK[s.light], sunDir = this.shotSun(id, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 0.9 + 4, 6, 36);
    this.sun.position.copy(focus).addScaledVector(sunDir, 160); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 10; sc.far = 360; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12); this.sun.shadow.radius = 3;
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term;
    TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    (su.uSun.value as THREE.Vector3).copy(sunDir); untone("#fff6e0", su.uGlow.value as THREE.Color); su.uGlowK.value = 0.25;
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog; scene.background = null;
    // ---- cast + effects ----
    const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
    const st = stage(id, t, { pos: cam.position, right, sun: sunDir });
    this.frustum.setFromProjectionMatrix(this.m4.multiplyMatrices(cam.projectionMatrix, cam.matrixWorldInverse));
    let ai = 0; const used: Actor[] = [];
    for (const p of st.places) {
      const sc2 = p.scale ?? 1;
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y + 1.1 * sc2, p.z), 3.5))) continue;
      const a = this.actor(ai++), [w, h, k] = p.size ?? [300, 500, 0.5];
      a.r = this.pool.req(p.key, w, h, k, p.draw);
      a.mesh.visible = true; a.mesh.position.set(p.x, p.y, p.z);
      a.mesh.rotation.set(0, p.yaw ?? Math.atan2(cam.position.x - p.x, cam.position.z - p.z), p.roll ?? 0);
      a.mesh.scale.set(sc2, sc2, sc2); a.mesh.castShadow = L.actorShadow; a.opacity(p.opacity ?? 1); used.push(a);
    }
    for (let i = ai; i < this.actors.length; i++) this.actors[i].mesh.visible = false;
    let fi = 0; const fused: Fx[] = [];
    for (const p of st.fx) {
      if (!this.frustum.intersectsSphere(this.sph.set(this.v.set(p.x, p.y, p.z), Math.max(p.w, p.h)))) continue;
      const fx = this.fx(fi++);
      fx.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw); fx.use(!!p.soft);
      fx.mesh.visible = true; fx.mesh.position.set(p.x, p.y, p.z);
      if (p.flat) fx.mesh.rotation.set(-Math.PI / 2, 0, p.rot ?? 0);
      else { fx.mesh.quaternion.copy(cam.quaternion); fx.mesh.rotateZ(p.rot ?? 0); }
      fx.mesh.scale.set(p.w, p.h, 1); fx.opacity(p.opacity ?? 1); fused.push(fx);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const fx of fused) fx.bind();
    return focus;
  }
}
