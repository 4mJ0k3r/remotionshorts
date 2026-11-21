"""Build the Blender master and bake the 42-cut calibration timeline."""
import json
import math
import random
import sys
from pathlib import Path

import bpy
from mathutils import Quaternion, Vector

HERE = Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
from sets import Stage, rgb, street, restaurant, paris, wedding, porch, cloth, silk_frame, textured
from cast import Actor, support_shadow
from shots import CAMERAS, DISSOLVE_CUTS, DISSOLVE_LENGTH, WHIP_CUTS, cast_specs
from polish import SUN_POSITION, actor_shadow, camera_rotation, setup_world, stage_shadows

OUT = HERE.parents[1] / 'renders' / HERE.name
CUTS = json.loads((HERE/'cuts.json').read_text(encoding='utf-8'))
V = Vector


def key(obj, frame, *paths):
    for path in paths:obj.keyframe_insert(data_path=path,frame=frame)


def appear(obj, start, end):
    obj.scale=(.00001,)*3;key(obj,max(0,start-1),'scale')
    obj.scale=(1,)*3;key(obj,start,'scale');key(obj,end,'scale')
    obj.scale=(.00001,)*3;key(obj,end+1,'scale')
    for k in obj.animation_data.action.fcurves[0].keyframe_points:k.interpolation='CONSTANT'
    for fc in obj.animation_data.action.fcurves[1:]:
        for k in fc.keyframe_points:k.interpolation='CONSTANT'


def particle_ribbons(g,r,p,length=1.0):
    objects=[]
    for i in range(3):
        mat=bpy.data.materials.get('Translucent olive wisps')
        if not mat:
            mat=bpy.data.materials.new('Translucent olive wisps');mat.use_nodes=True;mat.surface_render_method='BLENDED'
            n,l=mat.node_tree.nodes,mat.node_tree.links;n.clear();out=n.new('ShaderNodeOutputMaterial');mix=n.new('ShaderNodeMixShader');t=n.new('ShaderNodeBsdfTransparent');em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(*rgb('8aa54e'),1);em.inputs[1].default_value=.65
            uv=n.new('ShaderNodeTexCoord');sep=n.new('ShaderNodeSeparateXYZ');l.new(uv.outputs['UV'],sep.inputs[0])
            falloff=n.new('ShaderNodeValToRGB');falloff.color_ramp.interpolation='EASE';l.new(sep.outputs['X'],falloff.inputs[0])
            for end in falloff.color_ramp.elements:end.color=(0,0,0,1)
            falloff.color_ramp.elements.new(.5).color=(.38,.38,.38,1)
            fade=n.new('ShaderNodeValToRGB');fade.color_ramp.interpolation='EASE';l.new(sep.outputs['Y'],fade.inputs[0])
            for end in fade.color_ramp.elements:end.color=(0,0,0,1)
            fade.color_ramp.elements.new(.3).color=(1,1,1,1)
            alpha=n.new('ShaderNodeMath');alpha.operation='MULTIPLY';l.new(falloff.outputs[0],alpha.inputs[0]);l.new(fade.outputs[0],alpha.inputs[1])
            l.new(alpha.outputs[0],mix.inputs[0]);l.new(t.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);l.new(mix.outputs[0],out.inputs[0])
        mesh=bpy.data.meshes.new('Tapered wisp');points=[];faces=[]
        for j in range(29):
            t=j/28;x=length*.078*math.sin(t*11+i*1.8);w=length*.033*math.sin(math.pi*t)
            points.extend(((x-w,0,t*length),(x+w,0,t*length)))
            if j:faces.append((j*2-2,j*2-1,j*2+1,j*2))
        mesh.from_pydata(points,[],faces);mesh.materials.append(mat)
        uv_layer=mesh.uv_layers.new()
        for loop in mesh.loops:uv_layer.data[loop.index].uv=(loop.vertex_index%2,(loop.vertex_index//2)/28)
        objects.append(g.link('Depth-aware odor ribbon',mesh,r,(p[0]+(i-1)*.27*length,p[1]+.028*i,p[2]+.07*i)))
    return objects


def heart(g,r,loc,scale):
    mesh=bpy.data.meshes.new('Puffy closed heart')
    count=56
    outline=[(scale*math.sin(a)**3,scale*(13*math.cos(a)-5*math.cos(2*a)-2*math.cos(3*a)-math.cos(4*a))/16) for a in (i*math.tau/count for i in range(count))]
    rings=[(.33,-.31),(.68,-.24),(.92,-.13),(1,0),(.92,.13),(.68,.24),(.33,.31)]
    points=[(x*rad,y*scale,z*rad) for rad,y in rings for x,z in outline]
    faces=[(i*count+j,i*count+(j+1)%count,(i+1)*count+(j+1)%count,(i+1)*count+j) for i in range(len(rings)-1) for j in range(count)]
    faces.extend((tuple(reversed(range(count))),tuple(range((len(rings)-1)*count,len(rings)*count))))
    mesh.from_pydata(points,[],faces);mesh.update()
    mat=g.mat('d12f65',rough=.1,em=1.8)
    next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED').inputs['Specular IOR Level'].default_value=1
    mesh.materials.append(mat)
    for face in mesh.polygons:face.use_smooth=True
    obj=g.link('Glossy ruby 3D heart',mesh,r,loc)
    g.ball('Heart white glint',(-scale*.31,-scale*.275,scale*.52),(scale*.15,scale*.024,scale*.061),g.mat('ffe8ef',rough=.1,em=2.5),obj)
    return obj


def stopwatch(g,r):
    gold=g.mat('db9b42',metal=.62,rough=.29);ink=g.mat('2a2546');face=g.mat('f5dfbd',em=.24)
    p=(.78,-.17,1.34);x,y,z=p
    g.ball('Solid gold stopwatch case',p,(.40,.11,.40),gold,r)
    g.ball('Ivory dial',(x,y-.091,z),(.338,.037,.338),face,r)
    g.ball('Winding crown',(x,y,z+.425),(.078,.06,.055),gold,r)
    for i in range(12):
        a=i*math.tau/12;dx,dz=math.sin(a),math.cos(a)
        g.rod('Stopwatch dial mark',(x+dx*.264,y-.112,z+dz*.264),(x+dx*.301,y-.112,z+dz*.301),.011,ink,r)
    g.rod('Stopwatch second hand',(x,y-.134,z),(x+.144,y-.134,z+.169),.012,g.mat('b33b62'),r)
    g.label('Stopwatch printed units','0.1 SEC',(x,y-.134,z-.129),.092,ink,r)


def stage_space(g,r):
    backdrop=g.mat('12265f',em=.54)
    g.box('Royal blue cyclorama',(0,6,3),(18,.14,12),backdrop,r)
    g.box('Blue stage ground',(0,1,-.22),(18,16,.19),textured(g,'Blue floor','1b2e63','263e76',6,ground=True),r)
    rng=random.Random(221)
    for i in range(100):
        x,y,z=rng.uniform(-7,7),rng.uniform(1,5.8),rng.uniform(-1,6)
        s=rng.uniform(.009,.045);g.ball('Distant stellar glint',(x,y,z),(s,.012,s),g.mat(('8ba2ff','ead7ff','9bd9fd')[i%3],em=1.8),r)
    base=g.mat('bf5898',rough=.51);pink=g.mat('ef8aac',rough=.44);blue=g.mat('222344');white=g.mat('fff0dc',em=.35)
    g.ball('Brain mass',(0,.16,1.27),(.62,.42,.52),base,r)
    for s in (-1,1):
        for j in range(9):
            z=1.12+(j%3)*.20;x=s*(.17+(j//3)*.135)
            pts=[(x+.048*math.sin(i*.73+j),-.15+.13*(j//3),z+.085*math.cos(i*.5)) for i in range(11)]
            g.curve('Brain gyrus fold',pts,.083,pink,r)
        x=s*.15;g.ball('Glossy cartoon brain eye',(x,-.332,1.35),(.077,.044,.11),blue,r);g.ball('Eye catchlight',(x-.02,-.367,1.39),(.022,.012,.026),white,r)
    g.curve('Brain smile',[(-.071,-.323,1.19),(0,-.359,1.153),(.071,-.323,1.19)],.013,blue,r)
    g.curve('Brain arm and thumb',[(-.41,-.05,1.24),(-.75,-.17,1.08),(-.76,-.21,1.32)],.064,pink,r)
    g.curve('Brain grip',[ (.43,-.03,1.19),(.63,-.18,1.04),(.81,-.23,1.12)],.064,pink,r)
    stopwatch(g,r)


def macro_wall(g,r):
    g.box('Mulberry gallery wallpaper',(0,.51,1.89),(13,.19,5),textured(g,'Gallery painted plaster','4c2940','794955',9),r)
    silk_frame(g,r,(0,.25,1.50));particle_ribbons(g,r,(0,-.13,1.61),.43)
    brass=g.mat('d49f62',metal=.6);g.box('Brass picture light',(0,-.015,2.10),(.87,.21,.099),brass,r,.04)
    g.light('Golden picture lamp','AREA',(0,-.18,2.0),(0,.17,1.48),77,'ffd492',r).data.size=.46
    for x,z in [(-.29,1.63),(.22,1.86)]:
        g.ball('Fly body',(x,-.29,z),(.028,.019,.024),g.mat('251e2b'),r)
        for s in (-1,1):g.ball('Pale fly wing',(x+s*.027,-.285,z+.020),(.027,.009,.012),g.mat('b7afc4',metal=.2),r)


def set_lighting(g,r,idx):
    if idx in (3,4):
        key_sun=g.light('Golden directional daylight','SUN',SUN_POSITION,(0,0,0),6.5,'fff6e5',r).data
        key_sun.angle=math.radians(5);key_sun.use_shadow=True
        target=V((0,3.3,0) if idx==3 else (0,.45,0))
        spot=g.light('Local daylight shadow spot','SPOT',target+V(SUN_POSITION)*2.45,target,35000,'fff1df',r).data
        spot.spot_size=math.radians(53);spot.spot_blend=.45;spot.use_shadow=True;spot.shadow_filter_radius=1.5
        fill_sun=g.light('Cool skylight fill','SUN',(4,-4,6),(0,0,1),.92,'aecbff',r).data
        fill_sun.use_shadow=False
        return [(key_sun,6.5),(fill_sun,.92),(spot,35000)]
    if idx==0:
        g.light('Warm key motivated by street lamps','AREA',(-2.9,-2.1,3.6),(-.5,.62,1.0),320,'ffd39e',r).data.size=2.4
        g.light('Low indigo street fill','AREA',(3.2,-1.8,2.9),(-.28,.6,1.1),117*.85,'a6b9f7',r).data.size=3.8
        g.light('Warm street edge light','AREA',(-1.48,2.8,3.18),(-.2,.62,1.25),160,'ffc77f',r).data.size=1.45
        return []
    values=[('ffd19e','9fb9ff',430,105),('f1aee3','80b5ff',380,100),('ffbe82','e6a3c1',380,91),('fff0bc','b2d1ff',630,158),('fff2c6','b8d8ff',630,152),('ffba83','cdaedc',590,148),('ffd591','c294d9',190,48)]
    warm,cool,a,b=values[idx]
    g.light('Directional key','AREA',(-3.8,-4.0,5.6),(0,0,1.1),a,warm,r).data.size=3.0
    g.light('Subordinate cool fill','AREA',(3.8,-2.8,3.4),(0,0,1.1),b,cool,r).data.size=4.2
    g.light('Contour separation','AREA',(0,2.4,4.4),(0,0,1.4),a*.74,warm,r).data.size=3.8
    if idx==5:
        sun=g.light('Low shadow-casting sun','SUN',(-4,-4,6),(0,0,1),1.75,warm,r)
        sun.data.angle=.23
        return [(sun.data,1.75)]
    return []


def glint(g,r,p,s):
    m=g.mat('fff1df',em=6.0)
    x,y,z=p
    g.ball('Glint vertical',(x,y,z),(.012,.008,s),m,r);g.ball('Glint horizontal',(x,y-.01,z),(s*.81,.008,.012),m,r)


def extra(g,r,n,actors,rot,start,end):
    if n in (1,7,33,43):
        wisps=particle_ribbons(g,r,{1:(-1.53,1.21,1.03),7:(-1.6,1.18,1.03),33:(-1.09,1.01,1.02),43:(.04,1.10,2.53)}[n],2.6 if n==43 else .63)
        for i,wisp in enumerate(wisps):
            key(wisp,start,'location');wisp.location.z+=1.18 if n==43 else .105;wisp.location.x+=.10*(i-1);key(wisp,end,'location')
    if n in (28,33,39,43):
        ps={28:[(-1.58,.75,1.64)],33:[(-.36,.79,1.47)],39:[(-.14,-.19,1.09)],43:[(-.90,1.13,3.40),(.54,1.08,4.32),(1.35,1.03,3.97)]}[n]
        for i,p in enumerate(ps):
            obj=heart(g,r,p,.24 if n==43 else .095)
            obj.rotation_euler.z=-.20;key(obj,start,'location','rotation_euler')
            obj.location.z+=1.35 if n==43 else .12;obj.rotation_euler.z=.32+i*.1;key(obj,end,'location','rotation_euler')
    if n in (5,6):
        g.rod('Empty cardboard tube',(-.85,.35,.071),(-.61,.43,.088),.063,g.mat('a17859'),r)
        g.ball('Hollow dark roll end',(-.852,.349,.071),(.011,.050,.047),g.mat('3f2c34'),r)
        cup=g.box('Dry tin mug',(-.44,.43,.087),(.15,.17,.15),g.mat('969bad',metal=.62),r,.057);cup.rotation_euler.z=.35
        g.curve('Mug handle',[(-.45,.43,.11),(-.43,.31,.15),(-.37,.28,.10),(-.34,.40,.10)],.012,g.mat('969bad',metal=.62),r)
    if n==9:
        for p,s in [((2.27,-.80,.53),.065),((2.58,-.80,.29),.035),((2.47,-.80,.61),.031)]:glint(g,r,p,s)
    if n==11:
        red=g.mat('a81b46',metal=.29,rough=.18)
        g.ball('Pointed red stiletto toe',(1.00,-.89,.072),(.19,.090,.056),red,r)
        g.ball('Sloping red patent shoe',(1.20,-.86,.129),(.15,.089,.078),red,r)
        g.rod('Red stiletto spike',(1.31,-.83,.145),(1.33,-.84,.021),.025,red,r)
        g.rod('Ankle descending from limo',(1.23,-.83,.16),(1.30,-.76,.65),.070,g.mat('f0c7b7'),r)
        support_shadow(g,'Red stiletto contact',r,(1.13,-.86,.008),(.28,.16),night=True)
    if n in (6,14,17,36):
        a=actors[0];m=g.mat('53b7df',rough=.05)
        p=next(node for node in m.node_tree.nodes if node.type=='BSDF_PRINCIPLED')
        p.inputs['Specular IOR Level'].default_value=1
        p.inputs['Coat Weight'].default_value=.48;p.inputs['Coat Roughness'].default_value=.05
        for i in range(2 if n==36 else 1):
            sign=(-1,1)[i] if n==36 else 1
            x=sign*(.13 if n==36 else .304);y=.02 if n==36 else .115
            o=g.ball('Attached tear or sweat drop',(x,y,.020),(.026 if n!=36 else .045,.06 if n!=36 else .17,.013),m,a.head)
            o.rotation_euler.z=.16*sign
            streak=g.ball('White tear highlight',(-.29,.18,.96),(.15,.43,.11),g.mat('f5fdff',rough=.05),o)
            streak.rotation_euler.z=.12
    if n in (20,22,34):
        a=actors[-1];hand={20:(-.49,.12),22:(-.59,.21),34:(-.61,.21)}[n]
        pos=a.base.location+V((0,0,.78))+rot@V((hand[0],hand[1]-.18,.09));silk=cloth(g,r,pos)
        silk.rotation_euler.z=.10 if n==20 else -.06
        glint(g,r,(pos.x+.17,pos.y-.06,pos.z+.095),.042)
    if n in (29,30,31):
        for i,a in enumerate(actors):
            held=(n==30 and i==0) or (n==31 and i==1)
            p=a.base.location+V((0,0,.60))+rot@V((.09 if i==0 else -.09,0,.15)) if held else V(((-1,1)[i]*.49,-.06,.945))
            g.ball('T-bone grilled steak',p,(.26,.061 if held else .16,.12 if held else .033),g.mat('834031',rough=.67),r)
            g.ball('Steak T-bone',(p.x+.03,p.y-.053 if held else p.y,p.z+.018),(.038,.022,.065 if held else .024),g.mat('dbae86'),r)
    if n==32:
        g.ball('Airborne silver tray',(1.49,.04,1.67),(.31,.19,.036),g.mat('bec6db',metal=.64),r).rotation_euler=(.37,-.52,-.20)
        for i in range(3):g.ball('Airborne porcelain plate',(1.37+i*.17,-.15+i*.12,1.92-i*.17),(.117,.091,.016),g.mat('f8ded0'),r).rotation_euler.y=i*.22-.4
    if n==36:g.box('Big white tear tissue',(1.63,.38,1.00),(.28,.035,.25),g.mat('fff4e4'),r,.032)


def compositor(scene):
    scene.use_nodes=True;n,l=scene.node_tree.nodes,scene.node_tree.links;n.clear()
    image=n.new('CompositorNodeRLayers').outputs['Image']
    balance=n.new('CompositorNodeHueSat');balance.label='Scene color balance'
    balance.inputs['Saturation'].default_value=1.19
    balance.inputs['Value'].default_value=.82;l.new(image,balance.inputs['Image'])
    glow=n.new('CompositorNodeGlare');glow.glare_type='FOG_GLOW';glow.mix=.16;glow.threshold=.80;glow.size=7;l.new(balance.outputs[0],glow.inputs[0])
    ellipse=n.new('CompositorNodeEllipseMask');ellipse.width=.82;ellipse.height=.86
    blur=n.new('CompositorNodeBlur');blur.filter_type='GAUSS';blur.size_x=155;blur.size_y=180;l.new(ellipse.outputs[0],blur.inputs[0])
    level=n.new('CompositorNodeMath');level.operation='MULTIPLY_ADD';level.inputs[1].default_value=.18;level.inputs[2].default_value=.82;l.new(blur.outputs[0],level.inputs[0])
    vig=n.new('CompositorNodeMixRGB');vig.blend_type='MULTIPLY';vig.inputs[0].default_value=1;l.new(glow.outputs[0],vig.inputs[1]);l.new(level.outputs[0],vig.inputs[2])
    grade=n.new('CompositorNodeHueSat');grade.inputs['Saturation'].default_value=.94;grade.inputs['Value'].default_value=1.04;l.new(vig.outputs[0],grade.inputs['Image'])
    gamma=n.new('CompositorNodeGamma');gamma.inputs['Gamma'].default_value=.84;l.new(grade.outputs[0],gamma.inputs[0]);l.new(gamma.outputs[0],n.new('CompositorNodeComposite').inputs[0])


def fixture_contacts(g,roots):
    night,_,dining,day,wedding_set,porch_set,_=roots
    support_shadow(g,'Street planter contact',night,(-1.22,.81,.009),(1.24,.61),night=True)
    support_shadow(g,'Paris shrub contact',day,(-.70,.56,.006),(1.41,.66))
    for dx in (-.29,.29):
        for dy in (-.25,.25):support_shadow(g,'Cart caster contact',night,(-2.63+dx,.45+dy,.009),(.17,.14),night=True)
    for x,y in ((0,0),(-3,2.25),(3,2.5)):
        support_shadow(g,'Dining table pedestal contact',dining,(x,y,.014),(.26,.25))
        for dx in (-1.04,1.04):
            for dy in (.07,.49):support_shadow(g,'Dining chair leg contact',dining,(x+dx,y+dy,.014),(.14,.14))
    for x in (-1.4,1.4):support_shadow(g,'Arch foot contact',wedding_set,(x,1.28,.008),(.26,.22))
    for y in (-1.55,-.45,.66):
        for x in (-2.5,-1.69,1.69,2.5):
            for dx in (-.18,.18):
                for dy in (-.18,.18):support_shadow(g,'Guest chair leg contact',wedding_set,(x+dx,y+dy,.007),(.12,.12))
    for x in (-1.08,1.08):support_shadow(g,'Bench support contact',porch_set,(x,.04,.12),(.24,.31))
    for x in (-3.7,3.8):support_shadow(g,'Porch shrub contact',porch_set,(x,-.32,-.008),(.85,.46))


def build(save=True):
    OUT.mkdir(exist_ok=True,parents=True)
    name='The Billionaire’s Silk Handkerchief'
    if not save:name+=' | Visual A-B'
    old=bpy.data.scenes.get(name) if save else None
    if bpy.context.window is None and bpy.app.background:
        scene=bpy.context.scene
        bpy.data.batch_remove(ids=tuple(o for o in scene.objects if o.users_scene==(scene,)))
        scene.name=name
    else:
        scene=bpy.data.scenes.new(name)
        bpy.context.window.scene=scene
    if old is not None and old!=scene:
        bpy.data.batch_remove(ids=tuple(o for o in old.objects if o.users_scene == (old,)))
        bpy.data.scenes.remove(old);scene.name=name
    scene.render.engine='BLENDER_EEVEE_NEXT';scene.eevee.use_raytracing=False;scene.eevee.taa_render_samples=32
    scene.render.use_motion_blur=True;scene.render.motion_blur_shutter=.65;scene.render.motion_blur_position='START'
    scene.render.use_simplify=True;scene.render.simplify_subdivision_render=2
    scene.render.resolution_x=1080;scene.render.resolution_y=1920;scene.render.resolution_percentage=100;scene.render.fps=30;scene.frame_end=3270
    scene.view_settings.view_transform='AgX';scene.view_settings.look='AgX - Medium High Contrast';scene.view_settings.exposure=.32
    scene.render.image_settings.file_format='PNG';scene.render.image_settings.color_mode='RGB';scene.render.use_sequencer=False
    sky,ambient,stars=setup_world(scene)
    g=Stage(scene)
    names=['Street Bush','Brain Space','Restaurant','Paris','Wedding','Porch','Frame Macro']
    roots=[g.link(name+' Set',xyz=(40*i,0,0)) for i,name in enumerate(names)]
    stage_collections=[]
    for idx in range(len(roots)):
        collection=bpy.data.collections.new(f'BH Stage {idx:02d}');collection['bh_stage']=idx
        scene.collection.children.link(collection);stage_collections.append(collection)
    car,door,rims=street(g,roots[0]);stage_space(g,roots[1]);restaurant(g,roots[2]);paris(g,roots[3]);wedding(g,roots[4]);porch(g,roots[5]);macro_wall(g,roots[6])
    stage_shadows(g,roots[3]);stage_shadows(g,roots[4],wedding=True)
    suns=[set_lighting(g,r,idx) for idx,r in enumerate(roots)]
    fixture_contacts(g,roots)
    for dx,dy in [(-1.13,-.53),(1.10,-.53),(-1.13,.53),(1.10,.53)]:support_shadow(g,'Tire contact shadow',car,(dx,dy,-.022),(.32,.22))
    for frame,x in [(1,18),(456,8),(528,1.32),(3270,1.32)]:
        car.location.x=x;car.keyframe_insert(data_path='location',index=0,frame=frame)
    for frame,y in [(1,.06),(932,.06),(954,1.46),(3270,1.46)]:
        car.location.y=y;car.keyframe_insert(data_path='location',index=1,frame=frame)
    for frame,angle in [(1,0),(609,0),(627,-1.10),(716,-1.10),(749,0)]:door.rotation_euler.z=angle;key(door,frame,'rotation_euler')
    for rim in rims:
        for frame,angle in [(1,0),(456,0),(528,-18),(565,-20.8),(606,-21.1)]:rim.rotation_euler.y=angle;key(rim,frame,'rotation_euler')
    cam_data=bpy.data.cameras.new('Vertical camera');camera=g.link('Story camera',cam_data);scene.camera=camera;camera.rotation_mode='QUATERNION'
    cam_data.sensor_fit='HORIZONTAL';cam_data.clip_end=45;cam_data.dof.use_dof=True
    focus=g.link('Evaluated optical focus');cam_data.dof.focus_object=focus
    narration=OUT/'narration.mp3'
    envelope_path=OUT/'narration_envelope.json'
    envelope=json.loads(envelope_path.read_text(encoding='utf-8')) if envelope_path.exists() else []
    if narration.exists():
        strip=scene.sequence_editor_create().sequences.new_sound('Hindi narration',str(narration),1,1)
        if hasattr(strip.sound,'pack'):strip.sound.pack()
        strip.sound.filepath='//narration.mp3'
    sky_colors=[('1e295b','0b1536'),('101738','293e85'),('352234','7b4660'),('a4c7e2','4279ab'),('a4c7e2','4279ab'),('c2593f','2e1638'),('432b50','906178')]
    scene['dissolve_starts']=list(DISSOLVE_CUTS);scene['dissolve_length']=DISSOLVE_LENGTH
    for c,(idx,p,target,lens) in zip(CUTS,CAMERAS):
        num,start,end=c['id'],c['start'],c['end']-int(c['id']!=len(CUTS))
        r=g.link(f"Cut {num:02d} — {c['caption']}",p=roots[idx]);appear(r,start,end)
        actors=[Actor(g,r,who,pos,sunglasses=who=='lady' and idx==0 and 12<=num<=28,outfit_rim=idx in (4,5),**options) for who,pos,options in cast_specs(num)]
        shadow_patches={}
        for actor_index,a in enumerate(actors):
            if idx in (3,4):actor_shadow(g,r,a,idx==4)
            if a.pose in ('sit','squat'):
                z={0:.306,2:.506,3:.009,5:.634}.get(idx,.008)
                support_shadow(g,'Seated body contact',r,(a.base.location.x,a.base.location.y,z),(.32,.21))
            if a.pose!='squat':
                shadow_patches[a]=[support_shadow(g,'Shoe contact patch',r,(0,0,0),(.26,.16) if idx==0 else (.23,.15),night=idx==0) for _ in a.feet]
            head_origin=a.head.location.copy()
            if num==32:
                # Keep the jaw over the collar in the shared cel plane as the root tips over.
                cel_rotation=(V(target)-V(p)).to_track_quat('-Z','Y')
                head_origin=a.body.location+cel_rotation@V((0,.65,0))
            for f in sorted({start,end,*range(start+10,end,10)}):
                breath=.5-.5*math.cos((f-start+actor_index*9)*math.tau/64)
                a.chest.scale.y=1+.015*breath;a.head.location=head_origin+V((0,0,.009*breath))
                key(a.chest,f,'scale');key(a.head,f,'location')
            for lid in a.eyelids:
                first=min(start+13+(num*7+actor_index*17)%32,end-4)
                for blink in range(first,end-3,64+(num%7)):
                    for f,size in [(blink-2,1),(blink,.035),(blink+1,.035),(blink+3,1)]:lid.scale.y=size;key(lid,f,'scale')
        if num in (14,15,23) and envelope:
            spoken={14:(27.72,29.38),15:(30.73,31.12),23:(47.88,49.13)}[num]
            mouth=actors[0].mouth
            for f in range(start,end+1):
                t=(f-1)/30
                level,rounding=envelope[f-1] if f<=len(envelope) and spoken[0]<=t<=spoken[1] else (0,0)
                mouth.scale=(.84+level*.19-rounding*.23,.16+level*.89,1);key(mouth,f,'scale')
        offset=V((40*idx,0,0));p0=V(p);t=V(target)
        focus.location=t+offset
        for f in (start,end):key(focus,f,'location')
        if actors and num not in (37,39,43):
            subject=actors[-1] if num in (16,22,31,34,40) else actors[0]
            tracking=focus.constraints.new('COPY_LOCATION');tracking.name=f'Cut {num:02d} subject';tracking.target=subject.body if num==32 else subject.head
            for f,amount in ((start-1,0),(start,1),(end,1),(end+1,0)):
                tracking.influence=amount;tracking.keyframe_insert(data_path='influence',frame=f)
        direction=-1 if num in (2,24,37,43) else 1
        movement=(t-p0)*direction*(.14 if num==43 else .125)
        screen_scale=abs((t-p0+movement*.5).length/(t-p0-movement*.5).length-1)
        assert .10<=screen_scale<=.15,(num,screen_scale)
        if num==32:
            a=actors[0];a.base.rotation_mode='QUATERNION'
            view_axis=(t-p0).to_track_quat('-Z','Y')@V((0,0,1))
            for f,angle,z in ((start,0,.02),(start+31,.11,.02),(start+40,-1.14,.08),(start+47,-1.57,.08),(end,-1.57,.08)):
                a.base.rotation_quaternion=Quaternion(view_axis,angle)
                a.base.location.z=z;key(a.base,f,'rotation_quaternion','location')
        if num==16:
            a=actors[-1]
            for f,x in [(start,1.12),(start+19,.93),(start+51,.50),(end,.38)]:a.base.location.x=x;key(a.base,f,'location')
        macro=num in (5,9,11,26,39,41)
        optics=1 if macro else 2.20 if num in (16,33,34,35) else 1.64
        for f,m in ((start,0),(end,1)):
            pos=p0+movement*(m-.5);rot=(t-pos).to_track_quat('-Z','Y');camera.location=pos+offset;camera.rotation_quaternion=camera_rotation(pos,t,f,start,end)
            cam_data.lens=lens*optics;cam_data.sensor_width=29*optics;cam_data.dof.aperture_fstop=1.8 if macro else 1.45
            key(camera,f,'location','rotation_quaternion');key(cam_data,f,'lens','sensor_width','dof.aperture_fstop')
            for a in actors:
                a.aim(rot,f)
                if a not in shadow_patches:continue
                base=a.base.location.copy()
                if num==16 and a is actors[-1]:base.x=1.12 if m==0 else .38
                for patch,foot in zip(shadow_patches[a],a.feet):
                    sole=base+a.body.location+rot@foot
                    patch.location=(sole.x,sole.y,.12 if idx==5 else .016 if idx==2 else .039 if idx==4 else .009)
                    key(patch,f,'location')
            if m==0:extra(g,r,num,actors,rot,start,end)
        whip_frames=sorted(({start+1,start+2,start+3} if start in WHIP_CUTS else set())|({end-2,end-1} if end+1 in WHIP_CUTS else set()))
        for f in whip_frames:
            pos=p0+movement*((f-start)/(end-start)-.5)
            camera.rotation_quaternion=camera_rotation(pos,t,f,start,end);key(camera,f,'rotation_quaternion')
        for f in (start,end):
            for element,col in zip(sky.color_ramp.elements,sky_colors[idx]):element.color=(*rgb(col),1);element.keyframe_insert('color',frame=f)
            ambient.default_value=.18 if idx in (3,4) else .45;ambient.keyframe_insert('default_value',frame=f)
            stars.default_value=.27 if idx==0 else .16 if idx==5 else 0;stars.keyframe_insert('default_value',frame=f)
            for j,lights in enumerate(suns):
                for sun,energy in lights:
                    sun.energy=energy if j==idx else 0;key(sun,f,'energy')
        marker=scene.timeline_markers.new(f"{c.get('label', f'{num:02d}')}  {c['caption']}",frame=start)
        marker.camera=camera
        collection=bpy.data.collections.new(f'BH Cut {num:02d}');collection['bh_cut']=num;stage_collections[idx].children.link(collection)
        for obj in (r,*r.children_recursive):
            collection.objects.link(obj);scene.collection.objects.unlink(obj)
    for root,collection in zip(roots,stage_collections):
        for obj in (root,*root.children_recursive):
            if obj.name in scene.collection.objects:
                collection.objects.link(obj);scene.collection.objects.unlink(obj)
    cut_ends={c['end']-int(c['id']!=len(CUTS)) for c in CUTS}
    for owner in (camera,cam_data,focus):
        for fc in owner.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='CONSTANT' if fc.data_path.endswith('.influence') or int(k.co.x) in cut_ends else 'LINEAR'
    compositor(scene);scene.frame_set(355)
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type=='VIEW_3D':area.spaces.active.region_3d.view_perspective='CAMERA'
    if save:bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'billionaire_handkerchief.blend'),compress=True)
    return scene


if __name__=='__main__':
    build()
