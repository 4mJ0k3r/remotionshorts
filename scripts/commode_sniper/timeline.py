from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders'/'commode_sniper'
FRAMES=1635
BOUNDS=(1,84,186,306,417,618,723,804,905,1083,1248,1362,1457,1539,1636)
STILLS=(25,110,260,380,520,675,760,875,990,1120,1300,1410,1500,1590)
EXTRA_STILLS=(65,160,210,325,820,1205,1380,1444,1542,1625)
def cut(f):return next(i for i in range(14) if BOUNDS[i]<=f<BOUNDS[i+1])
