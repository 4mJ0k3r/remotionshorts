// "School Hero" — 122.0 s (3660 f @ 30 fps), ten beats through one lockdown day. Same calibrated post chain as the
// earlier shorts: InkPass (world ink) -> lens blur pre + main (thin-lens DOF) -> [bloom (emissive only) +
// NEUTRAL tone mapping + colour grade] (one merged EffectPass), MSAA 4. Ink before the DOF, bloom after, grade
// display-referred. The ten beats are hard cuts on one canvas; HUD cards (blind spot, hero meter) are HTML overlays
// so their text stays crisp, and the chalk hit adds a 4-frame white flash.
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
import {
  TOTAL, SHOTS, GRADE_OF, layersAt, dofAt,
  STAIRS_AT, VENT_AT, THWACK_AT,
} from "./story";

export const SCHOOL_FRAMES = TOTAL;

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
  gradeFor(fx.grade, GRADE_OF[light]);
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

// ---------------- HUD ----------------
const MONO = '"Cascadia Mono", "Consolas", monospace';
const fade = (f: number, a: number, b: number, k = 8) => Math.min(1, Math.max(0, (f - a) / k), Math.max(0, (b - f) / k));

const HeroMeter: React.FC<{ f: number }> = ({ f }) => {
  const a = fade(f, STAIRS_AT, VENT_AT + 4, 10);
  if (a <= 0) return null;
  const k = Math.min(1.18, Math.max(0, (f - STAIRS_AT) / 100) * 1.18);
  return (
    <div style={{ position: "absolute", right: 54, bottom: 210, width: 470, opacity: a, pointerEvents: "none" }}>
      <div style={{ padding: "16px 20px 18px", border: "2px solid rgba(255,214,74,0.85)", background: "linear-gradient(180deg, rgba(20,14,4,0.8), rgba(8,6,2,0.62))", boxShadow: "0 0 26px rgba(255,196,60,0.35), inset 0 0 20px rgba(255,196,60,0.12)" }}>
        <div style={{ display: "flex", justifyContent: "space-between", alignItems: "baseline", marginBottom: 10 }}>
          <span style={{ fontFamily: MONO, fontSize: 26, fontWeight: 800, letterSpacing: 3, color: "#ffe9b0" }}>HERO METER</span>
          <span style={{ fontFamily: MONO, fontSize: 30, fontWeight: 900, color: k > 1 ? "#ff9a4a" : "#ffe066", textShadow: "0 0 14px rgba(255,190,70,0.8)" }}>{k > 1 ? ">100%" : `${Math.round(k * 100)}%`}</span>
        </div>
        <div style={{ height: 34, background: "#0d1420", border: "2px solid rgba(255,214,74,0.5)", position: "relative", overflow: "hidden" }}>
          <div style={{ width: `${Math.min(1, k / 1.18) * 100}%`, height: "100%", background: "linear-gradient(90deg, #ffcf3a, #ff8a3a)", boxShadow: "0 0 18px rgba(255,170,40,0.9)" }} />
          {[0.25, 0.5, 0.75, 1].map((x) => <div key={x} style={{ position: "absolute", left: `${x * 100}%`, top: 0, bottom: 0, width: 2, background: "rgba(6,12,18,0.55)" }} />)}
        </div>
        {k > 1 && <div style={{ fontFamily: MONO, fontSize: 24, fontWeight: 900, letterSpacing: 4, color: "#ff9a4a", textAlign: "right", marginTop: 8, textShadow: "0 0 14px rgba(255,140,60,0.9)" }}>MAX!</div>}
      </div>
    </div>
  );
};

export const SchoolHeroShort: React.FC = () => {
  const f = useCurrentFrame();
  const [handle] = useState(() => delayRender("school first draw"));
  const layers = useMemo(() => layersAt(f), [f]);
  const [drawn, setDrawn] = useState(0);
  useEffect(() => { setDrawn(0); }, [f]);
  useEffect(() => { if (drawn >= layers.length) continueRender(handle); }, [drawn, layers.length, handle]);
  const flash = f >= THWACK_AT && f < THWACK_AT + 4 ? [0.9, 0.6, 0.34, 0.14][f - THWACK_AT] : 0;
  return (
    <AbsoluteFill style={{ background: "#070a10" }}>
      <Audio src={staticFile("school/audio.mp3")} />
      {layers.map((l, i) => <ShotView key={i ? `over${i}` : "base"} id={l.id} alpha={l.alpha} onDrawn={() => setDrawn((d) => d + 1)} />)}
      <HeroMeter f={f} />
      {flash > 0 && <AbsoluteFill style={{ background: "#f4feff", opacity: flash }} />}
    </AbsoluteFill>
  );
};
