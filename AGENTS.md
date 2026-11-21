# Default engine for all new animated Shorts

Use the Rick's Clips Blender workflow by default, regardless of which agent is connected.
Before writing scene code, read [RICKS_STYLE_SKILL.md v6](RICKS_STYLE_SKILL.md), inspect
and import [scripts/ricks_v2_kit.py](scripts/ricks_v2_kit.py), and follow the runnable
[starter template](scripts/templates/ricks_short_template.py).
An explicitly requested renderer or archived look takes precedence for that task.

**Legacy / archived for new Shorts**

- [ANIMATION_STYLE_HANDOFF.md](ANIMATION_STYLE_HANDOFF.md) and the older
  [animation skill](animated-3d-story-video/SKILL.md) describe prior workflows.
- [BLENDER_SKILL.md](BLENDER_SKILL.md) contains archived V13 lookdev.
- [cel-studio-contract.md](animated-3d-story-video/references/cel-studio-contract.md)
  and the old visual recipes in [SHORTS_PIPELINE.md](scripts/SHORTS_PIPELINE.md)
  contain archived flat-card and lighting rules.
- [scripts/ricks_lookdev.py](scripts/ricks_lookdev.py) is a legacy dependency of the
  shared kit. New scenes enter through `ricks_v2_kit.py`.

Carry forward only the RTX 3050 hardware, GPU lock, and QA gates from those
references. V13 shaders, sculpted 3D sleeves, flat-card defaults, and static-hold
rules require explicit user direction on a new Short.

## Active local handoff

For `gold_mine_salting_10s` / `gold_mine_salting_v2`, read `HANDOFF_GOLD_MINE_SALTING_V2.md` first. The user stopped production on 2026-11-17 to switch accounts; the saved chat, exact briefs, source checkpoints and remaining gates are linked there. Resume only when the user asks to continue; no native V2 final has been rendered.

Use the user's current story, assets, backend, text preferences and authorized
render stage. Do not resume a previous production merely because its source
or a launcher exists. Default to no subtitles unless requested. A zero-text
brief also excludes HUD and baked scene lettering.

When Remotion is explicitly requested, reuse `src/engine/`. Give every new
production its own timing, input paths, and render settings from the current brief.

The repository excludes voice tracks, Blender binaries, private references
and renders. Read the README setup instructions and supply the current
project's inputs. A missing local video is not evidence of reviewed motion.
Use the provided scripts only for the currently authorized work.

Before rendering, inspect the calibration and contact extremes. Numerical
grip checks complement visible finger/surface contact. Preserve versioned
sources and actual output resolution; respect the shared GPU lock. On a
stop/partial-delivery request, stop the owned job and deliver its validated
completed prefix with matching audio. Do not silently restart afterward.
