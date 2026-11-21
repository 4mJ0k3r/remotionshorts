"""Build the complete timeline; render authorization ends at calibration."""
import bpy,math,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE))
from kit import Kit,rgb,heart_mesh
from rig import create_cast,image
import part1_sets_and_cuts_1_to_9 as part1
import part2_cuts_10_to_18_and_sheet as part2
OUT=ROOT/'renders/crorepati_poop_love';ART=OUT/'assets'

def main():
    bpy.ops.object.select_all(action='SELECT');bpy.ops.object.delete(use_global=False)
    s=bpy.context.scene;s['studio_root']=str(ROOT);s['production']='crorepati_poop_love';s['revision']=2;s['render_scope']='calibration_only; await user visual approval'
    s.render.engine='BLENDER_EEVEE_NEXT';s.eevee.use_raytracing=False;s.eevee.fast_gi_method='AMBIENT_OCCLUSION_ONLY';s.eevee.taa_render_samples=16
    s.render.resolution_x=1080;s.render.resolution_y=1920;s.render.resolution_percentage=50;s.render.fps=30;s.frame_start=1;s.frame_end=2124
    s.render.use_simplify=True;s.render.simplify_subdivision=2;s.render.image_settings.file_format='PNG';s.render.image_settings.color_mode='RGB';s.render.image_settings.compression=15
    s.view_settings.view_transform='AgX';s.view_settings.look='AgX - Medium High Contrast'
    s.world.use_nodes=True;bg=next(n for n in s.world.node_tree.nodes if n.type=='BACKGROUND');bg.inputs[0].default_value=(*rgb('a5b6d1'),1);bg.inputs[1].default_value=.22
    wn=s.world.node_tree.nodes;wl=s.world.node_tree.links
    coords=wn.new('ShaderNodeTexCoord');sep=wn.new('ShaderNodeSeparateXYZ');wl.new(coords.outputs['Normal'],sep.inputs[0])
    height=wn.new('ShaderNodeMapRange');height.inputs['From Min'].default_value=.12;height.inputs['From Max'].default_value=-.62;wl.new(sep.outputs['Z'],height.inputs[0])
    ramp=wn.new('ShaderNodeValToRGB');ramp.name='WorldCameraSkyRamp';ramp.color_ramp.elements.new(.48);wl.new(height.outputs[0],ramp.inputs[0])
    sky=wn.new('ShaderNodeBackground');sky.inputs[1].default_value=.8;wl.new(ramp.outputs[0],sky.inputs[0])
    paths=wn.new('ShaderNodeLightPath');wmix=wn.new('ShaderNodeMixShader');wl.new(paths.outputs['Is Camera Ray'],wmix.inputs[0]);wl.new(bg.outputs[0],wmix.inputs[1]);wl.new(sky.outputs[0],wmix.inputs[2]);wl.new(wmix.outputs[0],next(n for n in wn if n.type=='OUTPUT_WORLD').inputs['Surface'])
    g=Kit(s);part1.build(g);part2.build(g);create_cast(g,ART)
    for i in range(24):heart_mesh(g,'HeartFX%02d'%i)
    for i in range(12):
        root=g.link('SparkFX%02d'%i)
        for axis in [0,1]:
            p=[(-.06,0,0),(-.01,.008,0),(0,.06,0),(.01,.008,0),(.06,0,0),(.01,-.008,0),(0,-.06,0),(-.01,-.008,0)]
            o=g.meshx('Diamond glint ray',p,[tuple(range(8))],g.mat('fff4cc',em=3.3),root)
            if axis:o.rotation_euler.z=.785;o.scale=(.60,.60,.60)
    for i in range(18):g.sphere('DustFX%02d'%i,(0,0,0),(.011,.011,.011),'cbb997',em=.15)
    for i in range(35):
        o=g.boxx('ConfettiFX%02d'%i,(0,0,0),(.022,.012,.003),g.mat('e7bd5a',metal=.65,rough=.25),ink=False);o.rotation_euler=(i*.6,i*.3,i*.7)
    mat=bpy.data.materials.new('Soft luminous ear steam');mat.use_nodes=True;mat.surface_render_method='BLENDED';n=mat.node_tree.nodes;n.clear();l=mat.node_tree.links
    vc=n.new('ShaderNodeVertexColor');vc.layer_name='SteamFade';em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(.85,.94,1,1);em.inputs[1].default_value=2.8
    tr=n.new('ShaderNodeBsdfTransparent');mix=n.new('ShaderNodeMixShader');l.new(vc.outputs['Alpha'],mix.inputs[0]);l.new(tr.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2]);out=n.new('ShaderNodeOutputMaterial');l.new(mix.outputs[0],out.inputs[0])
    for i in range(4):
        o=g.meshx('SteamFX%02d'%i,[(0,0,0)]*36,[(j*2,j*2+1,j*2+3,j*2+2) for j in range(17)],mat)
        attr=o.data.color_attributes.new(name='SteamFade',type='FLOAT_COLOR',domain='CORNER')
        for loop,value in zip(o.data.loops,attr.data):value.color=(1,1,1,.5*math.sin(math.pi*(loop.vertex_index//2)/17))
    lips=g.sphere('KissLips',(0,0,0),(.055,.032,.020),'ed6e98',rough=.23,em=.25)
    g.meshx('ButlerTissue',[(-.085,-.085,0),(.085,-.085,0),(.072,.085,0),(-.075,.085,0),(0,0,.018)],[(0,1,4),(1,2,4),(2,3,4),(3,0,4)],g.mat('f8f2df',rough=.8))
    g.light('PinkHeartLight','POINT',(0,0,0),(0,0,0),0,'ff6fa2')
    g.light('BellyWarning','POINT',(0,0,0),(0,0,0),0,'ffa137')
    for name in ['GoldenToiletA','GoldenToiletB','ChildPottyA','ChildPottyB']:
        for o in bpy.data.objects[name].children_recursive:
            if o.type=='MESH':o['set_ink']=True
    camera=g.link('StoryCamera',bpy.data.cameras.new('StoryCamera'));s.camera=camera;camera.data.clip_start=.025;camera.data.clip_end=250;camera.data.dof.use_dof=True;camera.data.dof.aperture_blades=7
    s.use_nodes=True;nt=s.node_tree;nt.nodes.clear();l=nt.links
    rl=nt.nodes.new('CompositorNodeRLayers');gl=nt.nodes.new('CompositorNodeGlare');gl.glare_type='FOG_GLOW';gl.threshold=.90;gl.mix=.12;gl.size=7;l.new(rl.outputs['Image'],gl.inputs[0])
    sat=nt.nodes.new('CompositorNodeHueSat');sat.inputs['Saturation'].default_value=1.10;l.new(gl.outputs[0],sat.inputs['Image'])
    vig=nt.nodes.new('CompositorNodeImage');vig.image=image(ART/'vignette.png');scale=nt.nodes.new('CompositorNodeScale');scale.space='RENDER_SIZE';l.new(vig.outputs[0],scale.inputs[0])
    mult=nt.nodes.new('CompositorNodeMixRGB');mult.blend_type='MULTIPLY';mult.inputs[0].default_value=1;l.new(sat.outputs[0],mult.inputs[1]);l.new(scale.outputs[0],mult.inputs[2])
    stamp=nt.nodes.new('CompositorNodeImage');stamp.name='CalendarImage';stamp.image=image(ART/'stamp_DAY_30.png');ss=nt.nodes.new('CompositorNodeScale');ss.space='RENDER_SIZE';l.new(stamp.outputs[0],ss.inputs[0])
    over=nt.nodes.new('CompositorNodeAlphaOver');over.name='CalendarOver';l.new(mult.outputs[0],over.inputs[1]);l.new(ss.outputs[0],over.inputs[2]);composite=nt.nodes.new('CompositorNodeComposite');l.new(over.outputs[0],composite.inputs[0])
    for name,path in [('crorepati_runtime.py',HERE/'runtime.py'),('crorepati_rig.py',HERE/'rig.py'),('crorepati_story.py',HERE/'story.py'),('studio_set_ink.py',ROOT/'scripts/studio/set_ink.py'),('studio_foot_stepper.py',ROOT/'scripts/elevator_leak/stepper.py'),('crorepati_audio_env.json',OUT/'audio_env.json')]:
        t=bpy.data.texts.get(name) or bpy.data.texts.new(name);t.clear();t.write(path.read_text(encoding='utf-8'))
    s['set_ink_enabled']=True;s['audio_role']='Narration, plus quoted plea f645-744 and Paris love dialogue windows'
    exec(bpy.data.texts['crorepati_runtime.py'].as_string(),{'__name__':'crorepati_runtime'})
    s.frame_set(35);bpy.context.view_layer.update()
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'crorepati_poop_love.blend'))
    bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'crorepati_poop_love_v2.blend'))
    print('CROREPATI_BUILD_COMPLETE',len(s.objects),flush=True)

if __name__=='__main__':main()
