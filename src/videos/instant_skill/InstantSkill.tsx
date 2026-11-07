// "InstantSkill" — the full 123.8 s short (3714 f @ 30 fps), 25 shots over 8 isolated 3D sets: Act 1 f0..1193
// (shots 1-8, the cheat-code highs), Act 2 f1194..2907 (shots 9-19, the price of the power) and Act 3 f2908..3713
// (shots 20-25, the avalanche rescue, the alien code and the question).
// Post chain, in this exact order: InkPass (#351f22) -> LensBlur.pre -> LensBlur.main -> Bloom -> ToneMapping
// (Neutral) -> Grade. Two HTML overlays share one `subs` switch: a stat pill in the top 14% band and a single crisp
// subtitle line at bottom 18% with a 4-frame #d8d8d8 -> #ffffff ease. `{ subs: false }` hides both for the
// calibration stills, so text never covers a hand, a prop or a feet line.
import React, { useEffect, useMemo, useState } from "react";
import * as THREE from "three";
import {
  AbsoluteFill, Audio, continueRender, delayRender, getInputProps, staticFile, useCurrentFrame,
} from "remotion";
import { ThreeCanvas } from "@remotion/three";
import { useThree } from "@react-three/fiber";
import { EffectComposer } from "@react-three/postprocessing";
import { BlendFunction, BloomEffect, ToneMappingEffect, ToneMappingMode } from "postprocessing";
import { World } from "./world";
import { InkPass, noInkFallback } from "./ink";
import { LensBlur } from "./lensblur";
import { GradeEffect, GRADES, gradeFor } from "./grade";
import { LIGHTS } from "./lights";
import { GRADE_OF, SHOTS, TOTAL, dofAt, hudAt, layersAt } from "./story";

export const INSTANT_SKILL_FRAMES = TOTAL;

const makeBloom = () => {
  const b = new BloomEffect({
    blendFunction: BlendFunction.ADD,
    intensity: 0.32,
    luminanceThreshold: 1.0,
    luminanceSmoothing: 0.2,
    mipmapBlur: true,
    levels: 6,
    radius: 0.6,
  });
  const mip = b.mipmapBlurPass;
  const setSize = mip.setSize.bind(mip);
  // the bloom pyramid is sized off the render target, which is 540x960 on a 0.5 pass — pin it to full height
  mip.setSize = (w: number, h: number) => setSize(Math.round((1920 * w) / Math.max(h, 1)), 1920);
  return b;
};

const fwd = new THREE.Vector3();
const fpt = new THREE.Vector3();

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

const Inner: React.FC<{ id: number; f: number; onDrawn: () => void }> = ({ id, f, onDrawn }) => {
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
  const fx = useMemo(() => ({
    ink: new InkPass(scene, camera as THREE.PerspectiveCamera, { color: "#351f22" }),
    lens: new LensBlur({ maxCoC: 20, nearScale: 1.2 }),
    bloom: makeBloom(),
    tone: new ToneMappingEffect({ mode: ToneMappingMode.NEUTRAL }),
    grade: new GradeEffect(GRADES.golden, 1),
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
  world.update(id, f, cam, scene);
  noInkFallback(world.root);

  // ---- DOF: focus is the distance from the lens to the live subject along the view axis, never a fixed number ----
  const d = dofAt(f);
  cam.getWorldDirection(fwd);
  const fp = d.focus(f);
  fpt.set(fp[0], fp[1], fp[2]);
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

const ShotView: React.FC<{ id: number; alpha: number; f: number; onDrawn: () => void }> = ({ id, alpha, f, onDrawn }) => (
  <AbsoluteFill style={{ opacity: alpha }}>
    <ThreeCanvas
      width={1080}
      height={1920}
      {...(dprOverride() ? { dpr: dprOverride() } : {})}
      shadows="percentage"
      gl={{ antialias: false, stencil: false, powerPreference: "high-performance", toneMappingExposure: 1.0 }}
      camera={{ fov: 46, near: 0.1, far: 1200 }}
    >
      <Inner id={id} f={f} onDrawn={onDrawn} />
    </ThreeCanvas>
  </AbsoluteFill>
);

// ---------------- SUBTITLES ----------------
// Forty-seven single Hindi lines over all 25 shots — twelve for Act 1, twenty-five for Acts 2 and 3. The frame
// windows are the script's, re-timed onto the measured narration pauses (silencedetect at -40 dB / 0.12 s on
// out/instant_skill/_narration16k.wav): every boundary sits inside a real breath and, as far as the audio allows,
// inside one SHOTS window. The table deliberately leaves the screen blank wherever the VO is silent — Act 1's
// 851..858 and 968..974, then 1825..1837, the 2487..2513 beat between the loop and the friends leaving, the
// avalanche's wind at 2906..2914, the car rolling in at 3333..3337, the 3450..3583 gap the narration leaves before
// the question, and the dead air after it (3707..3713) — so a line never dies mid-word.
export const CUES: [number, number, string][] = [
  [0, 92, "सोचो अगर तुम दुनिया की कोई भी स्किल"],
  [93, 175, "बस 1 बार देखकर तुरंत सीख जाओ!"],
  [176, 267, "सुनने में अल्टीमेट चीट-कोड लगता है,"],
  [268, 365, "पर असली बायोलॉजी के हिसाब से"],
  [366, 455, "तुम्हारा शरीर ही दुश्मन बन जाएगा!"],
  [456, 545, "शुरुआत में तो फुल स्वैग रहेगा—"],
  [546, 635, "15 सेकंड में रूबिक्स क्यूब सॉल्व!"],
  [636, 754, "और बिना देखे ग्रैंडमास्टर चारों खाने चित!"],
  [755, 850, "भाई, कल तक तो प्यादे चलाना भी नहीं आता था!"],
  [859, 967, "ब्रो, तेरा भाई अब चलता-फिरता ChatGPT है!"],
  [975, 1085, "फ्लाइट में 1 डिक्शनरी पढ़कर 40 भाषाएं,"],
  [1086, 1193, "और गेमिंग से पोकर तक हर जगह नोट छापोगे!"],
  // ---- ACT 2 ----
  [1194, 1290, "पर यहीं फिजिक्स और बायोलॉजी ने"],
  [1291, 1296, "तुम्हारी वाट लगा दी!"],
  [1297, 1377, "क्योंकि दिमाग तो 1 सेकंड में अपग्रेड"],
  [1378, 1381, "हो गया, पर मसल्स और हड्डियां"],
  [1382, 1492, "अभी भी नॉर्मल इंसान वाली हैं!"],
  [1502, 1541, "ओलंपिक वीडियो देखकर स्नोबोट पर"],
  [1542, 1587, "डबल बैकफ्लिप, या रेस कार में"],
  [1588, 1660, "300 की स्पीड तो पकड़ लोगे!"],
  [1666, 1729, "पर लैंडिंग के झटके और जी-फोर्स से"],
  [1730, 1790, "गर्दन और कलाई की हड्डियां"],
  [1796, 1824, "खड़क से टूट जाएंगी!"],
  [1838, 1915, "दिमाग तो प्रो लेवल है भाई,"],
  [1916, 1978, "पर इस सस्ती बॉडी का क्या करूं?"],
  [1991, 2052, "असल में जब तुम 1 सेकंड में"],
  [2053, 2066, "हज़ारों गानों का डेटा"],
  [2067, 2164, "दिमाग में ठूंसोगे तो न्यूरॉन्स"],
  [2165, 2253, "ओवरहीट होने लगेंगे!"],
  [2260, 2321, "सबसे बुरी साइड ये कि कुछ भी"],
  [2326, 2370, "भूल नहीं पाओगे— हर इनसल्ट,"],
  [2378, 2435, "हर ब्रेकडाउन, हर डरावना सीन"],
  [2436, 2486, "24 घंटे HD लूप पर चलेगा!"],
  [2514, 2602, "दोस्त तुमसे जलकर दूर हो जाएंगे,"],
  [2610, 2697, "वो गिटार जो साल से बजा रहे थे"],
  [2698, 2747, "उसे 3 मिनट में मास्टर कर लिया,"],
  [2752, 2786, "यानी जीत का मज़ा खत्म!"],
  // ---- ACT 3 ----
  [2915, 2991, "फिर पहाड़ों पर भयंकर avalanche आता है"],
  [2998, 3076, "और बेस्ट फ्रेंड बर्फ के नीचे दब जाता है!"],
  [3088, 3186, "तुम इंस्टेंट नॉलेज से बर्फ का एंगल कैलकुलेट"],
  [3192, 3249, "करके 3 मिनट में उसकी जान बचा लेते हो!"],
  [3257, 3332, "और ठीक अगले हफ्ते घर के बाहर एक गाड़ी"],
  [3338, 3372, "रुकती है, एजेंट्स कोड देते हैं"],
  [3381, 3449, "जिसे धरती पर सिर्फ तुम्हारा दिमाग"],
  [3584, 3635, "तो क्या तुम ये सुपर पावर लोगे?"],
  [3636, 3675, "कमेंट्स में बताओ..."],
  [3689, 3706, "और ज़रा..."],
];

const EASE = 4;
const USABLE = 1080 - 2 * 56;

const Subtitles: React.FC<{ f: number }> = ({ f }) => {
  const cue = CUES.find(([a, b]) => f >= a && f <= b);
  if (!cue) return null;
  const [a, , text] = cue;
  const u = Math.min(1, (f - a + 1) / EASE);
  const k = u * u * (3 - 2 * u);
  const c = Math.round(0xd8 + (0xff - 0xd8) * k);
  // one line, never wrapped: shrink the type instead of letting a long cue break onto two lines
  const size = Math.min(84, Math.floor(USABLE / Math.max(1, text.length * 0.62)));

  return (
    <div
      style={{
        position: "absolute",
        left: 56,
        right: 56,
        bottom: "18%",
        textAlign: "center",
        transform: `scale(${0.97 + 0.03 * k})`,
        transformOrigin: "50% 100%",
        pointerEvents: "none",
        whiteSpace: "nowrap",
      }}
    >
      <span
        style={{
          fontFamily: '"Nirmala UI", "Noto Sans Devanagari", "Segoe UI", Arial, sans-serif',
          fontWeight: 900,
          fontSize: size,
          lineHeight: 1.1,
          color: `rgb(${c},${c},${c})`,
          WebkitTextStroke: `${Math.round(size * 0.16)}px #1a1214`,
          paintOrder: "stroke fill",
          textShadow: `0 ${Math.round(size * 0.1)}px 0 #1a1214, 0 14px 26px rgba(0,0,0,0.45)`,
        }}
      >
        {text}
      </span>
    </div>
  );
};

// ---------------- HUD stat pills ----------------
// The stat readouts the v1 boards used to paint into the set. One pill at a time in the top band: its bottom edge
// lands at v ~18.5% of 1920, which is exactly the line scripts/is_frame.mjs keeps every head and prop below.
const HUD_POP = 6;
const HUD_TOP = "14%";

const HudPill: React.FC<{ f: number }> = ({ f }) => {
  const cue = hudAt(f);
  // the opening pill is already up at frame 0; every later one cross-fades so the swap is not a single-frame jump
  const u = cue.a === 0 ? 1 : Math.min(1, (f - cue.a + 1) / HUD_POP);
  const k = u * u * (3 - 2 * u);
  const col = cue.tone === "gold" ? "#ffd23f" : "#7fe7ff";

  return (
    <div
      style={{
        position: "absolute",
        left: 0,
        right: 0,
        top: HUD_TOP,
        display: "flex",
        justifyContent: "center",
        opacity: k,
        transform: `scale(${0.92 + 0.08 * k})`,
        transformOrigin: "50% 0%",
        pointerEvents: "none",
      }}
    >
      <span
        style={{
          fontFamily: '"Segoe UI", "Noto Sans", Arial, sans-serif',
          fontWeight: 800,
          fontSize: 42,
          lineHeight: 1.15,
          letterSpacing: 1.6,
          color: col,
          background: "rgba(22,18,34,0.86)",
          border: "2px solid rgba(255,255,255,0.2)",
          borderRadius: 999,
          padding: "14px 34px",
          whiteSpace: "nowrap",
          textShadow: `0 0 18px ${cue.tone === "gold" ? "rgba(255,210,63,0.45)" : "rgba(127,231,255,0.45)"}`,
          boxShadow: "0 12px 30px rgba(0,0,0,0.38)",
        }}
      >
        {cue.text}
      </span>
    </div>
  );
};

export const InstantSkillShort: React.FC<{ subs?: boolean }> = ({ subs = true }) => {
  const f = useCurrentFrame();
  // bridge-stills.mjs sends BRIDGE_PROPS as render inputProps, which reach the component through getInputProps()
  const showSubs = (getInputProps() as { subs?: boolean }).subs !== false && subs;
  const [handle] = useState(() => delayRender("instant_skill first draw"));
  const layers = useMemo(() => layersAt(f), [f]);
  const [drawn, setDrawn] = useState(0);

  useEffect(() => { setDrawn(0); }, [f]);
  useEffect(() => { if (drawn >= layers.length) continueRender(handle); }, [drawn, layers.length, handle]);

  return (
    <AbsoluteFill style={{ background: "#1a140f" }}>
      {layers.map((l, i) => (
        <ShotView key={i ? `over${i}` : "base"} id={l.id} alpha={l.alpha} f={f} onDrawn={() => setDrawn((d) => d + 1)} />
      ))}
      {showSubs ? <HudPill f={f} /> : null}
      {showSubs ? <Subtitles f={f} /> : null}
      {/* one 123.79 s narration track runs the whole 25-shot film: 0..39.53 s is Act 1, the rest carries Acts 2-3 */}
      <Audio src={staticFile("instant_skill/audio.mp3")} />
    </AbsoluteFill>
  );
};
