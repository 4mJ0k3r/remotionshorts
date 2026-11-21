"""Render the native calibration and the 50%-scale approval preview."""
import json
from pathlib import Path
from uuid import uuid4
import sys

import bpy

root=Path(__file__).resolve().parents[3]
sys.path.insert(0,str(root/"scripts"))
import shorts_preflight as gate

phase=sys.argv[-1]
out=root/"renders/one_year_no_wipe/v01"
shots=json.loads((out/"shots.json").read_text())
s=bpy.context.scene
r=s.render
assert (r.resolution_x,r.resolution_y,r.resolution_percentage,r.fps,s.frame_end)==(1080,1920,100,30,837)
assert all(image.packed_file for image in bpy.data.images if image.source=="FILE")
r.image_settings.file_format="PNG"
r.image_settings.compression=0
if phase=="proof":
    proofs=out/f"native_proofs_{uuid4().hex[:8]}"
    measurements=[]

    def inspect(frame):
        item=gate.validate_resources(s)
        measurements.append(item["visible_triangles"])
        if not item["pass"] or item["target_exceeded"]:
            raise RuntimeError(f"Frame {frame} overshot resources: {item}")

    report=gate.benchmark(s,shots["proof_frames"],proofs,update=inspect)
    report["max_evaluated_triangles"]=max(measurements)
    report["proofs_dir"]=proofs.name
    (out/"benchmark.json").write_text(json.dumps(report,indent=2))
    if report["status"]!="PASS":
        raise RuntimeError("Preview GPU gate failed")
elif phase=="preview":
    report=json.loads((out/"benchmark.json").read_text())
    density=json.loads((out/"proof_edge.json").read_text())
    if report["status"]!="PASS" or density["status"]!="PASS":
        raise RuntimeError("The native proof must pass before the preview")
    images=out/"preview_frames"
    images.mkdir(exist_ok=True)
    r.resolution_percentage=50
    r.filepath=str(images/"frame_")
    r.use_overwrite=True
    bpy.ops.render.render(animation=True)
