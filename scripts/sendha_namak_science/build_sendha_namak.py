"""Rock salt visual comedy: isolated 3D stages, independently billboarded cel rigs."""
import bpy, math, sys, random, json
from pathlib import Path
from mathutils import Vector

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/washroom_experiment'))
sys.path.insert(0,str(ROOT/'scripts/inside_brain_dog'))
from sets import Stage, rgb
from build_inside_brain_dog import card, cel_material, image
OUT=ROOT/'renders/sendha_namak_science'; ART=OUT/'assets'
random.seed(41)

def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    s=bpy.context.scene;s['studio_root']=str(ROOT)
    s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.use_raytracing=False
    s.eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY';s.eevee.taa_render_samples=16
    s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=50
    s.render.fps=30;s.frame_start=1;s.frame_end=1728
    s.render.use_simplify=True;s.render.simplify_subdivision=2
    s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
    s.world.use_nodes=True;bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(*rgb('b9d1e4'),1);bg.inputs[1].default_value=.28
    g=Stage(s);m=g.mat
    def box(n,p,d,c,parent=None,ink=True):
        o=g.box(n,p,d,m(c),parent);o['set_ink']=ink;return o
    def ball(n,p,d,c,parent=None,em=0):return g.ball(n,p,d,m(c,em=em),parent)
    def torus(n,p,major,minor,c,parent=None):
        bpy.ops.mesh.primitive_torus_add(major_segments=48,minor_segments=8,location=(0,0,0),major_radius=major,minor_radius=minor)
        o=bpy.context.object;o.name=n;o.parent=parent;o.location=p;o.data.materials.append(m(c,metal=.25,em=.6));return o
    def cel(n,path):
        mat=cel_material(n,path)
        mat.use_fake_user=True
        for nd in mat.node_tree.nodes:
            if nd.type=='EMISSION':nd.inputs[1].default_value=.96
            if nd.type=='MIX_SHADER' and not any(l.from_node.type=='TEX_IMAGE' for l in nd.inputs[0].links):nd.inputs[0].default_value=.74
        return mat
    def pic(n,path,size,parent):return card(g,n,*size,cel(n,ART/path),parent)
    def room(n,offset,wall,floor):
        r=g.link(n,xyz=(offset,0,0))
        box(n+' floor',(0,0,-.09),(7.2,9,.18),floor,r)
        for x in [-3.5,3.5]:box(n+' side',(x,.0,1.9),(.16,9,3.8),wall,r,False)
        box(n+' rear',(0,3.9,1.9),(7.2,.16,3.8),wall,r,False)
        box(n+' front',(0,-4.4,1.9),(7.2,.16,3.8),wall,r,False)
        box(n+' ceiling',(0,0,3.85),(7.2,9,.12),'ded6c9',r,False)
        for x in [-3.4,3.4]:box(n+' skirting',(x,0,.13),(.09,8.7,.24),'66534a',r)
        box(n+' back skirting',(0,3.79,.13),(6.9,.10,.24),'66534a',r)
        g.light(n+' key','AREA',(-2,-1,3.3),(0,.2,.9),280,'ffe0b7',r).data.size=2.1
        g.light(n+' fill','AREA',(2,-.6,2.6),(0,.2,1.2),85,'9fc8ff',r)
        g.light(n+' rim','AREA',(0,2.5,3),(0,0,1.3),150,'ffbb83',r)
        # Recessed framed light window and physical bars, casting diagonal shadows.
        if n not in ['SET_MOUTH','SET_TISSUE']:
            box(n+' window surround',(-2,3.78,2.4),(1.7,.12,1.8),'3c454f',r)
            box(n+' window luminous glass',(-2,3.69,2.4),(1.53,.025,1.61),'8bc7e1',r,False)
            for x in [-2.7,-2.25,-1.8,-1.3]:box(n+' window mullion',(x,3.62,2.4),(.055,.065,1.65),'e9ded0',r)
            box(n+' window crossbar',(-2,3.62,2.45),(1.6,.07,.06),'e9ded0',r)
        for i in range(13):box(n+' floor seam',(-3.2+i*.52,0,.006),(.008,8.6,.006),'8b6b55',r,False)
        return r
    def table(n,r,pos=(0,-.2,0),width=1.6):
        r=g.link(n,p=r)
        x,y,z=pos
        box(n+' top',(x,y,z+.78),(width,.72,.105),'b87843',r)
        for dx in [-width*.42,width*.42]:
            for dy in [-.27,.27]:box(n+' leg',(x+dx,y+dy,z+.365),(.075,.075,.73),'584032',r)
        for j in range(7):box(n+' woodgrain',(x-width*.45+j*width*.14,y,.837+z),(.009,.64,.002),'88512f',r,False)
    bedroom=room('SET_BEDROOM',0,'b0a79b','a7825e')
    dining=room('SET_DINING',40,'dfbd84','aa7857')
    clinic=room('SET_CLINIC',60,'9bbcb5','719d9c')
    mouth=room('SET_MOUTH',20,'5f172e','b6425c')
    tissue=room('SET_TISSUE',80,'631a47','ac536f')
    table('Strawberry worktable',bedroom,(0,-.35,0))
    table('Dining',dining,(0,-.35,0))
    box('Dining seat',(-.25,.18,.30),(.55,.52,.10),'5b7d83',dining)
    for x in [-.46,-.04]:
        for y in [-.02,.39]:box('Dining chair foot',(x,y,.14),(.045,.045,.28),'5a463d',dining)
    # Bedroom physical furniture, bed/lamps/curtains and chart easel.
    box('Bed frame',(-1.85,1.8,.34),(1.65,2.8,.50),'5e4438',bedroom)
    box('Bed mattress',(-1.85,1.8,.65),(1.58,2.67,.18),'e9d9b9',bedroom)
    box('Folded teal blanket',(-1.85,1.25,.77),(1.56,1.44,.15),'287e90',bedroom)
    for x in [-2.3,-1.5]:box('Soft pillow',(x,2.65,.82),(.65,.55,.19),'f5e7cb',bedroom)
    # Sculpted quilt rises over the supported lap and drapes down the bed sides.
    quilt=g.link('TuckedQuilt',p=bedroom)
    verts=[];faces=[];NX=32;NY=42
    def quilt_point(x,y):
        lap=.36*math.exp(-((x+1.85)/.43)**2-((y-2.55)/.50)**2)
        drape=.36*max(0,(abs(x+1.85)-.64)/.20)
        quilted=.014*math.cos((x+1.85)*math.pi/.18)*math.cos(y*math.pi/.18)
        return (x,y,.82+lap-drape+quilted)
    for j in range(NY):
        y=.43+j*2.51/(NY-1)
        for i in range(NX):verts.append(quilt_point(-2.70+i*1.70/(NX-1),y))
    for j in range(NY-1):
        for i in range(NX-1):k=j*NX+i;faces.append((k,k+1,k+1+NX,k+NX))
    me=bpy.data.meshes.new('Quilted navy lap surface');me.from_pydata(verts,[],faces);me.materials.append(m('1d3557',rough=.8));g.link('Sculpted navy bed blanket',me,quilt)
    for poly in me.polygons:poly.use_smooth=True
    for i in range(9):
        x=-2.58+i*.18;g.curve('Quilt stitched channel',[quilt_point(x,.45+j*.05) for j in range(42)],.002,m('42607d',rough=.9),quilt)
    for i in range(11):
        y=.50+i*.18;g.curve('Quilt cross stitch',[quilt_point(-2.68+j*.052,y) for j in range(33)],.002,m('42607d',rough=.9),quilt)
    box('Bed headboard',(-1.85,3.24,.94),(1.72,.13,1.30),'79553f',bedroom)
    for j in range(3):box('Bed headboard slat',(-2.35+j*.5,3.14,.99),(.04,.035,1.08),'c18a53',bedroom)
    box('Bedside cabinet',(-.65,2.6,.45),(.55,.6,.9),'886046',bedroom)
    ball('Amber lampshade',(-.65,2.6,1.24),(.25,.25,.24),'e9b56c',bedroom,em=.4)
    g.rod('Lamp stem',(-.65,2.6,.9),(-.65,2.6,1.2),.025,m('a18150'),bedroom)
    g.light('Bedside practical','POINT',(-.65,2.55,1.3),(0,0,0),22,'ffbb6d',bedroom)
    board=g.link('MedicalBoard',p=bedroom,xyz=(1.0,.6,1.52))
    box('Chart wooden backing',(0,0,0),(.93,.08,1.20),'5d3e2d',board)
    chart=pic('Glowing pictorial medical diagram','diagram.png',(.84,1.11),board);chart.location=(0,-.049,0);chart.rotation_euler.x=math.pi/2
    for x in [-.34,.34]:g.rod('Easel legs',(x,.08,-1.5),(x,.08,.43),.025,m('a16c3e'),board)
    g.rod('Easel rear kickstand',(0,.7,-1.5),(0,.1,.1),.025,m('a16c3e'),board)
    # Strawberry tapered body; dense seed sockets make its identity readable.
    strawberry=g.link('Strawberry',p=bedroom,xyz=(.38,-.46,1.08))
    verts=[];faces=[];rings=18;segs=40
    for j in range(rings+1):
        t=j/rings;z=-.25+t*.52;r=.25*math.sin(math.pi*t)**.65*(.55+.65*t)
        for i in range(segs):a=i*math.tau/segs;verts.append((r*math.cos(a),r*math.sin(a),z))
    for j in range(rings):
        for i in range(segs):k=j*segs+i;faces.append((k,j*segs+(i+1)%segs,(j+1)*segs+(i+1)%segs,k+segs))
    mesh=bpy.data.meshes.new('Strawberry sculpt');mesh.from_pydata(verts,[],faces);mesh.materials.append(m('d52b3c',rough=.35));g.link('Real seeded strawberry flesh',mesh,strawberry)
    for p in mesh.polygons:p.use_smooth=True
    for j in range(1,8):
        t=j/9;z=-.25+t*.52;r=.25*math.sin(math.pi*t)**.65*(.55+.65*t)
        for i in range(11):
            a=(i+j*.5)*math.tau/11;o=ball('Strawberry golden seed',(r*math.cos(a),r*math.sin(a),z),(.011,.011,.019),'f3ce64',strawberry)
    for i in range(7):
        a=i*math.tau/7;leaf=ball('Strawberry crown leaf',(.14*math.cos(a),.14*math.sin(a),.25),(.16,.045,.019),'347a34',strawberry);leaf.rotation_euler.z=a
    g.rod('Strawberry stem',(0,0,.24),(.03,.015,.39),.023,m('4b8735'),strawberry)
    strawberry.scale=(.20,.20,.172);strawberry['height_m']=.11;strawberry['radius_m']=.05
    ball('Strawberry white plate',(-.30,-.20,.848),(.16,.14,.012),'f4f4e9',bpy.data.objects['Strawberry worktable'])
    # A real grasp socket on the barrel surface, plus visible front fingers.
    # Reusable shaker: translucent blue-tinted vessel with a connected perforated lid.
    shaker=g.link('SaltShaker')
    glass=m('b8dfed',rough=.12);p=next(n for n in glass.node_tree.nodes if n.type=='BSDF_PRINCIPLED');p.inputs['Transmission Weight'].default_value=.45;p.inputs['Alpha'].default_value=.52;glass.surface_render_method='BLENDED'
    g.rod('Shaker glass base',(0,0,-.12),(0,0,.10),.065,glass,shaker)
    g.rod('Shaker visible white salt',(0,0,-.115),(0,0,.035),.048,m('f4efe1'),shaker)
    g.rod('Shaker metal lid',(0,0,.10),(0,0,.14),.071,m('a9b5c6',metal=.7),shaker)
    for x,y in [(-.025,0),(.025,0),(0,.03),(0,-.03)]:ball('Lid perforation',(x,y,.142),(.007,.007,.002),'29364a',shaker)
    grip=g.link('ShakerGrip',p=shaker,xyz=(-.050,-.045,-.015))
    for j in range(3):
        g.curve('Shaker wrapped mitten finger',[(-.055,-.043,-.048+j*.031),(-.030,-.066,-.048+j*.031),(.004,-.068,-.048+j*.031),(.028,-.055,-.048+j*.031)],.009,m('161219',rough=.96),shaker)
    phone=g.link('Phone');box('Cyan phone case',(0,0,0),(.17,.026,.28),'183a52',phone);box('Phone cyan screen',(0,-.017,.005),(.145,.007,.239),'54d8ed',phone)
    phlight=g.light('Phone face glow','POINT',(0,-.1,.1),(0,0,0),18,'50dfff',phone)
    ban=g.link('Prohibition');ring=torus('Prohibition ring',(0,0,0),.24,.026,'ff3939',ban);ring.rotation_euler.x=math.pi/2
    g.rod('Prohibition diagonal',(-.17,-.01,.17),(.17,-.01,-.17),.028,m('ff3939',em=.7),ban)
    meters=[]
    for i,x in enumerate([-.65,.65]):
        root=g.link('HealthPillar'+str(i),p=bedroom,xyz=(x,1.1,0))
        box('Health meter housing',(0,0,1.05),(.23,.20,1.80),'3f494b',root)
        o=box('Health meter fill',(0,-.118,1.05),(.14,.025,1.63),'55d687',root,False);meters.append(o)
        for z in [.36,.66,.96,1.26,1.56,1.86]:box('Meter separation',(0,-.139,z),(.16,.009,.012),'33434b',root,False)
    alarm=g.light('Emergency red wash','AREA',(0,.5,3.4),(0,0,1),0,'ff2635',bedroom)
    ball('Warning red lamp',(0,1.1,2.45),(.15,.15,.12),'ed2939',bedroom,em=1)
    g.rod('Warning lamp mount',(0,1.1,2.48),(0,1.1,3.77),.024,m('5b5151'),bedroom)
    # Dining dishes are genuinely curved 3D bowl surfaces, not flat decal food.
    bowl=g.link('Raita bowl',p=dining,xyz=(.20,-.48,.89))
    shell=ball('White ceramic raita bowl',(0,0,0),(.29,.26,.115),'f1f4e9',bowl)
    torus('Raita ceramic rim',(0,0,.07),.265,.021,'f1f4e9',bowl)
    ball('White yogurt surface',(0,0,.071),(.251,.227,.012),'fff7df',bowl)
    for i in range(30):
        a=random.random()*math.tau;r=random.random()**.5*.22;ball('Golden boondi',(r*math.cos(a),r*math.sin(a),.085),(.014,.014,.013),'efbf43',bowl)
    for i in range(3):o=ball('Mint leaf',(.02+i*.025,.04,.10),(.045,.018,.006),'398f43',bowl);o.rotation_euler.z=i*.7
    plate=ball('Cucumber ceramic plate',(-.48,-.47,.86),(.27,.25,.025),'d9e9e1',dining)
    for i in range(6):
        x=-.63+(i%3)*.13;y=-.56+(i//3)*.16
        ball('Cucumber green rind',(x,y,.9),(.082,.075,.017),'34834b',dining)
        ball('Cucumber pale slice',(x,y,.918),(.067,.060,.005),'cfdf85',dining)
        for j in range(3):ball('Cucumber seed',(x+(j-1)*.022,y,.924),(.006,.018,.002),'ecf3bb',dining)
    halo=torus('Golden halo',(0,0,0),.29,.016,'ffd46a')
    shield=g.link('MedicalShield');pts=[(-.25,0,.25),(.25,0,.25),(.23,0,-.09),(0,0,-.32),(-.23,0,-.09)]
    me=bpy.data.meshes.new('Shield pentagon');me.from_pydata(pts,[],[(0,1,2,3,4)]);me.materials.append(m('29d899',em=.7));g.link('Green shield plate',me,shield)
    g.curve('Shield gold rim',pts,.012,m('c2ffac',em=.7),shield,True)
    box('Medical plus upright',(0,-.015,.02),(.055,.015,.25),'f1ffdb',shield)
    box('Medical plus crossbar',(0,-.016,.02),(.19,.016,.055),'f1ffdb',shield)
    spray=g.link('SprayBottle');g.rod('Blue hygiene bottle',(0,0,-.12),(0,0,.10),.065,m('409ddb'),spray)
    box('Spray pump',(0,-.025,.15),(.10,.12,.05),'e4f6ed',spray);box('Spray nozzle',(0,-.10,.15),(.045,.09,.03),'2e435a',spray)
    # Clinic furniture, wheels, cabinet drawers and unlabelled medicine vials.
    box('Clinic storage',(1.65,2.8,1.1),(1.8,.6,2.2),'d9e8e0',clinic)
    for x in [1.2,2.1]:
        box('Clinic cabinet door',(x,2.47,1.37),(.83,.04,1.4),'c4dcd4',clinic)
        box('Cabinet handle',(x+.24,2.42,1.2),(.035,.055,.21),'637b83',clinic)
    for i in range(7):g.rod('Medicine bottle',(.99+i*.18,2.38,2.23),(.99+i*.18,2.38,2.47),.048,m(['80b4bd','eadbc0','c095b4'][i%3]),clinic)
    box('Exam chair back',(-1.7,1.4,1.05),(.65,.17,1.05),'3f8c99',clinic)
    box('Exam chair seat',(-1.7,1.15,.49),(.67,.65,.11),'3f8c99',clinic)
    g.rod('Exam chair support',(-1.7,1.2,.03),(-1.7,1.2,.46),.07,m('738d96',metal=.5),clinic)
    stool=g.link('Doctor rolling stool',p=clinic,xyz=(.9,1.5,0));ball('Stool cushion',(0,0,.50),(.30,.26,.07),'3d8190',stool)
    g.rod('Stool piston',(0,0,.12),(0,0,.47),.045,m('9aaab6',metal=.7),stool)
    for i in range(5):
        a=i*math.tau/5;p=(.31*math.cos(a),.31*math.sin(a),.08);g.rod('Stool spoke',(0,0,.13),p,.022,m('627883'),stool);ball('Stool wheel',p,(.06,.025,.055),'253a45',stool)
    # Mouth cavern: enclosing sculpted palate, gums, tooth arches and back throat.
    for x in [-1.55,1.55]:ball('Fleshy mouth side',(x,1,1.65),(.50,2.2,1.75),'9a3454',mouth)
    ball('Oral vaulted palate',(0,1.4,3.3),(1.7,2.5,.66),'c25a75',mouth)
    ball('Dark open throat',(0,2.8,1.65),(.72,.08,1.13),'35102d',mouth)
    tongue=ball('Giant contoured tongue',(0,.8,.49),(1.12,1.65,.38),'e97089',mouth)
    Olight=g.light('Mouth soft front light','AREA',(0,-1.4,2.2),(0,1.6,1.4),190,'ffd0cc',mouth);Olight.data.size=2
    for j in range(5):
        g.curve('Palate soft ridge',[(-1.3+i*.13,.4+j*.35,3.04-.10*math.sin(i/20*math.pi)) for i in range(21)],.014,m('d7758b'),mouth)
    g.curve('Tongue central groove',[(0,-.57,.75),(0,.2,.87),(0,1.0,.88),(0,1.8,.72)],.018,m('b33c66'),mouth)
    for i in range(13):
        a=math.pi*i/12;x=1.31*math.cos(a);y=.1+1.55*math.sin(a)
        for upper in [False,True]:
            z=2.81 if upper else .39
            ball('Pink dental gum',(x,y,z),(.26,.28,.20),'e8788c',mouth)
            o=box('Ivory molar',(x,y-.06,z+(-.18 if upper else .16)),(.25,.30,.37),'f9edce',mouth);o.modifiers[0].width=.075;o.modifiers[0].segments=3
    tonsils=[]
    for i,x in enumerate([-.70,.70]):
        o=ball('Hanging tonsil'+str(i),(x,2.07,1.98),(.31,.31,.57),'d8577b',mouth);tonsils.append(o)
    ball('Central hanging uvula',(0,2.12,2.48),(.14,.20,.32),'e989a0',mouth)
    # Tissue undulates continuously in space, never jittering over time.
    verts=[];faces=[];N=96
    for j in range(N):
        for i in range(N):
            x=-2.2+i*4.4/(N-1);y=-1+j*5/(N-1)
            distance=10
            for k in range(7):
                t=max(0,min(9.999,(y+.65)/.34));lo=int(t);t-=lo
                center=-1.5+k*.45+.13*((1-t)*math.sin(lo*2+k)+t*math.sin((lo+1)*2+k))
                distance=min(distance,abs(x-center))
            z=.28+.015*math.sin(x*4+y)*math.cos(y*2)-.10*math.exp(-distance*distance/.0015);verts.append((x,y,z))
    for j in range(N-1):
        for i in range(N-1):k=j*N+i;faces.append((k,k+1,k+1+N,k+N))
    me=bpy.data.meshes.new('Cellular mucosa');me.from_pydata(verts,[],faces);tissue_mat=m('db839a',rough=.48);me.materials.append(tissue_mat);slab=g.link('Pink tissue slab',me,tissue)
    basis=slab.shape_key_add(name='Uninjured tissue');cut=slab.shape_key_add(name='Micro-cut depression')
    for vertex in basis.data:
        x,y=vertex.co.x,vertex.co.y;vertex.co.z=.28+.015*math.sin(x*4+y)*math.cos(y*2)
    cut.value=0
    for p in me.polygons:p.use_smooth=True
    nt=tissue_mat.node_tree;pr=next(n for n in nt.nodes if n.type=='BSDF_PRINCIPLED');noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=9
    bump=nt.nodes.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.18;bump.inputs['Distance'].default_value=.035;nt.links.new(noise.outputs['Fac'],bump.inputs['Height']);nt.links.new(bump.outputs['Normal'],pr.inputs['Normal'])
    cracks=g.link('MicroCracks',p=tissue)
    for i in range(7):
        pts=[(-1.5+i*.45+.13*math.sin(j*2+i),-.65+j*.34,.36) for j in range(11)]
        o=g.curve('Displaced dark crevice',pts,.045,m('641f55'),cracks);o.scale.z=.10;o.location.z=.20
        o=g.curve('Glowing exposed cut',[(x,y,z+.005) for x,y,z in pts],.014,m('ff3d6b',em=2.5),cracks);o.scale.z=.1;o.location.z=.206
        for j in [3,6]:
            x,y,z=pts[j];o=g.curve('Crack branch',[(x,y,z),(x+.18,y+.15,z),(x+.26,y+.32,z)],.018,m('fa567e',em=1.4),cracks);o.scale.z=.1;o.location.z=.247
    # Stable, real 3D germs, tiny fork tines and articulated attack roots.
    def germ(n,r,boss=False):
        root=g.link(n);radius=.23 if boss else .105
        ball(n+' jelly bean',(0,0,0),(radius,radius*.7,radius*1.25),r,root)
        for x in [-radius*.38,radius*.38]:
            ball(n+' solid angry eye',(x,-radius*.69,.04),(radius*.14,.014,radius*.23),'1b1620',root)
            g.rod(n+' scowling brow',(x-radius*.21,-radius*.71,.10),(x+radius*.21,-radius*.71,.075),radius*.055,m('211723'),root)
            ball(n+' white fang',(x,-radius*.73,-.08),(radius*.09,.012,radius*.16),'fff1dc',root)
        for side in [-1,1]:g.curve(n+' stick arm',[(side*radius*.8,0,0),(side*radius*1.3,-.03,-.05),(side*radius*1.5,-.05,.05)],.012,m('18131c'),root)
        if boss:
            for i in range(16):
                a=i*math.tau/16;p=(math.cos(a)*radius*.9,0,math.sin(a)*radius*.9)
                g.rod(n+' spike',p,(p[0]*1.55,0,p[2]*1.55),.032,m(r),root)
        else:
            x=radius*1.48
            g.rod(n+' pitchfork shaft',(x,-.05,-.10),(x,-.05,.34),.009,m('171320'),root)
            g.rod(n+' pitchfork crossbar',(x-.055,-.05,.26),(x+.055,-.05,.26),.009,m('171320'),root)
            for dx in [-.055,0,.055]:g.rod(n+' pitchfork tine',(x+dx,-.05,.26),(x+dx,-.05,.36),.008,m('171320'),root)
        return root
    for i in range(25):germ('Germ%02d'%i,'52b788')
    for i in range(3):germ('VirusBoss'+str(i),['9d4edd','e63946','9d4edd'][i],True)
    for i in range(3):
        root=g.link('ConquestFlag'+str(i));g.rod('Flagpole',(0,0,0),(0,0,.52),.012,m('46263d'),root)
        me=bpy.data.meshes.new('Red triangular flag');me.from_pydata([(0,0,.51),(.25,0,.43),(0,0,.34)],[],[(0,1,2)]);me.materials.append(m('ef334c'));g.link('Red conquest pennant',me,root)
    # Human cel rigs with shared assets/materials; controller owns all motion.
    for kind in ['boy','partner','doctor']:
        root=g.link('char_'+kind);root['kind']=kind
        head=pic(kind+'_head',f'{kind}_neutral.png',(1.02,1.02),None)
        for exp in ['smirk','panic','hypno','worry','spiral','smile','blink']:cel(kind+'_'+exp,ART/f'{kind}_{exp}.png')
        torso=pic(kind+'_torso',f'body_{kind}.png',(.57,.91),None)
        ball(kind+'_hips',(0,0,0),(.165,.095,.115),'1d2d44')
        mouthcard=pic(kind+'_mouth','mouth_smile_0.png',(.245,.153),None)
        if kind=='boy':
            cel('boy_profile',ART/'boy_profile.png')
            for state in ['smile','o','flat','panic','open']:
                for talk in range(6):cel(f'mouth_{state}_{talk}',ART/f'mouth_{state}_{talk}.png')
        for side in ['L','R']:
            for limb in ['arm','leg']:
                g.curve(f'{kind}_{limb}{side}',[(0,0,0)]*25,.019,m('161219',rough=.96))
            ball(kind+'_hand'+side,(0,0,0),(.036,.025,.040),'161219')
            ball(kind+'_shoe'+side,(0,0,0),(.085,.045,.037),'161219')
        # Ground discs have real floor contact, never follow an airborne head.
        for side in ['L','R']:ball(kind+'_contact'+side,(0,0,.006),(.11,.08,.004),'665951')
    q=pic('QuestionIcon','question.png',(.35,.35),None)
    soul=pic('DoctorSoul','soul.png',(.43,.50),None)
    ball('DoctorFaintShadow',(0,0,.006),(.45,.18,.004),'698b8d')
    # Rounded tongue segments follow a continuous mouth-to-tip ribbon; no floating wrist props.
    for name,color in [('TongueInk','2b1810'),('TongueFill','ff758f')]:
        me=bpy.data.meshes.new(name);me.from_pydata([(0,0,0)]*66,[],[tuple(range(66))]);me.materials.append(m(color,rough=1,em=.55));g.link(name,me)
    m('ec3658',rough=1,em=.65).use_fake_user=True
    helmet=g.link('SafariHelmet');helmet.scale=(.35,.35,.35)
    ball('Khaki helmet dome',(0,0,.045),(.13,.10,.075),'d4a373',helmet)
    band=torus('Safari dark hat band',(0,0,.035),.106,.013,'5b4630',helmet);band.scale.y=.8
    rim=torus('Khaki pith brim',(0,0,0),.13,.025,'d4a373',helmet);rim.scale.y=.8
    g.rod('Helmet top button',(0,0,.09),(0,0,.14),.018,m('89733d'),helmet)
    mirror=g.link('DoctorMirror');g.rod('Silver head mirror',(0,0,0),(0,.025,0),.09,m('b2c2cb',metal=.8),mirror);ball('Mirror center hole',(0,-.004,0),(.022,.004,.022),'30455d',mirror)
    flashlight=g.link('PenFlashlight');g.rod('Silver penlight',(0,0,-.10),(0,0,.10),.022,m('afc2d2',metal=.7),flashlight)
    g.light('Penlight beam','SPOT',(0,0,.11),(0,0,1),15,'fff3c6',flashlight).data.spot_size=.45
    # Particles are assigned closed-form trajectories. No random state in the frame handler.
    for i in range(55):
        o=box('SaltCrystal%02d'%i,(0,0,0),(.025,.027,.030),'f4f4e2',None,False);o.rotation_euler=(i*.7,i*.9,i*.4)
    for i in range(28):o=box('SpiceFlake%02d'%i,(0,0,0),(.045,.035,.009),'c73d27',None,False);o.rotation_euler.z=i*.7
    for i in range(20):ball('Smoke%02d'%i,(0,0,0),(.1,.1,.1),'659776',em=.05)
    for i in range(8):ball('Sweat%02d'%i,(0,0,0),(.018,.010,.040),'7cdaf0',em=.2)
    for i in range(12):ball('TongueSpot%02d'%i,(0,0,0),(.014,.006,.020),'8032ad')
    for i in range(8):ball('SprayMist%02d'%i,(0,0,0),(.012,.012,.012),'a6deef',em=.2)
    crystal_mat=m('e8f4ee',rough=.20)
    pr=next(n for n in crystal_mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');pr.inputs['Transmission Weight'].default_value=.24
    for i in range(36):
        o=g.box('EmbeddedSalt%02d'%i,(0,0,0),(.04+(i%4)*.01,.035+(i%3)*.012,.04+(i%4)*.01),crystal_mat,bevel=.005)
        o.rotation_euler=(i*.51,i*.73,i*.31)
    # Camera and optical focus target are authored independently of room walls.
    camera=g.link('StoryCamera',bpy.data.cameras.new('Story lens'));s.camera=camera
    camera.data.lens=43;camera.data.clip_start=.03;camera.data.clip_end=150
    camera.data.dof.use_dof=True;camera.data.dof.aperture_fstop=3.6;camera.data.dof.aperture_blades=6
    s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();lk=nt.links
    rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.threshold=.8;gl.mix=.18;gl.size=7;lk.new(rl.outputs['Image'],gl.inputs[0])
    sat=nt.nodes.new('CompositorNodeHueSat');sat.inputs['Saturation'].default_value=1.16;lk.new(gl.outputs[0],sat.inputs['Image'])
    vi=nt.nodes.new('CompositorNodeImage');vi.image=image(ART/'vignette.png');resize=nt.nodes.new('CompositorNodeScale');resize.space='RENDER_SIZE';lk.new(vi.outputs[0],resize.inputs[0])
    mul=nt.nodes.new('CompositorNodeMixRGB');mul.blend_type='MULTIPLY';mul.inputs[0].default_value=1;lk.new(sat.outputs[0],mul.inputs[1]);lk.new(resize.outputs[0],mul.inputs[2])
    output=nt.nodes.new('CompositorNodeComposite');lk.new(mul.outputs[0],output.inputs[0])
    for name,path in [('sendha_runtime.py',Path(__file__).with_name('runtime.py')),('studio_set_ink.py',ROOT/'scripts/studio/set_ink.py')]:
        tx=bpy.data.texts.get(name) or bpy.data.texts.new(name);tx.clear();tx.write(path.read_text())
    s['set_ink_enabled']=True;s['audio_role']='Voiceover narration; faces use audio-gated reaction/speaking variants.'
    namespace={'__name__':'sendha_runtime'};exec(bpy.data.texts['sendha_runtime.py'].as_string(),namespace)
    s.frame_set(55);bpy.context.view_layer.update()
    s['production_version']=2
    s['production']='sendha_namak_science V2; 1728f; 30fps; 540x960 review; no screen text'
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'sendha_namak_science.blend'))
    print('SENDHA_BUILD_COMPLETE',len(s.objects),flush=True)

if __name__=='__main__':main()
