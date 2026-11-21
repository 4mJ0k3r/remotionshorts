"""Construction smoke check for the drawn look and camera program opt-ins.

  python tests/blender_optin_smoke.py        # launcher: takes .blender_gpu.lock, runs Blender

Builds the starter template four ways (cel/drawn x keyed/handoff) through its
real build() entry point. Never renders and never writes into renders/; a
temporary .blend proves the drawn look survives save and reopen.
A pass verifies construction only, not visual quality.
"""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
BLENDER = os.environ.get("BLENDER_EXE", r"D:\tools\Blender\4.2.23\blender.exe")


def launcher():
    lock, owner = ROOT / ".blender_gpu.lock", uuid4().hex
    try:
        with lock.open("x", encoding="utf-8") as fh:
            json.dump({"project": "tests/blender_optin_smoke", "pid": os.getpid(), "owner": owner}, fh)
    except FileExistsError:
        raise SystemExit(f"GPU busy. Wait for the owner of {lock}.")
    try:
        subprocess.run([BLENDER, "-b", "--factory-startup", "--python-exit-code", "1",
                        "--python", str(Path(__file__).resolve()), "--", "worker"], check=True, cwd=ROOT)
    finally:
        if lock.exists() and json.loads(lock.read_text(encoding="utf-8")).get("owner") == owner:
            lock.unlink()


def worker():
    import importlib.util
    import bpy
    from mathutils import Vector

    sys.path[:0] = [str(ROOT / "scripts")]
    import ricks_v2_kit as kit
    import ricks_drawn_look as drawn
    import ricks_camera as rc
    import shorts_preflight as gate

    spec = importlib.util.spec_from_file_location("ricks_short_template",
                                                  ROOT / "scripts/templates/ricks_short_template.py")
    template = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(template)
    FRAMES = (1, 4, 10, 11, 15, 18, 23, 24, 25, 26, 30, 48)

    class Shim:                        # the anchor function only needs the rig's controls
        def __init__(self, name="Hero"):
            o = bpy.data.objects
            self.arms = [o[f"{name} | round-tipped arm {s}"] for s in "LR"]
            self.feet = [o[f"{name} | foot tick {s}"] for s in "LR"]
            self.head, self.root = o[f"{name} | head control"], o[name]

    def anchors(scene):
        out = {}
        for f in FRAMES:
            scene.frame_set(f)
            out[f] = drawn.contact_anchors(Shim())
        return out

    def camera_track(scene):
        out = {}
        for f in FRAMES:
            scene.frame_set(f)
            m = scene.camera.matrix_world
            out[f] = (m.translation.copy(), (m.to_3x3() @ Vector((0, 0, -1))).normalized())
        return out

    def ink_profile(scene, frame):
        scene.frame_set(frame)
        deps = bpy.context.evaluated_depsgraph_get()
        face = bpy.data.objects["Hero | ellipsoid head"]
        hull = bpy.data.objects["Hero | ellipsoid head • ink"]
        light = bpy.data.objects["Drawn look | Hero light"]
        toward = (light.matrix_world.to_3x3() @ Vector((0, 0, 1))).normalized()
        fe, he = face.evaluated_get(deps), hull.evaluated_get(deps)
        fm, hm = fe.to_mesh(), he.to_mesh()
        try:
            assert len(fm.vertices) == len(hm.vertices), "hull topology changed"
            rot = fe.matrix_world.to_3x3()
            lit, shade, chin, all_ = [], [], [], []
            for a, b in zip(fm.vertices, hm.vertices):
                d = (he.matrix_world @ b.co - fe.matrix_world @ a.co).length
                n = (rot @ a.normal).normalized()
                all_.append(d)
                if n.dot(toward) > .6:
                    lit.append(d)
                elif n.dot(toward) < -.6:
                    shade.append(d)
                if n.z < -.75:
                    chin.append(d)
        finally:
            fe.to_mesh_clear()
            he.to_mesh_clear()
        mean = lambda v: sum(v) / len(v)
        peak = max(all_)
        return {"lit": mean(lit), "shade": mean(shade), "chin": mean(chin),
                "normalized": [d / peak for d in all_]}

    def decal_gap(scene):
        """Largest gap (mm) between the visible face artwork and the head surface,
        over the decal's central eye-and-mouth area."""
        from mathutils.bvhtree import BVHTree
        scene.frame_set(1)
        deps = bpy.context.evaluated_depsgraph_get()
        face = bpy.data.objects["Hero | ellipsoid head"].evaluated_get(deps)
        tree = BVHTree.FromObject(face, deps)
        inv = face.matrix_world.inverted()
        decal = bpy.data.objects["Hero | curious"]
        uv = decal.data.uv_layers[0].data
        central = {l.vertex_index for l in decal.data.loops
                   if .2 < uv[l.index].uv[0] < .8 and .2 < uv[l.index].uv[1] < .8}
        gap = 0.0
        for i in central:
            p = inv @ (decal.matrix_world @ decal.data.vertices[i].co)
            gap = max(gap, tree.find_nearest(p)[3])
        return gap * 1000

    def outline(scene):
        """Front-outline radii of the drawn head relative to a circle."""
        import math
        face = bpy.data.objects["Hero | ellipsoid head"]
        pts = [v.co for v in face.data.vertices if abs(v.co.y) < .02]
        left = max(-p.x for p in pts); right = max(p.x for p in pts)
        top = max(p.z for p in pts); bottom = max(-p.z for p in pts)
        return {"left_right_ratio": left / right, "bottom_top_ratio": bottom / top}

    report = {}
    built = {}
    for look in ("cel", "drawn"):
        for cam in ("keyed", "handoff"):
            scene = template.build(bpy, kit, look, cam)
            res = gate.validate_resources(scene)
            assert res["pass"] and not res["target_exceeded"], (look, cam, res)
            has_drawn = any(o.name.startswith("Drawn look |") for o in scene.objects)
            assert has_drawn == (look == "drawn"), "drawn objects leaked into the default look"
            ink_mods = [m for o in scene.objects for m in o.modifiers if m.type == "NODES"]
            assert bool(ink_mods) == (look == "drawn")
            entry = {"triangles": res["visible_triangles"], "anchors": anchors(scene), "camera": camera_track(scene)}
            entry["decal_gap_mm"] = decal_gap(scene)
            if look == "drawn":
                a = ink_profile(scene, 30)
                entry["ink"] = {k: a[k] for k in ("lit", "shade", "chin")}
                # Frames 10 -> 11: the head is still turning and leaning.
                t0, t1 = ink_profile(scene, 10), ink_profile(scene, 11)
                entry["ink_stability"] = max(abs(x - y) for x, y in zip(t0["normalized"], t1["normalized"]))
                entry["head_outline"] = outline(scene)
                fists = [p.radius for p in bpy.data.objects["Hero | round-tipped arm R"].data.splines[0].bezier_points]
                entry["fist_radius"] = fists[2]
            built[(look, cam)] = entry
            report[f"{look}/{cam}"] = {k: v for k, v in entry.items() if k not in {"anchors", "camera"}}

    # 1. Both character paths expose the same contact anchors.
    worst = 0.0
    for cam in ("keyed", "handoff"):
        for f in FRAMES:
            a, b = built[("cel", cam)]["anchors"][f], built[("drawn", cam)]["anchors"][f]
            assert a.keys() == b.keys()
            worst = max(worst, max((a[k] - b[k]).length for k in a))
    assert worst < 1e-6, f"anchors drift between looks: {worst}"
    report["anchor_max_difference_m"] = worst

    # 2. Drawn ink: thin on the lit side, heavy on the shade side and under the chin; stable.
    ink = built[("drawn", "keyed")]["ink"]
    assert ink["shade"] > 1.6 * ink["lit"], ink
    assert ink["chin"] > 1.4 * ink["lit"], ink
    assert built[("drawn", "keyed")]["ink_stability"] < .05, built[("drawn", "keyed")]["ink_stability"]
    shape = built[("drawn", "keyed")]["head_outline"]
    assert abs(shape["left_right_ratio"] - 1) > .01 or abs(shape["bottom_top_ratio"] - 1) > .02, shape
    # Face artwork stays on the warped surface about as well as on the default head.
    assert built[("drawn", "keyed")]["decal_gap_mm"] < built[("cel", "keyed")]["decal_gap_mm"] + 2.0, \
        (built[("drawn", "keyed")]["decal_gap_mm"], built[("cel", "keyed")]["decal_gap_mm"])

    # 3. Default camera untouched by the drawn look; handoff keeps the post-cut shot.
    for f in FRAMES:
        a, b = built[("cel", "keyed")]["camera"][f], built[("drawn", "keyed")]["camera"][f]
        assert (a[0] - b[0]).length < 1e-9 and (a[1] - b[1]).length < 1e-9
    for f in (25, 26, 30, 48):
        a, b = built[("cel", "keyed")]["camera"][f], built[("cel", "handoff")]["camera"][f]
        assert (a[0] - b[0]).length < 1e-5 and (a[1] - b[1]).length < 1e-5, f"post-cut shot changed at {f}"

    # 4. Handoff program evaluates around the handoff and the cut; bake matches the plan.
    scene = template.build(bpy, kit, "drawn", "handoff")
    assert list(scene["ricks_camera_cuts"]) == [template.CUT]
    eyes = bpy.data.objects["Focus | Hero eyes"]
    program = template.handoff_program(rc, lambda f: tuple(eyes.matrix_world.translation))
    focus = bpy.data.objects["Focus | camera program"]
    cam_path = {}
    for f in range(1, template.CUT + 3):
        scene.frame_set(f)
        state = program.evaluate(f)
        m = scene.camera.matrix_world
        fwd = (m.to_3x3() @ Vector((0, 0, -1))).normalized()
        want = (Vector(state.aim) - Vector(state.pos)).normalized()
        assert (m.translation - Vector(state.pos)).length < 1e-4, f
        assert fwd.dot(want) > .99999, f
        assert (focus.matrix_world.translation - Vector(state.focus)).length < 1e-4, f
        cam_path[f] = m.translation.copy()
    step = lambda f: (cam_path[f + 1] - cam_path[f]).length
    assert step(10) > .005, "camera stopped during the handoff"
    assert step(template.CUT - 2) < 1e-4, "shot A did not settle before the cut"
    assert step(template.CUT - 1) > .5, "the hard cut was smoothed away"
    report["handoff_step_m"] = {"f10": step(10), "f23": step(template.CUT - 2), "cut": step(template.CUT - 1)}
    report["handoff_settle_frame"] = rc.settle_frame(program, 0)

    # 5. The drawn look survives save and reopen.
    with tempfile.TemporaryDirectory() as tmp:
        path = os.path.join(tmp, "optin_smoke.blend")
        bpy.ops.wm.save_as_mainfile(filepath=path, copy=True)
        bpy.ops.wm.open_mainfile(filepath=path)
        reopened = ink_profile(bpy.context.scene, 30)
        assert abs(reopened["shade"] / reopened["lit"] - ink["shade"] / ink["lit"]) < 1e-3
        report["reopen_shade_to_lit"] = reopened["shade"] / reopened["lit"]
        bpy.ops.wm.read_factory_settings(use_empty=True)
    print("OPTIN_SMOKE_REPORT " + json.dumps(report, default=float))
    print("OPTIN_SMOKE_OK NO_RENDER")


if __name__ == "__main__":
    if "--" in sys.argv and sys.argv[sys.argv.index("--") + 1:] == ["worker"]:
        worker()
    else:
        launcher()
