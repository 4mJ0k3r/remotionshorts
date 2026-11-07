// The four school zones as one three.js scene: the 24 m classroom, the 45 m locker hallway, the 26 m chemistry lab
// and the 80 m plaza. update(id, f, camera) poses everything for shot `id` at frame f (pure function of id + f): set
// visibility, animated props (fans, strobes, doors, chair, vent, hologram, lightbars, helicopter), camera-relative
// key light frozen per shot, gradient sky, cast cards and effects.
import * as THREE from "three";
import { buildSets } from "./build";
import { LIGHTS, LOOK, LightPreset } from "./lights";
import { TONE, CHAR, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage } from "./cast";
import {
  FPS, SHOTS, camAt, PAN_AT, DOOR_AT, SLAM_AT, SLAM2_AT, VENT_AT, FROST_AT, EXIT_AT, THWACK_AT, clamp01, smooth,
} from "./story";

/** per-shot sun overrides (az/el in degrees from the shot's forward axis, +az = screen right) */
const SUN_SHOT: Record<number, { az?: number; el?: number }> = {
  // the plaza sun sits behind the facade so the two-storey front gets a hard side key and long shadows
  9: { az: 118, el: 38 },
  10: { az: 118, el: 38 },
};

const discTex = () => {
  const c = document.createElement("canvas"); c.width = c.height = 128;
  const g = c.getContext("2d")!;
  const gr = g.createRadialGradient(64, 64, 54, 64, 64, 64);
  gr.addColorStop(0, "rgba(255,255,255,1)"); gr.addColorStop(0.62, "rgba(255,255,255,1)"); gr.addColorStop(1, "rgba(255,255,255,0)");
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

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight; private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh; private skyMat: THREE.ShaderMaterial;
  private fog = new THREE.Fog("#2a201c", 8, 42);
  private sunDisc: THREE.Sprite; private sunHalo: THREE.Sprite;
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
    this.sunDisc = new THREE.Sprite(new THREE.SpriteMaterial({ map: discTex(), color: new THREE.Color(6.0, 4.4, 2.4), fog: false, depthWrite: false }));
    this.sunHalo = new THREE.Sprite(new THREE.SpriteMaterial({ map: haloTex(), color: new THREE.Color(1, 1, 1), fog: false, depthWrite: false, depthTest: true,
      transparent: true, blending: THREE.AdditiveBlending }));
    this.sunDisc.renderOrder = -0.5; this.sunHalo.renderOrder = 5;
    for (const m of [this.sunDisc, this.sunHalo]) { m.frustumCulled = false; m.layers.set(NOINK); R.add(m); }
    this.hemi = new THREE.HemisphereLight("#cfe6ff", "#6c5c8c", 1.1);
    this.sun = new THREE.DirectionalLight("#fff0d6", 2.6);
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
    const az = THREE.MathUtils.degToRad(SUN_SHOT[id]?.az ?? L.az), el = THREE.MathUtils.degToRad(SUN_SHOT[id]?.el ?? L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az), hz = fz * Math.cos(az) + fx * Math.sin(az); // screen right = (-fz, fx)
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  private actor(i: number) { while (this.actors.length <= i) this.actors.push(new Actor(this.root)); return this.actors[i]; }
  private fx(i: number) { while (this.fxs.length <= i) this.fxs.push(new Fx(this.root)); return this.fxs[i]; }

  private animateProps(id: number, f: number) {
    const fans = this.pr<THREE.Group[]>("fans");
    if (fans) for (const r of fans) r.rotation.y = f * 0.22;

    // red lockdown strobes: they only exist in the classroom, and pulse after the window pan.
    // aK decays to 0.22 across the beat-2 cut: the alarm is the flash, not the lighting of the whole act, and a
    // full-strength red wash for 900 frames is what made the door shots read as a pink box.
    const alarm = f >= PAN_AT;
    const aK = f < 375 ? 1 : Math.max(0.22, 1 - (f - 375) / 260);
    const pulse = 0.55 + 0.45 * Math.sin((f / FPS) * 9.5);
    for (const g of this.pr<THREE.Mesh[]>("strobeGlows") ?? []) g.visible = alarm;
    for (const b of this.pr<THREE.Mesh[]>("strobeBeams") ?? []) {
      b.visible = alarm;
      const bm = b.material as THREE.MeshBasicMaterial;
      bm.opacity = (0.05 + 0.17 * pulse) * aK;
    }
    const red = this.pr<THREE.PointLight>("alarmLight");
    if (red) red.intensity = alarm ? (1.5 + 1.5 * pulse) * aK : 0;

    // classroom door: kicked open at DOOR_AT, then left ajar
    const door = this.pr<THREE.Group>("classDoor");
    if (door) door.rotation.y = -1.32 * smooth((f - DOOR_AT) / 14);

    // the hero's chair is NOT a 3D prop: it is drawn onto his 2D hands in toon.ts (mode "lift"/"smash"), so no
    // mesh can drift away from the card that is holding it.

    // hallway hologram + neon breathing
    const holo = this.pr<THREE.Group>("holo");
    if (holo) { holo.rotation.y = f * 0.014; const k = 1 + 0.03 * Math.sin(f * 0.09); holo.scale.set(k, k, k); }
    const neon = this.pr<THREE.MeshBasicMaterial>("neon");
    if (neon) { const k = 0.85 + 0.15 * Math.sin(f * 0.07); neon.color.setRGB(0.4 * k, 2.2 * k, 3.0 * k); }

    // lab vent panel pops open as the hero drops
    const vent = this.pr<THREE.Group>("ventPanel");
    if (vent) vent.rotation.x = -1.15 * smooth((f - VENT_AT) / 12);

    // courtyard doors burst open for the exit
    const dl = this.pr<THREE.Group>("courtDoorL"), dr = this.pr<THREE.Group>("courtDoorR");
    if (dl && dr) {
      const u = smooth((f - EXIT_AT) / 24);
      dl.rotation.y = 1.35 * u; dr.rotation.y = -1.35 * u;
    }

    // police lightbars alternate red / blue
    const bars = this.pr<THREE.Mesh[]>("carBars") ?? [];
    bars.forEach((m, i) => {
      const car = Math.floor(i / 2), red2 = i % 2 === 0;
      const on = (Math.floor(f / 7) + car) % 2 === 0;
      const mat = m.material as THREE.MeshBasicMaterial;
      if (red2) mat.color.setRGB(on ? 3.2 : 0.14, 0.16, 0.16);
      else mat.color.setRGB(0.14, 0.24, on ? 3.2 : 0.14);
    });

    // helicopter hover + rotors
    const heli = this.pr<THREE.Group>("heli");
    if (heli) {
      heli.position.y = 11.5 + 0.35 * Math.sin((f / FPS) * 1.1);
      const rotor = this.pr<THREE.Group>("heliRotor"), tail = this.pr<THREE.Group>("heliTail");
      if (rotor) rotor.rotation.y = f * 2.4;
      if (tail) tail.rotation.x = f * 5.2;
    }
    void id; void FROST_AT; void SLAM2_AT; void THWACK_AT; void clamp01;
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
    this.animateProps(id, f);
    // ---- light rig ----
    const K = LOOK[s.light], sunDir = this.shotSun(id, L);
    this.hemi.color.set(L.sky); this.hemi.groundColor.set(L.ground); this.hemi.intensity = L.hemiI;
    this.sun.color.set(L.sunCol); this.sun.intensity = L.sunI;
    const Rr = THREE.MathUtils.clamp(dist * 1.15 + 2.5, 5, 30);
    this.sun.position.copy(focus).addScaledVector(sunDir, 140); this.sun.target.position.copy(focus);
    const sc = this.sun.shadow.camera;
    sc.left = -Rr; sc.right = Rr; sc.top = Rr; sc.bottom = -Rr; sc.near = 10; sc.far = 320; sc.updateProjectionMatrix();
    this.sun.shadow.bias = L.bias; this.sun.shadow.normalBias = L.normalBias * (Rr / 12);
    this.sun.shadow.radius = 5;
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
    untone(s.light === "plaza" ? "#ffe6c2" : "#fff3da", su.uGlow.value as THREE.Color);
    su.uGlowK.value = s.light === "plaza" ? 0.3 : s.light === "hall" ? 0.08 : 0.14;
    this.sky.position.copy(cam.position);
    untone(L.fog, this.fog.color); this.fog.near = L.fogNear; this.fog.far = L.fogFar;
    scene.fog = this.fog; scene.background = null;
    this.sunDisc.visible = this.sunHalo.visible = false;
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
