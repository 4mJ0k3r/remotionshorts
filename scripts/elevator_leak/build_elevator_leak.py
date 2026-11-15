"""Build the 71.5-second elevator comedy for calibration-only approval."""
import bpy
import json
import math
import sys
from pathlib import Path

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'renders/elevator_leak'
ART=OUT/'assets'
sys.path.insert(0,str(ROOT/'scripts/washroom_experiment'))
sys.path.insert(0,str(ROOT/'scripts/inside_brain_dog'))
from sets import Stage,rgb
from build_inside_brain_dog import cel_material,card,image


def create_card_material(name,path=None):
    material=cel_material(name,path)
    if path:
        emission=next(node for node in material.node_tree.nodes if node.type=='EMISSION')
        emission.inputs[1].default_value=1.04
        shader_mix=next(node for node in material.node_tree.nodes if node.type=='MIX_SHADER' and any(link.from_node.type=='BSDF_PRINCIPLED' for link in node.inputs[1].links))
        shader_mix.inputs[0].default_value=.75
    return material


def marked(obj):
    obj['set_ink']=True
    return obj


def box(stage,name,position,dimensions,material,parent=None,bevel=.012):
    return marked(stage.box(name,position,dimensions,material,parent,bevel))


def rod(stage,name,a,b,radius,material,parent=None):
    return marked(stage.rod(name,a,b,radius,material,parent))


def sphere(stage,name,position,scale,material,parent=None,ink=True):
    obj=stage.ball(name,position,scale,material,parent)
    if ink:
        marked(obj)
    return obj


def bezier(stage,name,material,radius):
    data=bpy.data.curves.new(name,'CURVE')
    data.dimensions='3D'
    data.bevel_depth=radius
    data.bevel_resolution=3
    spline=data.splines.new('BEZIER')
    spline.bezier_points.add(2)
    for point in spline.bezier_points:
        point.handle_left_type=point.handle_right_type='FREE'
    data.materials.append(material)
    return stage.link(name,data)


def steel_material(stage):
    material=stage.mat('9aa3ad',metal=.72,rough=.34)
    nodes=material.node_tree.nodes
    links=material.node_tree.links
    principled=next(node for node in nodes if node.type=='BSDF_PRINCIPLED')
    texcoord=nodes.new('ShaderNodeTexCoord')
    scale=nodes.new('ShaderNodeVectorMath')
    scale.operation='MULTIPLY'
    scale.inputs[1].default_value=(3,3,180)
    links.new(texcoord.outputs['Generated'],scale.inputs[0])
    noise=nodes.new('ShaderNodeTexNoise')
    noise.inputs['Scale'].default_value=4
    noise.inputs['Detail'].default_value=2
    links.new(scale.outputs[0],noise.inputs[0])
    ramp=nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color=(*rgb('78838e'),1)
    ramp.color_ramp.elements[1].color=(*rgb('abb4bd'),1)
    links.new(noise.outputs['Fac'],ramp.inputs[0])
    links.new(ramp.outputs[0],principled.inputs['Base Color'])
    return material


def plaque(stage,name,position,width,height,texture,orientation=(math.pi/2,0,0)):
    frame=box(stage,name+' steel frame',position,(width+.045,.035,height+.045),stage.mat('59636d',metal=.7))
    plane=card(stage,name+' printed enamel',width,height,cel_material(name,ART/texture))
    plane.location=(position[0],position[1]-.026,position[2])
    plane.rotation_euler=orientation
    for sx in [-1,1]:
        for sz in [-1,1]:
            sphere(stage,name+' mounting screw',(position[0]+sx*(width/2-.025),position[1]-.036,position[2]+sz*(height/2-.025)),(.009,.005,.009),stage.mat('e1e5e8',metal=.8),ink=False)


def cabin(stage):
    metal=steel_material(stage)
    chrome=stage.mat('bdc6d2',metal=.88,rough=.22)
    dark=stage.mat('202a34',metal=.5)
    # Tile pieces carry no contour tags, so grout remains lit texture detail.
    stage.tile_floor('Ceramic checker',8,8,.43,(-1.505,-1.505),['181a1f','e5e9f0'],None)
    for material in stage.materials.values():
        if material.name.startswith(('181a1f','e5e9f0')):
            next(node for node in material.node_tree.nodes if node.type=='BSDF_PRINCIPLED').inputs['Roughness'].default_value=.14
    box(stage,'Cabin plinth',(0,0,-.12),(3.60,3.54,.18),dark)
    for index,x in enumerate([-1.35,-.45,.45,1.35]):
        box(stage,'Back brushed panel '+str(index),(x,1.72,1.40),(.886,.10,2.80),metal)
    for sign in [-1,1]:
        for index,y in enumerate([-1.20,-.40,.40,1.20]):
            box(stage,('Left' if sign<0 else 'Right')+' brushed panel '+str(index),(sign*1.78,y,1.40),(.10,.785,2.80),metal)
        rod(stage,'Tubular chrome side handrail',(sign*1.65,-1.15,.91),(sign*1.65,1.30,.91),.025,chrome)
        for y in [-1.08,1.20]:
            rod(stage,'Handrail wall bracket',(sign*1.73,y,.91),(sign*1.64,y,.91),.016,chrome)
    rod(stage,'Tubular back handrail',(-1.55,1.57,.91),(1.55,1.57,.91),.025,chrome)
    for x in [-1.40,1.40]:
        rod(stage,'Back rail support',(x,1.69,.91),(x,1.57,.91),.016,chrome)
    for x in [-1.19,1.19]:
        obj=box(stage,'Door jamb',(x,-1.70,1.31),(.15,.22,2.62),chrome)
        obj['front_door']=True
    header=box(stage,'Elevator lintel',(0,-1.70,2.65),(2.57,.24,.22),dark)
    header['front_door']=True
    for name,x in [('Left sliding door',-.88),('Right sliding door',1.40)]:
        door=box(stage,name,(x,-1.70,1.28),(1.15,.10,2.54),metal)
        door['front_door']=True
    box(stage,'Floor display enclosure',(0,1.57,2.44),(.64,.08,.20),dark)
    stage.label('Digital red floor header','1  ↑',(0,1.51,2.44),.13,stage.mat('ff352b',em=3))
    for x in [-1.20,0,1.20]:
        for y in [-.75,.75]:
            frame=box(stage,'Ceiling LED recess',(x,y,2.79),(.83,1.10,.065),dark)
            frame['ceiling']=True
            panel=box(stage,'Glowing recessed ceiling panel',(x,y,2.751),(.73,1.0,.018),stage.mat('fff8eb',em=3),bevel=.008)
            panel['ceiling']=True
    ceiling=box(stage,'Solid steel cabin ceiling',(0,0,2.85),(3.66,3.56,.10),dark)
    ceiling['ceiling']=True
    plaque(stage,'Safety notice',(-.98,1.60,2.08),.90,.31,'safety.png')
    plaque(stage,'Capacity plaque',(.98,1.60,2.08),.91,.31,'capacity.png')
    plaque(stage,'Advertisement',(-1.04,1.60,1.46),.68,.30,'advert.png')
    box(stage,'90-floor chrome button panel',(1.681,-.53,1.43),(.06,.94,1.87),chrome)
    for row in range(15):
        for column in range(6):
            number=row*6+column+1
            y=-.88+column*.14
            z=.65+row*.111
            button=sphere(stage,f'Floor button {number}',(1.631,y,z),(.025,.049,.041),stage.mat('e1e5e8',metal=.78,rough=.28))
            label=stage.label(f'Engraved floor {number}',str(number),(1.600,y,z),.041,stage.mat('192431'))
            label.rotation_euler=(math.pi/2,0,-math.pi/2)
            button['floor_number']=number
    box(stage,'Emergency stop yellow box',(-1.69,-.72,1.20),(.15,.33,.38),stage.mat('f4c430'),bevel=.035)
    sphere(stage,'Emergency mushroom',(-1.59,-.72,1.20),(.050,.098,.098),stage.mat('e61919',rough=.32))
    for z in [1.05,1.35]:
        for y in [-.84,-.60]:
            sphere(stage,'Emergency box screw',(-1.60,y,z),(.005,.010,.010),chrome,ink=False)
    stage.light('Overhead soft ceiling','AREA',(0,0,2.64),(0,0,.6),160,'fff8eb').data.size=2.2
    stage.light('Front diffused fill','AREA',(-.5,-2.5,2.1),(0,.5,1.3),75,'d5e9ff').data.size=2.4
    stage.light('Cool rear rim','AREA',(1.2,1.25,2.45),(0,0,1.2),95,'60a5fa').data.size=1.6
    key=stage.light('Warm golden directional key','SPOT',(-.65,-.95,2.45),(0,.2,.9),280,'ffe0a3')
    key.data.spot_size=math.radians(65)
    key.data.spot_blend=.55
    key.data.use_shadow=True
    key.data.shadow_soft_size=.35
    stage.light('Alarm wash','AREA',(-1.4,-.4,2.2),(0,0,1),0,'ff5649').data.size=1.3
    alarm=stage.light('Red emergency pulse','POINT',(0,-.2,2.35),(0,0,0),0,'ff2222')
    alarm.data.shadow_soft_size=.6
    for frame,energy in [(1,0),(1449,0)]+[(frame,35 if index%2==0 else 130) for index,frame in enumerate(range(1450,2160,15))]:
        alarm.data.energy=energy
        alarm.data.keyframe_insert('energy',frame=frame)
    for fcurve in alarm.data.animation_data.action.fcurves:
        for point in fcurve.keyframe_points:
            point.interpolation='LINEAR'


def stroller(stage):
    before=set(stage.scene.objects)
    chrome=stage.mat('b8c7d6',metal=.8,rough=.24)
    blue=stage.mat('206fce',rough=.62)
    rubber=stage.mat('151a24',rough=.9)
    x,y=-.91,-.57
    for sign in [-1,1]:
        rod(stage,'Stroller crossing frame',(x+sign*.32,y-.34,.16),(x+sign*.32,y+.25,.90),.018,chrome)
        rod(stage,'Stroller lower diagonal',(x+sign*.32,y+.34,.16),(x+sign*.32,y-.22,.60),.018,chrome)
        rod(stage,'Stroller handle riser',(x+sign*.32,y+.25,.80),(x+sign*.32,y+.44,1.14),.021,chrome)
        for offset in [-.29,.29]:
            wheel=sphere(stage,'Rubber stroller wheel',(x+sign*.32,y+offset,.145),(.055,.14,.14),rubber)
            sphere(stage,'Chrome stroller hub',(x+sign*.378,y+offset,.145),(.012,.078,.078),chrome)
            for angle in [0,math.pi/3,2*math.pi/3]:
                dy,dz=.11*math.cos(angle),.11*math.sin(angle)
                rod(stage,'Wheel spoke',(x+sign*.383,y+offset-dy,.145-dz),(x+sign*.383,y+offset+dy,.145+dz),.006,chrome)
    rod(stage,'Stroller padded handle',(x-.32,y+.44,1.14),(x+.32,y+.44,1.14),.029,rubber)
    box(stage,'Blue fabric stroller seat',(x,y,.49),(.52,.48,.10),blue,bevel=.03)
    box(stage,'Blue padded stroller back',(x,y+.17,.73),(.54,.11,.55),blue,bevel=.04)
    rod(stage,'Stroller front safety bar',(x-.30,y-.29,.64),(x+.30,y-.29,.64),.022,chrome)
    # A short canopy sits behind the baby's face and never covers its eyes.
    for sign in [-1,1]:
        rod(stage,'Canopy upright',(x+sign*.30,y+.16,.79),(x+sign*.30,y+.14,1.18),.012,chrome)
    box(stage,'Blue canopy hood',(x,y+.20,1.20),(.64,.31,.075),blue,bevel=.032)
    for obj in set(stage.scene.objects)-before:
        obj['stroller']=True
    assembly=stage.link('Stroller assembly root')
    assembly['stroller']=True
    for obj in set(stage.scene.objects)-before:
        if obj!=assembly and obj.parent is None:
            obj.parent=assembly


def cast(stage,who,size,color):
    before=set(stage.scene.objects)
    ink=cel_material('Matte marker limbs '+who)
    root=stage.link(who+'_root')
    body=card(stage,who+'_body',.69*size,.79*size,create_card_material(who+' suit',ART/f'{who}_body.png'),root)
    back_body=card(stage,who+'_body_rear',.69*size,.79*size,create_card_material(who+' suit back',ART/f'{who}_body_back.png'),root)
    back_body.hide_render=True
    head=stage.link(who+'_head',p=root)
    card(stage,who+'_head_art',1.04*size,1.04*size,create_card_material(who+' cream',ART/f'{who}_head.png'),head)
    rear=card(stage,who+'_back_art',1.04*size,1.04*size,create_card_material(who+' rear hair',ART/f'{who}_back.png'),head)
    rear.hide_render=True
    face=stage.link(who+'_face_group',p=head)
    for expression in ['panic','angry','innocent','laugh','horror','baby','blink','whistle_up']:
        for amount in range(5):
            obj=card(stage,f'{who}_{expression}_{amount}',1.04*size,1.04*size,create_card_material(who+expression+str(amount),ART/f'face_{expression}_{amount}.png'),face)
            obj['expression']=expression
            obj['mouth']=amount
            obj.hide_render=True
    sphere(stage,who+'_pelvis',(0,0,.7),(.16*size,.075*size,.095*size),stage.mat('cfc8be' if who=='boss' else color,rough=.96),ink=False)
    for index in range(2):
        bezier(stage,f'{who}_arm_{index}',ink,.018*size)
        sphere(stage,f'{who}_hand_{index}',(0,0,0),(.031*size,.025*size,.033*size),ink,ink=False)
        bezier(stage,f'{who}_leg_{index}',ink,(.048 if who in ['boss','employee'] else .021)*size)
        if who in ['boss','employee']:
            bezier(stage,f'{who}_trouser_{index}',ink,.042*size)
            core=stage.scene.objects[f'{who}_trouser_{index}']
            core.data.materials.clear()
            core.data.materials.append(stage.mat('dcd5cb' if who=='boss' else '262a30',rough=.96,em=.10))
            core.data.use_fill_caps=True
            for point,radius in zip(core.data.splines[0].bezier_points,[1.06,.99,.96]):
                point.radius=radius
        shoe=sphere(stage,f'{who}_shoe_{index}',(0,0,.05),(.073*size,.13*size,.050*size),stage.mat('111317',rough=.15 if who=='boss' else .95),ink=False)
        # Grounding patches are receiver-local and carry no world ink.
        sphere(stage,f'{who}_contact_{index}',(0,0,.003),(.095*size,.145*size,.003),stage.mat('11131b',rough=1),ink=False)
    for index in range(6 if who=='employee' else 0):
        drop=sphere(stage,f'{who}_sweat_{index}',(0,0,0),(.012,.026,.008),stage.mat('9ee9ff',rough=.2,em=.3),ink=False)
    if who=='baby':
        masked=card(stage,'baby_masked_head_art',1.04*size,1.04*size,create_card_material('Baby featureless masked head',ART/'baby_head_masked.png'),head)
        masked.hide_render=True
        mask=stage.link('Baby gas mask assembly',p=head)
        olive=stage.mat('4a5d23',rough=.65)
        sphere(stage,'Gas mask facepiece',(0,-.035,.045),(.165,.135,.042),olive,mask)
        for sign in [-1,1]:
            sphere(stage,'Gas mask lens rim',(sign*.077,.015,.078),(.065,.058,.022),stage.mat('192319'),mask)
            sphere(stage,'Reflective goggle lens',(sign*.077,.015,.099),(.050,.042,.010),stage.mat('567a8d',metal=.6,rough=.15),mask)
            sphere(stage,'Olive dual-filter canister',(sign*.144,-.088,.081),(.054,.061,.043),olive,mask)
            for yy in [-.104,-.086,-.068]:
                rod(stage,'Filter inlet ridge',(sign*.144-.038,yy,.117),(sign*.144+.038,yy,.117),.004,stage.mat('24301c'),mask)
        sphere(stage,'Central mask snout',(0,-.098,.095),(.055,.051,.043),olive,mask)
    if who=='employee':
        for index in range(2):
            note=card(stage,f'Whistle music note {index}',.12,.18,create_card_material('Gold whistle note '+str(index),ART/'whistle_note.png'),head)
            note.location=(.42+index*.12,-.06+index*.17,.012)
            note.hide_render=True
    for obj in set(stage.scene.objects)-before:
        obj['cast_owner']=who


def payload(stage,name):
    root=stage.link(name)
    brown=stage.mat('3b2311',rough=.35)
    for index in range(3):
        sphere(stage,name+' organic segment '+str(index),((index-1)*.034,0,.0),(.036,.034+(index%2)*.007,.035),brown,root)
    root['length_m']=.14
    return root


def compositing(scene):
    scene.use_nodes=True
    nodes=scene.node_tree.nodes
    nodes.clear()
    links=scene.node_tree.links
    render=nodes.new('CompositorNodeRLayers')
    glow=nodes.new('CompositorNodeGlare')
    glow.glare_type='FOG_GLOW'
    glow.threshold=.82
    glow.mix=.16
    glow.size=7
    links.new(render.outputs['Image'],glow.inputs[0])
    saturation=nodes.new('CompositorNodeHueSat')
    saturation.inputs['Saturation'].default_value=1.15
    links.new(glow.outputs[0],saturation.inputs['Image'])
    vignette=nodes.new('CompositorNodeImage')
    vignette.image=image(ART/'vignette.png')
    scale=nodes.new('CompositorNodeScale')
    scale.space='RENDER_SIZE'
    links.new(vignette.outputs[0],scale.inputs[0])
    multiply=nodes.new('CompositorNodeMixRGB')
    multiply.blend_type='MULTIPLY'
    multiply.inputs[0].default_value=1
    links.new(saturation.outputs[0],multiply.inputs[1])
    links.new(scale.outputs[0],multiply.inputs[2])
    last=multiply.outputs[0]
    for index in range(18):
        source=nodes.new('CompositorNodeImage')
        source.image=image(ART/f'hud_{index}.png')
        scale=nodes.new('CompositorNodeScale')
        scale.space='RENDER_SIZE'
        links.new(source.outputs[0],scale.inputs[0])
        over=nodes.new('CompositorNodeAlphaOver')
        over.name=f'HUD_GATE_{index}'
        over.inputs[0].default_value=0
        links.new(last,over.inputs[1])
        links.new(scale.outputs[0],over.inputs[2])
        last=over.outputs[0]
    output=nodes.new('CompositorNodeComposite')
    links.new(last,output.inputs[0])


def build():
    scene=bpy.context.scene
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    scene.name='Elevator 90 Floors | Double System Leak'
    scene['elevator_leak']=True
    scene['set_ink_enabled']=False
    scene['audio_envelope']=(ART/'envelope.json').read_text()
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.eevee.use_raytracing=False
    if hasattr(scene.eevee,'fast_gi_method'):
        scene.eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY'
    scene.eevee.taa_render_samples=16
    scene.render.use_simplify=True
    scene.render.simplify_subdivision=2
    scene.render.resolution_x=1080
    scene.render.resolution_y=1920
    scene.render.resolution_percentage=50
    scene.render.fps=30
    scene.frame_start=1
    scene.frame_end=2145
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.world.use_nodes=True
    background=next(node for node in scene.world.node_tree.nodes if node.type=='BACKGROUND')
    background.inputs[0].default_value=(*rgb('7489a0'),1)
    background.inputs[1].default_value=.30
    stage=Stage(scene)
    cabin(stage)
    stroller(stage)
    for who,size,color in [('employee',1,'343a40'),('boss',1.03,'eae4dc'),('baby',.78,'facc15'),('commuter1',.91,'8e304e'),('commuter2',.91,'26436d'),('commuter3',.91,'dcbb82')]:
        cast(stage,who,size,color)
    payload(stage,'Prop_Turd_1')
    payload(stage,'Prop_Turd_2')
    for index in [1,2]:
        card(stage,f'Payload heat wisp {index}',.10,.24,cel_material('Subtle rising heat '+str(index),ART/'heat.png'))
        sphere(stage,f'Payload floor contact {index}',(0,0,.002),(.087,.045,.002),stage.mat('151317',rough=1),ink=False)
    gas=card(stage,'Green smell ribbon',.60,.95,cel_material('Soft translucent green smell',ART/'gas.png'))
    camera=stage.link('Elevator shot camera',bpy.data.cameras.new('Elevator optics'))
    scene.camera=camera
    camera.data.sensor_fit='HORIZONTAL'
    camera.data.dof.use_dof=True
    compositing(scene)
    scene.sequence_editor_create()
    voice=scene.sequence_editor.sequences.new_sound('Hindi narration and quoted dialogue',str(OUT/'narration.wav'),channel=1,frame_start=1)
    voice.sound.pack()
    for name,path in [('studio_set_ink.py',ROOT/'scripts/studio/set_ink.py'),('leg_stepper.py',ROOT/'scripts/elevator_leak/stepper.py'),('elevator_runtime.py',ROOT/'scripts/elevator_leak/runtime.py')]:
        text=bpy.data.texts.new(name)
        text.write(path.read_text())
        text.use_module=name=='elevator_runtime.py'
    exec(bpy.data.texts['elevator_runtime.py'].as_string(),{'__name__':'elevator_runtime'})
    scene.frame_set(190)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'elevator_leak.blend'))
    print('Saved calibration source with packed cels/audio and embedded frame runtime.')


if __name__=='__main__':
    build()
