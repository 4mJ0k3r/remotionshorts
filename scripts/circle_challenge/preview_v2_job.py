from pathlib import Path
path=Path('D:/remotionshorts/scripts/circle_challenge/preview.py')
exec(compile(path.read_text(),str(path),'exec'),{})
