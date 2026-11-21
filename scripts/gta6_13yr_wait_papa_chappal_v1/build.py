"""Build an original two-set animated short in the shared Blender cel style."""
import bpy
import sys
import math
import random
import json
from pathlib import Path
from mathutils import Vector as V
from mathutils.geometry import tessellate_polygon

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[1]
OUT=ROOT/'renders'/HERE.name
GEOMETRY=ROOT/'scripts/project_paradox_india_ep03_5rs_blade/v04/geometry.py'
sys.path[:0]=[str(ROOT/'scripts'),str(GEOMETRY.parent)]
import ricks_lookdev as look
import geometry as G

S=bpy.context.scene
for obj in list(S.objects):
    bpy.data.objects.remove(obj,do_unlink=True)
data=json.loads((OUT/'timing.json').read_text(encoding='utf8'))
look.setup_scene(S,frame_end=data['frames'],samples=int(sys.argv[-1]) if sys.argv[-1].isdigit() else 32)
S.eevee.bokeh_max_size=10
S.render.image_settings.file_format='PNG'
S.render.image_settings.compression=10
S.render.use_sequencer=False

ink=G.emission('Marker ink','#16121C')
ink.use_backface_culling=True
dark=G.emission('Graphic ink','#211927')
skin=look.clean_toon('Warm cream face',stops=[(0,'#C4C8EA'),(.30,'#DFD9EC'),(.65,'#F3E5E6'),(1,'#FFF5EF')],light_min=.075,light_max=.40)
ivory=G.emission('Eyes and teeth','#FFF4E6')
sweat=G.emission('Blue sweat enamel','#80DFFE')
black=look.metal('Gunmetal trim','#222939',.28,.41,emission_strength=.12)
glass=look.metal('PC tempered glass','#6A92B8',.27,.18)
glass.node_tree.nodes['Principled BSDF'].inputs['Alpha'].default_value=.13
glass.surface_render_method='BLENDED'
cream=look.metal('Cooler ivory polymer','#ECDCC6',.01,.52,emission_strength=.20)
gold=look.metal('Satin gold hammered trim','#D6A657',.55,.31,emission_strength=.22)
silver=look.metal('Brushed fasteners','#7493A6',.5,.32,emission_strength=.20)
leather=look.metal('Spiced brown leather','#79452B',.03,.65,emission_strength=.24)
hoodie=look.clean_toon('Gamer slate hoodie',stops=[(0,'#141526'),(.36,'#282A48'),(.72,'#404467'),(1,'#616387')],light_min=.04,light_max=.43)
kurta=look.clean_toon('Papa cotton kurta',stops=[(0,'#686785'),(.40,'#A8A5BB'),(.74,'#E0D6D7'),(1,'#FFF2D5')],light_min=.06,light_max=.58)
hair=look.clean_toon('Ink black hair',stops=[(0,'#171220'),(.48,'#291F32'),(1,'#45384A')],light_min=.08,light_max=.48)
pink=G.emission('RGB blush','#F638A2',1.4)
cyan=G.emission('RGB turquoise','#42DEED',1.3)
violet=G.emission('RGB violet','#7865FA',1.15)
amber=G.emission('Hallway amber fixture','#FFD094',1.45)
red=G.emission('Alarm red','#ED4052',1.18)
white=G.emission('Paper warm white','#FFF1D0',.9)
viewport=G.emission('Blue display coal','#131E34')
soft=G.emission('Display neutral blue','#617B97')
bold=bpy.data.fonts.load('C:/Windows/Fonts/segoeuib.ttf')

def text(name, body, parent, pos, size, mat=white, align='CENTER'):
    font=bpy.data.curves.new(name,'FONT')
    font.body=body
    font.font=bold
    font.size=size
    font.align_x=align
    font.align_y='CENTER'
    font.extrude=.00035
    font.materials.append(mat)
    o=G.obj(name,font,parent)
    o.location=pos
    o.rotation_euler.x=math.pi/2
    return o

def box(name,parent,pos,size,mat,bevel=.026,ink_width=0):
    return G.cube(name,pos,size,mat,parent,bevel,ink_width)

def ring(name,parent,x,y,z,r,th,mat,xy=False,segments=32):
    t=[i*math.tau/segments for i in range(segments+1)]
    pts=[(x+r*math.cos(a),y+r*math.sin(a),z) if xy else (x+r*math.cos(a),y,z+r*math.sin(a)) for a in t]
    return G.line(name,pts,th,mat,parent)

def textile(name,a,b,scale):
    mat=look.metal(name,a,0,.67,emission_strength=.12)
    n,l=mat.node_tree.nodes,mat.node_tree.links
    xyz=n.new('ShaderNodeTexCoord')
    vec=n.new('ShaderNodeVectorMath')
    vec.operation='MULTIPLY'
    vec.inputs[1].default_value=scale
    l.new(xyz.outputs['Object'],vec.inputs[0])
    noise=n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=1
    noise.inputs['Detail'].default_value=2
    l.new(vec.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=look.rgba(a)
    ramp.color_ramp.elements[1].color=look.rgba(b)
    l.new(noise.outputs['Fac'],ramp.inputs[0])
    bs=n['Principled BSDF']
    l.new(ramp.outputs[0],bs.inputs['Base Color'])
    bump=n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.13
    bump.inputs['Distance'].default_value=.011
    l.new(noise.outputs['Fac'],bump.inputs['Height'])
    l.new(bump.outputs[0],bs.inputs['Normal'])
    return mat

wood=textile('Satin walnut grain','#402B2F','#9A5E40',(4,55,14))
paint=textile('Night blue wall plaster','#203859','#455779',(10,8,10))
pawnpaint=textile('Pawn amber plaster','#845145','#CA9260',(12,12,15))
pane=look.metal('Night window glass','#3A588A',.30,.24,emission_strength=.17)
carpet=textile('Indigo woven rug','#23293E','#444262',(79,91,96))
hall_mat=look.metal('Ochre hallway','#B7794D',0,.76,emission_strength=.32)

room=G.obj('Bedroom set');room['stage']=1
pawn=G.obj('Pawn shop set');pawn['stage']=0;pawn.location.x=-22
def timber_floor(root,mat):
    box(root.name+' floor',root,(0,-.4,-.11),(8,10,.22),mat,0)
    for i in range(19):
        x=(i-9)*.37
        G.line('Inlaid floor seam',[(x,-4.6,.001),(x,3.7,.001)],.004,black,root)

def area(name,root,pos,target,w,hue,size,shadow=True):
    lamp=G.light(name,'AREA',pos,target,w,hue,size)
    lamp.parent=root
    lamp.data.use_shadow=shadow
    return lamp

def spot(name,root,pos,target,w,hue,size=.15):
    lamp=G.light(name,'SPOT',pos,target,w,hue,size)
    lamp.parent=root
    lamp.data.spot_size=math.radians(62)
    return lamp

def support(name,root,pos,scale):
    o=G.sphere(name,pos,scale,G.emission(name+' matte occlusion','#161628'),root,16,8)
    look.mark_role(o,'ink')
    return o

# Pawn counter and the years montage occupy the same warm, dressed corner.
timber_floor(pawn,wood)
box('Pawn rear stucco',pawn,(0,2.25,1.68),(6.8,.20,3.36),pawnpaint)
box('Pawn left wall',pawn,(-3.42,.5,1.60),(.17,3.6,3.2),pawnpaint)
box('Pawn baseboard',pawn,(0,2.10,.17),(6.8,.14,.23),wood)
box('Pawn counter slab',pawn,(0,.48,1.00),(2.58,.88,.11),wood,.042,.006)
box('Pawn counter dark body',pawn,(0,.55,.51),(2.52,.69,.94),black,.05,.003)
for i in range(10):
    x=-1.14+i*.25
    box('Counter fluted cedar panel',pawn,(x,.195,.58),(.215,.035,.66),wood,.016)
box('Counter brass foot rail',pawn,(0,.175,.19),(2.6,.062,.063),gold,.017)
for z in (1.18,1.67,2.16):
    box('Pawn side shelf',pawn,(1.72,1.95,z),(1.66,.44,.065),wood)
    for i in range(4):
        x=1.11+i*.37
        h=.15+.055*((i+int(z*2))%3)
        box('Pawn vintage carton',pawn,(x,1.88,z+.06+h/2),(.26,.20,h),[black,leather,cream,silver][i],.014)
box('Pawn shop wall sign',pawn,(.85,2.08,2.78),(2.75,.11,.39),black,.04,.006)
text('Pawn shop lettering','LAST CHANCE PAWN',pawn,(.85,2.01,2.78),.145)
calendar=G.obj('Flip calendar',parent=pawn);calendar.location=(-.72,1.97,2.11)
box('Calendar hardback',calendar,(0,0,0),(1.00,.083,.83),black,.035,.006)
box('Calendar ivory sheet',calendar,(0,-.051,-.026),(.91,.026,.73),cream,.010)
box('Calendar hot top tab',calendar,(0,-.073,.253),(.91,.013,.16),red,.01)
text('Calendar title','THE WAIT',calendar,(0,-.084,.255),.103)
for i in range(14):
    text(f'Calendar year {2013+i}',str(2013+i),calendar,(0,-.074,.024),.262,dark)
for j in range(6):
    for k in range(3):
        box('Calendar grid rule',calendar,(-.31+j*.122,-.072,-.14-k*.061),(.089,.008,.026),silver,.004)
for x in (-.33,.33):
    ring('Calendar wire ring',calendar,x,-.057,.388,.052,.009,gold)
for i in range(6):
    page=box(f'Calendar flying paper {i}',pawn,(-.70,1.7,2.3),(.59,.010,.40),cream,.007)
    G.line('Paper ruled edge',[(-.245,-.008,.10),(.245,-.008,.10)],.007,red,page)

wait_screen=G.obj('Pawn waiting display',parent=pawn)
wait_screen.location=(-1.45,1.93,1.43)
box('Pawn vintage screen cabinet',wait_screen,(0,0,0),(.68,.17,.46),black,.052,.006)
box('Pawn vintage screen kinescope',wait_screen,(0,-.094,0),(.58,.021,.37),viewport,.028)
text('Pawn vintage screen text','LOADING',wait_screen,(0,-.111,.067),.078,cyan)
box('Pawn vintage load track',wait_screen,(0,-.111,-.064),(.445,.013,.029),soft,.009)
box('Pawn vintage load fill',wait_screen,(-.111,-.12,-.064),(.211,.013,.019),cyan,.007)
receipt=G.obj('Pawn receipt',parent=pawn);receipt.location=(.87,.20,1.135);receipt.rotation_euler.x=math.radians(29)
paper=box('Receipt paper',receipt,(0,0,.006),(.44,.27,.012),cream,.012,.002)
receipt_text=text('Receipt amount','₹2,00,000',receipt,(0,0,.015),.076,dark)
receipt_text.rotation_euler.x=0
G.line('Receipt rest rail',[(.66,.079,1.065),(1.08,.079,1.065)],.010,gold,pawn)
box('Card reader',pawn,(.99,.62,1.11),(.23,.25,.11),black,.042,.003)
box('Card reader screen',pawn,(.99,.585,1.172),(.13,.092,.011),cyan,.009)

cooler=G.obj('Kidney cooler',parent=pawn);cooler.location=(-.60,.40,1.055)
box('Cooler main shell',cooler,(0,0,.125),(.44,.30,.25),cream,.043,.005)
box('Cooler red lid',cooler,(0,0,.268),(.46,.32,.065),red,.023,.005)
G.line('Cooler handle',[(-.115,0,.300),(-.115,0,.385),(.115,0,.385),(.115,0,.300)],.021,black,cooler)
text('Cooler front label','KIDNEY',cooler,(0,-.153,.138),.084,dark)
G.obj('Cooler handle anchor',parent=cooler).location=(0,0,.386)
phone=G.obj('Old cracked phone',parent=pawn);phone.location=(.12,.27,1.065)
box('Phone dark case',phone,(0,0,0),(.13,.25,.028),black,.017,.004)
box('Phone cracked display glass',phone,(0,0,.017),(.116,.217,.010),pane,.008)
for points in [[(-.055,-.085,.024),(-.012,-.020,.024),(.044,.015,.024),(.057,.087,.024)],
               [(-.01,-.020,.024),(.021,-.064,.024),(.053,-.082,.024)]]:
    G.line('Cracked phone glazing',points,.0024,white,phone)
bangles=G.obj('Mothers bangles',parent=pawn);bangles.location=(.42,.38,1.065)
for i in range(3):
    ring('Engraved gold bangle',bangles,0,0,.015+i*.022,.082,.012,gold,xy=True,segments=30)
    ring('Bangle thin glint',bangles,0,0,.024+i*.022,.087,.002,white,xy=True,segments=32)

# Midnight bedroom, cool practicals, warm corridor and a genuine hinge opening.
timber_floor(room,wood)
box('Bedroom blue rug',room,(-.62,-.37,.012),(2.78,2.42,.024),carpet,.035)
box('Bedroom dark rear painted wall',room,(-.98,2.23,1.67),(4.30,.20,3.34),paint)
box('Bedroom right jamb wall',room,(3.22,2.23,1.65),(1.83,.20,3.30),paint)
box('Bedroom lintel wall',room,(1.40,2.23,2.85),(1.43,.20,.92),paint)
box('Bedroom right return',room,(3.93,-.83,1.57),(.19,5.98,3.16),paint)
box('Bedroom right base rail',room,(3.81,-.83,.14),(.085,5.95,.15),wood,.013)
box('Room left return',room,(-3.12,-.83,1.65),(.20,6.1,3.30),paint)
box('Room dark blue ceiling',room,(.43,-.66,3.37),(7.14,5.95,.18),paint)
box('Left wall lower walnut rail',room,(-3.00,-.83,.15),(.09,5.98,.22),wood,.017)
for pos in [(-2.995,-.97,1.78),(-2.995,.05,1.93)]:
    box('Side sound panel frame',room,pos,(.09,.68,.93),black,.029)
    box('Side sound panel woven insert',room,(pos[0]+.055,pos[1],pos[2]),(.025,.59,.83),carpet,.022)
    for i in range(6):
        box('Side sound panel acoustic rib',room,(pos[0]+.076,pos[1],pos[2]-.34+i*.135),(.02,.565,.025),wood,.007)
box('Corridor warm end wall',room,(1.71,3.68,1.63),(2.62,.19,3.30),hall_mat)
for y in (2.14,2.58,3.28):
    box('Hallway cornice',room,(1.39,y,2.41),(1.42,.09,.11),wood,.012)
for x in (.72,2.08):
    box('Door carved front jamb',room,(x,2.105,1.19),(.115,.24,2.38),wood,.018,.004)
box('Door carved lintel',room,(1.40,2.101,2.37),(1.48,.24,.13),wood,.023,.004)
box('Hallway warm floor threshold',room,(1.40,2.22,.025),(1.43,1.72,.05),hall_mat,.008)
door=G.obj('Room door hinge',parent=room);door.location=(2.035,2.11,0)
box('Bedroom door leaf',door,(-.638,.055,1.169),(1.276,.10,2.31),wood,.031,.007)
for z,h in ((.57,.76),(1.69,.87)):
    box('Bedroom door raised rail panel',door,(-.638,-.005,z),(1.02,.043,h),leather,.027,.003)
for z in (.38,1.85):
    G.cylinder('Visible hinge barrel',(0,-.019,z),(0,-.019,z+.14),.043,gold,door,20,.003)
G.sphere('Bedroom door brass spindle',(-1.122,-.075,1.064),(.064,.041,.062),gold,door,24,12,.003)
G.line('Turn latch lever',[(-1.16,-.119,1.065),(-1.045,-.119,1.065)],.023,gold,door)
G.obj('Door hand latch anchor',parent=door).location=(-1.08,-.124,1.065)
for z in (.14,2.94):
    box('Bedroom edging rail',room,(-1.0,2.105,z),(4.14,.10,.13),wood,.018)
box('Blue slatted window case',room,(-1.81,2.095,1.98),(1.43,.15,1.24),black,.027,.008)
box('Moonlit blue window glass',room,(-1.81,2.007,1.98),(1.32,.025,1.13),pane,.013)
for i in range(8):
    box('Window horizontal slate shade',room,(-1.81,1.970,1.54+i*.126),(1.31,.074,.049),black,.008)
box('Window middle bar',room,(-1.81,1.935,1.99),(.043,.055,1.15),silver,.006)
for x,z,w,h in [(-.51,2.37,.39,.51),(0,2.19,.43,.62),(-.51,1.75,.33,.37)]:
    box('Framed print walnut frame',room,(x,2.105,z),(w,.07,h),wood,.018,.003)
    box('Framed print neon art paper',room,(x,2.063,z),(w-.045,.014,h-.048),[violet,soft,red][int(z*10)%3],.009)
    for i in range(3):
        G.line('Print geometric wave',[(x-w*.34,2.051,z-h*.19+i*.058),(x,2.051,z+h*.16+i*.038),
                                      (x+w*.34,2.051,z-h*.15+i*.055)],.008,black,room)
for z in (1.31,1.78):
    box('Bedroom floating shelf',room,(-2.46,1.86,z),(1.07,.34,.067),wood,.014)
    for i in range(5):
        x=-2.87+i*.16
        h=.12+(i%3)*.053
        box('Shelf book and collector case',room,(x,1.86,z+.04+h/2),(.132,.19,h),[leather,black,cream,silver,violet][i],.01)

desk=G.obj('Walnut desk',parent=room);desk.location=(-.67,.76,0)
box('Walnut satin desktop',desk,(0,0,.932),(2.75,.96,.10),wood,.054,.008)
box('Desk front black inlay',desk,(0,-.468,.895),(2.65,.04,.067),black,.018)
for x in (-1.22,1.22):
    for y in (-.36,.34):
        box('Desk square tube leg',desk,(x,y,.45),(.076,.084,.90),black,.015)
        box('Desk rubber foot',desk,(x,y,.027),(.105,.12,.054),black,.012)
box('Desk rear cable raceway',desk,(0,.31,.79),(2.39,.17,.17),black,.024)
box('Wide stitched keyboard mat',room,(-.68,.57,.987),(1.40,.49,.018),carpet,.043,.003)

chair=G.obj('Gaming chair',parent=room);chair.location=(-.67,-.35,0)
box('Chair blue padded seat',chair,(0,0,.54),(.60,.61,.15),black,.075,.005)
box('Chair sculpted high back',chair,(0,-.26,.93),(.63,.138,.88),black,.072,.006)
box('Chair magenta lumbar insert',chair,(0,-.179,.90),(.31,.050,.44),violet,.045,.004)
for x in (-.263,.263):
    G.line('Chair piping',[(x,-.17,.70),(x,-.17,1.13),(x*.78,-.171,1.30)],.014,pink,chair)
for x in (-.35,.35):
    box('Chair arm upright',chair,(x,-.05,.642),(.059,.075,.25),black,.018)
    box('Chair arm cushion',chair,(x,.02,.775),(.103,.35,.070),black,.028,.003)
G.cylinder('Chair load-bearing spindle',(0,0,.12),(0,0,.47),.052,silver,chair,20)
for i in range(5):
    a=math.tau*i/5
    x,y=.34*math.cos(a),.34*math.sin(a)
    G.line('Chair star base leg',[(0,0,.148),(x,y,.098)],.031,black,chair)
    G.sphere('Chair grounded rubber caster',(x,y,.048),(.077,.053,.047),black,chair,20,10,.003)
    support('Small caster contact',chair,(x,y,.002),(.086,.061,.003))

def tower(name,parent,pos):
    t=G.obj(name,parent=parent);t.location=pos
    box(name+' aluminium housing',t,(0,.026,.305),(.38,.32,.61),black,.040,.007)
    box(name+' glass side',t,(0,-.164,.308),(.345,.018,.546),glass,.015)
    for obj in t.children:
        if 'glass side' in obj.name:obj.visible_shadow=False
    box(name+' rear backlight',t,(0,-.142,.304),(.32,.013,.53),viewport,.018)
    for i,z in enumerate((.148,.31,.482)):
        G.cylinder('PC intake fan hub',(.064,-.173,z),(.064,-.198,z),.060,black,t,24)
        ring('RGB fan diffuser',t,.064,-.200,z,.068,.010,(cyan,pink,violet)[i])
        for j in range(5):
            a=j*math.tau/5
            G.line('Fan blade',[(.064,-.205,z),(.064+.043*math.cos(a+.3),-.205,z+.048*math.sin(a+.3))],.009,soft,t)
    box('PC GPU board',t,(-.056,-.192,.188),(.20,.045,.051),black,.008,.003)
    G.line('PC cooling tube cyan',[(-.12,-.218,.195),(-.124,-.216,.381),(-.063,-.216,.439),(-.020,-.216,.401)],.013,cyan,t)
    G.line('PC cooling tube pink',[(-.10,-.214,.195),(-.105,-.214,.361),(-.054,-.214,.415),(-.013,-.214,.387)],.011,pink,t)
    box('PC soft power diode',t,(-.126,-.198,.546),(.039,.019,.018),cyan,.004)
    return t

tower('Bedroom RGB tower',room,(.46,1.008,.986))
tower('Pawn RGB PC reveal',pawn,(.70,.51,1.055))

clock=G.obj('Desk digital clock',parent=room);clock.location=(-1.61,.52,1.052)
box('Clock bevel',clock,(0,0,0),(.39,.19,.13),black,.031,.006)
box('Clock smoke glass',clock,(0,-.101,0),(.335,.012,.091),viewport,.016)
text('Clock before midnight','11:59',clock,(0,-.111,0),.080,red)
text('Clock at midnight','12:00 AM',clock,(0,-.111,0),.056,cyan)

keyboard=G.obj('RGB keyboard',parent=room);keyboard.location=(-.81,.57,1.018)
box('Keyboard inset shell',keyboard,(0,0,0),(.68,.25,.046),black,.021,.004)
box('Keyboard lower light pipe',keyboard,(0,0,-.016),(.65,.238,.013),violet,.009)
for j in range(4):
    for i in range(11):
        x=-.280+.056*i
        y=-.085+.054*j
        name='ALT key' if (j,i)==(0,2) else 'TAB key' if (j,i)==(2,0) else 'Enter key' if (j,i)==(1,10) else f'Keyboard key {j}_{i}'
        box(name,keyboard,(x,y,.030),(.045,.043,.029),[cyan,violet,soft,pink][(i+j)%4],.006)
for name,word in [('ALT key','ALT'),('TAB key','TAB')]:
    label=text(name+' lettering',word,bpy.data.objects[name],(0,0,.017),.013,dark)
    label.rotation_euler.x=0
mouse=G.obj('RGB mouse grip',parent=room);mouse.location=(-.18,.555,1.040)
G.sphere('Gaming mouse shell',(0,0,0),(.073,.114,.044),black,mouse,28,14,.004)
G.line('RGB mouse seam',[(0,-.088,.029),(0,-.039,.044),(0,.042,.035)],.006,pink,mouse)
G.sphere('Mouse wheel',(0,.012,.041),(.020,.026,.018),silver,mouse,16,8)

# Screen graphics and original miniature beach art built in depth on the display.
mon=G.obj('Curved widescreen monitor',parent=room);mon.location=(-.66,1.011,1.42)
box('Monitor foot',mon,(0,.12,-.418),(.46,.38,.045),black,.042,.005)
box('Monitor support strut',mon,(0,.13,-.22),(.098,.089,.43),black,.013,.004)
box('Monitor matte bevel',mon,(0,0,0),(1.42,.16,.77),black,.045,.010)
box('Monitor underglow edge',mon,(0,-.073,-.354),(1.34,.019,.025),pink,.009)
for side in (-1,1):
    box('Curved swept display side',mon,(side*.687,-.068,0),(.063,.095,.724),black,.032)
screen=G.obj('Display artwork',parent=mon);screen.location.y=-.093
box('Monitor lit face',screen,(0,0,0),(1.30,.015,.665),viewport,.014)

def display_box(name,parent,x,z,w,h,mat,layer=.012):
    return box(name,parent,(x,-layer,z),(w,.003,h),mat,.004)

loading=G.obj('Loading display',parent=screen)
text('Game preflight headline','NIGHT DRIVE VI',loading,(0,-.028,.12),.11,cyan)
text('Loading status','CONNECTING',loading,(0,-.027,-.02),.055,white)
display_box('Boot progress background',loading,0,-.133,1.02,.038,soft)
display_box('Boot progress fill',loading,-.12,-.133,.75,.019,cyan,.019)

beach=G.obj('Original beach display',parent=screen)
sky=[G.emission('Beach pastel sky '+str(i),c) for i,c in enumerate(('#FAAE8B','#F8C48E','#F7D893','#F5E8B4','#9BE2EC','#83D2EF','#72C4E6','#79BDEA'))]
for i,m in enumerate(sky):
    display_box('Original beach sky strip',beach,0,-.04+i*.046,1.297,.047,m)
sea=G.emission('Beach jade sea','#45BCCA')
sea2=G.emission('Beach surf light','#8EE5DF')
sand=G.emission('Beach ivory sand','#F8D59A')
sun=G.emission('Beach pale sun','#FFF1BD')
palm=G.emission('Palm deep silhouettes','#244952')
display_box('Sea horizon',beach,0,-.105,1.296,.153,sea,.014)
display_box('Beach sand strip',beach,0,-.247,1.296,.166,sand,.016)
G.sphere('Beach sunset',(-.264,-.017,.143),(.071,.002,.071),sun,beach,28,14)
for i in range(8):
    x=-.57+i*.158
    z=-.137+(.017*i% .045)
    G.line('Blue foam streak',[(x,-.020,z),(x+.095,-.020,z+.011)],.004,sea2,beach)
for j,(x,z,k) in enumerate([(-.49,-.22,1),(.46,-.20,.86),(.59,-.17,.55)]):
    tip=V((x+.061*k,-.026,z+.40*k))
    G.line('Island palm curved trunk',[(x,-.025,z),(x+.015*k,-.025,z+.19*k),tip],.009*k,palm,beach)
    for i in range(7):
        a=math.pi*.05+math.pi*.91*i/6
        step=V((math.cos(a)*.111*k,0,math.sin(a)*.084*k))
        end=tip+step+V((0,0,-.055*k))
        G.line('Island palm hanging frond',[tip,tip+step*.62+V((0,0,.024*k)),end],.009*k,palm,beach)
boardwalk=G.emission('Terracotta boardwalk','#CB8E7F')
for i in range(12):
    display_box('Boardwalk pier seam',beach, -.591+i*.108,-.299,.093,.049,boardwalk,.021)

performer=G.obj('Original beach walker',parent=beach);performer.location=(.06,-.045,-.278)
rose=G.emission('Beach jacket coral','#F5537E')
mint=G.emission('Beach shorts mint','#47D1BD')
tan=G.emission('Beach figure tan','#CC855F')
G.sphere('Beach figure animated head',(0,0,.341),(.047,.033,.052),tan,performer,24,14,.002)
G.sphere('Beach figure copper hair',(0,.005,.368),(.051,.032,.036),leather,performer,22,10,.002)
G.loft('Beach figure dimensional jacket',[(.137,.033,.023),(.186,.046,.030),(.245,.043,.028),(.271,.029,.022)],rose,performer,20,.003)
box('Beach figure round waist',performer,(0,0,.139),(.076,.045,.058),mint,.019,.002)
G.line('Beach figure necklace',[(-.026,-.028,.246),(0,-.037,.229),(.026,-.028,.246)],.003,gold,performer)
for i in (-1,1):
    G.sphere('Beach sunglasses',(i*.020,-.032,.347),(.021,.004,.013),dark,performer,16,8)
    ring('Beach gold hoop',performer,i*.046,-.020,.313,.014,.003,gold,segments=18)
    G.line(f'Beach walker arm {i}',[(i*.035,0,.244),(i*.057,-.002,.196),(i*.044,-.005,.157)],.011,tan,performer)
    G.line(f'Beach walker leg {i}',[(i*.023,0,.135),(i*.026,0,.061),(i*.029,-.003,.013)],.013,tan,performer)
    G.sphere(f'Beach walker shoe {i}',(i*.025,-.012,.015),(.018,.022,.014),white,performer,12,6)

display_box('Original mission plaque',beach,-.428,.266,.38,.065,viewport,.028)
text('Original mission prompt','BEACH RUN',beach,(-.428,-.033,.266),.045,white)
error=G.obj('Freeze warning popup',parent=screen)
display_box('Freeze warning shell',error,0,.036,1.108,.259,white,.081)
display_box('Freeze warning header strip',error,0,.127,1.108,.075,red,.085)
text('Freeze warning title','NOT RESPONDING',error,(0,-.090,.13),.079,white)
text('Freeze warning message','ALT + TAB   /   WAIT',error,(0,-.091,.015),.047,dark)

text('Original display fidelity badge','UHD',beach,(.547,-.035,.266),.042,white)

# Transparent tapered graphic smoke from the frozen controls.
smoke=bpy.data.materials.new('Keyboard smoke translucent')
smoke.use_nodes=True
smoke.surface_render_method='BLENDED'
nodes,links=smoke.node_tree.nodes,smoke.node_tree.links
nodes.clear()
mix=nodes.new('ShaderNodeMixShader')
transparent=nodes.new('ShaderNodeBsdfTransparent')
cloud=nodes.new('ShaderNodeEmission')
cloud.inputs[0].default_value=look.rgba('#BCD1F7')
uv=nodes.new('ShaderNodeTexCoord')
sep=nodes.new('ShaderNodeSeparateXYZ')
fade=nodes.new('ShaderNodeValToRGB')
fade.color_ramp.elements[0].color=(.002,.002,.002,1)
fade.color_ramp.elements[1].color=(0,0,0,1)
fade.color_ramp.elements.new(.39).color=(.27,.27,.27,1)
links.new(uv.outputs['Generated'],sep.inputs[0])
links.new(sep.outputs['Z'],fade.inputs[0])
links.new(fade.outputs[0],mix.inputs[0])
links.new(transparent.outputs[0],mix.inputs[1]);links.new(cloud.outputs[0],mix.inputs[2])
links.new(mix.outputs[0],nodes.new('ShaderNodeOutputMaterial').inputs[0])
for k in range(3):
    verts=[]
    for i in range(11):
        u=i/10;cx=.038*math.sin(u*4.4+k)
        w=.045*max(.001,math.sin(math.pi*u))
        verts.extend([(cx-w,0,u*.26),(cx+w,0,u*.26)])
    obj=G.mesh(f'Keyboard fault smoke {k}',verts,[(2*i,2*i+1,2*i+3,2*i+2) for i in range(10)],smoke,room,smooth=False)
    look.mark_role(obj,'wisp')

# Glossy packet with visible seam, separate rip strip and surface grips.
bag=G.obj('Chips packet',parent=room);bag.location=(-1.49,.22,.989)
chips_orange=look.metal('Crinkled coral chip wrapper','#ED552B',.32,.37,emission_strength=.27)
box('Chip bag crimped pillow',bag,(0,0,.113),(.236,.094,.232),chips_orange,.038,.005)
box('Chip bag bottom seal',bag,(0,0,.010),(.243,.068,.031),gold,.009)
box('Chip bag rip seal',bag,(0,0,.231),(.245,.067,.036),gold,.007,.003)
text('Chip bag printed brand','CRUNCH',bag,(0,-.055,.135),.059,white)
for i in range(6):
    x=-.09+(i%3)*.09
    box(f'Airborne potato chip {i}',room,(x,0,.7),(.052,.015,.038),gold,.012)
G.obj('Bag left seam grip',parent=bag).location=(-.104,-.014,.168)
G.obj('Bag right seam grip',parent=bag).location=(.104,-.014,.168)

# Lightweight dimensional cast, with deliberately graphic hands and features.
def facepoint(x,z,extra=.004):
    r=.305*G.rough(math.atan2(-z,x))
    return x,-.072*math.sqrt(max(.03,1-(x*x+z*z)/(r*r)))-extra,z
G.facepoint=facepoint

def make_actor(name,parent,is_papa=False):
    root=G.obj(name,parent=parent)
    body=G.obj(name+' torso rig',parent=root)
    head=G.obj(name+' head pivot',parent=body);head.location.z=1.51
    skull=G.sphere(name+' rough cream skull',(0,0,0),(.305,.072,.305),skin,head,48,20)
    for v in skull.data.vertices:
        rr=G.rough(math.atan2(-v.co.z,v.co.x))
        v.co.x*=rr
        v.co.z*=rr
    G.ink(skull,.011)
    top=kurta if is_papa else hoodie
    G.loft(name+' shaped cotton top',[(.64,.18,.102),(.76,.233,.122),(1.07,.247,.115),(1.15,.195,.096),(1.20,.095,.071)],top,body,36,.008)
    G.sphere(name+' connected neck',(0,0,1.209),(.096,.076,.095),top,body,24,12,.006)
    if is_papa:
        G.line('Kurta centre placket',[(0,-.098,1.17),(0,-.124,1.03),(0,-.13,.83)],.011,ivory,body)
        for i in range(4):
            G.sphere('Kurta small button',(0,-.138,1.12-i*.064),(.012,.006,.013),silver,body,12,6)
        G.patch(name+' mustache',[(-.120,-.062),(-.075,-.050),(-.025,-.061),(0,-.068),(.023,-.061),(.077,-.047),
                                  (.118,-.066),(.100,-.095),(.048,-.087),(0,-.080),(-.053,-.105),(-.102,-.094)],dark,head,.013)
    else:
        G.loft('Gamer hood rim',[(1.107,.175,.108),(1.153,.182,.125),(1.202,.116,.106)],hoodie,body,28,.004)
        for side in (-1,1):
            G.line('Hoodie cotton drawstring',[(side*.08,-.104,1.12),(side*.093,-.123,1.00),(side*.076,-.125,.92)],.006,silver,body)
        G.line('Hoodie pocket stitched lip',[(-.146,-.108,.84),(-.089,-.126,.795),(.089,-.126,.795),(.146,-.108,.84)],.009,black,body)
        hair_pts=[(-.278,.106),(-.273,.221),(-.206,.285),(-.087,.294),(-.039,.324),(.023,.291),(.108,.321),
                  (.151,.278),(.237,.282),(.266,.196),(.291,.131),(.197,.163),(.157,.120),(.059,.181),
                  (.010,.128),(-.063,.195),(-.117,.142),(-.176,.181),(-.227,.105)]
        coords=[facepoint(x,z,.010) for x,z in hair_pts]
        # Tessellate the flat drawing first and wrap every subdivided triangle onto the head.
        outline=[V((x,0,z)) for x,z in hair_pts]
        triangles=[tuple(outline[i] for i in tri) for tri in tessellate_polygon([outline])]
        for _ in range(3):
            refined=[]
            for a,b,c in triangles:
                ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
                refined.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
            triangles=refined
        fitted=[facepoint(v.x,v.z,.013) for tri in triangles for v in tri]
        G.mesh('Messy asymmetrical pointed fringe',fitted,
               [tuple(range(i,i+3)) for i in range(0,len(fitted),3)],hair,head,smooth=False)
        G.line('Hair bold outer ink',[V(co)+V((0,-.004,0)) for co in coords+[coords[0]]],.008,dark,head)
        G.sphere('Back of gamer hair',(0,.054,.043),(.290,.092,.253),hair,head,32,16,.004)
        headphones=G.obj('RGB headset worn',parent=head)
        G.line('Headset arched crown',[(-.302,-.001,.063),(-.276,.009,.208),(-.18,.016,.299),(0,.020,.341),
                  (.18,.014,.293),(.268,.002,.199),(.30,-.004,.051)],.028,black,headphones)
        for side in (-1,1):
            G.sphere('Headset cushioned ear cup',(side*.296,-.005,.020),(.050,.070,.099),black,headphones,24,14,.005)
            G.line('RGB headphone diffuser',[(side*.300,-.066,-.046),(side*.324,-.065,.007),(side*.314,-.061,.063)],.012,
                   cyan if side<0 else pink,headphones)
        G.line('Microphone curved boom',[(.299,-.037,-.007),(.258,-.074,-.064),(.182,-.097,-.087)],.011,black,headphones)
    for side in (-1,1):
        G.line(f'{name} arm {side}',[(0,0,.95)]*20,.024 if is_papa else .027,dark,root)
        G.line(f'{name} leg {side}',[(0,0,.49)]*20,.027 if is_papa else .033,dark,root)
        hand=G.obj(f'{name} hand {side}',parent=root)
        G.sphere('Graphic palm',(0,0,0),(.056,.017,.052),dark,hand,24,12)
        for j in range(2):
            G.line('Graphic fingers along grip',[(.016,-.018,-.023+j*.022),(.044,-.018,-.027+j*.022),(.055,-.013,-.019+j*.022)],.010,dark,hand)
        G.sphere(f'{name} sole {side}',(0,0,.067),(.077,.130,.059),black,root,24,12,.004)
        mark=support(f'{name} grounded contact {side}',root,(side*.13,0,.002),(.105,.149,.002))
        r=side*.105
        G.oval(f'{name} eye white {side}',r,.026,.048,.056,ivory,head,.012)
        G.oval(f'{name} pupil {side}',r,.026,.023,.039,dark,head,.016)
        G.oval(f'{name} eye catch {side}',r-.006,.044,.008,.010,ivory,head,.019)
        G.faceline(f'{name} blink {side}',[(r-.037,.023),(r,.015),(r+.037,.022)],.008,dark,head)
        G.faceline(f'{name} eyebrow {side}',[(r-.038,.110),(r,.124),(r+.043,.106)],.010,dark,head)
        if not is_papa:
            G.faceline(f'{name} tired bag {side}',[(r-.042,-.031),(r,-.042),(r+.038,-.033)],.007,soft,head)
            G.line(f'{name} eye neon {side}',[facepoint(r-.015,.063,.020),facepoint(r+.003,.083,.020),
                   facepoint(r+.020,.074,.020)],.006,cyan if side<0 else pink,head)
        else:
            rx=.077;z=.036
            G.line('Papa rectangular glasses',[facepoint(r-rx,z-.049,.026),facepoint(r+rx,z-.049,.026),facepoint(r+rx,z+.050,.026),
                        facepoint(r-rx,z+.050,.026),facepoint(r-rx,z-.049,.026)],.010,dark,head)
    if is_papa:
        G.faceline('Papa spectacles bridge',[(-.030,.04),(0,.051),(.030,.04)],.008,dark,head)
    G.faceline(name+' closed mouth',[(-.061,-.113),(0,-.136 if not is_papa else -.121),(.060,-.104 if not is_papa else -.142)],.009,dark,head)
    G.oval(name+' wide mouth',0,-.115,.074,.076,dark,head,.010)
    G.patch(name+' upper teeth',[(-.051,-.079),(.051,-.079),(.040,-.093),(-.039,-.093)],ivory,head,.015)
    G.oval(name+' speaking mouth',0,-.12,.064,.040,dark,head,.014)
    for i in range(4):
        G.mesh(f'{name} sweat {i}',[(0,0,.049),(.024,0,-.010),(.019,0,-.027),(0,0,-.034),
               (-.020,0,-.027),(-.025,0,-.010)],[(0,1,2,3,4,5)],sweat,head,smooth=False)
    return root

make_actor('Pawn Gamer',pawn)
make_actor('Gamer',room)
make_actor('Papa',room,True)

def slipper(name,parent,pos):
    root=G.obj(name,parent=parent);root.location=pos
    G.sphere(name+' grounded leather sole',(0,0,.026),(.092,.18,.029),leather,root,28,16,.005)
    G.line(name+' rounded toe strap',[(-.079,-.056,.047),(-.062,-.053,.083),(0,-.046,.101),(.062,-.053,.083),(.079,-.056,.047)],.021,leather,root)
    G.line(name+' gold double stitch',[(-.064,-.062,.088),(0,-.055,.112),(.064,-.061,.089)],.005,gold,root)
    G.obj(name+' hand seat',parent=root).location=(0,-.044,.100)
    return root

slipper('Papa right chappal',room,(1.45,.84,0))
slipper('Papa left chappal',room,(1.79,.88,0))

def stars(name,parent):
    pts=[]
    for i in range(10):
        angle=math.pi/2+math.pi*i/5
        r=.096 if i%2==0 else .044
        pts.append((r*math.cos(angle),0,r*math.sin(angle)))
    star=G.mesh(name,pts,[tuple(range(10))],gold,parent,smooth=False)
    G.line('Wanted star dark keyline',pts+[pts[0]],.008,dark,star)
    return star

wanted=G.obj('Wanted star cluster',parent=room)
for i in range(5):
    star=stars(f'Original wanted star {i}',wanted)
    star.location.x=(i-2)*.211
    star.data.materials[0]=amber

# Lights have separate stage ownership, and practical changes are baked by the runtime.
for light in S.objects:
    if light.get('ricks_light'):
        light.hide_render=light.hide_viewport=True
area('Pawn overhead amber',pawn,(-1.7,-1.7,3.20),(0,.65,1.10),330,'#FFE1B0',2.0)
area('Pawn copper bounce',pawn,(1.9,-.7,2.42),(0,.7,1.2),72,'#D48766',1.75,False)
spot('Pawn counter reflection',pawn,(.57,.63,2.57),(.24,.39,1.043),92,'#FFF0D2')
area('Bedroom cool key',room,(-2.9,-.7,3.01),(-.25,.1,1.24),210,'#9FAFEF',2.17)
area('Bedroom quiet lavender fill',room,(2.5,-1.4,2.81),(-.55,-.1,1.1),64,'#B4A2EE',2.3,False)
area('Bedroom high neutral eye key',room,(.35,-1.3,2.73),(-.53,-.21,1.25),97,'#FFEDE0',1.77,False)
spot('Cool diagonal window beam',room,(-1.9,1.86,2.51),(-.92,-.9,.4),132,'#AECCFF',.15)
area('Door hallway practical',room,(1.47,2.88,2.76),(1.18,.35,1.02),254,'#FFD78B',1.10)
area('Door rim to Papa',room,(1.4,2.66,1.96),(1.18,.55,1.34),99,'#FEB461',.90,False)
area('TV warm pink bounce',room,(-.71,.48,1.58),(-.68,-.36,1.30),42,'#FF75BD',.67,False)
area('TV cold cyan bounce',room,(-.34,.40,1.36),(-.72,-.29,1.29),28,'#6FDFEE',.53,False)
area('Siren warm sweep',room,(2.59,-.30,2.36),(-.03,.24,1.24),0,'#F5444F',1.05,False)
area('Siren cool sweep',room,(-2.4,-.20,2.31),(.45,-.14,1.24),0,'#476EFF',1.18,False)
box('Hallway wall lamp',room,(1.56,3.54,1.98),(.36,.055,.27),amber,.041,.004)

cam_data=bpy.data.cameras.new('Shot lens')
cam=G.obj('Story camera',cam_data)
S.camera=cam
focus=G.obj('Optical focus')
look.configure_camera(cam,focus,45,3.2)
# Independent screen graphics. The banner is authored as original typography.
banner=G.obj('Last frame original warning',parent=cam)
banner.location=(0,-.080,-.78)
banner.scale=(.486,.486,.486)
wanted.parent=cam
wanted.location=(0,.216,-.73)
wanted.rotation_euler.x=-math.pi/2
wanted.scale=(.27,.27,.27)
black_banner=box('Screen graphic warning backplate',banner,(0,0,0),(.64,.145,.004),viewport,.02)
for x in (-.30,.30):
    box('Screen graphic red side rule',banner,(x,0,.004),(.012,.115,.005),red,.003)
busted=text('Original BUSTED graphic','BUSTED',banner,(0,.004,.010),.122,red)
busted.rotation_euler.x=0

for n in list(S.node_tree.nodes):
    if n.type=='MATH' and n.operation=='MULTIPLY' and abs(n.inputs[1].default_value-.45)<.005:
        n.inputs[1].default_value=.15
comp=next(n for n in S.node_tree.nodes if n.type=='COMPOSITE')
tree=S.node_tree; original=comp.inputs[0].links[0].from_socket
sink=tree.nodes.new('CompositorNodeHueSat')
sink.name='Payoff grade'
tree.links.new(original,sink.inputs['Image'])
color_parts=tree.nodes.new('CompositorNodeSeparateColor')
tree.links.new(original,color_parts.inputs[0])
others=tree.nodes.new('CompositorNodeMath');others.operation='MAXIMUM'
tree.links.new(color_parts.outputs[1],others.inputs[0]);tree.links.new(color_parts.outputs[2],others.inputs[1])
subtract=tree.nodes.new('CompositorNodeMath');subtract.operation='SUBTRACT'
tree.links.new(color_parts.outputs[0],subtract.inputs[0]);tree.links.new(others.outputs[0],subtract.inputs[1])
mask=tree.nodes.new('CompositorNodeMath');mask.operation='GREATER_THAN';mask.inputs[1].default_value=.47
tree.links.new(subtract.outputs[0],mask.inputs[0])
protect=tree.nodes.new('CompositorNodeMixRGB')
# Protect the red graphic without isolating the orange spill or neutral set edges.
g_minus_b=tree.nodes.new('CompositorNodeMath')
g_minus_b.operation='SUBTRACT'
tree.links.new(color_parts.outputs[1],g_minus_b.inputs[0])
tree.links.new(color_parts.outputs[2],g_minus_b.inputs[1])
true_red=tree.nodes.new('CompositorNodeMath')
true_red.operation='LESS_THAN'
true_red.inputs[1].default_value=.031
tree.links.new(g_minus_b.outputs[0],true_red.inputs[0])
select_red=tree.nodes.new('CompositorNodeMath')
select_red.operation='MULTIPLY'
tree.links.new(true_red.outputs[0],select_red.inputs[0])
tree.links.new(mask.outputs[0],select_red.inputs[1])
tree.links.new(select_red.outputs[0],protect.inputs[0])
tree.links.new(sink.outputs[0],protect.inputs[1])
tree.links.new(original,protect.inputs[2])
tree.links.new(protect.outputs[0],comp.inputs[0])
blueprint=OUT/'timing.json'
data_paths={'geometry.py':GEOMETRY,'ricks_lookdev.py':ROOT/'scripts/ricks_lookdev.py','runtime.py':HERE/'runtime.py','timing.json':blueprint}
for name,path in data_paths.items():
    bpy.data.texts.new(name).from_string(path.read_text(encoding='utf-8-sig'))
bootstrap="""import sys,types,bpy
for name in ('ricks_lookdev','geometry','runtime'):
    mod=types.ModuleType(name);sys.modules[name]=mod
    exec(compile(bpy.data.texts[name+'.py'].as_string(),name+'.py','exec'),mod.__dict__)
sys.modules['runtime'].register()
"""
bpy.data.texts.new('START_HERE.py').from_string(bootstrap)
seq=S.sequence_editor_create()
seq.sequences.new_sound('Original Hindi narration and original foley',str(OUT/'final_mix.wav'),channel=1,frame_start=1).sound.pack()
bpy.ops.file.pack_all()
exec(bootstrap)
S.frame_set(1)
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'gta6_13yr_wait_papa_chappal_v1.blend'))
