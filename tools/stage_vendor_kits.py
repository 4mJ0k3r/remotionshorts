"""Stage licensed reference ZIPs into the git-ignored refs/vendor tree.

Merges multi-part archives into one folder, normalizes Windows separators,
refuses absolute or parent-relative entries, and reports same-path files
whose contents differ instead of silently overwriting them.

  python tools/stage_vendor_kits.py SOURCE_DIR

Writes refs/vendor/<package>/ plus refs/vendor/<package>/STAGING_MANIFEST.json.
Never commit refs/; the vendor licences restrict redistribution.
"""
import hashlib
import json
from pathlib import Path, PurePosixPath
import sys
import zipfile

ROOT = Path(__file__).resolve().parents[1]
DEST = ROOT / "refs" / "vendor"
PACKAGES = {
    "ricksclips_v1.1": ["RicksClips_V1.1_1_skill.zip", "RicksClips_V1.1_2_character_views.zip",
                        "RicksClips_V1.1_3_character_sheets.zip"],
    "tickingatlas_v12": ["TickingAtlas_RicksClips_v12_Full_Skill_And_Kit.zip"],
}


def raw_entries(archive):
    """Yield (ZipInfo, raw name) without zipfile's os.sep rewrite hiding backslashes."""
    with zipfile.ZipFile(archive) as z:
        for info in z.infolist():
            raw = info.orig_filename
            yield z, info, raw


def safe_path(raw):
    name = raw.replace("\\", "/")
    parts = PurePosixPath(name).parts
    if name.startswith("/") or (parts and parts[0].endswith(":")) or ".." in parts:
        raise ValueError(f"Unsafe archive entry: {raw!r}")
    return PurePosixPath(*parts)


def stage(source, package, archives):
    out = DEST / package
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"{out} already has files; stage into a fresh folder.")
    out.mkdir(parents=True, exist_ok=True)
    seen, conflicts, normalized, files = {}, [], 0, 0
    for name in archives:
        archive = source / name
        for z, info, raw in raw_entries(archive):
            rel = safe_path(raw)
            normalized += "\\" in raw
            if raw.endswith(("/", "\\")) or info.is_dir():
                (out / rel).mkdir(parents=True, exist_ok=True)
                continue
            data = z.read(info)
            digest = hashlib.sha256(data).hexdigest()
            key = rel.as_posix()
            if key in seen:
                if seen[key]["sha256"] != digest:
                    conflicts.append({"path": key, "kept": seen[key]["archive"], "other": name,
                                      "kept_sha256": seen[key]["sha256"], "other_sha256": digest})
                continue  # first archive in the declared order wins; reported above
            target = out / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            seen[key] = {"archive": name, "sha256": digest, "bytes": len(data)}
            files += 1
    manifest = {"package": package, "archives": archives, "files": files,
                "backslash_entries_normalized": normalized, "same_path_conflicts": conflicts,
                "redistribution": "restricted - see the package licence; keep under refs/ only"}
    (out / "STAGING_MANIFEST.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


def main():
    source = Path(sys.argv[1]).expanduser().resolve()
    for package, archives in PACKAGES.items():
        result = stage(source, package, archives)
        print(json.dumps({k: v for k, v in result.items() if k != "same_path_conflicts"}),
              "conflicts:", len(result["same_path_conflicts"]))


if __name__ == "__main__":
    main()
