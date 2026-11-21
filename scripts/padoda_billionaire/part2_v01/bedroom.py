"""Dressed childhood bedroom and practical lighting."""
import math
from random import Random

import ricks_v2_kit as k
from courtyard import box

BED_TOP = .567


def bedroom(c):
    wood=k.texture("Amber maple grain",("#35222c","#784935","#b17b50"),"wood",(.68,.82))
    indigo=k.texture("Indigo painted bedroom",("#162248","#24335c","#3c4873"),"plaster",(.72,.85))
    cloth=k.surface("Canvas midnight teal","#1f6568",.8)
    cream=k.surface("Pillow linen","#f2bd91",.8)
    gold=k.surface("Brushed brass keepsakes","#ac7538",.70,.28)
    palette=[k.surface("Toy and textile paint",color,.77) for color in
             ("#bf5448","#edac4c","#36918b","#405e9d","#a26183")]
    box("Bedroom timber floor",c,(0,0,-.11),(9,8,.22),wood)
    box("Bedroom back wall",c,(0,2.53,2.3),(8,.19,4.7),indigo)
    box("Walnut skirting",c,(0,2.34,.12),(8,.13,.24),wood,.018)
    for i in range(20):
        box("Board joint",c,(i*.44-4.4,0,.001),(.012,8,.004),indigo,0)
    box("Single bed maple frame",c,(0,.86,.31),(2.05,1.6,.28),wood,.063,True)
    box("Rounded maple headboard",c,(0,1.73,.76),(2.10,.14,1.31),wood,.088,True)
    for x in (-.91,.91):
        for y in (.22,1.51):
            box("Bed feet",c,(x,y,.138),(.14,.14,.31),wood,.022,True)
    mattress=box("Soft mattress edge",c,(0,.83,.475),(1.98,1.54,.184),cream,.067,True)
    box("Striped duvet base",c,(0,.88,.559),(1.92,1.38,.019),cloth,.007)
    for i in range(12):
        box("Duvet woven stripe",c,(-.87+i*.154,.92,.570),(.09,1.35,.009),palette[i%5],.004)
    pillow=k.ball("Rumpled cream pillow",c,(-.53,1.32,.66),(.44,.25,.122),cream,segments=28,rings=14)
    pillow.rotation_euler.z=.22
    box("Low wooden bed step",c,(0,-.235,.069),(1.41,.58,.140),wood,.026,True)
    before_practical=set(c.objects)
    box("Bedside cabinet",c,(1.41,.84,.34),(.67,.68,.68),wood,.063,True)
    for z in (.20,.43):
        box("Nightstand drawer front",c,(1.41,.48,z),(.60,.058,.19),wood,.025)
        k.ball("Drawer pull",c,(1.41,.436,z),(.039,.026,.026),gold)
    lens=k.emission("Amber bedside practical","#ffaf4a",2.8)
    k.cylinder("Lamp brass foot",c,(1.47,.95,.72),.148,.072,gold)
    k.cylinder("Lamp brass stem",c,(1.47,.95,.91),.025,.36,gold)
    k.cylinder("Retro tapered bedside shade",c,(1.47,.95,1.19),.218,.31,palette[1],r2=.111)
    k.cylinder("Lamp lower diffuser",c,(1.47,.95,1.027),.193,.021,lens)
    k.make_light_cone("Amber light cone",c,(1.47,.95,1.022),(1.29,.78,.52),.138,.39,"#FFB05A")
    for j in range(3):
        o=box("Stacked bedside comic",c,(1.15,.63,.697+j*.036),(.21,.19,.032),palette[j],.009)
        o.rotation_euler.z=.14*(j-1)
    clock=k.cylinder("Alarm clock shell",c,(1.58,.65,.815),.116,.09,palette[0])
    clock.rotation_euler.x=math.pi/2
    dial=k.cylinder("Clock dial",c,(1.58,.60,.815),.093,.019,cream)
    dial.rotation_euler.x=math.pi/2
    k.tube("Alarm clock hands",c,[(1.56,.585,.856),(1.58,.585,.815),(1.632,.585,.800)],.008,indigo)
    for x in (1.505,1.655):
        k.ball("Alarm bell",c,(x,.65,.914),(.048,.043,.024),gold)
    practical_objects=set(c.objects)-before_practical
    practical=k.empty("Bedside table and amber lamp placement",c)
    for item in practical_objects:
        if item.parent is None:
            item.parent=practical
    practical.location=(-2.70,.12,0)
    window=k.emission("Twilight blue glass","#324d91",.85)
    box("Deep window frame",c,(-.97,2.32,1.83),(1.58,.22,1.43),wood,.038,True)
    box("Twilight window",c,(-.97,2.18,1.83),(1.46,.042,1.30),window,.024)
    for i in range(11):
        slat=box("Blue moonlight blind",c,(-.97,2.13,1.25+i*.116),(1.44,.10,.056),indigo,.008)
        slat.rotation_euler.x=.31
    sheer=k.surface("Blue sheer curtains","#697bb1",.9)
    shader=next(n for n in sheer.node_tree.nodes if n.type=="BSDF_PRINCIPLED")
    shader.inputs["Alpha"].default_value=.52
    sheer.surface_render_method="BLENDED"
    curtains=[]
    for s in (-1,1):
        points=[(-.97+s*(.60+.037*math.sin(z*2))+.023*j,2.075+.042*math.sin(j*1.38),1.19+.15*z)
                for z in range(10) for j in range(11)]
        faces=[(i,i+1,i+12,i+11) for i in range(98) if i%11!=10]
        curtains.append(k.mesh("Sheer window fabric",c,points,faces,sheer,smoothing=True))
    for j,x in enumerate((.27,.85,1.50)):
        z=1.98+.08*(j%2)
        box("Colored rocket and hero poster",c,(x,2.391,z),(.42,.034,.62),palette[j],.014,True)
        k.mesh("Poster rocket silhouette",c,[(x-.071,2.367,z-.18),(x+.088,2.367,z-.17),
               (x+.051,2.367,z+.083),(x,2.367,z+.19),(x-.055,2.367,z+.063)],[(0,1,2,3,4)],cream)
        k.ball("Poster porthole",c,(x,2.358,z+.037),(.038,.007,.038),palette[(j+3)%5],segments=12,rings=8)
    box("Toy display shelf",c,(.74,2.13,1.47),(1.84,.32,.084),wood,.026,True)
    for i in range(7):
        box("Shelf toys and books",c,(.04+i*.16,2.06,1.56),(.12,.135,.12+.04*(i%3)),palette[i%5],.019)
    k.cylinder("Little trophy stem",c,(1.40,2.03,1.58),.042,.18,gold)
    k.cylinder("Trophy cup",c,(1.40,2.03,1.70),.085,.12,gold,r2=.118)
    backpack=k.ball("School backpack rounded shell",c,(-1.47,1.91,.33),(.26,.17,.32),palette[0])
    backpack.rotation_euler.y=-.13
    box("School backpack pocket",c,(-1.49,1.759,.264),(.34,.11,.225),palette[2],.064,True)
    k.tube("Backpack handle",c,[(-1.55,1.89,.59),(-1.53,1.88,.70),(-1.43,1.88,.71),(-1.39,1.89,.62)],.021,cloth)
    rng=Random(82)
    for i in range(12):
        x=(-1 if i%2 else 1)*rng.uniform(.55,1.28)
        y=rng.uniform(-1.51,-.45)
        block=box("Painted toy block",c,(x,y,.062),(.115,.115,.12),palette[i%5],.014,True)
        block.rotation_euler.z=rng.uniform(-.9,.9)
    k.make_ricks_light("Cool indigo window key",c,(-1.16,1.92,2.55),(.04,-.4,.73),"#7A99FF",110,1.18)
    k.make_ricks_light("Warm bedside key",c,(-1.35,.02,1.70),(0,.12,1.15),"#FFAF4A",138,.98)
    k.make_ricks_light("Soft cool camera fill",c,(1.55,-1.88,2.55),(0,.1,1),"#B8CCFF",200,1.55)
    spill=k.make_ricks_light("Lime gas bounce",c,(-.61,-.16,1.11),(.17,.54,.94),"#6BFF4E",0,.69)
    return mattress,curtains,spill
