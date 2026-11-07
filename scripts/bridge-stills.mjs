// usage: node scripts/bridge-stills.mjs <outPrefix> <frame,frame,...> [scale]  (bundles once, GPU via ANGLE, jpeg)
// BRIDGE_ENTRY=src/sandboxes/<name>/index.tsx renders a sandbox copy instead of the main project entry.
import fs from "node:fs";
// each bundle copies public/ (~1.3 GB) into the temp dir; keep bundles on the big D: drive
// Remotion bundles fill the temp folder (~1.3 GB each): set REMOTION_TMP to a folder on a big drive
if (!process.env.REMOTION_TMP) process.env.REMOTION_TMP = "D:/remotion-tmp";
fs.mkdirSync(process.env.REMOTION_TMP, { recursive: true });
process.env.TEMP = process.env.TMP = process.env.REMOTION_TMP;
import { bundle } from "@remotion/bundler";
import { renderStill, selectComposition } from "@remotion/renderer";
import path from "node:path";
const [prefix, frames, scale = "0.5"] = process.argv.slice(2);
const inputProps = process.env.BRIDGE_PROPS ? JSON.parse(process.env.BRIDGE_PROPS) : {};
const browserExecutable = "C:/Program Files/Google/Chrome/Application/chrome.exe";
const chromiumOptions = { gl: "angle" };
const tmpBefore = new Set(fs.readdirSync(process.env.REMOTION_TMP));
const dirSize = (d) => { let s = 0; for (const e of fs.readdirSync(d, { withFileTypes: true })) { const p = path.join(d, e.name); try { s += e.isDirectory() ? dirSize(p) : fs.statSync(p).size; } catch {} } return s; };
const serveUrl = await bundle({ entryPoint: path.resolve(process.env.BRIDGE_ENTRY || "src/index.ts"), publicDir: path.resolve("public") });
const composition = await selectComposition({ serveUrl, id: process.env.BRIDGE_ID || "BridgeShort", browserExecutable, chromiumOptions });
const onBrowserLog = (l) => { if (process.env.BRIDGE_DEBUG || l.type === "error" || l.type === "warning") console.log(`[${l.type}]`, l.text.slice(0, 300)); };
for (const f of frames.split(",").map(Number)) {
  const t0 = Date.now();
  await renderStill({ composition, serveUrl, frame: f, output: `${prefix}${f}.jpg`, imageFormat: "jpeg", jpegQuality: 88, scale: Number(scale), inputProps,
    browserExecutable, chromiumOptions, timeoutInMilliseconds: 180000, onBrowserLog });
  console.log("still", f, ((Date.now() - t0) / 1000).toFixed(1) + "s");
}
// remove this run's temp bundle folders (previous runs' folders are left alone); BRIDGE_KEEP_TMP=1 opts out
if (!process.env.BRIDGE_KEEP_TMP) {
  let n = 0, freed = 0;
  for (const name of fs.readdirSync(process.env.REMOTION_TMP)) {
    if (tmpBefore.has(name) || !/^(remotion-webpack-bundle-|puppeteer_dev_chrome_profile-)/.test(name)) continue;
    const p = path.join(process.env.REMOTION_TMP, name);
    try { freed += dirSize(p); fs.rmSync(p, { recursive: true, force: true }); n++; } catch {}
  }
  console.log(`cleanup: removed ${n} temp dir(s), ${(freed / 1e6).toFixed(0)} MB from ${process.env.REMOTION_TMP}`);
}
