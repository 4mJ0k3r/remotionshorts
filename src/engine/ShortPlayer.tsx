import React, {useEffect, useMemo, useRef} from "react";
import * as THREE from "three";
import {AbsoluteFill, Audio, continueRender, delayRender, staticFile, useCurrentFrame, useVideoConfig} from "remotion";
import {ThreeCanvas} from "@remotion/three";
import {useThree} from "@react-three/fiber";
import {EffectComposer} from "@react-three/postprocessing";
import {BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode} from "postprocessing";
import {InkPass, noInkFallback} from "./shaders/ink";
import {LensBlur} from "./shaders/lensblur";
import {GradeEffect, GRADES, gradeFor} from "./shaders/grade";
import type {Cam} from "./camera";

export type SubtitleCue = readonly [a: number, b: number, text: string]; // inclusive endpoints
export type PlayerShot = {id: number; a: number; b: number; hud?: string; grade?: string; exposure?: number};
export type PlayerWorld = {
  root: THREE.Object3D;
  update: (id: number, f: number, camera: THREE.PerspectiveCamera, scene: THREE.Scene) => unknown;
  dispose?: () => void;
};
export type ShortPlayerProps = {
  createWorld: () => PlayerWorld;
  shots: readonly PlayerShot[];
  cues?: readonly SubtitleCue[];
  /** Public asset path (resolved through staticFile), or a complete URL. */
  audio?: string;
  subs?: boolean;
  hud?: string | ((f: number, shot: PlayerShot) => string);
  camAt?: (f: number) => Cam;
  dofAt: (f: number) => {focus: number; cInf: number};
  background?: string;
  subtitleSize?: number;
  dpr?: number;
};
export const HudPill: React.FC<{text: string}> = ({text}) => text ? (
  <div style={{position: "absolute", top: "10%", left: "5%", right: "5%", textAlign: "center", pointerEvents: "none"}}>
    <span style={{display: "inline-block", maxWidth: "100%", boxSizing: "border-box", padding: "18px 30px", background: "rgba(22,18,34,0.86)", border: "2px solid rgba(255,255,255,0.2)", borderRadius: 999, color: "white", fontFamily: '"Noto Sans Devanagari", "Nirmala UI", "Mangal", "Arial Black", sans-serif', fontSize: 38, fontWeight: 900}}>{text}</span>
  </div>
) : null;
export const SUBTITLE_FONT = '"Noto Sans Devanagari", "Nirmala UI", "Mangal", "Arial Black", sans-serif';
/** Browser text nodes preserve HarfBuzz shaping of Devanagari conjuncts and matras. */
export const Subtitles: React.FC<{f: number; cues: readonly SubtitleCue[]; fontSize?: number}> = ({f, cues, fontSize = 56}) => {
  const cue = cues.find(([a,b]) => f >= a && f <= b);
  const ref = useRef<HTMLSpanElement>(null);
  useEffect(() => {
    const handle = delayRender("subtitle font metrics");
    let active = true;
    const fit = async () => {
      await document.fonts.load(`900 ${fontSize}px ${SUBTITLE_FONT}`, cue?.[2] ?? "अ");
      await document.fonts.ready;
      if (!active) return;
      const el = ref.current;
      if (el?.parentElement) {
        el.style.fontSize = `${fontSize}px`;
        const available = el.parentElement.clientWidth;
        const needed = el.scrollWidth;
        if (needed > available) el.style.fontSize = `${fontSize * available / needed}px`;
      }
      continueRender(handle);
    };
    void fit().catch(() => { if (active) continueRender(handle); });
    return () => {active = false; continueRender(handle);};
  }, [cue, fontSize]);
  if (!cue) return null;
  const u = Math.min(1, (f - cue[0] + 1) / 4), k = u*u*(3-2*u), c = Math.round(216 + 39*k);
  return <div style={{position: "absolute", left: "6%", right: "6%", bottom: "18%", textAlign: "center", transform: `scale(${0.97+0.03*k})`, transformOrigin: "50% 100%", pointerEvents: "none"}}>
    <span ref={ref} style={{display: "inline-block", whiteSpace: "nowrap", fontFamily: SUBTITLE_FONT, fontWeight: 900, fontSize, lineHeight: 1.4, color: `rgb(${c},${c},${c})`, WebkitTextStroke: "10px #1a1214", paintOrder: "stroke fill", textShadow: "0 6px 0 #1a1214, 0 10px 22px rgba(0,0,0,0.45)"}}>{cue[2]}</span>
  </div>;
};
const makeBloom = () => {
  const b = new BloomEffect({blendFunction: BlendFunction.ADD, intensity: 0.4, luminanceThreshold: 1, luminanceSmoothing: 0.2, mipmapBlur: true, levels: 6, radius: 0.6});
  const resize = b.mipmapBlurPass.setSize.bind(b.mipmapBlurPass);
  b.mipmapBlurPass.setSize = (w,h) => resize(Math.round(1920*w/Math.max(h,1)),1920);
  return b;
};
const Scene: React.FC<ShortPlayerProps & {shot: PlayerShot}> = (props) => {
  const f = useCurrentFrame();
  const {camera,scene,gl,advance} = useThree();
  const cam = camera as THREE.PerspectiveCamera;
  const world = useMemo(props.createWorld, [props.createWorld]);
  const fx = useMemo(() => ({ink: new InkPass(scene,cam,{color: "#351f22"}), lens: new LensBlur({maxCoC: 14, nearScale: 1, minBackgroundCoC: 6, backgroundMaxCoC: 10}), bloom: makeBloom(), tone: new ToneMappingEffect({mode: ToneMappingMode.NEUTRAL}), grade: new GradeEffect(GRADES.vivid,1)}), [scene,cam]);
  useEffect(() => () => {world.dispose?.();}, [world]);
  useEffect(() => () => {fx.ink.dispose(); fx.lens.dispose(); fx.bloom.dispose(); fx.tone.dispose(); fx.grade.dispose();}, [fx]);
  if (props.camAt) {
    const c = props.camAt(f);
    cam.position.set(...c.pos); cam.fov = Math.max(38,Math.min(50,c.fov));
    cam.up.set(0,1,0); cam.lookAt(...c.look); cam.rotateZ(c.roll); cam.updateProjectionMatrix(); cam.updateMatrixWorld();
  }
  world.update(props.shot.id,f,cam,scene);
  cam.fov = Math.max(38, Math.min(50,cam.fov)); cam.updateProjectionMatrix();
  noInkFallback(world.root);
  const dof = props.dofAt(f);
  fx.lens.focus = dof.focus; fx.lens.cInf = dof.cInf;
  // Reuse InkPass world-only depth: card cutouts bypass both blur passes,
  // while background taps never borrow their colour or spread across their ink.
  fx.lens.sharpDepth = fx.ink.worldDepthTexture;
  gradeFor(fx.grade,props.shot.grade ?? "vivid");
  gl.toneMappingExposure = props.shot.exposure ?? 1;
  useEffect(() => {
    const handle = delayRender(`studio frame ${f}`);
    let raf = 0, done = false;
    const tick = () => {
      gl.info.reset(); advance(performance.now());
      if (gl.info.render.calls > 0) {done = true; continueRender(handle);}
      else raf = requestAnimationFrame(tick);
    };
    raf = requestAnimationFrame(tick);
    return () => {cancelAnimationFrame(raf); if (!done) continueRender(handle);};
  }, [f,advance,gl]);
  return <>
    <primitive object={world.root} dispose={null}/>
    <EffectComposer multisampling={4}>
      <primitive object={fx.ink} dispose={null}/>
      <primitive object={fx.lens.pre} dispose={null}/>
      <primitive object={fx.lens.main} dispose={null}/>
      <primitive object={fx.bloom} dispose={null}/>
      <primitive object={fx.tone} dispose={null}/>
      <primitive object={fx.grade} dispose={null}/>
    </EffectComposer>
  </>;
};
export const ShortPlayer: React.FC<ShortPlayerProps> = (props) => {
  const f = useCurrentFrame(), {width,height} = useVideoConfig();
  const shot = props.shots.find(s => f >= s.a && f < s.b);
  if (!shot) throw new Error(`No studio shot covers frame ${f}`);
  const hud = typeof props.hud === "function" ? props.hud(f,shot) : props.hud ?? shot.hud ?? "";
  return <AbsoluteFill style={{background: props.background ?? "#9fd0f5"}}>
    <ThreeCanvas width={width} height={height} dpr={props.dpr} shadows="percentage" camera={{fov: 45,near: 0.2,far: 1500}} gl={{antialias: false,stencil: false,localClippingEnabled: true,powerPreference: "high-performance"}}>
      <Scene {...props} shot={shot}/>
    </ThreeCanvas>
    {props.audio && <Audio src={/^(https?:|data:|blob:)/.test(props.audio) ? props.audio : staticFile(props.audio)}/>}
    <HudPill text={hud}/>
    {props.subs !== false && <Subtitles f={f} cues={props.cues ?? []} fontSize={props.subtitleSize}/>}
  </AbsoluteFill>;
};
