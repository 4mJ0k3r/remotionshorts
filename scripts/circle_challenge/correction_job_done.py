from pathlib import Path
ROOT=Path('D:/remotionshorts/scripts/circle_challenge')
exec(compile((ROOT/'correct.py').read_text(),str(ROOT/'correct.py'),'exec'),{})
exec(compile((ROOT/'calibrate.py').read_text(),str(ROOT/'calibrate.py'),'exec'),{})
