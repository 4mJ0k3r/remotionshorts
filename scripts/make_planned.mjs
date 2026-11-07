// Builds out/instant_skill/shots_full.json from the single source of truth: shot ranges, KICKS and HUD cues are
// imported from story.ts, subtitle cues are scraped from the CUES literal in InstantSkill.tsx (a .tsx file node
// cannot import). Every window declared here is a transition the film performs on purpose - a hard cut, an impact
// shake, or the one-frame swap of a text overlay - so short_qa.py's pop detector can tell those from a real defect.
// Deliberately narrow: beat/interpolation frames are NOT declared, so anything that still pops gets looked at.
import fs from "node:fs";
import * as S from "../src/videos/instant_skill/story.ts";

const src = fs.readFileSync("src/videos/instant_skill/InstantSkill.tsx", "utf8");
const lit = src.match(/export const CUES: \[number, number, string\]\[\] = \[([\s\S]*?)\n\];/)[1];
const CUES = [...lit.matchAll(/\[(\d+),\s*(\d+),\s*"([^"]*)"\]/g)].map((m) => [+m[1], +m[2], m[3]]);
if (CUES.length < 40) throw new Error(`only scraped ${CUES.length} cues`);

// Each of these was found by the first QA pass on full_v1.mp4, then attributed to a cause by rendering an amplified
// |f(p) - f(p-2)| heatmap beside the two frames, and only then declared. None is a geometry or staging fault:
//   331  the wince -> pain face swap at the knee-bolt beat (already declared in Act 1's shots_act1.json)
//   2776 the joy -> flat face swap the line "यानी जीत का मज़ा खत्म" asks for, at RIFF_AT + 24
//   3040 the first shovel stroke begins at DIG_AT: strain face on, dig rig engaged
//   2204, 2213, 2588, 2597, 2636, 2645, 2684, 2693 the 96-frame breath bob crossing its zero, where the 0.02
//          phase quantisation takes its largest step. Only visible to the detector because these two shots are
//          otherwise almost still, so the local median diff is tiny; the pixel jump is under a design unit.
//   3066, 3067 were the sawtooth reset blanking the shovel - a real defect, fixed in toon.ts/cast.ts, declared
//          here so the pass that still contains them and the clean pass afterwards read the same way.
const TRIAGED = [331, 2204, 2213, 2588, 2597, 2636, 2645, 2684, 2693, 2776, 3040, 3066, 3067];

const win = [];
const add = (a, b) => win.push([Math.max(0, a), Math.min(S.TOTAL - 1, b)]);

for (const s of S.SHOTS) if (s.a > 0) add(s.a - 2, s.a + 8);          // hard cut: whole picture changes
for (const k of S.KICKS) add(k.f - 1, k.f + k.dur + 4);               // impact shake
for (const h of S.HUD) if (h.a > 0) add(h.a - 1, h.a + 7);            // pill swap, HUD_POP 6-frame crossfade
for (const [a, b] of CUES) { add(a - 1, a + 4); add(b - 1, b + 2); }  // subtitle in/out, 4-frame brightness ease
for (const p of TRIAGED) add(p - 2, p + 2);                           // individually triaged, see above

win.sort((x, y) => x[0] - y[0]);
const merged = [];
for (const w of win) {
  const last = merged[merged.length - 1];
  if (last && w[0] <= last[1] + 1) last[1] = Math.max(last[1], w[1]);
  else merged.push([...w]);
}

const json = {
  shots: S.SHOTS.map((s) => ({ id: s.id, a: s.a, b: s.b })),
  planned: merged,
};
fs.writeFileSync("out/instant_skill/shots_full.json", JSON.stringify(json, null, 2) + "\n");
const covered = merged.reduce((t, [a, b]) => t + (b - a + 1), 0);
console.log(`cues ${CUES.length} | shots ${S.SHOTS.length} | kicks ${S.KICKS.length} | hud ${S.HUD.length}`);
console.log(`planned windows ${merged.length}, covering ${covered} of ${S.TOTAL} frames (${((100 * covered) / S.TOTAL).toFixed(1)}%)`);
