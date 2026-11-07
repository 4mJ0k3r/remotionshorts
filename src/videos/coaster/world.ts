// The three coaster sets as one three.js scene. update(id, f, camera) poses everything for shot `id` at frame f (a pure
// function of id + f): set visibility, the bending loop, the cart on its drop, the crane lowering the white arch, the
// Ferris wheel, the camera-relative sun frozen per shot, the gradient sky, cast cards and effects.
import * as THREE from "three";
import { buildSets, LoopArc } from "./build";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage, rivalGrip, cardPoint, RIVAL_SCALE } from "./cast";
import { FPS, SHOTS, RIVAL, camAt, bendAt, archLiftAt, smooth, clamp01, SHOT2_AT, CART_END } from "./story";

const UP = new THREE.Vector3(0, 1, 0);
const setCable = (m: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3) => {
  const d = b.clone().sub(a), L = d.length();
  m.position.copy(a).addScaledVector(d, 0.5); m.scale.set(1, Math.max(0.01, L), 1);
  m.quaternion.setFromUnitVectors(UP, d.normalize());
};

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
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el));
          c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el));
          c = mix(c, c4, smoothstep(e.z, e.w, el));
          float g = pow(max(dot(d, uSun), 0.0), 6.0);
          c = mix(c, uGlow, g * uGlowK);
          gl_FragColor = vec4(c, 1.0); }`,
      side: THREE.BackSide, depthWrite: false, fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(900, 40, 20), this.skyMat);
    this.sky.renderOrder = -1; this.sky.frustumCulled = false; this.sky.layers.set(NOINK);
    R.add(this.sky);
    this.hemi = new THREE.HemisphereLight("#dcecff", "#8fae68", 0.6);
    this.sun = new THREE.DirectionalLight("#fff2dc", 3.0);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(4096, 4096);
    R.add(this.hemi, this.sun, this.sun.target);
    this.sets = buildSets();
    R.add(this.sets.root);
  }

  private pr<T>(name: string) { return this.sets.props[name] as T | undefined; }

  /** camera-relative sun, frozen per shot: the shot's mean view direction turned by az toward screen right, lifted by el */
  private shotSun(id: number, L: LightPreset) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1];
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 3) {
      const c = camAt(id, f), x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2], n = Math.hypot(x, z) || 1;
      fx += x / n; fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1; fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(L.az), el = THREE.MathUtils.degToRad(L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  private animateProps(f: number) {
    // shot 1: the hammer lands at f14 and the loop kinks over the next 10 frames (ease-out, so it snaps)
    const b = bendAt(f);
    this.pr<LoopArc>("loopArc")?.setBend(1 - (1 - b) ** 3);

    // shot 2: the red cart rolls off the scaffolding and down the drop
    const cart = this.pr<THREE.Group>("cart"), curve = this.pr<THREE.Curve<THREE.Vector3>>("dropCurve");
    if (cart && curve) {
      const u = 0.004 + 0.99 * smooth((f - SHOT2_AT) / (CART_END - SHOT2_AT));
      const p = curve.getPointAt(u), d = curve.getTangentAt(u);
      cart.position.copy(p);
      cart.rotation.set(0, Math.atan2(-d.z, d.x), Math.asin(THREE.MathUtils.clamp(d.y, -1, 1)), "YXZ");
    }

    // shot 3: the crane lowers the white arch toward the gap; hook cable + slings follow
    const arch = this.pr<THREE.Group>("arch");
    if (arch) {
      const lift = archLiftAt(f);
      arch.position.y = lift;
      const top = this.pr<THREE.Vector3>("craneTop")!, ends = this.pr<THREE.Vector3[]>("archEnds")!;
      const hookP = new THREE.Vector3(top.x, ends[0].y + lift + 2.2, top.z);
      setCable(this.pr<THREE.Mesh>("hookCable")!, top, hookP.clone().add(new THREE.Vector3(0, 0.25, 0)));
      this.pr<THREE.Mesh>("hookBlock")!.position.copy(hookP);
      const sl = this.pr<THREE.Mesh[]>("slings")!;
      sl.forEach((m, i) => setCable(m, hookP, ends[i].clone().add(new THREE.Vector3(0, lift, 0))));
    }
    const fw = this.pr<THREE.Group>("ferris"), gond = this.pr<THREE.Group[]>("gondolas");
    if (fw && gond) {
      const rot = f * 0.006;
      fw.rotation.z = rot;
      gond.forEach((g, i) => {
        const a = (i / gond.length) * Math.PI * 2;
        g.position.set(Math.cos(a) * 7, Math.sin(a) * 7, 0);
        g.rotation.z = -rot;
      });
    }
    void clamp01;
  }

  /** the winch lever's knob goes to the exact world point of the rival's 2D fist for THIS camera (same billboard
   *  math as the card placement), pushed 8 cm behind the card so the fist is drawn over it; the shaft spans from the
   *  fixed pivot on the winch base to the knob, so contact holds through the whole push-in */
  private aimLever(f: number, cam: THREE.PerspectiveCamera) {
    const lv = this.pr<{ pivot: THREE.Mesh; shaft: THREE.Mesh; knob: THREE.Mesh }>("lever");
    if (!lv) return;
    const [gx, gy] = rivalGrip(f);
    const k = cardPoint(cam.position, RIVAL.rival, RIVAL_SCALE, gx, gy);
    k.addScaledVector(k.clone().sub(cam.position).normalize(), 0.08); // knob radius 0.05 + 3 cm: the whole ball stays behind the card
    const b = new THREE.Vector3(...RIVAL.leverBase);
    lv.pivot.position.copy(b);
    lv.knob.position.copy(k);
    setCable(lv.shaft, b, k);
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene) {
    const t = f / FPS, s = SHOTS[id - 1], L = LIGHTS[s.light];
    // ---- camera ----
    const c = camAt(id, f);
    cam.position.set(...c.pos); cam.up.set(0, 1, 0); cam.lookAt(...c.look); cam.rotateZ(c.roll);
    cam.fov = c.fov; cam.near = 0.05; cam.far = 1200; cam.updateProjectionMatrix(); cam.updateMatrixWorld();
    const focus = new THREE.Vector3(...c.look), dist = cam.position.distanceTo(focus);
    cam.layers.enable(NOINK);
    // ---- set visibility ----
    for (const [name, g] of Object.entries(this.sets.sets)) g.visible = name === s.set;
    this.animateProps(f);
    if (s.set === "rival") this.aimLever(f, cam);
    // ---- light rig ----
    const K = LOOK[s.light], sunDir = this.shotSun(id, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.15 + 4, 6, 34);
    this.sun.position.copy(focus).addScaledVector(sunDir, 160); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 10; sc.far = 360; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    this.sun.shadow.radius = 3;
    TONE.uLitCol.value.set(...L.lit); TONE.uShadeCol.value.set(...L.shade); TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert; TONE.uSideK.value = L.sideK; TONE.uTerm.value = L.term;
    TONE.uBounce.value.set(...K.bounce); TONE.uSat.value = K.sat;
    CHAR.uCharTint.value.set(...L.charTint); CHAR.uCharShade.value = L.charShade; CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad; CHAR.uSideTint.value.set(...L.sideTint);
    // ---- sky, fog ----
    const su = this.skyMat.uniforms;
    K.sky.c.forEach((h, i) => untone(h, su["c" + i].value));
    const e = K.sky.e.map((deg) => THREE.MathUtils.degToRad(deg));
    su.e.value.set(e[1], e[2], e[3], e[4]);
    (su.uSun.value as THREE.Vector3).copy(sunDir);
    untone("#fff6e0", su.uGlow.value as THREE.Color);
    su.uGlowK.value = 0.25;
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog; scene.background = null;
    // ---- cast + effects ----
    const right = new THREE.Vector3().setFromMatrixColumn(cam.matrixWorld, 0);
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
      a.opacity(p.opacity ?? 1);
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
      fx.opacity(p.opacity ?? 1);
      fused.push(fx);
    }
    for (let i = fi; i < this.fxs.length; i++) this.fxs[i].mesh.visible = false;
    this.pool.flush();
    for (const a of used) a.bind();
    for (const fx of fused) fx.bind();
    return focus;
  }
}
