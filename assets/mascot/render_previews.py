"""Modal GPU Showcase & Proof Renderer for the Official Mascot Asset Package.

Generates all 4 deliverables in `assets/mascot/previews/` using Blender 4.2 LTS
(`BLENDER_EEVEE_NEXT`, 32 samples, `use_dof=False`, RT off):
  1. `hero_3_reference_poses.png`  (3240 x 1920 — three 1080x1920 reference scenes)
  2. `turnaround_4views.png`       (3240 x 1920 — Front, 3/4 Hero, 90° Side, Back)
  3. `expression_grid_18.png`      (3240 x 1920 — 12 expressions + 6 visemes on 3D head)
  4. `mascot_demo_reel_1080p.mp4`  (1080 x 1920, 30 fps, 450 frames = 15.0 s, H.264 CRF 18)

Modal GPU invocation examples (never run local PC Blender):
  modal run scripts/modal_blender.py --mode run --project assets/mascot \\
      --script assets/mascot/render_previews.py --runner blender \\
      --script-args "--stage proofs" --overwrite

  modal run scripts/modal_blender.py --mode run --project assets/mascot \\
      --script assets/mascot/render_previews.py --runner blender \\
      --script-args "--stage reel --frame-start 1 --frame-end 225" \\
      --download-frames --no-encode-frames --overwrite
"""
from __future__ import annotations

import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile

ROOT = next(p for p in Path(__file__).resolve().parents if (p / "scripts/ricks_v2_kit.py").is_file())
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
if str(ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(ROOT / "scripts"))

PREVIEWS_DIR = ROOT / "assets" / "mascot" / "previews"
SHOWCASE_WORK_DIR = ROOT / "renders" / "mascot_showcase"
SAMPLES = 32
FPS = 30
REEL_END = 450


# --------------------------------------------------------------------------- Typography & Pillow Helpers
def _load_font(size: int, bold: bool = True):
    from PIL import ImageFont

    candidates = []
    try:
        import bpy
        res = Path(bpy.utils.resource_path("LOCAL")) / "datafiles" / "fonts"
        candidates.extend([
            res / "Inter.woff2",
            res / "DejaVuSans.ttf",
            res / "droidsans.ttf",
            res / "bmonofont-i18n.ttf",
        ])
    except Exception:
        pass
    for bfont_dir in (Path("/opt/blender42/4.2/datafiles/fonts"),):
        if bfont_dir.is_dir():
            candidates.extend([
                bfont_dir / "Inter.woff2",
                bfont_dir / "DejaVuSans.ttf",
                bfont_dir / "droidsans.ttf",
                bfont_dir / "bmonofont-i18n.ttf",
            ])
    candidates.extend([
        Path("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"),
        Path("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf"),
        Path("C:/Windows/Fonts/segoeui.ttf"),
        Path("C:/Windows/Fonts/arialbd.ttf" if bold else "C:/Windows/Fonts/arial.ttf"),
    ])
    for path in candidates:
        if path.is_file():
            try:
                return ImageFont.truetype(str(path), size=size)
            except Exception:
                continue
    return ImageFont.load_default()


def _draw_pill_label(draw, center_x: int, y_top: int, text: str, font, *,
                     bg=(20, 16, 22, 232), border=(255, 210, 31, 255), fg=(255, 253, 251, 255),
                     pad_x: int = 22, pad_y: int = 10, radius: int = 16, border_w: int = 2):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    w, h = tw + pad_x * 2, th + pad_y * 2
    x0 = int(center_x - w // 2)
    y0 = int(y_top)
    draw.rounded_rectangle([x0, y0, x0 + w, y0 + h], radius=radius, fill=bg, outline=border, width=border_w)
    draw.text((x0 + pad_x - bbox[0], y0 + pad_y - bbox[1]), text, font=font, fill=fg)


# --------------------------------------------------------------------------- Core Blender Scene Helpers
def _reset_eevee_scene(bpy, kit, *, width: int, height: int, frame_end: int = 60,
                       world_color: str = "#1B2238", world_strength: float = 0.85,
                       cinema_grade: bool = True, lens: float = 26.0):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    kit.configure_ricks_scene(scene, width=width, height=height, fps=FPS, frame_end=frame_end, samples=SAMPLES)
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = SAMPLES
    scene.eevee.use_raytracing = False
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "AgX"
    scene.view_settings.look = "AgX - Medium High Contrast"

    world = bpy.data.worlds.new("ShowcaseWorld")
    world.use_nodes = True
    bg = world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = kit.look.rgba(world_color)
    bg.inputs["Strength"].default_value = world_strength
    scene.world = world

    col = scene.collection
    bpy.ops.object.camera_add(location=(0.0, -2.4, 0.85))
    camera = scene.camera = bpy.context.object
    kit.setup_ricks_camera(camera, lens=lens, fstop=4.0, clip_end=140.0)
    if cinema_grade:
        kit.setup_ricks_compositor(scene, camera=camera, cinema_grade=True)
    camera.data.dof.use_dof = False
    return scene, col, camera


def _enforce_render_contract(scene, camera):
    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.eevee.taa_render_samples = SAMPLES
    scene.eevee.use_raytracing = False
    scene.render.resolution_percentage = 100
    scene.render.pixel_aspect_x = 1.0
    scene.render.pixel_aspect_y = 1.0
    scene.render.fps = FPS
    scene.render.fps_base = 1.0
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    camera.data.dof.use_dof = False


def _add_box(bpy, kit, col, name: str, loc, size, mat, *, rot=(0.0, 0.0, 0.0),
             ink: bool = False, ink_thickness: float = 0.005, shadow: bool = True):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = kit.put(bpy.context.object, col, mat=mat)
    obj.name = name
    obj.scale = size
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.visible_shadow = shadow
    if ink:
        kit.apply_prop_ink(obj, col, thickness=ink_thickness)
    return obj


def _add_sun(bpy, kit, col, name: str, loc, target, color: str, energy: float = 1.6, angle_deg: float = 3.5):
    data = bpy.data.lights.new(name, "SUN")
    data.color = kit.look.rgba(color)[:3]
    data.energy = energy
    data.angle = math.radians(angle_deg)
    data.use_shadow = True
    data.use_shadow_jitter = False
    obj = kit.put(bpy.data.objects.new(name, data), col)
    obj.location = loc
    kit.aim(obj, target)
    return obj


def _set_drawn_light_if_present(hero, direction):
    """Align any directional toon/drawn light empty on the Mascot rig if exposed."""
    from mathutils import Vector
    d = Vector(direction).normalized()
    rot = d.to_track_quat("Z", "Y").to_euler()
    for attr in ("light_empty", "drawn_light", "shade_light"):
        light_obj = getattr(hero, attr, None)
        if light_obj is not None and hasattr(light_obj, "rotation_euler"):
            light_obj.rotation_euler = rot


def _build_hero_star_prop(bpy, kit, col, loc=(0.0, 0.0, 0.0)):
    """Build a colorful 3D Golden Star Gem Trophy prop for `pickup_and_present`."""
    root = kit.empty("HeroProp | GoldenStar", col, loc=loc)
    gold = kit.surface("Prop | Gleaming Gold", "#FFD21F", rough=0.32, metal=0.25, glow=0.18)
    coral = kit.surface("Prop | Ruby Core", "#FF3B6B", rough=0.28, metal=0.10, glow=0.32)
    cyan = kit.surface("Prop | Cyan Base", "#2CE0FF", rough=0.35, metal=0.15, glow=0.22)

    # Pedestal grip base (centered at root so hand socket grabs cleanly)
    handle = kit.cylinder("StarHandle", col, (0, 0, -0.035), 0.028, 0.07, cyan, parent=root)
    kit.apply_prop_ink(handle, col, thickness=0.004)

    # 5-pointed plump 3D star body
    verts, faces = [(0.0, -0.034, 0.055), (0.0, 0.034, 0.055)], []
    outer_r, inner_r = 0.105, 0.046
    for i in range(10):
        ang = -math.pi / 2 + i * math.pi / 5
        r = outer_r if i % 2 == 0 else inner_r
        verts.append((r * math.cos(ang), 0.0, 0.055 + r * math.sin(ang)))
    for i in range(10):
        a = 2 + i
        b = 2 + ((i + 1) % 10)
        faces.append((0, b, a))
        faces.append((1, a, b))
    star = kit.mesh("StarBody", col, verts, faces, gold, parent=root, smoothing=False)
    kit.apply_prop_ink(star, col, thickness=0.0045)

    gem = kit.ball("StarRubyCore", col, (0.0, -0.032, 0.055), (0.030, 0.016, 0.030), coral, parent=root, segments=18, rings=12)
    kit.apply_prop_ink(gem, col, thickness=0.003)
    return root


# --------------------------------------------------------------------------- Deliverable 1: Hero 3 Reference Poses
def _dress_stop_hold_up_set(bpy, kit, col):
    """Golden sunset city street recreation for Reference Image 5 (`stop_hold_up`)."""
    asphalt = kit.make_wet_puddle_material("SunsetWetStreet", ("#181522", "#2A2133", "#3D2D3B"))
    _add_box(bpy, kit, col, "StreetFloor", (0.0, 2.5, -0.06), (12.0, 14.0, 0.12), asphalt, shadow=True)

    # Full-bleed warm golden sunset sky backdrop (tall enough to cover entire low-angle frustum)
    sky_low = kit.emission("SunsetSkyHorizon", "#FFC25C", 1.65)
    sky_mid = kit.emission("SunsetSkyAmber", "#F08A2B", 1.35)
    sun_halo = kit.emission("SunsetHaloDisc", "#FFE49E", 1.95)
    _add_box(bpy, kit, col, "SunsetBackdropLow", (0.0, 9.5, 2.6), (18.0, 0.2, 6.2), sky_low, shadow=False)
    _add_box(bpy, kit, col, "SunsetBackdropHigh", (0.0, 9.6, 8.8), (18.0, 0.2, 7.2), sky_mid, shadow=False)
    halo_disc = kit.ball("SunsetCrownGlow", col, (-0.15, 7.8, 3.6), (2.2, 0.25, 2.2), sun_halo, segments=24, rings=14)
    halo_disc.visible_shadow = False

    bldg_dark = kit.surface("CityBldgSilhouette", "#38263A", rough=0.72)
    bldg_warm = kit.surface("CityBldgWarm", "#664038", rough=0.68)
    win_glow = kit.emission("CityWindowGold", "#FFE39C", 1.9)
    van_white = kit.surface("StreetVanWhite", "#EAE4DC", rough=0.55)
    metal_dark = kit.surface("StreetMetal", "#1E1B24", rough=0.52)
    red_light = kit.emission("TrafficRed", "#FF382E", 2.8)

    # Left & right avenue buildings reaching high up the vertical 9:16 frame
    specs = [
        (-2.35, 5.4, 3.4, (1.35, 1.2, 6.8), bldg_dark),
        (-1.45, 7.2, 4.0, (1.25, 1.1, 8.0), bldg_warm),
        (1.65, 6.6, 3.8, (1.30, 1.2, 7.6), bldg_warm),
        (2.45, 4.8, 3.2, (1.20, 1.1, 6.4), bldg_dark),
        (0.55, 8.3, 4.2, (1.05, 0.9, 8.4), bldg_warm),
    ]
    for idx, (bx, by, bz, bsz, bmat) in enumerate(specs):
        _add_box(bpy, kit, col, f"CityBldg_{idx}", (bx, by, bz), bsz, bmat, ink=True, ink_thickness=0.008)
        for wz in (1.2, 2.0, 2.8, 3.6, 4.4, 5.2):
            if wz < bsz[2] - 0.5:
                _add_box(bpy, kit, col, f"CityWin_{idx}_{wz:.1f}",
                         (bx + (-0.42 if bx > 0 else 0.42), by - bsz[1] * 0.51, wz),
                         (0.26, 0.04, 0.34), win_glow, shadow=False)

    # Left street van + right traffic signal + floating kinetic bicycle/car silhouettes (Image 5 homage)
    _add_box(bpy, kit, col, "LeftVanBody", (-1.32, 2.55, 0.48), (0.68, 1.35, 0.72), van_white, ink=True, ink_thickness=0.006)
    _add_box(bpy, kit, col, "LeftVanWindshield", (-0.97, 2.25, 0.58), (0.05, 0.52, 0.28), metal_dark)
    _add_box(bpy, kit, col, "TrafficPole", (1.12, 2.55, 0.85), (0.06, 0.06, 1.70), metal_dark, ink=True)
    _add_box(bpy, kit, col, "TrafficBox", (1.08, 2.48, 1.32), (0.14, 0.14, 0.36), metal_dark, ink=True)
    kit.ball("TrafficRedLamp", col, (1.08, 2.40, 1.40), (0.045, 0.02, 0.045), red_light, segments=14, rings=10)

    # Floating upper-right bicycle wheel & car bumper silhouettes (kinetic time-stop vibe)
    wheel = kit.tube("FloatingBikeWheel", col, [
        (0.76 + 0.22 * math.cos(i * math.tau / 24), 2.35, 1.62 + 0.22 * math.sin(i * math.tau / 24))
        for i in range(25)
    ], 0.018, metal_dark)
    wheel.rotation_euler = (0.18, -0.25, 0.12)
    _add_box(bpy, kit, col, "FloatingCarSilhouette", (0.88, 2.85, 2.32), (0.78, 1.15, 0.36),
             metal_dark, rot=(0.24, -0.18, 0.32), ink=True, ink_thickness=0.006, shadow=False)

    # Golden bokeh orbs in background
    bokeh = kit.emission("GoldenBokeh", "#FFE39E", 2.2)
    for idx, (ox, oy, oz, r) in enumerate([
        (-0.85, 3.4, 1.85, 0.045), (0.62, 3.8, 1.95, 0.038),
        (-0.55, 2.8, 0.28, 0.028), (0.78, 2.9, 0.42, 0.032),
        (-0.35, 3.6, 2.45, 0.042), (0.42, 3.5, 2.65, 0.036),
    ]):
        b = kit.ball(f"SunsetBokeh_{idx}", col, (ox, oy, oz), (r, r, r), bokeh, segments=14, rings=10)
        b.visible_shadow = False

    # Portrait + sunset rim lighting
    _add_sun(bpy, kit, col, "SunsetSun", (-2.2, 3.5, 3.8), (0.0, 0.0, 0.75), "#FFD180", energy=1.95)
    kit.make_ricks_light("FrontCleanKey", col, (0.85, -1.75, 1.55), (0.0, 0.0, 0.88), "#FFF7EC", 135, size=0.95)
    kit.make_ricks_light("SunsetGoldenRimL", col, (-1.15, 1.35, 1.65), (-0.1, 0.0, 0.88), "#FFB340", 240, size=0.85)
    kit.make_ricks_light("SunsetGoldenRimR", col, (1.15, 1.25, 1.55), (0.0, 0.0, 0.85), "#FF9E2C", 190, size=0.85)


def _dress_power_aura_set(bpy, kit, col):
    """Fiery amber/orange backdrop + cyan aura lighting for Reference Image 6 (`power_aura_stance`)."""
    ground = kit.texture("CrackedArenaAsphalt", ("#171822", "#252634", "#363648"), "asphalt")
    _add_box(bpy, kit, col, "ArenaGround", (0.0, 1.5, -0.06), (10.0, 12.0, 0.12), ground, shadow=True)

    # Tall full-bleed fiery amber sky so zero dark gap appears at top of low-angle 26mm shot
    sky_fire = kit.emission("FireSkyBackdrop", "#FF8E1E", 1.50)
    _add_box(bpy, kit, col, "FireBackdrop", (0.0, 7.6, 5.2), (16.0, 0.2, 11.5), sky_fire, shadow=False)

    # Stylized billowing fire/smoke spheres filling background from ground to top edge
    fire_hot = kit.emission("FireCloudHot", "#FFE074", 1.85)
    fire_bright = kit.emission("FireCloudGold", "#FFB838", 1.55)
    fire_mid = kit.emission("FireCloudOrange", "#EB5E16", 1.25)
    fire_smoke = kit.surface("FireSmokeAmber", "#6E3524", rough=0.82)
    clouds = [
        (-1.35, 4.8, 1.85, (0.95, 0.55, 0.92), fire_bright),
        (-0.65, 5.2, 2.65, (1.05, 0.60, 1.00), fire_hot),
        (0.75, 5.1, 2.55, (1.02, 0.60, 0.98), fire_hot),
        (1.45, 4.7, 1.65, (0.90, 0.55, 0.88), fire_mid),
        (-1.55, 4.3, 0.85, (0.82, 0.50, 0.78), fire_bright),
        (1.50, 4.2, 0.75, (0.85, 0.50, 0.80), fire_bright),
        (-1.15, 5.4, 3.85, (1.15, 0.65, 1.05), fire_mid),
        (0.05, 5.5, 4.15, (1.25, 0.65, 1.15), fire_hot),
        (1.25, 5.4, 3.75, (1.15, 0.65, 1.05), fire_bright),
        (0.0, 5.8, 1.40, (1.45, 0.65, 1.20), fire_smoke),
    ]
    for idx, (cx, cy, cz, cr, cmat) in enumerate(clouds):
        c = kit.ball(f"FireCloud_{idx}", col, (cx, cy, cz), cr, cmat, segments=20, rings=14)
        c.visible_shadow = False

    # Right highway overpass & streetlamp silhouette (Image 6 right side)
    steel = kit.surface("OverpassSteel", "#2B2430", rough=0.68)
    _add_box(bpy, kit, col, "OverpassDeck", (1.45, 3.0, 1.55), (1.6, 0.55, 0.24),
             steel, rot=(0.0, -0.34, 0.15), ink=True, ink_thickness=0.007)
    _add_box(bpy, kit, col, "LampPost", (1.18, 2.65, 2.15), (0.05, 0.05, 1.65),
             steel, rot=(0.0, -0.20, 0.0), ink=True, ink_thickness=0.005)

    # Floating dark concrete debris blocks + fiery ember sparks outside character silhouette
    rock_mat = kit.surface("DebrisRock", "#2D2936", rough=0.78)
    debris = [
        (-0.62, 0.95, 1.48, (0.17, 0.14, 0.12), (0.4, 0.5, 0.3)),
        (-0.68, 0.85, 0.96, (0.14, 0.12, 0.18), (0.7, -0.3, 0.5)),
        (-0.56, 0.72, 0.34, (0.13, 0.11, 0.12), (-0.4, 0.6, 0.2)),
        (0.64, 0.92, 1.42, (0.15, 0.13, 0.13), (0.3, -0.5, 0.6)),
        (0.60, 0.80, 0.44, (0.14, 0.12, 0.13), (0.6, 0.4, -0.4)),
        (0.52, 0.68, 0.20, (0.11, 0.10, 0.10), (0.2, 0.7, 0.3)),
    ]
    for idx, (dx, dy, dz, dsz, drot) in enumerate(debris):
        _add_box(bpy, kit, col, f"DebrisChunk_{idx}", (dx, dy, dz), dsz, rock_mat,
                 rot=drot, ink=True, ink_thickness=0.005, shadow=False)

    ember_mat = kit.emission("ArenaEmberSpark", "#FFAE34", 2.8)
    for idx, (ex, ey, ez) in enumerate([
        (-0.34, -0.25, 0.14), (0.36, -0.22, 0.18), (-0.42, 0.20, 0.52), (0.44, 0.18, 0.58),
    ]):
        sp = kit.ball(f"EmberSpark_{idx}", col, (ex, ey, ez), (0.016, 0.016, 0.016), ember_mat, segments=10, rings=8)
        sp.visible_shadow = False

    _add_sun(bpy, kit, col, "ArenaSun", (-1.8, -2.4, 3.8), (0.0, 0.0, 0.65), "#FFF0DC", energy=1.85)
    kit.make_ricks_light("ArenaFrontKey", col, (0.65, -1.85, 1.35), (0.0, 0.0, 0.82), "#FFF9F2", 130, size=0.95)
    kit.make_ricks_light("ArenaCyanRimL", col, (-1.15, 0.65, 1.15), (0.0, 0.0, 0.72), "#3BE8FF", 210, size=0.75)
    kit.make_ricks_light("ArenaFireRimR", col, (1.20, 1.10, 1.25), (0.0, 0.0, 0.72), "#FF7B1A", 225, size=0.85)


def _dress_chill_chair_set(bpy, kit, col):
    """Sunlit studio room + Polaroid gallery + blue-sky terrace for Reference Image 7 (`chill_chair_lean`)."""
    wood_floor = kit.texture("StudioParquet", ("#3B2820", "#6E4730", "#9C6B46"), "wood")
    _add_box(bpy, kit, col, "LoungeFloor", (0.0, 1.0, -0.06), (10.0, 10.0, 0.12), wood_floor, shadow=True)

    # Left warm studio wall + framed gallery cards reaching full height
    wall_mat = kit.surface("StudioWarmWall", "#5E483D", rough=0.78)
    _add_box(bpy, kit, col, "LeftGalleryWall", (-0.86, 1.15, 1.85), (1.45, 0.14, 3.90),
             wall_mat, rot=(0.0, 0.0, -0.18), ink=True, ink_thickness=0.006)

    frame_white = kit.surface("PolaroidBorder", "#F5EFE6", rough=0.65)
    frame_art = kit.surface("PolaroidArt", "#8B7D72", rough=0.72)
    badge_red = kit.surface("PolaroidBadge", "#D92329", rough=0.55, glow=0.15)
    for idx, (pz, tilt) in enumerate([(1.32, 0.07), (0.98, -0.05), (0.64, 0.06)]):
        px = -0.58 - 0.03 * idx
        _add_box(bpy, kit, col, f"PolaroidCard_{idx}", (px, 1.04, pz), (0.34, 0.03, 0.28),
                 frame_white, rot=(0.0, tilt, -0.18), ink=True, ink_thickness=0.004)
        _add_box(bpy, kit, col, f"PolaroidInner_{idx}", (px, 1.02, pz + 0.015), (0.27, 0.032, 0.20),
                 frame_art, rot=(0.0, tilt, -0.18))
        _add_box(bpy, kit, col, f"PolaroidTag_{idx}", (px - 0.11, 1.00, pz - 0.08), (0.11, 0.035, 0.065),
                 badge_red, rot=(0.0, tilt, -0.18))

    # Full-bleed right open terrace blue sky + soft clouds + balcony railing + golden foliage + infinity neon
    sky_blue = kit.emission("TerraceBlueSky", "#3592F5", 1.38)
    cloud_white = kit.emission("TerraceCloudSoft", "#CCE8FF", 1.55)
    _add_box(bpy, kit, col, "TerraceSkyBackdrop", (1.25, 5.2, 4.2), (12.0, 0.2, 9.6), sky_blue, shadow=False)
    for idx, (cx, cz, cr) in enumerate([(0.85, 2.25, (0.65, 0.2, 0.26)), (1.45, 2.45, (0.75, 0.2, 0.30))]):
        cl = kit.ball(f"SkyCloud_{idx}", col, (cx, 4.8, cz), cr, cloud_white, segments=18, rings=12)
        cl.visible_shadow = False

    foliage_gold = kit.surface("SunlitFoliageGold", "#E0A82E", rough=0.72, glow=0.12)
    foliage_green = kit.surface("SunlitFoliageGreen", "#5B8C3E", rough=0.76)
    for idx, (fx, fy, fz, fr, fmat) in enumerate([
        (0.95, 3.0, 0.76, (0.48, 0.35, 0.42), foliage_gold),
        (1.35, 3.2, 0.98, (0.52, 0.38, 0.48), foliage_green),
        (0.75, 3.3, 0.60, (0.42, 0.32, 0.36), foliage_green),
    ]):
        kit.ball(f"TerraceTree_{idx}", col, (fx, fy, fz), fr, fmat, segments=18, rings=12)

    rail_mat = kit.surface("BalconyRail", "#3B3542", rough=0.62)
    _add_box(bpy, kit, col, "BalconyTopRail", (1.05, 2.35, 0.68), (2.2, 0.06, 0.05), rail_mat, ink=True)
    _add_box(bpy, kit, col, "BalconyMidRail", (1.05, 2.35, 0.46), (2.2, 0.05, 0.04), rail_mat, ink=True)

    # Glowing golden infinity loop clearly visible in upper-right sky (Image 7 nod)
    neon_gold = kit.emission("InfinityNeonGold", "#FFD859", 3.4)
    inf_pts = []
    for i in range(49):
        t = i * math.tau / 48
        denom = 1.0 + math.sin(t) ** 2
        ix = 0.16 * math.cos(t) / denom
        iz = 0.13 * math.sin(t) * math.cos(t) / denom
        inf_pts.append((0.34 + ix, 1.35, 1.24 + iz))
    inf_curve = kit.tube("InfinitySign", col, inf_pts, 0.013, neon_gold)
    inf_curve.visible_shadow = False

    # Foreground-left sleek dark desk corner + open laptop lid raised into lower-left frame (Image 7)
    desk_mat = kit.surface("StudioDeskDark", "#262028", rough=0.52)
    laptop_mat = kit.surface("StudioLaptopBody", "#1D1E26", rough=0.38, metal=0.35)
    laptop_rim = kit.surface("StudioLaptopRim", "#DFD8CE", rough=0.42, metal=0.25)
    _add_box(bpy, kit, col, "FgDeskCorner", (-0.36, -0.56, 0.24), (0.48, 0.36, 0.05), desk_mat, ink=True)
    _add_box(bpy, kit, col, "FgLaptopLid", (-0.32, -0.58, 0.37), (0.30, 0.016, 0.22),
             laptop_mat, rot=(-0.18, 0.0, 0.14), ink=True, ink_thickness=0.004)
    _add_box(bpy, kit, col, "FgLaptopTopBezel", (-0.32, -0.576, 0.48), (0.30, 0.018, 0.011),
             laptop_rim, rot=(-0.18, 0.0, 0.14))

    _add_sun(bpy, kit, col, "LoungeSun", (2.2, -1.8, 3.6), (0.0, 0.0, 0.65), "#FFE8BD", energy=1.85)
    kit.make_ricks_light("LoungeCleanKey", col, (-0.55, -1.65, 1.35), (0.0, 0.0, 0.78), "#FFF9F2", 135, size=0.95)
    kit.make_ricks_light("LoungeSunRim", col, (1.15, 0.85, 1.45), (0.0, 0.0, 0.78), "#FFD066", 225, size=0.80)


def _best_settled_frame(scene, f0: int, f1: int, metric_fn) -> int:
    """Pick the frame in [f0, f1] maximizing `metric_fn()` after depsgraph update."""
    import bpy
    best_f, best_v = int((f0 + f1) * 0.78), -1e18
    for f in range(int(f0 + (f1 - f0) * 0.45), f1 + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        val = metric_fn(f)
        if val > best_v:
            best_v, best_f = val, f
    return best_f


def render_hero_3_reference_poses(bpy, kit, mascot_api, anim_library, tmp_dir: Path):
    """Render 3 native 1080x1920 reference pose panels into `tmp_dir`."""
    from mathutils import Vector
    from bpy_extras.object_utils import world_to_camera_view

    panel_paths = []

    # --- Panel 1: Image 5 (`stop_hold_up`) ---
    scene, col, cam = _reset_eevee_scene(bpy, kit, width=1080, height=1920, frame_end=60,
                                         world_color="#4A2E3B", world_strength=0.72, cinema_grade=True, lens=26.0)
    _dress_stop_hold_up_set(bpy, kit, col)
    hero = mascot_api.load_mascot(col, name="MascotStop", bottom_style="pajamas", arm_style="hoodie")
    _set_drawn_light_if_present(hero, (-0.55, -0.65, 0.52))
    anim_library.stop_hold_up(hero, 1, 60, loc=(0.0, 0.0, 0.0), yaw=0.0)
    hero.finish_bake()

    best_f = _best_settled_frame(scene, 1, 60, lambda _f: -hero.hand_socket_L.matrix_world.translation.y)
    scene.frame_set(best_f)
    bpy.context.view_layer.update()

    # Frame close to outstretched open_stop L palm on viewer-left while keeping all 5 fingers & face 100% inside frame
    hand_pos = hero.hand_socket_L.matrix_world.translation.copy()
    head_pos = hero.head.matrix_world.translation.copy()
    cam.location = Vector((hand_pos.x * 0.45, min(hand_pos.y - 0.62, -1.04), head_pos.z - 0.22))
    aim_pt = Vector((head_pos.x * 0.32 + hand_pos.x * 0.30, 0.02, head_pos.z - 0.11))
    kit.aim(cam, aim_pt)
    bpy.context.view_layer.update()

    # Exact vertex-level screen-space clearance solver for ALL 5 fingers of `open_stop` + right body margin
    hand_meshes = [
        o for o in hero._objects
        if o.type == "MESH" and not o.hide_render and "hand" in o.name.lower() and "_l" in o.name.lower()
    ]
    head_meshes = [
        o for o in hero._objects
        if o.type == "MESH" and not o.hide_render and ("head" in o.name.lower() or "beanie" in o.name.lower())
    ]
    for _iter in range(12):
        h_xs = [
            world_to_camera_view(scene, cam, o.matrix_world @ v.co).x
            for o in hand_meshes for v in o.data.vertices
        ] or [world_to_camera_view(scene, cam, hand_pos).x]
        b_xs = [
            world_to_camera_view(scene, cam, o.matrix_world @ v.co).x
            for o in head_meshes for v in o.data.vertices
        ] or [world_to_camera_view(scene, cam, head_pos).x]
        min_hx, max_hx = min(h_xs), max(h_xs)
        max_bx = max(b_xs)
        if min_hx < 0.058 and max_bx > 0.90:
            # Both left finger tips and right beanie are tight: pull camera back slightly
            cam.location.y -= 0.06
        elif min_hx < 0.058:
            # Shift framing slightly left so outermost finger tip has >= 5.8% (~63 px) left margin
            shift = (0.065 - min_hx) * 0.55
            cam.location.x -= shift
            aim_pt.x -= shift * 0.85
        elif max_bx > 0.945:
            shift = (max_bx - 0.935) * 0.55
            cam.location.x += shift
            aim_pt.x += shift * 0.85
        else:
            break
        kit.aim(cam, aim_pt)
        bpy.context.view_layer.update()
    print(f"[showcase] Panel 1 open_stop X bounds: [{min_hx:.3f}, {max_hx:.3f}], head max X: {max_bx:.3f}", flush=True)

    hero.update_ink(cam, frame=None, pixels=4.2)
    _enforce_render_contract(scene, cam)
    p1 = tmp_dir / "hero_panel_1_stop.png"
    scene.render.filepath = str(p1)
    bpy.ops.render.render(write_still=True)
    panel_paths.append(str(p1))

    # --- Panel 2: Image 6 (`power_aura_stance`) ---
    scene, col, cam = _reset_eevee_scene(bpy, kit, width=1080, height=1920, frame_end=60,
                                         world_color="#3A1F28", world_strength=0.72, cinema_grade=True, lens=26.0)
    _dress_power_aura_set(bpy, kit, col)
    hero = mascot_api.load_mascot(col, name="MascotPower", bottom_style="pajamas", arm_style="hoodie")
    _set_drawn_light_if_present(hero, (-0.45, -0.72, 0.52))
    anim_library.power_aura_stance(hero, 1, 60, aura=True, loc=(0.0, 0.0, 0.0), yaw=0.0, collection=col)
    hero.finish_bake()

    best_f = _best_settled_frame(
        scene, 1, 60,
        lambda _f: hero.hand_socket_L.matrix_world.translation.z + hero.hand_socket_R.matrix_world.translation.z,
    )
    scene.frame_set(best_f)
    bpy.context.view_layer.update()

    cam.location = Vector((0.0, -1.16, 0.46))
    kit.aim(cam, (0.0, 0.0, 0.67))
    bpy.context.view_layer.update()
    hero.update_ink(cam, frame=None, pixels=4.2)
    _enforce_render_contract(scene, cam)
    p2 = tmp_dir / "hero_panel_2_power.png"
    scene.render.filepath = str(p2)
    bpy.ops.render.render(write_still=True)
    panel_paths.append(str(p2))

    # --- Panel 3: Image 7 (`chill_chair_lean`) ---
    scene, col, cam = _reset_eevee_scene(bpy, kit, width=1080, height=1920, frame_end=60,
                                         world_color="#2D4A6E", world_strength=0.78, cinema_grade=True, lens=28.0)
    _dress_chill_chair_set(bpy, kit, col)
    hero = mascot_api.load_mascot(col, name="MascotChill", bottom_style="pajamas", arm_style="hoodie")
    _set_drawn_light_if_present(hero, (0.45, -0.70, 0.55))
    anim_library.chill_chair_lean(hero, 1, 60, seat_z=0.42, loc=(0.0, 0.0, 0.0), yaw=0.0,
                                  build_chair=True, collection=col)
    hero.finish_bake()

    best_f = _best_settled_frame(
        scene, 1, 60,
        lambda _f: hero.hand_socket_L.matrix_world.translation.z + hero.hand_socket_R.matrix_world.translation.z,
    )
    scene.frame_set(best_f)
    bpy.context.view_layer.update()

    head_pos = hero.head.matrix_world.translation.copy()
    cam.location = Vector((0.10, -1.22, 0.64))
    kit.aim(cam, (0.02, 0.0, max(0.68, head_pos.z - 0.16)))
    bpy.context.view_layer.update()
    hero.update_ink(cam, frame=None, pixels=4.2)
    _enforce_render_contract(scene, cam)
    p3 = tmp_dir / "hero_panel_3_chill.png"
    scene.render.filepath = str(p3)
    bpy.ops.render.render(write_still=True)
    panel_paths.append(str(p3))

    (tmp_dir / "hero_meta.json").write_text(json.dumps({"panels": panel_paths}), encoding="utf-8")


# --------------------------------------------------------------------------- Deliverable 2: 4-View Studio Turnaround
def render_turnaround_4views(bpy, kit, mascot_api, tmp_dir: Path):
    """Render clean bright lit 4-panel studio turnaround panels into `tmp_dir`."""
    from mathutils import Vector

    panel_w, panel_h = 810, 1920
    scene, col, cam = _reset_eevee_scene(
        bpy, kit, width=panel_w, height=panel_h, frame_end=10,
        world_color="#CFD8E8", world_strength=0.58, cinema_grade=False, lens=34.0,
    )

    floor_mat = kit.surface("TurnaroundFloor", "#CED7E6", rough=0.82)
    wall_mat = kit.surface("TurnaroundWall", "#C2CDDF", rough=0.88)
    ring_mat = kit.surface("TurntableAccent", "#8F9EB8", rough=0.70)
    _add_box(bpy, kit, col, "StudioFloor", (0.0, 0.0, -0.05), (8.0, 8.0, 0.10), floor_mat, shadow=True)
    _add_box(bpy, kit, col, "StudioBackdrop", (0.0, 3.2, 1.5), (8.0, 0.15, 4.2), wall_mat, shadow=False)

    ring_pts = [(0.36 * math.cos(i * math.tau / 64), 0.36 * math.sin(i * math.tau / 64), 0.0015) for i in range(65)]
    ring_obj = kit.tube("FloorContactRing", col, ring_pts, 0.003, ring_mat)
    ring_obj.visible_shadow = False

    _add_sun(bpy, kit, col, "TurnaroundSun", (-1.8, -2.2, 4.2), (0.0, 0.0, 0.55), "#FFFDF9", energy=2.95, angle_deg=5.0)
    kit.make_ricks_light("TurnaroundKey", col, (1.25, -2.2, 1.85), (0.0, 0.0, 0.72), "#FFFFFF", 95, size=1.2)
    kit.make_ricks_light("TurnaroundFill", col, (-1.35, -1.9, 1.45), (0.0, 0.0, 0.68), "#EDF3FF", 55, size=1.2)
    kit.make_ricks_light("TurnaroundRim", col, (0.35, 1.85, 1.95), (0.0, 0.0, 0.75), "#FFF7E8", 85, size=1.0)

    hero = mascot_api.load_mascot(col, name="MascotTurnaround", bottom_style="pajamas", arm_style="hoodie")
    ratio_info = hero.head_bbox_ratio()
    print(f"[showcase] Mascot head bbox ratio: {ratio_info}", flush=True)

    views = [
        ("FRONT (0 deg)", 0.0),
        ("3/4 HERO (35 deg)", math.radians(35.0)),
        ("90 deg SIDE PROFILE", math.radians(90.0)),
        ("BACK (180 deg)", math.pi),
    ]

    cam.location = Vector((0.0, -2.06, 0.66))
    kit.aim(cam, (0.0, 0.0, 0.65))
    _enforce_render_contract(scene, cam)

    rendered_panels = []
    for idx, (label, yaw_rad) in enumerate(views):
        hero.pose(
            None,
            loc=(0.0, 0.0, 0.0),
            yaw=yaw_rad,
            arm_L=((-0.285, -0.04, -0.03), (-0.255, 0.02, 0.09)),
            arm_R=((+0.285, -0.04, -0.03), (+0.255, 0.02, 0.09)),
            hand_L="relaxed_curl",
            hand_R="relaxed_curl",
            expr="idle_cute",
        )
        _set_drawn_light_if_present(hero, (-0.52, -0.68, 0.52))
        bpy.context.view_layer.update()
        hero.update_ink(cam, frame=None, pixels=4.2)
        out_i = tmp_dir / f"turnaround_{idx}.png"
        scene.render.filepath = str(out_i)
        bpy.ops.render.render(write_still=True)
        rendered_panels.append({"label": label, "path": str(out_i)})

    (tmp_dir / "turnaround_meta.json").write_text(
        json.dumps({"panel_w": panel_w, "panel_h": panel_h, "ratio": ratio_info["ratio"], "panels": rendered_panels}),
        encoding="utf-8",
    )


# --------------------------------------------------------------------------- Deliverable 3: 18-Expression 3D Grid
def render_expression_grid_18(bpy, kit, mascot_api, tmp_dir: Path):
    """Render all 12 story expressions + 6 lip-sync visemes on the 3D Mascot head into `tmp_dir`."""
    from mathutils import Vector

    cols, rows = 6, 3
    cell_w, cell_h = 540, 640
    all_names = [(name, "STORY") for name in mascot_api.EXPRESSIONS] + [
        (name, "VISEME") for name in mascot_api.VISEMES
    ]
    if len(all_names) != 18:
        raise RuntimeError(f"Expected 18 expressions (12 story + 6 visemes), got {len(all_names)}")

    scene, col, cam = _reset_eevee_scene(
        bpy, kit, width=cell_w, height=cell_h, frame_end=10,
        world_color="#C9D4E6", world_strength=0.95, cinema_grade=False, lens=32.0,
    )

    bg_mat = kit.surface("ExprCardBackdrop", "#BCC9DF", rough=0.88)
    _add_box(bpy, kit, col, "ExprBackdrop", (0.0, 2.0, 1.0), (5.0, 0.15, 3.5), bg_mat, shadow=False)

    _add_sun(bpy, kit, col, "ExprSun", (-1.6, -2.4, 3.4), (0.0, 0.0, 0.96), "#FFFDF9", energy=1.45)
    kit.make_ricks_light("ExprKey", col, (0.75, -1.65, 1.35), (0.0, 0.0, 0.96), "#FFFFFF", 115, size=0.95)
    kit.make_ricks_light("ExprFill", col, (-0.85, -1.55, 1.15), (0.0, 0.0, 0.94), "#EEF4FF", 85, size=0.95)

    hero = mascot_api.load_mascot(col, name="MascotExpr", bottom_style="pajamas", arm_style="hoodie")
    hero.pose(None, loc=(0.0, 0.0, 0.0), yaw=math.radians(4.0), head_pitch=math.radians(-2.0),
              hand_L="relaxed_curl", hand_R="relaxed_curl", expr="idle_cute")
    _set_drawn_light_if_present(hero, (-0.52, -0.68, 0.52))
    bpy.context.view_layer.update()

    head_center = hero.head.matrix_world.translation.copy()
    cam.location = Vector((0.02, -0.76, head_center.z - 0.02))
    kit.aim(cam, (0.0, 0.0, head_center.z - 0.03))
    bpy.context.view_layer.update()
    hero.update_ink(cam, frame=None, pixels=3.8)
    _enforce_render_contract(scene, cam)

    cell_files = []
    for idx, (expr_name, kind) in enumerate(all_names):
        hero.set_expression(expr_name, frame=None)
        bpy.context.view_layer.update()
        cell_path = tmp_dir / f"expr_{idx:02d}_{expr_name}.png"
        scene.render.filepath = str(cell_path)
        bpy.ops.render.render(write_still=True)
        cell_files.append({"idx": idx, "name": expr_name, "kind": kind, "path": str(cell_path)})

    (tmp_dir / "expr_meta.json").write_text(
        json.dumps({"cols": cols, "rows": rows, "cell_w": cell_w, "cell_h": cell_h, "cells": cell_files}),
        encoding="utf-8",
    )


def stitch_proof_sheets(tmp_dir: Path, out_dir: Path):
    """Stitch and label any rendered proof sheets in `tmp_dir` using system Python + Pillow."""
    from PIL import Image, ImageDraw

    out_dir.mkdir(parents=True, exist_ok=True)

    hero_meta_file = tmp_dir / "hero_meta.json"
    if hero_meta_file.is_file():
        meta = json.loads(hero_meta_file.read_text(encoding="utf-8"))
        composite = Image.new("RGB", (3240, 1920), (16, 14, 20))
        for i, p_str in enumerate(meta["panels"]):
            img = Image.open(p_str).convert("RGB")
            if img.size != (1080, 1920):
                img = img.resize((1080, 1920), Image.Resampling.LANCZOS)
            composite.paste(img, (i * 1080, 0))
        out_path = out_dir / "hero_3_reference_poses.png"
        composite.save(out_path, format="PNG", compress_level=4)
        print(f"[showcase] Saved {out_path} ({composite.size[0]}x{composite.size[1]})", flush=True)

    turn_meta_file = tmp_dir / "turnaround_meta.json"
    if turn_meta_file.is_file():
        meta = json.loads(turn_meta_file.read_text(encoding="utf-8"))
        panel_w, panel_h = meta["panel_w"], meta["panel_h"]
        sheet = Image.new("RGBA", (panel_w * 4, panel_h), (200, 210, 227, 255))
        title_font = _load_font(30, bold=True)
        sub_font = _load_font(20, bold=False)

        for idx, item in enumerate(meta["panels"]):
            img = Image.open(item["path"]).convert("RGBA")
            sheet.paste(img, (idx * panel_w, 0))

        draw = ImageDraw.Draw(sheet, "RGBA")
        pretty_labels = ["FRONT (0°)", "3/4 HERO (35°)", "90° SIDE PROFILE", "BACK (180°)"]
        for idx, item in enumerate(meta["panels"]):
            x0 = idx * panel_w
            if idx > 0:
                draw.line([(x0, 0), (x0, panel_h)], fill=(20, 16, 22, 95), width=3)
            lbl = pretty_labels[idx] if idx < len(pretty_labels) else item["label"]
            _draw_pill_label(draw, x0 + panel_w // 2, 34, lbl, title_font,
                             bg=(20, 16, 22, 235), border=(255, 210, 31, 255), pad_x=28, pad_y=12, radius=18)

        footer = (
            f"OFFICIAL MASCOT TURNAROUND  |  Height ~1.28 m  |  Head H/W = {meta['ratio']:.3f}  |  "
            f"Sneaker Soles Flat @ Z = 0.000 m"
        )
        _draw_pill_label(draw, (panel_w * 4) // 2, panel_h - 74, footer, sub_font,
                         bg=(20, 16, 22, 220), border=(230, 36, 41, 255), pad_x=30, pad_y=10, radius=14)
        out_path = out_dir / "turnaround_4views.png"
        sheet.convert("RGB").save(out_path, format="PNG", compress_level=4)
        print(f"[showcase] Saved {out_path} ({sheet.size[0]}x{sheet.size[1]})", flush=True)

    expr_meta_file = tmp_dir / "expr_meta.json"
    if expr_meta_file.is_file():
        meta = json.loads(expr_meta_file.read_text(encoding="utf-8"))
        cols, rows, cell_w, cell_h = meta["cols"], meta["rows"], meta["cell_w"], meta["cell_h"]
        grid = Image.new("RGBA", (cols * cell_w, rows * cell_h), (188, 201, 223, 255))
        label_font = _load_font(22, bold=True)
        tag_font = _load_font(15, bold=True)

        for item in meta["cells"]:
            r, c = divmod(item["idx"], cols)
            img = Image.open(item["path"]).convert("RGBA")
            grid.paste(img, (c * cell_w, r * cell_h))

        draw = ImageDraw.Draw(grid, "RGBA")
        for item in meta["cells"]:
            idx, expr_name, kind = item["idx"], item["name"], item["kind"]
            r, c = divmod(idx, cols)
            x0, y0 = c * cell_w, r * cell_h
            draw.rectangle([x0, y0, x0 + cell_w - 1, y0 + cell_h - 1], outline=(20, 16, 22, 80), width=2)
            border_col = (255, 210, 31, 255) if kind == "STORY" else (59, 232, 255, 255)
            badge_prefix = f"{idx + 1:02d}" if kind == "STORY" else f"V{idx - 11}"
            _draw_pill_label(
                draw, x0 + cell_w // 2, y0 + cell_h - 56, f"{badge_prefix} · {expr_name}", label_font,
                bg=(20, 16, 22, 235), border=border_col, pad_x=18, pad_y=8, radius=14,
            )
            tag_bg = (230, 36, 41, 225) if kind == "STORY" else (24, 118, 168, 225)
            _draw_pill_label(
                draw, x0 + 68, y0 + 14, kind, tag_font,
                bg=tag_bg, border=(255, 253, 251, 200), pad_x=10, pad_y=4, radius=10, border_w=1,
            )
        out_path = out_dir / "expression_grid_18.png"
        grid.convert("RGB").save(out_path, format="PNG", compress_level=4)
        print(f"[showcase] Saved {out_path} ({grid.size[0]}x{grid.size[1]})", flush=True)


# --------------------------------------------------------------------------- Deliverable 4: 15s 1080p Demo Reel
def _dress_showcase_studio(bpy, kit, col):
    """Build a multi-zone bright cinema-lit 3D Creator Studio stage for the 450f reel."""
    floor_wood = kit.texture("ShowcaseWoodFloor", ("#382824", "#6B4A35", "#9A6E4B"), "wood")
    wall_indigo = kit.texture("ShowcaseStudioWall", ("#1E2947", "#2C3B63", "#465987"), "plaster")
    trim_gold = kit.surface("ShowcaseGoldTrim", "#E8B339", rough=0.45, metal=0.25)
    rug_teal = kit.surface("ShowcaseTealRug", "#224B63", rough=0.88)
    rug_crimson = kit.surface("ShowcaseCrimsonRug", "#6E2332", rough=0.88)
    wood_warm = kit.surface("ShowcaseShelfWood", "#7A4E34", rough=0.68)
    lamp_amber = kit.emission("ShowcaseWarmLamp", "#FFC86B", 2.2)
    cyan_accent = kit.emission("ShowcaseCyanStrip", "#3BE8FF", 1.9)

    # Continuous studio floor at exact Z = 0.000 m
    _add_box(bpy, kit, col, "MainStudioFloor", (0.0, 0.0, -0.08), (16.0, 16.0, 0.16), floor_wood, shadow=True)

    # Surrounding dressed studio walls (placed well clear of all camera paths)
    _add_box(bpy, kit, col, "NorthBackWall", (0.0, 5.4, 2.2), (16.0, 0.25, 4.8), wall_indigo)
    _add_box(bpy, kit, col, "EastStageWall", (5.6, 0.0, 2.2), (0.25, 12.0, 4.8), wall_indigo)
    _add_box(bpy, kit, col, "WestStageWall", (-5.6, 0.0, 2.2), (0.25, 12.0, 4.8), wall_indigo)
    _add_box(bpy, kit, col, "BaseboardNorth", (0.0, 5.26, 0.09), (15.8, 0.06, 0.18), trim_gold, ink=True)

    # Zone 1 & 7 (Center Runway / Spotlight Stage around X=0, Y=0)
    _add_box(bpy, kit, col, "CenterRunwayMat", (0.0, 0.10, 0.002), (2.4, 2.2, 0.004), rug_teal, shadow=True)
    # Bookshelf + warm lamp + framed art behind Center Stage (Y = +3.6 .. +5.1)
    _add_box(bpy, kit, col, "CenterBookcase", (-1.15, 4.65, 1.05), (1.35, 0.42, 2.10), wood_warm, ink=True)
    for idx, (bx, bz, col_hex) in enumerate([
        (-1.45, 1.45, "#E62429"), (-1.30, 1.45, "#FFD21F"), (-1.12, 1.45, "#3BE8FF"),
        (-0.85, 0.92, "#FF7B89"), (-1.05, 0.92, "#7ED957"),
    ]):
        bmat = kit.surface(f"BookColor_{idx}", col_hex, rough=0.65)
        _add_box(bpy, kit, col, f"StudioBook_{idx}", (bx, 4.52, bz), (0.11, 0.24, 0.30), bmat, ink=True)

    _add_box(bpy, kit, col, "LampStand", (1.25, 4.25, 0.75), (0.08, 0.08, 1.50), trim_gold, ink=True)
    kit.ball("WarmPracticalOrb", col, (1.25, 4.25, 1.62), (0.18, 0.18, 0.18), lamp_amber)
    kit.make_light_cone("StudioWarmCone", col, (1.25, 4.25, 1.60), (1.05, 3.85, 0.05), 0.14, 0.68, "#FFC86B")

    # Zone 2 (Power Arena Alcove around X = +2.8, Y = +0.2)
    _add_box(bpy, kit, col, "PowerArenaPad", (2.8, 0.2, 0.003), (1.9, 1.9, 0.006), rug_crimson, shadow=True)
    for side in (-1, 1):
        _add_box(bpy, kit, col, f"PowerPylon_{side}", (2.8 + side * 1.15, 2.45, 1.25),
                 (0.22, 0.22, 2.50), wood_warm, ink=True)
        _add_box(bpy, kit, col, f"PowerNeon_{side}", (2.8 + side * 1.15, 2.32, 1.25),
                 (0.05, 0.04, 2.10), cyan_accent, shadow=False)

    # Zone 3 (Prop Showcase & Hype Stage around X = -2.8, Y = +0.2)
    _add_box(bpy, kit, col, "PropStageRug", (-2.8, 0.2, 0.003), (2.2, 2.0, 0.006), rug_teal, shadow=True)
    pedestal_mat = kit.surface("PropPlinthMat", "#EAEFF8", rough=0.55)
    # Low pickup pad right in front-right of mascot (-2.54, 0.02) so pickup reach is natural & clean
    _add_box(bpy, kit, col, "PropPickupPad", (-2.54, 0.02, 0.09), (0.28, 0.28, 0.18), pedestal_mat, ink=True)
    # Side display column for background depth
    _add_box(bpy, kit, col, "StageBackPlinth", (-3.55, 2.15, 0.55), (0.42, 0.42, 1.10), pedestal_mat, ink=True)
    kit.ball("StageDecorOrb", col, (-3.55, 2.15, 1.28), (0.16, 0.16, 0.16), lamp_amber)

    # Zone 4 (Cozy Sunlit Lounge Chair Alcove around X = 0.0, Y = +2.55)
    # Dressed window blinds & warm art panels on NorthBackWall behind Y=2.55
    for z in (1.05, 1.35, 1.65, 1.95, 2.25):
        _add_box(bpy, kit, col, f"LoungeBlind_{z:.2f}", (0.15, 5.18, z), (1.55, 0.08, 0.07), trim_gold, ink=True)
    kit.make_light_cone("LoungeSunShaft", col, (0.35, 4.95, 2.25), (-0.15, 2.65, 0.10), 0.35, 0.95, "#FFE09E")

    # Global shadow-casting sun + bright warm/cool studio fill lights covering all 4 zones
    _add_sun(bpy, kit, col, "ShowcaseMasterSun", (-2.8, -3.6, 5.2), (0.0, 0.5, 0.65), "#FFF5E4", energy=1.65, angle_deg=3.8)
    for idx, (lx, ly, lz, tx, ty, col_hex, watts) in enumerate([
        (0.6, -2.4, 2.2, 0.0, 0.0, "#FFF9F0", 165),
        (-0.8, 1.6, 2.1, 0.0, 0.0, "#8CC8FF", 115),
        (3.2, -1.8, 2.1, 2.8, 0.2, "#FFF5E8", 165),
        (2.2, 1.6, 1.9, 2.8, 0.2, "#3BE8FF", 140),
        (-2.3, -1.8, 2.1, -2.8, 0.2, "#FFF7EC", 165),
        (0.6, 0.7, 2.1, 0.0, 2.55, "#FFF6E8", 160),
    ]):
        kit.make_ricks_light(f"StudioFill_{idx}", col, (lx, ly, lz), (tx, ty, 0.75), col_hex, watts, size=1.25)


def _key_visibility_window(obj, f0: int, f1: int, total_end: int = REEL_END):
    """Ensure a temporary zone prop/chair is visible ONLY during [f0, f1]."""
    targets = [obj, *getattr(obj, "children_recursive", [])]
    keyframes = [(1, True), (max(1, f0 - 1), True), (f0, False), (f1, False), (min(total_end, f1 + 1), True)]
    for t in targets:
        for prop in ("hide_render", "hide_viewport"):
            for frame, hidden in keyframes:
                setattr(t, prop, hidden)
                t.keyframe_insert(prop, frame=frame)
            if t.animation_data and t.animation_data.action:
                fcurve = t.animation_data.action.fcurves.find(prop)
                if fcurve:
                    for kp in fcurve.keyframe_points:
                        kp.interpolation = "CONSTANT"


def build_demo_reel_scene(bpy, kit, rc, mascot_api, anim_library):
    """Author the 450-frame (15.0s @ 30fps) 1080x1920 Mascot Demo Reel."""
    scene, col, cam = _reset_eevee_scene(
        bpy, kit, width=1080, height=1920, frame_end=REEL_END,
        world_color="#2A3A5E", world_strength=0.88, cinema_grade=True, lens=26.0,
    )
    _dress_showcase_studio(bpy, kit, col)

    hero = mascot_api.load_mascot(col, name="MascotReel", bottom_style="pajamas", arm_style="hoodie")
    _set_drawn_light_if_present(hero, (-0.50, -0.68, 0.52))

    # Create colorful 3D Golden Star Trophy prop on the pickup pad for Beat 4 (`199..264`)
    prop_start_loc = (-2.54, 0.02, 0.22)
    hero_prop = _build_hero_star_prop(bpy, kit, col, loc=prop_start_loc)
    hero_prop.location = prop_start_loc
    hero_prop.keyframe_insert("location", frame=1)
    hero_prop.keyframe_insert("location", frame=199)
    _key_visibility_window(hero_prop, 199, 264, REEL_END)

    # --- Build kinetic `ricks_camera.py` CameraProgram FIRST so `point_at_camera_wink` tracks exact lens ---
    def walk_pos_at(f):
        u = rc.ease5((f - 1) / 65.0)
        return (-0.92 * (1.0 - u), 0.55 * (1.0 - u), 0.72)

    # Shot 1 (1..132): Lateral tracking lead on `walk_to`, then smooth whip-drop push-in into `stop_hold_up`!
    shot_1_walk_and_stop = rc.Shot(
        1, 132, name="walk_to_and_stop_whip",
        pos=rc.Track([
            (1, (-1.08, -1.35, 0.84)),
            (62, (-0.14, -1.42, 0.80)),
            (84, (-0.08, -1.04, 0.68)),
            (132, (-0.06, -1.00, 0.68)),
        ], "carry"),
        aim=rc.handoff(rc.lead(walk_pos_at, frames=4.0, max_m=0.16), (-0.02, 0.02, 0.82), 62, 82),
        lens=26.0,
    )

    # Shot 2 (133..198): Heroic low-angle crane arc around `power_aura_stance`
    shot_2_power = rc.Shot(
        133, 198, name="power_aura_stance",
        pos=rc.Track([
            (133, (2.56, -0.96, 0.45)),
            (168, (2.82, -0.94, 0.47)),
            (198, (2.98, -0.98, 0.48)),
        ], "carry"),
        aim=rc.Track([(133, (2.80, 0.20, 0.67)), (198, (2.80, 0.20, 0.70))], "ease"),
        lens=26.0,
    )

    # Shot 3 (199..264): Whip handoff from colorful 3D Golden Star prop onto Mascot `pickup_and_present`
    shot_3_pickup = rc.Shot(
        199, 264, name="pickup_and_present",
        pos=rc.Track([
            (199, (-2.42, -1.12, 0.62)),
            (232, (-2.68, -1.18, 0.70)),
            (264, (-2.72, -1.15, 0.72)),
        ], "carry"),
        aim=rc.handoff((-2.56, 0.04, 0.34), (-2.76, 0.20, 0.74), 203, 224),
        lens=27.0,
    )

    # Shot 4 (265..328): Energetic 3/4 dynamic orbit on `celebrate_hype`
    shot_4_hype = rc.Shot(
        265, 328, name="celebrate_hype",
        pos=rc.Track([
            (265, (-3.12, -1.08, 0.58)),
            (298, (-2.82, -1.18, 0.64)),
            (328, (-2.62, -1.14, 0.66)),
        ], "carry"),
        aim=rc.Track([(265, (-2.80, 0.20, 0.70)), (328, (-2.80, 0.20, 0.76))], "ease"),
        lens=26.0,
    )

    # Shot 5 (329..392): Cozy sunlit 3/4 lounge dolly on `chill_chair_lean`
    shot_5_chill = rc.Shot(
        329, 392, name="chill_chair_lean",
        pos=rc.Track([
            (329, (0.24, 1.32, 0.64)),
            (365, (0.12, 1.35, 0.64)),
            (392, (0.06, 1.36, 0.64)),
        ], "carry"),
        aim=rc.Track([(329, (0.02, 2.55, 0.72)), (392, (0.0, 2.55, 0.73))], "ease"),
        lens=28.0,
    )

    # Shot 6 (393..450): Final push-in (`393..418`) -> completely settled payoff hold (`419..450`) on `point_at_camera_wink`
    shot_6_wink = rc.Shot(
        393, 450, name="point_at_camera_wink",
        pos=rc.Track([
            (393, (0.18, -1.52, 0.74)),
            (418, (0.0, -1.32, 0.72)),
            (450, (0.0, -1.32, 0.72)),
        ], "ease"),
        aim=rc.Track([
            (393, (0.0, -0.15, 0.78)),
            (418, (0.0, -0.15, 0.80)),
            (450, (0.0, -0.15, 0.80)),
        ], "ease"),
        lens=26.0,
    )

    program = rc.CameraProgram([
        shot_1_walk_and_stop,
        shot_2_power,
        shot_3_pickup,
        shot_4_hype,
        shot_5_chill,
        shot_6_wink,
    ])

    speeds = rc.screen_speed(program)
    max_speed = max((v for _, v in speeds), default=0.0)
    print(f"[showcase] CameraProgram cuts (1-based): {program.cuts} | max pre-render speed: {max_speed:.1f} px/frame",
          flush=True)

    rc.bake(cam, program, focus_object=None)
    _enforce_render_contract(scene, cam)

    # --- Bake all 7 required animations in exact sequence across 1..450 ---
    # 1. `walk_to` (1..66): Bouncy arrival down Center Runway to (0.0, 0.0)
    anim_library.walk_to(hero, 1, 66, (-0.92, 0.55), (0.0, 0.0), ground_z=0.0, expr="idle_cute")

    # 2. `stop_hold_up` (67..132): Seamless stop + dramatic low-angle `open_stop` palm at (0.0, 0.0)
    anim_library.stop_hold_up(hero, 67, 132, loc=(0.0, 0.0, 0.0), yaw=0.0)

    # 3. `power_aura_stance` (133..198): Power Arena Zone (2.8, 0.2, 0.0) with cyan lightning aura
    anim_library.power_aura_stance(hero, 133, 198, aura=True, loc=(2.8, 0.2, 0.0), yaw=0.0, collection=col)

    # 4. `pickup_and_present` (199..264): Prop Stage (-2.8, 0.2, 0.0) grabbing `hero_prop`
    anim_library.pickup_and_present(hero, 199, 264, hero_prop, loc=(-2.8, 0.2, 0.0), yaw=0.0, side="R")

    # 5. `celebrate_hype` (265..328): Joyful double-fist hype hops on Prop Stage (-2.8, 0.2, 0.0)
    anim_library.celebrate_hype(hero, 265, 328, loc=(-2.8, 0.2, 0.0), yaw=0.0)

    # 6. `chill_chair_lean` (329..392): Cozy Sunlit Lounge (0.0, 2.55, 0.0)
    anim_library.chill_chair_lean(hero, 329, 392, seat_z=0.42, loc=(0.0, 2.55, 0.0), yaw=0.0,
                                  build_chair=True, collection=col)

    # 7. `point_at_camera_wink` (393..450): Center Spotlight Payoff (0.0, -0.15, 0.0)
    anim_library.point_at_camera_wink(hero, 393, 450, loc=(0.0, -0.15, 0.0), yaw=0.0, camera=cam)

    for f in range(1, REEL_END + 1):
        scene.frame_set(f)
        bpy.context.view_layer.update()
        hero.update_ink(cam, frame=f, pixels=4.2)

    hero.finish_bake()
    _enforce_render_contract(scene, cam)

    # Save 0-based QA manifest for `scripts/short_qa.py --strict`
    manifest = {
        "shots": [
            {"id": 1, "name": "walk_to", "a": 0, "b": 66},
            {"id": 2, "name": "stop_hold_up", "a": 66, "b": 132},
            {"id": 3, "name": "power_aura_stance", "a": 132, "b": 198},
            {"id": 4, "name": "pickup_and_present", "a": 198, "b": 264},
            {"id": 5, "name": "celebrate_hype", "a": 264, "b": 328},
            {"id": 6, "name": "chill_chair_lean", "a": 328, "b": 392},
            {"id": 7, "name": "point_at_camera_wink", "a": 392, "b": 450},
        ],
        "cuts": [c - 1 for c in program.cuts],
        "action_ranges": [[0, 65], [132, 197], [198, 263], [264, 327]],
        "shadow_checks": [
            {
                "name": "settled_payoff_floor_shadow",
                "start": 420,
                "end": 450,
                "registration": "locked-camera",
                "regions": [[0.10, 0.80, 0.32, 0.94]],
                "max_adjacent_luma": 1.2,
            }
        ],
    }
    SHOWCASE_WORK_DIR.mkdir(parents=True, exist_ok=True)
    manifest_path = SHOWCASE_WORK_DIR / "shots_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return scene, cam, manifest_path


def encode_demo_reel_mp4(frames_dir: Path, out_mp4: Path):
    """Encode frame_0001..frame_0450.png into canonical 1080x1920 30fps H.264 CRF 18 MP4."""
    missing = [f for f in range(1, REEL_END + 1) if not (frames_dir / f"frame_{f:04d}.png").is_file()]
    if missing:
        print(f"[showcase] Skipping MP4 encode ({len(missing)} frame(s) not yet present, e.g. {missing[:5]})",
              flush=True)
        return False
    out_mp4.parent.mkdir(parents=True, exist_ok=True)
    cmd = [
        "ffmpeg", "-y", "-v", "error",
        "-framerate", str(FPS),
        "-i", str(frames_dir / "frame_%04d.png"),
        "-frames:v", str(REEL_END),
        "-c:v", "libx264",
        "-crf", "18",
        "-preset", "slow",
        "-vf", "setsar=1",
        "-pix_fmt", "yuv420p",
        "-r", str(FPS),
        "-movflags", "+faststart",
        str(out_mp4),
    ]
    subprocess.run(cmd, check=True)
    print(f"[showcase] Encoded {out_mp4}", flush=True)
    return True


def render_demo_reel(bpy, kit, rc, mascot_api, anim_library, *, frame_start: int, frame_end: int,
                     frames_dir: Path, out_mp4: Path):
    scene, cam, _ = build_demo_reel_scene(bpy, kit, rc, mascot_api, anim_library)
    frames_dir.mkdir(parents=True, exist_ok=True)
    scene.frame_start = max(1, int(frame_start))
    scene.frame_end = min(REEL_END, int(frame_end))
    _enforce_render_contract(scene, cam)
    scene.render.filepath = str(frames_dir / "frame_")
    print(f"[showcase] Rendering demo reel frames {scene.frame_start}..{scene.frame_end} -> {frames_dir}", flush=True)
    bpy.ops.render.render(animation=True)
    encode_demo_reel_mp4(frames_dir, out_mp4)


# --------------------------------------------------------------------------- CLI Entrypoint
def _parse_args(argv: list[str]):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--stage",
        choices=("proofs", "hero", "turnaround", "expressions", "reel", "encode", "stitch", "all"),
        default="all",
    )
    parser.add_argument("--frame-start", type=int, default=1)
    parser.add_argument("--frame-end", type=int, default=REEL_END)
    parser.add_argument("--frames-dir", type=Path, default=SHOWCASE_WORK_DIR / "frames")
    parser.add_argument("--out-dir", type=Path, default=PREVIEWS_DIR)
    parser.add_argument("--tmp-dir", type=Path, default=None)
    return parser.parse_args(argv)


def _run_blender_worker(args):
    import bpy
    import ricks_v2_kit as kit
    import ricks_camera as rc
    from assets.mascot import mascot_api, anim_library

    out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir)
    frames_dir = args.frames_dir if args.frames_dir.is_absolute() else (ROOT / args.frames_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    with tempfile.TemporaryDirectory(prefix="mascot_showcase_") as tmp:
        tmp_dir = Path(args.tmp_dir) if args.tmp_dir else Path(tmp)
        tmp_dir.mkdir(parents=True, exist_ok=True)
        need_stitch = False
        if args.stage in ("proofs", "hero", "all"):
            render_hero_3_reference_poses(bpy, kit, mascot_api, anim_library, tmp_dir)
            need_stitch = True
        if args.stage in ("proofs", "turnaround", "all"):
            render_turnaround_4views(bpy, kit, mascot_api, tmp_dir)
            need_stitch = True
        if args.stage in ("proofs", "expressions", "all"):
            render_expression_grid_18(bpy, kit, mascot_api, tmp_dir)
            need_stitch = True

        if need_stitch:
            py_exe = "python3" if os.name != "nt" else "python"
            subprocess.run(
                [py_exe, str(Path(__file__).resolve()), "--stage", "stitch",
                 "--tmp-dir", str(tmp_dir), "--out-dir", str(out_dir)],
                check=True,
                cwd=ROOT,
            )

        if args.stage in ("reel", "all"):
            render_demo_reel(
                bpy, kit, rc, mascot_api, anim_library,
                frame_start=args.frame_start,
                frame_end=args.frame_end,
                frames_dir=frames_dir,
                out_mp4=out_dir / "mascot_demo_reel_1080p.mp4",
            )


def main():
    in_blender = False
    try:
        import bpy  # noqa: F401
        in_blender = True
    except ModuleNotFoundError:
        pass

    if "--" in sys.argv:
        raw_argv = sys.argv[sys.argv.index("--") + 1:]
    else:
        raw_argv = sys.argv[1:]
    args = _parse_args(raw_argv)

    if args.stage == "stitch":
        if not args.tmp_dir:
            raise SystemExit("--stage stitch requires --tmp-dir")
        out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir)
        stitch_proof_sheets(args.tmp_dir, out_dir)
        return

    if args.stage == "encode":
        frames_dir = args.frames_dir if args.frames_dir.is_absolute() else (ROOT / args.frames_dir)
        out_dir = args.out_dir if args.out_dir.is_absolute() else (ROOT / args.out_dir)
        if not encode_demo_reel_mp4(frames_dir, out_dir / "mascot_demo_reel_1080p.mp4"):
            raise SystemExit(1)
        return

    if in_blender:
        _run_blender_worker(args)
        return

    if os.environ.get("RICKS_REMOTE") != "modal":
        raise SystemExit(
            "Refusing to run local PC Blender. Launch on Modal GPU via:\n"
            "  modal run scripts/modal_blender.py --mode run --project assets/mascot "
            "--script assets/mascot/render_previews.py --runner blender --script-args \"--stage proofs\" --overwrite"
        )
    blender_exe = os.environ.get("BLENDER_EXE", "/opt/blender42/blender")
    subprocess.run(
        [blender_exe, "-b", "--factory-startup", "--python-exit-code", "1",
         "--python", str(Path(__file__).resolve()), "--", *raw_argv],
        check=True,
        cwd=ROOT,
    )


if __name__ == "__main__":
    main()
