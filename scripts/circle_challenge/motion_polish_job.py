from pathlib import Path
root=Path('D:/remotionshorts/scripts/circle_challenge')
for script in ('motion_polish.py','calibrate_motion.py'):
    path=root/script
    exec(compile(path.read_text(),str(path),'exec'),{})
