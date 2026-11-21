"""Elon's deal, Mars launch, world power and the approved vault callback."""
import importlib.util
import json
from pathlib import Path
from random import Random
import struct
import sys
import wave

HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parent))
from sequence_tools import *

OUT=ROOT/"renders/padoda_billionaire/part5_v01"
END=619
CAL=(29,153,197,252,319,387,445,609)
BENCH=(*CAL,1,300,416,619)
GOLDEN=HERE.parent/"v04"
sys.path.insert(0,str(GOLDEN))
source=importlib.util.spec_from_file_location("approved_padoda_vault",GOLDEN/"build.py")
approved=importlib.util.module_from_spec(source)
source.loader.exec_module(approved)

def audio_envelope():
    with wave.open(str(OUT/"part5_narration.wav"),"rb") as file:
        pcm=file.readframes(file.getnframes())
        unit=file.getframerate()//30
    return [math.sqrt(sum(sample*sample for (sample,) in struct.iter_unpack("<h",pcm[i*unit*2:(i+1)*unit*2]))/unit)/32768
            for i in range(END)]

def yard(c):
    navy=k.texture("Courtyard deep blue pavement",("#192138","#252c49","#41435a"),"plaster",(.70,.8))
    concrete=k.texture("Industrial patio siding",("#25374c","#444c62","#66657d"),"plaster",(.71,.85))
    rails=k.surface("Painterly tower railings","#58657b",.72)
    glow=k.emission("Dim practical courtyard gold","#ffc673",1.9)
    green=k.emission("Matte green power tags","#9de659",1.66)
    box("Plant courtyard floor",c,(0,0,-.12),(22,25,.23),navy)
    box("Plant courtyard rear facade",c,(-.19,2.45,1.69),(8.3,.45,3.45),concrete,.055,True)
    box("Padoda Power Plant sign board",c,(.05,2.17,2.31),(3.48,.14,.45),navy,.026,True)
    text(c,"PADODA POWER PLANT",(.05,2.089,2.23),.227,glow)
    for i in range(9):
        x=-3.7+.92*i
        box("Dark seam in facade",c,(x,2.15,1.03),(.088,.125,2.04),rails,.023)
        box("Amber factory window",c,(x+.39,2.141,1.61),(.58,.042,.42),glow,.02,True)
        for x0 in (x+.26,x+.52):
            box("Vertical window bars",c,(x0,2.103,1.61),(.035,.03,.42),navy,.008)
    for i in range(8):
        x=-3+i*.79
        box("Painted courtyard lane marker",c,(x,-.65,.003),(.42,.060,.005),rails,.003)
    for x in (-2.58,2.48):
        k.cylinder("Bollard post",c,(x,.86,.35),.059,.71,rails,length_segments=14)
        k.cylinder("Bollard painted lamp",c,(x,.86,.71),.083,.062,green,length_segments=14)
        k.make_light_cone("Warm courtyard grazing cone",c,(x,1.66,2.54),(x,.47,.01),.12,.60,"#FFBC63")
    for i in range(4):
        x=-2.85+i*.33
        box("Staged fuel crates",c,(x,1.68,.186),(.31,.27,.37),rails,.025,True)
    k.make_ricks_light("Night blue courtyard light",c,(-2,1.51,3.16),(0,0,1.12),"#8BA9FF",235,1.65)
    k.make_ricks_light("Warm faces key",c,(-.68,-2.17,2.87),(0,0,1.04),"#FFB874",288,1.64)
    k.make_ricks_light("Cool frontal bounce",c,(2.67,-1.97,2.31),(0,0,1.21),"#98C3FF",221,1.54)
    can=k.empty("Green gold Padoda deal canister",c)
    k.cylinder("Brushed gold canister base",c,(0,0,-.093),.126,.053,rails,can,length_segments=22)
    k.cylinder("Glowing green deal canister",c,(0,0,0),.109,.158,green,can,length_segments=22)
    k.cylinder("Brushed gold canister lid",c,(0,0,.086),.130,.046,rails,can,length_segments=22)
    return can

def stars(c,height=25):
    mat=k.emission("Subdued star points","#d0e5ff",1.10)
    rng=Random(582)
    verts=[];faces=[]
    for _ in range(178):
        x=rng.uniform(-9,9); y=rng.uniform(5.4,11.0); z=rng.uniform(.7,height); d=rng.uniform(.007,.028)
        i=len(verts);verts.extend(((x-d,y,z),(x,y,z+d),(x+d,y,z),(x,y,z-d)))
        faces.append((i,i+1,i+2,i+3))
    k.mesh("Starfield in deep indigo sky",c,verts,faces,mat)

def rocket_stage(c):
    stars(c,27)
    white=k.surface("Painterly off-white rocket ceramics","#dbe0ec",.71,.13)
    black=k.surface("Ink black rocket hardware","#1c2438",.77,.22)
    cyan=k.emission("Cool edge indicator","#81dbf0",1.35)
    glow=k.emission("Powered green fuel hose","#80ed54",2.3)
    steel=k.surface("Blue charcoal gantry lattice","#4e617c",.71,.35)
    orange=k.emission("Golden thrust core","#ffd66c",3.35)
    floor=k.surface("Indigo launchpad hardstand","#273350",.79)
    box("SpaceX concrete launch deck",c,(0,0,-.12),(15,24,.22),floor)
    k.cylinder("Round raised launch pedestal",c,(0,0,.11),.66,.24,steel,length_segments=28)
    for x in (-1.44,-.91):
        for y in (.48,.85):
            rod("Gantry tower corner column",c,(x,y,.02),(x,y,3.85),.058,.053,steel,8)
    for i in range(8):
        z=.32+i*.44
        rod("Gantry horizontal rung",c,(-1.48,.48,z),(-.85,.48,z),.042,.042,steel,8)
        rod("Diagonal gantry cross-brace",c,(-1.42,.48,z),(-.89,.48,z+.35),.029,.028,steel,8)
    for i in range(5):
        box("Gantry work light",c,(-1.34,.395,.49+i*.70),(.19,.047,.052),cyan,.006)
    box("Fuel cart",c,(1.09,.34,.269),(.54,.59,.55),steel,.041,True)
    text(c,"PADODA FUEL",(1.10,.025,.295),.071,glow)
    hose=k.tube("Thick live Padoda Fuel hose",c,[(1.14,.24,.32),(1.12,-.18,.31),(.52,-.30,.31),(.18,-.18,.61)],
               .038,glow)
    root=k.empty("Ascending launch vehicle",c)
    k.cylinder("Rocket tall ceramic core",c,(0,0,1.32),.234,2.40,white,root,length_segments=28)
    k.cylinder("Rocket graphite tail ring",c,(0,0,.39),.241,.34,black,root,length_segments=28)
    k.cylinder("Black thermal seam",c,(0,0,2.23),.239,.111,black,root,length_segments=28)
    nose=k.ball("Ellipsoid rocket nose cone",c,(0,0,2.54),(.233,.233,.37),white,root,segments=26,rings=18)
    for x in (-.19,.19):
        k.mesh("Landing fin",c,[(x,-.06,.27),(x*1.96,-.023,.31),(x*1.95,.06,-.075),(x,.055,.04)],
               [(0,1,2,3)],black,root)
    for z in (1.54,1.66):
        disk("Rocket tiny window",c,(0,-.226,z),.032,.018,cyan,root)
    text(c,"SPACEX",(0,-.234,1.21),.104,black,root)
    plume=[]
    for i in range(9):
        plume.append(k.ball("Lime burner gradient plume",c,(0,0,0),(.17,.16,.42),
                           transparent("Soft neon motor flame","#83FF52" if i%3 else "#ffd45f",.66,2.35),
                           root,segments=12,rings=8))
    mars=k.ball("Rocky red Mars",c,(1.56,1.02,16.06),(.79,.79,.79),
        k.texture("Red Martian crater relief",("#4a242e","#a44336","#da7c50"),"plaster",(.79,.88)),
        segments=40,rings=28)
    k.make_ricks_light("Launchpad white-blue sky",c,(-2.1,-4.2,5.5),(0,0,1.33),"#9fc6ff",385,2.4)
    l=k.make_ricks_light("Launch engine hot key",c,(.32,-.32,1.4),(0,0,1.3),"#b5fa7d",160,.72)
    k.make_ricks_light("Mars sunlight",c,(1.6,-2.7,17.74),(1.56,1.02,16),"#ffd6ad",950,2.7)
    return root,plume,hose,mars,l

def earth_stage(c):
    stars(c,12)
    blue=k.texture("Earth blue ocean gradients",("#142b58","#205279","#45949d"),"plaster")
    land=k.surface("Blue emerald illustrated terrain","#529884",.79)
    gold=k.emission("Golden Padoda distribution routes","#ffc85d",2.45)
    center=vec((0,.72,1.55))
    rig=k.empty("Spinning powered Earth",c,center)
    k.ball("Dimensional Earth globe",c,(0,0,0),(.93,.93,.93),blue,rig,segments=46,rings=32)
    def point(lon,lat,r=.947):
        a,b=math.radians(lon),math.radians(lat)
        return vec((r*math.cos(b)*math.sin(a),-r*math.cos(b)*math.cos(a),r*math.sin(b)))
    outlines=[
        [(-88,56),(-69,66),(-43,52),(-40,28),(-55,17),(-62,27),(-78,31),(-86,44)],
        [(-56,17),(-36,11),(-29,-6),(-44,-39),(-49,-43),(-56,-24),(-61,-5)],
        [(-13,45),(19,55),(48,63),(78,63),(99,50),(97,25),(78,19),(61,11),(45,28),(29,23),(16,42)],
        [(-5,33),(29,32),(39,13),(24,-31),(10,-25),(-4,3),(-14,19)],
        [(67,-14),(92,-13),(103,-27),(83,-37),(65,-25)],
    ]
    for outline in outlines:
        pts=[point(*p) for p in outline]
        mid=vec((sum(p.x for p in pts),sum(p.y for p in pts),sum(p.z for p in pts))).normalized()*.946
        verts=[mid,*pts]
        k.mesh("Illustrated raised continental patch",c,verts,
               [(0,i+1,(i+1)%len(pts)+1) for i in range(len(pts))],land,rig)
    cities=[(55,20),(-52,33),(-41,-16),(9,43),(31,2),(79,-23),(88,41),(-62,49),(15,33)]
    routes=[]
    for lon,lat in cities[1:]:
        points=[point(55+(lon-55)*i/25,20+(lat-20)*i/25+math.sin(math.pi*i/25)*7,1.003) for i in range(26)]
        routes.append(k.tube("World power pipeline",c,points,.012,gold,rig))
        lamp=point(lon,lat,.986)
        k.ball("Golden distribution city",c,lamp,(.038,.038,.038),gold,rig,segments=10,rings=6)
    for z in (-.41,.26):
        pts=[point(i*360/48,math.degrees(math.asin(z)),.997) for i in range(49)]
        k.tube("Energy latitude orbit",c,pts,.009,gold,rig)
    k.make_ricks_light("World amber solar key",c,(-2.13,-2.38,3.94),(0,.72,1.59),"#ffdc85",244,1.68)
    k.make_ricks_light("Electric blue planet rim",c,(1.44,1.65,2.87),(0,.72,1.59),"#7dcaff",338,1.52)
    return rig,routes

def build():
    envelope=audio_envelope()
    s,cam=scene_setup(END,((1,0),(410,0),(411,.062),(412,.148),(413,.003),(414,0),
                           (472,0),(473,.070),(474,.148),(475,.002),(476,0),(END,0)))
    street=collection(s,"Padoda power plant courtyard")
    launch=collection(s,"Gantry and Mars flight",25)
    deal=collection(s,"Power plant deal courtyard",50)
    planet=collection(s,"Global power globe",75)
    vault=collection(s,"Golden Master vault callback",100)
    c=street[0]; d=deal[0]; v=vault[0]
    intro_can=yard(c); can=yard(d)
    box("Canister display plinth",d,(.013,-.14,.30),(.32,.31,.595),
        k.surface("Display plinth navy enamel","#273047",.78),.037,True)
    elon_images={image.stem:image for image in (HERE/"art").glob("*.png") if image.stem!="elon_jacket"}
    def musk(group,name):
        a=actor(group,name,elon_images,HERE/"art/elon_jacket.png",base="#1f2330")
        hair=bpy.data.objects[name+" | shaped hair cap"]
        hair.rotation_euler.z=-.34
        hair.scale.z=.91
        return a
    runner=musk(c,"Elon Musk"); hero=actor(c)
    elon=musk(d,"Elon Deal"); dealer=actor(d,"Hero Deal")
    air,plume,hose,mars,launch_spill=rocket_stage(launch[0])
    earth,routes=earth_stage(planet[0])
    bills,brass,golds,glow=approved.vault(v)
    king=actor(v,"Hero Vault")
    crown,glasses=approved.ornaments(v,king,golds[2],glow)
    goblet=k.empty("Raised green-gold Padoda cup",v)
    cup=k.emission("Lime energy in goblet","#aff56e",2.15)
    k.cylinder("Goblet brass base",v,(0,0,-.06),.05,.018,brass,goblet,length_segments=18)
    k.cylinder("Goblet gold stem",v,(0,0,-.013),.018,.09,brass,goblet,length_segments=16)
    k.cylinder("Pedestal cup bowl",v,(0,0,.058),.044,.112,brass,goblet,r2=.079,length_segments=22)
    k.cylinder("Power tonic surface",v,(0,0,.115),.074,.014,cup,goblet,length_segments=22)
    dustmat=transparent("Foot skid warm dust","#b79a81",.21,1.05)
    dust=[k.ball("Warm skid dust wisp",c,(0,0,0),(.128,.071,.044),dustmat,segments=12,rings=8)
          for _ in range(5)]
    ring_light=k.emission("Shape carried amber ring","#ffbf59",2)
    handoff=ring("Canister circular gold edge",d,(0,-.12,1.13),.16,ring_light)
    earth_ink=k.emission("Fading handoff ring gold","#ffbf59",2)
    nodes,links=earth_ink.node_tree.nodes,earth_ink.node_tree.links
    shader=next(node for node in nodes if node.type=="EMISSION")
    surface_out=next(node for node in nodes if node.type=="OUTPUT_MATERIAL")
    fade=nodes.new("ShaderNodeMixShader")
    links.new(nodes.new("ShaderNodeBsdfTransparent").outputs[0],fade.inputs[1])
    links.new(shader.outputs[0],fade.inputs[2])
    links.new(fade.outputs[0],surface_out.inputs["Surface"])
    earth_ink.surface_render_method="BLENDED"
    for frame,opacity in ((414,1),(415,.86),(416,.65),(417,.42),(418,.19),(419,.035),
                          (420,0),(471,0),(472,1)):
        fade.inputs[0].default_value=opacity
        key(fade.inputs[0],frame,"default_value")
    earth_ring=ring("Earth arrival amber ring",planet[0],(0,-.389,1.55),.91,earth_ink)
    vault_ring=ring("Vault matching outline",v,(-.28,4.57,2.39),2.14,ring_light,.028)
    lengths=king.measure_leg_lengths()
    rng=Random(89)
    bill_positions=[(rng.uniform(-2.50,2.50),rng.uniform(-1.1,3.1),rng.uniform(.49,3.58),rng.uniform(0,6.28))
                    for _ in bills]
    last_runner=last_elon=last_hero=None
    checks={}
    def run_route(f):
        return (-2.98+2.72*step(f,1,136),-.093-.13*step(f,1,122),0)
    for f in range(1,END+1):
        if f<=243:
            stand=vec((.415,.14,0)); run=vec(run_route(f))
            run_yaw=1.14
            grab=step(f,133,150)*(1-step(f,159,177))
            talk=step(f,179,193)
            run_yaw-=.47*step(f,111,149)
            stride=k.eval_stick_walk_cycle(f,run_route,run_yaw,start_frame=1,stop_frame=136,
                                          strength=1-.84*step(f,120,138),plant_yaw=1.14)
            pitch=stride.tilt*(1-step(f,122,146))+.085*grab
            bounce=stride.bounce*(1-step(f,122,145))
            legs=stride.legs if f<=136 else floor_legs()
            arms=list((vec(hand),vec(elbow)) for hand,elbow in stride.arms) if f<=136 else idle()
            for i,side in enumerate((-1,1)):
                pt=stand+vec((side*.102,-.024,.932))
                elbow=vec((side*.24,-.089,.32))
                hand=arms[i][0].lerp(contact(pt,run,run_yaw,pitch,bounce,elbow),grab)
                arms[i]=(hand,elbow)
                if f==153:checks[f"shoulder_{i}"]=measure_contact(arms[i],run,run_yaw,pitch,bounce,pt)
            arms[0]=(arms[0][0].lerp(vec((-.21,-.24,.79)),talk),arms[0][1])
            voice=envelope[f-1]
            expression=("awe" if f<176 else "rest" if f<181 or voice<.022 else
                        "talk2" if voice>.125 else "talk1" if voice>.061 else "talk0")
            runner.pose(f,run,run_yaw,pitch,arms,legs,expression if last_runner!=expression else None,
                        bounce=bounce,head_yaw=-.19,head_tilt=-.05*talk)
            last_runner=expression
            hero.pose(f,stand,-.24,.067,idle(),floor_legs(),"smug" if f==1 else None,
                      head_yaw=-.28,head_tilt=.078*grab)
            for item in intro_can.children:visible(item,False,f)
            for j,obj in enumerate(dust):
                t=step(f,128+j,152+j)
                obj.location=(-.78-.5*t-.10*j,-.32+.10*j,.057+.10*t)
                obj.scale=(max(.001,.78*math.sin(math.pi*t)),)*3
                key(obj,f,"location","scale")
            if f<166:
                t=step(f,1,156)
                follow=run.x*.83-.18
                p=vec((follow-.78,-3.23,1.10)).lerp(vec((.52,-3.31,1.24)),t)
                aim=(follow+.20,.05,.91)
                aim=vec(aim).lerp(vec((.02,.1,.96)),t)
                camera_pose(cam,street,f,p,aim,35)
            else:
                t=step(f,166,243)
                p=vec((1.29,-3.25,1.44)).lerp(vec((1.11,-2.96,1.41)),t)
                camera_pose(cam,street,f,p,(.012,.045,1.13),38,(-.18,-.16,1.22))
        elif f<=333:
            boost=step(f,251,329)
            altitude=14.17*boost
            air.location=(-.26+.78*boost,0,altitude)
            air.rotation_euler.y=.29*step(f,278,330)
            key(air,f,"location","rotation_euler")
            visible(hose,f<253,f)
            launch_spill.location.z=altitude+1.22
            launch_spill.data.energy=89+155*step(f,251,263)
            key(launch_spill,f,"location");key(launch_spill.data,f,"energy")
            for j,obj in enumerate(plume):
                obj.location=(.025*math.sin(f*.9+j),.02*math.cos(f*.6+j),.06-.129*j)
                growth=step(f,247,257)*(1-.31*step(f,312,331))
                obj.scale=(.94-.048*j,.80,.72+.44*math.sin(f*.8+j)**2)
                obj.scale*=growth
                key(obj,f,"location","scale")
                visible(obj,f>=248,f)
            shake=.055*math.sin(f*2.72)*(1-step(f,254,257)) if f>=253 else 0
            p=vec((1.53+.27*boost+shake,-5.2,1.91+altitude*.99))
            aim=(.24+.64*boost,.03,1.38+altitude)
            camera_pose(cam,launch,f,p,aim,37,air.location+vec((0,-.19,1.43)))
        elif f<=413:
            a,b=vec((-.51,.12,0)),vec((.50,.16,0))
            pose=step(f,337,353);repeat=(.027*math.sin(f*.60))*pose
            shake=vec((.011,-.194,.97+repeat))
            arms=idle();both=idle()
            for root,arr,i,yaw in ((a,arms,1,.30),(b,both,0,-.32)):
                elbow=vec(((1 if i else -1)*.31,-.11,.31))
                arr[i]=(arr[i][0].lerp(contact(shake,root,yaw,.17,0,elbow),pose),elbow)
            elon.pose(f,a,.30,.17,arms,floor_legs(),"grin" if f==334 else None,head_yaw=.18)
            dealer.pose(f,b,-.32,.17,both,floor_legs(),"smug" if f==334 else None,head_yaw=-.18)
            if f==387:
                checks["Elon handshake"]=measure_contact(arms[1],a,.30,.17,0,shake)
                checks["Hero handshake"]=measure_contact(both[0],b,-.32,.17,0,shake)
            can.location=(.013,-.14,.714)
            key(can,f,"location")
            visible(handoff,f>=410,f)
            t=step(f,399,413)
            p=vec((1.26,-3.21,1.29)).lerp(vec((.035,-1.38,1.11)),t)
            aim=vec((0,.02,1.01)).lerp(vec((0,-.12,1.13)),t)
            camera_pose(cam,deal,f,p,aim,37+3*t)
        elif f<=475:
            t=step(f,414,475)
            earth.rotation_euler=(.11,.14,.17+.59*t)
            key(earth,f,"rotation_euler")
            for j,route in enumerate(routes):
                route.data.bevel_factor_end=max(.0001,step(f,415+j*2,427+j*2))
                key(route.data,f,"bevel_factor_end")
            visible(earth_ring,f<=419 or f>=472,f)
            p=vec((.25,-3.34,1.67)).lerp(vec((1.21,-3.43,2.04)),t)
            camera_pose(cam,planet,f,p,(0,.73,1.56),39,(0,.02,1.57))
        else:
            cheer=step(f,479,499)
            settle=step(f,536,END-18)
            tilt=.08+.22*settle
            yaw=.18-.15*settle
            bounce=-.27
            basis=Euler((0,0,yaw)).to_matrix()
            body=Euler((tilt,0,0)).to_matrix()
            pelvis=vec((0,.817,1.425))
            root=pelvis-basis@(body@vec((0,0,.07))+vec((0,0,.59+bounce)))
            arms=idle()
            arms[0]=(arms[0][0].lerp(vec((-.28,-.19,.34)),cheer),arms[0][1])
            arms[1]=(arms[1][0].lerp(vec((.379,-.142,.536)),cheer),arms[1][1])
            legs=[]
            for side in (-1,1):
                ankle=basis.transposed()@(vec((side*.129,.563,1.313))-root)
                legs.append((ankle,(side*.17,-.55,.305)))
            face="smug" if f==476 else "wink" if f==END-17 else None
            king.pose(f,root,yaw,tilt,arms,legs,face,bounce=bounce,
                      head_tilt=-.087*settle,leg_lengths=lengths)
            crown.location=(.012,.039,.267); crown.rotation_euler=(.101,.17,-.15)
            glasses.location=(0,-.232,-.046)
            hand,elbow=arms[1]
            tip=root+basis@(body@(hand+(hand-elbow).normalized()*.016)+vec((0,0,.59+bounce)))
            goblet.location=tip+vec((.025,-.01,.029))
            goblet.rotation_euler=(.12,-.15+.32*cheer,-.20)
            key(goblet,f,"location","rotation_euler")
            t=step(f,478,END-18)
            p=vec((.01,-2.38,1.73)).lerp(vec((.31,-4.04,1.66)),t)
            aim=vec((.02,.68,1.98)).lerp(vec((.03,.79,1.71)),t)
            camera_pose(cam,vault,f,p,aim,35,(0,.58,2.02))
            visible(vault_ring,f<=479,f)
            for i,(bill,(x,y,z,a)) in enumerate(zip(bills,bill_positions)):
                pos=vec((x+.19*math.sin(f*.046+a),y+.12*math.sin(f*.039+a),z+.16*math.cos(f*.048+a)))
                if pos.y<1.21 and 1.49<pos.z<2.69 and abs(pos.x)<.63:
                    pos.x=math.copysign(.77+.08*math.cos(f*.036+a),x)
                bill.location=pos
                bill.rotation_euler=(.91+.31*math.cos(f*.074+a),.56*math.sin(f*.052+a),a+f*.039)
                key(bill,f,"location","rotation_euler")
    for group,first,last in ((street,1,243),(launch,244,333),(deal,334,413),(planet,414,475),(vault,476,END)):
        stage(group,first,last)
    assert max(checks.values())<.001
    (OUT/"contact_check.json").write_text(json.dumps(checks,indent=2))
    finish(s,OUT/"padoda_part5_v01.blend",(runner,hero,elon,dealer,king))

if __name__=="__main__":
    build()
