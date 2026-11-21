"""Scene-lit geometry, semantic fixtures and dimensional Hanfu characters."""
import bpy,bmesh,math,random
from pathlib import Path
from mathutils import Vector as V,Matrix,Quaternion
from primitives import Stage,mat,rgb,noise_material,image,key,linear
OUT=Path(r'D:\remotionshorts\renders\ancient_condom');ART=OUT/'assets'
def ease(a,b,f):
    u=max(0.,min(1.,(f-a)/(b-a)));return u*u*(3-2*u)
def setkey(o,path,value,f):setattr(o,path,value);o.keyframe_insert(path,frame=f)
def curve_at(o,points,f):
    pts=[V(x) for x in points]
    for i,(p,v) in enumerate(zip(o.data.splines[0].bezier_points,pts)):
        tangent=(pts[min(len(pts)-1,i+1)]-pts[max(0,i-1)])*(.24 if 0<i<len(pts)-1 else .3)
        p.handle_left_type=p.handle_right_type='FREE';p.co=v;p.handle_left=v-tangent;p.handle_right=v+tangent
        for path in ['co','handle_left','handle_right']:p.keyframe_insert(path,frame=f)
def lit(h,rough=.5,metal=0,alpha=1,gradient=False):
    m=mat(h,metal=metal,rough=rough)
    if alpha<1:m=m.copy();m.name='Lit translucent '+h;m.surface_render_method='DITHERED';m.node_tree.nodes.get('Principled BSDF').inputs['Alpha'].default_value=alpha
    if gradient and not m.get('gradient'):
        n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Coat Weight'].default_value=.18;p.inputs['Coat Roughness'].default_value=.3
        facing=n.new('ShaderNodeLayerWeight');r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].color=(.63,.63,.63,1);r.color_ramp.elements[1].color=(1,1,1,1);l.new(facing.outputs['Facing'],r.inputs[0])
        mix=n.new('ShaderNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=1;mix.inputs[1].default_value=(*rgb(h),1);l.new(r.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],p.inputs['Base Color']);m['gradient']=True
    return m
def soft(h,alpha=.25,emission=0):
    m=lit(h,rough=1,alpha=1).copy();m.name='Soft lit '+h;m.surface_render_method='BLENDED';p=m.node_tree.nodes.get('Principled BSDF');p.inputs['Emission Color'].default_value=(*rgb(h),1);p.inputs['Emission Strength'].default_value=emission
    n=m.node_tree.nodes;l=m.node_tree.links;t=n.new('ShaderNodeTexImage');t.image=image(ART/'soft_alpha.png');o=n.new('ShaderNodeObjectInfo');mul=n.new('ShaderNodeMath');mul.operation='MULTIPLY';mul.inputs[1].default_value=alpha;l.new(t.outputs['Alpha'],mul.inputs[0]);gate=n.new('ShaderNodeMath');gate.operation='MULTIPLY';l.new(mul.outputs[0],gate.inputs[0]);l.new(o.outputs['Alpha'],gate.inputs[1]);l.new(gate.outputs[0],p.inputs['Alpha']);return m
def shadow(g,xy,rx,ry,parent=None,z=.002):
    return g.plane('Support-local contact shadow',rx*2,ry*2,soft('24180d',.34),xyz=(xy[0],xy[1],z),parent=parent)
def lathe(g,name,profile,material,xyz=(0,0,0),parent=None,n=40):
    verts=[];rings=[];faces=[]
    for r,z in profile:
        if r<1e-6:rings.append([len(verts)]);verts.append((0,0,z))
        else:
            ring=[]
            for i in range(n):ring.append(len(verts));a=i*math.tau/n;verts.append((r*math.cos(a),r*math.sin(a),z))
            rings.append(ring)
    for a,b in zip(rings,rings[1:]):
        for i in range(n):
            if len(a)==1 and len(b)>1:faces.append((a[0],b[(i+1)%n],b[i]))
            elif len(b)==1 and len(a)>1:faces.append((a[i],a[(i+1)%n],b[0]))
            elif len(a)>1 and len(b)>1:faces.append((a[i],a[(i+1)%n],b[(i+1)%n],b[i]))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(material);mesh.update();o=g.obj(name,mesh,xyz,parent)
    for p in mesh.polygons:p.use_smooth=True
    return o
def ring(g,name,xyz,r,t,material,parent=None):
    pts=[(r*math.cos(i*math.tau/64),r*math.sin(i*math.tau/64),0) for i in range(64)]
    o=g.curve(name,pts,t,material,parent,True);o.location=xyz;return o
def tube(g,name,points,r,material,parent=None,rib=.04):
    pts=[V(p) for p in points];verts=[];faces=[];n=16
    for i,p in enumerate(pts):
        tangent=(pts[min(len(pts)-1,i+1)]-pts[max(0,i-1)]).normalized();ref=V((0,0,1)) if abs(tangent.z)<.95 else V((0,1,0));a=tangent.cross(ref).normalized();b=tangent.cross(a)
        radius=r*(1+rib*math.cos(i*math.pi*.8))
        for j in range(n):v=p+radius*(a*math.cos(j*math.tau/n)+b*math.sin(j*math.tau/n));verts.append(tuple(v))
    for i in range(len(pts)-1):
        for j in range(n):a=i*n+j;b=i*n+(j+1)%n;faces.append((a,b,b+n,a+n))
    mesh=bpy.data.meshes.new(name);mesh.from_pydata(verts,[],faces);mesh.materials.append(material);mesh.update();o=g.obj(name,mesh,parent=parent)
    for p in mesh.polygons:p.use_smooth=True
    return o
def coil(g,name,material,xyz,scale=1):
    pts=[]
    for i in range(120):
        t=i/119;a=t*math.tau*2.6;r=.14+.27*t;pts.append((r*math.cos(a),r*.75*math.sin(a),.025*math.sin(t*math.tau)))
    root=g.obj(name+' root',xyz=xyz);o=tube(g,name,pts,.057,material,root,.05);root.scale=(scale,)*3;return root
def sheath(g,name,material,xyz,length=1.05,radius=.074,parent=None):
    root=g.obj(name+' root',xyz=xyz,parent=parent);profile=[]
    for i in range(65):
        z=(length-radius)*i/64;r=radius+.0035*math.sin(i/64*math.tau*19);profile.append((r,z))
    for i in range(1,13):a=i/12*math.pi/2;profile.append((radius*math.cos(a),length-radius+radius*math.sin(a)))
    for r,z in reversed(profile[:-1]):profile.append((max(0,r-.004),z-.003))
    lathe(g,name+' ribbed thin wall',profile,material,parent=root,n=32);ring(g,name+' open rolled rim',(0,0,0),radius,.006,material,root);return root
def peg(g,xyz):
    root=g.obj('Peeled peachwood peg',xyz=xyz);wood=noise_material('Peachwood long fibres','b47842','dfb17c',7,.55,.06,True)
    lathe(g,'Clearly wooden flat-ended peg',[(0,0),(.068,0),(.068,.9),(0,.9)],wood,parent=root,n=32);return root
def teapot(g,xyz,pink=False):
    root=g.obj('Pink warm-water teapot' if pink else 'Terracotta vinegar teapot',xyz=xyz);m=lit('ca8b83' if pink else '9e5536',rough=.35,gradient=True)
    lathe(g,'Round clay teapot',[(0,-.17),(.16,-.17),(.25,-.06),(.26,.08),(.18,.20),(.11,.23),(.10,.20),(.17,.17)],m,parent=root)
    lathe(g,'Fitted clay lid',[(0,.235),(.14,.235),(.12,.26),(.03,.28),(0,.28)],m,parent=root);g.ball('Clay lid knob',(0,0,.31),(.04,.04,.035),m,root)
    tube(g,'Connected tapered teapot spout',[(-.17,0,.05),(-.30,0,.12),(-.43,0,.24),(-.55,0,.28)],.048,m,root,0)
    g.curve('Connected clay handle',[(.19,0,.15),(.40,0,.15),(.41,0,-.12),(.20,0,-.10)],.035,m,root)
    root['spout_local']=(-.55,0,.28);return root
def knife(g,xyz,small=False):
    root=g.obj('Traditional curved knife grip',xyz=xyz);wood=lit('4b2819',rough=.55);steel=lit('b7b6ae',rough=.23,metal=.78)
    g.box('Connected knife handle',(.24,0,0),(.35,.07,.075),wood,root,.025)
    points=[(.06,-.015,-.035),(-.18,-.015,-.055),(-.53,-.015,-.18),(-.65,-.015,-.27),(-.43,-.015,-.25),(-.15,-.015,-.13),(.06,-.015,.045)]
    verts=points+[(x,.015,z) for x,y,z in points];n=len(points);faces=[tuple(range(n-1,-1,-1)),tuple(range(n,2*n))]+[(i,(i+1)%n,(i+1)%n+n,i+n) for i in range(n)]
    me=bpy.data.meshes.new('Curved steel blade');me.from_pydata(verts,[],faces);me.materials.append(steel);g.obj('Single connected curved blade',me,parent=root)
    for x in [.17,.30]:g.ball('Knife rivet',(x,-.04,0),(.013,.005,.013),lit('bca96b',metal=.8),root)
    root.scale=(.55,)*3 if small else (1,)*3;return root
def hand(g,xyz,point=False):
    root=g.obj('Dimensional hand root',xyz=xyz);skin=lit('dfb58b',rough=.47,gradient=True)
    g.ball('Scene-lit palm',(0,0,0),(.20,.16,.075),skin,root);g.ball('Wrist entering from right',(.24,0,.005),(.17,.105,.065),skin,root)
    for i in range(4):
        y=(i-1.5)*.075
        if point and i>0:pts=[(-.12,y,0),(-.22,y,.08),(-.09,y,.10)]
        elif point:pts=[(-.12,y,0),(-.35,y,-.01),(-.55,y,-.02)]
        else:pts=[(-.11,y,0),(-.36,y,-.05),(-.48,y,-.29)]
        g.curve('Rounded anatomical finger '+str(i),pts,.041-i*.002,skin,root)
        for p in pts:g.ball('Finger knuckle',p,(.041-i*.002,)*3,skin,root)
    g.curve('Opposing thumb',[(.09,-.12,0),(.17,-.26,-.12),(-.01,-.28,-.23)],.05,skin,root)
    root['index_pad_local']=(-.55,-.1125,-.06) if point else (-.48,-.1125,-.33);return root
def sheep(g,xyz,clay=False):
    root=g.obj('Clay sheep root' if clay else 'Horned white sheep root',xyz=xyz);wool=noise_material('Clay wool' if clay else 'Warm ivory wool','85827b' if clay else 'c7c5b8','c6c3b9' if clay else 'f0ecda',16,.9,.04)
    g.ball('Sheep rounded body',(0,0,.48),(.48,.25,.30),wool,root);g.ball('Sheep head',(.43,-.02,.59),(.20,.14,.18),wool,root)
    for x in [-.27,.27]:
        for y in [-.15,.15]:g.rod('Grounded sheep leg',(x,y,.055),(x,y,.34),.045,lit('746654'),root);g.ball('Sheep hoof',(x,y,.045),(.06,.055,.045),lit('3b3229'),root)
    for sign in [-1,1]:
        g.ball('Soft sheep ear',(.45,sign*.16,.64),(.12,.045,.06),wool,root)
        g.curve('Curled ivory horn',[(.38,sign*.10,.72),(.34,sign*.16,.91),(.51,sign*.18,.92),(.56,sign*.15,.78)],.035,lit('cbbd99',rough=.45),root)
        g.ball('Sheep black eye',(.53,sign*.108,.62),(.022,.012,.025),lit('201a17'),root)
    g.ball('Sheep muzzle',(.60,-.015,.53),(.08,.11,.065),lit('a69b88'),root)
    for i in range(12):a=i*2.4;g.ball('Wool tuft',(.33*math.cos(a),.16*math.sin(a),.62+.10*(i%3)/2),(.11,.10,.1),wool,root)
    return root
def rose(g,xyz):
    root=g.obj('Rose semantic stem grip',xyz=xyz);green=lit('36552a');red=lit('aa2534',rough=.5)
    g.rod('Rose stem',(0,0,-.1),(0,0,.24),.009,green,root)
    for i in range(7):
        a=i*math.tau/7;o=g.ball('Rose dimensional petal',(.038*math.cos(a),.038*math.sin(a),.25+.014*(i%2)),(.038,.025,.05),red,root);o.rotation_euler.z=a
    g.ball('Rose folded centre',(0,0,.27),(.035,.035,.045),red,root);g.ball('Stem leaf',(.04,0,.06),(.06,.012,.022),green,root);return root
def decal_material(path):
    m=bpy.data.materials.new('Pure scene-lit '+Path(path).stem);m.use_nodes=True;m.surface_render_method='DITHERED';n=m.node_tree.nodes;l=m.node_tree.links;p=n.get('Principled BSDF');p.inputs['Roughness'].default_value=.65
    t=n.new('ShaderNodeTexImage');t.image=image(path);l.new(t.outputs['Color'],p.inputs['Base Color']);l.new(t.outputs['Alpha'],p.inputs['Alpha']);return m
def face_mesh(g,name,material,parent):
    verts=[];uvs=[];faces=[];n=18
    for j in range(n+1):
        for i in range(n+1):
            x=(i/n-.5)*.55;y=(j/n-.5)*.55;z=.31*math.sqrt(max(.02,1-(x/.35)**2-(y/.34)**2))+.002;verts.append((x,y,z));uvs.append((i/n,j/n))
    for j in range(n):
        for i in range(n):k=j*(n+1)+i;faces.append((k,k+1,k+n+2,k+n+1))
    me=bpy.data.meshes.new(name);me.from_pydata(verts,[],faces);me.materials.append(material);uv=me.uv_layers.new()
    for p in me.polygons:
        p.use_smooth=True
        for li in p.loop_indices:uv.data[li].uv=uvs[me.loops[li].vertex_index]
    return g.obj('Face decal / '+name,me,parent=parent)
class CoupleActor:
    def __init__(self,g,who,position):
        self.g=g;self.who=who;self.root=g.obj(who+' Hanfu actor',xyz=position);female=who=='female';cloth=lit('258d88' if female else '4e60a0',rough=.68,gradient=True);trim=lit('d9b781',rough=.5);skin=lit('f2dfbd',rough=.55,gradient=True)
        lathe(g,who+' flowing Hanfu',[(0,.10),(.30,.10),(.26,.40),(.16,.73),(.23,.94),(.19,1.04),(.08,1.08),(0,1.08)],cloth,parent=self.root)
        g.curve('Hanfu crossed collar',[(-.17,0,1.02),(.08,-.18,.81),(.17,-.15,.68)],.017,trim,self.root);g.curve('Hanfu inner collar',[(.17,0,1.02),(-.07,-.19,.82),(-.15,-.15,.72)],.017,trim,self.root)
        ring(g,'Hanfu tied belt',(0,0,.70),.17,.035,trim,self.root)
        g.ball('Clothed neck',(0,0,1.10),(.07,.07,.105),skin,self.root)
        self.head=g.obj(who+' independent dimensional head',xyz=(0,0,1.43),parent=self.root);g.ball(who+' spherical cream head',(0,0,0),(.35,.34,.31),skin,self.head)
        # Thin inverted hull gives an ink silhouette while retaining physical lighting.
        bm=bmesh.new();bmesh.ops.create_uvsphere(bm,u_segments=32,v_segments=20,radius=1);bmesh.ops.scale(bm,verts=list(bm.verts),vec=(.358,.348,.318));bmesh.ops.reverse_faces(bm,faces=list(bm.faces));ink=lit('382821',rough=.8).copy();ink.use_backface_culling=True;ink.use_backface_culling_shadow=True;ink.use_backface_culling_lightprobe_volume=True;g.mesh('Dimensional head ink hull',bm,ink,parent=self.head)
        hair=lit('30201a',rough=.55);verts=[];faces=[]
        for j in range(11):
            phi=j/10*1.07
            for i in range(40):
                a=i*math.tau/40;edge=.03*math.sin(a*3) if j==10 else 0;ph=phi+edge;verts.append((.36*math.sin(ph)*math.cos(a),.35*math.cos(ph),.325*math.sin(ph)*math.sin(a)))
        for j in range(10):
            for i in range(40):a=j*40+i;b=j*40+(i+1)%40;faces.append((a,b,b+40,a+40))
        me=bpy.data.meshes.new('Fitted ancient hair');me.from_pydata(verts,[],faces);me.materials.append(hair);g.obj('Polygon hair cap',me,parent=self.head);g.ball('Ancient topknot',(.02,.37,-.04),(.11,.10,.11),hair,self.head)
        g.rod('Golden hair pin',(-.17,.39,-.025),(.18,.39,-.025),.012,lit('d3ad53',metal=.6),self.head)
        self.faces={pose:face_mesh(g,who+' '+pose,decal_material(ART/f'face_{pose}.png'),self.head) for pose in ['smile','shy','panic','horror','blink']}
        self.arms=[];self.hands=[]
        for sign in [-1,1]:
            self.arms.append(g.curve('Wide Hanfu sleeve',[(sign*.20,0,.94),(sign*.32,-.05,.79),(sign*.29,-.12,.71)],.095,cloth,self.root));self.hands.append(g.ball('Rounded scene-lit hand',(sign*.29,-.12,.71),(.055,.047,.055),skin,self.root))
            g.ball('Grounded black silk shoe',(sign*.13,-.07,.045),(.10,.17,.045),lit('25242b'),self.root);shadow(g,(sign*.13,-.07),.13,.19,self.root)
        self.drops=[]
        for sign in [-1,1]:
            drop=g.ball('Attached temple sweat',(sign*.30,.05,.17),(.025,.06,.016),lit('8cdbec',rough=.15),self.head);self.drops.append(drop)
    def pose(self,f,cam,expression='smile',hands=None,sweat=False):
        q=cam.rotation_euler.to_quaternion();self.head.rotation_euler=q.to_euler();key(self.head,'rotation_euler',f)
        blink=(f+(19 if self.who=='female' else 0))%103 in [0,1,2]
        for name,o in self.faces.items():o.scale=(1,1,1) if name==('blink' if blink else expression) else (0,0,0);key(o,'scale',f)
        for d in self.drops:d.scale=(.025,.06,.016) if sweat else (0,0,0);key(d,'scale',f)
        for i,sign in enumerate([-1,1]):
            shoulder=V((sign*.20,0,.94));target=V(hands[i]) if hands else V((sign*.30,-.08,.72));elbow=shoulder+V((sign*.20,-.04,-.14));curve_at(self.arms[i],[shoulder,elbow,target],f);self.hands[i].location=target;key(self.hands[i],'location',f)
def barrel(g,xy):
    root=g.obj('Open wooden barrel on round stool',xyz=(xy[0],xy[1],.45));wood=noise_material('Barrel curved staves','674329','b38350',8,.62,.08,True)
    lathe(g,'Watertight wooden barrel liner',[(0,0),(.36,0),(.41,.07),(.44,.36),(.41,.70),(.38,.73),(.35,.70),(.38,.36),(.34,.06),(0,.06)],wood,parent=root)
    for i in range(20):a=i*math.tau/20;o=g.box('Individual barrel stave',(.405*math.cos(a),.405*math.sin(a),.36),(.065,.125,.64),wood,root,.015);o.rotation_euler.z=a
    for z in [.10,.61]:ring(g,'Forged barrel hoop',(0,0,z),.43,.022,lit('3b3932',metal=.65),root)
    lathe(g,'Round stool seat',[(0,-.07),(.32,-.07),(.32,0),(0,0)],wood,parent=root)
    for i in range(3):a=i*math.tau/3;x=xy[0]+.23*math.cos(a);y=xy[1]+.23*math.sin(a);g.rod('Grounded stool leg',(x,y,0),(x,y,.38),.035,wood);shadow(g,(x,y),.06,.06)
    return root
def world(g):
    ground=lit('b88454',rough=.78);n=ground.node_tree.nodes;l=ground.node_tree.links;p=n.get('Principled BSDF');tc=n.new('ShaderNodeTexCoord');vor=n.new('ShaderNodeTexVoronoi');vor.feature='DISTANCE_TO_EDGE';vor.inputs['Scale'].default_value=90;l.new(tc.outputs['Generated'],vor.inputs[0]);r=n.new('ShaderNodeValToRGB');r.color_ramp.elements[0].position=.008;r.color_ramp.elements[0].color=(*rgb('6e4726'),1);r.color_ramp.elements[1].position=.035;r.color_ramp.elements[1].color=(*rgb('b88454'),1);l.new(vor.outputs['Distance'],r.inputs[0]);l.new(r.outputs[0],p.inputs['Base Color']);b=n.new('ShaderNodeBump');b.inputs['Strength'].default_value=.48;b.inputs['Distance'].default_value=.012;l.new(vor.outputs['Distance'],b.inputs['Height']);l.new(b.outputs[0],p.inputs['Normal'])
    g.box('Cracked ochre earth',(0,0,-.08),(14,12,.16),ground,bevel=0)
    stone=noise_material('Old courtyard stone','6c6f63','a8a58c',7,.82,.13);wood=noise_material('Weathered workbench grain','694128','b2804c',7,.64,.09,True);red=lit('a83f31',rough=.7)
    # Stone house, deep doorway, roof tiles and unlettered red banners.
    g.box('Stone house mass',(-.3,4.0,1.30),(6.0,.45,2.60),stone,bevel=.035)
    for row in range(8):
        for col in range(17):
            x=-3.15+col*.35+(row%2)*.175
            if -.65<x<.65 and row<6:continue
            g.box('Mortared house stone',(x,3.73,.17+row*.31),(.335,.065,.285),stone,bevel=.02)
    g.box('Deep red doorway',(0,3.66,1.0),(1.12,.10,2),lit('66342c'),bevel=.02)
    for x in [-.72,.72]:g.box('Unlettered red door banner',(x,3.59,1.20),(.15,.025,2.05),red,bevel=.008)
    roof=lit('535d61',rough=.68)
    for side in [-1,1]:
        for i in range(24):
            for j in range(5):
                o=g.box('Individual grey roof tile',(-3.30+i*.28,4.0+side*(.12+j*.25),3.20-j*.17),(.29,.32,.075),roof,bevel=.025);o.rotation_euler.x=side*math.radians(34)
    for i in range(34):
        x=-5+i*.31;g.box('Wooden palisade picket',(x,2.75,.9),(.23,.12,1.8+(i%3)*.08),wood,bevel=.025)
    for z in [.45,1.25]:g.box('Connected fence cross rail',(0,2.80,z),(10.6,.12,.10),wood)
    for i in range(12):g.rod('Hanging red firecracker',(2.45+(i%2)*.09,2.52,2.4-i*.07),(2.45+(i%2)*.09,2.52,2.45-i*.07),.034,red)
    bark=noise_material('Displaced grooved tree bark','342a20','6a4c2d',15,.9,.18,True)
    pts=[(-3.6,-.6,0),(-3.55,-.58,1),(-3.7,-.53,2),(-3.45,-.45,3)]
    trunk=tube(g,'Organic bark trunk',pts,.29,bark,rib=.15);sub=trunk.modifiers.new('Bark subdivision capped at two','SUBSURF');sub.levels=sub.render_levels=2;tex=bpy.data.textures.new('Fine physical bark relief',type='CLOUDS');tex.noise_scale=.09;dis=trunk.modifiers.new('Real bark displacement','DISPLACE');dis.texture=tex;dis.strength=.024;dis.mid_level=.5
    for target in [(-4.3,-.3,3.3),(-2.75,-.2,3.4),(-3.15,.6,3.6)]:g.rod('Connected tree bough',(-3.6,-.5,2.1),target,.13,bark)
    for i in range(12):a=i*2.4;g.ball('Soft tree canopy',(-3.5+.9*math.cos(a),-.2+.7*math.sin(a),3.3+.15*(i%3)),(.7,.55,.42),lit(['657142','6e7945','4b5b37'][i%3],rough=.9))
    shadow(g,(-3.6,-.6),.45,.45)
    # Workbench, joined hardware and readable long-grain scratches.
    g.box('Weathered workbench top',(0,-.4,.84),(2.1,.88,.12),wood,bevel=.035)
    for x in [-.85,.85]:
        for y in [-.73,-.07]:g.box('Workbench grounded leg',(x,y,.39),(.12,.12,.78),wood);shadow(g,(x,y),.1,.1)
    g.box('Workbench apron',(0,-.4,.70),(1.8,.72,.14),wood)
    for i in range(9):g.curve('Worktop grain groove',[(-.95,-.72+i*.075,.901),(-.25,-.70+i*.075,.901),(.90,-.73+i*.075,.901)],.003,lit('73502f'))
    barrel(g,(1.15,-.05));barrel(g,(4.05,1.0))
    # Stone fire ring and unlit split logs (flames are authored only in Cut8).
    for i in range(12):a=i*math.tau/12;g.ball('Campfire ring stone',(1.9+.52*math.cos(a),-1.7+.52*math.sin(a),.14),(.16,.13,.14),stone)
    for i in range(3):g.rod('Split hearth log',(1.52,-1.85+i*.13,.11),(2.28,-1.6-i*.08,.17),.07,lit('493022'))
    # Hollow mossy stone well and a connected, open bamboo spout.
    moss=noise_material('Mossy well stone','405942','868d6e',5,.86,.12)
    for row in range(4):
        for i in range(14):a=(i+(row%2)*.5)*math.tau/14;o=g.box('Mossy well block',(2.8+.52*math.cos(a),1+.52*math.sin(a),.11+row*.21),(.26,.19,.20),moss,bevel=.035);o.rotation_euler.z=a+math.pi/2
    for x in [2.25,3.35]:g.box('Grounded well post',(x,1.08,.86),(.10,.10,1.72),wood);shadow(g,(x,1.08),.09,.09)
    bamboo=lit('75834e',rough=.45)
    for i in range(5):a=V((2.9+i*.23,1.03,1.70-i*.025));b=a+V((.235,0,-.025));g.rod('Connected bamboo water pipe',a,b,.052,bamboo);g.ball('Bamboo joint',a,(.061,.061,.061),bamboo)
    g.rod('Bamboo terminal elbow',(4.04,1.03,1.575),(4.05,1,1.52),.055,bamboo)
    ring(g,'Open bamboo spout lip',(4.05,1,1.52),.047,.010,bamboo)
    # Stone preparation block and background grey brick wall.
    g.box('Rectangular preparation stone',(-2.2,1.6,.40),(1.25,.78,.80),stone,bevel=.04);shadow(g,(-2.2,1.6),.65,.42)
    for row in range(7):
        for col in range(10):g.box('Shaded grey brick',(-3.9+col*.34+(row%2)*.17,2.19,.15+row*.30),(.325,.16,.28),stone,bevel=.017)
    # Vegetable table in the background.
    g.box('Vegetable display tabletop',(3.9,2.0,.83),(1.45,.65,.10),wood)
    for x in [3.35,4.45]:
        for y in [1.78,2.22]:g.rod('Vegetable table leg',(x,y,0),(x,y,.8),.04,wood)
    for i in range(7):g.ball('Cabbage',(3.42+(i%4)*.24,1.85+(i//4)*.25,.97),(.12,.11,.13),lit('789553',rough=.8))
    for i in range(5):g.rod('Carrot',(4.13+i*.05,2.13,.9),(4.20+i*.04,1.91,.95),.027,lit('b86b35'))
    for xy,rx,ry in [((2.8,1),.77,.70),((1.9,-1.7),.65,.61),((-.3,4),3.1,.35),((0,2.75),5.3,.14)]:shadow(g,xy,rx,ry)
    for x in [3.35,4.45]:
        for y in [1.78,2.22]:shadow(g,(x,y),.08,.08)
    return {'bench':V((0,-.4,.90)),'tub':V((1.15,-.05,1.10)),'rinse':V((4.05,1.0,1.10)),'spout':V((4.05,1.0,1.52)),'stone':V((-2.2,1.6,.80)),'bowl':V((.2,.65,.46))}
