// "Tower Qwen" — the 1952 Tower Bridge bus jump. 10.0 s (300 f @ 30 fps), 1080x1920, three hard-cut shots on one canvas.
// Post chain (house order): InkPass (world ink #351f22) -> LensBlur.pre -> LensBlur.main (thin-lens DOF) -> Bloom
// (emissive only) -> ToneMapping NEUTRAL -> Grade. Subtitles are an HTML overlay so the text stays crisp: exactly ONE
// cue string is on screen at any frame, it switches cleanly on its cue frame, and the new line eases #d8d8d8 -> #ffffff
// over 4 frames. One font size, fitted (by canvas measurement) to the widest cue, keeps every line on a single row.
import React, { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { AbsoluteFill, continueRender, delayRender, getInputProps, useCurrentFrame } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";
import { World } from "./world";
import { InkPass, noInkFallback } from "./ink";
import { LensBlur } from "./lensblur";
import { GradeEffect, GRADES, gradeFor } from "./grade";
import { LIGHTS } from "./lights";
import { TOTAL, SHOTS, GRADE_OF, layersAt, dofAt } from "./story";

export const TOWER_QWEN_FRAMES = TOTAL;

const makeBloom = () => {
  const b = new BloomEffect({ blendFunction: BlendFunction.ADD, intensity: 0.4, luminanceThreshold: 1.0, luminanceSmoothing: 0.2, mipmapBlur: true, levels: 6, radius: 0.6 });
  const mip = b.mipmapBlurPass;
  const setSize = mip.setSize.bind(mip);
  mip.setSize = (w: number, h: number) => setSize(Math.round((1920 * w) / Math.max(h, 1)), 1920);
  return b;
};

const fwd = new THREE.Vector3(), fpt = new THREE.Vector3();

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
  const fx = useMemo(() => ({
    ink: new InkPass(scene, camera as THREE.PerspectiveCamera, { color: "#351f22" }),
    lens: new LensBlur({ maxCoC: 20, nearScale: 1.2 }),
    bloom: makeBloom(),
    tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
    grade: new GradeEffect(GRADES.day, 1),
  }), [camera, scene]);
  useEffect(() => () => fx.ink.dispose(), [fx]);
  const post = useMemo(() => (
    <EffectComposer multisampling={4}>
      <primitive object={fx.ink} dispose={null} />
      <primitive object={fx.lens.pre} dispose={null} />
      <primitive object={fx.lens.main} dispose={null} />
      <primitive object={fx.bloom} dispose={null} />
      <primitive object={fx.tone} dispose={null} />
      <primitive object={fx.grade} dispose={null} />
    </EffectComposer>
  ), [fx]);
  const cam = camera as THREE.PerspectiveCamera;
  target.copy(world.update(id, f, cam, scene));
  noInkFallback(world.root);
  const d = dofAt(f);
  cam.getWorldDirection(fwd);
  fpt.set(...d.focus(f));
  fx.lens.focus = Math.max(0.3, fpt.sub(cam.position).dot(fwd));
  fx.lens.cInf = d.cInf;
  const light = SHOTS[id - 1].light;
  gradeFor(fx.grade, GRADE_OF[light]);
  gl.toneMappingExposure = LIGHTS[light].exposure;
  return (
    <>
      <primitive object={world.root} dispose={null} />
      {post}
    </>
  );
};

const dprOverride = () => (getInputProps() as { post?: { dpr?: number } }).post?.dpr;
const ShotView: React.FC<{ id: number; alpha: number; onDrawn: () => void }> = ({ id, alpha, onDrawn }) => (
  <AbsoluteFill style={{ opacity: alpha }}>
    <ThreeCanvas width={1080} height={1920} {...(dprOverride() ? { dpr: dprOverride() } : {})} shadows="percentage" gl={{ antialias: false, stencil: false, powerPreference: "high-performance", toneMappingExposure: 1.0 }}
      camera={{ fov: 45, near: 0.2, far: 1500 }}>
      <Inner id={id} onDrawn={onDrawn} />
    </ThreeCanvas>
  </AbsoluteFill>
);

// ---------------- subtitles ----------------
// One — and only one — cue per frame; the ranges tile 0..299 with no overlap and no gap inside a shot.
export const CUES: [number, number, string][] = [
  [0, 30, "He was halfway across"], [31, 62, "the bridge when"], [63, 94, "the road split open."],
  [95, 128, "Instead of hitting the brakes,"], [129, 162, "the driver slammed"], [163, 194, "the gas."],
  [195, 228, "He jumped the double-decker"], [229, 262, "across the river"], [263, 299, "and got a £10 bonus."],
];
const EASE = 4;
const FONT = '"Arial Black", "Segoe UI Black", "Helvetica Neue", Arial, sans-serif';
const MAXW = 954;   // 1080 - 2 x 54 gutter - the 16px stroke's 2 x 8 px of outer ink
/** one size for the whole film, fitted to the widest cue so every line is guaranteed to stay on a single row */
const fitAll = () => {
  const g = document.createElement("canvas").getContext("2d");
  if (!g) return 64;
  g.font = `900 100px ${FONT}`;
  let em = 0;
  for (const [, , t] of CUES) em = Math.max(em, g.measureText(t).width / 100);
  return Math.max(40, Math.min(92, Math.floor(MAXW / em)));
};
const Subtitles: React.FC<{ f: number }> = ({ f }) => {
  const size = useMemo(fitAll, []);
  const cue = CUES.find(([a, b]) => f >= a && f <= b);
  if (!cue) return null;
  const [a, , text] = cue;
  const u = Math.min(1, (f - a + 1) / EASE), k = u * u * (3 - 2 * u);
  const c = Math.round(0xd8 + (0xff - 0xd8) * k);
  return (
    <div style={{ position: "absolute", left: 54, right: 54, bottom: "18%", textAlign: "center", transform: `scale(${0.97 + 0.03 * k})`, transformOrigin: "50% 100%" }}>
      <span style={{
        display: "inline-block", whiteSpace: "nowrap",
        fontFamily: FONT, fontWeight: 900, fontSize: size, lineHeight: 1.08,
        color: `rgb(${c},${c},${c})`, WebkitTextStroke: "16px #1a1214", paintOrder: "stroke fill",
        textShadow: "0 9px 0 #1a1214, 0 14px 26px rgba(0,0,0,0.45)",
      }}>{text}</span>
    </div>
  );
};

export const TowerQwenShort: React.FC = () => {
  const f = useCurrentFrame();
  const [handle] = useState(() => delayRender("tower_qwen first draw"));
  const layers = useMemo(() => layersAt(f), [f]);
  const [drawn, setDrawn] = useState(0);
  useEffect(() => { setDrawn(0); }, [f]);
  useEffect(() => { if (drawn >= layers.length) continueRender(handle); }, [drawn, layers.length, handle]);
  return (
    <AbsoluteFill style={{ background: "#9fd0f5" }}>
      {layers.map((l, i) => <ShotView key={i ? `over${i}` : "base"} id={l.id} alpha={l.alpha} onDrawn={() => setDrawn((d) => d + 1)} />)}
      {(getInputProps() as { subs?: boolean }).subs === false ? null : <Subtitles f={f} />}
    </AbsoluteFill>
  );
};
