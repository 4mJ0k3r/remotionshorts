"""Original stylized historical environments; all surveillance graphics are illustrative."""
import math
from random import Random
import bpy
import ricks_v2_kit as k

def box(c,name,p,size,mat,ink=False,parent=None):
    bpy.ops.mesh.primitive_cube_add(size=1,location=p)
    obj=k.put(bpy.context.object,c,parent,mat)
    obj.name=name
    for v in obj.data.vertices:
        for i in range(3):
            v.co[i]*=size[i]
    if ink:k._ink_hull(obj,c,.0035,color=k.STUDIO_INK,strength=1.)
    return obj

def label(c,s,p,size,mat):
    data=bpy.data.curves.new(s,"FONT");data.body=s;data.size=size;data.align_x="CENTER"
    obj=k.put(bpy.data.objects.new(s,data),c,mat=mat)
    obj.location=p;obj.rotation_euler.x=math.pi/2
    return obj

def trace(c,name,points,r,mat,parent=None):
    obj=k.tube(name,c,points,r,mat,parent)
    obj.data.resolution_u=3
    obj.data.bevel_resolution=1
    return obj

def lights(c,warm="#ffc38b",blue="#7ca9ff"):
    k.make_ricks_light("Warm cinematic key",c,(-1.6,-2.3,2.74),(0,.1,1.15),warm,245,1.15)
    k.make_ricks_light("Soft indigo fill",c,(1.81,-1.19,2.12),(0,.1,1.22),blue,139,1.20)
    k.make_ricks_light("Cool contour light",c,(.74,1.6,2.35),(0,.1,1.17),blue,121,.74)

def war_room(c,rig):
    navy=k.texture("War room textured indigo",("#11162b","#273453","#53617d"),"plaster",(.7,.85))
    slate=k.surface("Painted graphite consoles","#293043",.76)
    cyan=k.emission("Luminous aged CRT teal","#57c0c6",1.2)
    teal=k.emission("Glass raster base","#10313e",.9)
    rust=k.emission("Red search overlay","#e34854",1.62)
    muted=k.emission("Cream period dimensional lettering","#dcc69e",1.15)
    box(c,"Dark waxed floor",(0,-.5,-.13),(9,9,.25),navy)
    box(c,"Ribbed operation room wall",(0,2.55,2.36),(9,.2,5),navy)
    for x in (-2.99,-1.92,-.86,.24,1.33,2.42):
        box(c,"Architectural upright",(x,2.41,1.97),(.09,.14,3.87),slate,True)
    for row in range(3):
        for j in range(6):
            x=-2.68+j*1.06; z=.96+.62*row
            box(c,"Analog screen casing",(x,2.295,z),(.98,.18,.57),slate,True)
            box(c,"CRT panel",(x,2.187,z),(.87,.025,.45),teal)
            for i in range(7):
                y=z-.19+i*.060
                trace(c,"CRT fine scan lattice",[(x-.42,2.17,y),(x+.42,2.17,y)],.0025,cyan)
            for i in range(7):
                xx=x-.37+i*.14
                trace(c,"CRT grid vertical",[(xx,2.167,z-.211),(xx,2.167,z+.211)],.0025,cyan)
            pts=[(x-.36+i*.101,2.159,z+.09*math.sin(i*1.7+j+row)) for i in range(8)]
            trace(c,"Screen terrain waveform",pts,.009,rust if (j+row)%4==0 else cyan)
    box(c,"Front console worktop",(.40,.43,.782),(1.61,.97,.114),slate,True)
    box(c,"Desk bulkhead",(.44,.48,.37),(1.44,.65,.75),navy,True)
    label(c,"1998   /   INTELLIGENCE",(.43,-.039,.60),.075,muted)
    for i in range(14):
        box(c,"Console control light",(-.29+i*.093,-.047,.718),(.041,.012,.021),cyan if i%4 else rust)
    for j in range(13):
        x=-.22+j*.083
        trace(c,"Abstract terrain hologram",[(x,.03+i*.057,.96+.038*math.sin(i*.75+j*.43)) for i in range(13)],.004,cyan)
    for j in range(10):
        yy=.03+j*.065
        trace(c,"Terrain crosshair",[(i*.083-.22,yy,.956+.044*math.sin(i*.55+j*.61)) for i in range(13)],.004,cyan)
    label(c,"RAJASTHAN",(.28,.002,1.05),.087,muted)
    for x in (-1.4,1.44):
        shade=k.surface("Copper lamp shade","#885642",.71)
        k.cylinder("Period console ceiling lamp",c,(x,.95,2.96),.24,.20,shade,r2=.13,length_segments=20)
        k.make_light_cone("Practical light cone",c,(x,.95,2.85),(x,.89,.81),.16,.64,"#ffd090")
    light_rim=k.emission("Eyeglass line",k.STUDIO_INK)
    for side in (-1,1):
        x=side*.096
        trace(c,"Rectangular analyst glasses",[(x-.060,-.225,.018),(x-.059,-.235,.088),
              (x+.061,-.235,.087),(x+.059,-.225,.017),(x-.060,-.225,.018)],.007,light_rim,rig.head)
    trace(c,"Eyeglass bridge",[(-.039,-.231,.067),(.038,-.231,.067)],.006,light_rim,rig.head)
    mug=k.empty("Porcelain coffee mug",c)
    k.cylinder("Coffee cup shell",c,(0,0,0),.074,.145,muted,mug,length_segments=24)
    k.cylinder("Coffee surface",c,(0,0,.073),.063,.010,slate,mug,length_segments=24)
    trace(c,"Coffee handle",[(.07+.043*math.cos(i*math.tau/20),0,.047*math.sin(i*math.tau/20)) for i in range(21)],.009,muted,mug)
    lights(c)
    return mug

def orbit(c):
    gold=k.texture("Crinkled golden insulation",("#764125","#c48243","#f3ba64"),"plaster")
    gun=k.surface("Ceramic graphite","#293954",.73)
    blue=k.emission("Photovoltaic cobalt","#254f92",1.1)
    line=k.emission("Solar solder joints","#77b0d9",1.46)
    red=k.emission("Illustrative red sweep","#f34359",2.3)
    root=k.empty("Illustrative spy satellite",c,(0,.22,1.36))
    box(c,"Gold foil spacecraft core",(0,0,0),(.63,.61,.64),gold,True,root)
    for j in range(5):
        box(c,"Instrument rails",(0,-.34,-.25+.118*j),(.62,.07,.021),gun,False,root)
    optic=k.cylinder("Telescope outer housing",c,(0,-.46,-.06),.24,.32,gun,root,length_segments=28)
    optic.rotation_euler.x=math.pi/2
    lens=k.cylinder("Deep indigo aperture",c,(0,-.632,-.06),.172,.048,blue,root,length_segments=26)
    lens.rotation_euler.x=math.pi/2
    for side in (-1,1):
        x=side*1.00
        box(c,"Solar array panel",(x,.02,.016),(1.21,.065,.61),blue,True,root)
        for j in range(13):
            xx=x-.58+j*.096
            trace(c,"Solar cell vertical seam",[(xx,-.025,-.282),(xx,-.025,.314)],.005,line,root)
        for j in range(8):
            z=-.273+j*.080
            trace(c,"Solar cell horizontal seam",[(x-.60,-.025,z),(x+.60,-.025,z)],.005,line,root)
    k.ball("Earth limb against space",c,(0,5.3,-4.0),(6,3.3,5.55),
           k.texture("Painterly Earth horizon",("#183266","#2b6088","#6b9e9c"),"plaster"),segments=42,rings=24)
    rng=Random(27)
    verts=[]; faces=[]
    for _ in range(290):
        x,z=rng.uniform(-7,7),rng.uniform(-2,5)
        v=len(verts); r=rng.uniform(.008,.027)
        verts.extend(((x-r,5,z),(x,5,z+r),(x+r,5,z),(x,5,z-r)));faces.append(tuple(range(v,v+4)))
    k.mesh("Period title star field",c,verts,faces,line)
    for i in range(15):
        x=-2.4+i*.34
        trace(c,"Symbolic scanning grid",[(x,.12,-.23),(x,3.7,-.23)],.010,red)
    for i in range(13):
        y=.1+i*.29
        trace(c,"Symbolic cross-scan", [(-2.4,y,-.23),(2.44,y,-.23)],.010,red)
    sweep=trace(c,"Moving scan-line accent",[(-2.32,0,-.21),(2.34,0,-.21)],.021,red)
    lights(c)
    return root,sweep

def cutaway(c):
    sand=k.texture("Thar sandstone cross section",("#50343d","#ab6b4e","#d68c55"),"plaster")
    stone=k.texture("Lower textured stone",("#362639","#684c50","#9c6560"),"plaster")
    brass=k.surface("Symbolic sealed cylinders","#465467",.77)
    glow=k.emission("Five amber test markers","#f0b86d",1.48)
    laser=k.emission("Stylized passing scan","#f04558",1.78)
    ridge=[(-4+i*.16,1.88+.124*math.sin(i*.17)+.09*math.sin(i*.43)) for i in range(51)]
    front=[(x,.64,z) for x,z in ridge]+[(4,.64,-1.0),(-4,.64,-1.0)]
    k.mesh("Earthen illustrative cutaway",c,front,[tuple(reversed(range(len(front))))],sand)
    for i in range(22):
        z=i*.128-.98
        points=[(-4+j*.2,.609,z+.037*math.sin(j*.49+i)+.036*math.sin(i*1.7+j*.23)) for j in range(41)]
        trace(c,"Layered sandstone cross-section stratum",points,.015,stone)
    for j in range(5):
        x=(j-2)*.61
        box(c,"Illustrative dark cutaway bay",(x,.563,.76),(.36,.06,1.46),stone,True)
        for k0 in range(9):
            box(c,"Cross section shadow hatch",(x,.522,.16+k0*.151),(.32,.019,.017),brass)
        k.ball("Sealed symbolic test canister",c,(x,.44,.62),(.122,.088,.242),brass,segments=20,rings=14)
        for z in (.49,.70):
            k.cylinder("Amber canister rim",c,(x,.44,z),.126,.026,glow,length_segments=24)
        label(c,str(j+1),(x,.336,.31),.123,glow)
    rng=Random(35)
    for j in range(80):
        x=rng.uniform(-4,4);z=rng.uniform(-.16,1.86)
        trace(c,"Illustrated stone hatch",[(x,.616,z),(x+.054,.615,z+.04)],.008,stone)
    trace(c,"High red scan over dune ridge",[(-4,.53,2.20),(4,.53,2.20)],.014,laser)
    lights(c,"#ffd0a1","#889acc")
    return next(n for n in glow.node_tree.nodes if n.type=="EMISSION").inputs["Strength"]
