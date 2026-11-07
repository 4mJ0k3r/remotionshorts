// usage: node scripts/bridge-video.mjs <out.mp4> [firstFrame] [lastFrame] [scale] [compositionId]
// Motion test: 540x960 h264, default frames 0-1500 at 30 fps. GPU via ANGLE like the stills renderer.
// compositionId defaults to BridgeShort (BRIDGE_ID also works for shells that support VAR=value cmd).
import fs from "node:fs";
import path from "node:path";
if (!process.env.REMOTION_TMP) process.env.REMOTION_TMP = "D:/remotion-tmp";
fs.mkdirSync(process.env.REMOTION_TMP, { recursive: true });
process.env.TEMP = process.env.TMP = process.env.REMOTION_TMP;
import { bundle } from "@remotion/bundler";
import { renderMedia, selectComposition } from "@remotion/renderer";
const [out, first = "0", last = "1500", scale = "0.5", compId] = process.argv.slice(2);
const inputProps = process.env.BRIDGE_PROPS ? JSON.parse(process.env.BRIDGE_PROPS) : {};
const browserExecutable = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const chromiumOptions = { gl: "angle" };
const tmpBefore = new Set(fs.readdirSync(process.env.REMOTION_TMP));
const dirSize = (d) => { let s = 0; for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); try { s += e.isDirectory() ? dirSize(p) : fs.statSync(p).size; } catch {} } return s; };
const serveUrl = await bundle({ entryPoint: path.resolve("src/index.ts"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: compId || process.env.BRIDGE_ID || "BridgeShort", browserExecutable, chromiumOptions });
const onBrowserLog = (l) => { if (process.env.BRIDGE_DEBUG || l.type === "error") console.log(`[${l.type}]`, l.text.slice(0, 300)); };
const t0 = Date.now();
let lastPct = -1;
await renderMedia({ composition, serveUrl, codec: "h264", crf: 20, outputLocation: out,
  frameRange: [Number(first), Number(last)], scale: Number(scale), inputProps,
  browserExecutable, chromiumOptions, timeoutInMilliseconds: 300000, onBrowserLog,
  concurrency: Number(process.env.BRIDGE_CONCURRENCY || 2),
  onProgress: ({ renderedFrames, encodedFrames }) => {
    const pct = Math.floor((renderedFrames / (Number(last) - Number(first) + 1)) * 100);
    if (pct >= lastPct + 10) { lastPct = pct - (pct % 10); console.log(`frames ${renderedFrames} (${pct}%), encoded ${encodedFrames}, ${((Date.now() - t0) / 60000).toFixed(1)} min`); }
  } });
console.log(`done ${out} in ${((Date.now() - t0) / 60000).toFixed(1)} min`);
if (!process.env.BRIDGE_KEEP_TMP) {
  let n = 0, freed = 0;
  for (const name of fs.readdirSync(process.env.REMOTION_TMP)) {
    if (tmpBefore.has(name) || !/^(remotion-webpack-bundle-|puppeteer_dev_chrome_profile-)/.test(name)) continue;
    const p = path.join(process.env.REMOTION_TMP, name);
    try { freed += dirSize(p); fs.rmSync(p, { recursive: true, force: true }); n++; } catch {}
  }
  console.log(`cleanup: removed ${n} temp dir(s), ${(freed / 1e6).toFixed(0)} MB from ${process.env.REMOTION_TMP}`);
}
