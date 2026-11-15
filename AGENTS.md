# Animation agent starting point

For animation work, read `ANIMATION_STYLE_HANDOFF.md` first, then
`animated-3d-story-video/SKILL.md` and its shared cel contract. Blender work
also uses `BLENDER_SKILL.md` and the relevant production recipes. These guides
describe the house style and contain the current acceptance criteria.

Use the user's current story, assets, backend, text preferences and authorized
render stage. Do not resume a previous production merely because its source
or a launcher exists. Default to no subtitles unless requested. A zero-text
brief also excludes HUD and baked scene lettering.

Remotion shorts reuse `src/engine/`; Blender examples and reusable geometry,
card and ink helpers are mapped in the production recipes. Do not blindly
copy an old project's timings, absolute paths or render settings.

The repository excludes voice tracks, Blender binaries, private references
and renders. Read the README setup instructions and supply the current
project's inputs. A missing local video is not evidence of reviewed motion.
Use the provided scripts only for the currently authorized work.

Before rendering, inspect the calibration and contact extremes. Numerical
grip checks complement visible finger/surface contact. Preserve versioned
sources and actual output resolution; respect the shared GPU lock. On a
stop/partial-delivery request, stop the owned job and deliver its validated
completed prefix with matching audio. Do not silently restart afterward.
