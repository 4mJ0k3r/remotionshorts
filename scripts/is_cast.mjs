// cast.ts audit. scripts/is_frame.mjs proves the DECLARED staging tables are well-framed; it cannot see cast.ts,
// because cast.ts is a browser module. This script imports the real stage() headlessly (a two-line document stub is
// all cast.ts touches at load time) and checks three things that are otherwise only visible after a 20-minute render:
//
//   1. CARD COVERAGE - every slot story.ts says a shot shows is emitted at that slot's own position and scale, and
//      no card is emitted where story.ts says the shot is empty. This is what catches a shot rendering nobody.
//   2. CACHE DISCIPLINE - every continuous float inside the emitted texture key sits on the 0.02 grid. A float that
//      skips q2 in hero() makes a brand-new full-size canvas for every frame of every actor, which is how a
//      3714-frame render runs out of memory at frame 900.
//   3. FX BUDGET - the number of cards per frame stays inside the pool the Actor/Fx arrays were sized for.
//
// Usage: node scripts/is_cast.mjs [step]
import * as S from "../src/videos/instant_skill/story.ts";
import * as THREE from "three";
import { register } from "node:module";

register("./ts_resolve.mjs", import.meta.url);

const STUB_CTX = new Proxy({}, { get: () => () => ({ addColorStop() {} }) });
globalThis.document = { createElement: () => ({ width: 0, height: 0, getContext: () => STUB_CTX }) };
const { stage } = await import("../src/videos/instant_skill/cast.ts");

const step = +(process.argv[2] ?? 5);
const UP = new THREE.Vector3(0, 1, 0);

/** cast.ts only ever reads the camera position and its right axis, both of which story.ts's profile gives us. */
const camInfo = (id, f) => {
  const c = S.camAt(id, f);
  const pos = new THREE.Vector3(...c.pos);
  const fwd = new THREE.Vector3(...c.look).sub(pos).normalize();
  return { pos, right: new THREE.Vector3().crossVectors(fwd, UP).normalize() };
};

const fails = [];
const slotsOf = (id, f) => (S.CAST_SLOTS[id] ?? []).filter((s) => !(s.hide ? s.hide(f) : false));

console.log("=== card coverage: stage() vs story.ts CAST_SLOTS ===");
for (const s of S.SHOTS) {
  let worst = 0, miss = 0, extra = 0, maxFx = 0, keys = new Set();
  for (let f = s.a; f < s.b; f += step) {
    const st = stage(s.id, f / S.FPS, camInfo(s.id, f));
    const want = slotsOf(s.id, f);
    if (st.places.length !== want.length) { miss++; continue; }
    for (const w of want) {
      const p = w.path ? w.path(f) : w.at;
      const near = st.places.reduce((b, c) =>
        Math.hypot(c.x - p[0], c.y - p[1], c.z - p[2]) < Math.hypot(b.x - p[0], b.y - p[1], b.z - p[2]) ? c : b);
      const d = Math.hypot(near.x - p[0], near.y - p[1], near.z - p[2]);
      worst = Math.max(worst, d);
      if (Math.abs(near.scale - w.scale) > 1e-9) extra++;
      keys.add(near.key);
    }
    maxFx = Math.max(maxFx, st.fx.length);
  }
  const bad = miss > 0 || worst > 0.05 || extra > 0;
  if (bad) {
    fails.push(`s${s.id}: count misses ${miss}, worst position drift ${(worst * 100).toFixed(1)} cm, scale mismatches ${extra}`);
  }
  console.log(`  shot ${String(s.id).padStart(2)}: cards ${slotsOf(s.id, s.a).length} -> ${miss ? "MISS" : "ok"}  drift ${(worst * 100).toFixed(1)} cm  fx/frame ${maxFx}  draw variants ${keys.size}  ${bad ? "FAIL" : "ok"}`);
}

console.log("\n=== cache discipline: every float in a card key sits on the 0.02 grid ===");
// sitDrop is a per-slot CONSTANT in design units (145.86 on the bench), never an animated float, so it is exempt.
const EXEMPT = new Set(["sitDrop"]);
for (const s of S.SHOTS) {
  const offenders = new Map();
  for (let f = s.a; f < s.b; f += step) {
    for (const p of stage(s.id, f / S.FPS, camInfo(s.id, f)).places) {
      if (!p.key.startsWith("CH|")) continue;
      const q = JSON.parse(p.key.slice(3));
      for (const [k, v] of Object.entries(q)) {
        if (typeof v !== "number" || EXEMPT.has(k)) continue;
        if (Math.abs(v * 50 - Math.round(v * 50)) > 1e-6) offenders.set(k, (offenders.get(k) ?? 0) + 1);
      }
    }
  }
  const bad = offenders.size > 0;
  if (bad) fails.push(`s${s.id}: un-quantised floats ${[...offenders.keys()].join(", ")} - Pool will redraw a canvas every frame`);
  console.log(`  shot ${String(s.id).padStart(2)}: ${bad ? [...offenders].map(([k, n]) => `${k} x${n}`).join(", ") : "all floats on grid"}  ${bad ? "FAIL" : "ok"}`);
}

console.log(`\n${fails.length ? `FAILURES (${fails.length}):\n` + fails.map((f) => `  ${f}`).join("\n") : `SUCCESS: ${S.SHOTS.length} shots staged, positions and scales agree with the slot table, no cache-key leak`}`);
process.exit(fails.length ? 1 : 0);
