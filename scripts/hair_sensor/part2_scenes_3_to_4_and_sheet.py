"""Drone/rescue stage and calibration manifest. No full-video rendering."""
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_lib import *
from part1_assets_and_scenes_1_to_2 import SHOT_ROWS,settings

def launch():
    g=settings('3A');lab(g)
    camera(g,(.8,-2.8,2.00),(-.25,.25,1.72),55,2.0,endpos=(.7,-2.6,2.05),endtarget=(-.20,.25,1.82))
    a=actor(g,'scientist','launch','happy',(-.8,.4,0),1)
    palm=a['right'];r,h=drone(g,palm+V((0,0,.14)),.6)
    # All landing feet lie on the hand support at launch; lift is a finite event.
    for f,dz in [(844,0),(888,0),(906,.18),(921,.58)]:r.location=palm+V((0,0,.14+dz));key(r,'location',f)
    linear(r)
    g.light('Drone headlight warm spill','POINT',palm+V((0,-.1,.2)),palm,9,'ffd655')
    return g

def chase():
    g=settings('3B');lab(g,False);camera(g,(.65,-.6,2.1),(.0,.5,1.86),48,2.0,endpos=(.7,.6,2.17),endtarget=(.0,2.1,1.95))
    r,h=drone(g,(0,.45,1.8),.9)
    for f,p,rot in [(922,(0,.45,1.8),(0,-.08,0)),(958,(-.25,.9,1.94),(.08,.15,-.15)),(994,(.18,1.5,1.86),(-.06,-.12,.13)),(1029,(0,2.1,1.9),(0,0,0))]:r.location=p;r.rotation_euler=rot;key(r,'location',f);key(r,'rotation_euler',f)
    linear(r);h.data.materials.clear();h.data.materials.append(mat('ffad34',em=3))
    ribbon(g,(0,.20,1.88),(.0,3.35,1.95),height=.14)
    return g

def dish(g,xyz):
    r=g.obj('Glass specimen dish',xyz=xyz);glass=mat('a5cfcb',rough=.18,metal=.25)
    g.rod('Dish glass base',(0,0,.0),(0,0,.035),.42,glass,r)
    g.curve('Dish glass rim',[(.42*math.cos(i*math.tau/60),.42*math.sin(i*math.tau/60),.08) for i in range(60)],.018,glass,r,True)
    random.seed(22)
    for i in range(30):
        rad=random.uniform(.04,.32);a=random.uniform(0,math.tau)
        coil(g,'Second curly hair cluster', (rad*math.cos(a),rad*math.sin(a),.04),.027,random.uniform(.12,.27),random.uniform(2,4),parent=r,seed=i)
    return r

def reveal():
    g=settings('3C');lab(g);camera(g,(.45,-3.0,1.92),(.15,.5,1.55),48,2.0,endpos=(.4,-2.7,1.9))
    dish(g,(.36,.35,1.08));r,h=drone(g,(-.25,0,1.65),.65);h.data.materials.clear();h.data.materials.append(mat('ffc15c',em=2))
    actor(g,'scientist','celebrate','happy',(-1.1,1.5,0),.8)
    g.rod('Flower vase', (1.2,.7,1.08),(1.2,.7,1.45),.12,mat('b5e0d6',rough=.18))
    for i in range(4):
        p=(1.2+.13*math.cos(i*2),.7+.1*math.sin(i*2),1.85+.10*(i%2));g.curve('Flower stem',[(1.2,.7,1.4),p],.009,mat('387d50'))
        for j in range(5):g.ball('Pink flower petal',V(p)+V((.06*math.cos(j*math.tau/5),.06*math.sin(j*math.tau/5),0)),(.05,.04,.025),mat('ed99b4'))
    ribbon(g,(-.20,0,1.65),(.30,.34,1.48),height=.07)
    return g

def scan():
    g=settings('4A');rubble(g);camera(g,(1.8,-4.6,1.8),(0,1,1.6),45,2.0,endpos=(1.6,-4.1,1.85),endtarget=(0,1.1,1.6))
    r,h=drone(g,(0,.9,2.0),1.15,True)
    for f,x in [(1110,-.35),(1175,.3)]:r.location.x=x;key(r,'location',f)
    linear(r)
    # A thin transparent scanner pyramid provides visible air scattering cheaply.
    verts=[(-.07,.9,1.84),(-.8,.12,.02),(.8,.12,.02),(.8,1.72,.02),(-.8,1.72,.02)]
    me=bpy.data.meshes.new('Scanner beam');me.from_pydata(verts,[],[(0,1,2),(0,2,3),(0,3,4),(0,4,1)]);me.materials.append(alpha_mat('Scanner cone / haze','65ffad',.055));g.obj('Volumetric scanner impression',me)
    return g

def survivor():
    g=settings('4B');con=rubble(g);camera(g,(.95,-2.6,1.40),(-.15,.45,1.05),55,2.0,endpos=(.85,-2.4,1.40))
    a=actor(g,'victim','wave','worried',(-.42,.72,-.42),.82)
    slab=g.box('Fallen concrete beam / crevice roof',(-.52,1.2,1.8),(2.5,.65,.28),con);slab.rotation_euler.y=-.12
    g.box('Left crevice slab',(-1.05,.5,.43),(.72,.9,.87),con)
    g.box('Leg-trapping foreground slab',(-.55,.15,.35),(1.25,.5,.45),con)
    r,h=drone(g,(.62,.15,1.62),.55,True);h.data.materials.clear();h.data.materials.append(mat('ffc65c',em=3))
    ribbon(g,(0,.65,.60),(.62,.15,1.67),'9deca3',.12)
    g.light('Scanner bounce protects cream face','POINT',(-.2,-.3,1.3),(0,0,0),25,'96e9b1')
    return g

def finale():
    g=settings('4C');rubble(g);camera(g,(1.75,-4.3,1.45),(0,.0,1.4),45,2.8,endpos=(1.5,-3.9,1.55),endtarget=(.10,.0,1.5))
    a=actor(g,'firefighter','carry','happy',(-.35,.55,0),1.03)
    victim=actor(g,'victim','carry','happy',(.10,.12,.65),.70)
    # Supported carry rests on the firefighter's arm instead of a detached flying victim.
    g.curve('Rescuer supporting forearm',[(-.70,.18,1.1),(-.12,-.06,1.08),(.48,.12,1.31)],.045,mat('20252d'))
    r,h=drone(g,(.95,-.15,1.72),.75);h.data.materials.clear();h.data.materials.append(mat('ffcf62',em=3))
    # Separate sensor beauty camera is planned as the final subcut.
    d=bpy.data.cameras.new('Final sensor macro optics');d.lens=65;d.sensor_fit='HORIZONTAL';d.sensor_width=36;d.dof.use_dof=True;d.dof.aperture_fstop=2.4
    beauty=g.obj('Final sensor beauty camera',d,(1.50,-1.32,2.09));focus=V((.95,-.15,1.98));beauty.rotation_euler=(focus-beauty.location).to_track_quat('-Z','Y').to_euler();d.dof.focus_distance=(focus-beauty.location).length;d.clip_start=.01
    mark=g.s.timeline_markers.new('Sensor hero beauty',frame=1355);mark.camera=beauty
    first=g.s.timeline_markers.new('Carry rescue payoff',frame=1273);first.camera=g.s.camera
    for character in (a,victim):
        for part in ('body','head'):
            for f,sc in [(1273,1),(1355,0)]:character[part].scale=(sc,)*3;key(character[part],'scale',f)
            for fc in character[part].animation_data.action.fcurves:
                if fc.data_path=='scale':
                    for k in fc.keyframe_points:k.interpolation='CONSTANT'
    return g

def main():
    import part1_assets_and_scenes_1_to_2 as first
    bpy.ops.object.select_all(action='DESELECT')
    first.build()
    stages=[launch(),chase(),reveal(),scan(),survivor(),finale()]
    manifest=[]
    for shot,a,b,f,cue,action in SHOT_ROWS:
        s=bpy.data.scenes[shot];s.frame_set(f)
        manifest.append({'shot':shot,'start_frame':a,'end_frame':b,'representative_frame':f,'start_seconds':(a-1)/30,'end_seconds':b/30,'narration_cue':cue,'visible_action':action,'audio_type':'external narration; character mouths held intentionally','scene':shot})
    (OUT/'segments_timeline.json').write_text(json.dumps({'project':'hair_sensor','fps':30,'frame_count':1413,'audio_duration':47.0726666667,'shots':manifest},indent=2))
    bpy.context.window.scene=bpy.data.scenes['1C']
    version='v2' if '--v2' in sys.argv else 'v1'
    bpy.ops.wm.save_as_mainfile(filepath=str(OUT/('hair_sensor_calibration_'+version+'.blend')))
    print('BUILD COMPLETE: 12 scenes, narration-aligned timeline, no full video rendered.',flush=True)

if __name__=='__main__':main()
