"""Build and render the isolated seven-cut spa short in Blender 4.2."""
import json
import math
import random
import sys
import time
from pathlib import Path

import bpy
from mathutils import Matrix, Vector, Quaternion
sys.path.insert(0,str(Path(__file__).resolve().parent))
from timeline import BOUNDS as CUTS, FRAMES, STILLS, LAND

OUT = Path(__file__).resolve().parents[2] / 'renders' / 'spa_fart_twist'
SPR = OUT / 'sprites'
BLEND = OUT / 'spa_fart_twist_v2.blend'

def rgba(hexcolor):
    def linear(value):
        return value/12.92 if value<=.04045 else ((value+.055)/1.055)**2.4
    return (*(linear(int(hexcolor[i:i+2],16)/255) for i in (0,2,4)),1)

def mat(name,color,rough=.6,emission=0):
    m=bpy.data.materials.new(name);m.use_nodes=True
    shader=m.node_tree.nodes['Principled BSDF']
    shader.inputs['Base Color'].default_value=rgba(color)
    shader.inputs['Roughness'].default_value=rough
    shader.inputs['Emission Color'].default_value=rgba(color)
    shader.inputs['Emission Strength'].default_value=emission
    return m

def wood(name,a,b,rough=.34):
    m=mat(name,a,rough);n=m.node_tree.nodes;l=m.node_tree.links
    coord=n.new('ShaderNodeTexCoord');scale=n.new('ShaderNodeVectorMath')
    scale.operation='MULTIPLY';scale.inputs[1].default_value=(.4,20,7)
    noise=n.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=3
    ramp=n.new('ShaderNodeValToRGB')
    for element,pos,color in zip(ramp.color_ramp.elements,(.19,.81),(a,b)):
        element.position=pos;element.color=rgba(color)
    l.new(coord.outputs['Object'],scale.inputs[0]);l.new(scale.outputs[0],noise.inputs[0])
    l.new(noise.outputs['Fac'],ramp.inputs[0]);l.new(ramp.outputs[0],n['Principled BSDF'].inputs['Base Color'])
    return m

def finish(o,name,m):
    o.name=name
    if m:o.data.materials.append(m)
    return o

def box(name,loc,size,m,bevel=.025):
    bpy.ops.mesh.primitive_cube_add(size=1,location=loc)
    o=finish(bpy.context.object,name,m)
    o.data.transform(Matrix.Diagonal((*size,1)))
    if bevel:
        mod=o.modifiers.new('Rounded edges','BEVEL');mod.width=bevel;mod.segments=3
        o.modifiers.new('Corner normals','WEIGHTED_NORMAL')
    return o

def oval(name,loc,size,m):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=20,ring_count=12,radius=1,location=loc)
    o=finish(bpy.context.object,name,m);o.scale=size
    for p in o.data.polygons:p.use_smooth=True
    return o

def stem(name,a,b,r,m,taper=1):
    a,b=Vector(a),Vector(b)
    bpy.ops.mesh.primitive_cone_add(vertices=12,radius1=r,radius2=r*taper,depth=(b-a).length,location=(a+b)/2)
    o=finish(bpy.context.object,name,m);o.rotation_euler=(b-a).to_track_quat('Z','Y').to_euler()
    return o

def tube(name,m,r):
    data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=r;data.bevel_resolution=2
    data.use_fill_caps=True
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.data.materials.append(m)
    return o

def poly(o,points):
    spline=o.data.splines.new('POLY');spline.points.add(len(points)-1)
    for point,co in zip(spline.points,points):point.co=(*co,1)
    return spline

def area(name,loc,target,energy,size,color):
    data=bpy.data.lights.new(name,'AREA');data.energy=energy;data.size=size;data.color=rgba(color)[:3]
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.location=loc
    o.rotation_euler=(Vector(target)-o.location).to_track_quat('-Z','Y').to_euler()

def spa():
    oak=wood('Honey oak grain','815027','cc9254',.22)
    cedar=wood('Oiled cedar','593018','a96533')
    walnut=wood('Table walnut','432718','926139')
    ivory=mat('Warm leather','f4f1ea',.48)
    white=mat('White spa linen','fffaf2',.85)
    stitching=mat('Leather welt','b8a694')
    paper=mat('Glowing rice paper','f5ebd6',.75,.26)
    wax=mat('Beeswax','ffeeaf',.62)
    flame=mat('Amber flame','ffaa33',.45,5)
    core=mat('Candle core','ffeccd',.5,8)
    dark=mat('Bronze lantern','422919',.45)
    terra=mat('Hand thrown ochre ceramic','9b7054',.37)
    earth=mat('Potting soil','35251b')
    leaves=[mat('Bamboo leaf '+c,c,.55,.025) for c in ('547445','668944','8c9a4b')]
    bamboo=mat('Bamboo stems','6e783b')
    box('Floor under plank joints',(0,0,-.06),(13,11,.11),walnut)
    for i in range(34):
        offset=1.6*(i%2)
        for j in range(-2,3):
            box('Honey oak plank',(j*3.18+offset,i*.29-4.9,-.015),(3.17,.282,.055),oak,.006)
    for side in (-1,1):
        y=side*2.8
        box('Cedar wall',(0,y,2.3),(10,.12,4.6),cedar)
        for i in range(32):
            x=i*.30-4.65
            box('Cedar slat',(x,y-side*.075,1.75),(.275,.12,3.4),cedar,.01)
        box('Low skirting',(0,y-side*.14,.11),(10,.1,.21),walnut)
        for x in (-3.9,-.75,2.3,4.5):
            box('Structural timber',(x,y-side*.18,1.75),(.15,.19,3.5),walnut)
        box('Ceiling beam',(0,y-side*.24,3.19),(10,.27,.21),walnut)
        for i in range(12):
            box('Upper cedar panel',(i*.83-4.56,y-side*.075,3.91),(.80,.12,1.39),cedar,.012)
        sx=2.30 if side==1 else -1.82
        sy=y-side*.27
        box('Shoji paper',(sx,sy,1.66),(1.95,.07,2.52),paper)
        for i in range(7):
            box('Shoji mullion',(sx+(i-3)*.325,sy-side*.065,1.66),(.042,.045,2.58),walnut,.006)
        for i in range(9):
            box('Shoji crossbar',(sx,sy-side*.07,.41+i*.314),(2.01,.05,.043),walnut,.006)
    # The north wall is seen in front shots. The south wall is a rear-shot backing.
    for x in (-4.6,4.6):
        box('Return cedar wall',(x,0,1.7),(.11,5.7,3.4),cedar)
    def candle(x,y,z,h):
        stem('Pillar candle',(x,y,z),(x,y,z+h),.041+h*.13,wax)
        oval('Wax lip',(x,y,z+h),(.049+h*.13,.049+h*.13,.008),wax)
        stem('Wick',(x,y,z+h),(x,y,z+h+.038),.006,dark)
        oval('Candle flame',(x+.008,y,z+h+.058),(.023,.023,.056),flame)
        oval('Flame center',(x+.002,y-.006,z+h+.035),(.010,.011,.023),core)
    rng=random.Random(343)
    for y,x in [(2.29,-2.22),(2.28,1.04),(-2.33,1.48)]:
        for z in (.49,1.22,2.02):
            box('Candle shelf',(x,y,z),(1.24,.47,.09),walnut)
            for i in range(3):
                candle(x-.48+i*.41,y+(.03 if i%2 else -.1),z+.045,rng.uniform(.13,.26))
            for dx in (-.49,.49): box('Shelf bracket',(x+dx,y+.03,z-.10),(.07,.30,.18),walnut)
    for x,y in [(-2.06,1.48),(1.99,1.85),(1.93,-1.72),(-2.18,-1.27),(2.7,.43)]:
        box('Lantern base',(x,y,.08),(.26,.26,.10),dark)
        box('Lantern paper',(x,y,.25),(.19,.19,.28),paper)
        box('Lantern cap',(x,y,.42),(.26,.26,.07),dark)
        for dx in (-.101,.101):
            for dy in (-.101,.101):box('Lantern corner',(x+dx,y+dy,.25),(.025,.025,.32),dark,.007)
    for x,y in [(-3.10,1.65),(.05,2.30),(2.87,1.68),(-2.95,-1.9),(2.77,-2.0)]:
        first=set(bpy.context.collection.objects)
        stem('Ceramic planter',(x,y,.015),(x,y,.43),.22,terra,1.33)
        oval('Planter soil',(x,y,.426),(.278,.278,.032),earth)
        for j in range(6):
            a=Vector((x+rng.uniform(-.16,.16),y+rng.uniform(-.15,.15),.43))
            b=Vector((a.x+rng.uniform(-.34,.34),a.y+rng.uniform(-.15,.15),rng.uniform(1.70,2.94)))
            stem('Bamboo cane',a,b,.014,bamboo,.58)
            for k in range(5):
                q=a.lerp(b,.35+k*.145)
                direction=(-1)**(j+k)
                end=q+Vector((direction*rng.uniform(.13,.35),rng.uniform(-.17,.17),.16))
                stem('Leaf twig',q,end,.006,bamboo,.3)
                for index in range(3):
                    p=q.lerp(end,.25+index*.32);v=Vector((direction*.13,(-1)**index*.11,-.057))
                    leaf=oval('Lanceolate bamboo leaf',p+v/2,(.026,.008,.112),rng.choice(leaves))
                    leaf.rotation_euler=v.to_track_quat('Z','Y').to_euler()
        for o in set(bpy.context.collection.objects)-first:
            o['bamboo_side']=1 if y>0 else -1
    box('Table apron',(0,0,.89),(2.74,1.21,.18),walnut,.05)
    for x in (-1.23,1.23):
        for y in (-.48,.48):
            box('Tapered oak massage table leg',(x,y,.465),(.13,.13,.92),oak,.022)
        stem('Table end cross brace',(x,-.53,.29),(x,.53,.29),.048,walnut)
        for y in (-.48,.48):
            stem('Table diagonal brace',(x,y,.39),(x*.65,y,.84),.039,walnut)
    for y in (-.48,.48):
        box('Long wood stretcher',(0,y,.31),(2.55,.095,.10),walnut)
    for i in range(12):box('Slatted linen rack',(-1.12+i*.20,0,.34),(.157,.89,.034),cedar,.006)
    box('Mattress piping',(0,0,1.015),(2.78,1.26,.07),stitching,.03)
    box('Padded ivory mattress',(0,0,1.095),(2.81,1.29,.19),ivory,.09)
    bpy.ops.mesh.primitive_torus_add(major_segments=40,minor_segments=12,major_radius=.215,minor_radius=.082,
                                   location=(-1.55,0,1.15))
    pillow=finish(bpy.context.object,'Padded round face cradle',ivory);pillow.scale=(1.05,1,.72)
    stem('Cradle bracket',(-1.62,0,1.06),(-1.17,0,1.02),.043,walnut)
    # A draped continuous towel runs over the waist and folds over the table edge.
    verts=[];faces=[]
    for i in range(13):
        t=i/12;y=-.73+t*1.14
        for j in range(13):
            s=j/12;x=.31+.79*s+.024*math.sin(t*15+s*8)
            z=1.208+.143*math.exp(-((y+.04)/.33)**2)+.011*math.cos(s*33+t*9)
            z-=.30*max(0,(-y-.47)/.26)**1.55
            verts.append((x,y,z))
    for i in range(12):
        for j in range(12):
            a=i*13+j;faces.append((a,a+1,a+14,a+13))
    mesh=bpy.data.meshes.new('Towel fold topology');mesh.from_pydata(verts,[],faces);mesh.update()
    towel=bpy.data.objects.new('White waist towel',mesh);bpy.context.collection.objects.link(towel);mesh.materials.append(white)
    for p in mesh.polygons:p.use_smooth=True
    thick=towel.modifiers.new('Linen thickness','SOLIDIFY');thick.thickness=.014
    area('Warm Amber Key',(-1.5,-2.1,3.65),(0,0,.9),180,3,'ffd0a4')
    area('Golden Candle Fill',(1.6,1.45,2.95),(0,0,1.05),110,2.8,'ffd298')
    area('Soft Overhead Fill',(.05,0,3.95),(0,0,0),90,2.7,'ffeddb')
    area('Shoji lantern bounce',(-1.8,2.2,1.95),(-1,1.8,1.2),30,2.1,'ffc279')

def key(o,path,frame,value):
    setattr(o,path,value);o.keyframe_insert(data_path=path,frame=frame)

def tex_mat(name,blend=False):
    m=bpy.data.materials.new(name);m.use_nodes=True
    m.surface_render_method='BLENDED' if blend else 'DITHERED'
    nt=m.node_tree;nt.nodes.clear();n=nt.nodes;l=nt.links
    img=n.new('ShaderNodeTexImage');img.image=bpy.data.images.load(str(SPR/(name+'.png')),check_existing=True)
    bs=n.new('ShaderNodeBsdfPrincipled');bs.inputs['Roughness'].default_value=1;bs.inputs['Specular IOR Level'].default_value=0
    em=n.new('ShaderNodeEmission');em.inputs['Strength'].default_value=.96
    for node,slot in ((bs,'Base Color'),(em,'Color')):l.new(img.outputs['Color'],node.inputs[slot])
    color=n.new('ShaderNodeMixShader');color.inputs[0].default_value=.74
    l.new(bs.outputs[0],color.inputs[1]);l.new(em.outputs[0],color.inputs[2])
    alpha=n.new('ShaderNodeMixShader');transparent=n.new('ShaderNodeBsdfTransparent')
    l.new(img.outputs['Alpha'],alpha.inputs[0]);l.new(transparent.outputs[0],alpha.inputs[1]);l.new(color.outputs[0],alpha.inputs[2])
    out=n.new('ShaderNodeOutputMaterial');l.new(alpha.outputs[0],out.inputs[0])
    return m

def pivot(name):
    o=bpy.data.objects.new(name,None);bpy.context.collection.objects.link(o);o.rotation_mode='QUATERNION';return o

def image_card(name,asset,parent,size,offset=(0,0,0),blend=False):
    bpy.ops.mesh.primitive_plane_add(size=1)
    o=finish(bpy.context.object,name,tex_mat(asset,blend));o.parent=parent;o.location=offset
    o.scale=(*size,1)
    return o

def swap(o,f,visible):
    key(o,'hide_render',f,not visible)

def bone_curve(name,m,radius):
    o=tube(name,m,radius)
    s=o.data.splines.new('BEZIER');s.bezier_points.add(2)
    for p in s.bezier_points:p.handle_left_type='FREE';p.handle_right_type='FREE'
    if hasattr(o,'visible_shadow'):o.visible_shadow=False
    # Thin ink strokes are line art. Keep them from casting long black streaks.
    o.data.materials[0].surface_render_method='BLENDED'
    return o

def arm_curve(o,f,points):
    a,b,c=map(Vector,points)
    incoming=b-a;outgoing=c-b
    tangent=(incoming.normalized()+outgoing.normalized()).normalized()
    middle=min(incoming.length,outgoing.length)*.23
    for p,co,left,right in zip(o.data.splines[0].bezier_points,(a,b,c),
            (a-incoming*.25,b-tangent*middle,c-outgoing*.25),
            (a+incoming*.25,b+tangent*middle,c+outgoing*.25)):
        p.co,p.handle_left,p.handle_right=co,left,right
        for channel in ('co','handle_left','handle_right'):p.keyframe_insert(channel,frame=f)

def compact_arm(shoulder,target,pole):
    axis=(Vector(target)-shoulder)
    reach=min(.498,max(.02,axis.length))
    axis=axis.normalized()
    outward=Vector(pole)-axis*axis.dot(Vector(pole))
    if outward.length<.001:outward=axis.cross(Vector((0,1,0)))
    hand=shoulder+axis*reach
    elbow=shoulder+axis*(reach/2)+outward.normalized()*math.sqrt(.25**2-(reach/2)**2)
    assert abs((elbow-shoulder).length-.25)<1e-5 and abs((hand-elbow).length-.25)<1e-5
    return elbow,hand

def words(text,loc,scale,m):
    data=bpy.data.curves.new('Drawn reaction','FONT');data.body=text;data.align_x='CENTER'
    data.size=scale;data.extrude=.002
    o=bpy.data.objects.new(text,data);bpy.context.collection.objects.link(o)
    data.materials.append(m);o.location=loc;o.rotation_mode='QUATERNION'
    return o

def smoother(x):
    x=max(0,min(1,x))
    return x*x*(3-2*x)

def ribbon_material():
    m=bpy.data.materials.new('Soft tapered green vapor');m.use_nodes=True;m.surface_render_method='BLENDED'
    nt=m.node_tree;n=nt.nodes;n.clear();l=nt.links
    attr=n.new('ShaderNodeAttribute');attr.attribute_name='ribbon_alpha'
    amp=n.new('ShaderNodeMath');amp.operation='MULTIPLY';amp.inputs[1].default_value=.56
    em=n.new('ShaderNodeEmission');em.inputs[0].default_value=rgba('b8de64');em.inputs[1].default_value=.78
    tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');out=n.new('ShaderNodeOutputMaterial')
    l.new(attr.outputs['Fac'],amp.inputs[0]);l.new(amp.outputs[0],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
    return m,amp

def ribbon(name,material,seed):
    verts=[];faces=[];alpha=[]
    for i in range(25):
        t=i/24;mid=.062*math.sin(t*12+seed);w=.042*math.sin(math.pi*t)
        for j in range(5):
            side=j/2-1
            verts.append((mid+side*w,0,t*.70))
            alpha.append((1-t)**.55*min(1,t*12)*(1-abs(side)**2))
    for i in range(24):
        for j in range(4):
            a=i*5+j;faces.append((a,a+1,a+6,a+5))
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    attrib=data.attributes.new('ribbon_alpha','FLOAT','POINT')
    for i,value in enumerate(alpha):attrib.data[i].value=value
    o=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(o);o.data.materials.append(material)
    return o

def characters(sc):
    camera=bpy.data.objects.new('Six shot camera',bpy.data.cameras.new('Vertical camera'))
    bpy.context.collection.objects.link(camera);sc.camera=camera;camera.rotation_mode='QUATERNION'
    camera.data.sensor_fit='VERTICAL';camera.data.sensor_height=36
    camera.data.dof.use_dof=True;camera.data.dof.aperture_fstop=2.4
    ink=mat('Matte ink','161219',.95,.17)
    ink.node_tree.nodes['Principled BSDF'].inputs['Specular IOR Level'].default_value=0
    peach=mat('Warm mitten','f7d7b5',.95,.19)
    brown=mat('Sculpted brown coil','422810',.53)
    titles=mat('Painted cream reaction glyph','fff2cf',.9,.85)
    mhead=pivot('Masseur head camera billboard');chead=pivot('Client head camera billboard')
    mbody=pivot('Connected tunic and trousers');cbody=pivot('Prone body cel')
    chead.parent=cbody
    mfaces={};cfaces={}
    pose_sets=(('m',mhead,('zen','shock','talk','startled','rear','calm'),mfaces,1.04),
               ('c',chead,('peace','shock','skeptic','angry','horror','dizzy'),cfaces,1.03))
    for actor,parent,poses,faces,size in pose_sets:
        for pose in poses:
            for mouth in (range(4) if pose in ('talk','angry','calm') else (0,)):
                obj=image_card(actor+' '+pose+str(mouth),f'{actor}_{pose}_{mouth}',parent,(size,size),(0,.047,0))
                faces[pose,mouth]=obj
    scrub=[image_card('Tunic '+side,'scrub_'+side,mbody,(.91,.84),(0,.057,.026)) for side in ('front','back')]
    pants=[image_card(name,name,mbody,(.80,1.58),(0,-.86,0)) for name in ('pants','pants_stain')]
    image_card('Prone shirtless torso','client_body',cbody,(1.51,.79))
    neck=oval('Masseur neck',(0,0,0),(.084,.034,.082),peach)
    feet=[oval('Masseur grounded shoe',(0,0,.045),(.093,.12,.044),ink) for _ in range(2)]
    arms=[[bone_curve(actor+' arm '+str(i+1),ink,.023 if actor=='Masseur' else .027) for i in range(2)] for actor in ('Masseur','Client')]
    hands=[[oval(actor+' black mitten '+str(i+1),(0,0,0),(.032,.032,.032),ink) for i in range(2)] for actor in ('Masseur','Client')]
    sweat_root=pivot('Temple sweat anchor');sweat=image_card('Attached sweat','sweat',sweat_root,(.22,.22),blend=True)
    soul_root=pivot('Rising blue soul');soul=image_card('Blue ghost','soul',soul_root,(.65,.65),blend=True)
    puffs=[]
    for i in range(6):
        root=pivot(f'Waist puff {i+1}')
        puffs.append((root,image_card(f'Soft cloud lobe {i+1}','puff',root,(.48,.48),blend=True)))
    mark=words('!!',(0,0,0),.24,titles);question=words('?',(0,0,0),.24,titles)
    coils=[]
    for i,(radius,thickness,z) in enumerate(((.133,.047,.055),(.102,.041,.126),(.064,.035,.189))):
        o=tube('Mound coil '+str(i+1),brown,thickness)
        poly(o,[(radius*math.cos(t*math.tau/70),radius*.80*math.sin(t*math.tau/70),z) for t in range(71)]);coils.append(o)
    coils.append(oval('Mound tip',(.027,0,.225),(.039,.040,.045),brown))
    mound=pivot('Mound floor impact');mound.location=(.12,1.08,.013)
    for obj in coils:obj.parent=mound
    snake=tube('Cuff drop spiral',brown,.043)
    poly(snake,[(.054*math.sin(i*.35),.051*math.cos(i*.35),i*.008) for i in range(64)])
    ribbons=[];ribbon_mat,ribbon_alpha=ribbon_material()
    for i in range(4):ribbons.append(ribbon('Vapor ribbon '+str(i+1),ribbon_mat,i*1.8))
    envelope=json.loads((OUT/'mouth_envelope_v2.json').read_text())
    # Short lenses / pulled-back axes protect the portrait crop and table contact.
    shots=[
        ((-1.94,-4.15,2.57),(-.63,.08,1.36),33),
        ((-1.42,-4.11,2.28),(-.48,.07,1.47),34),
        ((-1.59,-3.86,1.98),(-.59,.08,1.64),32),
        ((-1.89,-3.54,1.27),(-.56,.04,1.58),34),
        ((.12,4.45,1.61),(-.41,.30,1.15),29),
        ((-.38,-4.64,2.12),(-.56,.04,1.56),33),
    ]
    previous=[None,None]
    for f in range(1,FRAMES+1):
        cut=next(i for i in range(len(shots)) if CUTS[i]<=f<CUTS[i+1])
        age=f-CUTS[cut];u=age/max(1,CUTS[cut+1]-CUTS[cut]-1)
        rear=cut==4
        cam,target,lens=shots[cut];cam,target=Vector(cam),Vector(target)
        # Cut-local wall visibility allows an orthogonal reverse in the same set.
        if f==CUTS[cut]:
            for ob in bpy.data.objects:
                if ob.type!='MESH' or ob.name.startswith(('Masseur','Client')):continue
                x,y,z=ob.location
                if ob.get('bamboo_side'):
                    swap(ob,f,(ob['bamboo_side']>0)!=rear)
                elif abs(y)>2.1 and (abs(y)>2.5 or ob.name.startswith(('Shoji','Structural timber','Low skirting','Cedar','Ceiling','Candle shelf','Pillar candle','Wax lip','Wick','Candle flame','Flame center','Shelf bracket'))):
                    swap(ob,f,(y>0)!=rear)
        jolt=.042*math.sin((f-62)*1.8)*(1-(f-62)/5) if cut==1 and 62<=f<67 else 0
        cam=cam.lerp(target,.10*smoother(u))+Vector((jolt,0,jolt*.68))
        q=(target-cam).to_track_quat('-Z','Y');right=q@Vector((1,0,0));up=q@Vector((0,1,0));front=q@Vector((0,0,1))
        key(camera,'location',f,cam);key(camera,'rotation_quaternion',f,q);key(camera.data,'lens',f,lens)
        mbase=Vector((.12,1.03 if rear else .32,1.13))
        if cut==3:mbase+=Vector((.085*smoother(age/13),.08*smoother(age/13),.015))
        mtorso=mbase+Vector((0,0,.36))
        # Keep trousers upright to the floor; only the heads use the full tilt.
        body_q=Quaternion((0,0,1),math.pi if rear else 0)@Quaternion((1,0,0),math.pi/2)
        key(mbody,'location',f,mtorso);key(mbody,'rotation_quaternion',f,body_q)
        mh=mbase+Vector((0,0,.88));key(mhead,'location',f,mh+front*.061);key(mhead,'rotation_quaternion',f,q)
        key(neck,'location',f,mbase+Vector((0,-.008,.61)))
        for i,foot in enumerate(feet):key(foot,'location',f,(mbase.x+(-1 if i==0 else 1)*.175,mbase.y+(.04 if rear else -.046),.043))
        raise_fraction=1-(1-min(1,age/10))**3 if cut==3 else .21 if rear else 0
        lift_q=Quaternion((0,1,0),math.radians(24)*raise_fraction)
        hinge=Vector((.18,-.15,1.35))
        body=hinge+lift_q@Vector((-.69,0,-.013))
        chest_q=lift_q@body_q
        key(cbody,'location',f,body);key(cbody,'rotation_quaternion',f,chest_q)
        ch=body+lift_q@Vector((-.80,-.007,.069))
        roll=math.radians((-20+24*raise_fraction) if cut==3 else -18 if cut in (0,2,5) else -11)
        key(chead,'location',f,chest_q.inverted()@(ch+front*.105-body))
        key(chead,'rotation_quaternion',f,chest_q.inverted()@q@Quaternion((0,0,1),roll))
        focal=(mh+ch)*.5 if not rear else Vector((-.35,.53,1.25))
        key(camera.data.dof,'focus_distance',f,(focal-cam).dot(-front))
        slot=min(FRAMES-1,CUTS[cut]-1+age//3*3)
        level=max(envelope[slot:min(slot+3,FRAMES)])
        mouth=0 if level<.11 else min(3,1+int(level*2.6))
        active=[(('zen','shock','talk','startled','rear','calm')[cut],mouth if cut in (2,5) else 0),
                (('peace','shock','skeptic','angry','horror','dizzy')[cut],mouth if cut==3 else 0)]
        for i,faces in enumerate((mfaces,cfaces)):
            if active[i]!=previous[i]:
                if previous[i] is not None:swap(faces[previous[i]],f,False)
                else:
                    for o in faces.values():swap(o,f,False)
                swap(faces[active[i]],f,True);previous[i]=active[i]
        if f==CUTS[cut]:
            for i,o in enumerate(scrub):swap(o,f,i==int(rear))
        for i,o in enumerate(pants):swap(o,f,i==int(rear and f>=LAND))
        for i,side in enumerate((-1,1)):
            shoulder=mtorso+Vector((side*.225,.022 if rear else -.11,.13))
            cshoulder=body+lift_q@Vector((-.41+.10*i,side*.064,.03))
            if cut==0:
                press=(.5-.5*math.cos(age*math.tau/28+i*.49))*max(0,1-age/63)
                hand=Vector((-.30+i*.51,-.112+i*.018,1.464-.022*press))
                chand=Vector((-.93+i*.46,side*.69,.89));celbow=Vector((-.97+i*.37,side*.67,1.22))
            elif cut==1:
                hand=Vector((-.32+i*.40,-.03+i*.04,1.53))
                chand=Vector((-.95+i*.39,side*.61,1.21));celbow=Vector((-.84+i*.32,side*.61,1.29))
            elif cut==2:
                if i==0:
                    hand=Vector((-.42,-.08,1.461+.064*(1-math.cos(age*.30))*max(0,1-age/55)))
                else:
                    hand=shoulder+Vector((.245,-.11,.27))
                chand=Vector((-.92+i*.42,side*.65,.97));celbow=Vector((-.92+i*.36,side*.64,1.24))
            elif cut==3:
                hand=shoulder+Vector((side*.30,-.16,-.14+i*.10))
                if i==0:
                    chand=Vector((-.95,-.46,1.224));celbow=Vector((-.81,-.41,1.245))
                else:
                    cshoulder=body+lift_q@Vector((-.35,-.10,.074))
                    chand=Vector((-.49,-.31,1.39)).lerp(mh-right*.53+up*.13+front*.26,raise_fraction)
                    celbow=cshoulder.lerp(chand,.48)+Vector((.16,-.18,-.10))
            elif rear:
                hand=shoulder+Vector((side*.20,.07,-.31))
                chand=ch+right*(side*.329)+up*.069+front*.14
                celbow=ch+right*(side*.425)-up*.099+front*.145
                cshoulder=ch+right*(side*.235)-up*.29+front*.126
            else:
                hand=shoulder+Vector((side*.33,-.14,.106))
                chand=Vector((-.97+i*.59,side*.69,.79));celbow=Vector((-.87+i*.47,side*.68,1.21))
            elbow,hand=compact_arm(shoulder,hand,(side*.62,-.28,-.47))
            for actor,(start,bend,end) in enumerate(((shoulder,elbow,hand),(cshoulder,celbow,chand))):
                arm_curve(arms[actor][i],f,(start,bend,end));key(hands[actor][i],'location',f,end)
                assert (start-end).length<1.45, (actor,f,start,end)
        for o in (sweat_root,soul_root):key(o,'rotation_quaternion',f,q)
        key(sweat_root,'location',f,ch+right*.259+up*.122+front*.101)
        swap(sweat,f,cut in (1,3))
        soul_u=smoother((age-5)/57) if cut==5 else 0
        key(soul_root,'location',f,ch+right*(-.06+.045*math.sin(age*.16))+
            up*(.32+.54*soul_u+.025*math.sin(age*.18))+front*.05)
        key(soul_root,'scale',f,(.36+.92*soul_u,)*3);swap(soul,f,cut==5 and age>=5)
        for i,(root,puff) in enumerate(puffs):
            cloud=smoother((f-62-i)/19);fade=smoother((116-f)/14)
            key(root,'rotation_quaternion',f,q)
            key(root,'location',f,Vector((.38+(i%3)*.123-.09*cloud,-.28-.09*(i//3),1.42+.15*(i//3)+.10*cloud)))
            key(root,'scale',f,(max(.01,fade*(.35+.88*cloud)),)*3)
            swap(puff,f,cut==1 and 62+i<=f<=115)
        for o,visible in ((mark,cut==1),(question,cut==2)):
            swap(o,f,visible);key(o,'location',f,ch+right*(-.31 if o==mark else -.33)+up*.33+front*.087)
            key(o,'rotation_quaternion',f,q@Quaternion((0,0,1),.20))
        for o in coils:swap(o,f,rear and f>=LAND)
        drop=smoother((f-326)/(LAND-326))
        key(snake,'location',f,(.295-.175*drop,1.08,.20-.144*drop))
        key(snake,'scale',f,(.79+.21*drop,.79+.21*drop,.12+.27*drop));swap(snake,f,rear and 326<=f<LAND)
        bounce={LAND:(1.21,1.16,.63),LAND+2:(.96,.96,1.13),LAND+6:(1,1,1)}
        if f in bounce:key(mound,'scale',f,bounce[f])
        vapor_age=f-LAND if rear else age
        ribbon_alpha.inputs[1].default_value=.56*smoother((vapor_age+3)/12) if rear or cut==5 else 0
        ribbon_alpha.inputs[1].keyframe_insert('default_value',frame=f)
        for i,o in enumerate(ribbons):
            swap(o,f,(rear and f>=LAND and i<3) or cut==5)
            x=.02+i*.113 if rear else -.87+i*.33
            key(o,'location',f,(x+.031*math.sin(age*.14+i),1.18 if rear else -.74,.20+.09*math.sin(age*.11+i)))
            key(o,'rotation_euler',f,(0,0,math.pi if rear else 0))
            key(o,'scale',f,(1,1,(.53 if rear else 1.13)+.12*math.sin(age*.12+i)))
    for action in bpy.data.actions:
        for curve in action.fcurves:
            mode='CONSTANT' if curve.data_path=='hide_render' or curve.data_path=='lens' else 'LINEAR'
            for k in curve.keyframe_points:k.interpolation=mode

def setup():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc=bpy.context.scene
    sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.use_raytracing=False
    if hasattr(sc.eevee,'use_fast_gi'):
        sc.eevee.use_fast_gi=True
    elif hasattr(sc.eevee,'use_fast_gi_approximation'):
        sc.eevee.use_fast_gi_approximation=True
    sc.render.use_simplify=True;sc.render.simplify_subdivision=2
    sc.render.resolution_x=1080;sc.render.resolution_y=1920;sc.render.fps=30
    sc.frame_start=1;sc.frame_end=FRAMES;sc.eevee.taa_render_samples=24
    sc.render.image_settings.file_format='PNG';sc.render.image_settings.compression=5
    sc.view_settings.view_transform='AgX';sc.view_settings.look='AgX - Medium High Contrast'
    world=bpy.data.worlds.new('Warm ambient bounce');sc.world=world;world.use_nodes=True
    bg=world.node_tree.nodes['Background'];bg.inputs['Color'].default_value=rgba('d0a57d');bg.inputs['Strength'].default_value=.28
    sc.use_nodes=True;nt=sc.node_tree;nt.nodes.clear()
    source=nt.nodes.new('CompositorNodeRLayers')
    bloom=nt.nodes.new('CompositorNodeGlare');bloom.glare_type='FOG_GLOW';bloom.threshold=.80;bloom.mix=.20
    hsv=nt.nodes.new('CompositorNodeHueSat');hsv.inputs['Saturation'].default_value=1.15
    vignette=nt.nodes.new('CompositorNodeEllipseMask');vignette.width=.86;vignette.height=.90
    blur=nt.nodes.new('CompositorNodeBlur');blur.filter_type='FAST_GAUSS';blur.use_relative=True;blur.factor_x=29;blur.factor_y=25
    mix=nt.nodes.new('CompositorNodeMixRGB');mix.blend_type='MULTIPLY';mix.inputs[0].default_value=.15
    out=nt.nodes.new('CompositorNodeComposite')
    for a,b in [(source.outputs['Image'],bloom.inputs['Image']),(bloom.outputs[0],hsv.inputs['Image']),
                (vignette.outputs[0],blur.inputs[0]),(blur.outputs[0],mix.inputs[2]),(hsv.outputs[0],mix.inputs[1]),(mix.outputs[0],out.inputs[0])]:nt.links.new(a,b)
    return sc

def build():
    sc=setup()
    spa()
    print(f'BUILD staging and baking {FRAMES} frames',flush=True)
    characters(sc)
    sc.frame_set(30)
    bpy.ops.file.pack_all()
    bpy.ops.wm.save_as_mainfile(filepath=str(BLEND))

def render(phase):
    bpy.ops.wm.open_mainfile(filepath=str(BLEND))
    sc=bpy.context.scene
    folder=OUT/('stills_v2' if phase=='sheet' else 'frames_v2');folder.mkdir(exist_ok=True)
    sc.render.resolution_percentage=50 if phase=='sheet' else 100
    sc.eevee.taa_render_samples=16 if phase=='sheet' else 24
    frames=STILLS if phase=='sheet' else range(1,FRAMES+1)
    start=time.monotonic()
    for f in frames:
        target=folder/f'f{f:04}.png'
        sc.frame_set(f);sc.render.filepath=str(target)
        bpy.ops.render.render(write_still=True)
        if phase=='sheet' or f%15==0:
            print(f'BUILD {phase} frame {f} elapsed {time.monotonic()-start:.1f}s',flush=True)

if __name__=='__main__':
    phase=sys.argv[sys.argv.index('--')+1]
    build() if phase=='build' else render(phase)
