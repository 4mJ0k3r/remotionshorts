"""Schoolyard, bus cabin, and Friday crossing sets."""
import math

from feature_scene import block, daylights, k, lettering, line, outdoor_sky


def clock_face(c,m,x,y,z):
    dial=k.cylinder("Ivory tower clock dial",c,(x,y,z),.287,.045,m["cream"],length_segments=40)
    dial.rotation_euler.x=math.pi/2
    for j in range(12):
        a=j*math.tau/12
        line(c,"Clock hour tick",[(x+.231*math.sin(a),y-.027,z+.231*math.cos(a)),
             (x+.257*math.sin(a),y-.027,z+.257*math.cos(a))],.010,m["ink"])
    line(c,"Clock hands",[(x-.115,y-.039,z+.083),(x,y-.039,z),(x+.025,y-.039,z+.17)],.014,m["ink"])


def school(c,m,offset=0,depth=3.4,*,yard=False):
    if yard:
        outdoor_sky(c,m)
        daylights(c)
        block(c,"School courtyard warm limestone paving",(0,.2,-.096),(17,11,.191),m["ground"])
    for x in (offset-3.05,offset,offset+3.05):
        block(c,"Brick school wing",(x,depth,1.46),(3.12,.48,2.92),m["brick"])
        block(c,"Cornice and roof coping",(x,depth-.13,2.93),(3.18,.57,.13),m["cream"])
        for u in (-1.04,0,1.04):
            for z in (.74,1.81,2.46):
                block(c,"Deep limestone window reveal",(x+u,depth-.262,z),(.58,.076,.51),m["cream"])
                block(c,"Blue school window",(x+u,depth-.306,z),(.478,.036,.426),m["glass"])
                block(c,"Window mullion",(x+u,depth-.331,z),(.027,.025,.426),m["cream"])
    block(c,"Square masonry clock tower",(offset,depth+.05,3.49),(1.39,.63,1.62),m["brick"])
    roof=block(c,"Clock tower hipped roof",(offset,depth+.03,4.32),(1.64,.91,.14),m["dark"])
    clock_face(c,m,offset,depth-.292,3.71)
    block(c,"School entrance stone surround",(offset,depth-.303,.89),(1.56,.093,1.82),m["cream"])
    block(c,"Twin blue school doors",(offset,depth-.363,.794),(1.37,.056,1.60),m["blue"])
    for x in (offset-.65,offset,offset+.65):
        block(c,"School door frame",(x,depth-.406,.80),(.055,.041,1.57),m["dark"])
    for x in (offset-.56,offset-.10,offset+.10,offset+.56):
        block(c,"Raised painted door bead molding",(x,depth-.406,.75),(.031,.042,1.33),m["cream"])
    for z in (.24,.42,.91,1.41):
        for x in (offset-.33,offset+.33):
            block(c,"Horizontal inset door bead molding",(x,depth-.411,z),(.49,.032,.028),m["cream"])
    for x in (offset-.19,offset+.19):
        block(c,"Brass handle mounted to school door",(x,depth-.433,.784),(.039,.036,.185),m["gold"])
    trim=offset-2.16
    block(c,"Fire bell pilaster",(trim,depth-.30,1.31),(.63,.15,2.62),m["brick"])
    for side in (-1,1):
        arm=offset+side*2.48
        for j in range(10):
            x=arm+(j-4.5)*.205
            line(c,"Wrought iron school gate picket",[(x,depth-.87,.08),(x,depth-.87,1.15+.18*math.cos(j*.38))],.017,m["dark"])
        for z in (.32,.88):
            line(c,"Wrought iron gate cross rail",[(arm-.97,depth-.87,z),(arm+.97,depth-.87,z)],.021,m["dark"])


def fire_bell(c,m,x,y,z):
    root=k.empty("Red school fire alarm bell",c,(x,y,z))
    block(c,"Red alarm mounting plate",(0,.046,0),(.62,.099,.62),m["red"],root)
    body=k.cylinder("Round spinning alarm gong",c,(0,-.035,0),.272,.153,m["red"],root,r2=.218,length_segments=40)
    body.rotation_euler.x=math.pi/2
    gold=k.cylinder("Brass gong striker nut",c,(0,-.12,0),.051,.052,m["cream"],root,length_segments=20)
    gold.rotation_euler.x=math.pi/2
    for a,b in ((-.24,-.24),(.24,-.24),(-.24,.24),(.24,.24)):
        bolt=k.cylinder("Bell housing fastener",c,(a,-.018,b),.019,.022,m["dark"],root,length_segments=9)
        bolt.rotation_euler.x=math.pi/2
    for radius in (.117,.152,.187):
        line(c,"Thin stamped red concentric gong detailing",
             [(radius*math.cos(i*math.tau/40),-.114,radius*math.sin(i*math.tau/40)) for i in range(41)],
             .0038,m["cream"],root)
    lettering(c,"FIRE ALARM",(0,-.007,-.39),.074,m["white"],root)
    return root


def crosswalk(c,m):
    for j in range(11):
        block(c,"Cream zebra crossing paint",(-.27,1.47+j*.112,.006),(.83,.067,.011),m["cream"])
    block(c,"Dropped curb approach to crossing",(-.27,1.27,.009),(.83,.24,.032),m["ground"])
    x,y=-1.04,1.08
    line(c,"Walk signal silver pole",[(x,y,.03),(x,y,2.01)],.026,m["dark"])
    block(c,"Pedestrian signal box",(x,y,1.81),(.22,.16,.30),m["dark"])
    green=k.emission("Walk signal mint green","#85f4a6",1.56)
    k.ball("Pedestrian walk symbol head",c,(x,y-.09,1.89),(.026,.007,.024),green,segments=12,rings=7)
    line(c,"Pedestrian walk symbol body",[(x,y-.092,1.856),(x-.02,y-.092,1.80),(x-.057,y-.092,1.761)],.012,green)
    line(c,"Pedestrian walk symbol arm",[(x-.041,y-.092,1.808),(x+.04,y-.092,1.832)],.010,green)
    line(c,"Pedestrian walk symbol leg",[(x-.02,y-.092,1.80),(x+.046,y-.092,1.761)],.012,green)


def bus(c,m):
    navy=k.surface("Matte woven lake-blue passenger seats","#4d5f7c",.84)
    tubing=k.surface("Brushed steel handrails","#7e90a1",.38,.38)
    block(c,"Mottled rubber bus floor",(0,.45,-.087),(2.51,7.2,.173),m["ground"])
    block(c,"Perforated cream bus ceiling",(0,.42,2.51),(2.63,7.1,.13),m["cream"])
    block(c,"Rear bus bulkhead",(0,3.59,1.26),(2.54,.1,2.5),m["blue"])
    daylight=k.emission("Sunny late afternoon behind the bus","#9abae4",.87)
    block(c,"Late afternoon strip outside the bus windows",(3.1,.05,1.42),(.06,11.7,3.69),daylight)
    k.make_ricks_light("Bus warm sun entering right side",c,(1.68,-.5,2.31),(-.31,.24,.98),"#ffc385",308,.88)
    k.make_ricks_light("Cool shaded seat fill",c,(-1.5,-1.6,1.96),(0,.2,.90),"#c9d7f9",140,1.42)
    k.make_ricks_light("Bus cabin skylight",c,(0,2.72,2.38),(0,0,.90),"#fff0da",120,1.28)
    for side in (-1,1):
        x=side*1.24
        for z,height in ((.385,.77),(2.318,.37)):
            block(c,"Lower and upper bus wall panels",(x,.43,z),(.08,7,.32 if z>2 else height),m["blue"])
        for z in (.81,2.13):
            line(c,"Brushed steel horizontal window channel",[(x,-2.93,z),(x,3.56,z)],.025,tubing)
        for y in (-2.64,-1.23,.25,1.73,3.20):
            block(c,"Rounded bus window division",(x,y,1.49),(.096,.146,1.48),m["dark"])
        for y in (-1.94,.15,1.31,2.43):
            xseat=side*(.79 if y!=.15 else .34)
            back=k.ball("Padded square bus seat back",c,(xseat,y+.34,.82),(.355,.120,.456),navy,segments=18,rings=13)
            back.rotation_euler.x=-.10
            k.ball("Soft blue passenger cushion",c,(xseat,y,.369),(.36,.333,.099),navy,segments=18,rings=10)
            for j in range(3):
                line(c,"Visible seat quilt seam",[(xseat-.245+j*.227,y+.228,.63),
                     (xseat-.245+j*.227,y+.222,1.055)],.005,m["blue"])
            line(c,"Grab bar curling over seat",[(xseat-.25,y+.285,.934),(xseat-.245,y+.26,1.20),
                 (xseat+.23,y+.26,1.23),(xseat+.27,y+.285,.935)],.021,tubing)
    for y in (-1.35,1.23,2.8):
        x=-1.08
        line(c,"Bus vertical boarding grab pole",[(x,y,.04),(x,y,2.46)],.026,tubing)
    for y in (-1.28,.4,2.16):
        block(c,"Recessed bus ceiling light",(.02,y,2.434),(.38,.50,.029),m["white"])
    backdrop=k.empty("Passing brick houses outside the school bus",c)
    for i in range(12):
        y=1.28*i-5.1
        block(c,"Passing brick house on bus route",(2.56,y,1.41),(.32,1.19,2.82),m["brick"],backdrop)
        for z in (1.02,1.95,2.34):
            block(c,"Sunlit window through bus glass",(2.38,y,z),(.04,.68,.31),m["glass"],backdrop)
            block(c,"Bright window surround",(2.35,y,z-.19),(.047,.75,.061),m["cream"],backdrop)
    sign=lettering(c,"BAKE SALE FRIDAY",(2.31,2.16,1.72),.107,m["white"],backdrop)
    sign.rotation_euler.z=-math.pi/2
    sign_back=block(c,"Bake sale burgundy banner",(2.40,2.16,1.77),(.055,1.44,.32),m["red"],backdrop)
    return backdrop
