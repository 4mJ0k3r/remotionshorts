"""Original cast, environment and props for The Pigeon Inspector."""
import math
import random

import bpy
import numpy as np
from mathutils import Vector

import ricks_v2_kit as kit


def artwork(name, paint):
    size = 768
    y, x = np.ogrid[0:1:complex(size), 0:1:complex(size)]
    rgba = np.zeros((size, size, 4), dtype=np.float32)
    rgba[:, :, :3] = (.011, .007, .013)

    def fill(mask, color):
        rgba[mask] = (*color, 1)

    def oval(cx, cy, rx, ry, color, wobble=0):
        a, b = (x - cx)/rx, (y - cy)/ry
        fill(a*a + b*b < 1 + wobble*np.sin(3*np.arctan2(b, a)), color)

    def stroke(x0, y0, x1, y1, width, color):
        dx, dy = x1-x0, y1-y0
        t = np.clip(((x-x0)*dx+(y-y0)*dy)/(dx*dx+dy*dy), 0, 1)
        fill((x-x0-t*dx)**2+(y-y0-t*dy)**2 < width**2, color)

    paint(oval, stroke)
    image = bpy.data.images.new(name, width=size, height=size, alpha=True)
    image.pixels.foreach_set(rgba.ravel())
    image.pack()
    return image


def face(name):
    def paint(oval, line):
        ink, white = (.013,.007,.016), (.96,.94,.92)
        expressions = {
            "reading": (.055, -.036, .562, .10),
            "gust": (.093, -.018, .565, .126),
            "following": (.071, .034, .543, .08),
            "reach": (.052, -.027, .537, .08),
            "inspect": (.083, -.012, .571, .092),
            "deadpan": (.036, .005, .577, .12),
        }
        height, gaze, eyeline, mouth = expressions[name]
        for i, x in enumerate((.273,.692)):
            oval(x, eyeline, .091, height+.012, ink, .08)
            oval(x, eyeline+.001, .077, height, white, .06)
            oval(x+gaze, eyeline-(.014 if name in {"reading","reach","following"} else 0),
                 .030 if name != "gust" else .025, min(height,.048), ink, .10)
            brow = eyeline+height+.072+(.022 if i == 0 else 0)
            wing = -.033 if (i == 0) ^ (name == "gust") else .017
            line(x-.08,brow+wing,x+.072,brow-wing,.018,ink)
        if name == "gust":
            oval(.487,.279,.053,.065,ink,.21)
        else:
            slope = .008 if name == "deadpan" else .022
            line(.493-mouth,.273,.493,.27,.013,ink)
            line(.493,.27,.493+mouth,.273+slope,.013,ink)
        line(.46,.451,.49,.418,.009,(.35,.20,.17))
        line(.49,.418,.524,.425,.008,(.35,.20,.17))
    return artwork("Commuter ink | " + name, paint)


def jacket_art():
    def paint(oval, line):
        ink, piping, trim = (.10,.030,.031), (.78,.33,.112), (.91,.62,.265)
        line(.493,.09,.55,.75,.019,ink)
        line(.552,.74,.26,.91,.023,ink)
        line(.55,.74,.78,.91,.027,ink)
        line(.18,.34,.37,.39,.027,ink)
        line(.647,.39,.811,.35,.025,ink)
        line(.184,.37,.355,.415,.009,trim)
        line(.657,.42,.803,.384,.009,piping)
        for x,y in ((.566,.63),(.545,.48),(.532,.31),(.518,.17)):
            oval(x,y,.021,.014,ink,.08)
            oval(x-.004,y+.003,.009,.006,trim)
    return artwork("Commuter ink | seams, welt pockets and buttons", paint)


def block(col, name, loc, size, mat, bevel=0, parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1)
    obj = kit.put(bpy.context.object, col, parent, mat)
    obj.name, obj.location = name, loc
    for v in obj.data.vertices:
        for i in range(3):
            v.co[i] *= size[i]
    if bevel:
        mod = obj.modifiers.new("Rolled edges", "BEVEL")
        mod.width, mod.segments = bevel, 1
        obj.modifiers.new("Weighted normals", "WEIGHTED_NORMAL")
    return obj


def platform(col):
    rng = random.Random(64)
    tile = [kit.texture("Vitrified slate " + str(i), palette, "plaster") for i,palette in enumerate((
        ("#34495A","#506473","#637789"), ("#354D5C","#4D6677","#677A88"),
        ("#3A515F","#536A79","#62778A"), ("#394757","#50606E","#667482"),
    ))]
    grout = kit.surface("Blue-black grout", "#273847")
    accent = kit.surface("Stippled amber enamel", "#D79B49")
    slate = kit.surface("Bullnose edge stone", "#607683")
    steel = kit.surface("Bench frame | black teal enamel", "#223B43", .46, .22)
    steel_light = kit.surface("Station ironwork | teal enamel", "#375B62", .55, .20)
    brass = kit.surface("Burnished rivets", "#C99458", .43, .42)
    wood = kit.texture("Bench | amber-stained slats", ("#48292D","#774332","#B1784D"), "wood")
    dark = kit.surface("Track bed / deep shadow", "#222A39")
    rail = kit.surface("Running rails", "#747980", .31, .63)
    wall = kit.texture("Opposite platform | blue ceramic", ("#253C4E","#3C5262","#526776"), "plaster")
    plaster = kit.surface("Frieze | warm concrete", "#717D7D")
    glass = kit.emission("Morning light through frosted panes", "#D79E75", .65)
    pale = kit.emission("Warm high panes", "#F2C895", .8)

    def b(name, loc, size, material, bevel=0):
        return block(col, name, loc, size, material, bevel)

    b("Platform slab", (0,-.90,-.15), (18,4.52,.28), grout,.023)
    for i in range(-10,11):
        for j in range(-4,4):
            x = i*.73 + (.365 if j%2 else 0)
            y = j*.55
            b("Staggered platform paver",(x,y,-.018),(.721,.541,.036),rng.choice(tile),.005)
    b("Tactile strip bed",(0,1.51,.001),(17,.185,.026),accent,.006)
    for i in range(-49,50):
        for y in (1.463,1.548):
            kit.ball("Raised tread",(col),(i*.149,y,.015),(.024,.024,.008),accent,segments=8,rings=4)
    b("Platform nosing",(0,1.85,-.069),(18,.31,.154),slate,.015)
    b("Track trench",(0,2.82,-.45),(18,2.10,.26),dark)
    for i in range(-14,15):
        b("Rail sleeper",(i*.56,2.84,-.292),(.16,1.51,.072),wood,.012)
    for y in (2.24,3.40):
        b("Rail web",(0,y,-.238),(18,.03,.11),steel)
        b("Rail head",(0,y,-.17),(18,.074,.041),rail,.008)
    b("Far platform",(0,4.09,-.13),(18,.82,.22),slate,.015)
    b("Opposite station wall",(0,5.12,2.35),(18,.4,5.8),wall,.025)
    b("Upper station spandrel",(0,4.91,3.66),(18,.13,.50),plaster,.012)
    b("Canopy fascia",(0,1.31,2.98),(18,.31,.28),steel,.024)
    b("Enamel fascia highlight",(0,1.132,2.93),(18,.026,.024),steel_light,.005)
    for z in (.28,.75,2.47,3.40):
        b("Continuous station moulding",(0,4.87,z),(18,.17,.09),steel_light,.016)
    for x in (-6,-3.9,-1.8,.3,2.4,4.5,6.6):
        b("Opposite wall pier",(x-.95,4.84,1.65),(.18,.22,3.4),plaster,.028)
        b("Recessed frame",(x,4.87,1.60),(1.7,.14,1.36),steel,.044)
        for dx in (-.51,0,.51):
            for z in (1.355,1.958):
                b("Frosted glazing",(x+dx,4.78,z),(.477,.045,.53 if z>1.5 else .61),pale if z>1.5 else glass,.022)
        for z in (1.09,1.67,2.24):
            b("Window muntin",(x,4.74,z),(1.57,.045,.031),steel_light,.006)
    for x in (-4.2,-2.16,2.95,5.46):
        b("Canopy column", (x,1.26,1.47),(.115,.115,2.94),steel_light,.02)
        b("Cast column plinth",(x,1.26,.11),(.23,.23,.22),steel,.025)
        b("Canopy cross beam",(x,.30,2.92),(.14,2.30,.12),steel,.01)
        kit.tube("Cantilever strut",col,[(x,1.23,2.28),(x,.95,2.61),(x,.42,2.89)],.024,steel_light)
        b("Frosted pendant",(x,.41,2.82),(.33,.18,.06),pale,.018)

    for x,y in ((-.05,-.22),(1.06,-.22),(-.05,.21),(1.06,.21)):
        b("Bench cast leg",(x,y,.231),(.078,.078,.462),steel,.014)
        b("Bench anchor foot",(x,y,.019),(.138,.102,.039),steel_light,.009)
        for dx in (-.044,.044):
            kit.ball("Bench anchor bolt",col,(x+dx,y,.04),(.012,.012,.009),brass,segments=10,rings=6)
    for x in (-.05,1.06):
        b("Seat bearer",(x,0,.414),(.092,.55,.065),steel,.012)
        b("Bench upright",(x,.249,.647),(.064,.071,.57),steel,.015)
        kit.tube("Curled bench arm",col,[(x,-.21,.47),(x,-.19,.63),(x,.02,.675),(x,.24,.64)],.023,steel)
    for y in (-.217,-.104,.009,.122,.235):
        b("Bench oiled seat slat",(.420,y,.471),(1.50,.100,.063),wood,.015)
        for x in (-.05,1.06):
            kit.ball("Flush slat screw",col,(x,y,.503),(.014,.014,.004),brass,segments=12,rings=6)
    for z in (.66,.787,.914):
        b("Bench backrest slat",(.420,.274,z),(1.50,.068,.111),wood,.015)
    for i in range(85):
        x,y = rng.uniform(-4,5),rng.uniform(-1.6,1.39)
        mat = slate if i%3==0 else grout
        b("Small paving aggregate",(x,y,.002),(rng.uniform(.014,.055),.007,.003),mat)
    kit.make_ricks_light("Warm morning across the tracks",col,(-2.55,3.38,4.25),(0,-.13,.15),"#FFBE87",690,3.2)
    kit.make_ricks_light("Cool station fill",col,(1.3,-2.9,3.7),(.5,.15,.45),"#B8DEFF",390,4.0)
    kit.make_ricks_light("Rake under bench",col,(3.2,-.15,1.7),(.48,-.1,.10),"#FFD5AA",95,1.5)


HALF = (.148,.082)
HOLE = (.054,.002, .033)
GRIP = Vector((-.129,-.022,0))


def ticket(col):
    root = kit.empty("Ticket | motion and grip origin",col)
    stock = kit.emission("Ticket | butter card stock","#FFF2CC",1.05)
    edge = kit.emission("Ticket | warm cut edge","#432B2E")
    teal = kit.emission("Ticket | teal service band","#41878A")
    ochre = kit.emission("Ticket | vermilion stripe","#DD9161")
    cx,cy,radius = HOLE
    n = 64
    angles = [i*math.tau/n for i in range(n)]
    angles += [math.atan2(y-cy,x-cx)%math.tau for x in (-HALF[0],HALF[0]) for y in (-HALF[1],HALF[1])]
    outside, inside = [], []
    for angle in sorted(angles):
        cos,sin = math.cos(angle),math.sin(angle)
        tx = ((math.copysign(HALF[0],cos)-cx)/cos) if abs(cos)>1e-8 else math.inf
        ty = ((math.copysign(HALF[1],sin)-cy)/sin) if abs(sin)>1e-8 else math.inf
        t = min(tx,ty)
        outside.append((cx+t*cos,cy+t*sin))
        r = radius*(1+.045*math.sin(angle*5)+.036*math.cos(angle*3))
        inside.append((cx+r*cos,cy+r*sin))
    n = len(outside)
    verts = [(x,y,z) for z in (.0026,-.0026) for loop in (outside,inside) for x,y in loop]
    faces, edges = [], []
    for i in range(n):
        j = (i+1)%n
        faces.extend([(i,j,j+n,i+n),(i+2*n,i+3*n,j+3*n,j+2*n)])
        edges.extend([(i,i+2*n,j+2*n,j),(i+n,j+n,j+3*n,i+3*n)])
    punched = kit.mesh("Ticket | pierced paper with open cut edge",col,verts,faces+edges,stock,root)
    punched.data.materials.append(edge)
    for poly in punched.data.polygons[len(faces):]:
        poly.material_index = 1
    plug = kit.mesh("Ticket | removable chad",col,verts[n:2*n]+verts[3*n:4*n],
                    [tuple(range(n)),tuple(reversed(range(n,2*n)))],stock,root)
    for side in (-1,1):
        block(col,"Ticket | teal band",(-.106,0,side*.0027),(.025,.151,.0002),teal,parent=root)
        block(col,"Ticket | apricot rule",(-.076,0,side*.0027),(.008,.151,.0002),ochre,parent=root)
        for j in range(7):
            block(col,"Ticket | die-cut guide dash",(-.047,(j-3)*.019,side*.0027),
                  (.003,.008,.0002),edge,parent=root)
    return root, plug


def commuter(col):
    rig = kit.build_ricks_character("Commuter",col,costume_image=jacket_art(),
                                    expression_images={k:face(k) for k in (
                                        "reading","gust","following","reach","inspect","deadpan")})
    body = bpy.data.objects["Commuter | graphic pill torso"]
    body.data.materials[0] = kit.make_cel_character_material("Commuter | persimmon canvas","#BA5D39")
    hair = bpy.data.objects["Commuter | shaped hair cap"]
    hair.data.materials[0] = kit.make_cel_character_material("Commuter | plum brown hair","#4C2F3B")
    streak = kit.make_cel_character_material("Commuter | painted hair streak","#794950")
    for child in rig.head.children:
        if "swept chestnut highlight" in child.name:
            child.data.materials[0] = streak
    drawn_look = __import__("ricks_drawn_look")
    drawn_look.apply_drawn_look(rig,col,head_shape="potato",head_width=1.03,
                               face="#FFF1DA",face_shadow="#CCB7B4",face_shadow_amount=.69,
                               light_dir=(-.41,-.71,.56),fists=False)
    skin = kit.emission("Commuter | hand pigment","#F4C698")
    warm = kit.emission("Commuter | hand shadow","#CA8B72")
    cuff = kit.emission("Commuter | cuff binding","#8B413A")
    hands = []
    for side in (-1,1):
        hand = kit.empty("Commuter | articulated pinch" if side<0 else "Commuter | loose hand",col)
        def part(name,loc,radii,mat,ink=.0028):
            obj = kit.ball(name,col,loc,radii,mat,hand,segments=16,rings=10)
            kit.apply_character_ink(obj,col).strength=-ink
            return obj
        part("Canvas cuff",(-.023,0,0),(.026,.026,.019),cuff)
        part("Palm",(.001,-.008,.001),(.034,.028,.022),skin)
        part("Curled middle and ring fingers",(.016,-.029,.003),(.022,.014,.014),warm)
        index = part("Index | upper pinch pad",(.040,.001,.014),(.025,.014,.0105),skin,.0022)
        thumb = part("Thumb | lower pinch pad",(.033,.010,-.014),(.023,.016,.0105),skin,.0022)
        hands.append((hand,index,thumb))
    for foot in rig.feet:
        for v in foot.data.vertices:
            v.co.x *= 1.25
            v.co.y *= 1.45
    return rig,hands


def pigeon(col):
    root = kit.empty("Pigeon | body control",col)
    head = kit.empty("Pigeon | head and beak",col,parent=root)
    ink = kit.emission("Pigeon | detail ink","#252236")
    grey = kit.make_cel_character_material("Pigeon | slate feathers","#8D9DB0")
    wing = kit.make_cel_character_material("Pigeon | blue mantle","#697F99")
    bars = kit.make_cel_character_material("Pigeon | two flight bars","#3E4B63")
    neck = kit.make_cel_character_material("Pigeon | green bib","#4C8D80")
    breast = kit.make_cel_character_material("Pigeon | lavender throat","#777291")
    beak = kit.emission("Pigeon | beak horn","#48394B")
    cere = kit.emission("Pigeon | pale cere","#E0CDD1")
    iris = kit.emission("Pigeon | marigold iris","#FFAE4D")
    glint = kit.emission("Pigeon | eye glint","#FFF2D5")
    pink = kit.emission("Pigeon | coral feet","#C97571")
    light_pink = kit.emission("Pigeon | toe scales","#E6A096")

    def plumage(name,loc,radii,mat,parent=root,ink_width=.003):
        obj = kit.ball(name,col,loc,radii,mat,parent,segments=24,rings=16)
        if ink_width:
            kit.apply_character_ink(obj,col).strength=-ink_width
        return obj

    plumage("Pigeon | pear-shaped body",(0,0,0),(.173,.119,.124),grey).rotation_euler.y=-.13
    plumage("Pigeon | breast",(-.066,0,.014),(.082,.095,.083),breast,ink_width=0)
    collar = plumage("Pigeon | articulated green neck",(-.122,0,.075),(.075,.092,.092),neck,ink_width=.0019)
    for y in (-.034,0,.034):
        plumage("Pigeon | tail quill",(.163,y,-.006),(.122,.033,.027),bars).rotation_euler.y=.28
    for side in (-1,1):
        y = side*.090
        plumage("Pigeon | folded wing",(.029,y,.016),(.151,.038,.084),wing).rotation_euler.y=.26
        for x,z in ((.055,.022),(.102,.005)):
            plumage("Pigeon | flight bar",(x,side*.119,z),(.017,.010,.058),bars,ink_width=0).rotation_euler.y=-.32
    plumage("Pigeon | round head",(0,0,0),(.089,.078,.085),grey,head)
    plumage("Pigeon | cere",(-.080,0,-.022),(.033,.039,.025),cere,head,.002)
    tip = (-.162,0,-.039)
    corn = [(-.073,-.036,-.012),(-.073,.036,-.012),(-.067,0,-.052),tip]
    cone = kit.mesh("Pigeon | pointed beak",col,corn,[(0,2,1),(0,1,3),(1,2,3),(2,0,3)],beak,head)
    kit.apply_prop_ink(cone,col,thickness=.0018)
    for side in (-1,1):
        plumage("Pigeon | eye rim",(-.028,side*.070,.020),(.035,.010,.032),ink,head,0)
        plumage("Pigeon | iris",(-.032,side*.079,.020),(.027,.008,.026),iris,head,0)
        plumage("Pigeon | pupil",(-.038,side*.085,.019),(.016,.006,.019),ink,head,0)
        plumage("Pigeon | glint",(-.043,side*.090,.028),(.006,.002,.006),glint,head,0)
    feet = []
    for side in (-1,1):
        foot = kit.empty("Pigeon | planted foot " + str(side),col)
        for j,dy in enumerate((-.036,0,.034)):
            kit.tube("Pigeon | splayed toe",col,[(.011,0,.012),(-.016,dy*.63,.010),
                     (-.044- .007*(j==1),dy,.007)],.008,pink,foot)
            plumage("Pigeon | toe tip",(-.043-.007*(j==1),dy,.008),(.010,.008,.007),light_pink,foot,0)
        kit.tube("Pigeon | rear toe",col,[(0,0,.014),(.023,.008,.009),(.035,.012,.007)],.007,pink,foot)
        shank = tuple(kit.ball("Pigeon | " + segment,col,(0,0,0),(.011,.011,1),pink,
                               segments=12,rings=8) for segment in ("upper shank","lower shank"))
        feet.append((foot,shank))
    return root,head,collar,Vector(tip),feet
