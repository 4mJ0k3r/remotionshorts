from pathlib import Path
import sys
from PIL import Image
root=Path('D:/remotionshorts')
sys.path.insert(0,str(root/'scripts'))
from calibration_sheet import make_sheet
v3=root/'renders/project_paradox_india_ep03_5rs_blade/v03'
labels={1:'Cupro nickel and room glints',77:'Barbershop materials',191:'Press and walnut insert',260:'White foam and reaction',
        350:'Bazaar brick and flying coins',520:'Heavy coin and shelf bokeh',758:'Hot metal and orange spill',
        870:'Forge and slotted blades',918:'Blade and price card',1021:'Brass balance',
        1191:'Mint stamp desk',1281:'Cast iron mint press'}
def read(index):
    with Image.open(v3/'calibration'/f'frame_{index+1:04d}.png') as img:
        return img.copy()
make_sheet(read,{'panels':[{'frame':frame-1,'label':label} for frame,label in labels.items()],'closeups':[]},
           v3/'V3_12_frame_calibration.jpg',columns=4,cell=(270,495))
