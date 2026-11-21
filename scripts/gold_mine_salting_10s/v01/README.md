# Gold mine salting — original V01

Inputs: supplied English MP3 and 360×640 reference clip in Downloads; V13 house examples. Exact narration decoded length 10.0078125 seconds. User chose to keep the recording, which ends at “called,” and use a visual wink payoff. No replacement speech, speed changes or subtitles. Timeline is 301 frames at 30 fps (10.033 seconds), 1080×1920.

| Frames, one-based | Actual audio cue | Visible action and coverage | Contacts |
|---|---|---|---|
| 1–45 | loaded / shotgun / gold | Miner beneath practical overhead cone; insert gold shell, close break action, raise gun | Grounded boots, left shell grip then forend, right trigger grip |
| 46–75 | fired it / into | Barrel-side golden blast, visible recoil and streak to rear wall | Gun hierarchy and both hand targets remain attached |
| 76–110 | walls of the mine | Tight impact and candle insert, rock debris, thin smoke, persistent embedded gold | Gold deposits remain in cracks |
| 111–270 | Buddy watches, then question at 6.68–8.94 s | Seated Buddy watches strike, small mug lift, turns toward camera, free-hand skeptical gesture, real-envelope mouth animation | Pelvis on stump, boots on dirt, hand wraps mug handle |
| 271–301 | You see, it's called… | Low-angle Miner, shotgun over shoulder, shell raised near chest, one-eye wink | Trigger grip and shell surface grip |

All geometry and procedural surfaces are original. No downloaded assets or unknown licenses. Shading, world, optics, scene settings, hull-width calculation and shadow roles use `scripts/ricks_lookdev.py`. Resource/camera/native performance use `shorts_preflight.py`; calibration and final QA use the shared tools. The enclosed tunnel's practical fixtures motivate the warm keys and cool depth fill. The shared Sun rig is retained at reduced intensity to suit the interior.

`prepare.py` writes preserved narration, original quiet plucked underscore, synthesized foley, envelope and story manifest. `launch.py` owns the shared exclusive GPU lock for each background Blender stage, waits for another owner, and does not restart a bridge or interrupt other work. `build.py` starts from factory data in this new folder; it never loads approved productions.

The saved blend packs the mix, shared look module, geometry helpers, audio envelope and runtime. After reopening, run packed `START_HERE.py` once to activate deterministic timeline evaluation. The render worker does this explicitly and aborts on callback errors. Direct seeking is checked against chronological evaluation. Rendered frames are tied to source/audio hashes and native dimensions.

Final evidence and review results are recorded beside the output, under `renders/gold_mine_salting_10s/v01/`.
