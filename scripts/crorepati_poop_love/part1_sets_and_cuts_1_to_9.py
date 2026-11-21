"""Act I architecture and the connected mansion threshold/foyer."""
import math

def build(g):
    street=g.root('SET_STREET',0);stone=g.surface('Evening cobbles','626777','99938b','stone')
    g.boxx('Street cobblestone ground',(0,1,-.06),(12,14,.12),stone,street,False)
    g.sky(street,['111c43','47578e','edbd91']);g.lighting(street,True,5,'ffc996')
    for side in [-1,1]:
        for i in range(3):
            x=side*(2.0+i*.8);g.boxx('Dusk shop masonry',(x,3.4+i*.35,1.55),(1.35,.6,3.1),['746779','8d7381','637387'][i],street)
            g.boxx('Shop recessed window',(x,3.06+i*.35,1.65),(.70,.04,1.20),'263242',street)
            g.boxx('Shop amber glass',(x,3.025+i*.35,1.65),(.58,.018,1.07),g.mat('efbc76',em=.65),street,False)
        g.lamp('Street lantern '+str(side),(side*1.55,1.0,2.5),street)
    wall=g.surface('Street garden masonry','687174','a1a095','stone')
    g.boxx('Street rear garden wall',(0,3.65,.50),(12,.28,1.0),wall,street)
    g.boxx('Garden wall stone coping',(0,3.65,1.06),(12,.37,.13),'b8b1a0',street)
    for i in range(49):
        x=-6+i*.25;g.bar('Garden iron upright',(x,3.60,1.10),(x,3.60,1.94),.014,'303344',street)
    for z in [1.26,1.78]:g.bar('Garden fence horizontal',(-6,3.60,z),(6,3.60,z),.020,'303344',street)
    for i in range(6):
        x=-5.3+i*2.12;h=3.1+(i%3)*.65
        g.boxx('Layered rear town facade',(x,5.45,h/2),(1.94,.6,h),['656479','877585','767f82'][i%3],street)
        g.boxx('Townhouse roof cornice',(x,5.45,h),(2.07,.71,.12),'a4a0a2',street)
        for dx in [-.43,.43]:
            for z in [1.5,2.45]:
                g.boxx('Rear window recess',(x+dx,5.125,z),(.49,.06,.66),'303447',street)
                g.boxx('Warm rear window',(x+dx,5.085,z),(.38,.012,.54),g.mat('ffc47b',em=.75),street,False)
    for x,y,s in [(-2.65,4.15,.75),(2.65,4.35,.85),(-4.3,4.6,.9),(4.5,4.7,.95)]:g.tree('Layered street garden tree',(x,y,0),street,s)
    coin=g.torus('RollingBronzeCoin',(0,0,0),.038,.010,'b58149',None,.8);coin.scale.z=.3
    for i in range(2):
        flap=g.link('EmptyPocket'+str(i));points=[(-.06,.045,0),(.06,.045,0),(.075,-.035,.004),(.045,-.13,.007),(-.025,-.15,.004),(-.067,-.06,0)]
        g.meshx('White turned out cloth',points,[tuple(range(6))],g.mat('f3eee5',rough=1),flap)
        g.curve('Pocket stitched cloth edge',points+[points[0]],.0025,g.mat('8e8584'),flap)
        g.curve('Pocket soft fold',[(-.03,.03,.002),(-.015,-.04,.007),(-.025,-.12,.010)],.003,g.mat('b9b2aa'),flap)

    park=g.root('SET_PARK',25);g.sky(park,['18385b','6e9bb0','f3d5a6']);g.lighting(park,True,5,'ffdfb4')
    g.boxx('Park flagstones',(0,1,-.05),(12,14,.10),g.surface('Park paving','9a9685','c2b69b'),park,False)
    booth=g.link('ParkRestroom',p=park)
    for x in [-.84,.84]:g.boxx('Restroom timber side',(x,1.5,1.35),(.16,1.2,2.7),'587366',booth)
    g.boxx('Restroom back',(0,2.03,1.35),(1.8,.15,2.7),'426358',booth)
    g.boxx('Restroom roof',(0,1.4,2.78),(2.1,1.7,.20),'6c4d37',booth)
    g.door('ParkDoor',booth,-.72,.95,1.44,2.6,1,'6b785e')
    for x in [-.78,.78]:g.boxx('Restroom door jamb',(x,.87,1.35),(.10,.16,2.7),'bca776',booth)
    for x,y in [(-2.3,2.0),(2.5,2.8),(-1.9,4.6),(1.5,5.0)]:g.tree('Park layered canopy',(x,y,0),park,.9)
    lock=g.link('ParkPadlock',p=park,xyz=(0,.77,1.43))
    shackle=g.torus('Iron shackle',(0,0,-.04),.15,.025,'869299',lock,.75);shackle.rotation_euler.x=math.pi/2
    g.boxx('Heavy padlock body',(0,-.02,-.23),(.29,.14,.30),'4e5d66',lock,bevel=.035)
    g.sphere('Padlock dark keyhole',(0,-.097,-.23),(.027,.007,.037),'17252f',lock)
    for i in range(17):
        x=-.68+i*.085;z=1.53-.11*math.sin(i/16*math.pi)
        o=g.torus('Linked iron security chain',(x,.77,z),.055,.010,'65747d',park,.7);o.rotation_euler=(math.pi/2,math.pi/2*(i%2),0)
    g.boxx('Park bench seat',(-1.65,.20,.46),(.80,.40,.08),'976b43',park)
    for x in [-1.95,-1.35]:g.boxx('Park bench iron foot',(x,.20,.22),(.045,.32,.44),'293d3d',park)

    cafe=g.root('SET_CAFE',50);g.sky(cafe,['193159','6190af','e7cda5']);g.lighting(cafe,True,5,'ffd7a5')
    g.boxx('Cafe sidewalk',(0,1,-.06),(12,14,.12),g.surface('Cafe stone sidewalk','97928c','c9bdad'),cafe,False)
    brick=g.surface('Cafe brick','81493d','b0785c','brick')
    for x,w in [(-2.0,2.2),(2.0,2.2)]:g.boxx('Cafe brick facade',(x,1.4,1.9),(w,.28,3.8),brick,cafe,False)
    g.boxx('Cafe lintel',(0,1.4,3.28),(1.8,.28,1.0),brick,cafe,False)
    g.door('CafeDoor',cafe,-.68,1.20,1.36,2.75,1,'334c4c')
    for x in [-1.6,1.6]:
        g.boxx('Cafe window frame',(x,1.20,1.65),(1.25,.12,1.65),'263d40',cafe)
        g.boxx('Warm cafe glazing',(x,1.125,1.65),(1.08,.025,1.45),g.mat('ffce83',em=.65),cafe,False)
    for i in range(14):
        x=-2.6+i*.4;canopy=g.boxx('Striped awning',(x,.70,2.96),(.39,1.1,.06),'c8c2a5' if i%2 else '9b3943',cafe);canopy.rotation_euler.x=.18
    g.boxx('Cafe warm rear plaster',(0,3.2,1.3),(1.8,.10,2.6),'a5764d',cafe,False)
    g.boxx('Cafe inside timber floor',(0,2.1,-.015),(1.6,2.1,.05),g.surface('Cafe interior wood','644630','a58158','wood'),cafe,False)
    for x in [-.75,.75]:g.boxx('Cafe brown timber door jamb',(x,1.15,1.4),(.14,.22,2.8),'74472e',cafe)
    g.boxx('Cafe brown timber door header',(0,1.15,2.8),(1.65,.22,.17),'74472e',cafe)
    g.light('Cafe warm doorway practical','AREA',(0,2.8,2.2),(0,.3,.9),180,'ffbd72',cafe).data.size=1.0
    g.boxx('Cafe service counter',(0,2.8,.65),(1.3,.45,1.3),'71452f',cafe)
    sign=g.label('Cafe awning lettering','CAFE',(0,.14,2.68),.20,g.mat('fff1c6',em=.20),cafe)
    boot=g.link('CafeKickingBoot',p=cafe)
    g.bar('Kick trouser shin',(0,0,0),(0,-.35,0),.065,'303a45',boot)
    g.sphere('Cafe leather boot',(0,-.39,-.03),(.10,.18,.08),'30262a',boot,rough=.32)
    g.sphere('Cafe boot sole',(0,-.42,-.09),(.11,.19,.025),'17181d',boot)

    mansion=g.room('SET_MANSION',75,'d9c6a4')
    entrance=g.link('EntranceArchitecture',p=mansion)
    for x in [-2.8,2.8]:g.boxx('Mansion stone facade',(x,1.5,2.15),(3.5,.34,4.3),'bcb2a1',entrance,False)
    g.boxx('Mansion upper lintel',(0,1.5,3.75),(2.3,.34,1.1),'d1bd98',entrance)
    for x in [-1.45,1.45]:
        g.bar('Fluted marble column',(x,1.05,.15),(x,1.05,3.3),.18,'e2d3b8',entrance)
        for j in range(12):
            a=j*math.tau/12;g.bar('Column carved flute',(x+.17*math.cos(a),1.05+.17*math.sin(a),.25),(x+.17*math.cos(a),1.05+.17*math.sin(a),3.2),.013,'b6a47e',entrance)
        for z in [.18,3.27]:g.boxx('Column capital',(x,1.05,z),(.50,.50,.15),'ebdabe',entrance)
    for i in range(3):g.boxx('Mansion marble step',(0,-.3+i*.35,.02*(i+1)),(3.25,1.30-i*.30,.04*(i+1)),g.surface('Exterior marble','b3aa98','e6d9bf','marble'),entrance)
    g.boxx('Mansion threshold platform',(0,1.25,.06),(2.8,1.10,.12),'d4c3a3',entrance)
    g.door('MansionDoorL',entrance,-1.0,1.28,1.0,3.15,1,'633725').location.z=.12
    g.door('MansionDoorR',entrance,1.0,1.28,1.0,3.15,-1,'633725').location.z=.12
    for x in [-1.9,1.9]:g.lamp('Mansion gold sconce '+str(x),(x,1.0,2.45),entrance)
    g.light('Golden foyer doorway spill','AREA',(0,2.0,2.7),(0,.5,1),100,'ffc477',mansion).data.size=1.5
    # Broad stair flight, individually supported marble steps and a recessed landing.
    for i in range(9):
        y=3.6+i*.23;z=.06*(i+1);g.boxx('Grand staircase tread',(0,y,z),(2.55,.26,z*2),'d8cbb3',mansion)
        g.boxx('Stair red carpet',(0,y,z*2+.008),(1.23,.25,.012),'842b3d',mansion,False)
    for side in [-1,1]:
        for i in range(9):g.bar('Stair baluster',(side*1.25,3.6+i*.23,.12+i*.12),(side*1.25,3.6+i*.23,.90+i*.12),.024,'926e3c',mansion)
        g.bar('Stair brass handrail',(side*1.25,3.6,.94),(side*1.25,5.44,1.90),.038,'c1a05c',mansion)
    g.boxx('Foyer woven runner',(0,2.45,.012),(1.85,4.2,.02),g.surface('Foyer carpet weave','6b263a','ac4150','weave'),mansion,False)
    chandelier=g.link('ChandelierPivot',p=mansion,xyz=(0,2.70,3.98))
    g.bar('Chandelier chain',(0,0,0),(0,0,-.43),.020,'c59b49',chandelier)
    g.torus('Chandelier gold crown',(0,0,-.65),.70,.028,'d5ae5a',chandelier,.8)
    for i in range(12):
        a=i*math.tau/12;x=.7*math.cos(a);y=.7*math.sin(a)
        g.bar('Chandelier curved spoke',(0,0,-.43),(x,y,-.65),.019,'bc9243',chandelier)
        g.sphere('Chandelier candle flame',(x,y,-.53),(.025,.025,.10),'ffeac1',chandelier,em=3)
        g.sphere('Crystal pendant',(x,y,-.86),(.045,.045,.13),'b9e2ee',chandelier,metal=.25,rough=.10)
    g.light('Chandelier practical','POINT',(0,2.7,3.05),(0,0,0),35,'ffd393',mansion)
    for x in [-2.8,2.8]:
        g.boxx('Foyer console cabinet',(x,3.0,.7),(.7,.5,1.4),'694636',mansion)
        g.tree('Decorative indoor foliage',(x,3.3,0),mansion,.50)
    # Props used in the montage/proposal; ownership and visibility are shot state.
    paper=g.link('FoldedNewspaper');g.boxx('Blank folded newspaper',(0,0,0),(.28,.018,.22),'d9d6c8',paper,False)
    for i in range(6):g.boxx('Newspaper column marks',(-.07+i*.028,-.012,0),(.008,.003,.15),'999384',paper,False)
    for i in range(2):
        case=g.link('LeatherSuitcase'+str(i));g.boxx('Suitcase body',(0,0,.22),(.40,.23,.44),'76533d',case,bevel=.04)
        g.bar('Suitcase handle',(-.06,0,.46),(.06,0,.46),.018,'c7a170',case)
        for dx in [-.13,.13]:g.boxx('Suitcase leather strap',(dx,-.124,.22),(.035,.009,.39),'b58b5b',case)
    plunger=g.link('GoldenPlunger');g.bar('Golden plunger scepter',(0,0,0),(0,0,.75),.022,'dbaf4c',plunger)
    g.sphere('Plunger golden cup',(0,0,0),(.15,.15,.09),'d8a937',plunger,metal=.92,rough=.14)
    return {'street':street,'park':park,'cafe':cafe,'mansion':mansion}
