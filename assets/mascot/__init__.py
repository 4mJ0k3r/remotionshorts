"""Official Main Character (Red-Beanie Yellow-Hoodie Chibi Mascot) package.

Quickstart inside Blender 4.2 Python:
    from assets.mascot import mascot_api, anim_library
    hero = mascot_api.load_mascot(scene.collection)
    anim_library.stop_hold_up(hero, 1, 60)
"""
from __future__ import annotations

import importlib

from . import mascot_api
from .mascot_api import (
    ALL_EXPRESSIONS,
    EXPRESSIONS,
    HAND_POSES,
    VISEMES,
    MascotRig,
    load_mascot,
)

__all__ = [
    "ALL_EXPRESSIONS",
    "EXPRESSIONS",
    "HAND_POSES",
    "VISEMES",
    "MascotRig",
    "anim_library",
    "expression_gen",
    "load_mascot",
    "mascot_api",
]


def __getattr__(name: str):
    if name in {"anim_library", "expression_gen"}:
        mod = importlib.import_module(f".{name}", __name__)
        globals()[name] = mod
        return mod
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
