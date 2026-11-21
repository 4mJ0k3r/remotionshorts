import {build} from "esbuild";
import {mkdir, readFile, writeFile} from "node:fs/promises";
import path from "node:path";
import {fileURLToPath} from "node:url";

const scriptsDir = path.dirname(fileURLToPath(import.meta.url));
const projectDir = path.resolve(scriptsDir, "..");
const outputDir = path.join(projectDir, "out", "gandhiji_school");

// This browser entry exists only in memory; esbuild resolves its imports from scripts/.
const entry = String.raw`
import * as THREE from "three";
import {EffectComposer, RenderPass, EffectPass, BloomEffect, BlendFunction, ToneMappingEffect, ToneMappingMode} from "postprocessing";
import {GandhijiWorld} from "../src/videos/gandhiji_school/world.ts";
import {camAt, dofAt, shotAt, CAL_FRAMES, TOTAL, hudAt} from "../src/videos/gandhiji_school/story.ts";
import {InkPass, noInkFallback} from "../src/engine/shaders/ink.ts";
import {LensBlur} from "../src/engine/shaders/lensblur.ts";
import {GradeEffect, GRADES, gradeFor} from "../src/engine/shaders/grade.ts";

const WIDTH = 540, HEIGHT = 960, FPS = 30;
const FONT = '"Arial Black",Arial,sans-serif';
const $ = (id) => document.getElementById(id);
window.__gandhijiReady = false;
window.currentFrame = 0;

async function boot() {
  if (CAL_FRAMES.length !== 8) throw new Error("Calibration requires exactly eight frames.");
  await document.fonts.ready;
  const stage = $("stage"), viewport = $("viewport"), slider = $("frame");
  const playButton = $("play"), sheetButton = $("sheet"), sound = $("sound");
  const notice = $("notice"), readout = $("readout"), audio = $("narration");
  slider.max = String(TOTAL - 1);

  const renderer = new THREE.WebGLRenderer({
    antialias: false, stencil: false, alpha: false, preserveDrawingBuffer: true,
    localClippingEnabled: true, powerPreference: "high-performance",
  });
  renderer.setPixelRatio(1);
  renderer.setSize(WIDTH, HEIGHT, false);
  renderer.shadowMap.enabled = true;
  renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  renderer.localClippingEnabled = true;
  renderer.outputColorSpace = THREE.LinearSRGBColorSpace;
  renderer.toneMapping = THREE.NoToneMapping;
  renderer.setClearColor("#9fd0f5", 1);
  renderer.domElement.id = "world-canvas";
  renderer.domElement.setAttribute("aria-label", "Gandhiji school scene");
  viewport.prepend(renderer.domElement);

  const scene = new THREE.Scene();
  const camera = new THREE.PerspectiveCamera(45, WIDTH / HEIGHT, 0.2, 1500);
  const world = new GandhijiWorld();
  scene.add(world.root);
  const ink = new InkPass(scene, camera, {color: "#351f22"});
  // InkPass enables its NOINK camera layer; do not reset camera.layers on seeks.
  const lens = new LensBlur({maxCoC: 14, nearScale: 1, minBackgroundCoC: 6, backgroundMaxCoC: 10});
  const bloom = new BloomEffect({
    blendFunction: BlendFunction.ADD, intensity: 0.4, luminanceThreshold: 1,
    luminanceSmoothing: 0.2, mipmapBlur: true, levels: 6, radius: 0.6,
  });
  // ShortPlayer holds bloom's mipmap resolution at the composition's 1920px height.
  const resizeBloom = bloom.mipmapBlurPass.setSize.bind(bloom.mipmapBlurPass);
  bloom.mipmapBlurPass.setSize = (w, h) => resizeBloom(Math.round(1920 * w / Math.max(h, 1)), 1920);
  const tone = new ToneMappingEffect({mode: ToneMappingMode.NEUTRAL});
  const grade = new GradeEffect(GRADES.vivid, 1);
  const composer = new EffectComposer(renderer, {
    depthBuffer: true, stencilBuffer: false, multisampling: 4, frameBufferType: THREE.HalfFloatType,
  });
  composer.addPass(new RenderPass(scene, camera));
  composer.addPass(ink);
  composer.addPass(new EffectPass(camera, lens.pre));
  // Match react-three/postprocessing's automatic merge in ShortPlayer: the second
  // convolution stage plus consecutive non-convolution effects share an EffectPass.
  composer.addPass(new EffectPass(camera, lens.main, bloom, tone, grade));
  composer.setSize(WIDTH, HEIGHT);
  lens.sharpDepth = ink.worldDepthTexture;

  const hudMeasure = document.createElement("canvas").getContext("2d");
  if (!hudMeasure) throw new Error("Canvas2D is unavailable.");
  const hudTitle = $("hud-title"), hudSecondary = $("hud-secondary");
  let hudLayout = [], playing = false, raf = 0, exporting = false;
  let startSeconds = 0, startedAt = 0, audioClock = false;
  const duration = TOTAL / FPS;
  const normalizeFrame = (value) => {
    const n = Number(value);
    return Math.max(0, Math.min(TOTAL - 1, Number.isFinite(n) ? Math.round(n) : 0));
  };

  function wrapText(text, availableWidth, fontSize) {
    hudMeasure.font = '900 ' + fontSize + 'px ' + FONT;
    const lines = [];
    let line = "";
    for (const word of String(text).split(/\s+/)) {
      const next = line ? line + " " + word : word;
      if (line && hudMeasure.measureText(next).width > availableWidth) {
        lines.push(line);
        line = word;
      } else line = next;
    }
    if (line) lines.push(line);
    return lines;
  }

  function pill(text, secondary, hud) {
    if (!text) return null;
    // GandhijiSchool's 1080px HUD dimensions are halved for this 540px preview.
    const fontSize = secondary ? 14 : 17;
    const paddingX = secondary ? 11 : 15, paddingY = secondary ? 6 : 7;
    const border = secondary ? 2 : 1.5;
    const radius = secondary ? hud.stamp ? 3 : 9 : 13;
    const maxWidth = WIDTH * 0.84;
    const lines = wrapText(text, maxWidth - 2 * (paddingX + border), fontSize);
    hudMeasure.font = '900 ' + fontSize + 'px ' + FONT;
    const width = Math.min(maxWidth, Math.max(...lines.map((s) => hudMeasure.measureText(s).width)) + 2 * (paddingX + border));
    const lineHeight = fontSize * 1.25;
    return {
      lines, fontSize, lineHeight, paddingX, paddingY, border, radius, width,
      height: lines.length * lineHeight + 2 * (paddingY + border),
      x: (WIDTH - width) / 2,
      y: HEIGHT * (secondary ? hud.stamp ? 0.14 : hud.cta ? 0.13 : 0.12 : 0.06),
      scale: secondary ? hud.scale ?? 1 : 1,
      rotation: secondary && hud.stamp ? -2 : 0,
      background: secondary ? hud.stamp ? "#fff1df" : hud.cta ? "#8d202e" : "#28334e" : "#182135",
      color: secondary ? hud.stamp ? "#ae2737" : "#fff9df" : "#fffaf0",
      borderColor: secondary ? hud.stamp ? "#ae2737" : "#e7bd51" : "#d6b562",
      shadowY: 3, shadowColor: "rgba(22,18,25,.25)",
    };
  }

  function placePill(element, layout) {
    element.hidden = !layout;
    if (!layout) { element.textContent = ""; return; }
    element.textContent = layout.lines.join("\n");
    Object.assign(element.style, {
      left: layout.x + "px", top: layout.y + "px", width: layout.width + "px",
      height: layout.height + "px", padding: layout.paddingY + "px " + layout.paddingX + "px",
      fontFamily: FONT, fontWeight: "900", fontSize: layout.fontSize + "px",
      lineHeight: layout.lineHeight + "px", background: layout.background, color: layout.color,
      border: layout.border + "px solid " + layout.borderColor, borderRadius: layout.radius + "px",
      boxShadow: "0 " + layout.shadowY + "px 0 " + layout.shadowColor,
      // The centered pill shares its center with the composition's 84%-wide wrapper.
      transform: "scale(" + layout.scale + ") rotate(" + layout.rotation + "deg)", transformOrigin: "50% 50%",
    });
  }

  function updateHud(f) {
    const hud = hudAt(f);
    const title = pill(hud.title, false, hud), secondary = pill(hud.secondary, true, hud);
    placePill(hudTitle, title);
    placePill(hudSecondary, secondary);
    hudLayout = [title, secondary].filter(Boolean);
  }

  function drawHud(ctx) {
    for (const p of hudLayout) {
      ctx.save();
      ctx.translate(p.x + p.width / 2, p.y + p.height / 2);
      ctx.scale(p.scale, p.scale);
      ctx.rotate(p.rotation * Math.PI / 180);
      ctx.translate(-p.width / 2, -p.height / 2);
      ctx.beginPath();
      ctx.roundRect(0, p.shadowY, p.width, p.height, p.radius);
      ctx.fillStyle = p.shadowColor;
      ctx.fill();
      ctx.beginPath();
      ctx.roundRect(0, 0, p.width, p.height, p.radius);
      ctx.fillStyle = p.background;
      ctx.fill();
      const inset = p.border / 2;
      ctx.beginPath();
      ctx.roundRect(inset, inset, p.width - p.border, p.height - p.border, p.radius - inset);
      ctx.strokeStyle = p.borderColor;
      ctx.lineWidth = p.border;
      ctx.stroke();
      ctx.font = '900 ' + p.fontSize + 'px ' + FONT;
      ctx.fillStyle = p.color;
      ctx.textAlign = "center";
      ctx.textBaseline = "alphabetic";
      const metrics = ctx.measureText("Mg");
      const ascent = metrics.fontBoundingBoxAscent ?? p.fontSize * 0.9;
      const descent = metrics.fontBoundingBoxDescent ?? p.fontSize * 0.22;
      const baseline = p.border + p.paddingY + (p.lineHeight - ascent - descent) / 2 + ascent;
      p.lines.forEach((line, i) => ctx.fillText(line, p.width / 2, baseline + i * p.lineHeight));
      ctx.restore();
    }
  }

  function renderFrame(value) {
    const f = normalizeFrame(value), shot = shotAt(f), c = camAt(f);
    camera.position.set(...c.pos);
    camera.fov = Math.max(38, Math.min(50, c.fov));
    camera.up.set(0, 1, 0);
    camera.lookAt(...c.look);
    camera.rotateZ(c.roll);
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    world.update(shot.id, f, camera, scene);
    camera.fov = Math.max(38, Math.min(50, camera.fov));
    camera.updateProjectionMatrix();
    camera.updateMatrixWorld();
    noInkFallback(world.root);
    const dof = dofAt(f);
    lens.focus = dof.focus;
    lens.cInf = dof.cInf;
    lens.sharpDepth = ink.worldDepthTexture;
    gradeFor(grade, shot.grade ?? "vivid");
    renderer.toneMappingExposure = shot.exposure ?? 1;
    composer.render(1 / FPS);
    updateHud(f);
    window.currentFrame = f;
    slider.value = String(f);
    readout.textContent = "Frame " + f + " / " + (TOTAL - 1) + " · " + (f / FPS).toFixed(2) + " s";
    for (const button of $("cuts").children) {
      button.setAttribute("aria-pressed", String(Number(button.dataset.frame) === f));
    }
    return f;
  }

  function syncAudio() {
    try { audio.currentTime = window.currentFrame / FPS; } catch { /* Metadata may not be ready yet. */ }
  }

  function pausePlayback() {
    playing = false;
    cancelAnimationFrame(raf);
    raf = 0;
    audio.pause();
    audioClock = false;
    playButton.textContent = "Play";
    playButton.setAttribute("aria-pressed", "false");
  }

  window.setFrame = (f) => {
    pausePlayback();
    const frame = renderFrame(f);
    syncAudio();
    return frame;
  };

  function playAudio() {
    syncAudio();
    audio.play().then(() => {
      if (playing && sound.checked) audioClock = true;
      else audio.pause();
    }).catch(() => {
      audioClock = false;
      notice.textContent = "Narration could not play; the visual preview continues silently.";
    });
  }

  function tick(now) {
    if (!playing) return;
    const seconds = audioClock && !audio.paused ? audio.currentTime : startSeconds + (now - startedAt) / 1000;
    if (seconds >= duration) {
      renderFrame(TOTAL - 1);
      pausePlayback();
      return;
    }
    const f = Math.min(TOTAL - 1, Math.floor(seconds * FPS));
    if (f !== window.currentFrame) renderFrame(f);
    raf = requestAnimationFrame(tick);
  }

  function startPlayback() {
    if (exporting || playing) return;
    if (window.currentFrame === TOTAL - 1) window.setFrame(0);
    startSeconds = window.currentFrame / FPS;
    startedAt = performance.now();
    playing = true;
    playButton.textContent = "Pause";
    playButton.setAttribute("aria-pressed", "true");
    if (sound.checked) playAudio();
    raf = requestAnimationFrame(tick);
  }

  audio.addEventListener("loadedmetadata", () => { if (!playing) syncAudio(); });
  audio.addEventListener("ended", () => {
    // A shorter narration does not shorten the 525-frame visual timeline.
    startSeconds = audio.currentTime;
    startedAt = performance.now();
    audioClock = false;
  });
  audio.addEventListener("error", () => {
    startSeconds = window.currentFrame / FPS;
    startedAt = performance.now();
    audioClock = false;
    notice.textContent = "Narration is unavailable; visual playback and sheet export still work.";
  });
  sound.addEventListener("change", () => {
    audio.pause();
    audioClock = false;
    startSeconds = window.currentFrame / FPS;
    startedAt = performance.now();
    if (playing && sound.checked) playAudio();
    else syncAudio();
  });
  playButton.addEventListener("click", () => playing ? pausePlayback() : startPlayback());
  slider.addEventListener("input", () => window.setFrame(slider.value));
  for (let i = 0; i < CAL_FRAMES.length; i++) {
    const button = document.createElement("button");
    button.type = "button";
    button.dataset.frame = String(CAL_FRAMES[i]);
    button.textContent = "cut " + shotAt(CAL_FRAMES[i]).id + " · " + CAL_FRAMES[i];
    button.addEventListener("click", () => window.setFrame(CAL_FRAMES[i]));
    $("cuts").append(button);
  }

  window.renderCalibrationSheet = async () => {
    if (exporting) throw new Error("A calibration sheet is already being rendered.");
    exporting = true;
    const savedFrame = window.currentFrame, resume = playing;
    pausePlayback();
    $("controls").disabled = true;
    notice.textContent = "Rendering eight calibration tiles…";
    try {
      await document.fonts.ready;
      const sheet = document.createElement("canvas");
      sheet.width = WIDTH * 4;
      sheet.height = HEIGHT * 2;
      const ctx = sheet.getContext("2d");
      if (!ctx) throw new Error("Canvas2D is unavailable.");
      for (let i = 0; i < CAL_FRAMES.length; i++) {
        window.setFrame(CAL_FRAMES[i]);
        renderer.getContext().finish();
        const x = (i % 4) * WIDTH, y = Math.floor(i / 4) * HEIGHT;
        ctx.save();
        ctx.translate(x, y);
        ctx.drawImage(renderer.domElement, 0, 0, WIDTH, HEIGHT);
        drawHud(ctx);
        const label = "cut " + shotAt(CAL_FRAMES[i]).id + " · frame " + CAL_FRAMES[i];
        ctx.font = "900 15px Arial, sans-serif";
        ctx.fillStyle = "rgba(15,12,24,0.88)";
        ctx.fillRect(8, 8, ctx.measureText(label).width + 16, 27);
        ctx.fillStyle = "white";
        ctx.textAlign = "left";
        ctx.textBaseline = "middle";
        ctx.fillText(label, 16, 21.5);
        ctx.restore();
      }
      const blob = await new Promise((resolve, reject) => sheet.toBlob(
        (result) => result ? resolve(result) : reject(new Error("JPEG encoding failed.")),
        "image/jpeg", 0.95,
      ));
      const url = URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = "gandhiji-school-calibration-2160x1920.jpg";
      document.body.append(link);
      link.click();
      link.remove();
      setTimeout(() => URL.revokeObjectURL(url), 10000);
      notice.textContent = "Calibration sheet downloaded: 2160 × 1920 JPEG.";
      return sheet;
    } catch (error) {
      notice.textContent = "Sheet export failed: " + (error?.message ?? String(error));
      throw error;
    } finally {
      window.setFrame(savedFrame);
      exporting = false;
      $("controls").disabled = false;
      if (resume) startPlayback();
    }
  };
  sheetButton.addEventListener("click", () => { window.renderCalibrationSheet().catch(console.error); });

  const resizeStage = () => { viewport.style.transform = "scale(" + stage.clientWidth / WIDTH + ")"; };
  const observer = new ResizeObserver(resizeStage);
  observer.observe(stage);
  resizeStage();
  renderer.domElement.addEventListener("webglcontextlost", (event) => {
    event.preventDefault();
    pausePlayback();
    window.__gandhijiReady = false;
    window.__gandhijiError = "WebGL context lost. Reload this preview.";
    notice.textContent = window.__gandhijiError;
    $("controls").disabled = true;
  });
  window.addEventListener("pagehide", () => {
    pausePlayback();
    observer.disconnect();
    world.dispose?.();
    composer.dispose();
    renderer.dispose();
    window.__gandhijiReady = false;
  }, {once: true});

  window.setFrame(0);
  renderer.getContext().finish();
  $("controls").disabled = false;
  notice.textContent = "Offline preview ready. Narration is optional; playback does not start automatically.";
  window.__gandhijiReady = true;
}

boot().catch((error) => {
  window.__gandhijiReady = false;
  window.__gandhijiError = error?.message ?? String(error);
  $("notice").textContent = "Preview failed: " + window.__gandhijiError;
  console.error(error);
});
`;

const result = await build({
  absWorkingDir: projectDir,
  stdin: {contents: entry, resolveDir: scriptsDir, sourcefile: "gandhiji-preview-entry.js", loader: "js"},
  bundle: true,
  write: false,
  platform: "browser",
  format: "iife",
  target: ["es2022"],
  minify: true,
  legalComments: "none",
  sourcemap: false,
  logLevel: "warning",
  define: {"process.env.NODE_ENV": '"production"'},
  loader: {".png": "dataurl", ".jpg": "dataurl", ".jpeg": "dataurl", ".webp": "dataurl", ".svg": "dataurl", ".mp3": "dataurl"},
});
const bundle = result.outputFiles[0].text.replace(/<\/script/gi, "<\\/script");
const narration = (await readFile(path.join(projectDir, "public", "gandhiji_school", "audio.mp3"))).toString("base64");
const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="color-scheme" content="dark">
<title>Gandhiji school · Offline calibration preview</title>
<style>
*{box-sizing:border-box}body{margin:0;background:#0e0b17;color:#f6f3fc;font:15px Arial,sans-serif}
main{width:min(100%,580px);margin:0 auto;padding:14px 20px 24px}h1{font-size:18px;margin:0 0 12px}
#stage{position:relative;width:100%;max-width:540px;aspect-ratio:9/16;overflow:hidden;background:#9fd0f5;border-radius:12px}
#viewport{position:absolute;left:0;top:0;width:540px;height:960px;transform-origin:0 0}
#world-canvas{display:block;width:540px;height:960px}.hud{position:absolute;box-sizing:border-box;text-align:center;white-space:pre;pointer-events:none}.hud[hidden]{display:none}
fieldset{padding:0;border:0;margin:14px 0 0;min-width:0}legend{position:absolute;width:1px;height:1px;padding:0;overflow:hidden;clip:rect(0,0,0,0)}
.row{display:flex;align-items:center;gap:10px;flex-wrap:wrap;margin:10px 0}button{cursor:pointer;border:1px solid #564668;border-radius:9px;background:#211a31;color:white;padding:10px 12px;font:inherit;min-height:44px}
button:hover,button[aria-pressed=true]{background:#443057;border-color:#ba97d9}button:disabled{cursor:wait;opacity:.5}
button:focus-visible,input:focus-visible{outline:2px solid #d6b8ff;outline-offset:3px}input[type=range]{width:100%;height:32px;accent-color:#bd98e6}input[type=checkbox]{width:18px;height:18px;accent-color:#bd98e6}
label{display:flex;align-items:center;gap:7px}#readout{font-variant-numeric:tabular-nums;font-size:14px}#cuts{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:7px}#cuts button{font-size:12px;padding:8px 4px}
#sheet{width:100%;margin-top:12px}#notice,.help{font-size:12px;line-height:1.5;color:#cbbfd7;margin:12px 0 0}
@media(max-width:380px){main{padding:10px 10px 20px}#cuts{grid-template-columns:repeat(2,minmax(0,1fr))}}
</style>
</head>
<body>
<main>
<h1>Gandhiji school · Calibration preview</h1>
<div id="stage"><div id="viewport"><div id="hud-title" class="hud" hidden></div><div id="hud-secondary" class="hud" hidden></div></div></div>
<fieldset id="controls" disabled>
<legend>Preview controls</legend>
<div class="row"><button id="play" type="button" aria-pressed="false">Play</button><label><input id="sound" type="checkbox">Narration</label><output id="readout" for="frame">Frame 0 / 524 · 0.00 s</output></div>
<label for="frame">Seek frame</label><input id="frame" type="range" min="0" max="524" step="1" value="0">
<div id="cuts" aria-label="Eight calibration frames"></div>
<button id="sheet" type="button">Download sheet</button>
</fieldset>
<p id="notice" role="status">Initializing offline WebGL preview…</p>
<p class="help">540 × 960 · 525 frames at 30 fps · 17.5 seconds. Sheet: four columns × two rows. Requires WebGL2; fonts use local system fallbacks. No network dependencies or MP4 output.</p>
<audio id="narration" preload="auto" src="data:audio/mpeg;base64,${narration}"></audio>
</main>
<script>${bundle}</script>
</body>
</html>
`;

await mkdir(outputDir, {recursive: true});
const outputFile = path.join(outputDir, "preview.html");
await writeFile(outputFile, html, "utf8");
console.log(`Wrote ${outputFile} (${(Buffer.byteLength(html) / 1024 / 1024).toFixed(2)} MiB; bundled JS and unchanged embedded narration).`);
