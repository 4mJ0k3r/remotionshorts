"""Final contact close checks; replace only affected tiles in the sheet."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parent))
import build_caveman_toilet as build
import check_v3
build.do_sheet(540,960,12,'v3_final')
