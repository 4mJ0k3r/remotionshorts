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
sys.path[:0]=[str(HERE),str(ROOT/'scripts'),str(GEOMETRY.parent)]
import ricks_lookdev as look
import geometry as G
import tailoring

S=bpy.context.scene
for obj in list(S.objects):
    bpy.data.objects.remove(obj,do_unlink=True)
data=json.loads((OUT/'timing.json').read_text(encoding='utf8'))
look.setup_scene(S,frame_end=data['frames'],samples=int(sys.argv[-1]) if sys.argv[-1].isdigit() else 32)
S.eevee.bokeh_max_size=10
S.eevee.use_raytracing=False
S.render.image_settings.file_format='PNG'
S.render.image_settings.compression=0
S.render.use_sequencer=False

ink=G.emission('Marker ink','#07070A')
ink.use_backface_culling=True
dark=G.emission('Graphic ink','#07070A')
fold=G.emission('Cotton crease ink','#151521')
skin=look.clean_toon('Warm cream face',stops=[(0,'#C4C8EA'),(.30,'#DFD9EC'),(.65,'#F3E5E6'),(1,'#FFF5EF')],light_min=.08,light_max=.78)
# Keep the face drawn but give the curved skull a broad, readable sidewall.
tree=skin.node_tree; sn,sl=tree.nodes,tree.links
emitter=next(n for n in sn if n.type=='EMISSION')
received=emitter.inputs['Color'].links[0].from_socket
coordinates=sn.new('ShaderNodeTexCoord'); axis=sn.new('ShaderNodeSeparateXYZ')
sl.new(coordinates.outputs['Generated'],axis.inputs[0])
wrap=sn.new('ShaderNodeValToRGB')
for j,(at,color) in enumerate(((0,'#777DB2'),(.21,'#CBCBE6'),(.45,'#FFF5EF'),(.73,'#FAE4D7'),(1,'#A8A1CA'))):
    el=wrap.color_ramp.elements[j] if j<2 else wrap.color_ramp.elements.new(at)
    el.position=at;el.color=look.rgba(color)
wrap.color_ramp.interpolation='EASE'
sl.new(axis.outputs['X'],wrap.inputs[0])
shading=sn.new('ShaderNodeMixRGB');shading.inputs[0].default_value=.56
sl.new(received,shading.inputs[1]);sl.new(wrap.outputs[0],shading.inputs[2])
screen_rim=sn.new('ShaderNodeValToRGB')
for j,(at,color) in enumerate(((0,'#E24A9F'),(.19,'#F1A2CD'),(.49,'#FFF2EF'),(.76,'#C3F5F7'),(1,'#52C9F8'))):
    el=screen_rim.color_ramp.elements[j] if j<2 else screen_rim.color_ramp.elements.new(at)
    el.position=at;el.color=look.rgba(color)
screen_rim.color_ramp.interpolation='EASE'
sl.new(axis.outputs['X'],screen_rim.inputs[0])
grade=sn.new('ShaderNodeMixRGB');grade.name='Monitor face reflection';grade.inputs[0].default_value=0
sl.new(shading.outputs[0],grade.inputs[1]);sl.new(screen_rim.outputs[0],grade.inputs[2])
sl.new(grade.outputs[0],emitter.inputs['Color'])
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
hoodie=look.clean_toon('Gamer slate hoodie',stops=[(0,'#232836'),(.47,'#2D3446'),(.61,'#414959'),(1,'#50576A')],light_min=.12,light_max=1.14)
kurta=look.clean_toon('Papa cotton kurta',stops=[(0,'#858096'),(.36,'#B5A9AC'),(.60,'#D1C1AA'),(1,'#EADDC4')],light_min=.13,light_max=.95)
trousers=G.emission('Matte charcoal trousers','#313445')
hood_nodes,hood_links=hoodie.node_tree.nodes,hoodie.node_tree.links
hood_emission=next(node for node in hood_nodes if node.type=='EMISSION')
hood_base=hood_emission.inputs['Color'].links[0].from_socket
hood_layer=hood_nodes.new('ShaderNodeLayerWeight')
hood_rim=hood_nodes.new('ShaderNodeMath');hood_rim.operation='SUBTRACT';hood_rim.inputs[0].default_value=1
hood_links.new(hood_layer.outputs['Facing'],hood_rim.inputs[1])
hood_weight=hood_nodes.new('ShaderNodeValue');hood_weight.name='Neon wardrobe reflection';hood_weight.outputs[0].default_value=0
hood_mix=hood_nodes.new('ShaderNodeMixRGB');hood_mix.blend_type='ADD'
hood_amount=hood_nodes.new('ShaderNodeMath');hood_amount.operation='MULTIPLY'
hood_links.new(hood_rim.outputs[0],hood_amount.inputs[0]);hood_links.new(hood_weight.outputs[0],hood_amount.inputs[1])
hood_coord=hood_nodes.new('ShaderNodeTexCoord');hood_axis=hood_nodes.new('ShaderNodeSeparateXYZ')
hood_links.new(hood_coord.outputs['Generated'],hood_axis.inputs[0])
hood_tint=hood_nodes.new('ShaderNodeValToRGB')
hood_tint.color_ramp.elements[0].color=look.rgba('#9E366A');hood_tint.color_ramp.elements[-1].color=look.rgba('#327EAB')
hood_tint.color_ramp.elements.new(.49).color=look.rgba('#141520')
hood_links.new(hood_axis.outputs['X'],hood_tint.inputs[0]);hood_links.new(hood_amount.outputs[0],hood_mix.inputs[0]);hood_links.new(hood_base,hood_mix.inputs[1]);hood_links.new(hood_tint.outputs[0],hood_mix.inputs[2]);hood_links.new(hood_mix.outputs[0],hood_emission.inputs['Color'])
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
    return G.cube(name,pos,size,mat,parent,bevel,ink_width if name.startswith(('Cooler','Phone','Latch','Calendar')) else 0)

def ring(name,parent,x,y,z,r,th,mat,xy=False,segments=32):
    t=[i*math.tau/segments for i in range(segments+1)]
    pts=[(x+r*math.cos(a),y+r*math.sin(a),z) if xy else (x+r*math.cos(a),y,z+r*math.sin(a)) for a in t]
    return G.line(name,pts,th,mat,parent)

def textile(name,a,b,scale,roughness=.58,metallic=0,relief=.0028):
    mat=look.metal(name,a,metallic,roughness)
    n,l=mat.node_tree.nodes,mat.node_tree.links
    xyz=n.new('ShaderNodeTexCoord')
    vec=n.new('ShaderNodeVectorMath')
    vec.operation='MULTIPLY'
    vec.inputs[1].default_value=scale
    l.new(xyz.outputs['Object'],vec.inputs[0])
    noise=n.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=1
    noise.inputs['Detail'].default_value=4
    l.new(vec.outputs[0],noise.inputs['Vector'])
    ramp=n.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=look.rgba(a)
    ramp.color_ramp.elements[1].color=look.rgba(b)
    l.new(noise.outputs['Fac'],ramp.inputs[0])
    bs=n['Principled BSDF']
    l.new(ramp.outputs[0],bs.inputs['Base Color'])
    rough=n.new('ShaderNodeMapRange')
    rough.inputs['To Min'].default_value=max(.12,roughness-.11)
    rough.inputs['To Max'].default_value=min(.95,roughness+.12)
    l.new(noise.outputs['Fac'],rough.inputs[0]);l.new(rough.outputs[0],bs.inputs['Roughness'])
    micro=n.new('ShaderNodeTexNoise')
    micro.inputs['Scale'].default_value=155
    micro.inputs['Detail'].default_value=2
    l.new(xyz.outputs['Object'],micro.inputs['Vector'])
    bump=n.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value=.23
    bump.inputs['Distance'].default_value=relief
    l.new((noise if max(scale)>38 else micro).outputs['Fac'],bump.inputs['Height'])
    l.new(bump.outputs[0],bs.inputs['Normal'])
    return mat

wood=textile('Satin walnut grain','#4A2B25','#976345',(114,3.5,44),.37,relief=.004)
paint=textile('Night blue wall plaster','#252E48','#374360',(3.1,3.1,4),.78)
pawnpaint=textile('Pawn amber plaster','#926B54','#AA8066',(2.8,2.8,3.5),.76)
pane=look.metal('Night window glass','#3A588A',.30,.24,emission_strength=.17)
carpet=textile('Indigo woven rug','#24283A','#494461',(116,125,145),.83,relief=.004)
chair_fabric=textile('Charcoal woven upholstery','#161B29','#39364E',(140,170,190),.82,relief=.002)
pc_metal=textile('Brushed graphite PC housing','#141C26','#343A4B',(380,7,135),.32,.69,.001)
hall_mat=look.metal('Ochre hallway','#AA8166',0,.76,emission_strength=.19)

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
    material=bpy.data.materials.get('Soft contact shadow')
    if material is None:
        material=G.emission('Soft contact shadow','#100D19')
        material.surface_render_method='BLENDED'
        material.use_backface_culling=True
        nodes,links=material.node_tree.nodes,material.node_tree.links
        coordinates=nodes.new('ShaderNodeTexCoord');flat=nodes.new('ShaderNodeVectorMath');flat.operation='MULTIPLY'
        flat.inputs[1].default_value=(1,1,0)
        distance=nodes.new('ShaderNodeVectorMath');distance.operation='DISTANCE';distance.inputs[1].default_value=(.5,.5,0)
        ramp=nodes.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE'
        ramp.color_ramp.elements[0].position=.11;ramp.color_ramp.elements[0].color=(.58,.58,.58,1)
        ramp.color_ramp.elements[1].position=.5;ramp.color_ramp.elements[1].color=(0,0,0,1)
        transparency=nodes.new('ShaderNodeBsdfTransparent');mix=nodes.new('ShaderNodeMixShader')
        links.new(coordinates.outputs['Generated'],flat.inputs[0]);links.new(flat.outputs[0],distance.inputs[0]);links.new(distance.outputs['Value'],ramp.inputs[0])
        links.new(ramp.outputs[0],mix.inputs[0]);links.new(transparency.outputs[0],mix.inputs[1])
        links.new(next(node for node in nodes if node.type=='EMISSION').outputs[0],mix.inputs[2]);links.new(mix.outputs[0],next(node for node in nodes if node.type=='OUTPUT_MATERIAL').inputs['Surface'])
    o=G.sphere(name,pos,scale,material,root,24,12)
    look.mark_role(o,'ink')
    return o

# Pawn counter and the years montage occupy the same warm, dressed corner.
timber_floor(pawn,wood)
box('Pawn rear stucco',pawn,(0,2.25,1.68),(6.8,.20,3.36),pawnpaint)
box('Pawn left wall',pawn,(-3.42,.5,1.60),(.17,3.6,3.2),pawnpaint)
box('Pawn baseboard',pawn,(0,2.10,.17),(6.8,.14,.23),wood)
box('Pawn cornice',pawn,(0,2.09,3.12),(6.75,.15,.16),wood,.024)
for x in (-2.77,-1.93,2.99):
    box('Pawn oak upright',pawn,(x,2.105,1.65),(.095,.065,2.97),wood,.014)
box('Pawn counter slab',pawn,(0,.48,.814),(2.58,.88,.11),wood,.042,.006)
box('Pawn counter dark body',pawn,(0,.55,.40),(2.52,.69,.75),black,.05,.003)
for i in range(10):
    x=-1.14+i*.25
    box('Counter fluted cedar panel',pawn,(x,.195,.457),(.215,.035,.55),wood,.016)
box('Counter brass foot rail',pawn,(0,.175,.19),(2.6,.062,.063),gold,.017)
for z in (1.18,1.67,2.16):
    box('Pawn side shelf',pawn,(1.72,1.95,z),(1.66,.44,.065),wood)
    for i in range(4):
        x=1.11+i*.37
        h=.15+.055*((i+int(z*2))%3)
        box('Pawn vintage carton',pawn,(x,1.88,z+.06+h/2),(.26,.20,h),[black,leather,cream,silver][i],.014)
    for x in (1.0,2.28):
        box('Pawn shelf bracket',pawn,(x,2.032,z-.125),(.055,.105,.235),gold,.012)
    for i in range(3):
        x=1.02+i*.43
        G.cylinder('Pawn shelf turned brass canister',(x,1.75,z+.035),(x,1.75,z+.155),.061,gold,pawn,18)
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
receipt=G.obj('Pawn receipt',parent=pawn);receipt.location=(.87,.20,.949);receipt.rotation_euler.x=math.radians(29)
paper=box('Receipt paper',receipt,(0,0,.006),(.44,.27,.012),cream,.012,.002)
receipt_text=text('Receipt amount','₹2,00,000',receipt,(0,0,.015),.076,dark)
receipt_text.rotation_euler.x=0
G.line('Receipt rest rail',[(.66,.079,.879),(1.08,.079,.879)],.010,gold,pawn)
box('Card reader',pawn,(.99,.62,.924),(.23,.25,.11),black,.042,.003)
box('Card reader screen',pawn,(.99,.585,.986),(.13,.092,.011),cyan,.009)

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
latch=G.obj('Sliding latch bolt',parent=door);latch.location=(-1.08,-.142,1.065)
box('Latch bronze strike case',door,(-1.115,-.075,1.065),(.235,.07,.077),gold,.012,.003)
G.cylinder('Latch nickel sliding bolt',(-.106,0,0),(.112,0,0),.019,silver,latch,20,.002)
G.sphere('Sliding latch thumb stud',(0,-.022,0),(.030,.028,.033),gold,latch,18,9)
G.obj('Door hand latch anchor',parent=latch).location=(0,-.039,.003)
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
box('Chair blue padded seat',chair,(0,0,.54),(.60,.61,.15),chair_fabric,.075)
box('Chair sculpted high back',chair,(0,-.26,.93),(.63,.138,.88),chair_fabric,.072)
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
    box(name+' aluminium housing',t,(0,.026,.305),(.38,.32,.61),pc_metal,.040)
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
    for x in (-.155,.155):
        for z in (.06,.55):
            G.cylinder('PC side panel screw',(x,-.166,z),(x,-.180,z),.012,silver,t,16)
    return t

tower('Bedroom RGB tower',room,(.46,1.008,.986))


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
    return x,-.139*math.sqrt(max(.03,1-(x*x+z*z)/(r*r)))-extra,z
G.facepoint=facepoint

def actor_ink(obj,width):
    shell=G.ink(obj,width)
    for source,edge in zip(obj.data.vertices,shell.data.vertices):
        p=source.co
        pressure=1+.24*math.sin(p.x*24+p.z*7)+.08*math.sin(p.x*61-p.z*17)
        edge.co=source.co+source.normal*width*pressure
    shell.data.update()

def hull_for_cloth(obj):
    hull=G.obj(obj.name+' / ink',obj.data,obj)
    look.mark_role(hull,'ink')
    sub=hull.modifiers.new('Smooth ink silhouette','SUBSURF')
    # The foreground garment is level 2. The thinner rear shell supports
    # Line Art only at silhouette breaks and can use a coarser subdivision.
    sub.levels=sub.render_levels=1
    graph=bpy.data.node_groups.get('Clothing ink offset')
    if graph is None:
        graph=bpy.data.node_groups.new('Clothing ink offset','GeometryNodeTree')
        graph.interface.new_socket(name='Geometry',in_out='INPUT',socket_type='NodeSocketGeometry')
        graph.interface.new_socket(name='Geometry',in_out='OUTPUT',socket_type='NodeSocketGeometry')
        nodes,links=graph.nodes,graph.links
        geometry=nodes.new('NodeGroupInput');out=nodes.new('NodeGroupOutput')
        normal=nodes.new('GeometryNodeInputNormal')
        offset=nodes.new('ShaderNodeVectorMath');offset.operation='SCALE'
        offset.inputs['Scale'].default_value=.008
        position=nodes.new('GeometryNodeSetPosition')
        reverse=nodes.new('GeometryNodeFlipFaces')
        material=nodes.new('GeometryNodeSetMaterial');material.inputs['Material'].default_value=ink
        links.new(geometry.outputs['Geometry'],position.inputs['Geometry'])
        links.new(normal.outputs['Normal'],offset.inputs[0]);links.new(offset.outputs[0],position.inputs['Offset'])
        links.new(position.outputs[0],reverse.inputs['Mesh']);links.new(reverse.outputs[0],material.inputs['Geometry'])
        links.new(material.outputs[0],out.inputs['Geometry'])
    hull.modifiers.new('Backface-only pressure edge','NODES').node_group=graph
    return hull

def drawn_contour(name,source,stage):
    drawing=bpy.data.grease_pencils.new(name)
    drawing.stroke_depth_order='3D'
    layer=drawing.layers.new('Character contour',set_active=True)
    layer.frames.new(1)
    stroke=G.obj(name,drawing,stage)
    stroke.use_grease_pencil_lights=False
    paint=bpy.data.materials.get('Graphite stroke')
    if paint is None:
        paint=bpy.data.materials.new('Graphite stroke')
        bpy.data.materials.create_gpencil_data(paint)
        paint.grease_pencil.color=look.rgba('#07070A')
    drawing.materials.append(paint)
    contour=stroke.grease_pencil_modifiers.new('Visible outer silhouette','GP_LINEART')
    contour.source_type='COLLECTION'
    contour.source_collection=source
    contour.target_layer=layer.info
    contour.target_material=paint
    contour.use_contour=True
    contour.use_crease=contour.use_material=contour.use_intersection=contour.use_edge_mark=False
    contour.thickness=17
    contour.stroke_depth_offset=.002
    pressure=stroke.grease_pencil_modifiers.new('Ink pressure','GP_THICK')
    pressure.thickness_factor=1.12
    noise=stroke.grease_pencil_modifiers.new('Fixed paper pressure','GP_NOISE')
    noise.factor=0
    noise.factor_thickness=.15
    noise.use_random=False
    look.mark_role(stroke,'ink')

def register_line_sources(stage, objects):
    name=stage.name+' character line sources'
    collection=bpy.data.collections.get(name)
    if collection is None:
        collection=bpy.data.collections.new(name)
        S.collection.children.link(collection)
        drawn_contour(stage.name+' unified line art',collection,stage)
    for obj in objects:
        collection.objects.link(obj)

def garment(name,profile,material,parent,width=.006):
    obj=G.loft(name,profile,material,parent,18,0)
    sub=obj.modifiers.new('Tailored smooth knit','SUBSURF')
    sub.levels=2
    bpy.context.view_layer.objects.active=obj
    bpy.ops.object.modifier_apply(modifier=sub.name)
    if width:actor_ink(obj,width)
    return obj

def soft_line(name,points,width,material,parent):
    if len(points)>2:
        p=[V(point) for point in points]
        rounded=[]
        for i in range(len(p)-1):
            a,b,c,d=p[max(0,i-1)],p[i],p[i+1],p[min(i+2,len(p)-1)]
            for step in range(5):
                t=step/5
                rounded.append(.5*(2*b+(-a+c)*t+(2*a-5*b+4*c-d)*t*t+(-a+3*b-3*c+d)*t*t*t))
        points=[*rounded,p[-1]]
    line=G.line(name,points,width,material,parent)
    line.data.bevel_resolution=3
    line.data.use_fill_caps=True
    return line

def make_actor(name,parent,is_papa=False):
    root=G.obj(name,parent=parent)
    body=G.obj(name+' torso rig',parent=root)
    head=G.obj(name+' head pivot',parent=body);head.location.z=1.51
    skull=G.sphere(name+' rough cream skull',(0,0,0),(.305,.139,.305),skin,head,72,34)
    for v in skull.data.vertices:
        rr=G.rough(math.atan2(-v.co.z,v.co.x))
        v.co.x*=rr
        v.co.z*=rr
    actor_ink(skull,.008)
    top=kurta if is_papa else hoodie
    torso=[(.57,.193,.102),(.59,.199,.108),(.72,.203,.120),(.89,.191,.108),(1.055,.236,.113),
           (1.113,.225,.11),(1.165,.159,.091),(1.185,.086,.069),(1.20,.08,.061)] if is_papa else [
           (.652,.163,.089),(.67,.175,.098),(.746,.218,.126),(.89,.224,.129),(1.055,.249,.120),
           (1.108,.233,.106),(1.161,.179,.097),(1.190,.087,.070),(1.206,.078,.062)]
    connected=tailoring.create(name+' shaped cotton top',torso,top,fold,body,G)
    hull_for_cloth(connected)
    outline_parts=[skull,connected]
    G.sphere(name+' connected neck',(0,0,1.197),(.071,.068,.078),top,body,36,18)
    garment(name+' fitted waist and seat',[(.588,.137,.091),(.61,.171,.096),(.727,.172,.093),(.755,.150,.082)],trousers,body,.006)
    if is_papa:
        garment('Kurta collar band',[(1.138,.114,.091),(1.158,.111,.094),(1.194,.098,.095),(1.206,.090,.084)],kurta,body,.004)
        soft_line('Kurta stitched placket edge',[(.023,-.095,1.16),(.023,-.123,1.06),(.023,-.113,.88)],.0045,fold,body)
        soft_line('Kurta centre placket',[(0,-.097,1.17),(0,-.123,1.06),(0,-.115,.90),(0,-.119,.84)],.0065,fold,body)
        for i in range(4):
            G.sphere('Kurta small button',(0,-.129,1.12-i*.064),(.010,.006,.011),gold,body,20,12)
        for side in (-1,1):
            soft_line('Kurta side fell seam',[(side*.165,-.064,.62),(side*.169,-.066,.73),(side*.153,-.064,.87)],.0045,fold,body)
        soft_line('Kurta front hem stitch',[(-.147,-.066,.611),(-.074,-.101,.610),(0,-.117,.606),(.074,-.101,.610),(.147,-.066,.611)],.0045,fold,body)
        mustache=[]
        for i in range(60):
            a=i*math.tau/60
            x=.125*math.cos(a)
            mustache.append((x,-.091+.037*math.sin(a)-.032*(abs(x)/.125)**1.45))
        G.patch(name+' mustache',mustache,dark,head,.018)
    else:
        hood=garment('Gamer sculpted double-layer hood',[(1.037,.18,.094),(1.083,.203,.126),(1.169,.168,.133),(1.217,.11,.113),(1.235,.080,.088)],hoodie,body,.005)
        hood.location.y=.020
        for side in (-1,1):
            end=V((side*.076,-.139,.915+.019*side))
            soft_line('Hoodie dark drawstring',[(side*.076,-.110,1.14),(side*.091,-.130,1.062),(side*.091,-.139,.991),end],.007,fold,body)
            G.cylinder('Drawstring black aglet',end,end+V((0,0,-.022)),.006,dark,body,16)
        garment('Kangaroo pouch raised knit',[(.737,.120,.027),(.748,.153,.034),(.792,.167,.042),(.842,.135,.031),(.861,.112,.021)],hoodie,body,.004).location.y=-.107
        for side in (-1,1):
            soft_line('Kangaroo angled seam',[(side*.153,-.139,.777),(side*.148,-.149,.809),(side*.119,-.138,.846)],.0065,fold,body)
            soft_line('Folded hood piped edge',[(side*.181,-.067,1.12),(side*.145,-.127,1.142),(side*.104,-.102,1.192)],.007,dark,body)
        hair_pts=[(-.278,.106),(-.273,.221),(-.206,.285),(-.087,.294),(-.039,.324),(.023,.291),(.108,.321),
                  (.151,.278),(.237,.282),(.266,.196),(.291,.131),(.197,.163),(.157,.120),(.059,.181),
                  (.010,.128),(-.063,.195),(-.117,.142),(-.176,.181),(-.227,.105)]
        rounded=[]
        for a,b in zip(hair_pts,hair_pts[1:]+hair_pts[:1]):
            rounded.extend(((.84*a[0]+.16*b[0],.84*a[1]+.16*b[1]),(.16*a[0]+.84*b[0],.16*a[1]+.84*b[1])))
        hair_pts=rounded
        coords=[facepoint(x,z,.010) for x,z in hair_pts]
        # Tessellate the flat drawing first and wrap every subdivided triangle onto the head.
        outline=[V((x,0,z)) for x,z in hair_pts]
        triangles=[tuple(outline[i] for i in tri) for tri in tessellate_polygon([outline])]
        for _ in range(2):
            refined=[]
            for a,b,c in triangles:
                ab=(a+b)/2;bc=(b+c)/2;ca=(c+a)/2
                refined.extend([(a,ab,ca),(ab,b,bc),(ca,bc,c),(ab,bc,ca)])
            triangles=refined
        fitted=[facepoint(v.x,v.z,.013) for tri in triangles for v in tri]
        G.mesh('Messy asymmetrical pointed fringe',fitted,
               [tuple(range(i,i+3)) for i in range(0,len(fitted),3)],hair,head)
        soft_line('Hair bold outer ink',[V(co)+V((0,-.004,0)) for co in coords+[coords[0]]],.011,dark,head)
        G.sphere('Back of gamer hair',(0,.054,.043),(.290,.092,.253),hair,head,32,16,.004)
        headphones=G.obj('RGB headset worn',parent=head)
        arch=[(-.302,-.001,.063),(-.276,.009,.208),(-.18,.016,.299),(0,.020,.341),(.18,.014,.293),(.268,.002,.199),(.30,-.004,.051)]
        soft_line('Headset top ink casing',arch,.036,dark,headphones)
        soft_line('Headset arched crown',[(-.302,-.027,.063),(-.276,-.017,.208),(-.18,-.010,.299),(0,-.006,.341),
                  (.18,.014,.293),(.268,.002,.199),(.30,-.004,.051)],.028,black,headphones)
        for side in (-1,1):
            cup=G.sphere('Headset cushioned ear cup',(side*.296,-.005,.020),(.050,.070,.099),black,headphones,36,20)
            actor_ink(cup,.007)
            G.line('RGB headphone diffuser',[(side*.300,-.066,-.046),(side*.324,-.065,.007),(side*.314,-.061,.063)],.012,
                   cyan if side<0 else pink,headphones)
        G.line('Microphone curved boom',[(.299,-.037,-.007),(.258,-.074,-.064),(.182,-.097,-.087)],.011,black,headphones)
    for side in (-1,1):
        G.line(f'{name} arm {side}',[(0,0,.95)]*32,0,dark,root)
        leg=G.line(f'{name} leg {side}',[(0,0,.49)]*32,.059 if is_papa else .065,trousers,root)
        leg.data.bevel_resolution=3;leg.data.use_fill_caps=True
        outline_parts.append(leg)
        for j,pt in enumerate(leg.data.splines[0].points):pt.radius=.78+.32*math.sin(math.pi*j/31)-.095*j/31
        G.line(f'{name} trouser fold {side}',[(0,0,.49)]*7,.0034,fold,root).data.bevel_resolution=2
        hand=G.obj(f'{name} hand {side}',parent=root)
        palm=G.sphere('Graphic palm',(0,0,0),(.053,.019,.046),dark,hand,36,18)
        outline_parts.append(palm)
        for j in range(2):
            G.line('Graphic fingers along grip',[(.016,-.018,-.023+j*.022),(.044,-.018,-.027+j*.022),(.055,-.013,-.019+j*.022)],.010,dark,hand)
        footwear=G.obj(f'{name} sole {side}',parent=root)
        upper=G.sphere('Sock' if is_papa else 'Foot upper',(0,-.012,-.011 if is_papa else -.002),(.062,.110,.043) if is_papa else (.073,.126,.049),trousers if is_papa else black,footwear,36,18)
        actor_ink(upper,.006)
        if not is_papa:
            outsole=G.sphere('Shoe shaped outsole',(0,-.018,-.036),(.077,.131,.018),silver,footwear,36,18)
            actor_ink(outsole,.004)
            for j in range(3):
                y=-.067+j*.022
                soft_line('Sneaker crossed lace',[(-.041,y+.009,.021),(0,y,.045),(.041,y-.009,.021)],.0045,ivory,footwear)
        mark=support(f'{name} grounded contact {side}',root,(side*.13,0,.002),(.105,.149,.002))
        r=side*.105
        G.oval(f'{name} eye white {side}',r,.026,.048,.056,ivory,head,.012)
        G.oval(f'{name} pupil {side}',r,.026,.023,.039,dark,head,.016)
        G.oval(f'{name} eye catch {side}',r-.006,.044,.008,.010,ivory,head,.019)
        G.faceline(f'{name} blink {side}',[(r-.037,.023),(r,.015),(r+.037,.022)],.008,dark,head)
        if is_papa:
            inner=r-side*.056
            brow=[(inner,.079),(inner+side*.049,.112),(inner+side*.104,.125)]
            soft_line(f'{name} eyebrow {side}',[facepoint(x,z,.031) for x,z in brow],.016,dark,head)
        else:G.faceline(f'{name} eyebrow {side}',[(r-.038,.110),(r,.124),(r+.043,.106)],.010,dark,head)
        if not is_papa:
            G.patch(f'{name} tired lid {side}',[(r-.048,.037),(r+.045,.037),(r+.043,.078),(r-.043,.079)],skin,head,.022)
            G.faceline(f'{name} tired bag {side}',[(r-.042,-.031),(r,-.042),(r+.038,-.033)],.013,black,head)
            signal=cyan if side<0 else pink
            neon=G.obj(f'{name} eye neon {side}',parent=head)
            G.faceline('Pupil beach horizon',[(r-.017,.020),(r+.015,.020)],.0033,signal,neon)
            G.faceline('Pupil palm reflection',[(r-.005,.020),(r+.002,.044),(r-.012,.033),(r+.002,.044),(r+.014,.034)],.0027,signal,neon)
        else:
            rx=.077;z=.036
            lens=G.patch('Papa subtle lens reflection',[(r-.062,.061),(r-.016,.063),(r+.022,.028),(r-.016,.036)],glass,head,.028)
            lens.visible_shadow=False
            G.line('Papa rectangular glasses',[facepoint(r-rx,z-.049,.026),facepoint(r+rx,z-.049,.026),facepoint(r+rx,z+.050,.026),
                        facepoint(r-rx,z+.050,.026),facepoint(r-rx,z-.049,.026)],.010,dark,head)
    if is_papa:
        G.faceline('Papa spectacles bridge',[(-.030,.04),(0,.051),(.030,.04)],.008,dark,head)
    if not is_papa:
        G.faceline(name+' tired mouth',[(-.048,-.126),(.002,-.121),(.047,-.125)],.008,dark,head)
    mouth=[(-.062,-.164),(-.031,-.148),(0,-.144),(.035,-.149),(.063,-.164)] if is_papa else [(-.061,-.113),(0,-.136),(.060,-.104)]
    soft_line(name+' closed mouth',[facepoint(x,z,.013) for x,z in mouth],.010,dark,head)
    G.oval(name+' wide mouth',0,-.115,.074,.076,dark,head,.010)
    G.patch(name+' upper teeth',[(-.051,-.079),(.051,-.079),(.040,-.093),(-.039,-.093)],ivory,head,.015)
    G.oval(name+' speaking mouth',0,-.161 if is_papa else -.12,.061,.024 if is_papa else .040,dark,head,.014)
    for i in range(4):
        G.mesh(f'{name} sweat {i}',[(0,0,.049),(.024,0,-.010),(.019,0,-.027),(0,0,-.034),
               (-.020,0,-.027),(-.025,0,-.010)],[(0,1,2,3,4,5)],sweat,head,smooth=False)
    register_line_sources(parent,outline_parts)
    return root

make_actor('Pawn Gamer',pawn)
make_actor('Gamer',room)
make_actor('Papa',room,True)

def slipper(name,parent,pos):
    root=G.obj(name,parent=parent);root.location=pos
    profile=[]
    for i in range(40):
        theta=math.tau*i/40
        y=.181*math.sin(theta)
        profile.append((.091*math.cos(theta)*(1-.23*math.sin(theta)),y))
    vertices=[(x*k,y*k,z) for z,k in ((.003,.96),(.013,1),(.037,1),(.048,.95)) for x,y in profile]
    faces=[list(reversed(range(40))),list(range(120,160))]
    faces.extend((i+j*40,(i+1)%40+j*40,(i+1)%40+(j+1)*40,i+(j+1)*40) for j in range(3) for i in range(40))
    outsole=G.mesh(name+' sculpted leather outsole',vertices,faces,leather,root)
    actor_ink(outsole,.008)
    G.line(name+' welt stitched edge',[(x,y,.034) for x,y in profile+[profile[0]]],.004,gold,root)
    strap=soft_line(name+' rounded toe strap',[(-.079,-.056,.047),(-.062,-.053,.083),(0,-.046,.101),(.062,-.053,.083),(.079,-.056,.047)],.021,leather,root)
    register_line_sources(parent,[strap])
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
area('Pawn overhead amber',pawn,(-1.7,-1.7,3.20),(0,.65,1.10),305,'#FFE3BB',1.35)
area('Pawn copper bounce',pawn,(1.9,-.7,2.42),(0,.7,1.2),35,'#D48766',1.75,False)
spot('Pawn counter reflection',pawn,(.57,.63,2.57),(.24,.39,1.043),92,'#FFF0D2')
area('Bedroom cool key',room,(-2.9,-.7,3.01),(-.25,.1,1.24),162,'#9FAFEF',1.37)
area('Bedroom quiet lavender fill',room,(2.5,-1.4,2.81),(-.55,-.1,1.1),28,'#B4A2EE',2.3,False)
area('Bedroom high neutral eye key',room,(.35,-1.3,2.73),(-.53,-.21,1.25),82,'#FFEDE0',1.21,False)
spot('Cool diagonal window beam',room,(-1.9,1.86,2.51),(-.92,-.9,.4),132,'#AECCFF',.15)
area('Door hallway practical',room,(1.47,2.88,2.76),(1.18,.35,1.02),221,'#FFDC9C',1.10)
area('Door rim to Papa',room,(1.4,2.66,1.96),(1.18,.55,1.34),81,'#FFC17F',.90,False)
area('TV warm pink bounce',room,(-.71,.48,1.58),(-.68,-.36,1.30),42,'#FF75BD',.67,False)
area('TV cold cyan bounce',room,(-.34,.40,1.36),(-.72,-.29,1.29),28,'#6FDFEE',.53,False)
area('Siren warm sweep',room,(2.59,-.30,2.36),(-.03,.24,1.24),0,'#F5444F',1.05,False)
area('Siren cool sweep',room,(-2.4,-.20,2.31),(.45,-.14,1.24),0,'#476EFF',1.18,False)
area('Bedroom magenta edge',room,(-1.53,.75,2.12),(-.67,-.23,1.34),84,'#F753AC',.67,False)
area('Bedroom cyan edge',room,(.21,.67,1.98),(-.67,-.23,1.30),63,'#52C9F8',.70,False)
area('Warm father corridor edge',room,(1.57,2.43,2.27),(1.10,1.12,1.30),166,'#FFD274',.77,False)
area('Pawn warm overhead edge',pawn,(.40,1.55,2.69),(-.50,.55,1.12),88,'#FFBF88',.92,False)
box('Hallway wall lamp',room,(1.56,3.54,1.98),(.36,.055,.27),amber,.041,.004)

cam_data=bpy.data.cameras.new('Shot lens')
cam=G.obj('Story camera',cam_data)
S.camera=cam
focus=G.obj('Optical focus')
look.configure_camera(cam,focus,45,3.2)
speed=G.obj('Whip pan action lines',parent=cam)
speed.location=(0,0,-.83)
for i,(x,y) in enumerate([(-.22,-.29),(.22,-.26),(-.23,.28),(.215,.31),(-.19,.36),(.19,-.35)]):
    line=G.line('Tapered action streak',[(x,y,0),(x*.73,y*.81,0),(x*.58,y*.69,0)],.0033,ivory,speed)
    for j,pt in enumerate(line.data.splines[0].points):pt.radius=1-.43*j
    look.mark_role(line,'streak')
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
sharpen=tree.nodes.new('CompositorNodeFilter');sharpen.filter_type='SHARPEN'
sharpen.inputs[0].default_value=.12
tree.links.new(original,sharpen.inputs[1]);original=sharpen.outputs[0]
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
data_paths={'geometry.py':GEOMETRY,'ricks_lookdev.py':ROOT/'scripts/ricks_lookdev.py','tailoring.py':HERE/'tailoring.py','runtime.py':HERE/'runtime.py','timing.json':blueprint}
for name,path in data_paths.items():
    bpy.data.texts.new(name).from_string(path.read_text(encoding='utf-8-sig'))
bootstrap="""import sys,types,bpy
for name in ('ricks_lookdev','geometry','tailoring','runtime'):
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
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/(HERE.name+'.blend')))

