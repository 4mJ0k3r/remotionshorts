// "Age 18" — 61.6 s (1848 f @ 30 fps), twelve shots through one life that never ages. Same calibrated post chain as
// the earlier shorts: InkPass (world ink) -> lens blur pre + main (thin-lens DOF) -> [bloom (emissive only) +
// NEUTRAL tone mapping + colour grade] (one merged EffectPass), MSAA 4. Ink before the DOF, bloom after, grade
// display-referred. Places crossfade by stacking a second canvas; the 18/18/18 spark adds a 4-frame white flash.
// The age badge is an HTML overlay projected from a world anchor above the hero's hood, so its text stays crisp.
import React, { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { AbsoluteFill, Audio, continueRender, delayRender, getInputProps, staticFile, useCurrentFrame } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";
import { World } from "./world";
import { InkPass, noInkFallback } from "./ink";
import { LensBlur, GrainEffect } from "./lensblur";
import { GradeEffect, GRADES, GRADE_STRENGTH, gradeFor } from "./grade";
import { LIGHTS } from "./lights";
import { TOTAL, FLASH_AT, SHOTS, layersAt, dofAt, camAt, badgeAge } from "./story";
import { badgeAt } from "./cast";

export const AGE18_FRAMES = TOTAL;

type PostToggles = { ink: boolean; lens: boolean; pre: boolean; bloom: boolean; grade: boolean; grain: boolean; composer: boolean };
const toggles = (): PostToggles => ({ ink: true, lens: true, pre: true, bloom: true, grade: true, grain: false, composer: true, ...((getInputProps() as { post?: Partial<PostToggles> }).post ?? {}) });

/** Bloom for emissive sources only. MIP chain pinned to 540x960-equivalent whatever the output size. */
const makeBloom = () => {
  const b = new BloomEffect({ blendFunction: BlendFunction.ADD, intensity: 0.5, luminanceThreshold: 1.0, luminanceSmoothing: 0.2, mipmapBlur: true, levels: 6, radius: 0.6 });
  const mip = b.mipmapBlurPass;
  const setSize = mip.setSize.bind(mip);
  mip.setSize = (w: number, h: number) => setSize(Math.round((1920 * w) / Math.max(h, 1)), 1920);
  return b;
};

const fwd = new THREE.Vector3(), fpt = new THREE.Vector3();

/** reports once the R3F render loop has actually drawn this canvas at least once */
const useFirstDraw = (onDrawn: () => void) => {
  const gl = useThree((s) => s.gl);
  const done = React.useRef(false);
  useEffect(() => {
    done.current = false;
    let raf = 0, stop = false;
    const check = () => {
      if (stop || done.current) return;
      if (gl.info.render.calls > 0) { done.current = true; onDrawn(); return; }
      raf = requestAnimationFrame(check);
    };
    raf = requestAnimationFrame(check);
    return () => { stop = true; cancelAnimationFrame(raf); };
  }, [gl, onDrawn]);
};

const Inner: React.FC<{ id: number; onDrawn: () => void }> = ({ id, onDrawn }) => {
  const f = useCurrentFrame();
  const { camera, scene, gl } = useThree();
  const advance = useThree((s) => s.advance);
  useFirstDraw(onDrawn);
  // with frameloop="never" the manual advance() tick can fire before the composer state commits: retry each rAF
  useEffect(() => {
    let raf = 0, tries = 0;
    const tick = () => {
      advance(performance.now());
      if (gl.info.render.calls > 0 || ++tries > 300) return;
      raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => cancelAnimationFrame(raf);
  }, [advance, gl, f]);
  const world = useMemo(() => new World(), []);
  const target = useMemo(() => new THREE.Vector3(), []);
  const on = useMemo(toggles, []);
  const fx = useMemo(() => ({
    ink: new InkPass(scene, camera as THREE.PerspectiveCamera),
    lens: new LensBlur({ maxCoC: 24, nearScale: 1.2 }),
    bloom: makeBloom(),
    tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
    grade: new GradeEffect(GRADES.day, GRADE_STRENGTH.day),
    grain: new GrainEffect({ amount: 0.025, cellPx: 1.5 }),
  }), [camera, scene]);
  useEffect(() => () => fx.ink.dispose(), [fx]);
  const post = useMemo(() => on.composer ? (
    <EffectComposer multisampling={4}>
      {on.ink ? <primitive object={fx.ink} dispose={null} /> : null}
      {on.lens && on.pre ? <primitive object={fx.lens.pre} dispose={null} /> : null}
      {on.lens ? <primitive object={fx.lens.main} dispose={null} /> : null}
      {on.bloom ? <primitive object={fx.bloom} dispose={null} /> : null}
      <primitive object={fx.tone} dispose={null} />
      {on.grade ? <primitive object={fx.grade} dispose={null} /> : null}
      {on.grain ? <primitive object={fx.grain} dispose={null} /> : null}
    </EffectComposer>
  ) : null, [fx, on]);
  const cam = camera as THREE.PerspectiveCamera;
  target.copy(world.update(id, f, cam, scene));
  noInkFallback(world.root);
  // thin-lens focus: distance along the view axis to the shot's focus point
  const d = dofAt(f);
  cam.getWorldDirection(fwd);
  if (d.focus) fpt.set(...d.focus(f)); else fpt.copy(target);
  fx.lens.focus = Math.max(0.3, fpt.sub(cam.position).dot(fwd));
  fx.lens.cInf = d.cInf;
  const light = SHOTS[id - 1].light;
  gradeFor(fx.grade, light);
  gl.toneMappingExposure = LIGHTS[light].exposure;
  fx.grain.seed = f;
  return (
    <>
      <primitive object={world.root} dispose={null} />
      {post}
    </>
  );
};

/** test stills only: inputProps `{ post: { dpr: 0.5 } }` forces the WebGL buffer size */
const dprOverride = () => (getInputProps() as { post?: { dpr?: number } }).post?.dpr;
const ShotView: React.FC<{ id: number; alpha: number; onDrawn: () => void }> = ({ id, alpha, onDrawn }) => (
  <AbsoluteFill style={{ opacity: alpha }}>
    <ThreeCanvas width={1080} height={1920} {...(dprOverride() ? { dpr: dprOverride() } : {})} shadows="percentage" gl={{ antialias: false, stencil: false, powerPreference: "high-performance", toneMappingExposure: 1.0 }}
      camera={{ fov: 40, near: 0.2, far: 1500 }}>
      <Inner id={id} onDrawn={onDrawn} />
    </ThreeCanvas>
  </AbsoluteFill>
);

// ---------------- HUD age badge ----------------
const HUD_CAM = new THREE.PerspectiveCamera(40, 1080 / 1920, 0.05, 1200);
const V = new THREE.Vector3();
/** badge frames that animate the pill's pop (shot entries + the shot-10 age ticks) */
const PULSES = [0, ...SHOTS.map((s) => s.a), 1372, 1398, 1424, 1450];
const fmtAge = (a: number) => (a >= 1000 ? "1,000" : String(a));

const Hud: React.FC<{ id: number; f: number }> = ({ id, f }) => {
  const anchor = badgeAt(id, f);
  if (!anchor) return null;
  const c = camAt(id, f);
  HUD_CAM.position.set(...c.pos);
  HUD_CAM.up.set(0, 1, 0);
  HUD_CAM.lookAt(c.look[0], c.look[1], c.look[2]);
  HUD_CAM.rotateZ(c.roll);
  HUD_CAM.fov = c.fov;
  HUD_CAM.updateProjectionMatrix();
  HUD_CAM.updateMatrixWorld();
  V.set(anchor[0], anchor[1], anchor[2]).applyMatrix4(HUD_CAM.matrixWorldInverse);
  if (V.z > -0.4) return null;
  V.set(anchor[0], anchor[1], anchor[2]).project(HUD_CAM);
  if (V.x < -1.05 || V.x > 1.05 || V.y < -1.05 || V.y > 1.05) return null;
  const x = Math.max(21, Math.min(79, (V.x * 0.5 + 0.5) * 100));
  const y = Math.max(9, Math.min(88, (-V.y * 0.5 + 0.5) * 100));
  const age = badgeAge(id, f);
  let pulse = 1;
  for (const t0 of PULSES) { const d = f - t0; if (d >= 0 && d < 10) pulse = Math.max(pulse, 1 + 0.1 * (1 - d / 10)); }
  return (
    <div style={{ position: "absolute", left: `${x}%`, top: `${y}%`, transform: `translate(-50%, -112%) scale(${pulse.toFixed(3)})`, transformOrigin: "50% 100%", pointerEvents: "none" }}>
      <div style={{
        display: "flex", alignItems: "center", gap: 14, padding: "12px 22px", borderRadius: 999,
        background: "linear-gradient(180deg, rgba(9,24,34,0.86) 0%, rgba(4,11,17,0.76) 100%)",
        border: "2px solid rgba(34,196,240,0.9)",
        boxShadow: "0 0 22px rgba(34,196,240,0.55), 0 6px 18px rgba(0,0,0,0.5), inset 0 0 16px rgba(34,196,240,0.16)",
        whiteSpace: "nowrap",
      }}>
        <span style={{ fontFamily: '"Cascadia Mono", "Consolas", monospace', fontSize: 30, fontWeight: 700, letterSpacing: 1, color: "#dff4ff", fontVariantNumeric: "tabular-nums" }}>
          AGE {fmtAge(age)}
        </span>
        <span style={{ fontSize: 26, color: "#5fd0ea", opacity: 0.9 }}>·</span>
        <span style={{
          fontFamily: '"Cascadia Mono", "Consolas", monospace', fontSize: 27, fontWeight: 700, letterSpacing: 1,
          color: "#8ff3ff", padding: "5px 12px", borderRadius: 10, fontVariantNumeric: "tabular-nums",
          border: "2px solid rgba(127,240,255,0.85)", boxShadow: "0 0 14px rgba(127,240,255,0.55), inset 0 0 10px rgba(127,240,255,0.18)",
        }}>
          LOOKS [18]
        </span>
      </div>
    </div>
  );
};

export const Age18Short: React.FC = () => {
  const f = useCurrentFrame();
  const [handle] = useState(() => delayRender("age18 first draw"));
  const layers = useMemo(() => layersAt(f), [f]);
  const [drawn, setDrawn] = useState(0);
  useEffect(() => { setDrawn(0); }, [f]);
  useEffect(() => { if (drawn >= layers.length) continueRender(handle); }, [drawn, layers.length, handle]);
  // the badge follows the incoming shot once its crossfade is past halfway
  const top = layers.length > 1 && layers[1].alpha < 0.5 ? layers[0] : layers[layers.length - 1];
  const flash = f >= FLASH_AT && f < FLASH_AT + 4 ? [0.85, 0.55, 0.3, 0.12][f - FLASH_AT] : 0;
  return (
    <AbsoluteFill style={{ background: "#070a10" }}>
      <Audio src={staticFile("age18/audio.mp3")} />
      {layers.map((l, i) => <ShotView key={i ? "over" : "base"} id={l.id} alpha={l.alpha} onDrawn={() => setDrawn((d) => d + 1)} />)}
      <Hud id={top.id} f={f} />
      {flash > 0 && <AbsoluteFill style={{ background: "#e9fdff", opacity: flash }} />}
    </AbsoluteFill>
  );
};
