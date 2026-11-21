"""Two physically separated stages with practical lighting and original dressing."""
from math import cos, pi, sin
from random import Random

from model import ball, beam, box, cylinder, emission, light, mesh, outline, surface, texture, tube


def apartment(c):
    timber = texture("Desk | oiled figured walnut", ("#3B1D1C", "#8D4727", "#B5763D"), "wood")
    pale = surface("Paper | parchment", "#E8D4AE")
    plaster = texture("Apartment | cobalt plaster", ("#15203A", "#223252", "#374660"), "plaster")
    dark = surface("Trim | midnight blue", "#1A213B")
    teal = surface("Lamp | glazed petrol enamel", "#217074", .28, .45)
    copper = surface("Lamp | aged brass", "#9B6343", .34, .58)
    glass = emission("Window | late blue hour", "#376DBA", .73)
    hot = emission("Tungsten | filament", "#FFB15F", 7)
    coffee = surface("Coffee | dark liquid", "#381D17", .18)
    floor = texture("Apartment | blue-stained oak", ("#151D2E", "#2B354F", "#423848"), "wood")
    box("Apartment wall", c, (0, 1.52, 1.50), (8, .14, 3), plaster)
    box("Apartment floor", c, (0, -.4, -.05), (8, 5, .1), floor)
    for i in range(-5, 6):
        box("Floor | board join", c, (i*.48, -.55, .001), (.014, 4.1, .004), dark, 0)
    box("Wall baseboard", c, (0, 1.42, .09), (7.9, .075, .17), dark, .014)
    box("Night window", c, (.25, 1.405, 1.58), (1.34, .06, 1.18), dark, .025, ink=.008)
    pane = box("Blue window glass", c, (.25, 1.36, 1.58), (1.23, .018, 1.064), glass, .008)
    pane.visible_shadow = False
    for i in range(12):
        slat = box(f"Venetian blind {i+1}", c, (.25, 1.31, 1.079+i*.091),
                   (1.23, .073, .055), dark, .005)
        slat.rotation_euler.x = .25
    for x in (-.23, .73):
        box("Blind pull tape", c, (x, 1.265, 1.57), (.016, .018, 1.15), copper, .003)
    box("Window sill", c, (.25, 1.29, 1.006), (1.49, .22, .055), dark, .012, ink=.006)
    box("Poster | walnut frame", c, (-1.12, 1.407, 1.76), (.52, .055, .67), timber, .02, ink=.006)
    box("Poster | indigo stock", c, (-1.12, 1.371, 1.76), (.45, .015, .59), dark, .008)
    poster_ink = surface("Poster lime ink", "#E3B876", glow=.36)
    mesh("Poster | three-color geometry", c, [(-1.29, 1.359, 1.611), (-1.17, 1.359, 1.96),
         (-1.04, 1.359, 1.68), (-.94, 1.359, 1.895), (-.96, 1.359, 1.60)], [(0, 1, 2), (2, 3, 4)], poster_ink)
    box("Floating shelf", c, (1.22, 1.33, 1.56), (.63, .29, .05), timber, .013, ink=.005)
    box("Lower shelf", c, (1.2, 1.33, 1.08), (.6, .27, .048), timber, .012)
    spines = [surface("Cloth binding", color) for color in ("#2D636C", "#8A4C48", "#A27840", "#435785")]
    for i in range(6):
        box("Book | cloth spine", c, (1.0+i*.062, 1.31, 1.15+.024*(i%3)),
            (.048, .15, .09+.047*(i%3)), spines[i%4], .005)
    cylinder("Plant | terracotta pot", c, (1.18, 1.29, 1.64), .082, .131, spines[1], r2=.101)
    plant = surface("Plant | jade", "#406D62")
    for i in range(9):
        a = i*2.4
        x, y, z = 1.18+cos(a)*.10, 1.29+sin(a)*.074, 1.733+.021*(i%4)
        tube("Plant | stem", c, [(1.18, 1.29, 1.652), ((x+1.18)/2, (y+1.29)/2, z-.042), (x,y,z)], .006, plant)
        leaf = ball("Plant | lance leaf", c, (x, y, z), (.026, .014, .071), plant, segments=10, rings=8)
        leaf.rotation_euler = (.42*sin(a), .67*cos(a), a)
    box("Desk top", c, (0, .066, .692), (1.96, .76, .101), timber, .035, ink=.007)
    box("Desk | brass band", c, (0, -.32, .674), (1.82, .013, .013), copper, .004)
    for x in (-.84, .84):
        for y in (-.22, .31):
            box("Desk | tapered support", c, (x, y, .344), (.088, .092, .65), timber, .019, ink=.004)
    box("Chair | curved back", c, (.13, .94, .785), (.46, .083, .44), teal, .04, ink=.009)
    box("Chair seat", c, (.13, .75, .48), (.46, .4, .077), teal, .028, ink=.006)
    for x in (-.045, .305):
        for y in (.63, .91):
            box("Chair leg", c, (x, y, .235), (.04, .043, .47), dark, .009)
    cyl = cylinder("Lamp | oval base", c, (-.65, .04, .771), .138, .044, teal)
    cyl.scale.y = .78
    outline(cyl, c, .005)
    tube("Lamp | curved brass stem", c, [(-.68,.06,.79),(-.74,.08,1.01),(-.66,.04,1.28),(-.53,-.008,1.28)], .024, copper)
    shade = cylinder("Lamp | teal shade", c, (-.50, -.018, 1.255), .151, .151, teal, r2=.082)
    outline(shade, c, .006)
    cylinder("Lamp | brass shade lip", c, (-.50,-.018,1.180), .155, .018, copper)
    ball("Lamp | visible hot glass", c, (-.50,-.018,1.165), (.068,.068,.038), hot)
    beam("Lamp | amber dust cone", c, (-.50,-.018,1.173), (-.26,.015,.759), .065, .239, "#FFAC67")
    for i in range(3):
        sheet = box("Desk | loose paper", c, (.56+i*.022,.004+i*.009,.744+i*.004),
                    (.30,.21,.003), pale, .001)
        sheet.rotation_euler.z = -.18 + i*.17
    for i in range(3):
        box("Notebook | printed rule", c, (.61,.052+i*.027,.756), (.15,.004,.002), spines[2], 0)
    pencil = cylinder("Desk | cedar pencil", c, (.49,-.148,.759), .009, .225, copper, length_segments=8)
    pencil.rotation_euler = (pi/2, .28, 0)
    mug = surface("Mug | sea green porcelain", "#368889", .31)
    cyl = cylinder("Mug | porcelain shell", c, (.765,.17,.805), .061, .127, mug, r2=.073)
    outline(cyl, c, .004)
    cylinder("Mug | coffee meniscus", c, (.765,.17,.870), .063, .006, coffee)
    tube("Mug | loop handle", c, [(.824,.17,.846),(.873,.17,.851),(.889,.17,.811),(.827,.17,.783)], .010, mug)
    light("Desk lamp | tungsten pool", c, (-.49,-.07,1.16), (-.23,.08,.72), "#FFBA75", 28, .038, "SPOT", 87)
    light("Desk lamp | warm face bounce", c, (-.82,-.36,1.37), (.1,.52,1.23), "#FFAB60", 75, .49)
    light("Window | cobalt broad side", c, (.95,.27,1.77), (.14,.55,1.22), "#82A6FF", 86, 1.1)
    light("Apartment | cool ambient side", c, (.16,-1,2.14), (.38,.75,1.25), "#657DFF", 25, 1.25)
    moon = light("Window | raking blue slats", c, (.55,1.395,1.84), (.12,-.55,.6), "#77A8FF", 90, .025, "SPOT", 81)
    moon.data.shadow_maximum_resolution = .014


def alley(c, ox):
    def p(x, y, z):
        return (ox+x, y, z)

    rng = Random(8220)
    brick = [surface("Brick | kiln variation", v) for v in ("#453147","#503043","#52394A","#673D4C","#3C2E48")]
    plaster = texture("Alley | rainy violet plaster", ("#24223B", "#3A354F", "#555170"), "plaster")
    mortar = surface("Alley | blue mortar", "#2B2A43")
    steel = surface("Fire escape | blued steel", "#202640", .43, .52)
    bronze = surface("Shopfront | copper liner", "#A16744", .33, .48)
    wood = texture("Pawn counter | dark striped timber", ("#2B1E25", "#503037", "#81503F"), "wood")
    wet = texture("Street | .04 slick pools / .45 damp asphalt", ("#182236","#282640","#343248"),
                  "asphalt", (.04, .45))
    warm = emission("Shop | amber light", "#FFBB69", 3.3)
    peach = emission("Neon | coral", "#FF4775", 3)
    cyan = emission("Neon | turquoise", "#42DBF1", 3.6)
    honey = emission("Neon | honey", "#FFB84F", 2.5)
    purple = emission("Display | violet", "#9B79FF", 1.1)
    whites = surface("Awning | pale ochre", "#D4A876", .78)
    reds = surface("Awning | burnt crimson", "#8E3F58", .75)
    bottle = [surface("Shop bottle", x, .28, .14, .47) for x in
              ("#E48144","#669BB0","#7B72AB","#D85972","#A0BA6A")]
    box("Rain street & cobbled edges", c, p(0,-.5,-.066), (11,16,.128), wet, 0)
    for x in (-2.23, 2.26):
        box("Pavement curb", c, p(x,-.05,.051), (.22,13,.113), steel, .034, ink=.009)
        for j in range(24):
            box("Sidewalk | scored slab", c, p(x+(.17 if x>0 else -.17),-6+j*.51,.081),
                (.28,.49,.10), mortar, .012)
    # Left storefront is modular so the display has real recess and shelf depth.
    for y, size in ((-5.85, 2.3), (2.32, 4.5)):
        box("Left | row-house wall", c, p(-2.62,y,1.55), (.35,size,3.10), plaster, .03, ink=.01)
    box("Shop | upper masonry", c, p(-2.63,-2.0,2.66), (.36,5.62,1.01), plaster, .03, ink=.01)
    box("Shop | window kickboard", c, p(-2.53,-2,.31), (.36,5.60,.56), mortar, .025)
    box("Shop | recessed display backing", c, p(-2.93,-2.,1.34), (.08,5.49,1.63), wood, .02)
    for z in (.58, 1.05, 1.49, 1.92, 2.13):
        box("Display | timber sill & shelf", c, p(-2.64,-2.,z), (.59,5.52,.055), wood, .015, ink=.006)
        if .59 < z < 2:
            box("Display | amber LED strip", c, p(-2.43,-2.,z-.033), (.025,5.45,.017), warm, .004)
    for y in (-4.75,-3.40,-2.07,-.72,.69):
        box("Shop | outlined copper jamb", c, p(-2.34,y,1.36), (.14,.075,1.61), bronze, .013, ink=.008)
    for row, z in enumerate((.64, 1.10, 1.53)):
        for j in range(17):
            y = -4.63+j*.323+rng.uniform(-.045,.045)
            radius = rng.uniform(.045,.079)
            ht = rng.uniform(.09,.22)
            mat = bottle[(j+2*row)%len(bottle)]
            if (j+row)%4:
                cylinder("Display | colored flask", c, p(-2.64,y,z+ht*.5), radius, ht, mat, r2=radius*.72, length_segments=12)
                cylinder("Display | cork seal", c, p(-2.64,y,z+ht+.011), radius*.51, .032, bronze, length_segments=8)
            else:
                box("Display | parcel", c, p(-2.67,y,z+ht*.5), (.11,.16,ht), mat, .015)
    for row in range(5):
        for j in range(14):
            y = -4.65+j*.41+(row%2)*.18
            box("Recessed shop | brick trim", c, p(-2.428,y,2.3+row*.123), (.047,.39,.108),
                rng.choice(brick), .012)
    for j in range(18):
        stripe = box("Striped canvas awning", c, p(-2.19,-4.69+j*.318,2.18),
                     (.77,.316,.048), reds if j%2 else whites, .011)
        stripe.rotation_euler.y = .24
        skirt = box("Awning | scalloped edging", c, p(-1.816,-4.69+j*.318,2.055),
                    (.042,.31,.112), reds if j%2 else whites, .022)
        if j in (0,17):
            outline(skirt, c, .007)
    for y in (-4.77, .77):
        tube("Awning | iron end rail", c, [p(-2.48,y,2.28),p(-2.01,y,2.17),p(-1.81,y,2.10)], .018, steel)
    for y in (-4.64, .59):
        box("Window neon | cyan vertical", c, p(-2.32,y,1.42), (.025,.024,1.31), cyan, .006)
    box("Window neon | rose top strip", c, p(-2.29,-2.04,1.99), (.026,5.26,.025), peach, .008)
    for y in (1.35, 2.63):
        box("Fire escape deck", c, p(-2.16,y,2.22), (.68,.97,.073), steel, .011, ink=.009)
        for j in range(5):
            box("Fire escape | slender baluster", c, p(-1.82,y-.41+j*.205,2.49),
                (.035,.035,.52), steel, .006)
        box("Fire escape | handrail", c, p(-1.82,y,2.74), (.052,.99,.04), steel, .007)
    for j in range(8):
        box("Fire escape | steel tread", c, p(-2.07,3.07+j*.155,2.22+j*.10), (.48,.17,.039), steel, .004)
    for y in (-5.75,-1.62,2.51,6.49):
        box("Right | high warehouse blocks", c, p(2.92,y,2.07), (1,4.0,4.16), plaster, .045, ink=.01)
        for z in (1.43, 2.59, 3.34):
            box("Warehouse | inset window", c, p(2.404,y+.19,z), (.04,.78,.46), steel, .018)
            box("Warehouse | distant lilac glass", c, p(2.377,y+.19,z), (.018,.68,.34), purple, .012)
            for offset in (-.23, 0, .23):
                box("Warehouse | mullion", c, p(2.358,y+.19+offset,z), (.023,.022,.35), mortar, .005)
        box("Warehouse | rain downpipe", c, p(2.39,y-1.46,1.81), (.078,.074,3.6), steel, .02)
    for j in range(7):
        x = (1.88 if j%2 else -1.94)
        y = -5.14+j*1.59
        box("Alley | shipping crate", c, p(x,y,.219), (.40,.37,.396), wood, .022, ink=.008)
        for dx in (-.127,.127):
            box("Crate | cedar strap", c, p(x+dx,y-.194,.22), (.057,.03,.36), bronze, .007)
    box("Pawnbroker | violet back wall", c, p(0,3.89,1.18), (2.08,.21,2.35), plaster, .02, ink=.012)
    for x in (-1.02,1.02):
        box("Pawn stall | timber post", c, p(x,2.77,1.08), (.1,.13,2.16), wood, .019, ink=.009)
    box("Pawn stall | canopy", c, p(0,3.21,2.12), (2.25,1.25,.14), wood, .025, ink=.011)
    box("Pawn counter | fascia", c, p(0,2.71,.449), (2.02,.59,.86), wood, .04, ink=.012)
    box("Pawn counter | worktop", c, p(0,2.67,.884), (2.14,.67,.075), wood, .026, ink=.009)
    box("Pawn counter | aged brass escutcheon", c, p(0,2.393,.626), (1.89,.02,.043), bronze, .008)
    for x in (-.93,-.72):
        box("Counter | glass divider frame", c, p(x, 2.58,1.095), (.018,.028,.353), bronze, .006)
    # Slightly translucent safety glass, left of the actor and cube sight lines.
    glass = surface("Counter | tinted clear glass", "#75B7BC", .11, .3)
    n, links = glass.node_tree.nodes, glass.node_tree.links
    opaque = next(node for node in n if node.type == "BSDF_PRINCIPLED")
    out = next(node for node in n if node.type == "OUTPUT_MATERIAL")
    clear, blend = n.new("ShaderNodeBsdfTransparent"), n.new("ShaderNodeMixShader")
    blend.inputs[0].default_value = .16
    links.new(clear.outputs[0], blend.inputs[1])
    links.new(opaque.outputs[0], blend.inputs[2])
    links.new(blend.outputs[0], out.inputs[0])
    glass.surface_render_method = "BLENDED"
    look_glass = box("Counter | glass divider", c, p(-.825,2.58,1.092), (.21,.012,.33), glass, .003)
    look_glass.visible_shadow = False
    for i, z in enumerate((.985, 1.245, 1.51, 1.765)):
        box("Backlit shelf", c, p(0,3.62,z), (1.92,.43,.061), wood, .012)
        for j in range(9):
            size = rng.uniform(.065,.135)
            x = -.83+j*.21
            if i in (1,2) and abs(x)<.31:
                continue
            cube = box("Memory archive | colored cube", c, p(x,3.56+rng.uniform(-.07,.07),z+.035+size/2),
                       (size,size,size), (honey,cyan,purple,peach)[(j+i)%4], .011)
            cube.rotation_euler.z = rng.uniform(-.3,.3)
    tube("Counter | pendant cable", c, [p(-.12,2.71,2.1),p(-.12,2.71,1.96),p(-.12,2.71,1.84)], .013, steel)
    cylinder("Counter | brass bulb mount", c, p(-.12,2.71,1.84), .057,.073,bronze)
    bulb = ball("Counter | exposed filament bulb", c, p(-.12,2.71,1.78), (.066,.066,.084), warm)
    beam("Counter | golden cone", c, p(-.12,2.71,1.74), p(-.62,2.55,.94), .054,.34, "#FFC27B")
    light("Pawn | bulb key", c, p(-.15,2.67,1.77), p(.13,3.10,1.09), "#FFB87C", 31,.075,"SPOT",54)
    light("Pawn | amber counter bounce", c, p(-.99,2.45,1.43), p(-.31,1.91,1.14), "#FFC08A", 34,.37)
    light("Pawn | cobalt counter side", c, p(.64,2.37,1.66), p(-.31,1.91,1.15), "#7791FF", 49,.54)
    for y in (-4.45,-2.3,-.36):
        light("Shop | amber emission bounce", c, p(-2.26,y,1.44), p(.02,y,.29), "#FFAE6B", 82,1.35)
    bounce = light("Shop | warm window bounce on passing hero", c,
                   p(-1.91,1.17,1.36),p(-.31,-.25,1.16),"#FFAF76",48,1.06)
    bounce.data.use_shadow = False
    light("Alley | cyan wet rim", c, p(1.72,-2.8,1.89), p(-.15,-.5,.37), "#5B9CFF", 101,1.55)
    light("Alley | magenta wet rim", c, p(.86,-5.16,1.37), p(-.08,-2.5,.43), "#EA65B2", 67,1.09)
    light("Alley | overhead moon wash", c, p(0,1,5.5), p(0,0,0), "#859FFF", 210,4.8)
    moon = emission("Night | pearlescent moon", "#B7D9FF", 2.5)
    ball("Night | full moon", c, p(-.68,11.31,4.01), (.44,.15,.44), moon, segments=32, rings=20)
    cloud = emission("Night | blue cloud silhouette", "#455577", .42)
    for i in range(8):
        ball("Night | soft cloud banks", c, p(-2.9+i*.76,11.1+.04*(i%2),3.25+.26*cos(i)),
             (.63,.23,.14+.05*(i%3)), cloud, segments=12, rings=8)
    return bulb, honey, cyan
