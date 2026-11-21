"""V4 lighting/material/geometry upgrade of the approved baked V3 motion."""
import math
import json
import random
from pathlib import Path
import bpy
from mathutils import Vector
from v2_common import OUT, SPR, bake, hide_keys, sphere, empty, mat_world, shadow_mat, noise_mod, log, _alpha_setup
from v2_story import CUTS, FIRE, ARCH, cut_at

SHEET_FRAMES=[40,230,415,480,560,620,700,800,850,950,1080,1180,1250,1330,1427,1560]
BOUNDS=[1,540,735,828,1206,1370,1621]
V4SPR=OUT/'sprites_v4'


def linear(c):
    return c/12.92 if c<=.04045 else ((c+.055)/1.055)**2.4


def color(h):
    h=h.lstrip('#')
    return tuple(linear(int(h[i:i+2],16)/255) for i in (0,2,4))


def erase_curve(ob,path):
    if ob.animation_data and ob.animation_data.action:
        action=ob.animation_data.action
        for fc in list(action.fcurves):
            if fc.data_path==path: action.fcurves.remove(fc)


def visibility(ob,start,end):
    erase_curve(ob,'hide_render')
    hide_keys(ob,BOUNDS,[not start<=f<end for f in BOUNDS])


def replace(ob,path,frames,values):
    erase_curve(ob,path)
    bake(ob,path,frames,values)


def directional_controls(char):
    group=bpy.data.node_groups.new(f'V4_PaintedLight_{char}','ShaderNodeTree')
    for name in ('CaveMix','FireSide'):
        group.interface.new_socket(name=name,in_out='OUTPUT',socket_type='NodeSocketFloat')
    output=group.nodes.new('NodeGroupOutput')
    cave=group.nodes.new('ShaderNodeValue'); cave.name='CaveMix'
    side=group.nodes.new('ShaderNodeValue'); side.name='FireSide'
    group.links.new(cave.outputs[0],output.inputs['CaveMix'])
    group.links.new(side.outputs[0],output.inputs['FireSide'])
    bake(group,'nodes["CaveMix"].outputs[0].default_value',[1,540,1370,1620],[0.,1.,0.,0.])
    for fc in group.animation_data.action.fcurves:
        for k in fc.keyframe_points: k.interpolation='CONSTANT'
    head=bpy.data.objects[f'headpivot_{char}']
    values=[]
    frames=list(range(540,1370))
    for f in frames:
        bpy.context.scene.frame_set(f)
        toward=Vector((*FIRE, .45))-head.matrix_world.translation
        right=head.matrix_world.to_quaternion()@Vector((1,0,0))
        dot=toward.normalized().dot(right) if toward.length else 0
        values.append(.5+.5*max(-1.,min(1.,dot*2.5)))
    bake(group,'nodes["FireSide"].outputs[0].default_value',frames,values)
    return group


def create_card_material(name,filename,controls):
    m=bpy.data.materials.new(name); m.use_nodes=True; _alpha_setup(m)
    # Opaque sprite interiors must write depth for crisp DOF and volumetric fog.
    m.surface_render_method='DITHERED'
    nt=m.node_tree; nt.nodes.clear()
    textures=[]
    for folder in ('day','warm_left','warm_right'):
        tex=nt.nodes.new('ShaderNodeTexImage'); tex.name=folder
        tex.image=bpy.data.images.load(str(V4SPR/folder/filename),check_existing=True)
        tex.image.colorspace_settings.name='sRGB'
        textures.append(tex)
    ctrl=nt.nodes.new('ShaderNodeGroup'); ctrl.node_tree=controls
    cave=nt.nodes.new('ShaderNodeMixRGB'); cave.name='Painted cave gradient'
    nt.links.new(ctrl.outputs['FireSide'],cave.inputs[0])
    nt.links.new(textures[1].outputs['Color'],cave.inputs[1])
    nt.links.new(textures[2].outputs['Color'],cave.inputs[2])
    palette=nt.nodes.new('ShaderNodeMixRGB'); palette.name='Outdoor / cave palette'
    nt.links.new(ctrl.outputs['CaveMix'],palette.inputs[0])
    nt.links.new(textures[0].outputs['Color'],palette.inputs[1])
    nt.links.new(cave.outputs[0],palette.inputs[2])
    bsdf=nt.nodes.new('ShaderNodeBsdfPrincipled')
    bsdf.inputs['Roughness'].default_value=1.
    bsdf.inputs['Specular IOR Level'].default_value=0.
    nt.links.new(palette.outputs[0],bsdf.inputs['Base Color'])
    emission=nt.nodes.new('ShaderNodeEmission')
    emission.inputs['Strength'].default_value=.88
    nt.links.new(palette.outputs[0],emission.inputs['Color'])
    shade=nt.nodes.new('ShaderNodeMixShader'); shade.name='Hotspot-proof 72 percent emission'
    shade.inputs[0].default_value=.72
    nt.links.new(bsdf.outputs[0],shade.inputs[1]);nt.links.new(emission.outputs[0],shade.inputs[2])
    transparent=nt.nodes.new('ShaderNodeBsdfTransparent')
    alpha=nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(textures[0].outputs['Alpha'],alpha.inputs[0])
    nt.links.new(transparent.outputs[0],alpha.inputs[1]);nt.links.new(shade.outputs[0],alpha.inputs[2])
    output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(alpha.outputs[0],output.inputs[0])
    return m


def character_materials():
    for char in ('caveman','buddy','elder'):
        controls=directional_controls(char)
        for ob in bpy.data.objects:
            if ob.name==f'torso_{char}':
                filename=f'v2torso_{char}.png'
            elif ob.name.startswith(f'head_{char}_') and ob.type=='MESH':
                filename='v2'+ob.name+'.png'
            else: continue
            ob.data.materials.clear()
            ob.data.materials.append(create_card_material('V4_'+ob.name,filename,controls))


def tighten_squat_neck():
    # Apply the requested .78 radius neck overlap only to the corner squat.
    head=bpy.data.objects['headpivot_caveman'];torso=bpy.data.objects['torso_caveman']
    values={}
    for f in range(735,828):
        bpy.context.scene.frame_set(f)
        up=torso.rotation_quaternion@Vector((0,1,0))
        values[f]=head.location-up*(.248*(.88-.78))
    for fc in head.animation_data.action.fcurves:
        if fc.data_path=='location':
            for key in fc.keyframe_points:
                f=round(key.co.x)
                if f in values:key.co.y=values[f][fc.array_index]
            fc.update()


def noise_material(name,colors,rough=.88,scale=3.,bump=.04,spec=.02):
    m=bpy.data.materials.new(name);m.use_nodes=True
    nt=m.node_tree;b=nt.nodes['Principled BSDF']
    b.inputs['Roughness'].default_value=rough;b.inputs['Specular IOR Level'].default_value=spec
    geometry=nt.nodes.new('ShaderNodeNewGeometry')
    noise=nt.nodes.new('ShaderNodeTexNoise');noise.inputs['Scale'].default_value=scale
    noise.inputs['Detail'].default_value=2.;noise.inputs['Roughness'].default_value=.65
    nt.links.new(geometry.outputs['Position'],noise.inputs['Vector'])
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.interpolation='EASE'
    ramp.color_ramp.elements[0].position=.23;ramp.color_ramp.elements[1].position=.77
    if len(colors)==3:ramp.color_ramp.elements.new(.50)
    for el,col in zip(ramp.color_ramp.elements,colors):el.color=(*color(col),1)
    nt.links.new(noise.outputs['Fac'],ramp.inputs[0]);nt.links.new(ramp.outputs[0],b.inputs['Base Color'])
    fine=nt.nodes.new('ShaderNodeTexNoise');fine.inputs['Scale'].default_value=8.;fine.inputs['Detail'].default_value=2.
    nt.links.new(geometry.outputs['Position'],fine.inputs['Vector'])
    bp=nt.nodes.new('ShaderNodeBump');bp.inputs['Distance'].default_value=bump;bp.inputs['Strength'].default_value=.24
    nt.links.new(fine.outputs['Fac'],bp.inputs['Height']);nt.links.new(bp.outputs[0],b.inputs['Normal'])
    return m


def mesh(name,verts,faces,material,parent):
    data=bpy.data.meshes.new(name);data.from_pydata(verts,[],faces);data.update()
    ob=bpy.data.objects.new(name,data);bpy.context.collection.objects.link(ob);ob.parent=parent
    ob.data.materials.append(material)
    return ob


def sculpt(ob,strength=.55):
    # Three actual subdivision passes are applied once to modest topology;
    # the scene still keeps its 4GB render simplification cap at level 2.
    bpy.context.view_layer.objects.active=ob;ob.select_set(True)
    sc=bpy.context.scene;old=sc.render.use_simplify;sc.render.use_simplify=False
    sub=ob.modifiers.new('Three sculpt subdivision passes','SUBSURF');sub.levels=3;sub.render_levels=3
    bpy.ops.object.modifier_apply(modifier=sub.name)
    sc.render.use_simplify=old
    for name,kind,amount,size in [('Broad Voronoi crags','VORONOI',strength*.64,.65),('Cloud erosion','CLOUDS',strength*.36,.34)]:
        tex=bpy.data.textures.new(name+'_'+ob.name,kind);tex.noise_scale=size
        mod=ob.modifiers.new(name,'DISPLACE');mod.texture=tex;mod.texture_coords='GLOBAL';mod.strength=amount
        mod.mid_level=.5
    for p in ob.data.polygons:p.use_smooth=True
    ob.select_set(False)
    visibility(ob,540,1370)


def cave_geometry():
    parent=bpy.data.objects['set_B']
    for ob in list(bpy.data.objects):
        if ob.name.startswith(('cave_back_','arch_jamb_')) or ob.name in ('arch_rim','cave_left','cave_right','cave_ceil'):
            bpy.data.objects.remove(ob,do_unlink=True)
    rock=noise_material('V4 craggy cavern rock',['#241e19','#3d332a'],rough=.88,scale=1.7,bump=.04)
    # Stylized ambient bounce preserves readable dark stone in fast EEVEE.
    # It follows displaced normals, so crags retain directional modelling.
    nt=rock.node_tree;b=nt.nodes['Principled BSDF']
    palette=next(n for n in nt.nodes if n.type=='VALTORGB')
    nt.links.new(palette.outputs[0],b.inputs['Emission Color'])
    geometry=next(n for n in nt.nodes if n.type=='NEW_GEOMETRY')
    dot=nt.nodes.new('ShaderNodeVectorMath');dot.operation='DOT_PRODUCT';dot.inputs[1].default_value=(0,-.6,-.8)
    nt.links.new(geometry.outputs['Normal'],dot.inputs[0])
    ambient=nt.nodes.new('ShaderNodeMath');ambient.operation='MULTIPLY_ADD';ambient.inputs[1].default_value=.23;ambient.inputs[2].default_value=.62
    nt.links.new(dot.outputs['Value'],ambient.inputs[0]);nt.links.new(ambient.outputs[0],b.inputs['Emission Strength'])
    verts=[];faces=[];nx,ny=20,16
    for j in range(ny+1):
        y=-8.5+j*14.3/ny
        for i in range(nx+1):
            a=math.pi*i/nx
            verts.append((4.85*math.cos(a),y,-.10+4.9*math.sin(a)))
    for j in range(ny):
        for i in range(nx):
            a=j*(nx+1)+i;faces.append((a,a+1,a+nx+2,a+nx+1))
    shell=mesh('V4 sculpted cavern vault',verts,faces,rock,parent);sculpt(shell)
    # Bowed rear rock face. The real opening remains clear for the lion shot.
    verts=[];faces=[];nx,nz=32,18
    for j in range(nz+1):
        z=j*5.3/nz-.08
        for i in range(nx+1):
            x=-5.15+i*10.3/nx
            verts.append((x,4.90+.28*(1-(x/5.2)**2)+.12*math.sin(z*1.4),z))
    for j in range(nz):
        for i in range(nx):
            a=j*(nx+1)+i
            x=(verts[a][0]+verts[a+1][0])/2;z=(verts[a][2]+verts[a+nx+1][2])/2
            mouth=((x-ARCH[0])/.90)**2+((z-1.02)/1.32)**2
            if mouth<1:continue
            if (x/5.3)**2+(max(0,z)/5.3)**2>1.12:continue
            faces.append((a,a+1,a+nx+2,a+nx+1))
    back=mesh('V4 bowed rock wall with real mouth',verts,faces,rock,parent);sculpt(back,.55)
    # Natural seven-boulder arch, no tube or rectangular doorway jambs.
    random.seed(408)
    for i in range(7):
        a=math.pi*i/6
        ob=sphere(f'V4 mouth boulder {i}',(ARCH[0]+1.02*math.cos(a),4.62,.42+2.00*math.sin(a)),
                  .42,rock,scale=(1.0,1.05,1.40),parent=parent)
        ob.rotation_euler=(random.uniform(-.15,.15),random.uniform(-.15,.15),random.uniform(-.25,.25))
        d=ob.modifiers.new('Natural arch crags','DISPLACE');d.texture=bpy.data.textures.get('rock_noise');d.strength=.16
        visibility(ob,540,1370)
    floor=bpy.data.objects['cave_floor'];floor.data.materials.clear();floor.data.materials.append(rock)
    return shell,back


def outdoor_materials():
    grass=noise_material('V4 matte three-color meadow',['#b59257','#5c8001','#7cb518'],rough=.92,scale=.43,bump=.012,spec=.02)
    soil=noise_material('V4 matte earth',['#563b23','#a07848'],rough=.96,scale=3.,bump=.025,spec=.01)
    for ob in bpy.data.objects:
        if ob.type!='MESH':continue
        if ob.name=='savanna_ground' or ob.name.startswith(('hill_','vg_','vhill_')):
            ob.data.materials.clear();ob.data.materials.append(grass)
        elif ob.name in ('soil_mound','corner_patch'):
            ob.data.materials.clear();ob.data.materials.append(soil)
    # A vertical earth gradient makes the existing half-metre trench read deep.
    m=noise_material('V4 recessed pit walls',['#251b12','#765335'],rough=.98,scale=7.,bump=.025,spec=.0)
    nt=m.node_tree;b=nt.nodes['Principled BSDF'];geometry=next(n for n in nt.nodes if n.type=='NEW_GEOMETRY')
    sep=nt.nodes.new('ShaderNodeSeparateXYZ');nt.links.new(geometry.outputs['Position'],sep.inputs[0])
    mapping=nt.nodes.new('ShaderNodeMapRange');mapping.inputs['From Min'].default_value=-.5;mapping.inputs['From Max'].default_value=.06
    nt.links.new(sep.outputs['Z'],mapping.inputs[0])
    ramp=nt.nodes.new('ShaderNodeValToRGB');ramp.color_ramp.elements[0].color=(*color('#100c08'),1);ramp.color_ramp.elements[1].color=(*color('#8b633b'),1)
    nt.links.new(mapping.outputs[0],ramp.inputs[0]);nt.links.new(ramp.outputs[0],b.inputs['Base Color'])
    for name in ('pit_left','pit_right','pit_front','pit_back'):
        ob=bpy.data.objects[name];ob.data.materials.clear();ob.data.materials.append(m)
    floor=bpy.data.objects['pit_floor'];floor.data.materials.clear();floor.data.materials.append(mat_world('V4 pit contact darkness',color('#120d08'),.99))


def orient_area(ob,target):
    ob.rotation_euler=(Vector(target)-ob.location).to_track_quat('-Z','Y').to_euler()


def lighting():
    fill=bpy.data.objects['CaveFill'];fill.location=(0,-1.5,3.2)
    fill.data.energy=150;fill.data.size=6.5;fill.data.color=color('#486581');fill.data.use_shadow=False
    orient_area(fill,(0,1.0,.8));visibility(fill,540,1370)
    camp=bpy.data.objects['Campfire'];camp.location=(0,.2,.45)
    camp.data.animation_data_clear();camp.data.energy=65;camp.data.color=color('#ff851b');camp.data.shadow_soft_size=.85
    # The fire's emission and broad light are separate; don't shadow-cage it.
    camp.data.use_shadow=True;noise_mod(camp.data,'energy',-1,scale=8,strength=3.)
    visibility(camp,540,1370)
    for ob in list(bpy.data.objects):
        if ob.type=='LIGHT' and (ob.name=='Toxic' or (ob.data.type=='POINT' and ob.data.color.g>ob.data.color.r*1.3 and ob.data.color.g>ob.data.color.b*1.3)):
            bpy.data.objects.remove(ob,do_unlink=True)
    light=bpy.data.lights.new('V4 broad toxic overhead','AREA');light.energy=95;light.size=4.5;light.color=color('#52e038');light.use_shadow=False
    toxic=bpy.data.objects.new('V4 broad toxic overhead',light);bpy.context.collection.objects.link(toxic);toxic.location=(.5,1.2,2.6)
    orient_area(toxic,(.5,1.2,0));visibility(toxic,828,1206)
    for name,start,end,hexcolor in [('Sun',1,540,'#fff3d6'),('Sunset',1370,1621,'#ff9e44')]:
        ob=bpy.data.objects[name];ob.data.energy=3.5;ob.data.angle=math.radians(15);ob.data.color=color(hexcolor);visibility(ob,start,end)
    data=bpy.data.lights.new('V4 outdoor sky fill','AREA');data.energy=240;data.size=15;data.use_shadow=False
    sky=bpy.data.objects.new('V4 outdoor sky fill',data);bpy.context.collection.objects.link(sky);sky.location=(0,0,8)
    data.color=color('#a8dadc');data.keyframe_insert('color',frame=1)
    data.color=color('#f4a261');data.keyframe_insert('color',frame=1370)
    for fc in data.animation_data.action.fcurves:
        for kp in fc.keyframe_points:kp.interpolation='CONSTANT'
    erase_curve(sky,'hide_render');hide_keys(sky,BOUNDS,[540<=f<1370 for f in BOUNDS])
    bulb=bpy.data.lights['BulbLight'];bulb.shadow_soft_size=.6
    action=bulb.animation_data.action
    for fc in action.fcurves:
        if fc.data_path=='energy':
            for k in fc.keyframe_points:k.co.y=min(25.,max(0.,k.co.y*25./12.))
    glow=bpy.data.materials['bulb_glow'];glow.node_tree.nodes['Principled BSDF'].inputs['Emission Strength'].default_value=3.5


def poison_fog():
    for ob in list(bpy.data.objects):
        if ob.name.startswith('haze_'):bpy.data.objects.remove(ob,do_unlink=True)
    m=bpy.data.materials.new('V4 soft translucent green vapor alpha .18');m.use_nodes=True
    m.diffuse_color=(*color('#89bc65'),.18);m['alpha']=.18
    nt=m.node_tree;nt.nodes.clear()
    coords=nt.nodes.new('ShaderNodeTexCoord')
    center=nt.nodes.new('ShaderNodeVectorMath');center.operation='SUBTRACT';center.inputs[1].default_value=(.5,.5,.5)
    nt.links.new(coords.outputs['Generated'],center.inputs[0])
    length=nt.nodes.new('ShaderNodeVectorMath');length.operation='LENGTH';nt.links.new(center.outputs[0],length.inputs[0])
    radial=nt.nodes.new('ShaderNodeMath');radial.operation='MULTIPLY_ADD';radial.inputs[1].default_value=-2.;radial.inputs[2].default_value=1.;radial.use_clamp=True
    nt.links.new(length.outputs['Value'],radial.inputs[0])
    alpha=nt.nodes.new('ShaderNodeValue');alpha.name='Alpha';alpha.outputs[0].default_value=.18
    density=nt.nodes.new('ShaderNodeMath');density.operation='MULTIPLY';nt.links.new(radial.outputs[0],density.inputs[0]);nt.links.new(alpha.outputs[0],density.inputs[1])
    soften=nt.nodes.new('ShaderNodeMath');soften.operation='MULTIPLY';soften.inputs[1].default_value=.25;nt.links.new(density.outputs[0],soften.inputs[0])
    volume=nt.nodes.new('ShaderNodeVolumePrincipled');volume.inputs['Color'].default_value=(*color('#89bc65'),1);volume.inputs['Anisotropy'].default_value=.15
    nt.links.new(soften.outputs[0],volume.inputs['Density'])
    output=nt.nodes.new('ShaderNodeOutputMaterial');nt.links.new(volume.outputs['Volume'],output.inputs['Volume'])
    random.seed(441)
    for i in range(15):
        x=random.uniform(-1.7,3.0);y=random.uniform(2.9,4.1);z=random.uniform(.45,1.9)
        ob=sphere(f'V4 drifting fog {i:02d}',(x,y,z),1,m,scale=(random.uniform(.65,1.05),random.uniform(.4,.75),random.uniform(.25,.45)),parent=bpy.data.objects['set_B'])
        fr=list(range(828,1207,3));vals=[(x+.12*math.sin((f-828)*.025+i),y+.08*math.cos((f-828)*.021+i),z+.12*math.sin((f-828)*.015+i)) for f in fr]
        bake(ob,'location',fr,vals);visibility(ob,828,1206)


def poop_geometry():
    material=noise_material('V4 coiled earthy brown',['#352315','#654326'],rough=.95,scale=9.,bump=.012,spec=.01)
    shadow=shadow_mat('V4 coil contact shadow',SPR/'tex_shadow.png')
    for i in range(4):
        old=bpy.data.objects[f'poop_{i}'];x,y=old.location[:2]
        bpy.data.objects.remove(old,do_unlink=True)
        root=empty(f'V4 poop mound {i}',parent=bpy.data.objects['set_B'])
        objects=[]
        for j,(radius,tube,z) in enumerate([(.13,.045,.055),(.098,.041,.13),(.065,.034,.196)]):
            bpy.ops.mesh.primitive_torus_add(major_radius=radius,minor_radius=tube,major_segments=24,minor_segments=8,location=(x,y,z))
            ob=bpy.context.object;ob.name=f'V4 poop {i} coil {j}';ob.scale.y=.86;ob.data.materials.append(material);ob.parent=root
            for face in ob.data.polygons:face.use_smooth=True
            objects.append(ob)
        bpy.ops.mesh.primitive_cone_add(vertices=20,radius1=.06,radius2=.012,depth=.11,location=(x+.018,y,.257))
        ob=bpy.context.object;ob.name=f'V4 poop {i} curled peak';ob.data.materials.append(material);ob.parent=root;objects.append(ob)
        bpy.ops.mesh.primitive_plane_add(size=1,location=(x,y,.007));ob=bpy.context.object;ob.name=f'V4 poop {i} floor contact';ob.scale=(.43,.37,1);ob.data.materials.append(shadow);ob.parent=root;objects.append(ob)
        for ob in objects+[root]:visibility(ob,735,1206)


def compositor():
    nt=bpy.context.scene.node_tree
    for node in nt.nodes:
        if node.type=='GLARE':node.threshold=1.1;node.mix=-.90;node.size=7
        if node.type=='HUE_SAT':node.inputs['Saturation'].default_value=1.06
        if node.type=='MIX_RGB':node.inputs[0].default_value=.12


def animate_held_shot_fire():
    """Keep held character poses alive after reducing noisy light hotspots."""
    frames=list(range(1,1621))
    def enhanced(f):return 540<=f<590 or 735<=f<828 or 1293<=f<1370
    for i,height in enumerate((.38,.55,.42)):
        ob=bpy.data.objects[f'flame_{i}']
        old=ob.animation_data.action.fcurves.find('scale',index=2)
        base=[old.evaluate(f) for f in frames]
        scales=[];locations=[]
        x,y,z=ob.location
        for f,b in zip(frames,base):
            active=enhanced(f)
            phase=f*2*math.pi/8.7+i*2.1
            sz=b*(1+.30*math.sin(phase)) if active else b
            sx=1+.18*math.sin(f*2*math.pi/11.3+i*1.4) if active else 1.
            scales.append((sx,1.,sz))
            locations.append((x,y,.16+height*.5*sz if active else z))
        erase_curve(ob,'scale');bake(ob,'scale',frames,scales)
        erase_curve(ob,'location');bake(ob,'location',frames,locations)
    flame=bpy.data.materials['flame'].node_tree
    values=[.70*(1+.12*math.sin(f*2*math.pi/10.7)) if enhanced(f) else .70 for f in frames]
    bake(flame,'nodes["Principled BSDF"].inputs["Emission Strength"].default_value',frames,values)


def animate_squat_fire_bounce():
    # In the corner-squat shot the fire is behind the camera. Give its soft
    # bounced contribution a restrained flicker while the approved pose holds.
    nt=bpy.data.materials['V4 craggy cavern rock'].node_tree
    p=nt.nodes['Principled BSDF']
    source=p.inputs['Emission Strength'].links[0].from_socket
    bounce=nt.nodes.new('ShaderNodeMath');bounce.name='Soft fire bounce in held squat';bounce.operation='MULTIPLY'
    nt.links.new(source,bounce.inputs[0]);nt.links.new(bounce.outputs[0],p.inputs['Emission Strength'])
    frames=list(range(1,1621))
    values=[1+.045*math.sin(f*.41)+.018*math.sin(f*.83+.8) if 735<=f<828 else 1. for f in frames]
    bake(nt,'nodes["Soft fire bounce in held squat"].inputs[1].default_value',frames,values)


def build_scene():
    bpy.ops.wm.open_mainfile(filepath=str(OUT/'caveman_toilet_v3.blend'))
    sc=bpy.context.scene;sc.render.engine='BLENDER_EEVEE_NEXT';sc.eevee.use_raytracing=False
    sc.render.use_simplify=True;sc.render.simplify_subdivision=2
    log('V4: replacing character card shaders and painted lighting')
    character_materials()
    tighten_squat_neck()
    log('V4: sculpting stone cavern and natural boulder mouth')
    shell,back=cave_geometry();outdoor_materials()
    log('V4: rebuilding broad cinematic lights, haze and coiled props')
    lighting();poison_fog();poop_geometry();compositor();animate_held_shot_fire();animate_squat_fire_bounce()
    sc.frame_start=1;sc.frame_end=1620;sc.render.fps=30
    sc.render.resolution_x=180;sc.render.resolution_y=320;sc.eevee.taa_render_samples=12
    sc.frame_set(1)
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'caveman_toilet_v4.blend'))
    log(f'V4 built: {len(bpy.data.objects)} objects; sculpt faces={len(shell.data.polygons)+len(back.data.polygons)}')
