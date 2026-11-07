// "ElevatorCrush" — 111.5 s (3345 f @ 30 fps), 11 shots, Hindi voiceover (public/elevator_crush/audio.mp3).
// Post chain: InkPass (#351f22) -> LensBlur.pre -> LensBlur.main -> Bloom -> ToneMapping (Neutral) -> Grade.
// Overlays: top HUD pill per shot (Rule 6) + bottom single-line subtitles (4-frame #d8d8d8 -> #ffffff ease).
import React, { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import { AbsoluteFill, Audio, continueRender, delayRender, getInputProps, staticFile, useCurrentFrame } from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";
import { World } from "./world";
import { InkPass, noInkFallback } from "./ink";
import { LensBlur } from "./lensblur";
import { GradeEffect, GRADES, gradeFor } from "./grade";
import { LIGHTS, LightName } from "./lights";
import { TOTAL, layersAt, dofAt, lightAt, shotAt } from "./story";

export const ELEVATOR_CRUSH_FRAMES = TOTAL;

const GRADE_OF: Record<LightName, string> = {
  amberCyan: "warm",
  rainy: "twilight",
  emergency: "warm",
  violetRim: "twilight",
  heartbeat: "warm",
  goldWarm: "warm",
  roseGold: "warm",
  neon: "twilight",
};

const makeBloom = () => {
  const b = new BloomEffect({
    blendFunction: BlendFunction.ADD,
    intensity: 0.35,
    luminanceThreshold: 1.0,
    luminanceSmoothing: 0.2,
    mipmapBlur: true,
    levels: 6,
    radius: 0.6,
  });
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
    lens: new LensBlur({ maxCoC: 16, nearScale: 1.2 }),
    bloom: makeBloom(),
    tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
    grade: new GradeEffect(GRADES.warm, 1),
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

  const light = lightAt(id, f);
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
    <ThreeCanvas
      width={1080}
      height={1920}
      {...(dprOverride() ? { dpr: dprOverride() } : {})}
      shadows="percentage"
      gl={{ antialias: false, stencil: false, powerPreference: "high-performance", toneMappingExposure: 1.0 }}
      camera={{ fov: 46, near: 0.1, far: 1200 }}
    >
      <Inner id={id} onDrawn={onDrawn} />
    </ThreeCanvas>
  </AbsoluteFill>
);

// ---------------- HUD PILL (top, per shot) ----------------
const HUD: Record<number, string> = {
  1: "😱 TRAPPED WITH CRUSH • 03:00:00",
  2: "🌧️ 1 SEC BEFORE CLOSING!",
  3: "⚡ POWER CUT • STUCK AT FLOOR 4!",
  4: "📵 HOUR 1 • ZERO NETWORK",
  5: "💀 ACTING NATURAL: 0%",
  6: "😭 STOMACH GROWLED IN SILENCE!",
  7: "⚠️ HOUR 2 • CABLE SLIPS 2 FEET!",
  8: "❤️ HEART RATE: 160 BPM!",
  9: "🔥 'जब तक मैं हूँ, तुम्हें कुछ नहीं होगा'",
  10: "✨ AWKWARDNESS: 0% • EYE CONTACT",
  11: "👇 COMMENT 'PART 2' NOW! 🔥",
};
const FONT = '"Nirmala UI", "Mangal", "Noto Sans Devanagari", "Arial Black", "Segoe UI Black", "Segoe UI Emoji", sans-serif';

const Hud: React.FC<{ f: number }> = ({ f }) => {
  const s = shotAt(f);
  const text = HUD[s.id];
  const pulse = s.id === 11 && f >= 3206 ? 1 + 0.06 * Math.sin((f - 3206) * 0.35) : 1;
  return (
    <div style={{ position: "absolute", top: "10%", left: 0, right: 0, display: "flex", justifyContent: "center", pointerEvents: "none" }}>
      <div
        style={{
          background: "rgba(22, 18, 34, 0.86)",
          border: "2px solid rgba(255,255,255,0.2)",
          borderRadius: 999,
          padding: "18px 40px",
          maxWidth: 980,
          whiteSpace: "nowrap",
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: text.length > 30 ? 40 : 46,
          color: "#ffffff",
          letterSpacing: 0.5,
          transform: `scale(${pulse})`,
          boxShadow: "0 8px 24px rgba(0,0,0,0.35)",
        }}
      >
        {text}
      </div>
    </div>
  );
};

// ---------------- SUBTITLES (authoritative cues; long cues split into sequential single lines) ----------------
const RAW_CUES: [number, number, string][] = [
  [0, 104, "सोचो अगर शाम की कोचिंग के बाद,"],
  [105, 209, "तुम और तुम्हारी क्रश 3 घंटों के लिए लिफ्ट में फँस जाओ!"],
  [210, 305, "बाहर तेज़ बारिश है, तुम लिफ्ट में अकेले हो..."],
  [306, 404, "और दरवाज़ा बंद होने से 1 सेकंड पहले वो अंदर आती है!"],
  [405, 485, "अभी तुम अपनी धड़कनें संभाल ही रहे होते हो"],
  [486, 570, "कि अचानक—भड़ाम! पूरी बिल्डिंग की लाइट कट जाती है,"],
  [571, 659, "और लिफ्ट चौथे फ्लोर के बीचों-बीच अटक जाती है!"],
  [660, 775, "पहला घंटा... भाई, एकदम जानलेवा ऑकवर्डनेस!"],
  [776, 905, "पिन-ड्रॉप साइलेंस है, और फ़ोन में नेटवर्क ज़ीरो।"],
  [906, 1030, "वो एक कोने में खड़ी अपने बाल ठीक कर रही है,"],
  [1031, 1169, "और तुम दूसरे कोने में फ्लोर बटन्स घूर रहे हो!"],
  [1170, 1310, "तुम कुछ बोलने के लिए मुँह खोलते हो, पर गला सूख जाता है।"],
  [1311, 1420, "ऊपर से खाली पेट में ज़ोर से गुड़गुड़ होती है—"],
  [1421, 1523, "लगता है धरती फट जाए और तुम समा जाओ!"],
  [1524, 1664, "तभी दूसरा घंटा... और केबल से आवाज़ आती है—खड़-खड़-खड़!"],
  [1665, 1817, "लिफ्ट 2 फीट नीचे खिसकती है और इमरजेंसी लाइट भी बंद!"],
  [1818, 1995, "डर से वो दौड़कर सीधा तुम्हारे सीने से लिपट जाती है!"],
  [1996, 2195, "तुम्हारे दिल की धड़कन सीधा उसके कानों में सुनाई देती है।"],
  [2196, 2330, "तुम काँपते हाथों से उसके कंधे को थामते हो—"],
  [2331, 2465, "'डरो मत, सेफ्टी ब्रेक्स लॉक हैं। तुम्हें कुछ नहीं होगा।'"],
  [2466, 2630, "5 सेकंड बाद डिम लाइट आती है, पर वो तुम्हें नहीं छोड़ती।"],
  [2631, 2834, "वो तुम्हारी आँखों में देखती है और ऑकवर्डनेस गायब!"],
  [2835, 3020, "पर असली खेल अब शुरू होता है—वो एक राज़ खोलने वाली है,"],
  [3021, 3205, "और तुम्हारी हथेली पर कुछ ऐसा लिखकर जाएगी कि होश उड़ जाएँगे!"],
  [3206, 3344, "आगे जानने के लिए अभी कमेंट करो 'PART 2' और फॉलो कर लो!"],
];

const MAX_CHARS = 30;
/** Split a long cue at the word boundary nearest its middle; time is shared in proportion to text length. */
const splitCue = ([a, b, t]: [number, number, string]): [number, number, string][] => {
  if (t.length <= MAX_CHARS) return [[a, b, t]];
  const words = t.split(" ");
  let best = 1, bestD = Infinity, acc = 0;
  for (let i = 1; i < words.length; i++) {
    acc += words[i - 1].length + 1;
    const d = Math.abs(acc - t.length / 2);
    if (d < bestD) { bestD = d; best = i; }
  }
  const p1 = words.slice(0, best).join(" "), p2 = words.slice(best).join(" ");
  const cut = a + Math.round(((b - a + 1) * p1.length) / (p1.length + p2.length));
  return [[a, cut - 1, p1], [cut, b, p2]];
};
export const CUES: [number, number, string][] = RAW_CUES.flatMap(splitCue);

const EASE = 4;
const Subtitles: React.FC<{ f: number }> = ({ f }) => {
  const cue = CUES.find(([a, b]) => f >= a && f <= b);
  if (!cue) return null;
  const [a, , text] = cue;
  const u = Math.min(1, (f - a + 1) / EASE);
  const k = u * u * (3 - 2 * u);
  const c = Math.round(0xd8 + (0xff - 0xd8) * k);
  const fs = Math.min(74, Math.floor(1900 / Math.max(10, text.length)));
  return (
    <div
      style={{
        position: "absolute", left: 30, right: 30, bottom: "18%", textAlign: "center",
        transform: `scale(${0.97 + 0.03 * k})`, transformOrigin: "50% 100%", pointerEvents: "none",
        whiteSpace: "nowrap",
      }}
    >
      <span
        style={{
          fontFamily: FONT,
          fontWeight: 900,
          fontSize: fs,
          lineHeight: 1.25,
          color: `rgb(${c},${c},${c})`,
          WebkitTextStroke: "14px #1a1214",
          paintOrder: "stroke fill",
          letterSpacing: 0.5,
          textShadow: "0 8px 0 #1a1214, 0 14px 26px rgba(0,0,0,0.45)",
        }}
      >
        {text}
      </span>
    </div>
  );
};

export const ElevatorCrushShort: React.FC<{ subs?: boolean }> = (p) => {
  const f = useCurrentFrame();
  const [handle] = useState(() => delayRender("elevator_crush first draw"));
  const layers = useMemo(() => layersAt(f), [f]);
  const [drawn, setDrawn] = useState(0);

  useEffect(() => { setDrawn(0); }, [f]);
  useEffect(() => { if (drawn >= layers.length) continueRender(handle); }, [drawn, layers.length, handle]);

  const props = { ...(getInputProps() as { subs?: boolean }), ...p };
  const showSubs = props.subs !== false;

  return (
    <AbsoluteFill style={{ background: "#2a2232" }}>
      <Audio src={staticFile("elevator_crush/audio.mp3")} />
      {layers.map((l, i) => (
        <ShotView key={i ? `over${i}` : "base"} id={l.id} alpha={l.alpha} onDrawn={() => setDrawn((d) => d + 1)} />
      ))}
      <Hud f={f} />
      {showSubs ? <Subtitles f={f} /> : null}
    </AbsoluteFill>
  );
};
