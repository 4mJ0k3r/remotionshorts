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
    obj.data.resolution_u=1 if len(points)==2 else 3
    obj.data.bevel_resolution=1
    return obj

def lights(c,warm="#ffc38b",blue="#7ca9ff"):
    k.make_ricks_light("Warm cinematic key",c,(-1.6,-2.3,2.74),(0,.1,1.15),warm,245,1.15)
    k.make_ricks_light("Soft indigo fill",c,(1.81,-1.19,2.12),(0,.1,1.22),blue,139,1.20)
    k.make_ricks_light("Cool contour light",c,(.74,1.6,2.35),(0,.1,1.17),blue,121,.74)

def translucent(caption,color,alpha,strength):
    material=k.emission(caption,color,strength)
    material.surface_render_method="BLENDED"
    material.use_transparency_overlap=False
    nodes,links=material.node_tree.nodes,material.node_tree.links
    emission=next(n for n in nodes if n.type=="EMISSION")
    output=next(n for n in nodes if n.type=="OUTPUT_MATERIAL")
    mix=nodes.new("ShaderNodeMixShader")
    mix.inputs[0].default_value=alpha
    links.new(nodes.new("ShaderNodeBsdfTransparent").outputs[0],mix.inputs[1])
    links.new(emission.outputs[0],mix.inputs[2])
    links.new(mix.outputs[0],output.inputs[0])
    return material

def oval(c,name,x,y,z,rx,rz,mat,r=.005):
    return trace(c,name,[(x+rx*math.cos(i*math.tau/32),y,z+rz*math.sin(i*math.tau/32)) for i in range(33)],r,mat)

def monitor(c,x,z,mode,cyan,rust,muted):
    y=2.159
    if mode in (0,1,4):
        for i in range(7):
            xx=x-.37+i*.14
            z0=z-.19+i*.060
            trace(c,"CRT horizontal reticle",[(x-.42,y,z0),(x+.42,y,z0)],.0026,cyan)
            trace(c,"CRT vertical reticle",[(xx,y,z-.211),(xx,y,z+.211)],.0026,cyan)
    if mode==0:
        oval(c,"Orbit path in window",x,y-.009,z,.30,.13,muted)
        oval(c,"Planet reticle",x+.08,y-.011,z+.015,.11,.11,cyan)
        trace(c,"Observation marker",[(x-.18,y-.013,z+.10),(x-.095,y-.013,z+.10),
              (x-.095,y-.013,z+.15)],.009,rust)
    elif mode==1:
        for index in range(4):
            trace(c,"Aerial desert contour",[(x-.37+i*.105,y-.011,z-.139+index*.079+.038*math.sin(i*.83+index))
                  for i in range(8)],.005,muted)
    elif mode==2:
        for j in range(1,5):
            oval(c,"Analog radar sweep ring",x,y,z,.086*j,.049*j,cyan)
        trace(c,"Crimson radar sweep needle",[(x,y-.009,z),(x+.235,y-.009,z+.137)],.007,rust)
        trace(c,"Radar horizontal crosshair",[(x-.36,y,z),(x+.36,y,z)],.004,cyan)
        trace(c,"Radar vertical crosshair",[(x,y,z-.19),(x,y,z+.19)],.004,cyan)
    elif mode==3:
        for j in range(9):
            height=.10+.171*(.5+.5*math.sin(j*1.8))
            xx=x-.35+.086*j
            box(c,"Telemetry bar",(xx,y,z-.145+height*.5),(.047,.015,height),cyan if j%4 else muted)
        for j in range(3):
            trace(c,"Telemetry scale",[(x-.41,y,z+.075*j-.15),(x+.41,y,z+.075*j-.15)],.003,muted)
    else:
        trace(c,"Continuous telemetry waveform",[(x-.37+i*.067,y-.012,z+.091*math.sin(i*1.64))
              for i in range(12)],.009,rust)

def war_room(c,rig):
    navy=k.surface("Clean matte architectural navy","#152238",.83)
    floor=k.surface("Polished indigo slab floor","#263758",.42,.14)
    panel=k.surface("Blue acoustic architectural panels","#2e3d58",.77)
    rib=k.surface("Dark brushed upright steel","#52667d",.64,.22)
    slate=k.surface("Painted graphite consoles","#293043",.76)
    cyan=k.emission("Luminous aged CRT teal","#57c0c6",1.2)
    teal=k.emission("Glass raster base","#10313e",.9)
    rust=k.emission("Red search overlay","#e34854",1.62)
    muted=k.emission("Cream period dimensional lettering","#dcc69e",1.15)
    box(c,"Dark waxed floor",(0,-.5,-.13),(9,9,.25),floor)
    box(c,"Ribbed operation room wall",(0,2.55,2.36),(9,.2,5),navy)
    for j in range(9):
        x=-4+j*.97
        box(c,"Recessed architectural panel",(x+.44,2.427,2.34),(.88,.059,4.66),panel)
        box(c,"Steel architectural rib",(x,2.39,2.34),(.062,.095,4.69),rib,True)
        box(c,"Polished floor panel seam",(x,-.69,.0005),(.013,8,.008),navy)
    for j in range(9):
        z=.41+j*.43
        box(c,"Architectural rail",(.0,2.393,z),(8.6,.044,.018),rib)
    for row in range(3):
        for j in range(6):
            x=-2.68+j*1.06; z=.96+.62*row
            box(c,"Analog screen casing",(x,2.295,z),(.98,.18,.57),slate,True)
            box(c,"CRT panel",(x,2.187,z),(.87,.025,.45),teal)
            monitor(c,x,z,(j+row*2)%5,cyan,rust,muted)
    for x in (-1.68,.0,1.68):
        box(c,"Framed intelligence-map display",(x,2.315,2.86),(1.42,.12,.73),slate,True)
        box(c,"Inset atlas backing",(x,2.243,2.86),(1.29,.022,.61),teal)
        for j in range(5):
            trace(c,"World map latitude",[(x-.61+i*.122,2.23,2.64+j*.096+.02*math.sin(i*.31))
                  for i in range(11)],.003,cyan)
        for j in range(4):
            trace(c,"Framed atlas borders",[(x-.56+i*.114,2.221,2.77+.098*math.sin(i*.63+j*.72))
                  for i in range(11)],.009,muted)
    box(c,"Front console worktop",(.15,.44,.782),(1.78,1.04,.114),slate,True)
    box(c,"Opaque whole front desk panel",(.15,-.046,.377),(1.70,.072,.754),navy,True)
    box(c,"Inset plaque plate",(.12,-.090,.545),(1.18,.025,.21),slate,True)
    label(c,"1998 / INTELLIGENCE",(.12,-.106,.521),.078,muted)
    for j in range(7):
        box(c,"Front console cabinet seam",(-.59+j*.22,-.086,.22),(.012,.010,.27),rib)
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
        trace(c,"Single clean rectangular lens rim",[(x-.061,-.247,.029),(x-.064,-.248,.034),
              (x-.064,-.248,.078),(x-.059,-.248,.084),(x+.059,-.248,.084),
              (x+.064,-.248,.078),(x+.064,-.248,.034),(x+.059,-.248,.029),(x-.061,-.247,.029)],
              .0043,light_rim,rig.head)
    trace(c,"Single narrow eyeglass bridge",[(-.032,-.248,.064),(0,-.249,.070),(.032,-.248,.064)],.004,light_rim,rig.head)
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
    earth_y,earth_z=5.3,-4.05
    radius=(6.0,3.30,5.55)
    k.ball("Clean deep blue Earth",c,(0,earth_y,earth_z),radius,
           k.surface("Ocean cobalt with low cyan fill","#255683",.78,glow=.16),segments=52,rings=28)
    air=k.emission("Cyan rim and compositor airglow","#54d7ff",2.7)
    haze=k.emission("Outer atmospheric haze line","#3c98bc",1.35)
    for offset,ink,width in ((.042,air,.029),(.105,haze,.016)):
        contour=[((radius[0]+offset)*math.cos(a),earth_y-.40,
                  earth_z+(radius[2]+offset)*math.sin(a))
                 for a in (math.pi*i/34 for i in range(35))]
        arc=trace(c,"Cyan atmospheric rim",contour,width,ink)
        arc.visible_shadow=False
    # Paint a stylized subcontinent patch on the near hemisphere, outside the scan mesh.
    coast=[(-1.39,.61),(-.91,1.06),(-.44,1.12),(-.11,.93),(.36,.88),(.81,1.01),
           (1.21,.83),(.76,.53),(.35,.44),(.20,.02),(-.23,-.38),(-.52,-.08),
           (-.63,.27),(-.94,.41),(-1.06,.33)]
    terrain=k.surface("Gold-lit Indian subcontinent paint","#bd9160",.77,glow=.32)
    def on_earth(x,z,clearance=.025):
        return x,earth_y-radius[1]*math.sqrt(max(.0,1-(x/radius[0])**2-((z-earth_z)/radius[2])**2))-clearance,z
    mid_x,mid_z=-.20,.62
    vertices=[]; polygons=[]
    for first,last in zip(coast,coast[1:]+coast[:1]):
        offset=len(vertices); steps=10
        for j in range(steps+1):
            for side in (first,last):
                vertices.append(on_earth(.36+mid_x+(side[0]-mid_x)*j/steps,
                                         -.84+mid_z+(side[1]-mid_z)*j/steps))
        polygons.extend((offset+2*j,offset+2*j+2,offset+2*j+3,offset+2*j+1) for j in range(steps))
    k.mesh("Golden stylized India land patch",c,vertices,polygons,terrain,smoothing=True)
    gold_land=k.emission("Rajasthan area warm highlight","#f3bc74",1.52)
    for j in range(13):
        x=-.56+.015*j
        z=-.12+.029*math.sin(j*.57)
        k.ball("Golden regional glint",c,on_earth(x,z,.044),(.012,.007,.012),gold_land,segments=8,rings=5)
    haze=k.emission("Blue Earth latitude shimmer","#3781a8",1.07)
    for j in range(9):
        curve=[on_earth(-4.1+i*.29,-.62-j*.16+.05*math.sin(i*.40+j),.027)
               for i in range(30)]
        trace(c,"Thin ocean band caught in Earthlight",curve,.007,haze)
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
    projection=scan_pyramid(c,"Crimson optical scan cone",.10)
    lights(c)
    return root,sweep,projection

def scan_pyramid(c,name,opacity):
    pts=[(0,0,0),(-1,-.5,1),(1,-.5,1),(1,.5,1),(-1,.5,1)]
    material=translucent(name+" glowing volume","#fc3149",opacity,2.8)
    cone=k.mesh(name,c,pts,[(0,2,1),(0,3,2),(0,4,3),(0,1,4)],material)
    cone.visible_shadow=False
    return cone

def desert_sky(c):
    sky=k.emission("Cobalt to ochre twilight sky","#202741",.93)
    nodes, links=sky.node_tree.nodes,sky.node_tree.links
    tex=nodes.new("ShaderNodeTexCoord")
    axis=nodes.new("ShaderNodeSeparateXYZ")
    ramp=nodes.new("ShaderNodeValToRGB")
    k.look._ramp(ramp,[(0,"#8b5964"),(.33,"#373c78"),(.68,"#162751"),(1,"#07142e")])
    links.new(tex.outputs["Generated"],axis.inputs[0]);links.new(axis.outputs["Z"],ramp.inputs[0])
    emission=next(node for node in nodes if node.type=="EMISSION")
    links.new(ramp.outputs[0],emission.inputs["Color"])
    box(c,"Full-frame twilight air backdrop",(0,4.99,2.26),(15,.031,6.90),sky)
    star=k.emission("Small cool desert stars","#c9d7ff",1.49)
    rng=Random(411)
    vertices=[];faces=[]
    for i in range(188):
        x,z=rng.uniform(-7,7),rng.uniform(2.13,5.87)
        d=rng.uniform(.005,.017)
        start=len(vertices)
        vertices.extend(((x-d,4.87,z),(x,4.87,z+d),(x+d,4.87,z),(x,4.87,z-d)))
        faces.append(tuple(range(start,start+4)))
    k.mesh("Twilight specks of starlight",c,vertices,faces,star)
    moon=k.emission("Hazy Rajasthan moon","#ffd8ab",2.9)
    globe=k.cylinder("Warm round twilight moon",c,(1.57,4.35,3.97),.26,.018,moon,length_segments=36)
    globe.rotation_euler.x=math.pi/2
    for i,color in enumerate(("#57436a","#654b65","#8b646b")):
        ridge=[]
        for j in range(61):
            x=-7+j*.234
            h=1.88+.089*i+.22*math.sin(x*.61+i)+.15*math.sin(x*1.26-i)
            ridge.append((x,3.92-.65*i,h))
        base=3.92-.65*i
        k.mesh("Overlapping distant dune ridge",c,[*ridge,(7.1,base,.92),(-7,base,.92)],
               [tuple(range(len(ridge)+2))],k.emission("Painted dusk dune",color,1.0))
    return scan_pyramid(c,"Soft red cone sweeping above the surface",.135)

def cutaway(c):
    sand=k.texture("Thar sandstone cross section",("#50343d","#ab6b4e","#d68c55"),"plaster")
    stone=k.texture("Lower textured stone",("#362639","#684c50","#9c6560"),"plaster")
    scan=desert_sky(c)
    brass=k.surface("Symbolic sealed cylinders","#465467",.77)
    glow=k.emission("Five amber test markers","#f0b86d",1.48)
    laser=k.emission("Stylized passing scan","#f04558",1.78)
    ridge=[(-4+i*.16,1.88+.124*math.sin(i*.17)+.09*math.sin(i*.43)) for i in range(51)]
    front=[(x,.64,z) for x,z in ridge]+[(4,.64,-3.6),(-4,.64,-3.6)]
    k.mesh("Earthen illustrative cutaway",c,front,[tuple(reversed(range(len(front))))],sand)
    deep=k.texture("Terracotta compressed sediment",("#392634","#6d454d","#9c5e49"),"plaster")
    ember=k.texture("Ochre sandstone upper shelf",("#6d4140","#a66643","#bf8656"),"plaster")
    for band,mat in enumerate((deep,stone,ember)):
        floor=-3.65+band*1.39
        upper=floor+1.46
        top=[(-4+j*.16,.635,upper+.10*math.sin(j*.35+band)) for j in range(51)]
        k.mesh("Deep geological color band",c,[*top,(4,.635,floor),(-4,.635,floor)],
               [tuple(reversed(range(53)))],mat)
    for i in range(40):
        z=i*.128-3.34
        points=[(-4+j*.2,.609,z+.037*math.sin(j*.49+i)+.036*math.sin(i*1.7+j*.23)) for j in range(41)]
        trace(c,"Layered sandstone cross-section stratum",points,.015,stone)
    slot=k.surface("Recessed warm steel housings","#36404b",.78)
    inner=k.surface("Deep industrial cavity","#221d29",.82)
    ledge=k.surface("Softly lit concrete shaft lip","#8c8080",.80)
    for j in range(5):
        x=(j-2)*.61
        box(c,"Industrial shaft steel outer frame",(x,.561,.77),(.37,.12,1.46),slot,True)
        box(c,"Recessed dark shaft",(x,.488,.78),(.295,.041,1.35),inner)
        box(c,"Concrete shaft overhead lintel",(x,.458,1.49),(.36,.09,.062),ledge)
        for sign in (-1,1):
            bevel=[(x+sign*.171,.448,.098),(x+sign*.137,.515,.132),
                   (x+sign*.137,.515,1.415),(x+sign*.171,.448,1.475)]
            k.mesh("Recessed angled concrete side wall",c,bevel,[(0,1,2,3)],ledge)
        for k0 in range(9):
            box(c,"Inside shaft hatch",(x,.466,.16+k0*.151),(.298,.021,.013),brass)
        k.ball("Sealed symbolic test canister",c,(x,.44,.62),(.122,.088,.242),brass,segments=20,rings=14)
        box(c,"Dim warm shaft worklight",(x,.438,1.260),(.092,.045,.046),glow)
        for z in (.49,.70):
            k.cylinder("Amber canister rim",c,(x,.44,z),.126,.026,glow,length_segments=24)
        label(c,str(j+1),(x,.336,.31),.123,glow)
    rng=Random(35)
    for j in range(80):
        x=rng.uniform(-4,4);z=rng.uniform(-.16,1.86)
        trace(c,"Illustrated stone hatch",[(x,.616,z),(x+.054,.615,z+.04)],.008,stone)
    for j in range(16):
        x=-2.3+j*.302
        z=1.93+.11*math.sin(j*.58)
        trace(c,"Slender boundary post",[(x,.54,z),(x,.54,z+.125)],.008,stone)
        if j%2:
            trace(c,"Scrub against the upper dune",[(x-.039,.53,z),(x,.52,z+.078),(x+.025,.52,z),
                    (x+.074,.53,z+.116)],.010,stone)
    for z in (1.98,2.04):
        trace(c,"Simple fence wire over surface",[(-2.44+i*.301,.533,z+.103*math.sin(i*.58))
             for i in range(17)],.005,stone)
    trace(c,"Red scan across the dune",[(-3.8,.58,1.92),(-.2,.57,1.99),(3.6,.6,1.88)],.011,laser)
    lights(c,"#ffd0a1","#889acc")
    return next(n for n in glow.node_tree.nodes if n.type=="EMISSION").inputs["Strength"],scan
