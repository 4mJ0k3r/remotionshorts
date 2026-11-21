"""V2 art direction applied to the preserved V1 Blender master."""
import math
import bpy
from mathutils import Vector
import geometry as G
from wardrobe import cloth
import ricks_lookdev as look

O = bpy.data.objects
M = bpy.data.materials
INK = M['Marker ink']
GRAPHIC = M['Graphic limbs and features']

def toon(name, *colors):
    return look.clean_toon(name, stops=list(zip((0,.34,.70,1),colors)), light_min=.13, light_max=.72)

def box(name, xyz, size, material, parent, bevel=.018, ink=.005):
    return G.cube(name, xyz, size, material, parent, bevel, ink)

def material(obj, mat):
    obj.data.materials[0] = mat

def remove_tree(obj):
    for child in list(obj.children_recursive)[::-1]:
        bpy.data.objects.remove(child, do_unlink=True)
    bpy.data.objects.remove(obj, do_unlink=True)

def text(name, value, xyz, size, parent, mat):
    font = bpy.data.curves.new(name, 'FONT')
    font.body = value
    font.font = bpy.data.fonts.get('Nirmala UI') or next(iter(bpy.data.fonts))
    font.size = size
    font.align_x = 'CENTER'
    font.align_y = 'CENTER'
    font.extrude = .0007
    font.materials.append(mat)
    obj = G.obj(name, font, parent)
    obj.location = xyz
    obj.rotation_euler.x = math.pi/2
    return obj

def costumes():
    skin = toon('V2 warm graphic skin','#C4C8EA','#E5DCE0','#F9EAE1','#FFF5EF')
    teal = toon('V2 barber teal','#15585E','#18867F','#2DBEB0','#59D7BF')
    ochre = toon('V2 customer ochre','#713718','#AA611D','#E3A135','#F8BD57')
    rust = toon('V2 rust vest','#5A2320','#8D3A22','#C4552B','#DE7242')
    burgundy = toon('V2 burgundy cotton','#401628','#682039','#983C51','#B95665')
    charcoal = toon('V2 charcoal jacket','#191926','#282B3C','#41485A','#575D6D')
    cream = toon('V2 warm ivory fabric','#877E92','#BDAD9F','#E6D4B7','#FDF0DB')
    gold = M['Brass']
    for name,mat in [('Barber',teal),('Customer',ochre),('Shopkeeper',cream),
                     ('Smuggler',burgundy),('Trader',burgundy)]:
        material(O[name+' connected torso'],mat)
    for name in ('Barber','Customer','Shopkeeper','Smuggler','Trader','Officer'):
        body,head = O[name+' body'],O[name+' head']
        material(O[name+' cream rough head'],skin)
        for old in list(body.children):
            if old.name.startswith(('Shopkeeper small apron','Trader charcoal vest','Smuggler charcoal vest')):
                remove_tree(old)
        if name in ('Shopkeeper','Trader','Smuggler'):
            for side in (-1,1):
                cloth(name+' tapered vest panel '+str(side),[(side*.055,1.18),(side*.195,1.14),(side*.19,.76),(side*.045,.745),(side*.076,1.02)],rust if name=='Shopkeeper' else charcoal,body)
        if name in ('Customer','Barber'):
            for side in (-1,1):
                cloth(name+' collar '+str(side),[(side*.025,1.20),(side*.13,1.16),(side*.075,1.09)],cream,body)
        cloth(name+' belt',[(-.177,.78),(.177,.78),(.175,.724),(-.175,.724)],charcoal,body)
        box(name+' belt buckle',(0,-.108,.753),(.071,.027,.058),gold,body,.008,.003)
        if name=='Officer':
            box('Officer gold badge',(-.135,-.105,1.075),(.052,.014,.051),gold,body,.008,.002)
        if name in ('Trader','Smuggler'):
            for brim in [o for o in head.children if o.name.startswith('Cap projecting brim')]:
                brim.location.z=.147
                brim.scale.y=1.45
        if name=='Customer':
            for old in [o for o in head.children if o.name.startswith('Customer lather')]:
                remove_tree(old)
            for side in (-1,1):
                points=[(.15,-.15),(.16,-.10),(.185,-.095),(.19,-.066),(.22,-.072),(.24,-.095),
                        (.232,-.113),(.229,-.145),(.204,-.167),(.193,-.184),(.163,-.176)]
                coords = [(side*x, -.063*math.sqrt(max(.04,1-(x*x+z*z)/.103))-.014,z) for x,z in points]
                G.mesh('Scalloped shaving foam',coords,[tuple(range(len(points)))],cream,head,smooth=False).visible_shadow=False
                cloth('Customer shoulder cape '+str(side),[(side*.045,1.18),(side*.17,1.165),(side*.225,1.08),(side*.20,.99),(side*.13,.955),(side*.102,1.08)],cream,body)
        if name=='Barber':
            apron = toon('V2 barber apron ground','#183D46','#256372','#368296','#5AABB1')
            cloth('Barber shaped apron',[(-.11,1.09),(.11,1.09),(.159,.784),(-.159,.784)],apron,body)
            for i in (-2,-1,0,1,2):
                x=i*.045
                from wardrobe import surface
                G.line('Barber apron woven stripe',[surface(x,1.075-j*.023,.008) for j in range(13)],.003,cream,body)
            cloth('Apron comb pocket',[(.045,1.025),(.125,1.025),(.125,.938),(.045,.938)],teal,body)
            box('Pocket comb',(.085,-.108,1.033),(.064,.014,.067),gold,body,.003,.002)
            for x in range(5):
                box('Comb tooth',(.061+x*.012,-.11,1.071),(.004,.012,.023),gold,body,.001,0)

def coin_details(root, radius, depth, alloy, rim, embossed=True):
    for child in list(root.children):
        if child.name.startswith(root.name+' milled body'):
            material(child,alloy)
    for sign in (-1,1):
        y=sign*(depth/2+.0008)
        G.cylinder('Raised minted circular field',(0,y-.001,0),(0,y+.001,0),.85*radius,alloy,root,56)
        points=[(.94*radius*math.cos(a*math.tau/64),y,.94*radius*math.sin(a*math.tau/64)) for a in range(65)]
        G.line('Burnished nickel rim',points,.013*radius,rim,root)
    for child in list(root.children):
        if child.type=='FONT' and ('physical relief' in child.name or 'reverse relief' in child.name):
            child.location.y=math.copysign(depth/2+.004,child.location.y)
            child.location.z=.011
            child.data.extrude=.0018
            material(child,rim)
    if embossed:
        text('Minted date','2002',(0,-depth/2-.004,-.045),radius*.20,root,rim)
        text('Minted alloy','CUPRO-NICKEL',(0,-depth/2-.004,-.075),radius*.124,root,rim)
        text('Reverse minted date','2002',(0,depth/2+.004,-.045),radius*.20,root,rim).rotation_euler.z=math.pi
        text('Reverse minted alloy','CUPRO-NICKEL',(0,depth/2+.004,-.075),radius*.124,root,rim).rotation_euler.z=math.pi

def slotted_blade(root, silver, edge):
    for child in list(root.children):
        remove_tree(child)
    # Matching inner and outer contours leave a real mounting aperture.
    outer=[(-.066,-.024),(-.058,-.034),(-.051,-.042),(-.024,-.042),
           (.024,-.042),(.051,-.042),(.058,-.034),(.066,-.024),
           (.066,.024),(.058,.034),(.051,.042),(.024,.042),
           (-.024,.042),(-.051,.042),(-.058,.034),(-.066,.024)]
    inner=[(-.028,-.003),(-.025,-.006),(-.018,-.006),(-.014,-.010),
           (.014,-.010),(.018,-.006),(.025,-.006),(.028,-.003),
           (.028,.003),(.025,.006),(.018,.006),(.014,.010),
           (-.014,.010),(-.018,.006),(-.025,.006),(-.028,.003)]
    n=len(outer)
    verts=[(x,y,z) for y in (-.0014,.0014) for ring in (outer,inner) for x,z in ring]
    faces=[]
    for i in range(n):
        j=(i+1)%n
        faces.extend(((i,j,j+n,i+n),(i+2*n,i+3*n,j+3*n,j+2*n),
                      (i,i+2*n,j+2*n,j),(i+n,j+n,j+3*n,i+3*n)))
    G.mesh(root.name+' open bevel steel',verts,faces,silver,root,.0012,False)
    for z in (-.039,.039):
        G.line('Sharpened bright blade edge',[(-.052,-.0018,z),(.052,-.0018,z)],.0016,edge,root)

def sets_and_props():
    bar,market,work,mint = (O[name+' stage'] for name in ('BARBER','MARKET','WORKSHOP','MINT'))
    plaster = toon('V2 buttery plaster','#A86C50','#CC936A','#E6B78B','#F5D3A7')
    terra = toon('V2 terracotta wainscot','#572F2A','#854538','#B76349','#CD7858')
    ochre = toon('V2 bazaar plaster','#785034','#BA7C42','#DE9F50','#F4BE70')
    olive = toon('V2 old mint stone','#555749','#828371','#B4B093','#D9D0AF')
    wood=M['Warm wood grain']
    brass=M['Brass']
    red=M['Brick crimson']
    iron=look.metal('V2 black cast iron','#36303A',.26,.32,emission_strength=.12)
    nickel=look.metal('V2 brushed cupro nickel','#A4917F',.48,.26,emission_strength=.17)
    rim=look.metal('V2 burnished coin relief','#E3C296',.45,.23,emission_strength=.22)
    silver=look.metal('V2 blade satin steel','#BECBD5',.49,.22,emission_strength=.20)
    edge=look.metal('V2 sharpened steel','#F0EEDE',.35,.18,emission_strength=.32)
    mirror=look.metal('V2 silvered mirror','#B7C4CC',.28,.18,emission_strength=.24)
    for o in list(O):
        if o.type!='MESH' or not o.data.materials:
            continue
        n=o.name
        if n.startswith(('BARBER lower wall','BARBER upper wall','BARBER window masonry')):
            material(o,plaster)
        if n.startswith(('MARKET lower wall','MARKET upper wall','MARKET window masonry')):
            material(o,ochre)
        if n.startswith(('MINT lower wall','MINT upper wall','MINT window masonry','MINT support floor','MINT side jamb')):
            material(o,olive)
        if n.startswith(('Press guide','Press base','Barber press moving ram','Mint machine column','Mint head crossbar','Mint base')):
            material(o,iron)
        if n.startswith('Supported coin die'):
            material(o,brass)
        if n in ('Mirror face','Hand mirror silver'):
            material(o,mirror)
        if n.startswith('RBI wall plaque'):
            material(o,brass)
    for j in range(17):
        x=(j-8)*.43
        box('Barber terracotta wainscot',(x,2.855,.54),(.414,.047,1.08),terra,bar,.010,.002)
    box('Wainscot cap rail',(0,2.805,1.085),(7.4,.12,.095),wood,bar)
    box('Mirror grooming shelf',(-1.45,2.42,.98),(1.53,.37,.08),wood,bar)
    for i,m in enumerate((red,M['Petrol turquoise'],brass)):
        x=-1.88+i*.21
        G.cylinder('Grooming glass bottle',(x,2.40,1.02),(x,2.40,1.20),.061,m,bar,16,.003)
        G.cylinder('Bottle neck and cap',(x,2.40,1.195),(x,2.40,1.25),.032,iron,bar,12)
    shelf_grip=O['Barber press moving ram']
    G.cylinder('Barber press iron handle bar',(-.13,-.10,.05),(-.13,-.26,.05),.022,iron,shelf_grip,16,.003)
    G.sphere('Barber press brass handle knob',(-.13,-.24,.05),(.04,.037,.04),brass,shelf_grip,16,8,.003)
    G.sphere('Hand mirror walnut surround',(0,.015,.13),(.165,.026,.205),wood,O['Customer hand mirror'],32,16,.004)
    # A tilted display window reflected as a restrained silver streak.
    G.line('Mirror silver glint',[(-.08,-.017,.19),(.05,-.017,.255)],.003,edge,O['Customer hand mirror'])
    for o in [x for x in list(O) if x.name.startswith('Barber striped pole') and x.parent==bar]:
        remove_tree(o)
    pole=G.obj('V2 rotating barber pole',parent=bar)
    pole.location=(1.46,1.12,.46)
    G.cylinder('White pole core',(0,0,0),(0,0,1.48),.085,M['White cotton'],pole,24,.003)
    for offset,m in [(0,red),(math.pi,M['Cobalt storefront paint'])]:
        G.line('Helical barber pole ribbon',[(.084*math.cos(offset+j*.13),.084*math.sin(offset+j*.13),1.48*j/144) for j in range(145)],.013,m,pole)
    for z in (0,1.48):
        G.sphere('Pole brass finial',(0,0,z),(.11,.11,.08),brass,pole,20,10,.003)
    for i in range(15):
        x=(i-7)*.35
        box('Kirana awning canvas panel',(x,1.93,2.55),(.35,1.0,.07),red if i%2==0 else plaster,market,.02,.002).rotation_euler.x=.15
        box('Kirana hanging awning edge',(x,1.43,2.49),(.35,.063,.16),red if i%2==0 else plaster,market,.025,.002)
    for stage,name in [(bar,'Barber counter'),(market,'Kirana counter'),(work,'Workshop bench'),(mint,'Mint blueprint desk')]:
        top=O[name+' top']
        length=1.50 if stage==mint else 2.70
        box(name+' carved front apron',(top.location.x,top.location.y-.423,.72),(length,.068,.18),wood,stage)
    for name,r,d in [('Loop hero coin',.16,.025),('Heavy coin macro',.13,.027)]:
        coin_details(O[name],r,d,nickel,rim)
    if O.get('Physical edge alloy'):
        remove_tree(O['Physical edge alloy'])
    for name in ['Pressed blade','Single sale blade']+[f'Six output blade {i}' for i in range(6)]:
        slotted_blade(O[name],silver,edge)
    slotted_blade(O['Coin reflected razor silhouette'],iron,edge)
    # Reflect the blade as inlaid art on the coin face, rather than a floating object.
    O['Coin reflected razor silhouette'].location.y=-.018
    glint=G.obj('V2 coin glint',parent=O['Loop hero coin'])
    glint.location=(0,-.017,0)
    glint_mat=G.emission('Spark hot ivory','#FFF1BF',2.8)
    G.line('Coin glint diagonal',[(-.026,0,-.04),(.026,0,.04)],.003,glint_mat,glint)
    spark=G.obj('V2 press spark',parent=O['Barber press'])
    spark.location=(.02,-.11,.103)
    for i in range(5):
        angle=.27+i*.51
        G.line('Impact spark',[(0,0,0),(.085*math.cos(angle),-.023,.085*math.sin(angle))],.003,glint_mat,spark)
    box('Mint lever bolted mounting bracket',(-.62,-.38,1.15),(.21,.70,.16),iron,O['Mint press assembly'],.028,.005)
    G.cylinder('Mint lever mounting pin',(-.81,-.70,1.15),(-.57,-.70,1.15),.066,brass,O['Mint press assembly'],20,.004)
    box('Thick coin cancellation paper',(-1.30,-.13,1.012),(.53,.25,.007),M['White cotton'],mint,.003,.002)
    mark=O['Physical red cancelled impression']
    mark.data.body='CANCELLED'
    mark.data.size=.069
    mark.location=(-1.30,-.142,1.018)
    material(O['Mint plaque'],GRAPHIC)
    O['Brass chai kettle'].location.x=-1.13
    O['Brass chai kettle'].scale=(.62,)*3
    for o in [o for o in market.children if o.name.startswith(('Chai kettle spout','Chai kettle arch handle'))]:
        o.location=(-1.13-2*.62,.50*(1-.62),1.08*(1-.62))
        o.scale=(.62,)*3
    for i in range(6):
        root=G.obj(f'V2 scale blade {i}',parent=O['Scale pan 1'])
        root.scale=(.74,.74,.74)
        root.rotation_euler=(math.pi/2,0,.18*(i-2.5))
        root.location=(.05,.028,.029+i*.004)
        slotted_blade(root,silver,edge)

def apply():
    costumes()
    sets_and_props()
    for name,y in [('Barber',1.18),('Shopkeeper',1.11),('Trader',1.17),('Smuggler',1.13),('Officer',.47)]:
        O[name].location.y=y
    O['Officer'].location.x=-.59
    for name in ('Shopkeeper','Trader','Smuggler','Officer'):
        for o in O[name].children:
            if ' leg ' in o.name:o.data.bevel_depth=.034
    for o in list(O):
        if o.type=='MESH' and 'flat dark hand' in o.name and not o.children:
            G.ink(o,.003)
    look.enforce_shadow_policy(bpy.context.scene)
