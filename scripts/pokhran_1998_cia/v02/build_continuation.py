"""Entry point for the separately baked native Pokhran continuation scenes."""
from pathlib import Path
import runpy
import sys

HERE=Path(__file__).resolve().parent
if __name__=="__main__":
    part=int(sys.argv[-1])
    if part not in (2,3,4):
        raise ValueError(part)
    sys.path.insert(0,str(HERE))
    runpy.run_path(str(HERE/f"part{part}.py"),run_name="__main__")
