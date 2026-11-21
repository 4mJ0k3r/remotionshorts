from pathlib import Path
import sys
from PIL import Image
root=Path('D:/remotionshorts')
sys.path.insert(0,str(root/'scripts'))
from calibration_sheet import make_sheet
target=root/'renders/project_paradox_india_ep03_5rs_blade/v04'
labels={
 77:'Barbershop light and faces',191:'Window-lit press',260:'Customer after recoil',
 350:'Jar shake and coins',758:'Molten pool close-up',1021:'Brass scale and shadows',
 1191:'Stamp and frosted grid',1281:'Waist-level press lever',
 224:'Shock recoil',338:'Coins leave the raised jar',668:'Dark forge stone floor',1111:'Chuckle and brim shadow',
 1214:'Stamp lift',1234:'Off arm relaxes',1254:'Lever down',817:'Pour and interactive spill',
}
def read(index):
    with Image.open(target/'calibration'/f'frame_{index+1:04d}.png') as source:
        return source.copy()

def assemble(name, frames):
    panels=[{'frame':f-1,'label':labels[f]} for f in frames]
    make_sheet(read,{'panels':panels,'closeups':[]},target/name,columns=4,cell=(270,495))

assemble('V4_8_frame_calibration.jpg',list(labels)[:8])
assemble('V4_acting_and_contacts.jpg',list(labels)[8:])
