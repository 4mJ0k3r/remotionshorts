"""Native Part 2 revision. Reuse every unmodified setup from the preview."""
from pathlib import Path
import shutil
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "part2_v01"))
from part2_scene import main

output = HERE.parents[2] / "renders/broken_headphones_shoko" / HERE.name
shutil.copyfile(HERE / "shout_wide.png", output / "shout_wide.png")
main(output, polish=True)
