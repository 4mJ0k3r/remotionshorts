"""Luxury bathroom, living room, Paris, proposal props and sunny wedding."""
import math

def build(g):
    bathroom=g.room('SET_BATHROOM',100,'d8cdb5',g.surface('Bathroom marble floor','b4b9b4','f1ead6','marble'))
    for x in [-2.8,2.8]:
        g.boxx('Bathroom dark marble pilaster',(x,4.2,1.8),(.38,.30,3.6),g.surface('Polished black marble','26333a','657773','marble'),bathroom)
        g.boxx('Bathroom brass band',(x,4.0,2.8),(.43,.05,.07),'bd9d5d',bathroom)
    g.toilet('GoldenToiletA',bathroom,(0,.65,0))
    for n,x,s in [('GoldenToiletB',1.35,1),('ChildPottyA',-.85,.48),('ChildPottyB',.85,.48)]:g.toilet(n,bathroom,(x,1.1 if s==1 else -.35,0),s)
    g.boxx('Bathroom framed mirror',(-1.6,2.7,1.8),(1.1,.08,1.5),'bc9b52',bathroom)
    g.boxx('Bathroom mirror glass',(-1.6,2.645,1.8),(.98,.025,1.36),g.mat('a6c0c4',metal=.65,rough=.12),bathroom,False)
    g.boxx('Floating marble vanity',(-1.6,2.3,.85),(1.25,.75,.15),'e4dac5',bathroom)
    g.sphere('Washbasin hollow',(-1.6,2.3,.94),(.36,.23,.025),'b3cbcf',bathroom)
    for x in [-1.9,-1.3]:g.bar('Vanity support',(x,2.3,0),(x,2.3,.77),.04,'b59653',bathroom)
    g.bar('Vanity golden faucet',(-1.6,2.55,.95),(-1.6,2.55,1.13),.022,'c59e4b',bathroom)
    trousers=g.link('AnkleTrousers')
    for x in [-.13,.13]:g.boxx('Bunched modest trousers',(x,0,.09),(.19,.20,.12),'393341',trousers,False,bevel=.045)
    shock=g.torus('AmberShockwave',(0,0,0),.35,.025,'ffbf48',None,em=3.2)

    living=g.room('SET_LIVING',125,'b69e88',g.surface('Polished parquet','634132','be8b58','wood'))
    # Alternating wood blocks carry an actual herringbone pattern, not a flat color.
    for col in range(4):
        specs=[]
        for i in range(-25,25):
            for j in range(-35,44):
                if (i*11+j*3)%4!=col:continue
                h=.16;d=(i-j)%6
                if d==0:specs.append((((i+1.5)*h,(j+.5)*h,.006),(3*h-.004,h-.004,.012)))
                elif d==5:specs.append((((i+.5)*h,(j+1.5)*h,.006),(h-.004,3*h-.004,.012)))
        g.batch('Parquet herringbone block '+str(col),specs,g.mat(['875d3e','a3724d','bd8d60','956a49'][col],rough=.25),living)
    g.sofa(living)
    blanket=g.link('CuddleBlanket',p=living);velvet=g.surface('Cuddle red blanket weave','8d1633','be3f50','weave')
    vs=[]
    for j in range(15):
        y=-.14+j*1.40/14
        for i in range(21):
            start=.35-.30*j/14;x=start+(1.70-start)*i/20;z=1.02+.14*y+.020*math.sin(i*.80+j*.55)
            if j==0:z=.66
            if i==20:z=.70+.05*y
            vs.append((x,y,z))
    g.meshx('Draped folded red blanket',vs,[(j*21+i,j*21+i+1,(j+1)*21+i+1,(j+1)*21+i) for j in range(14) for i in range(20)],velvet,blanket)
    for row in [0,14]:g.curve('Blanket gold embroidered hem',[vs[row*21+i] for i in range(21)],.008,g.mat('d5ae59',metal=.5),blanket)
    for col in [0,20]:g.curve('Blanket side gold embroidered hem',[vs[j*21+col] for j in range(15)],.008,g.mat('d5ae59',metal=.5),blanket)
    g.boxx('Fireplace stone mantel',(-2.5,3.7,1.0),(1.8,.65,1.9),'c9b79c',living)
    g.boxx('Fireplace dark opening',(-2.5,3.34,.75),(1.18,.04,1.15),'342425',living)
    for i in range(5):g.sphere('Warm fireplace flame',(-2.84+i*.17,3.25,.40),(.12,.08,.20+i%2*.13),'ffb65d',living,em=3)
    g.light('Fireplace warm spill','POINT',(-2.5,3.0,.55),(0,0,0),70,'ffb367',living)
    g.boxx('Living side table',(2.4,1.5,.62),(.65,.65,.10),'674737',living)
    for x in [2.18,2.62]:g.boxx('Living table leg',(x,1.5,.29),(.05,.5,.58),'674737',living)
    g.lamp('Living brass lamp',(2.4,1.5,1.5),living)

    paris=g.root('SET_PARIS',150);g.sky(paris,['2b1055','d94e67','ffbe76']);g.lighting(paris,True,5.2,'ffd4a0')
    g.boxx('Paris stone balcony',(0,.7,-.07),(8,8,.14),g.surface('Paris balcony travertine','a5a09b','e0c6a5'),paris,False)
    for x in [-2.5,2.5]:g.boxx('Paris stone balustrade pillar',(x,2.1,.72),(.30,.32,1.44),'c2b195',paris)
    for x in [i*.25 for i in range(-10,11)]:
        g.bar('Wrought iron rail',(x,2.1,.14),(x,2.1,1.30),.016,'30303a',paris)
        g.curve('Iron balcony scroll',[(x+.08*math.cos(a*math.pi/12),2.1,.68+.18*math.sin(a*math.pi/12)) for a in range(25)],.009,g.mat('39333b'),paris)
    for z in [.15,1.30]:g.bar('Iron balcony horizontal rail',(-2.5,2.1,z),(2.5,2.1,z),.028,'30303a',paris)
    tower=g.link('EiffelLatticeTower',p=paris,xyz=(.0,8,0));tower.scale=(.75,)*3
    metal=g.mat('725c55',metal=.55,rough=.35)
    # Blender Z is height; Y=8 is the intended distant background, not Z=-4.5.
    for sx in [-1,1]:
        for sy in [-1,1]:
            pts=[(sx*1.5,sy*1.0,0),(sx*.95,sy*.65,1.6),(sx*.48,sy*.35,3.6),(sx*.17,sy*.13,5.4),(sx*.045,sy*.035,6.8)]
            for a,b in zip(pts,pts[1:]):g.rod('Eiffel tapered main leg',a,b,.055,metal,tower)
    for i in range(18):
        z=i*.36+.1;w=1.5*(1-z/7)**1.7+.045;yn=w*.67
        for sy in [-1,1]:
            g.rod('Eiffel lattice horizontal',(-w,sy*yn,z),(w,sy*yn,z),.018,metal,tower)
            if i<17:
                w2=1.5*(1-(z+.36)/7)**1.7+.045
                g.rod('Eiffel diagonal cross',(-w,sy*yn,z),(w2,sy*w2*.67,z+.36),.016,metal,tower)
                g.rod('Eiffel reverse diagonal',(w,sy*yn,z),(-w2,sy*w2*.67,z+.36),.016,metal,tower)
    for z,w in [(1.7,1.1),(3.6,.61)]:g.boxx('Eiffel viewing platform',(0,0,z),(2*w,1.45*w,.12),'897065',tower)
    g.bar('Eiffel antenna',(0,0,6.6),(0,0,7.3),.025,'8f7560',tower)

    box=g.link('RingBox');g.boxx('Velvet ring box base',(0,0,0),(.28,.24,.11),'7d1733',box,bevel=.025)
    g.boxx('Velvet inner cushion',(0,-.01,.06),(.23,.19,.028),'2d2033',box,False,bevel=.02)
    lid=g.link('RingBox lid hinge',p=box,xyz=(0,.12,.05));lid.rotation_euler.x=math.radians(-110)
    g.boxx('Velvet hinged lid',(0,-.12,.04),(.28,.24,.07),'a62e4b',lid,bevel=.02)
    paper=g.torus('ToiletPaperRing',(0,-.01,.147),.057,.016,'f8efd9',box);paper.rotation_euler.x=math.pi/2
    g.torus('Paper ring rolled edge',(0,-.027,.147),.057,.004,'cfbea3',box).rotation_euler.x=math.pi/2
    verts=[(0,-.01,.25)]+[(.043*math.cos(i*math.tau/8),-.01+.043*math.sin(i*math.tau/8),.19) for i in range(8)]+[(.024*math.cos(i*math.tau/8),-.01+.024*math.sin(i*math.tau/8),.165) for i in range(8)]
    faces=[(0,i+1,(i+1)%8+1) for i in range(8)]+[(i+1,(i+1)%8+1,(i+1)%8+9,i+9) for i in range(8)]+[tuple(range(9,17))]
    verts=[(x,y,z+.042) for x,y,z in verts]
    diamond=g.meshx('Faceted blue white diamond',verts,faces,g.mat('b9edff',metal=.30,rough=.08,em=.15),box)
    for color in ['7ac8ec','e5f7ff']:diamond.data.materials.append(g.mat(color,metal=.30,rough=.08,em=.15))
    for i,poly in enumerate(diamond.data.polygons):poly.material_index=i%3
    for i in range(42):
        a=i*2.4;r=.3+(i%7)*.21;o=g.sphere('ProposalRosePetal%02d'%i,(math.cos(a)*r,math.sin(a)*r,.024),(.05,.026,.009),'b83e60');o.rotation_euler.z=a
    crown=g.link('GoldenCrown');g.torus('Crown gold circlet',(0,0,0),.25,.025,'d8ac43',crown,.92)
    for i in range(7):
        a=i*math.tau/7;x=.25*math.cos(a);y=.25*math.sin(a)
        g.meshx('Crown triangular point',[(x,y,0),(x*.75,y*.75,.19),(x+.07*math.cos(a+1.57),y+.07*math.sin(a+1.57),0)],[(0,1,2)],g.mat('edbf53',metal=.92,rough=.18),crown)
        g.sphere('Crown ruby',(x*.84,y*.84,.10),(.022,.018,.025),'b73a51',crown,metal=.3)

    wedding=g.root('SET_WEDDING',175);g.sky(wedding,['1b6ca8','56b4e9','e8f4f8']);g.lighting(wedding,True,5,'fff0c7')
    g.boxx('Wedding stone terrace',(0,1,-.06),(12,16,.12),g.surface('Wedding pale paving','b8b5a4','dfddca'),wedding,False)
    g.boxx('Wedding woven red runner',(0,1.3,.015),(1.48,9,.025),g.surface('Wedding rug woven','8c2638','bd4954','weave'),wedding,False)
    lawn=g.surface('Estate garden lawn','315b3c','78a558','wood')
    next(n for n in lawn.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Roughness'].default_value=.95
    g.boxx('Estate garden grass',(0,7.5,.014),(18,8.5,.028),lawn,wedding,False)
    for x in [-6,-4.5,-3,3,4.5,6]:g.boxx('Manicured estate hedge',(x,5.6,.49),(1.6,.75,.94),'426c45',wedding,bevel=.20)
    for x in [i*.38 for i in range(-18,19)]:g.bar('White garden baluster',(x,4.7,.12),(x,4.7,.78),.035,'e4decc',wedding)
    for z in [.12,.82]:g.boxx('White stone garden balustrade',(0,4.7,z),(14,.22,.13),'e7dfca',wedding)
    for k,x in enumerate([-4.8,-2.8,2.8,4.8]):
        tree=g.tree('Flowering estate tree',(x,6.2+(k%2)*1.2,0),wedding,.85)
        for i in range(12):
            a=i*2.4;cx=.8*math.cos(a);cy=.6*math.sin(a);cz=2.5+(i%3)*.20
            for j in range(3):g.sphere('Estate blossom petal',(cx+.05*math.cos(j*2.1),cy,cz+.05*math.sin(j*2.1)),(.07,.04,.07),'e9b0bd' if k%2 else 'f8e5c9',tree)
    arch=[]
    for i in range(33):a=i*math.pi/32;arch.append((1.5*math.cos(a),3.2,1.85+1.5*math.sin(a)))
    g.curve('Ivory wedding arch',arch,.065,g.mat('f6ecd8'),wedding)
    for side in [-1,1]:g.bar('Wedding arch upright',(side*1.5,3.2,0),(side*1.5,3.2,1.85),.065,'f6ecd8',wedding)
    for i,p in enumerate(arch):
        if i%2:continue
        x,y,z=p
        for k in range(4):g.sphere('Sculpted wedding rose petal',(x+.04*math.cos(k*1.57),y-.04,z+.04*math.sin(k*1.57)),(.065,.035,.045),'e8a9b4' if i%4 else 'fff2df',wedding)
        g.meshx('Wedding pointed leaves',[(x-.14,y,z-.03),(x,y-.03,z+.11),(x+.14,y,z-.03),(x,y+.04,z-.12)],[(0,1,2,3)],g.mat('4d7854'),wedding)
    for side in [-1,1]:
        for j in range(3):
            x=side*(1.25 if side<0 and j==2 else 1.7);y=1.35 if side<0 and j==2 else -.8+j*.95
            g.boxx('Wedding oak pew seat',(x,y,.44),(1.0,.45,.10),'77543b',wedding)
            g.boxx('Wedding pew back',(x,y+.22,.81),(1.0,.09,.73),'906c4e',wedding)
            for dx in [-.38,.38]:g.boxx('Wedding pew supported leg',(x+dx,y,.20),(.07,.35,.40),'634932',wedding)
    return {'bathroom':bathroom,'living':living,'paris':paris,'wedding':wedding}
