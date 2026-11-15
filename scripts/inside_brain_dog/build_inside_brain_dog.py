"""Three-cut studio presenter. The upper-right insert is intentionally empty."""
import bpy
import json
import math
import sys
from pathlib import Path
from mathutils import Vector, Quaternion

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/'scripts/washroom_experiment'))
from sets import Stage, rgb

OUT = ROOT/'renders/inside_brain_dog'
ART = OUT/'assets'
V = Vector


def ease(value):
    value = max(0,min(1,value))
    return value*value*(3-2*value)


def key(obj, prop, frame):
    obj.keyframe_insert(data_path=prop,frame=frame)


def image(path):
    result=bpy.data.images.load(str(path),check_existing=True)
    if not result.packed_file:
        result.pack()
    return result


def cel_material(name,path=None):
    material=bpy.data.materials.new(name)
    material.use_nodes=True
    material.surface_render_method='DITHERED'
    nodes=material.node_tree.nodes
    nodes.clear()
    links=material.node_tree.links
    output=nodes.new('ShaderNodeOutputMaterial')
    emission=nodes.new('ShaderNodeEmission')
    emission.inputs[1].default_value=.88
    diffuse=nodes.new('ShaderNodeBsdfPrincipled')
    diffuse.inputs['Roughness'].default_value=1
    diffuse.inputs['Specular IOR Level'].default_value=0
    if path:
        texture=nodes.new('ShaderNodeTexImage')
        texture.image=image(path)
        links.new(texture.outputs['Color'],emission.inputs[0])
        links.new(texture.outputs['Color'],diffuse.inputs['Base Color'])
    else:
        color=(*rgb('161219'),1)
        emission.inputs[0].default_value=color
        diffuse.inputs['Base Color'].default_value=color
    mix=nodes.new('ShaderNodeMixShader')
    mix.inputs[0].default_value=.72
    links.new(diffuse.outputs[0],mix.inputs[1])
    links.new(emission.outputs[0],mix.inputs[2])
    surface=mix.outputs[0]
    if path:
        alpha=nodes.new('ShaderNodeMixShader')
        transparent=nodes.new('ShaderNodeBsdfTransparent')
        links.new(texture.outputs['Alpha'],alpha.inputs[0])
        links.new(transparent.outputs[0],alpha.inputs[1])
        links.new(surface,alpha.inputs[2])
        surface=alpha.outputs[0]
    links.new(surface,output.inputs[0])
    return material


def card(stage,name,width,height,material,parent=None):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(-width/2,-height/2,0),(width/2,-height/2,0),(width/2,height/2,0),(-width/2,height/2,0)],[],[(0,1,2,3)])
    mesh.materials.append(material)
    for item,uv in zip(mesh.uv_layers.new().data,[(0,0),(1,0),(1,1),(0,1)]):
        item.uv=uv
    return stage.link(name,mesh,parent)


def ribbon(stage,name,material):
    mesh=bpy.data.meshes.new(name)
    mesh.from_pydata([(0,0,0)]*50,[],[(2*i,2*i+1,2*i+3,2*i+2) for i in range(24)])
    mesh.materials.append(material)
    return stage.link(name,mesh)


def pose_ribbon(obj,start,elbow,end,rotation,frame):
    # A smooth quadratic remains inside the convex hull of its anchored controls.
    side=rotation@V((1,0,0))
    up=rotation@V((0,1,0))
    normal=rotation@V((0,0,1))
    points=[]
    for i in range(25):
        t=i/24
        point=(1-t)**2*start+2*(1-t)*t*elbow+t*t*end
        tangent=2*(1-t)*(elbow-start)+2*t*(end-elbow)
        width_axis=tangent.cross(normal)
        if width_axis.length<1e-5:
            width_axis=side.copy()
        width_axis.normalize()
        radius=.0175*(1-.12*t)
        points.extend([point-width_axis*radius,point+width_axis*radius])
    if frame==1:
        for vertex,position in zip(obj.data.vertices,points):
            vertex.co=position
        obj.shape_key_add(name='Rest contour')
        return
    shape=obj.shape_key_add(name=f'pose_{frame:03}',from_mix=False)
    for vertex,position in zip(shape.data,points):
        vertex.co=position
    shape.value=0
    shape.keyframe_insert('value',frame=frame-1)
    shape.value=1
    shape.keyframe_insert('value',frame=frame)
    shape.value=0
    shape.keyframe_insert('value',frame=frame+1)


def compositor(scene):
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
    resize=nodes.new('CompositorNodeScale')
    resize.space='RENDER_SIZE'
    links.new(vignette.outputs[0],resize.inputs[0])
    multiply=nodes.new('CompositorNodeMixRGB')
    multiply.blend_type='MULTIPLY'
    multiply.inputs[0].default_value=1
    links.new(saturation.outputs[0],multiply.inputs[1])
    links.new(resize.outputs[0],multiply.inputs[2])
    last=multiply.outputs[0]
    for index,(start,end) in enumerate([(1,65),(66,123),(124,165)]):
        source=nodes.new('CompositorNodeImage')
        source.image=image(ART/f'hud_{index}.png')
        scale=nodes.new('CompositorNodeScale')
        scale.space='RENDER_SIZE'
        links.new(source.outputs[0],scale.inputs[0])
        over=nodes.new('CompositorNodeAlphaOver')
        links.new(last,over.inputs[1])
        links.new(scale.outputs[0],over.inputs[2])
        for frame,value in [(0,0),(start,1),(end+1,0)]:
            over.inputs[0].default_value=value
            over.inputs[0].keyframe_insert('default_value',frame=frame)
        last=over.outputs[0]
    output=nodes.new('CompositorNodeComposite')
    links.new(last,output.inputs[0])
    for curve in scene.node_tree.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation='CONSTANT'


def build():
    # Isolated factory-startup process owns this scene.
    scene=bpy.context.scene
    for obj in list(scene.objects):
        bpy.data.objects.remove(obj,do_unlink=True)
    scene.name='Inside Brain | Studio Presenter'
    scene.render.engine='BLENDER_EEVEE_NEXT'
    scene.eevee.use_raytracing=False
    if hasattr(scene.eevee,'use_fast_gi'):
        scene.eevee.use_fast_gi=True
    elif hasattr(scene.eevee,'fast_gi_method'):
        scene.eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY'
    print('EEVEE AO settings',[(prop.identifier,str(getattr(scene.eevee,prop.identifier))) for prop in scene.eevee.bl_rna.properties if 'gi' in prop.identifier or 'occlusion' in prop.identifier])
    scene.eevee.taa_render_samples=32
    scene.render.use_simplify=True
    scene.render.simplify_subdivision=2
    scene.render.resolution_x=1080
    scene.render.resolution_y=1920
    scene.render.resolution_percentage=50
    scene.render.fps=30
    scene.frame_start=1
    scene.frame_end=165
    scene.view_settings.view_transform='AgX'
    scene.view_settings.look='AgX - Medium High Contrast'
    scene.world.color=(.025,.025,.025)
    scene.world.use_nodes=True
    background=next(node for node in scene.world.node_tree.nodes if node.type=='BACKGROUND')
    background.inputs[0].default_value=(*rgb('6c91b3'),1)
    background.inputs[1].default_value=.30
    stage=Stage(scene)
    wood=stage.mat('d48c46',rough=.48)
    navy=stage.mat('102536')
    trim=stage.mat('243e4e')
    brass=stage.mat('d4a359',metal=.60,rough=.36)
    stage.box('Studio back wall',(0,1.05,1.5),(4.4,.18,3.4),navy)
    stage.box('Studio floor',(0,0,-.055),(6,6,.10),stage.mat('152b35'),bevel=0)
    stage.box('Wood wainscot',(0,.93,.42),(4.4,.12,.84),stage.mat('61412b'))
    stage.box('Wainscot brass cap',(0,.845,.85),(4.4,.035,.026),brass)
    for index in range(19):
        x=-2.1+index*.23
        stage.box('Wood panel joint',(x,.86,.42),(.012,.025,.78),stage.mat('37291e'))
    for x in [-1.65,-1.49,-1.33]:
        stage.box('Acoustic panel',(x,.87,1.86),(.075,.13,1.55),trim)
    stage.box('Oak desk top',(-.20,-.24,.72),(2.20,.96,.10),wood,bevel=.035)
    stage.box('Desk front edge',(-.20,-.72,.66),(2.20,.055,.12),stage.mat('946030'),bevel=.018)
    for x in [-1.12,.71]:
        stage.box('Desk pedestal',(x,-.13,.34),(.17,.65,.68),stage.mat('583e2c'))
    # A framed recessed blank insert, with no supplied meme art or animal rig.
    portal=stage.link('BACKGROUND_INSERT_ANCHOR',xyz=(.64,.73,2.08))
    portal['purpose']='Empty display for a separately approved nonsexual insert'
    portal['inner_width_m']=.79
    portal['inner_height_m']=.98
    stage.box('Recessed display interior',(0,0,0),(.82,.055,1.02),stage.mat('07151e'),portal,.018)
    for x in [-.445,.445]:
        stage.box('Display side frame',(x,-.035,0),(.065,.11,1.15),brass,portal,.015)
    for z in [-.545,.545]:
        stage.box('Display upper lower frame',(0,-.035,z),(.95,.11,.065),brass,portal,.015)
    stage.box('Portal inner bevel',(0,-.030,-.48),(.82,.025,.018),stage.mat('43717c'),portal)
    ink=cel_material('Matte deep-ink limbs')
    root=stage.link('char_speaker',xyz=(-.32,0,0))
    body=card(stage,'Sky-blue cel shirt',.70,.79,cel_material('Hotspot-proof shirt',ART/'body.png'),root)
    body.location=(0,.045,.81)
    pelvis=stage.ball('Royal-blue pelvis',(-.32,.045,.49),(.17,.09,.11),stage.mat('1d5dec',rough=.96))
    head_pivot=stage.link('Independent camera-facing head',p=root,xyz=(0,-.19,1.39))
    head_card=card(stage,'Stable cream and jagged hair',1.16,1.16,cel_material('Hotspot-proof cream head',ART/'head.png'),head_pivot)
    face_pivot=stage.link('Grouped face parallax',p=head_pivot,xyz=(0,0,.006))
    faces={}
    for style in ['serious','question','smirk']:
        for amount in range(5):
            for blink in range(3):
                path=ART/f'face_{style}_{amount}_{blink}.png'
                obj=card(stage,path.stem,1.16,1.16,cel_material(path.stem,path),face_pivot)
                obj.hide_render=True
                faces[(style,amount,blink)]=obj
    arms=[ribbon(stage,name,ink) for name in ['Left anchored curved arm','Right anchored curved arm']]
    hands=[stage.ball(name,(0,0,0),(.032,.022,.030),ink) for name in ['Left matte mitten','Right matte mitten']]
    pointer=stage.link('Pointing index assembly')
    pointer_shaft=stage.rod('Extended pointing index',(0,0,0),(.12,0,.08),.013,ink,pointer)
    pointer_tip=stage.ball('Rounded index tip',(.12,0,.08),(.013,)*3,ink,pointer)
    question=stage.label('Question beat','?',(-.70,-.08,1.94),.19,brass)
    # Practical microphone assembly stays on its named desk support.
    metal=stage.mat('18212a',metal=.6,rough=.42)
    stage.ball('Microphone foot',(-.70,-.47,.789),(.085,.065,.018),metal)
    stage.rod('Microphone stand',(-.70,-.47,.79),(-.70,-.47,.98),.013,brass)
    stage.ball('Studio microphone capsule',(-.70,-.47,1.04),(.043,.039,.085),metal)
    for z in [.99,1.015,1.04,1.065,1.09]:
        stage.rod('Microphone grille',(-.736,-.505,z),(-.664,-.505,z),.0035,brass)
    for obj in scene.objects:
        if obj.name.startswith(('Microphone','Studio microphone')):
            obj.location.x+=.12
    stage.light('Warm key','AREA',(-2,-2.1,2.8),(-.3,0,1.2),180,'ffe2bf')
    stage.light('Cool rim','AREA',(1.55,.45,2.2),(-.2,0,1.3),110,'8ccfff')
    stage.light('Overhead fill','AREA',(-.3,-.2,3.3),(0,0,.7),120,'e5efff')
    camera=stage.link('Studio camera',bpy.data.cameras.new('Studio optics'))
    scene.camera=camera
    camera.data.sensor_fit='HORIZONTAL'
    camera.data.lens=46
    camera.data.dof.use_dof=True
    camera.data.dof.aperture_fstop=4
    compositor(scene)
    envelope=json.loads((ART/'audio_envelope.json').read_text())
    contact_errors=[]
    previous_face=None
    for frame in range(1,166):
        if frame<=65:
            t=ease((frame-1)/64)
            position=V((.02,-2.72+.13*t,1.32))
            target=V((.01,.12,1.29))
            style='serious'
            roll=0
        elif frame<=123:
            t=ease((frame-66)/57)
            position=V((.02,-2.59+.10*t,1.33))
            target=V((.01,.12,1.31))
            style='question'
            roll=math.radians(5)*ease((frame-66)/10)
        else:
            t=ease((frame-124)/14)
            position=V((.02+.13*t,-2.49+.22*t,1.33+.04*t))
            target=V((.01+.075*t,.12,1.31+.065*t))
            style='smirk'
            roll=math.radians(5)*(1-t)
        rotation=(target-position).to_track_quat('-Z','Y')
        camera.data.lens=46 if frame<124 else 46-3*ease((frame-124)/14)
        key(camera.data,'lens',frame)
        camera.location=position
        camera.rotation_mode='QUATERNION'
        camera.rotation_quaternion=rotation
        head_pivot.rotation_mode='QUATERNION'
        head_pivot.rotation_quaternion=rotation@Quaternion((0,0,1),roll)
        body.rotation_mode='QUATERNION'
        body.rotation_quaternion=rotation
        head_position=V((-.32,-.19,1.39))
        camera.data.dof.focus_distance=(head_position-position).dot(rotation@V((0,0,-1)))
        turn=.18*ease((frame-124)/11) if frame>=124 else 0
        face_pivot.location=(turn*.42*.22,0,.006)
        for obj,prop in [(camera,'location'),(camera,'rotation_quaternion'),(camera.data,'dof.focus_distance'),(head_pivot,'rotation_quaternion'),(body,'rotation_quaternion'),(face_pivot,'location')]:
            key(obj,prop,frame)
        blink=0
        for start in [42,118]:
            if start<=frame<=start+3:
                blink=1 if frame in [start,start+3] else 2
        # Measured audio extends the first phrase through f68, then pauses.
        speaking=3<=frame<=68 or 78<=frame<=116 or 137<=frame<=152
        sample=min(164,((frame-1)//2)*2)
        amount=envelope[sample] if speaking else 0
        choice=(style,amount,blink)
        if choice!=previous_face:
            if previous_face:
                old=faces[previous_face]
                old.hide_render=True
                key(old,'hide_render',frame)
            new=faces[choice]
            if previous_face is None:
                for item in faces.values():
                    item.hide_render=True
                    key(item,'hide_render',0)
            new.hide_render=False
            key(new,'hide_render',frame)
            previous_face=choice
        # Both fixed resting anchors lie on the actual oak top plus mitten radius.
        left_rest=V((-.60,-.30,.80))
        right_rest=V((.06,-.27,.80))
        left=left_rest.copy()
        right=right_rest.copy()
        if frame>=66:
            up=ease((frame-66)/12)
            left=left.lerp(V((-.76,-.12,1.84)),up)
        if frame>=124:
            up=ease((frame-125)/10)
            right=right.lerp(V((.28,-.13,1.48)),up)
            left=left.lerp(left_rest,ease((frame-124)/11))
        shoulders=[V((-.53,-.035,1.00)),V((-.11,-.035,1.00))]
        elbows=[V((-.74,-.30,.93)),V((.18,-.30,.95))]
        if frame>=66:
            elbows[0]=elbows[0].lerp(V((-.88,-.14,1.07)),ease((frame-66)/12))
        if frame>=124:
            elbows[0]=elbows[0].lerp(V((-.74,-.30,.93)),ease((frame-124)/11))
            elbows[1]=elbows[1].lerp(V((.31,-.16,1.02)),ease((frame-125)/10))
        for index,endpoint in enumerate([left,right]):
            pose_ribbon(arms[index],shoulders[index],elbows[index],endpoint,rotation,frame)
            hands[index].location=endpoint
            hands[index].rotation_mode='QUATERNION'
            hands[index].rotation_quaternion=rotation
            key(hands[index],'location',frame)
            key(hands[index],'rotation_quaternion',frame)
        pointer.location=right
        pointer.hide_render=frame<132
        pointer_shaft.hide_render=frame<132
        pointer_tip.hide_render=frame<132
        key(pointer,'location',frame)
        key(pointer,'hide_render',frame)
        key(pointer_shaft,'hide_render',frame)
        key(pointer_tip,'hide_render',frame)
        question.scale=(1,)*3 if 78<=frame<=123 else (.00001,)*3
        key(question,'scale',frame)
        if frame<=65:
            contact_errors.append(max((left-left_rest).length,(right-right_rest).length))
    # All discrete face states hold exactly. Baked transforms interpolate linearly.
    for datablock in [*scene.objects,camera.data]:
        if datablock.animation_data and datablock.animation_data.action:
            for curve in datablock.animation_data.action.fcurves:
                for point in curve.keyframe_points:
                    point.interpolation='CONSTANT' if curve.data_path=='hide_render' else 'LINEAR'
    for arm in arms:
        for curve in arm.data.shape_keys.animation_data.action.fcurves:
            for point in curve.keyframe_points:
                point.interpolation='LINEAR'
    scene.sequence_editor_create()
    voice=scene.sequence_editor.sequences.new_sound('Hindi studio dialogue',str(OUT/'narration.wav'),channel=1,frame_start=1)
    voice.sound.pack()
    for frame,name in [(1,'1A Serious setup'),(66,'1B Question gesture'),(124,'1C Point to empty display')]:
        scene.timeline_markers.new(name,frame=frame)
    scene['background_insert_status']='Empty, nonsexual insert may be added later'
    scene.frame_set(20)
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'inside_brain_dog.blend'))
    (OUT/'build_report.json').write_text(json.dumps({'frames':165,'fps':30,'audio_seconds':5.5,'rest_hand_target_error_m':max(contact_errors),'background':'empty display','subtitles':False},indent=2))


if __name__=='__main__':
    build()
