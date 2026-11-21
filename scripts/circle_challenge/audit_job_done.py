from pathlib import Path
p=Path('D:/remotionshorts/scripts/circle_challenge/audit.py')
exec(compile(p.read_text(),str(p),'exec'),{})
