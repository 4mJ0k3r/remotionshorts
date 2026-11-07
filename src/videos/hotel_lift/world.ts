// Three.js world manager for HotelLiftShort:
// Manages lighting, sky, camera, 3D sets, animations, 2D-to-3D hand pinning, and cast actors.
import * as THREE from "three";
import { buildSets, WorldSets } from "./build";
import { LIGHTS, LOOK, LightPreset, LightName } from "./lights";
import { TONE, CHAR, untone } from "./shade";
import { NOINK } from "./ink";
import { Pool, Actor, Fx, stage, handWorldPos } from "./cast";
import { FPS, SHOTS, camAt, glide, clamp01 } from "./story";

const UP = new THREE.Vector3(0, 1, 0);

/** Orients and stretches a cylinder mesh between points a and b */
const setCable = (m: THREE.Mesh, a: THREE.Vector3, b: THREE.Vector3) => {
  const d = b.clone().sub(a);
  const L = d.length();
  m.position.copy(a).addScaledVector(d, 0.5);
  m.scale.set(1, Math.max(0.01, L), 1);
  m.quaternion.setFromUnitVectors(UP, d.normalize());
};

export class World {
  root = new THREE.Group();
  private pool = new Pool();
  private actors: Actor[] = [];
  private fxs: Fx[] = [];
  private hemi: THREE.HemisphereLight;
  private sun: THREE.DirectionalLight;
  private sky: THREE.Mesh;
  private skyMat: THREE.ShaderMaterial;
  private sets: WorldSets;
  private sunCache = new Map<number, THREE.Vector3>();

  constructor() {
    const R = this.root;

    // Gradient Sky Sphere
    this.skyMat = new THREE.ShaderMaterial({
      uniforms: {
        c0: { value: new THREE.Color() },
        c1: { value: new THREE.Color() },
        c2: { value: new THREE.Color() },
        c3: { value: new THREE.Color() },
        c4: { value: new THREE.Color() },
        e: { value: new THREE.Vector4() },
        uSun: { value: new THREE.Vector3(0, 1, 0) },
      },
      vertexShader: `
        varying vec3 vP;
        void main() {
          vP = normalize(position);
          gl_Position = projectionMatrix * modelViewMatrix * vec4(position, 1.0);
        }
      `,
      fragmentShader: `
        uniform vec3 c0, c1, c2, c3, c4;
        uniform vec4 e;
        uniform vec3 uSun;
        varying vec3 vP;
        void main() {
          vec3 d = normalize(vP);
          float el = asin(clamp(d.y, -1.0, 1.0));
          vec3 c = mix(c0, c1, smoothstep(0.0, e.x, el));
          c = mix(c, c2, smoothstep(e.x, e.y, el));
          c = mix(c, c3, smoothstep(e.y, e.z, el));
          c = mix(c, c4, smoothstep(e.z, e.w, el));
          gl_FragColor = vec4(c, 1.0);
        }
      `,
      side: THREE.BackSide,
      depthWrite: false,
      fog: false,
    });
    this.sky = new THREE.Mesh(new THREE.SphereGeometry(900, 32, 16), this.skyMat);
    this.sky.renderOrder = -1;
    this.sky.frustumCulled = false;
    this.sky.layers.set(NOINK);
    R.add(this.sky);

    // Lights
    this.hemi = new THREE.HemisphereLight("#d6ecfa", "#8a7b68", 0.6);
    this.sun = new THREE.DirectionalLight("#fff5e4", 3.0);
    this.sun.castShadow = true;
    this.sun.shadow.mapSize.set(4096, 4096);
    this.sun.shadow.camera.near = 0.5;
    this.sun.shadow.camera.far = 120;
    this.sun.shadow.camera.left = -25;
    this.sun.shadow.camera.right = 25;
    this.sun.shadow.camera.top = 25;
    this.sun.shadow.camera.bottom = -25;
    R.add(this.hemi, this.sun, this.sun.target);

    // 3D Sets
    this.sets = buildSets();
    R.add(this.sets.set1.root);
    R.add(this.sets.set2.root);
    R.add(this.sets.set3.root);
  }

  private actor(i: number) {
    while (this.actors.length <= i) this.actors.push(new Actor(this.root));
    return this.actors[i];
  }

  private fx(i: number) {
    while (this.fxs.length <= i) this.fxs.push(new Fx(this.root));
    return this.fxs[i];
  }

  /** Camera-relative frozen sun per shot */
  private shotSun(id: number, L: LightPreset) {
    let v = this.sunCache.get(id);
    if (v) return v;
    const s = SHOTS[id - 1];
    let fx = 0, fz = 0;
    for (let f = s.a; f < s.b; f += 4) {
      const c = camAt(id, f);
      const x = c.look[0] - c.pos[0], z = c.look[2] - c.pos[2];
      const n = Math.hypot(x, z) || 1;
      fx += x / n;
      fz += z / n;
    }
    const n = Math.hypot(fx, fz) || 1;
    fx /= n; fz /= n;
    const az = THREE.MathUtils.degToRad(L.az);
    const el = THREE.MathUtils.degToRad(L.el);
    const hx = fx * Math.cos(az) - fz * Math.sin(az);
    const hz = fz * Math.cos(az) + fx * Math.sin(az);
    v = new THREE.Vector3(hx * Math.cos(el), Math.sin(el), hz * Math.cos(el)).normalize();
    this.sunCache.set(id, v);
    return v;
  }

  update(id: number, f: number, cam: THREE.PerspectiveCamera, scene: THREE.Scene): THREE.Vector3 {
    const s = SHOTS[id - 1];
    const lightName: LightName = s.light;
    const L = LIGHTS[lightName];
    const look = LOOK[lightName];

    // ---- 1. Camera ----
    const c = camAt(id, f);
    cam.position.set(...c.pos);
    cam.up.set(0, 1, 0);
    cam.lookAt(...c.look);
    cam.fov = c.fov;
    cam.near = 0.1;
    cam.far = 1000;
    cam.updateProjectionMatrix();
    cam.updateMatrixWorld();
    cam.layers.enable(NOINK);

    // ---- 2. Lighting & Sun ----
    const sunDir = this.shotSun(id, L);
    this.sun.position.copy(cam.position).addScaledVector(sunDir, 40);
    this.sun.target.position.copy(cam.position);
    this.sun.color.set(L.sunCol);
    this.sun.intensity = L.sunI;
    this.hemi.color.set(L.sky);
    this.hemi.groundColor.set(L.ground);
    this.hemi.intensity = L.hemiI;

    // Sync shader uniforms with shade.ts & cardshade.ts
    TONE.uLitCol.value.set(...L.lit);
    TONE.uShadeCol.value.set(...L.shade);
    TONE.uShadeLift.value.set(...L.lift);
    TONE.uLambert.value = L.lambert;
    TONE.uSideK.value = L.sideK;
    TONE.uTerm.value = L.term;
    TONE.uBounce.value.set(...look.bounce);
    TONE.uSat.value = look.sat;

    CHAR.uCharTint.value.set(...L.charTint);
    CHAR.uCharShade.value = L.charShade;
    CHAR.uGrad.value = L.charGrad;
    CHAR.uBodyGrad.value = L.bodyGrad;
    CHAR.uSideTint.value.set(...L.sideTint);

    // Sky colors
    const sc = look.sky.c;
    const se = look.sky.e;
    this.skyMat.uniforms.c0.value.copy(untone(sc[0]));
    this.skyMat.uniforms.c1.value.copy(untone(sc[1]));
    this.skyMat.uniforms.c2.value.copy(untone(sc[2]));
    this.skyMat.uniforms.c3.value.copy(untone(sc[3]));
    this.skyMat.uniforms.c4.value.copy(untone(sc[4]));
    this.skyMat.uniforms.e.value.set(
      THREE.MathUtils.degToRad(se[1]),
      THREE.MathUtils.degToRad(se[2]),
      THREE.MathUtils.degToRad(se[3]),
      THREE.MathUtils.degToRad(se[4])
    );
    this.skyMat.uniforms.uSun.value.copy(sunDir);

    // Fog
    if (!scene.fog) {
      scene.fog = new THREE.Fog(L.fog, L.fogNear, L.fogFar);
    } else {
      (scene.fog as THREE.Fog).color.set(L.fog);
      (scene.fog as THREE.Fog).near = L.fogNear;
      (scene.fog as THREE.Fog).far = L.fogFar;
    }

    // ---- 3. STRICT 3D SET ISOLATION (Hard Rule 8) ----
    this.sets.set1.root.visible = (id === 1);
    this.sets.set2.root.visible = (id === 2);
    this.sets.set3.root.visible = (id === 3);

    // ---- 4. 3D Reactive Set Motion ----
    if (id === 1) {
      // Hotel lift: f = 20..80 rises +1.4m
      const liftT = glide(f, 20, 80);
      const yOffset = liftT * 1.4;
      this.sets.set1.hotelLiftRoot.position.y = yOffset;

      // Jackscrews rotate
      for (const j of this.sets.set1.jacks) {
        j.rotation.y = liftT * Math.PI * 6;
      }
    } else if (id === 2) {
      // Engineer cranks lever: f = 131..155 crankP: 0 -> 1
      let crankP = 0.0;
      if (f < 131) crankP = 0.0;
      else if (f <= 155) crankP = clamp01((f - 131) / 21);
      else crankP = 1.0;

      // Closed fist design space coordinate
      const dx = THREE.MathUtils.lerp(168, 132, crankP);
      const dy = 585;

      // 2D-to-3D Hand Contact Pinning (SKILL.md Section 3 Rule B)
      const fistPos = handWorldPos(cam.position, [0.28, 0.0, 0.8], 0.92, dx, dy, -0.08);

      // Jack collar position
      const collarPos = new THREE.Vector3(-0.28, 0.88, 0.8);
      this.sets.set2.collar.rotation.y = crankP * 1.4;

      // Place knob at fistPos
      this.sets.set2.leverKnob.position.copy(fistPos);

      // Connect lever bar between collar and knob
      setCable(this.sets.set2.leverBar, collarPos, fistPos);

      // Lift overhead needle beam (+0.25m)
      this.sets.set2.liftBeam.position.y = 2.35 + crankP * 0.25;
    } else if (id === 3) {
      // Hotel finishes final lift (+0.8m) from f = 195..238, locking at f = 235
      const liftT = glide(f, 195, 238);
      this.sets.set3.hotelLiftRoot.position.y = (liftT - 1.0) * 0.8;
    }

    // ---- 5. Cast Staging ----
    const camRight = new THREE.Vector3();
    cam.matrixWorld.extractBasis(camRight, new THREE.Vector3(), new THREE.Vector3());

    const staged = stage(id, f / FPS, { pos: cam.position, right: camRight });

    // Pose actors
    let aIdx = 0;
    for (const p of staged.places) {
      const act = this.actor(aIdx++);
      act.mesh.position.set(p.x, p.y, p.z);
      const sc = p.scale ?? 1.0;
      act.mesh.scale.set(sc, sc, sc);
      // Yaw billboard: face the camera exactly
      act.mesh.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z);
      act.r = this.pool.req(p.key, p.size![0], p.size![1], p.size![2], p.draw);
      act.mesh.visible = true;
    }
    while (aIdx < this.actors.length) {
      this.actors[aIdx++].mesh.visible = false;
    }

    // Pose FX cards
    let fxIdx = 0;
    for (const p of staged.fx) {
      const fxx = this.fx(fxIdx++);
      fxx.mesh.position.set(p.x, p.y, p.z);
      fxx.mesh.scale.set(p.w, p.h, 1);
      if (p.flat) {
        fxx.mesh.rotation.x = -Math.PI / 2;
        fxx.mesh.rotation.y = 0;
      } else {
        fxx.mesh.rotation.x = 0;
        fxx.mesh.rotation.y = Math.atan2(cam.position.x - p.x, cam.position.z - p.z);
      }
      fxx.use(!!p.soft);
      fxx.r = this.pool.req(p.key, p.cw, p.ch, 1, p.draw);
      fxx.opacity(p.opacity ?? 1.0);
    }
    while (fxIdx < this.fxs.length) {
      this.fxs[fxIdx++].mesh.visible = false;
    }

    // Flush pool and bind textures
    this.pool.flush();
    for (const a of this.actors) if (a.mesh.visible) a.bind();
    for (const x of this.fxs) if (x.mesh.visible) x.bind();

    return new THREE.Vector3(...c.look);
  }
}
