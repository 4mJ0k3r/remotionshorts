// Single source of truth for InstantSkillShort: time, beats, shots, camera paths, impact kicks, DOF tracking and
// the coordinate tables every other file shares. Pure math only — no Three.js meshes anywhere in this file.
//
// ACT 1 = 8 shots over f0..1193 (39.8 s), three story blocks:
//   BLOCK 1  f0..455     TWILIGHT CITY SKATEPARK   kickflip cheat-code, then the biology backfire  (shots 1-3)
//   BLOCK 2  f456..983   CHESS LOUNGE              15-second Rubik's solve, blindfold checkmate     (shots 4-6)
//   BLOCK 3  f984..1193  CABIN + POKER             40 languages on a flight, then the poker millions (shots 7-8)
// ACT 2 = 11 shots over f1194..2907 (57.1 s), the price of the power:
//   BLOCK 4  f1194..1837 SKATEPARK + SNOW + HIGHWAY  brain level 999, body still level 1             (shots 9-13)
//   BLOCK 5  f1838..2487 NEON BRAIN CHAMBER          neurons overheat, nothing forgotten, 24 h loop  (shots 14-16)
//   BLOCK 6  f2488..2907 SKATEPARK                   friends leave, the guitar dies, winning stops    (shots 17-19)
// ACT 3 = 6 shots over f2908..3713 (26.9 s), the payoff and the question:
//   BLOCK 7  f2908..3256 SNOW                        avalanche, the buried friend, the snow angle     (shots 20-22)
//   BLOCK 8  f3257..3713 NIGHT ROAD                  the empty car, the alien code, "would you?"      (shots 23-25)
// Eight isolated THREE.Group sets (SKILL.md Hard Rule 8): SET_SKATE (1-3, 9-10, 17-19), SET_CHESS (4-6), SET_CABIN (7),
// SET_POKER (8), SET_SNOW (11, 20-22), SET_HWY (12-13), SET_BRAIN (14-16), SET_ROAD (23-25).
// A shot never sees a mesh from another set.
//
// v2 art direction: no easels or placards anywhere (every stat readout is an HTML HUD pill, HUD[] below), a head
// never repeats a front-on camera angle, twilight-violet exteriors with lit windows, a bare sphere head, and chess
// + poker staged in DEPTH so the cast never projects as a side-by-side lineup.
export const FPS = 30;
export const TOTAL = 3714;

export type V3 = [number, number, number];
export type LightName = "dusk" | "hall" | "cabin" | "lounge" | "snow" | "asphalt" | "mind" | "night";
export type SetName = "skate" | "chess" | "cabin" | "poker" | "snow" | "hwy" | "brain" | "road";
export type ShotDef = { id: number; a: number; b: number; light: LightName; set: SetName; desc: string };

// ---------------- math helpers ----------------
export const clamp01 = (v: number) => Math.max(0, Math.min(1, v));
export const lerp = (a: number, b: number, t: number) => a + (b - a) * t;
export const seg = (a: number, b: number, x: number) => clamp01((x - a) / (b - a));
/** smootherstep — every camera move in the film runs through this */
export const glide = (f: number, a: number, b: number) => {
  const t = clamp01((f - a) / Math.max(1, b - a));
  return t * t * (3 - 2 * t);
};
export const v3Lerp = (p0: V3, p1: V3, t: number): V3 => [lerp(p0[0], p1[0], t), lerp(p0[1], p1[1], t), lerp(p0[2], p1[2], t)];
/**
 * Post-move micro-drift. SKILL.md 4.1 forbids a still hold at the end of a shot: once the main glide has landed,
 * the camera keeps creeping forward by `dist` metres over the remaining frames so no frame is ever frozen.
 */
export const pushK = (f: number, a: number, b: number, dist: number) => glide(f, a, b) * dist;

// ---------------- beat markers ----------------
// BLOCK 1 — skatepark
export const PHONE_DOWN_AT = 55;      // phone lowers into the hip, the download lands, his eyes go neon
export const PHONE_DOWN_END = 112;
export const GLOW_AT = PHONE_DOWN_AT;
export const GLOW_END = 164;
export const FLIP_START_AT = 180;     // board pops off the pad
export const FLIP_APEX_AT = 208;      // mid-air, board spinning under the feet
export const LAND_AT = 235;           // clean landing + KICK + pop spark
export const AIR_LIFT = 0.34;         // metres the whole card leaves the concrete at the apex of the kickflip
export const JAW_AT = 205;            // red-hoodie skater's jaw drops
export const PAIN_AT = 285;           // wince starts, kneePainP 0 -> 1
export const PAIN_END = 330;          // pain pose settled, sparks keep pulsing
// BLOCK 2 — chess hall
export const CUBE_START_AT = 460;     // cube enters the hands
export const CUBE_SLAM_AT = 560;      // solved cube hits the tabletop + KICK
export const SMUG_AT = 575;           // arms up, smirk
export const DISBELIEF_AT = 470;      // green-hoodie friend starts staring
export const BLIND_AT = 636;          // blindfold goes on with the shot
export const REACH_START_AT = 648;    // hero's fist travels toward the 3D king
export const KING_FALL_AT = 705;      // king tips over + KICK + impact star
export const REACH_END_AT = 726;
export const GM_SHOCK_AT = 712;       // grandmaster jumps
export const GESTURE_AT = 482;        // friend throws both arms out at the solved cube — inside shot 4, where his face is framed
export const UNBLIND_AT = 860;        // blindfold pushed up
export const THUMBS_AT = 872;         // double thumbs at his own chest
export const STARS_AT = 885;          // gold sparkle bursts on the shoulders
// BLOCK 3 — cabin + poker
export const DICT_AT = 990;           // grammar book enters the hands, fans 0 -> 1
export const DICT_END_AT = 1044;
export const CLAP_AT = 1040;          // passenger claps
export const SHADES_AT = 1090;        // sunglasses on
export const CASH_START_AT = 1100;    // cash stacks begin rising
export const CASH_SPARK_AT = 1125;    // sparkle burst + KICK
export const CASH_END_AT = 1160;
export const SLUMP_AT = 1130;         // both opponents slump in defeat
// BLOCK 4 — the body protests (shots 9-13)
export const PROTEST_AT = 1215;       // hero looks at his own hands, physics lecture lands
export const POINT_AT = 1258;         // he accuses the sky, the friend doubles over laughing
export const SPLIT_AT = 1330;         // one hand to the head, one to the thigh: BRAIN vs BODY
export const SPLIT_END_AT = 1470;
export const DROP_AT = 1524;          // snow: he leaves the kicker lip
export const APEX_AT = 1552;          // mid-air, board spinning under the feet
export const AIR_LIFT_SNOW = 0.70;    // metres of arc above the slope line — capped by shot 11's crown band
export const SNOW_LAND_AT = 1574;
export const SPEED_AT = 1604;         // highway: hands to the wheel, the road starts scrolling
export const SPEED_END_AT = 1660;
export const GRIP_FAIL_AT = 1712;     // he feels the G-force, the body gives out
export const DESPAIR_AT = 1770;       // hands clamp the head: dimag pro, body sasti
// BLOCK 5 — the brain chamber (shots 14-16)
export const DATA_AT = 1880;          // the neuron core lights, thousands of songs download
export const OVERHEAT_AT = 1955;      // core turns red, sparks leave the shoulders + KICK
export const OVERHEAT_END_AT = 2050;
export const NOFORGET_AT = 2110;      // he realises nothing is going away: startle
export const LOOP_AT = 2290;          // the three memory screens switch on in sequence
export const LOOP_AT2 = 2352;
export const LOOP_AT3 = 2414;
export const COVER_AT = 2440;         // both hands over the ears
// BLOCK 6 — the fun goes (shots 17-19)
export const LEAVE_AT = 2528;         // the two friends turn and walk out of frame
export const LEAVE_END_AT = 2600;
export const GUITAR_AT = 2716;        // the guitar enters his hands
export const RIFF_AT = 2752;          // first chord lands + KICK
export const GUITAR_END_AT = 2800;
export const DEFLATE_AT = 2832;       // arms drop, the smile goes flat
export const BENCH_AT = 2856;         // he sits down on the bench, alone
// BLOCK 7 — the avalanche (shots 20-22)
export const AVAL_AT = 2940;          // the snow wall starts its traverse + KICK at 2975
export const AVAL_HIT_AT = 2975;
export const BURIED_AT = 3006;        // the mound settles over his friend
export const DIG_AT = 3040;           // shovel strokes begin
export const DIG_END_AT = 3170;
export const SOLVE_AT = 3108;         // the snow-angle read: the core screen goes cyan
export const BREAK_AT = 3200;         // friend pops out of the snow + KICK
export const RELIEF_AT = 3228;
// BLOCK 8 — the night road (shots 23-25)
export const CAR_IN_AT = 3272;        // the empty car rolls in from off-frame
export const CAR_STOP_AT = 3348;      // it parks, engine glow still moving + KICK at 3300
export const DOOR_AT = 3400;
export const UFO_AT = 3424;           // the beam column reaches the street
export const CODE_AT = 3450;          // the glyph drops into his fist + KICK
export const CODE_END_AT = 3566;
export const CHOICE_AT = 3600;        // he looks straight into the lens
export const FINAL_THUMBS_AT = 3640;  // last thumb up + KICK

// ---------------- HUD stat pills ----------------
// The only text laid over the picture besides the subtitles: InstantSkill.tsx draws one pill at a time in the top
// band and hides it with the same `subs` flag the calibration stills use. Every `a` is a planned window in
// shots_act1.json, because swapping the pill text is a real frame-to-frame change the pop detector would flag.
export type HudCue = { a: number; b: number; text: string; tone: "gold" | "cyan" };
export const HUD: HudCue[] = [
  { a: 0, b: 165, text: "HOW TO KICKFLIP  ·  10 SEC TUTORIAL", tone: "cyan" },
  { a: 165, b: 270, text: "1ST TRY  ·  LANDED CLEAN", tone: "gold" },
  { a: 270, b: 456, text: "BRAIN: PRO  ·  BODY: NORMAL", tone: "gold" },
  { a: 456, b: 636, text: "0:15.00  ·  RUBIK'S SOLVED", tone: "cyan" },
  { a: 636, b: 855, text: "BLINDFOLD CHECKMATE", tone: "gold" },
  { a: 855, b: 984, text: "HUMAN CHAT-GPT", tone: "cyan" },
  { a: 984, b: 1086, text: "40 LANGUAGES MASTERED", tone: "gold" },
  { a: 1086, b: 1194, text: "WIN ODDS: 99.8%", tone: "cyan" },
  { a: 1194, b: 1297, text: "PHYSICS STRIKES BACK", tone: "gold" },
  { a: 1297, b: 1499, text: "BRAIN: INSTANT  ·  BODY: LVL 1", tone: "cyan" },
  { a: 1499, b: 1588, text: "OLYMPIC FEED  ·  DOUBLE BACKFLIP", tone: "cyan" },
  { a: 1588, b: 1663, text: "300 KM/H  ·  GRIP LOCKED", tone: "gold" },
  { a: 1663, b: 1838, text: "MIND: 999  ·  BODY: STOCK", tone: "gold" },
  { a: 1838, b: 2067, text: "NEURONS OVERHEATING  ·  1000 SONGS", tone: "gold" },
  { a: 2067, b: 2248, text: "FORGETTING: DISABLED", tone: "cyan" },
  { a: 2248, b: 2487, text: "24H HD LOOP  ·  NO OFF SWITCH", tone: "gold" },
  { a: 2487, b: 2698, text: "FRIENDS: 3  ·  0 LEFT", tone: "gold" },
  { a: 2698, b: 2810, text: "GUITAR MASTERED: 03:00", tone: "cyan" },
  { a: 2810, b: 2908, text: "FUN OF WINNING: 0%", tone: "cyan" },
  { a: 2908, b: 2998, text: "AVALANCHE  ·  CLASS 4", tone: "gold" },
  { a: 2998, b: 3088, text: "FRIEND UNDER SNOW  ·  4 MIN", tone: "gold" },
  { a: 3088, b: 3257, text: "SNOW ANGLE SOLVED  ·  DIG NOW", tone: "cyan" },
  { a: 3257, b: 3381, text: "02:14 AM  ·  ENGINE STILL WARM", tone: "cyan" },
  { a: 3381, b: 3584, text: "ALIEN CODE  ·  1 MIND ON EARTH", tone: "gold" },
  { a: 3584, b: 3714, text: "WOULD YOU TAKE IT?", tone: "cyan" },
];
export const hudAt = (f: number): HudCue => HUD.find((h) => f >= h.a && f < h.b) ?? HUD[HUD.length - 1];

// ---------------- language speech bubbles, shot 7 ----------------
// Replaces the four placards: rounded 2D bubble cards that pop one after another beside the hero's head and stay,
// so the reads stack into a cascade instead of flipping like a board.
// Solved against shot 7's moving lens (scripts/is_frame.mjs projects these same quads): each card clears both
// heads by >15 px of screen area, stays inside u 12..88, keeps its top edge below the HUD band (v >= 24) and
// under the ceiling box (y <= 2.45 + 0.10 half-height vs its 2.58 soffit).
export type Bubble = { c: V3; w: number; h: number; text: string; a: number; b: number };
export const BUBBLES: Bubble[] = [
  { c: [0.14, 1.895, 1.30], w: 0.55, h: 0.20, text: "水色だよ (Japanese)", a: 1002, b: 1086 },
  { c: [0.36, 2.115, 0.95], w: 0.55, h: 0.20, text: "¡Hola! (Spanish)", a: 1026, b: 1086 },
  { c: [0.56, 2.355, 0.60], w: 0.55, h: 0.20, text: "Bonjour! (French)", a: 1050, b: 1086 },
];

// ---------------- shots ----------------
export const SHOTS: ShotDef[] = [
  { id: 1, a: 0, b: 165, light: "dusk", set: "skate", desc: "Right 3/4 portrait: the 10-second tutorial glows in his hand, eyes go cyan" },
  { id: 2, a: 165, b: 270, light: "dusk", set: "skate", desc: "Low wide 3/4: pop, 360 spin, 0.45 m of air, clean landing, jaw drops" },
  { id: 3, a: 270, b: 456, light: "dusk", set: "skate", desc: "Tight from the opposite side: biology backfires, knee bolts, sweat" },
  { id: 4, a: 456, b: 636, light: "hall", set: "chess", desc: "3/4 across the lounge: 15-second Rubik's solve, slam, friend in disbelief" },
  { id: 5, a: 636, b: 855, light: "hall", set: "chess", desc: "Over the shoulder across the board: blindfold fist tips the black king" },
  { id: 6, a: 855, b: 984, light: "hall", set: "chess", desc: "Tight hero close-up: blindfold up, double thumbs, gold stars" },
  { id: 7, a: 984, b: 1086, light: "cabin", set: "cabin", desc: "Aisle 3/4 in the night cabin: grammar book fans, three language bubbles pop" },
  { id: 8, a: 1086, b: 1194, light: "lounge", set: "poker", desc: "Crane down over the felt: shades on, cash rises, opponents slump" },
  // ---- ACT 2 ----
  { id: 9, a: 1194, b: 1297, light: "dusk", set: "skate", desc: "Ground-level from the left: the physics lecture lands, he protests at the sky" },
  { id: 10, a: 1297, b: 1499, light: "dusk", set: "skate", desc: "High crane behind the pad: one hand on the brain, one on the stock thigh" },
  { id: 11, a: 1499, b: 1588, light: "snow", set: "snow", desc: "Wide and low off the kicker: 720 of board spin, an arc of snow, spray on landing" },
  { id: 12, a: 1588, b: 1663, light: "asphalt", set: "hwy", desc: "Skim the tarmac past the front wing: 300 km/h, road scrolling under the wheels" },
  { id: 13, a: 1663, b: 1838, light: "asphalt", set: "hwy", desc: "High from the other flank of the car: the landing jolt and the G-force snap the neck and wrists" },
  { id: 14, a: 1838, b: 2067, light: "mind", set: "brain", desc: "Pull back through the chamber: the neuron core lights, then runs red and sparks" },
  { id: 15, a: 2067, b: 2248, light: "mind", set: "brain", desc: "Tight 3/4 on the face: he realises nothing is ever leaving again" },
  { id: 16, a: 2248, b: 2487, light: "mind", set: "brain", desc: "Wide from the core outward: three memory screens switch on, hands over the ears" },
  { id: 17, a: 2487, b: 2698, light: "dusk", set: "skate", desc: "Low tight over his shoulder: the two friends turn and walk out of the frame" },
  { id: 18, a: 2698, b: 2810, light: "dusk", set: "skate", desc: "3/4 from the bench side: a year of guitar mastered in three minutes, no joy in it" },
  { id: 19, a: 2810, b: 2908, light: "dusk", set: "skate", desc: "Rising wide off the empty plaza: he sits down on the bench and the guitar drops" },
  // ---- ACT 3 ----
  { id: 20, a: 2908, b: 2998, light: "snow", set: "snow", desc: "From below the ridge, the slope behind him: the Class-4 wall traverses the frame" },
  { id: 21, a: 2998, b: 3088, light: "snow", set: "snow", desc: "Straight down from above the mound: shovel strokes, a hand still showing" },
  { id: 22, a: 3088, b: 3257, light: "snow", set: "snow", desc: "Track across the rescue: angle solved, the friend breaks the surface, arms up" },
  { id: 23, a: 3257, b: 3381, light: "night", set: "road", desc: "Wide from the far kerb: an empty car rolls in and parks outside the house" },
  { id: 24, a: 3381, b: 3584, light: "night", set: "road", desc: "Low from inside the beam: the glyph descends into his fist, cyan on the street" },
  { id: 25, a: 3584, b: 3714, light: "night", set: "road", desc: "Slow push into the face: the last look at the lens, one thumb up, the question" },
];

export const shotAt = (f: number): ShotDef => SHOTS.find((s) => f >= s.a && f < s.b) ?? SHOTS[SHOTS.length - 1];
/** hard cuts only — one layer at a time, which is what keeps the pop detector honest */
export const layersAt = (f: number): { id: number; alpha: number }[] => [{ id: shotAt(f).id, alpha: 1 }];

export const GRADE_OF: Record<LightName, string> = {
  dusk: "twilight", hall: "warm", cabin: "warm", lounge: "golden",
  // snow: a bright cold noon is the only preset that holds the daylight band; asphalt runs hot and saturated so the
  // tarmac never reads grey; mind is a windowless chamber, so it takes the sterile clinic ramp and all the colour
  // budget goes into the emissive core; night is the real night grade, warmed a hair by the streetlamp.
  snow: "day", asphalt: "vivid", mind: "clinic", night: "night",
};

// ---------------- set landmarks ----------------
// Shared verbatim by build.ts (which places the meshes), cast.ts (which places the cards) and
// scripts/is_frame.mjs (which projects them and asserts framing). Never duplicate these numbers elsewhere.

/** one standing point per character slot, at the FEET, plus the head height used by the framing check */
// crown = design y 90 (head centre 235 minus radius 145), eyes = design y 235, both lifted by the PIV 975 feet
// pivot at SU 0.00216 m per design unit and scaled by the actor's card scale (ACTOR_SCALE 0.92 for the hero).
export const headY = (scale: number) => (975 - 90) * 0.00216 * scale;    // 1.7587 m at 0.92
export const eyeY = (scale: number) => (975 - 235) * 0.00216 * scale;    // 1.4705 m at 0.92

/** How far a SEATED card's whole figure comes down from standing, in design units, for a cushion whose top surface
 *  is `pan` metres ABOVE THAT CARD'S OWN PIVOT. Standing hip line is design 575 and the pivot is 975, so 400 units
 *  is hip-to-floor: solving 575 + drop = 975 - pan/SU puts the drawn hip exactly on the set's cushion, which is
 *  what makes a seated card read as seated. The card must therefore be authored on the FLOOR under its seat, not
 *  on the seat itself - authored on the cushion, the legs have no canvas left to reach the ground with and the
 *  shoes hang in mid-air. seatM is the same number in metres, which is what scripts/is_frame.mjs subtracts from
 *  headY/eyeY for every slot flagged `seated`, so the crown the gate polices is the crown the audience is shown.
 *  toon.ts `sitP` multiplies this by `sitDrop`, and cast.ts passes it per slot from SEAT_PAN. */
const CARD_SU = 0.00216;   // the card's own metres-per-design-unit; cast.ts exports the same under its own name
export const seatDrop = (pan: number, scale: number) => 400 - pan / (CARD_SU * scale);
export const seatM = (pan: number, scale: number) => seatDrop(pan, scale) * CARD_SU * scale;   // 400*SU*scale - pan
/** cushion height above the floor each seated set is built to. build.ts owns the mesh, this owns the number. */
/** cockpit: the tub floor is the card's pivot, the cushion rises 0.13 m out of it.
 *  bench: SKATE.benchTop - the plank surface - because heroBench is authored on the plaza floor. Spelled as a
 *  literal, not SKATE.benchTop: SEAT_PAN is evaluated above SKATE's own declaration and a const reference here
 *  would throw a temporal-dead-zone error the moment anything imported this file. Keep the two in step by hand. */
export const SEAT_PAN = { cockpit: 0.13, bench: 0.505 };
/** the default drop, kept for any seated draw that does not name a seat: the cockpit at heroScale 0.86 */
export const SIT_DROP = seatDrop(SEAT_PAN.cockpit, 0.86);

/** card scales. The hero and every standing actor take ACTOR_SCALE; the one seated-for-its-whole-life actor (the
 *  cabin passenger) is authored a shade smaller so her card reads as a body in a seat, not a shrunken standing one.
 *  They live here because build.ts, cast.ts, world.ts and the framing checker all have to agree on them. */
export const ACTOR_SCALE = 0.92;
export const PASSENGER_SCALE = 0.88;

// Framing law for a 9:16 lens: a fov-45 vertical opens 2*tan(22.5)*0.5625 = 0.828 m of frame WIDTH per metre of
// distance, so at 3.8 m the frame is only 1.77 m across while one standing card paints 1.19 m of canvas. That
// single number is what the stagings below are built around: keep the PRIMARY subject within 0.4 m of its own view
// axis (that holds the head inside u 15..85), then buy composition room in DEPTH and by pushing secondary cast
// off-axis - and where depth cannot separate three 1.19 m cards (the hall's wide angle, the over-the-shoulder) the
// shot is authored to be answerable for two faces, not three. scripts/is_frame.mjs projects all of it and fails the
// build otherwise.
export const SKATE = {
  // the pad sits 1.55 m in front of the world origin so the lit towers 14..18 m behind read as real distance
  hero: [0.0, 0, 1.55] as V3,
  // ONE onlooker, not two: the brief's block 1 only ever has the red-hoodie skater reacting, and a second card at
  // his depth made every hero portrait either cover a face or slice one off the frame edge. He stands on the top
  // step 2.85 m deeper, where the hero's card is 1.9x the width of his, so a 0.9 m offset in the camera's own
  // screen-right keeps both faces whole in the same 9:16 frame.
  skater: [0.35, 0.25, -1.30] as V3,
  stairs: [0.55, 0, -1.65] as V3,
  ramp: [-2.05, 0, -3.45] as V3,
  /** 1.4 m down the plaza from the ramp. The bench used to sit at z -2.75, i.e. 0.075 m in FRONT of the ramp's own
   *  1.9 m back panel, and shot 19 looks at the seated hero from az -42 straight through that gap: the panel covered
   *  45% of his card and only his crown showed. Nothing else in the plaza is between these two, so the bench moves
   *  and the ramp does not. */
  bench: [-1.95, 0, -1.35] as V3,
  /** build.ts centres a 0.09 m plank at y 0.46, so the surface he actually sits on is 0.505 m - and SEAT_PAN.bench
   *  is that same number, because the drop that puts his hip on it is computed from it. */
  benchTop: 0.505,
  /** authored on the PLAZA FLOOR under the bench, not on the plank: a card pivoted at the cushion has no canvas
   *  left below its own origin for the legs to reach the ground with, and v1's hero floated two shoes in mid-air. */
  heroBench: [-1.74, 0, -1.20] as V3,
  /** block 6's two friends. They stand ON the hero's own depth band (z 1.0-1.1 against his 1.55) so shot 17's low
   *  lens can hold three faces whole, and they leave along x because that is the axis no later skate shot needs. */
  friend: [-1.28, 0, 1.02] as V3,
  friend2: [1.34, 0, 1.14] as V3,
  friendLeave: [-4.60, 0, 1.90] as V3,
  friend2Leave: [4.70, 0, 2.00] as V3,
  lamps: [[-2.95, 0, -0.85], [2.95, 0, -1.3], [-0.35, 0, -5.15]] as V3[],
  /** both flanks of the plaza, never behind the pad. The three skate cameras cover ~50 deg of azimuth, so any tree
   *  within x -3..3 projects across the hero's crown in at least one frame and reads as a hair cap; these four
   *  slots measure zero canopy overlap with either head's crown band across all 77 sampled frames of shots 1-3. */
  trees: [[-6.5, 0, -6.0], [-4.5, 0, -3.0], [5.0, 0, -9.0], [6.5, 0, -4.5]] as V3[],
  /** lit apartment band + a distant downtown. A 9:16 lens at fov 45 is `2*tan(22.5)*depth` = 0.83*depth tall, so a
   *  building only shows its roof (and a strip of violet sky above it) when its height stays under ~0.35*depth.
   *  That is why the near blocks are 2-3 storey walk-ups at 12-16 m and the towers are 12-16 m at 58-72 m: v1's
   *  opening frame was 8-14 m blocks at 14 m, which painted the whole top half brick and left the pill no sky.
   *  They are also spaced 1.5-2.2 m apart instead of shoulder to shoulder, so twilight sky shows BETWEEN them. */
  city: [
    { c: [-15.0, 2.1, -11.6] as V3, w: 4.2, h: 4.2, d: 3.6 },
    { c: [-8.4, 2.4, -13.4] as V3, w: 4.6, h: 4.8, d: 4.0 },
    { c: [-2.0, 2.6, -15.2] as V3, w: 5.2, h: 5.2, d: 4.2 },
    { c: [4.0, 2.4, -14.0] as V3, w: 4.8, h: 4.8, d: 4.0 },
    { c: [10.6, 2.8, -16.0] as V3, w: 5.4, h: 5.6, d: 4.4 },
    { c: [17.2, 2.1, -12.4] as V3, w: 4.0, h: 4.2, d: 3.6 },
    { c: [-20.0, 6.5, -58.0] as V3, w: 9.0, h: 13.0, d: 8.0 },
    { c: [-2.0, 8.0, -72.0] as V3, w: 10.0, h: 16.0, d: 9.0 },
    { c: [16.0, 6.0, -64.0] as V3, w: 8.0, h: 12.0, d: 7.0 },
  ],
};

export const CHESS = {
  /** depth-staged, and pushed screen-left so the near hero's big card and the two small far cards share one frame:
   *  the hero holds the left third, the far pair the right, none of them projected at the same size. */
  hero: [-0.80, 0, 2.45] as V3,
  friend: [-0.90, 0, 1.05] as V3,
  /** 0.45, not 1.20: shot 4 films across the table at azimuth 50 with its axis 0.39 m screen-left of the hero, and
   *  three 1.19 m cards cannot share a 2.6 m frame. At 1.20 the grandmaster's shoulder poked 5% into the right
   *  border as a sliced torso; 1.75 m of depth gap puts his whole silhouette outside the frame in shot 4 while
   *  shot 5 (where his shock IS the beat) keeps him at u 54..86, and shot 6 leaves him behind the lens entirely. */
  gm: [0.55, 0, 0.45] as V3,
  /** the long axis runs near -> far, so the players face each other across the lens instead of beside it */
  tableC: [-0.10, 0.9, 1.72] as V3,
  /** 1.75, not 1.6: the board, cube and clock are world-axis-aligned while the top is canted tableRot, so a
   *  rotated square eats width fast — at 1.6 the board's far corner sits 0.03 m and the cube 0.06 m off the wood. */
  tableSize: [1.75, 1.8] as [number, number],
  tableRot: 0.32,
  /** authored UNDER the Rule B fist: world.ts drags the king onto HERO_FIST from f648, and a 2D billboard card can
   *  only reach 0.42 m along its own right vector, so the board has to live where that fist lands at shot 5's yaw
   *  (-14 deg): fist = hero + right*0.419 - forward*0.08 at the tabletop. */
  board: [-0.36, 0.90, 2.37] as V3,
  king: [-0.36, 0.918, 2.39] as V3,
  clock: [0.55, 0.93, 1.42] as V3,
  cubeRest: [-0.78, 0.9425, 2.26] as V3,
  /** night city on the back wall — this band carries the set's luma now that the banners are gone. Shot 4 films
   *  across the table at azimuth 50, so its view axis exits the wall at x -3.8 with 2.5 m of frame either side;
   *  the band therefore has to run x -9..+5 to leave no void behind any of the three hall cameras. */
  windowBand: { c: [-2.0, 2.02, -1.3] as V3, hw: 7.0, hh: 0.95 },
  pendant: [0.05, 2.28, 1.72] as V3,
};

export const CABIN = {
  hero: [0.55, 0, 1.62] as V3,
  // seated (soles on the footrest, y 0.46) in the window seat on the OPPOSITE side of the aisle, one row ahead.
  // The aisle camera's screen-right is nearly +x, so her 1.0 m of seat pitch lands at u 24 - exactly where her
  // whole silhouette (props reach 0.49 m) stays inside the frame while the hero keeps the right two thirds.
  passenger: [-0.45, 0.46, 0.98] as V3,
  bubbles: BUBBLES,
  ceilStrip: [0.0, 2.6, 0.6] as V3,
  backWall: { c: [0, 1.4, -2.6] as V3, hw: 2.5, hh: 1.45 },
};

export const POKER = {
  /** the crane looks DOWN the table from behind the near pair, so the depth read is vertical, not lateral: the two
   *  opponents sit 1.85 m nearer the lens and their crowns land at v ~45, BELOW the far hero's chin, while the
   *  hero himself holds the upper middle of the frame above the pot. Near/far inversion, no lineup. */
  hero: [0.10, 0, 0.45] as V3,
  oppL: [-0.38, 0, 2.30] as V3,
  oppR: [0.58, 0, 2.25] as V3,
  tableC: [0.10, 0.8, 1.40] as V3,
  tableR: 1.05,
  cashRow: [0.10, 0.815, 1.40] as V3,
  cardRow: [0.10, 0.815, 1.62] as V3,
  snacks: [[-0.62, 0.815, 1.05], [0.78, 0.815, 1.72]] as V3[],
  windowBand: { c: [3.28, 1.8, 1.0] as V3, hw: 1.25, hh: 1.55 },
  /** 2.30, not 1.62: the crane comes down behind the near pair and looks straight along the table, so a low shade
   *  sat between the lens and the far hero and capped him. build.ts derives the cord from this y. */
  lamp: [0.10, 2.30, 1.40] as V3,
};

// ---------------- Act 2/3 landmarks ----------------

/** SNOW — a fog basin with the piste running along x and five ridgelines ringing it, because the four snow cameras
 *  face four different ways: shot 11 looks toward +x, shot 20 back up the face toward +z, shots 21-22 down toward
 *  −x/−z. One upslope wall would have left three of them with empty sky behind the hero. Avalanche geometry lives
 *  up the +z face, where shot 20's camera is aimed. */
export const SNOW = {
  hero: [0.0, 0, 1.6] as V3,
  /** the buried friend is a real card, sunk under the mound: world y of the FEET goes to -0.62 so only the drawn
   *  glove clears the snow. BREAK_AT is the frame the mound is cut away and the card returns to 0. */
  friend: [1.05, 0, 0.55] as V3,
  friendSunk: -0.62,
  mound: [1.05, 0.19, 0.55] as V3,
  /** takeoff and landing share the hero's own z and travel along x, which is the DEPTH axis of shot 11's 72-degree
   *  azimuth. Authored as a z-flight the same parabola slides 1.5 m across the frame and out of the head band. */
  launch: [-1.15, 0.55, 1.6] as V3,
  landPad: [0.90, 0, 1.6] as V3,
  /** one box that traverses the face; world.ts drives z from these two numbers.
   *  avalEndZ is a CLEARANCE, not a framing choice: build.ts hangs teeth and foot-debris up to ~5.4 m downstage of
   *  the box centre, and the slab's 11.5 deg lean swings that field further toward the lens, so an end position of
   *  5.2 parked a 4 m wide drift ball at z -0.9 and y 1.1 — mid-torso — directly in front of SNOW.hero (z 1.6) and
   *  SNOW.friend (z 0.55), which sliced both bodies in half for the last 8 frames of shot 20. 8.8 leaves 0.8 m of
   *  clear air behind the hero's own card plane; scripts/is_snow.mjs proves it on every frame of the shot. */
  avalStartZ: 26.0,
  avalEndZ: 8.8,
  avalY: 2.6,
  avalSize: [40, 5.2, 5.0] as [number, number, number],
  pines: [
    [-6.2, 0.9, 3.2], [-7.6, 1.6, 6.4], [5.4, 1.1, 3.8], [7.2, 1.9, 6.9],
    [-4.4, 2.4, 9.6], [3.4, 2.6, 10.8], [-9.0, 3.1, 12.5], [8.6, 3.4, 13.4],
  ] as V3[],
  /** seven ridgelines ringing the basin, tops from 4.6 to 10 m. They are placed by BEARING, not by looks: a 9:16
   *  lens at fov 46 sees only a ~26 degree azimuth wedge, so the four snow cameras (axis 108 up the piste for shot
   *  11, 348 straight up the avalanche face for 20, 162 over the mound for 21, 220 across the rescue for 22) each
   *  need at least one mass standing inside their own wedge or the shot reads as a figure on a white sheet. The
   *  low ones (4.6, 5.2) exist for the two down-angle shots, whose frames have almost no sky left above a tall
   *  ridge — see SKYLINES. */
  ridges: [
    { c: [2.0, 4.5, 30.0] as V3, w: 32.0, h: 9.0, d: 14.0 },
    { c: [-8.0, 3.5, -28.0] as V3, w: 26.0, h: 7.0, d: 12.0 },
    { c: [30.0, 5.0, -6.0] as V3, w: 24.0, h: 10.0, d: 12.0 },
    { c: [-26.0, 4.0, -14.0] as V3, w: 22.0, h: 8.0, d: 12.0 },
    { c: [16.0, 3.0, 20.0] as V3, w: 20.0, h: 6.0, d: 10.0 },
    /** az 115, 30 m out: the second mass inside shot 11's wedge, so the backflip is measured against a range and
     *  not against one lonely peak. Tall is free here — that lens is tilted UP. */
    { c: [27.2, 4.25, -12.7] as V3, w: 22.0, h: 8.5, d: 11.0 },
    /** az 345: inside shot 20's wedge, aimed up the face the avalanche comes down. Kept at 5.2 m so a roofline
     *  still leaves sky above it under that lens's 11 degree down-tilt. */
    { c: [-7.8, 2.6, 29.0] as V3, w: 26.0, h: 5.2, d: 12.0 },
    /** az 222: the near shoulder of the basin for shot 22's rescue track, 4.6 m so it reads as a snow bank the
     *  two of them stand in rather than a wall that eats the whole top of the frame */
    { c: [-17.4, 2.3, -19.4] as V3, w: 18.0, h: 4.6, d: 9.0 },
  ],
};

/** HIGHWAY — a straight open-wheel car parked on its own 16 m of tarmac. Nothing scrolls in world space except the
 *  painted dashes, which world.ts runs along z at 300 km/h and wraps with a modulo. */
export const HIGHWAY = {
  /** the car body's origin, on the ground plane, at the rear axle */
  car: [0.0, 0, 1.5] as V3,
  /** the hero is authored SEATED in the cockpit: his card's feet pivot sits on the tub floor, 0.30 m up */
  hero: [0.0, 0.30, 1.62] as V3,
  heroScale: 0.86,
  /** the wheel rim he grips: design-space hands, so the 3D wheel and the 2D fists are solved by Rule A (drawn),
   *  not Rule B. Only the cockpit TUB is 3D. */
  wheel: [0.0, 0.62, 1.16] as V3,
  laneW: 3.9,
  stripeZ: 4.0,
  guardL: -3.6,
  guardR: 3.6,
  /** the city he is driving away from: a strip of lit windows low on the horizon, both sides */
  lights: [
    [-13.0, 1.6, -26.0], [-7.5, 2.4, -30.0], [8.0, 1.9, -28.0], [14.0, 2.8, -33.0],
  ] as V3[],
};

/** BRAIN — a windowless chamber with one oversized 3D neuron at the centre of it. The core is the subject the lens
 *  keeps coming back to, so its own position is a framing entry, not just set dressing. */
export const BRAIN = {
  hero: [0.0, 0, 1.4] as V3,
  core: [0.0, 1.90, -2.2] as V3,
  coreR: 1.10,
  /** three memory screens on the back wall, angled in toward the core so a wide lens sees all three at once */
  screens: [
    { c: [-2.15, 2.05, -3.35] as V3, w: 1.55, h: 0.98, rot: 0.52 },
    { c: [0.0, 2.45, -3.95] as V3, w: 1.75, h: 1.12, rot: 0.0 },
    { c: [2.15, 2.00, -3.35] as V3, w: 1.55, h: 0.98, rot: -0.52 },
  ],
  dendriteR: 3.3,
  /** the chamber is a windowless box; the back wall is a COVER entry because the only thing that may be behind the
   *  hero in a room with no windows is more room. 16 x 9 m at z -6 overfills every lens in shots 14-16. */
  wall: { c: [0.0, 3.0, -6.0] as V3, hw: 16.0, hh: 9.0 },
  roomSize: [13.2, 6.0, 13.2] as [number, number, number],
  floorY: 0,
};

/** ROAD — one suburban street at 02:14, a house facade, a streetlamp, the empty car parked at the kerb and a UFO
 *  hovering inside its own beam. The beam column and its pool are the only strong light sources after the lamp. */
export const ROAD = {
  hero: [0.0, 0, 1.9] as V3,
  /** where the car arrives: pulled over at the left kerb, three quarters nose-in to the lens */
  carRest: [-2.35, 0, 0.75] as V3,
  carIn: [-13.5, 0, 3.6] as V3,
  house: [0.6, 0, -4.1] as V3,
  houseSize: [7.4, 5.4, 4.2] as [number, number, number],
  door: [-0.75, 1.05, -1.95] as V3,
  lamp: [2.35, 0, -0.55] as V3,
  ufo: [0.55, 7.4, -0.6] as V3,
  ufoR: 2.15,
  beam: [0.55, 0, -0.6] as V3,
};

// ---------------- KICKS ----------------
export type Kick = { f: number; dur: number; amp: number; freq: number };
export const KICKS: Kick[] = [
  { f: LAND_AT, dur: 11, amp: 0.075, freq: 2.1 },   // board lands on the concrete
  { f: CUBE_SLAM_AT, dur: 10, amp: 0.065, freq: 2.4 }, // solved cube hits the table
  { f: KING_FALL_AT, dur: 11, amp: 0.070, freq: 2.0 }, // 3D king topples
  { f: CASH_SPARK_AT, dur: 12, amp: 0.060, freq: 1.7 }, // first cash bundle locks in
  { f: SNOW_LAND_AT, dur: 12, amp: 0.070, freq: 1.9 }, // he lands the double backflip on the snow
  { f: OVERHEAT_AT, dur: 11, amp: 0.062, freq: 2.6 },  // the core runs red and spits sparks
  { f: RIFF_AT, dur: 10, amp: 0.058, freq: 2.2 },      // the first chord lands clean
  { f: AVAL_HIT_AT, dur: 13, amp: 0.075, freq: 1.6 },  // the wall crosses the ridge line
  { f: BREAK_AT, dur: 12, amp: 0.068, freq: 2.0 },     // his friend breaks the surface
  { f: CAR_STOP_AT, dur: 11, amp: 0.060, freq: 1.8 },  // the empty car parks
  { f: CODE_AT, dur: 12, amp: 0.072, freq: 2.3 },      // the glyph drops into his fist
  { f: FINAL_THUMBS_AT, dur: 10, amp: 0.055, freq: 2.0 }, // the last beat before the question
];

export const kickOffset = (f: number): V3 => {
  let ox = 0, oy = 0, oz = 0;
  for (const k of KICKS) {
    if (f >= k.f && f < k.f + k.dur) {
      const u = (f - k.f) / k.dur;
      const decay = (1 - u) * (1 - u);
      const s = Math.sin((f - k.f) * k.freq) * k.amp * decay;
      ox += s * 0.42; oy += s * 1.0; oz += s * 0.28;
    }
  }
  return [ox, oy, oz];
};

// ---------------- cameras ----------------
// 25 shots, 25 different lenses. scripts/is_frame.mjs measures each lens against its OWN subject and passes a pair
// only when one of four numbers separates them (azimuth >= 25 deg, distance ratio >= 1.4, height >= 0.45 m or pitch
// >= 8 deg), so a future tweak that recreates a repeated front-on angle fails the check instead of the audience.
// Shots 1-8 are authored as raw pos/look; 9-25 are authored as rig() profiles so the numbers below are inputs, not
// outputs. fov stays inside 43..49 the whole time (Hard Rule 5).
export type CamState = { pos: V3; look: V3; fov: number };

type ShotCam = {
  posA: V3; posB: V3; lookA: V3; lookB: V3; fovA: number; fovB: number;
  moveEnd: number; drift: number;
};

/**
 * Camera authoring for shots 9-25. The four numbers scripts/is_frame.mjs measures — azimuth around the subject,
 * horizontal distance, lens height, view pitch — are the INPUTS here, so an authored angle and a measured angle can
 * never disagree, and a profile that collides with another shot's fails the checker the moment it is typed.
 *   az    degrees from +z toward +x, measured AT the subject (0 = camera on the subject's +z side)
 *   d     metres from the subject to the lens, horizontally
 *   h     lens height, world metres
 *   lookY where the view axis crosses the subject's own vertical, world metres
 *   cx,cz the subject's x/z — the rig is built around the figure the shot is answerable for
 * Pitch is derived, never authored: atan((h - lookY) / d).
 */
export type Prof = { az: number; d: number; h: number; lookY: number; cx: number; cz: number };
const d2r = (a: number) => (a * Math.PI) / 180;
export const posOf = (p: Prof): V3 => [p.cx + Math.sin(d2r(p.az)) * p.d, p.h, p.cz + Math.cos(d2r(p.az)) * p.d];
export const lookOf = (p: Prof): V3 => [p.cx, p.lookY, p.cz];
export const rig = (a: Prof, b: Prof, fovA: number, fovB: number, moveEnd: number, drift: number): ShotCam => ({
  posA: posOf(a), posB: posOf(b), lookA: lookOf(a), lookB: lookOf(b), fovA, fovB, moveEnd, drift,
});

const CAM: Record<number, ShotCam> = {
  // 1: 3/4 portrait from the hero's screen right, the lit towers 16 m behind him. Feet on concrete, crown under the HUD.
  1: { posA: [1.15, 1.50, 5.15], posB: [0.95, 1.44, 4.65], lookA: [0.02, 1.22, 1.55], lookB: [0.00, 1.24, 1.52], fovA: 45, fovB: 44, moveEnd: 132, drift: 0.26 },
  // 2: the only ground-level angle in the act, aimed off the hero toward the steps so the jump arc and the
  // skater's dropped jaw both live inside one wide frame.
  2: { posA: [2.62, 0.94, 6.05], posB: [2.95, 0.90, 6.70], lookA: [0.31, 1.22, 0.88], lookB: [0.23, 1.30, 0.68], fovA: 47, fovB: 49, moveEnd: 246, drift: 0.20 },
  // 3: the opposite side of the same pad, lens 0.62 m off the concrete looking UP the legs, so the locked knee and
  // the wincing face share one frame without a full-figure pull-back.
  3: { posA: [-1.55, 0.62, 3.95], posB: [-1.40, 0.66, 3.60], lookA: [0.05, 1.34, 1.60], lookB: [0.10, 1.32, 1.58], fovA: 44, fovB: 43, moveEnd: 384, drift: 0.24 },
  // 4: the widest hall angle, 5.3 m back and 50 degrees round the table, aimed between the near hero and his friend.
  4: { posA: [3.30, 1.62, 5.90], posB: [3.15, 1.56, 5.62], lookA: [-0.39, 1.25, 2.17], lookB: [-0.41, 1.23, 2.14], fovA: 47, fovB: 46, moveEnd: 578, drift: 0.22 },
  // 5: behind and left of the blindfolded hero, down the arm and onto the 3D king on the far edge of the board.
  // The aim sits 0.22 m screen-left of the hero's own axis: that is what keeps his eye column at u 26..30 instead
  // of u 7, so the foreground shoulder reads as a shoulder and not as a head sliced off the frame edge.
  5: { posA: [-1.55, 1.52, 5.55], posB: [-1.40, 1.46, 5.10], lookA: [-0.53, 1.30, 2.50], lookB: [-0.50, 1.26, 2.46], fovA: 45, fovB: 44, moveEnd: 790, drift: 0.20 },
  // 6: tight from the other side of his face — blindfold up, double thumbs, stars. Shoulders alone are 0.35 m of
  // a 0.55 m half-frame at 2.5 m, so the axis has to pass within 0.14 m of his own centre or an arm is sliced.
  6: { posA: [0.85, 1.55, 4.30], posB: [0.70, 1.50, 4.00], lookA: [-0.53, 1.44, 2.56], lookB: [-0.55, 1.42, 2.52], fovA: 44, fovB: 43, moveEnd: 946, drift: 0.16 },
  // 7: down the aisle from the galley end, 5.1 m back so BOTH seats fit widthwise — the hero right of centre with
  // the language cascade beside him, the passenger in the far window seat on the left.
  7: { posA: [1.05, 2.00, 6.60], posB: [0.96, 1.92, 6.28], lookA: [0.30, 1.32, 1.20], lookB: [0.32, 1.34, 1.18], fovA: 46, fovB: 45, moveEnd: 1054, drift: 0.12 },
  // 8: crane behind the near pair, 3.5 m high and 25 degrees down the table, then settle lower on the hero as the
  // cash climbs. The steep pitch is what puts the two foreground crowns BELOW the far hero's chin.
  8: { posA: [0.45, 3.50, 7.20], posB: [0.40, 2.85, 6.35], lookA: [0.10, 0.70, 1.10], lookB: [0.10, 0.90, 1.20], fovA: 48, fovB: 46, moveEnd: 1162, drift: 0.16 },
  // ---- ACT 2 ----
  // 9: the mirror of shot 3 — same pad, same ground-skimming lens, but 48 degrees round the other way, so the
  // protest reads against a different wall of towers than the kickflip did. Past -52 the view axis slips off the
  // city block entirely and the shot is a boy yelling at empty sky.
  9: rig({ az: -48, d: 4.6, h: 0.72, lookY: 1.30, cx: 0, cz: 1.55 }, { az: -44, d: 4.05, h: 0.78, lookY: 1.32, cx: 0, cz: 1.55 }, 48, 47, 1252, 0.18),
  // 10: straight down from behind the pad, the only near-top-down angle left in the skatepark.
  10: rig({ az: 8, d: 4.6, h: 2.85, lookY: 1.30, cx: 0, cz: 1.55 }, { az: 6, d: 4.15, h: 2.72, lookY: 1.34, cx: 0, cz: 1.55 }, 47, 46, 1440, 0.22),
  // 11: 8.4 m back and 45 cm off the snow, aimed ABOVE his crown at the ridge: the whole trick happens in the sky
  // and the peaks give it something to be measured against.
  11: rig({ az: -72, d: 8.4, h: 0.45, lookY: 1.90, cx: 0, cz: 1.6 }, { az: -66, d: 7.5, h: 0.62, lookY: 1.80, cx: 0, cz: 1.6 }, 49, 48, 1566, 0.2),
  // 12: the tarmac itself, 42 cm up and past the front wing — speed reads from the road plane, not from a wide fov.
  12: rig({ az: 38, d: 4.9, h: 0.42, lookY: 1.15, cx: 0, cz: 1.62 }, { az: 34, d: 4.35, h: 0.50, lookY: 1.18, cx: 0, cz: 1.62 }, 47, 46, 1640, 0.25),
  // 13: the opposite flank and 2.25 m up, looking DOWN into the cockpit at the body giving out.
  13: rig({ az: -24, d: 4.2, h: 2.25, lookY: 1.15, cx: 0, cz: 1.62 }, { az: -20, d: 3.85, h: 2.15, lookY: 1.20, cx: 0, cz: 1.62 }, 47, 46, 1800, 0.2),
  // 14: the widest chamber angle, back and above, so the core and the figure in front of it stay one composition.
  14: rig({ az: 14, d: 6.6, h: 2.55, lookY: 1.30, cx: 0, cz: 1.4 }, { az: 11, d: 5.9, h: 2.42, lookY: 1.34, cx: 0, cz: 1.4 }, 46, 45, 2000, 0.25),
  // 15: 2.4 m in, chest-up, the core just off his shoulder — the one shot that is only a face.
  15: rig({ az: -44, d: 2.4, h: 1.60, lookY: 1.48, cx: 0, cz: 1.4 }, { az: -40, d: 2.22, h: 1.56, lookY: 1.46, cx: 0, cz: 1.4 }, 43, 43, 2210, 0.16),
  // 16: pulled back to 7.4 m and 2.6 m high so all three memory screens fit above him.
  16: rig({ az: 58, d: 7.4, h: 2.60, lookY: 1.25, cx: 0, cz: 1.4 }, { az: 54, d: 6.7, h: 2.48, lookY: 1.30, cx: 0, cz: 1.4 }, 48, 47, 2430, 0.24),
  // 17: almost nose-to-nose, 75 degrees round from shot 10: the friends leave through the frame edges he is facing.
  17: rig({ az: -75, d: 2.2, h: 1.60, lookY: 1.42, cx: 0, cz: 1.55 }, { az: -71, d: 2.45, h: 1.55, lookY: 1.40, cx: 0, cz: 1.55 }, 45, 44, 2570, 0.18),
  // 18: from the bench side at hip height, so the guitar sits between the lens and the empty plaza.
  18: rig({ az: 68, d: 3.1, h: 1.45, lookY: 1.25, cx: 0, cz: 1.55 }, { az: 64, d: 2.92, h: 1.42, lookY: 1.27, cx: 0, cz: 1.55 }, 46, 45, 2720, 0.2),
  // 19: rise and pull wide off the bench until the plaza is empty behind him. The lens starts at 1.55 m and nearly
  // level: at 3.00 m / 14 degrees down the two blocks standing in this wedge were sliced by the top edge and the
  // frame read as a wall. Level, the same two roofs sit at v 26 with dusk sky above them and the bench small below.
  19: rig({ az: -42, d: 5.4, h: 1.55, lookY: 1.35, cx: -1.74, cz: -1.2 }, { az: -37, d: 7.4, h: 2.60, lookY: 2.00, cx: -1.74, cz: -1.2 }, 47, 46, 2870, 0.24),
  // ---- ACT 3 ----
  // 20: azimuth 168 — the lens is BELOW the hero on the piste, looking back UP the face, so the avalanche wall
  // travels toward the camera instead of across it.
  // The axis sits 0.35 m toward the friend and 5.6 m back, not on the hero at 4.4: at the old numbers the lens
  // stood only 2.2 m from his card, so his silhouette measured 45% of a frame width and ran 3% off the left border.
  // Measured at the new ones: hero head u 51..73, friend head u 11..41, friend body 9..44, 5.6% of clean air
  // between the two silhouettes, both crowns under the HUD line, the hero's head still 11% of frame height.
  20: rig({ az: 168, d: 5.6, h: 2.20, lookY: 1.35, cx: 0.35, cz: 1.5 }, { az: 172, d: 5.25, h: 2.10, lookY: 1.40, cx: 0.35, cz: 1.5 }, 49, 48, 2968, 0.2),
  // 21: straight down over the mound, 27 degrees, the one angle in the film where the rescue is read as a plan.
  // The lens sits 2.75 m up with its axis crossing the slope at 1.10 m: that pairing is what keeps his crown out
  // of the HUD band (at 2.05 m the head landed at v 21.6 and one pixel of it was under the pill) while the angle
  // stays steep enough to read as a map rather than a medium shot.
  21: rig({ az: -18, d: 3.3, h: 2.75, lookY: 1.10, cx: 0, cz: 1.6 }, { az: -14, d: 3.05, h: 2.55, lookY: 1.05, cx: 0, cz: 1.6 }, 45, 45, 3060, 0.15),
  // 22: track across the slope from the other shoulder as the friend breaks the surface. Three numbers are
  // load-bearing: the rig turns about a point BETWEEN the two of them, not about the hero, because orbiting the hero
  // alone put the friend 1.48 m off the axis - sixty-four percent of a frame width - clean off the right edge; the
  // lens is 3 m up, because at 2.35 m this was the same composition as shot 16 in the memory chamber; and the axis
  // crosses the slope at 1.95 m rather than at their chests, because the 19-degree down-tilt that leaves buried in
  // the snow would stand two snow walls in place of the sky this shot is measured against.
  22: rig({ az: 20, d: 6.6, h: 3.05, lookY: 1.95, cx: 0.40, cz: 1.10 }, { az: 17, d: 6.2, h: 2.90, lookY: 1.85, cx: 0.40, cz: 1.10 }, 46, 45, 3216, 0.2),
  // 23: 7.6 m back down the street at eye level, the house and the arriving car inside one wide frame.
  23: rig({ az: -64, d: 7.6, h: 1.45, lookY: 1.25, cx: 0, cz: 1.9 }, { az: -60, d: 6.9, h: 1.42, lookY: 1.30, cx: 0, cz: 1.9 }, 48, 47, 3350, 0.2),
  // 24: 1 m off the asphalt from inside the beam, aimed slightly UP so the glyph descends into frame. Azimuth 62 and
  // not 52 because at 52 this lens was the same lens as shot 2 two minutes earlier - 22 degrees round, the same
  // height, the same distance - and the film may not show the audience the same composition twice.
  24: rig({ az: 62, d: 4.8, h: 1.02, lookY: 1.55, cx: 0, cz: 1.9 }, { az: 58, d: 4.3, h: 1.00, lookY: 1.58, cx: 0, cz: 1.9 }, 45, 44, 3540, 0.22),
  // 25: the last move in the film: 2.35 m out and 2.1 m high, easing down into his eyes as he asks the question.
  25: rig({ az: -3, d: 2.35, h: 1.90, lookY: 1.30, cx: 0, cz: 1.9 }, { az: -2, d: 2.20, h: 1.86, lookY: 1.32, cx: 0, cz: 1.9 }, 43, 43, 3690, 0.12),
};

export const camAt = (id: number, f: number): CamState => {
  const s = SHOTS[id - 1];
  const c = CAM[id];
  const t = glide(f, s.a, c.moveEnd);
  const drift = pushK(f, c.moveEnd, s.b - 1, c.drift);

  // the drift creeps along the view axis, not along world -z, so it stays a push-in on every shot
  const dirX = c.lookB[0] - c.posB[0], dirY = c.lookB[1] - c.posB[1], dirZ = c.lookB[2] - c.posB[2];
  const L = Math.hypot(dirX, dirY, dirZ) || 1;

  const pos = v3Lerp(c.posA, c.posB, t);
  pos[0] += (dirX / L) * drift;
  pos[1] += (dirY / L) * drift;
  pos[2] += (dirZ / L) * drift;

  const [kx, ky, kz] = kickOffset(f);
  return {
    pos: [pos[0] + kx, pos[1] + ky, pos[2] + kz],
    look: v3Lerp(c.lookA, c.lookB, t),
    fov: lerp(c.fovA, c.fovB, t),
  };
};

/** the camera's angle around its own subject: azimuth (deg, 0 = straight down the +z axis), horizontal distance,
 *  lens height and view pitch. scripts/is_frame.mjs compares these between every pair of shots. */
export const camToSubject = (id: number, f: number, subj: V3) => {
  const c = camAt(id, f);
  const dx = c.pos[0] - subj[0], dy = c.pos[1] - subj[1], dz = c.pos[2] - subj[2];
  const fx = c.look[0] - c.pos[0], fy = c.look[1] - c.pos[1], fz = c.look[2] - c.pos[2];
  const L = Math.hypot(fx, fy, fz) || 1;
  return {
    az: (Math.atan2(dx, dz) * 180) / Math.PI,
    d: Math.hypot(dx, dz),
    h: c.pos[1],
    pitch: (Math.atan2(-fy, Math.hypot(fx, fz)) * 180) / Math.PI,
    fov: c.fov,
    dist: Math.hypot(dx, dy, dz),
  };
};

// ---------------- DOF ----------------
// v1 racked focus off a background landmark, so shot 1 opened with the whole skatepark soft. Every shot now pins
// the lens on its own subject for its entire length — sharp on frame 0, and the only soft pixels are the towers
// behind him. cInf is the blur radius of an object at infinity, in px at 1080x1920, so small values keep the
// background legible; tight shots afford more because there is almost no background in frame.
export type DofSpec = { focus: (f: number) => V3; cInf: number };

// A focus point is either a fixed world coordinate or a function of the frame, and the difference is load-bearing in
// shot 11: the hero is airborne for half the shot, so a static plane puts him 0.7 m off focus at the apex and the
// subject of the film's biggest trick renders soft. Every other shot's subject keeps his feet on the ground, so a
// point at chest height is enough.
export type FocusSpec = { p?: V3; at?: (f: number) => V3; cInf: number };
const FOCUS: Record<number, FocusSpec> = {
  1: { p: [0.0, 1.26, 1.55], cInf: 4.5 },   // hero chest, towers 16 m back
  2: { p: [0.0, 1.32, 1.55], cInf: 5.0 },   // the jump arc, mid-chest
  3: { p: [0.0, 1.16, 1.55], cInf: 7.0 },   // thighs + wincing face, same plane
  4: { p: [-0.80, 1.26, 2.45], cInf: 5.5 }, // the near hero, far pair behind him
  5: { p: [-0.80, 1.28, 2.45], cInf: 6.5 }, // the blindfolded hero himself, king 1.2 m past his fist
  6: { p: [-0.80, 1.44, 2.45], cInf: 8.0 }, // face only
  7: { p: [0.55, 1.28, 1.62], cInf: 5.5 },  // hero at the window seat
  8: { p: [0.10, 1.28, 0.45], cInf: 5.0 },  // the far hero above the pot, near pair soft in the foreground
  // ---- ACT 2 ----
  9: { p: [0.0, 1.26, 1.55], cInf: 5.5 },
  10: { p: [0.0, 1.26, 1.55], cInf: 6.0 },
  11: { at: (f) => { const p = snowAir(f); return [p[0], p[1] + 1.30, p[2]] as V3; }, cInf: 5.0 },
  12: { p: [0.0, 1.06, 1.62], cInf: 6.0 },   // seated head: pivot 0.30 + (975-235-330) x SU x 0.86
  13: { p: [0.0, 1.06, 1.62], cInf: 6.5 },
  14: { p: [0.0, 1.26, 1.40], cInf: 6.0 },
  15: { p: [0.0, 1.42, 1.40], cInf: 8.0 },   // face only, core 3.6 m behind him
  16: { p: [0.0, 1.26, 1.40], cInf: 7.0 },
  17: { p: [0.0, 1.30, 1.55], cInf: 8.0 },
  18: { p: [0.0, 1.26, 1.55], cInf: 6.0 },
  19: { p: [-1.74, 1.18, -1.20], cInf: 5.5 },
  // ---- ACT 3 ----
  20: { p: [0.0, 1.26, 1.60], cInf: 5.0 },
  21: { p: [0.0, 1.26, 1.60], cInf: 6.0 },
  22: { p: [0.0, 1.26, 1.60], cInf: 5.5 },
  23: { p: [0.0, 1.26, 1.90], cInf: 5.0 },
  24: { p: [0.0, 1.30, 1.90], cInf: 6.5 },
  25: { p: [0.0, 1.44, 1.90], cInf: 8.0 },
};

export const dofAt = (f: number): DofSpec => {
  const s = FOCUS[shotAt(f).id];
  return { focus: s.at ? s.at : () => s.p as V3, cInf: s.cInf };
};

// ---------------- shared card paths ----------------
// Three shots deliberately take a card off the ground line, and two of them move it through the frame. The maths
// lives HERE, once, because cast.ts draws the card, world.ts lights it and scripts/is_frame.mjs projects it: any
// one of the three inventing its own copy is exactly how Act 1 shipped a 11 cm disagreement about how high a
// kickflip actually is.
/** the gravity-shaped 0->1->0 arc both jumps ride: 0 at takeoff and landing, 1 at apex */
export const arc = (t: number) => 1 - (2 * clamp01(t) - 1) ** 2;
/** the kickflip parabola (cast.ts multiplies it by AIR_LIFT) */
export const kickflipAir = (f: number) => arc(seg(FLIP_START_AT + 6, LAND_AT, f));
/** shot 11: down the lip, 720 degrees of board, out on the flat — x carries the travel, y is the arc */
export const snowAir = (f: number): V3 => {
  const t = seg(DROP_AT, SNOW_LAND_AT, f);
  const lift = f >= DROP_AT && f <= SNOW_LAND_AT ? arc(t) * AIR_LIFT_SNOW : 0;
  return [
    lerp(SNOW.launch[0], SNOW.landPad[0], t),
    lerp(SNOW.launch[1], SNOW.landPad[1], t) + lift,
    lerp(SNOW.launch[2], SNOW.landPad[2], t),
  ];
};
/** shot 17: a friend turns and walks out of the frame over LEAVE_AT..LEAVE_END_AT */
export const walkOff = (f: number, a: V3, b: V3): V3 => v3Lerp(a, b, glide(f, LEAVE_AT, LEAVE_END_AT));
/** how far under the snow the buried friend's feet pivot is: 0 standing, SNOW.friendSunk once covered, 0 again when
 *  the dig breaks him out at BREAK_AT. */
export const sunkDepth = (f: number) => SNOW.friendSunk * glide(f, BURIED_AT, BURIED_AT + 20) * (1 - glide(f, BREAK_AT, BREAK_AT + 24));
export const buriedFriend = (f: number): V3 => [SNOW.friend[0], sunkDepth(f), SNOW.friend[2]];
/** shots 23-25: the empty car rolls in from off-frame left and parks at the kerb */
export const carRoll = (f: number): V3 => v3Lerp(ROAD.carIn, ROAD.carRest, glide(f, CAR_IN_AT, CAR_STOP_AT));
/** shot 20: the avalanche wall's centre, traversing down the face */
export const avalPos = (f: number): V3 => [0.0, SNOW.avalY, lerp(SNOW.avalStartZ, SNOW.avalEndZ, glide(f, AVAL_AT, AVAL_HIT_AT + 24))];

// ---------------- declarative staging tables ----------------
// What scripts/is_frame.mjs is allowed to know about a shot. Writing this down instead of hardcoding eight branches
// in the checker is what lets a 25-shot film be proven before a pixel renders: the checker walks these rows, so a
// new shot is covered by the same head-band, border-crop, face-occlusion, grounding and skyline laws automatically.
export type SlotDef = {
  n: string;                 // card name, unique inside a shot
  at: V3;                    // feet, world metres (ignored when path is set)
  scale: number;
  primary?: boolean;         // the lens and the focus are built around this card
  required?: boolean;        // the story has to SHOW this face, so a crop or an occlusion is a failure
  ots?: boolean;             // foreground shoulder: the silhouette is authored to run off the border
  held?: boolean;            // painted with something out at the 260-unit prop reach, so it measures 260 wide
  noGround?: boolean;        // airborne or buried: the crown is answerable, the feet line is not
  seated?: number;           // cushion top, metres ABOVE this card's own pivot; the figure drops seatM(pan, scale)
  path?: (f: number) => V3;  // animated feet
  hide?: (f: number) => boolean; // inside 3D geometry on purpose (under a snow mound), so not projected at all
};
export const CAST_SLOTS: Record<number, SlotDef[]> = {
  1: [{ n: "hero", at: SKATE.hero, scale: ACTOR_SCALE, primary: true, required: true },
      { n: "skater", at: SKATE.skater, scale: ACTOR_SCALE }],
  2: [{ n: "hero", at: SKATE.hero, scale: ACTOR_SCALE, primary: true, required: true, held: true, noGround: true,
       path: (f) => [SKATE.hero[0], SKATE.hero[1] + kickflipAir(f) * AIR_LIFT, SKATE.hero[2]] },
      { n: "skater", at: SKATE.skater, scale: ACTOR_SCALE, required: true }],
  3: [{ n: "hero", at: SKATE.hero, scale: ACTOR_SCALE, primary: true, required: true },
      { n: "skater", at: SKATE.skater, scale: ACTOR_SCALE }],
  4: [{ n: "hero", at: CHESS.hero, scale: ACTOR_SCALE, primary: true, required: true, held: true },
      { n: "friend", at: CHESS.friend, scale: ACTOR_SCALE, required: true },
      { n: "grandmaster", at: CHESS.gm, scale: ACTOR_SCALE }],
  5: [{ n: "hero", at: CHESS.hero, scale: ACTOR_SCALE, primary: true, required: true, ots: true },
      { n: "friend", at: CHESS.friend, scale: ACTOR_SCALE },
      { n: "grandmaster", at: CHESS.gm, scale: ACTOR_SCALE, required: true }],
  6: [{ n: "hero", at: CHESS.hero, scale: ACTOR_SCALE, primary: true, required: true },
      { n: "friend", at: CHESS.friend, scale: ACTOR_SCALE },
      { n: "grandmaster", at: CHESS.gm, scale: ACTOR_SCALE }],
  7: [{ n: "hero", at: CABIN.hero, scale: ACTOR_SCALE, primary: true, required: true, held: true },
      { n: "passenger", at: CABIN.passenger, scale: PASSENGER_SCALE, required: true, noGround: true }],
  8: [{ n: "hero", at: POKER.hero, scale: ACTOR_SCALE, primary: true, required: true },
      { n: "oppL", at: POKER.oppL, scale: ACTOR_SCALE, required: true },
      { n: "oppR", at: POKER.oppR, scale: ACTOR_SCALE, required: true }],
  9: [{ n: "hero", at: SKATE.hero, scale: ACTOR_SCALE, primary: true, required: true },
      { n: "skater", at: SKATE.skater, scale: ACTOR_SCALE }],
  10: [{ n: "hero", at: SKATE.hero, scale: ACTOR_SCALE, primary: true, required: true },
       { n: "skater", at: SKATE.skater, scale: ACTOR_SCALE }],
  11: [{ n: "hero", at: SNOW.hero, scale: ACTOR_SCALE, primary: true, required: true, held: true, noGround: true,
         path: snowAir }],
  // 12/13: SEATED in the tub. noGround stays because the drawn lower legs disappear behind the 3D dash, but the
  // crown is now seatM lower than a standing card, so the gate polices the crown he is actually shown.
  12: [{ n: "hero", at: HIGHWAY.hero, scale: HIGHWAY.heroScale, primary: true, required: true, noGround: true,
        seated: SEAT_PAN.cockpit }],
  13: [{ n: "hero", at: HIGHWAY.hero, scale: HIGHWAY.heroScale, primary: true, required: true, noGround: true,
        seated: SEAT_PAN.cockpit }],
  14: [{ n: "hero", at: BRAIN.hero, scale: ACTOR_SCALE, primary: true, required: true }],
  15: [{ n: "hero", at: BRAIN.hero, scale: ACTOR_SCALE, primary: true, required: true }],
  16: [{ n: "hero", at: BRAIN.hero, scale: ACTOR_SCALE, primary: true, required: true }],
  17: [{ n: "hero", at: SKATE.hero, scale: ACTOR_SCALE, primary: true, required: true },
       { n: "friend", at: SKATE.friend, scale: ACTOR_SCALE, path: (f) => walkOff(f, SKATE.friend, SKATE.friendLeave) },
       { n: "friend2", at: SKATE.friend2, scale: ACTOR_SCALE, path: (f) => walkOff(f, SKATE.friend2, SKATE.friend2Leave) }],
  18: [{ n: "hero", at: SKATE.hero, scale: ACTOR_SCALE, primary: true, required: true, held: true }],
  19: [{ n: "hero", at: SKATE.heroBench, scale: ACTOR_SCALE, primary: true, required: true, held: true,
        seated: SEAT_PAN.bench }],
  20: [{ n: "hero", at: SNOW.hero, scale: ACTOR_SCALE, primary: true, required: true },
       // required, not dressing: he is the one the wall buries, so his face has to be whole in the frame that
       // establishes it. Without the flag is_frame only prints a note for a card that leaves the frame.
       { n: "friend", at: SNOW.friend, scale: ACTOR_SCALE, required: true, hide: (f) => f >= BURIED_AT }],
  21: [{ n: "hero", at: SNOW.hero, scale: ACTOR_SCALE, primary: true, required: true },
       { n: "friend", at: SNOW.friend, scale: ACTOR_SCALE, path: buriedFriend, hide: () => true }],
  22: [{ n: "hero", at: SNOW.hero, scale: ACTOR_SCALE, primary: true, required: true },
       { n: "friend", at: SNOW.friend, scale: ACTOR_SCALE, path: buriedFriend, hide: (f) => f < BREAK_AT, required: true }],
  23: [{ n: "hero", at: ROAD.hero, scale: ACTOR_SCALE, primary: true, required: true }],
  24: [{ n: "hero", at: ROAD.hero, scale: ACTOR_SCALE, primary: true, required: true, held: true }],
  25: [{ n: "hero", at: ROAD.hero, scale: ACTOR_SCALE, primary: true, required: true }],
};

export type QuadDef = {
  n: string; kind: "PROP" | "COVER" | "BG";   // PROP: inside 12..88. COVER: part of the plate union. BG: reported only.
  c?: V3; hw: number; hh: number;
  /** which world plane the plate lies in: "z" (default) is a wall facing the lens, "x" a flank wall, "y" a floor or
   *  ceiling. Without it the checker can only model rooms whose back wall is what the camera sees, and a crane lens
   *  looking 25 degrees DOWN is mostly seeing a floor. */
  axis?: "x" | "y" | "z";
  live?: (f: number) => V3;        // animated centre (the wall, the arriving car)
  window?: [number, number];       // only answerable while it exists on screen
  /** a prop the audience reads because a 2D hand holds it (Rule A: toon.ts paints it). Its position is a design
   *  point on `slot`'s card, so the checker solves the same billboard transform world.ts uses instead of trusting
   *  a world coordinate that would drift the moment the camera moves. */
  slot?: string; hand?: [number, number];
};
export const PROP_QUADS: Record<number, QuadDef[]> = {
  4: [{ n: "cube", kind: "PROP", c: [CHESS.cubeRest[0], CHESS.cubeRest[1], CHESS.cubeRest[2]], hw: 0.12, hh: 0.12 },
      { n: "windowBand", kind: "COVER", c: CHESS.windowBand.c, hw: CHESS.windowBand.hw, hh: CHESS.windowBand.hh }],
  5: [{ n: "board", kind: "PROP", c: [CHESS.board[0], CHESS.board[1] + 0.02, CHESS.board[2]], hw: 0.30, hh: 0.02 },
      { n: "windowBand", kind: "COVER", c: CHESS.windowBand.c, hw: CHESS.windowBand.hw, hh: CHESS.windowBand.hh }],
  6: [{ n: "windowBand", kind: "COVER", c: CHESS.windowBand.c, hw: CHESS.windowBand.hw, hh: CHESS.windowBand.hh }],
  7: [...BUBBLES.map((b, i) => ({ n: `bubble${i}`, kind: "PROP" as const, c: b.c, hw: b.w / 2, hh: b.h / 2, window: [b.a, b.b] as [number, number] })),
      { n: "backWall", kind: "COVER", c: CABIN.backWall.c, hw: CABIN.backWall.hw, hh: CABIN.backWall.hh }],
  8: [{ n: "pot", kind: "PROP", c: [POKER.cashRow[0], POKER.cashRow[1] + 0.22, POKER.cashRow[2]], hw: 0.42, hh: 0.22 },
      { n: "windowBand", kind: "COVER", c: POKER.windowBand.c, hw: POKER.windowBand.hw, hh: POKER.windowBand.hh }],
  11: [{ n: "kicker", kind: "PROP", c: [SNOW.launch[0], SNOW.launch[1] / 2, SNOW.launch[2]], hw: 0.9, hh: SNOW.launch[1] / 2 }],
  12: [{ n: "car", kind: "PROP", c: [HIGHWAY.car[0], 0.52, HIGHWAY.car[2]], hw: 0.95, hh: 0.52 }],
  13: [{ n: "car", kind: "PROP", c: [HIGHWAY.car[0], 0.52, HIGHWAY.car[2]], hw: 0.95, hh: 0.52 }],
  14: [{ n: "core", kind: "PROP", c: BRAIN.core, hw: BRAIN.coreR, hh: BRAIN.coreR },
       { n: "backWall", kind: "COVER", c: BRAIN.wall.c, hw: BRAIN.wall.hw, hh: BRAIN.wall.hh }],
  15: [{ n: "core", kind: "PROP", c: BRAIN.core, hw: BRAIN.coreR, hh: BRAIN.coreR }],
  16: [{ n: "core", kind: "PROP", c: BRAIN.core, hw: BRAIN.coreR, hh: BRAIN.coreR },
       ...BRAIN.screens.map((s, i) => ({ n: `screen${i}`, kind: "PROP" as const, c: s.c, hw: s.w / 2, hh: s.h / 2, window: [LOOP_AT + i * 62, 2487] as [number, number] })),
       { n: "backWall", kind: "COVER", c: BRAIN.wall.c, hw: BRAIN.wall.hw, hh: BRAIN.wall.hh }],
  20: [{ n: "wall", kind: "COVER", c: SNOW.ridges[0].c, hw: 40, hh: SNOW.avalY + SNOW.avalSize[1] / 2, live: avalPos, window: [AVAL_AT, 2998] }],
  21: [{ n: "mound", kind: "PROP", c: [SNOW.mound[0], SNOW.mound[1], SNOW.mound[2]], hw: 0.85, hh: 0.34 }],
  22: [{ n: "mound", kind: "BG", c: [SNOW.mound[0], 0.12, SNOW.mound[2]], hw: 0.85, hh: 0.24, window: [3088, BREAK_AT + 12] }],
  23: [{ n: "car", kind: "PROP", c: ROAD.carRest, hw: 1.05, hh: 0.75, live: carRoll, window: [CAR_STOP_AT, 3380] },
       { n: "house", kind: "COVER", c: [ROAD.house[0], ROAD.houseSize[1] / 2, ROAD.house[2]], hw: ROAD.houseSize[0] / 2, hh: ROAD.houseSize[1] / 2 }],
  24: [{ n: "code", kind: "PROP", slot: "hero", hand: [452, 512], hw: 0.16, hh: 0.20, window: [CODE_AT, CODE_END_AT] },
       { n: "ufo", kind: "BG", c: ROAD.ufo, hw: ROAD.ufoR, hh: 0.42 },
       { n: "house", kind: "COVER", c: [ROAD.house[0], ROAD.houseSize[1] / 2, ROAD.house[2]], hw: ROAD.houseSize[0] / 2, hh: ROAD.houseSize[1] / 2 }],
  25: [{ n: "ufo", kind: "BG", c: ROAD.ufo, hw: ROAD.ufoR, hh: 0.42 }],
};

/** The four sets that stand under open sky. world.ts wraps every scene in a 900 m gradient dome coloured from
 *  LIGHTS[name].sky, so above these sets' horizon there is always something painted and the hole test has nothing
 *  to find — the SKYLINES law is what proves an outdoor frame is not empty above the cast. The four interiors are
 *  deliberately NOT on this list: a hole in the chess lounge does not show the sky, it shows exactly that dome,
 *  which is the failure the hole test exists to catch. */
export const SKY_SETS = ["skate", "snow", "hwy", "road"] as const;

/** The big planes build.ts closes each INTERIOR room with, as the frame checker's model of them. One plate can no
 *  more fill a 9:16 frame than one wall can close a room, so COVER is judged as a UNION per shot: the shell below,
 *  plus any animated COVER row in PROP_QUADS (the window bands, the back walls). Numbers are copied from the
 *  matching `root.add(plane(...))` calls in build.ts and every one of them is a mirror, not a wish — if a set's
 *  shell changes, this table is the file that has to be told. Outdoor sets carry no entry: their ground plate can
 *  never project up to the horizon, so listing it would only make the hole test cry void on a lit sky. */
export const COVER_SHELLS: Record<string, readonly QuadDef[]> = {
  chess: [
    { n: "floor", kind: "COVER", axis: "y", c: [0, 0, 2.2], hw: 10, hh: 10 },
    { n: "wallBack", kind: "COVER", axis: "z", c: [0, 2.35, -1.42], hw: 10, hh: 2.35 },
    { n: "wallL", kind: "COVER", axis: "x", c: [-4.6, 2.35, 2.4], hw: 7.5, hh: 2.35 },
    { n: "wallR", kind: "COVER", axis: "x", c: [4.6, 2.35, 2.4], hw: 7.5, hh: 2.35 },
    { n: "ceiling", kind: "COVER", axis: "y", c: [0, 4.6, 2.4], hw: 4.7, hh: 7.5 },
  ],
  cabin: [
    { n: "floor", kind: "COVER", axis: "y", c: [0, 0, 3.0], hw: 2.5, hh: 6.8 },
    { n: "port", kind: "COVER", axis: "x", c: [-1.62, 1.35, 3.0], hw: 6.8, hh: 1.45 },
    { n: "stbd", kind: "COVER", axis: "x", c: [1.62, 1.35, 3.0], hw: 6.8, hh: 1.45 },
    { n: "ceiling", kind: "COVER", axis: "y", c: [0, 2.72, 3.0], hw: 1.7, hh: 6.8 },
  ],
  poker: [
    { n: "floor", kind: "COVER", axis: "y", c: [0.1, 0, 1.5], hw: 7, hh: 9 },
    { n: "wallBack", kind: "COVER", axis: "z", c: [0.1, 2.0, -3.5], hw: 4.1, hh: 2 },
    { n: "wallL", kind: "COVER", axis: "x", c: [-3.24, 2.0, 1.5], hw: 9, hh: 2 },
    { n: "wallR", kind: "COVER", axis: "x", c: [3.44, 2.0, 1.5], hw: 9, hh: 2 },
    { n: "ceiling", kind: "COVER", axis: "y", c: [0.1, 4.0, 1.5], hw: 3.4, hh: 9 },
  ],
  // the chamber keeps its +z face open on purpose (a wall there would stand between the lens and the core), so the
  // shell is floor, ceiling and two flanks; BRAIN.wall in PROP_QUADS is the back face.
  brain: [
    { n: "floor", kind: "COVER", axis: "y", c: [0, BRAIN.floorY, 1.6], hw: 6.6, hh: 6.6 },
    { n: "ceiling", kind: "COVER", axis: "y", c: [0, BRAIN.roomSize[1], 1.6], hw: 6.6, hh: 6.6 },
    { n: "wallL", kind: "COVER", axis: "x", c: [-BRAIN.roomSize[0] / 2, 3, 1.6], hw: 6.6, hh: 3 },
    { n: "wallR", kind: "COVER", axis: "x", c: [BRAIN.roomSize[0] / 2, 3, 1.6], hw: 6.6, hh: 3 },
    { n: "wallBack", kind: "COVER", axis: "z", c: [0, 3, 1.6 - 6.6], hw: 6.6, hh: 3 },
  ],
};

/** Per-shot skyline law. `blocks` are the set's own buildings, width included, because scripts/is_frame.mjs samples
 *  each roof ACROSS that width: a 9:16 lens at fov 45 sees only ~27 degrees of azimuth, so a 32 m ridge 30 m back is
 *  fully in shot even when its centre sits outside the frame, and a centre-only measurement would call it empty.
 *  Then three numbers say "a place is in shot and the top of the frame is not a wall": `minInside` rooflines must
 *  reach the frame at all, `minSky` must keep a sky strip above them, and no more than `maxCropped` may be sliced by
 *  the top edge. A steep down-angle (shot 10's crane) legitimately has no sky in frame and says so. */
export type SkyPolicy = {
  blocks: readonly { c: V3; w: number; h: number; d: number }[];
  minInside: number; minSky: number; maxCropped: number;
};
export const SKYLINES: Record<number, SkyPolicy> = {
  1: { blocks: SKATE.city, minInside: 2, minSky: 2, maxCropped: 1 },
  2: { blocks: SKATE.city, minInside: 2, minSky: 2, maxCropped: 1 },
  3: { blocks: SKATE.city, minInside: 2, minSky: 2, maxCropped: 1 },
  // azimuth -48, not -60: the city is a wall along -z, and a lens 60 degrees round the pad aims its 26-degree wedge
  // at empty sky past the block's left edge. At -48 the axis crosses the two blocks nearest +x.
  9: { blocks: SKATE.city, minInside: 2, minSky: 2, maxCropped: 1 },
  // the near-top-down crane: its frame top is 5 degrees above the horizon, so the plaza's enclosing facades are
  // allowed to fill it. What is NOT allowed is zero rooflines, which would mean the pad floats in a void.
  10: { blocks: SKATE.city, minInside: 2, minSky: 0, maxCropped: 5 },
  // shot 11 tilts UP at the flip, so a full sky strip is free: two ranges, both with room above them.
  11: { blocks: SNOW.ridges, minInside: 2, minSky: 2, maxCropped: 1 },
  // 19 is the dusk wide that closes the pad: the lens is nearly level at hip height, which is what puts the two
  // blocks standing in its wedge at v 26 with sky over their roofs instead of sliced by the top edge.
  19: { blocks: SKATE.city, minInside: 2, minSky: 2, maxCropped: 1 },
  // 20 looks up the avalanche face and 22 across the top of the basin: one low ridge may keep the thin sky strip
  // those 9-11 degree down-angles leave above the horizon, and two of the eight masses are allowed to be cut.
  20: { blocks: SNOW.ridges, minInside: 2, minSky: 1, maxCropped: 2 },
  22: { blocks: SNOW.ridges, minInside: 2, minSky: 1, maxCropped: 2 },
  // Two dusk shots are deliberately NOT in this table. Shot 18 is a waist-up 3/4 at azimuth 68, looking across the
  // OPEN side of the pad: the city wall sits 35 degrees outside its 26-degree wedge, so its background is sky over
  // concrete, which is what a portrait wants. Shot 21 is the plan view, and the geometry is not a matter of taste:
  // 26.6 degrees down from 2.75 m puts the top edge of the frame 4 degrees BELOW the horizon, so no ridge in the
  // basin can project into it at any azimuth. That frame is answered by the snowfield, which the BODY and grounding
  // laws already hold to the plate.
};

/** shots authored chest-up: the silhouette is MEANT to run off the bottom edge, so only the head column is
 *  answerable there. Shot 3 (knees), 6 and 15 (faces), 17 and 18 (waist-up on the pad), 25 (the last look). */
export const TIGHT_SHOTS: Record<number, boolean> = { 3: true, 6: true, 15: true, 17: true, 18: true, 25: true };
