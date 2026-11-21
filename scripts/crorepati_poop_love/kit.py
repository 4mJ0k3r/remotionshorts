"""Rich lightweight architecture, procedural grounds and mechanical assemblies."""
import bpy, math, random, sys
from pathlib import Path
from mathutils import Vector
ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/washroom_experiment'))
from sets import Stage,rgb
V=Vector

class Kit(Stage):
    def __init__(self,scene):super().__init__(scene);self.rng=random.Random(58)
    def boxx(self,n,p,d,c,parent=None,ink=True,bevel=.015):
        mat=c if not isinstance(c,str) else self.mat(c)
        o=self.box(n,p,d,mat,parent,bevel);o['set_ink']=ink;return o
    def sphere(self,n,p,scale,c,parent=None,metal=0,rough=.55,em=0):return self.ball(n,p,scale,self.mat(c,metal,rough,em),parent)
    def bar(self,n,a,b,r,c,parent=None):return self.rod(n,a,b,r,self.mat(c),parent)
    def torus(self,n,p,r,t,c,parent=None,metal=0,em=0):
        bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=8,major_radius=r,minor_radius=t)
        o=bpy.context.object;o.name=n;o.parent=parent;o.location=p;o.data.materials.append(self.mat(c,metal,.25,em));return o
    def meshx(self,n,verts,faces,material,parent=None):
        me=bpy.data.meshes.new(n);me.from_pydata(verts,[],faces);me.materials.append(material);return self.link(n,me,parent)
    def surface(self,name,a,b,kind='stone'):
        key=('surface',name)
        if key in self.materials:return self.materials[key]
        m=bpy.data.materials.new(name);m.use_nodes=True;n=m.node_tree.nodes;l=m.node_tree.links
        p=next(x for x in n if x.type=='BSDF_PRINCIPLED');p.inputs['Roughness'].default_value=.27
        tc=n.new('ShaderNodeTexCoord');noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=7 if kind=='marble' else 35;noise.inputs['Detail'].default_value=3;l.new(tc.outputs['Object'],noise.inputs['Vector'])
        if kind in ['stone','brick']:
            tex=n.new('ShaderNodeTexBrick');tex.inputs['Scale'].default_value=3.5;tex.inputs['Mortar Size'].default_value=.012;tex.inputs['Brick Width'].default_value=.45;tex.inputs['Row Height'].default_value=.25
            tex.inputs['Color1'].default_value=(*rgb(a),1);tex.inputs['Color2'].default_value=(*rgb(b),1);tex.inputs['Mortar'].default_value=(*rgb('57515a'),1);l.new(tc.outputs['Object'],tex.inputs['Vector']);l.new(tex.outputs['Color'],p.inputs['Base Color']);height=tex.outputs['Fac']
        else:
            ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*rgb(a),1);ramp.color_ramp.elements[1].color=(*rgb(b),1)
            l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],p.inputs['Base Color']);height=noise.outputs['Fac']
            if kind=='marble':
                noise.inputs['Scale'].default_value=3.0;noise.inputs['Roughness'].default_value=.8
                ramp.color_ramp.elements[0].position=.35;ramp.color_ramp.elements[1].position=.57
        bump=n.new('ShaderNodeBump');bump.inputs['Strength'].default_value=.20;bump.inputs['Distance'].default_value=.026;l.new(height,bump.inputs['Height']);l.new(bump.outputs[0],p.inputs['Normal'])
        self.materials[key]=m;return m
    def root(self,name,x):return self.link(name,xyz=(x,0,0))
    def sky(self,r,colors):
        r['sky_colors']=colors
        mat=bpy.data.materials.new(r.name+' three-stop sky');mat.use_nodes=True;n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links
        tc=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(tc.outputs['Generated'],sep.inputs[0])
        ramp=n.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].position=0;ramp.color_ramp.elements[0].color=(*rgb(colors[2]),1);e=ramp.color_ramp.elements.new(.48);e.color=(*rgb(colors[1]),1);ramp.color_ramp.elements[-1].position=1;ramp.color_ramp.elements[-1].color=(*rgb(colors[0]),1)
        height=n.new('ShaderNodeMapRange');height.inputs['From Min'].default_value=3/14;height.inputs['From Max'].default_value=10/14
        l.new(sep.outputs['Z'],height.inputs[0]);l.new(height.outputs[0],ramp.inputs[0]);em=n.new('ShaderNodeEmission');em.inputs[1].default_value=.8;l.new(ramp.outputs[0],em.inputs[0]);out=n.new('ShaderNodeOutputMaterial');l.new(em.outputs[0],out.inputs[0])
        # Sky lives in the camera-only World shader. An opaque backdrop wall
        # would intercept the low sunset SUN and erase railing cast shadows.
        for i in range(9):
            x=-7+i*1.8;z=3.6+(i%3)*.7
            for j in range(3):self.sphere('Soft cloud puff',(x+j*.42,10.8,z+.10*(j%2)),(.65,.20,.20+.08*(j%2)),'e7d5cf',r,rough=1,em=.30)
    def lighting(self,r,day=True,energy=5,color='ffe0b5'):
        if day:
            rear=r.name in ['SET_PARIS','SET_WEDDING']
            sun=self.light(r.name+' Sun','SUN',(-3,7,4) if rear else (-4,-3,7),(0,.3,0) if rear else (0,1,0),energy,color,r);sun.data.angle=math.radians(10);sun.data.use_shadow=True
            if rear:self.light(r.name+' front bounce','AREA',(0,-1.4,3.4),(0,.5,1.4),180,'ffe2bb',r).data.size=3
        else:self.light(r.name+' key','AREA',(-1.5,-1.1,3),(0,0,1.1),160,color,r).data.size=1.8
        self.light(r.name+' fill','AREA',(2,-.5,3),(0,1,1),70,'9eace3',r)
        self.light(r.name+' rim','AREA',(-1,2.8,3),(0,0,1.4),100,'ffc77e',r)
    def room(self,name,x,wall='d3c1a0',floor=None):
        r=self.root(name,x);floor=floor or self.surface(name+' marble','c5b89e','f3e8d1','marble')
        self.boxx(name+' Floor',(0,.8,-.08),(8,13,.16),floor,r,False)
        for side in [-1,1]:
            self.boxx(name+' side',(side*3.95,.7,2.1),(.14,13,4.2),wall,r,False)
            self.boxx('Dark skirting',(side*3.84,.7,.13),(.09,12.8,.22),'544553',r)
        self.boxx(name+' Rear',(0,5.9,2.1),(8,.15,4.2),wall,r,False)
        self.boxx(name+' Ceiling',(0,.7,4.22),(8,13,.12),'eee0c7',r,False)
        self.boxx(name+' Front',(0,-5.7,2.1),(8,.12,4.2),wall,r,False)
        for x in [-2.8,-1.4,0,1.4,2.8]:
            self.boxx('Recessed wall panel',(x,5.79,1.95),(1.10,.035,2.8),'a99478',r)
            self.boxx('Inset warm plaster',(x,5.756,1.95),(1.02,.028,2.70),wall,r)
        self.lighting(r,False)
        return r
    def lamp(self,name,p,r):
        x,y,z=p;self.bar(name+' post',(x,y,0),(x,y,z),.032,'282c3a',r)
        self.boxx(name+' lantern',(x,y,z),(.23,.20,.34),'423a34',r)
        self.boxx(name+' glowing panes',(x,y-.105,z),(.16,.012,.25),self.mat('ffcd78',em=2),r,False)
        self.light(name+' pool','POINT',(x,y-.13,z),(0,0,0),85,'ffbd69',r)
    def tree(self,name,pos,r,scale=1):
        root=self.link(name,p=r,xyz=pos);root.scale=(scale,)*3
        bark=self.surface(name+' bark','49352e','89734f','wood')
        self.rod('Bark trunk',(0,0,0),(.12,0,2.9),.14,bark,root)
        for j in range(6):
            a=j*math.tau/6;end=V((math.cos(a)*.8,math.sin(a)*.65,2.3+(j%2)*.45));self.rod('Sculpted branch',(.05,0,1.5),end,.055,bark,root)
            for k in range(7):
                c=end+V((self.rng.uniform(-.45,.45),self.rng.uniform(-.4,.4),self.rng.uniform(-.3,.5)))
                w=.40+self.rng.random()*.20;h=.18+self.rng.random()*.12
                verts=[(-w,0,0),(-w*.35,-.10,h*.6),(0,0,h),(.55*w,.05,.55*h),(w,0,0),(.45*w,.07,-h*.7),(0,.12,-h),(-.55*w,.08,-h*.45)]
                o=self.meshx('Layered pointed foliage',verts,[(0,1,2,3,4,5,6,7)],self.mat(['476b43','365a3c','61854d'][k%3],rough=.8),root);o.location=c;o.rotation_euler.z=j*.8+k*.4
        return root
    def door(self,name,r,x,y,width=1.0,height=2.5,side=1,color='68412c'):
        # Leaf runs from the chosen hinge toward the latch in local X.
        hinge=self.link(name+' hinge',p=r,xyz=(x,y,0));hinge['side']=side
        self.boxx(name+' leaf',(side*width/2,0,height/2),(width,.09,height),color,hinge)
        for z in [.60,1.65]:self.boxx(name+' carved inset',(side*width/2,-.06,z),(width-.15,.04,.70),'95653b',hinge)
        self.boxx(name+' gold border',(side*width/2,-.084,height-.10),(width-.12,.025,.04),'c89c48',hinge)
        self.boxx(name+' handle rosette',(side*(width-.12),-.09,1.15),(.075,.035,.15),'cfa95a',hinge)
        self.rod(name+' mounted lever',(side*(width-.12),-.13,1.15),(side*(width-.27),-.13,1.15),.018,self.mat('cfa95a',metal=.8),hinge)
        return hinge
    def toilet(self,name,r,p=(0,0,0),scale=1):
        root=self.link(name,p=r,xyz=p);root.scale=(scale,)*3
        gold=self.mat('ffd700',metal=.92,rough=.14)
        self.ball(name+' pedestal',(0,.08,.20),(.25,.31,.23),gold,root)
        # Open double-walled bowl, not a solid ellipsoid piercing seated legs.
        profile=[(.14,.20,.21),(.25,.34,.33),(.34,.44,.50),(.33,.42,.57),(.27,.34,.57),(.25,.32,.48),(.11,.15,.35)]
        verts=[(rx*math.cos(i*math.tau/48),-.13+ry*math.sin(i*math.tau/48),z) for rx,ry,z in profile for i in range(48)]
        faces=[(j*48+i,j*48+(i+1)%48,(j+1)*48+(i+1)%48,(j+1)*48+i) for j in range(len(profile)-1) for i in range(48)]
        bowl=self.meshx(name+' sculpted hollow bowl',verts,faces,gold,root)
        for poly in bowl.data.polygons:poly.use_smooth=True
        ring=self.torus(name+' seat rim',(0,-.11,.57),.30,.035,'ffd700',root,.92);ring.scale.y=1.25
        self.sphere(name+' recessed cavity',(0,-.10,.454),(.22,.28,.009),'372b20',root)
        root['seat_z']=.605;root['bowl_front_y']=-.57
        self.boxx(name+' tank',(0,.38,.79),(.62,.24,.62),gold,root)
        self.boxx(name+' cistern lid',(0,.38,1.12),(.66,.28,.06),gold,root)
        self.sphere(name+' flush button',(.20,.36,1.16),(.045,.045,.014),'ecdbac',root,metal=.9)
        return root
    def sofa(self,r):
        root=self.link('VelvetSofa',p=r)
        velvet=self.surface('Red velvet weave','791c35','ad3b49','weave')
        self.boxx('Sofa base',(0,.65,.28),(3.8,1.40,.30),'5b2634',root,bevel=.10)
        for x in [-1.14,0,1.14]:
            self.boxx('Tufted seat cushion',(x,.42,.50),(1.10,1.10,.22),velvet,root,bevel=.10)
            self.boxx('Sofa buttoned back',(x,1.20,1.03),(1.10,.25,1.02),velvet,root,bevel=.10)
            for dx in [-.28,0,.28]:self.sphere('Velvet tuft button',(x+dx,1.055,1.04),(.025,.012,.025),'c57976',root)
        for x in [-1.80,1.80]:self.boxx('Rounded sofa arm',(x,.63,.73),(.25,1.40,.60),velvet,root,bevel=.10)
        for x in [-1.55,1.55]:
            for y in [.12,1.1]:self.boxx('Sofa dark wooden foot',(x,y,.10),(.12,.13,.20),'342c31',root)
        return root

def heart_mesh(g,name,parent=None):
    pts=[]
    for i in range(48):
        a=i*math.tau/48;pts.append((.01*16*math.sin(a)**3,0,.01*(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))))
    vs=[(x,y-.025,z) for x,y,z in pts]+[(x,y+.025,z) for x,y,z in pts]
    faces=[tuple(range(47,-1,-1)),tuple(range(48,96))]+[(i,(i+1)%48,(i+1)%48+48,i+48) for i in range(48)]
    o=g.meshx(name,vs,faces,g.mat('ff6ba1',rough=.20,em=3),parent);mod=o.modifiers.new('Soft beveled heart','BEVEL');mod.width=.012;mod.segments=2;return o
