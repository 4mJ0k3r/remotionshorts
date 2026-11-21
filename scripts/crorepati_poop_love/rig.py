"""One continuous body cel; independent image-plane head, outward IK and supports."""
import bpy,math
from mathutils import Vector,Quaternion
from pathlib import Path
V=Vector

def image(path):
    im=bpy.data.images.load(str(path),check_existing=True)
    if not im.packed_file:im.pack()
    return im

def cel(name,path,lit=True):
    m=bpy.data.materials.new(name);m.use_nodes=True;m.use_fake_user=True;m.surface_render_method='DITHERED' if lit else 'BLENDED'
    n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    tex=n.new('ShaderNodeTexImage');tex.image=image(path)
    em=n.new('ShaderNodeEmission');em.inputs[1].default_value=1;l.new(tex.outputs['Color'],em.inputs[0]);surf=em.outputs[0]
    if lit:
        p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Roughness'].default_value=.9;p.inputs['Specular IOR Level'].default_value=0;l.new(tex.outputs['Color'],p.inputs['Base Color'])
        mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.18;l.new(p.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);surf=mix.outputs[0]
    tr=n.new('ShaderNodeBsdfTransparent');alpha=n.new('ShaderNodeMixShader');l.new(tex.outputs['Alpha'],alpha.inputs[0]);l.new(tr.outputs[0],alpha.inputs[1]);l.new(surf,alpha.inputs[2]);out=n.new('ShaderNodeOutputMaterial');l.new(alpha.outputs[0],out.inputs[0]);return m

def card(g,name,w,h,m):
    me=bpy.data.meshes.new(name);me.from_pydata([(-w/2,-h/2,0),(w/2,-h/2,0),(w/2,h/2,0),(-w/2,h/2,0)],[],[(0,1,2,3)]);me.materials.append(m)
    for uv,val in zip(me.uv_layers.new().data,[(0,0),(1,0),(1,1),(0,1)]):uv.uv=val
    return g.link(name,me)

def swap(o,name):
    m=bpy.data.materials[name]
    if o.data.materials[0]!=m:o.data.materials.clear();o.data.materials.append(m)

def curve_pose(obj,a,k,b):
    # Rounded quadratic ribbon, with fixed anatomical endpoint anchors.
    for i,p in enumerate(obj.data.splines[0].points):
        t=i/24;p.co=(*((1-t)**2*a+2*(1-t)*t*k+t*t*b),1)

def seated_leg(obj,hip,knee,ankle):
    # A quadratic with the knee as its control never reaches the knee.
    # Preserve real thigh/shin segments and round only the anatomical corner.
    before=knee.lerp(hip,.12);after=knee.lerp(ankle,.12)
    for i,point in enumerate(obj.data.splines[0].points):
        t=i/24
        if t<.42:p=hip.lerp(before,t/.42)
        elif t>.58:p=after.lerp(ankle,(t-.58)/.42)
        else:
            u=(t-.42)/.16;p=(1-u)**2*before+2*(1-u)*u*knee+u*u*after
        point.co=(*p,1)

def elbow(a,b,pole,length):
    d=b-a;dist=max(.001,d.length);axis=d/dist;reach=min(dist,length*2-.0001);b=a+axis*reach
    perp=pole-axis*pole.dot(axis)
    if perp.length<1e-5:perp=V((1,0,0))
    return a+axis*reach*.5+perp.normalized()*math.sqrt(max(.0001,length*length-reach*reach*.25)),b

def create_cast(g,art):
    for path in art.glob('*.png'):
        if path.stem=='vignette':continue
        cel(path.stem,path,not path.stem.startswith('stamp_'))
    for who,size in [('broke',.88),('millionaire',.88),('butler',.83),('kid1',.528),('kid2',.528)]:
        root=g.link('char_'+who);root['size']=size
        headkind='broke' if who=='broke' else who
        card(g,who+'_head',1.12*size,1.12*size,bpy.data.materials['head_'+headkind])
        card(g,who+'_face',1.12*size,1.12*size,bpy.data.materials['face_neutral'+('_butler' if who=='butler' else '')])
        card(g,who+'_body',.72*size,1.04*size,bpy.data.materials['body_ragged'])
        card(g,who+'_mouth',.24*size,.16*size,bpy.data.materials['mouth_smile_0'])
        for j in ['L','R']:
            for limb in ['arm','leg']:g.curve(who+'_'+limb+j,[(0,0,0)]*25,.020*size,g.mat('1a1214',rough=1))
            g.sphere(who+'_hand'+j,(0,0,0),(.043*size,.030*size,.042*size),'1a1214',rough=1)
            g.sphere(who+'_shoe'+j,(0,0,0),(.085*size,.13*size,.045*size),'19151a',rough=.8)
            g.sphere(who+'_shadow'+j,(0,0,0),(.12*size,.16*size,.004),'454048',rough=1)
            g.sphere(who+'_knee'+j,(0,0,0),(.043*size,.053*size,.053*size),'19151a',rough=1)
        for j in range(4):
            tear=g.curve(who+'_tear'+str(j),[(0,0,0)]*25,.009*size,g.mat('91c9e1',rough=.08,em=.10))
            tear['fx']=True

class Actor:
    def __init__(self,who):
        self.who=who;self.o=bpy.context.scene.objects;self.size=self.o['char_'+who]['size']
        self.parts=[o for o in self.o if o.name.startswith(who+'_')]
    def visible(self,on):
        for o in self.parts:o.hide_render=not on
    def pose(self,root,q,expr='neutral',wardrobe='ragged',hands=None,feet=None,roll=0,spine=None,seated=False,kneel=False,talk=0,turn=0,tears=False,ground=0,seat_z=None,front_y=None,foot_z=None,mouth_style=None):
        self.visible(True);s=self.size;root=V(root);right=q@V((1,0,0));n=q@V((0,0,1))
        qr=Quaternion(n,math.radians(roll));hq=q@Quaternion((0,0,1),math.radians(roll))
        axis=V(spine).normalized() if spine is not None else qr@V((0,0,1));side=qr@right
        pivot=.70*s if spine is None and abs(roll)>.001 else 0
        def p(x,z,depth=0):return root+V((0,0,pivot))+side*(x*s)+axis*(z*s-pivot)+n*(depth*s)
        hc=p(0,1.92);body=p(0,1.12,-.008)
        # A low camera can make the lower card nearer than the head. Recess
        # the entire continuous body behind the head plane so its collar and
        # neck cannot draw across the cream chin during pitched shots.
        body-=n*max(0,n.dot(body-hc)+.020*s)
        for part,pos in [('head',hc),('body',body),('face',hc+n*.006*s)]:
            o=self.o[self.who+'_'+part];o.location=pos;o.rotation_mode='QUATERNION';o.rotation_quaternion=hq
        hk='neat' if self.who=='broke' and wardrobe not in ['ragged','bath','booted'] else self.who
        swap(self.o[self.who+'_head'],'head_'+hk)
        swap(self.o[self.who+'_body'],'body_'+wardrobe)
        seed={'broke':61,'millionaire':117,'butler':39,'kid1':84,'kid2':141}[self.who]
        face_expr='blink' if expr in ['neutral','warm','sad'] and (bpy.context.scene.frame_current-seed)%157<3 else expr
        swap(self.o[self.who+'_face'],'face_'+face_expr+('_butler' if self.who=='butler' else ''))
        self.o[self.who+'_face'].location+=side*(turn*.435*s*.22)
        mood='sad' if expr in ['sad','plead','cry'] else ('teeth' if expr in ['panic','angry'] else ('o' if expr=='shock' else ('kiss' if expr=='kiss' else 'smile')))
        mp=hc+hq@V((turn*.435*s*.22,(.5-1080/1536)*1.12*s,.012*s))
        mouth=self.o[self.who+'_mouth'];mouth.location=mp;mouth.rotation_mode='QUATERNION';mouth.rotation_quaternion=hq;swap(mouth,f'mouth_{mouth_style or mood}_{talk}')
        if expr in ['sleep','relief']:mouth.scale=(.75,.5,1)
        else:mouth.scale=(1,1,1)
        actual_hands=[];max_arm=0
        for i,sgn in enumerate([-1,1]):
            letter='L' if i==0 else 'R';a=p(sgn*.18,1.34,.0)
            target=V(hands[i]) if hands and hands[i] is not None else p(sgn*.27,.92,.02)
            k,b=elbow(a,target,side*sgn+n*.10,.42*s);curve_pose(self.o[self.who+'_arm'+letter],a,k,b)
            self.o[self.who+'_hand'+letter].location=b;actual_hands.append(b);max_arm=max(max_arm,(a-b).length)
            hip=p(sgn*.11,.65 if seated and seat_z is not None else .70)
            if feet is not None:ankle=V(feet[i])
            elif seated:ankle=V((root.x,root.y,ground))+right*(sgn*.15*s)+V((0,-.41*s,.045*s))
            elif kneel:ankle=V((root.x,root.y,ground))+right*(sgn*.15*s)+V((0,.20*s,.045*s))
            else:ankle=p(sgn*.14,.052,.02)
            if seated:knee=root+right*(sgn*.15*s)+V((0,-.38*s,.70*s-.015))
            elif kneel:knee=V((root.x,root.y,ground))+right*(sgn*.12*s)+V((0,-.20*s,.053*s))
            elif spine is not None:knee=(hip+ankle)*.5+n*.03
            else:knee=(hip+ankle)*.5+V((0,-.055*s,0))
            if kneel=='one' and i==0:
                ankle=V((root.x,root.y,ground))+right*(sgn*.15*s)+V((0,-.32,.045*s))
                knee=V((root.x,root.y,ground))+right*(sgn*.12*s)+V((0,-.32,.30))
            if seated and seat_z is not None:
                hip.z=seat_z+.022
                knee=V((hip.x,front_y+.02,seat_z+.022))
                ankle=V((hip.x,front_y-.025,ground+.045*s if foot_z is None else foot_z))
                seated_leg(self.o[self.who+'_leg'+letter],hip,knee,ankle)
            else:curve_pose(self.o[self.who+'_leg'+letter],hip,knee,ankle)
            self.o[self.who+'_leg'+letter]['hip']=list(hip)
            self.o[self.who+'_leg'+letter]['knee']=list(knee)
            self.o[self.who+'_leg'+letter]['ankle']=list(ankle)
            self.o[self.who+'_knee'+letter].hide_render=not kneel or kneel=='one' and i==0
            self.o[self.who+'_knee'+letter].location=knee
            shoe=self.o[self.who+'_shoe'+letter];shoe.location=ankle;shoe.rotation_mode='QUATERNION';shoe.rotation_quaternion=qr
            shadow=self.o[self.who+'_shadow'+letter];shadow.location=(ankle.x,ankle.y,(ground if seated or kneel else root.z)+.006);shadow.hide_render=roll!=0 or spine is not None or self.who.startswith('kid') and seated
        for j in range(4):
            o=self.o[self.who+'_tear'+str(j)];o.hide_render=not tears
            if tears:
                t=(bpy.context.scene.frame_current+j*9)%29/29;sgn=-1 if j<2 else 1
                start=hc+hq@V((sgn*.19*s,-.06*s,.018*s));end=start+hq@V((sgn*.03*s,-(.10+.17*t)*s,.001))
                curve_pose(o,start,(start+end)*.5+hq@V((sgn*.02*s,0,0)),end)
        return {'head':hc,'mouth':mp,'hands':actual_hands,'q':hq,'n':n,'root':root,'arm_reach':max_arm,'size':s}
