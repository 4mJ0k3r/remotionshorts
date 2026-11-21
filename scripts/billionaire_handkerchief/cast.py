"""Layered lit cel art, independent face pivots and curved articulated limbs."""
import math
from mathutils import Vector
from sets import rgb

INK = '2c1d22'
PALETTES = {
    'street': ('eee1cf','594c38','534038','372a30'),
    'groom': ('faeee0','263653','51352e','202a3d'),
    'oldman': ('fae4cf','c3a488','eee3d8','694d45'),
    'lady': ('f7e4d7','f9f0db','392632','583045'),
    'bride': ('fff0e2','f8ece4','3a2633','f8ece4'),
    'oldlady': ('f4dbcd','d69c98','bab0bb','645169'),
    'guard': ('ead0be','25293e','ead0be','202336'),
    'waiter': ('f4dbc8','292b46','302738','28223a'),
}


def pigment(g,h):
    import bpy
    k=('cel',h)
    if k in g.materials:return g.materials[k]
    m=bpy.data.materials.new('Cel pigment '+h); m.diffuse_color=(*rgb(h),1);m.use_nodes=True
    lit=next(n for n in m.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
    lit.inputs['Base Color'].default_value=m.diffuse_color;lit.inputs['Roughness'].default_value=.7
    lit.inputs['Specular IOR Level'].default_value=.28
    g.materials[k]=m
    return m


def poly(g, name, points, depth, material, parent, form=None):
    import bpy
    area=sum(x*v-u*y for (x,y),(u,v) in zip(points,points[1:]+points[:1]))
    if area<0:points=points[::-1]
    mesh=bpy.data.meshes.new(name)
    if form:
        # Sample the normals of a rounded shell on the ink drawing's existing plane.
        # Coplanar facial and wardrobe pieces can keep their established depth order.
        cx,cy,rx,ry=form
        count=len(points)
        vertices=[(cx,cy,0)]+[(cx+(x-cx)*q,cy+(y-cy)*q,0) for q in (.28,.56,.79,1) for x,y in points]
        faces=[(0,1+i,1+(i+1)%count) for i in range(count)]
        for ring in range(3):
            a=1+ring*count;b=a+count
            faces.extend((a+i,b+i,b+(i+1)%count,a+(i+1)%count) for i in range(count))
        mesh.from_pydata(vertices,[],faces);mesh.update()
        normals=[]
        for x,y,_ in vertices:
            u,v=(x-cx)/rx,(y-cy)/ry
            normals.append(Vector((u*.81,v*.63,math.sqrt(max(.09,1-.69*u*u-.52*v*v)))).normalized())
        for face in mesh.polygons:face.use_smooth=True
        mesh.normals_split_custom_set_from_vertices(normals)
    else:
        mesh.from_pydata([(x,y,0) for x,y in points],[],[tuple(range(len(points)))]);mesh.update()
    mesh.materials.append(material)
    return g.link(name,mesh,parent,(0,0,depth))


def oval(g,name,x,y,rx,ry,d,h,parent,organic=False,form=None,egg=False,lid=False):
    points=[]
    for i in range(64):
        a=i*math.tau/64;r=1+.022*math.sin(2*a+.6)-.015*math.cos(3*a-.8)+.008*math.sin(5*a+1.9) if organic else 1
        s=math.sin(a)
        vertical=max(-.86,min(.86,s)) if lid else s
        points.append((x+rx*r*math.cos(a)*(1+.12*s if egg else 1),y+ry*r*vertical))
    return poly(g,name,points,d,pigment(g,h),parent,form)


def stroke(g,name,a,b,c,depth,width,h,parent):
    nodes=[]
    for j in range(17):
        t=j/16;u=1-t
        x,y=[u*u*a[i]+2*u*t*b[i]+t*t*c[i] for i in range(2)]
        dx,dy=[2*u*(b[i]-a[i])+2*t*(c[i]-b[i]) for i in range(2)];n=max(.001,math.hypot(dx,dy))
        nodes.append(((x-dy*width/n,y+dx*width/n),(x+dy*width/n,y-dx*width/n)))
    poly(g,name,[v[1] for v in nodes]+[v[0] for v in reversed(nodes)],depth,pigment(g,h),parent)
    for x,y in (a,c):oval(g,name+' round cap',x,y,width,width,depth+.0001,h,parent)


def support_shadow(g, name, root, xyz, size, night=False):
    import bpy
    material_key='Night street contact shadow' if night else 'Soft receiver contact shadows'
    m=g.materials.get(material_key)
    if m is None:
        m=bpy.data.materials.new(material_key);m.use_nodes=True;m.surface_render_method='BLENDED'
        g.materials[material_key]=m
        n,l=m.node_tree.nodes,m.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial')
        tex=n.new('ShaderNodeTexCoord');d=n.new('ShaderNodeVectorMath');d.operation='DISTANCE';d.inputs[1].default_value=(.5,.5,0)
        l.new(tex.outputs['UV'],d.inputs[0]);fall=n.new('ShaderNodeMapRange');fall.interpolation_type='SMOOTHERSTEP'
        fall.inputs['From Min'].default_value=.19 if night else .045;fall.inputs['From Max'].default_value=.5;fall.inputs['To Min'].default_value=.68 if night else .72;fall.inputs['To Max'].default_value=0
        l.new(d.outputs['Value'],fall.inputs[0]);mix=n.new('ShaderNodeMixShader');l.new(fall.outputs[0],mix.inputs[0]);t=n.new('ShaderNodeBsdfTransparent');e=n.new('ShaderNodeEmission');e.inputs[0].default_value=(.001,.001,.002,1) if night else (.012,.007,.014,1);l.new(t.outputs[0],mix.inputs[1]);l.new(e.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
    x,y=size
    mesh=bpy.data.meshes.new(name);mesh.from_pydata([(-x,-y,0),(x,-y,0),(x,y,0),(-x,y,0)],[],[(0,1,2,3)]);mesh.materials.append(m)
    for loop,uv in zip(mesh.uv_layers.new().data,((0,0),(1,0),(1,1),(0,1))):loop.uv=uv
    return g.link(name,mesh,root,xyz)


class Actor:
    def __init__(self,g,root,who,position,scale=1,pose='stand',hands=None,expression='smile',turn=0,sunglasses=False,outfit_rim=False):
        skin,shirt,hair,pants=PALETTES[who]
        self.base=g.link(who+' actor',p=root,xyz=position);self.base.scale=(scale,)*3
        self.head=g.link(who+' independent camera-facing head',p=self.base,xyz=(0,0,1.02 if pose=='squat' else .95 if pose=='sit' else 1.43))
        self.body=g.link(who+' body and limbs',p=self.base,xyz=(0,0,.30 if pose in ('sit','squat') else .78))
        self.face=g.link('Grouped facial features',p=self.head,xyz=(turn*.080,0,.010))
        self.eyelids=[];self.feet=[];self.pose=pose
        self.chest=g.link(who+' chest breathing',p=self.body,xyz=(0,-.25,0))
        h,b,f=self.head,self.body,self.face
        feminine=who in ('lady','bride','oldlady'); young_lady=who in ('lady','bride')
        if young_lady:
            hair_root=g.link('Long hair behind shoulders',p=b,xyz=(0,0,-.063))
            for sign in (-1,1):
                oval(g,'Long inked side lock',sign*.289,.34,.128,.385,0,INK,hair_root,True)
                oval(g,'Chestnut side lock',sign*.286,.345,.105,.371,.002,hair,hair_root,True,(sign*.286,.345,.11,.37))
            oval(g,'Crown behind face',.012,.05,.372,.37,-.028,hair,h,True)
        if who=='oldlady':
            oval(g,'Silver bun outline',.24,.31,.17,.16,-.018,INK,h)
            oval(g,'Silver bun',.24,.31,.143,.135,-.017,hair,h)
        if who=='bride':
            poly(g,'Ivory veil',[(-.30,.24),(-.49,-.60),(.45,-.62),(.32,.20)],-.016,pigment(g,'ebdfec'),h)
        oval(g,'Variable-width head ink',0,0,.355,.365,0,INK,h,True,egg=True)
        oval(g,'Cool edge inside silhouette',.002,.006,.329,.337,.001,'bda6b7' if not feminine else 'c6adbb',h,True,(0,0,.33,.34),egg=True)
        oval(g,'Lit organic face',.006,.012,.321,.329,.002,skin,h,True,(0,0,.331,.34),egg=True)
        stroke(g,'Fine warm edge',(-.298,.065),(-.308,.148),(-.242,.232),.003,.0035,'fff0d6',h)
        if who in ('street','groom','oldman','waiter'):
            points=[(-.34,.03),(-.39,.22),(-.29,.35),(-.25,.44),(-.13,.36),(-.03,.49),(.08,.39),(.20,.44),(.30,.33),(.39,.26),(.32,.06),(.27,.24),(.17,.30),(-.04,.24),(-.23,.25),(-.29,.14)]
            if who!='street':points=[(x,y*.77+.036) for x,y in points]
            poly(g,'Inked asymmetric hairline',points,.004,pigment(g,INK),h)
            poly(g,'Hair painted fill',[(x*.925,(y-.23)*.85+.242) for x,y in points],.005,pigment(g,hair),h)
            if who!='waiter':
                oval(g,'Beard ink',.008,-.229,.247,.130,.006,INK,h,True)
                oval(g,'Trimmed beard',.010,-.226,.226,.110,.007,hair,h,True)
        if young_lady or who=='oldlady':
            stroke(g,'Side-swept bang',(-.316,.139),(-.14,.43),(.245,.256),.005,.054,INK,h)
            stroke(g,'Warm hair highlight',(-.30,.154),(-.13,.418),(.232,.267),.006,.042,hair,h)
        for side in (-1,1):
            ex=side*.124
            eye=g.link('Horizontal lid aperture',p=f,xyz=(ex,.068,.001));self.eyelids.append(eye)
            oval(g,'Horizontal-lid clipped pupil',turn*.008,0,.034,.054,0,INK,eye,lid=True)
            stroke(g,'Upper eyelid',(-.042,.043),(0,.054),(.046,.043),.003,.008,INK,eye)
            if sunglasses or who=='guard':
                poly(g,'Dark rectangular designer lens',[(ex-.102,.118),(ex-.092,.016),(ex+.089,.017),(ex+.104,.118)],.007,pigment(g,'201d2b'),f)
                stroke(g,'Glasses specular stripe',(ex-.060,.099),(ex-.015,.101),(.023+ex,.104),.008,.005,'706174',f)
            if who in ('oldman','oldlady'):
                g.curve('Round eyeglass frame',[(ex+.075*math.cos(i*math.tau/32),.073+.070*math.sin(i*math.tau/32),.005) for i in range(32)],.007,pigment(g,'977452'),f,True)
            yaw=.033 if expression in ('panic','cry','shock') else .009
            stroke(g,'Expressive brow',(ex-.052,.149-yaw*side),(ex,.167),(ex+.049,.149+yaw*side),.003,.012,hair if who not in ('oldlady','guard') else INK,f)
            if feminine:oval(g,'Painted cheek blush',ex*1.39,-.039,.062,.024,.002,'e6a1a0',f)
        if sunglasses or who in ('guard','oldman','oldlady'):stroke(g,'Eyewear bridge',(-.033,.070),(0,.082),(.033,.070),.009,.010,'514050',f)
        stroke(g,'Nose',(-.007,.025),(.046,-.022),(.002,-.040),.003,.008,'a9766e',f)
        self.mouth=g.link('Articulated mouth',p=f,xyz=(0,-.144,.004))
        mouth='a51c3f' if feminine else INK
        if expression in ('panic','cry','shock','bite'):
            oval(g,'Open mouth',0,0,.085,.064,0,mouth,self.mouth)
            oval(g,'Mouth tongue',0,-.031,.045,.018,.001,'d77d86',self.mouth)
        else:
            stroke(g,'Curved smile',(-.066,.008),(0,-.075),(.072,.013),0,.016 if feminine else .012,mouth,self.mouth)
            if feminine:stroke(g,'Ruby lower lip',(-.027,-.030),(0,-.054),(.040,-.024),.001,.007,'d74a61',self.mouth)
        # All garment shapes share one flat body plane, with the limb roots under the garment ink.
        garment=[(-.24,-.25),(-.30,.25),(-.23,.38),(-.10,.44),(.10,.44),(.25,.37),(.30,.22),(.24,-.25),(.16,-.31),(-.16,-.31)]
        if who=='bride':garment=[(-.37,-.68),(-.24,-.27),(-.28,.25),(-.18,.42),(.16,.42),(.28,.25),(.24,-.27),(.38,-.68)]
        if who=='lady':garment=[(-.25,-.31),(-.30,-.24),(-.29,-.14),(-.34,-.10),(-.32,.02),(-.36,.12),(-.34,.23),(-.37,.29),(-.33,.37),(-.25,.43),(-.18,.44),(-.11,.49),(.08,.49),(.17,.45),(.25,.45),(.34,.37),(.37,.29),(.34,.21),(.35,.11),(.31,.05),(.33,-.06),(.30,-.14),(.30,-.23),(.25,-.31),(.11,-.35),(-.12,-.34)]
        if who!='lady':
            oval(g,'Continuous neck under jaw',0,.435,.103,.134,-.057,INK,b)
            oval(g,'Neck lit pigment',0,.440,.079,.117,-.056,skin,b)
        for side in (-1,1):
            sh=(side*.245,.283);hand=(hands or ((-.37,-.14),(.37,-.14)))[int(side>0)]
            elbow=(side*(.43+max(0,abs(hand[0])-.43)*.45),(.27+hand[1])*.49-.088)
            stroke(g,'Curved sleeve and forearm ink',sh,elbow,hand,.004,.101 if who=='lady' else .063,INK,b)
            stroke(g,'Lit sleeve pigment',sh,elbow,hand,.005,.078 if who=='lady' else .044,shirt,b)
            oval(g,'Round dark mitten',*hand,.075,.069,.010,INK,b)
            foot=(side*(.29 if pose in ('sit','squat') else .154),-.30 if pose=='squat' else -.739)
            knee=(side*.25,-.27 if pose=='squat' else -.44 if pose=='sit' else -.50)
            stroke(g,'Curved leg ink',(side*.137,-.23),knee,foot,.003,.066,INK,b)
            stroke(g,'Trouser pigment',(side*.137,-.23),knee,foot,.004,.046,pants,b)
            self.feet.append(Vector((foot[0]+side*.025,foot[1]-.034,.009)))
            oval(g,'Rounded shoe',foot[0]+side*.025,foot[1],.103,.050,.009,'8c2448' if feminine else INK,b)
        clothing_start=set(b.children)
        poly(g,'Unified torso ink',garment,.008,pigment(g,INK),b)
        poly(g,'Cool fabric edge',[(x*.94,y*.95) for x,y in garment],.009,pigment(g,('b8a3ae' if feminine else '424357')),b)
        tall=who=='bride';form=(0,-.09,.40,.67) if tall else (0,.05,.35,.48)
        poly(g,'Lit clothing',[(x*.9+.004,y*.91+.009) for x,y in garment],.010,pigment(g,shirt),b,form)
        if outfit_rim and who in ('bride','groom','oldman','oldlady'):
            color={'bride':'fff5e6','groom':'677791','oldman':'edc2a0','oldlady':'efbcb5'}[who]
            stroke(g,'Dimensional garment rim',(-.268,.19),(-.232,.330),(-.13,.374),.011,.009,color,b)
            if tall:stroke(g,'Gown lower rim',(-.322,-.562),(-.233,-.347),(-.220,-.25),.011,.008,color,b)
        if who in ('groom','guard','waiter'):
            poly(g,'Ivory collar',[(-.125,.391),(0,-.085),(.128,.391),(.0,.329)],.011,pigment(g,'f7e8dc'),b)
            poly(g,'Silk necktie',[(-.037,.342),(.038,.342),(.039,.138),(0,.082),(-.039,.138)],.012,pigment(g,'ba3b57' if who=='groom' else '252235'),b)
        elif feminine:
            if who=='lady':
                for side in (-1,1):
                    for i in range(7):
                        x=side*(.086+i*.031);y=.247+i*.022
                        oval(g,'Soft scalloped fur collar',x,y,.068,.059,.013+i*.0001,('e4d9c9','fff8e7','eee8da')[i%3],b,True,(x,y,.087,.072))
                stroke(g,'Cream fur seam',(.014,.086),(.056,-.13),(.035,-.28),.015,.009,'d0c2ba',b)
            gems=g.mat('fff6eb',metal=.32,rough=.17)
            for j in range(-5,6):
                x=j*.027;y=.242+abs(j)*.024;s=.019 if j else .030
                poly(g,'White diamond V necklace',[(x-s,y),(x,y-s*1.28),(x+s,y),(x,y+s*1.08)],.025,gems,b,(x,y,s*1.2,s*1.35))
                poly(g,'White diamond facet',[(x-s*.65,y+.002),(x,y+s*.82),(x+s*.42,y+.002),(x,y-s*.21)],.026,pigment(g,'fffdf5'),b)
            if who=='bride':
                for s in (-1,1):
                    stroke(g,'Ivory gown fold',(s*.067,-.18),(s*.11,-.37),(s*.20,-.60),.011,.012,'ccb7c5',b)
        else:
            stroke(g,'Frayed jacket opening',(-.04,.345),(.015,.022),(-.025,-.24),.011,.015,'6f6156',b)
            for y in (.10,-.035,-.166):oval(g,'Jacket button',.061,y,.019,.022,.012,'463948',b)
        for obj in set(b.children)-clothing_start:
            obj.parent=self.chest;obj.location.y+=.25

    def aim(self,rotation,frame):
        for o in (self.head,self.body):
            o.rotation_mode='QUATERNION';o.rotation_quaternion=rotation;o.keyframe_insert(data_path='rotation_quaternion',frame=frame)
