"""Four contact-only fixes on the delivered V3 scene. No art/camera/lighting/HUD changes."""
import bpy,bmesh,json,math,hashlib,sys
from pathlib import Path
from mathutils import Vector as V,Quaternion,Matrix,Euler
sys.path.insert(0,str(Path(__file__).resolve().parent))
from scene_lib import Stage
OUT=Path(r'D:\remotionshorts\renders\hair_sensor')
DATA=json.loads((OUT/'shots_v3.json').read_text());ROWS=DATA['shots']
CHANGED=['1A','1C','1D','3A','3B','4B','4C']

def channel(ob,path,f):
    value=ob.path_resolve(path);value=list(value) if hasattr(value,'__len__') else value
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            if fc.data_path==path:
                if isinstance(value,list):value[fc.array_index]=fc.evaluate(f)
                else:value=fc.evaluate(f)
    return value

def animations(ob):
    if not ob.animation_data or not ob.animation_data.action:return []
    return [(fc.data_path,fc.array_index,[(tuple(k.co),k.interpolation) for k in fc.keyframe_points]) for fc in ob.animation_data.action.fcurves]

def stable_value(value):
    if isinstance(value,(float,int,bool,str)) or value is None:return value
    if isinstance(value,bpy.types.ID):return value.name
    try:return list(value)
    except TypeError:return str(value)

def properties(ob,names):
    active={fc.data_path for fc in ob.animation_data.action.fcurves} if ob.animation_data and ob.animation_data.action else set()
    return {name:stable_value(ob.path_resolve(name)) for name in names if hasattr(ob,name.split('.')[0]) and name not in active}

def node_tree(tree):
    if not tree:return None
    nodes=[]
    for n in tree.nodes:
        props={k:stable_value(getattr(n,k)) for k in ('blend_type','operation','glare_type','threshold','mix','size','quality','space','width','height') if hasattr(n,k)}
        nodes.append((n.name,n.bl_idname,props,[(i.identifier,stable_value(i.default_value)) for i in n.inputs if hasattr(i,'default_value')],n.image.name if hasattr(n,'image') and n.image else None))
    return [nodes,[(l.from_node.name,l.from_socket.identifier,l.to_node.name,l.to_socket.identifier) for l in tree.links],animations(tree)]

def invariant_snapshot():
    result={'timeline':[(r['shot'],r['start_frame'],r['end_frame']) for r in ROWS],'scenes':{},'art':{}}
    for r in ROWS:
        s=bpy.data.scenes[r['scene']];c=bpy.data.objects[r['camera']]
        lights=[]
        for ob in s.objects:
            if ob.type=='LIGHT':lights.append((ob.name,properties(ob,['location','rotation_euler','scale']),animations(ob),properties(ob.data,['type','color','energy','use_shadow','size','angle','spot_size','spot_blend','shadow_soft_size']),animations(ob.data)))
        result['scenes'][s.name]={'frames':[s.frame_start,s.frame_end],'format':[s.render.resolution_x,s.render.resolution_y,s.render.resolution_percentage,s.render.fps],'camera':[c.name,properties(c,['location','rotation_euler','rotation_quaternion','scale']),animations(c),properties(c.data,['lens','sensor_width','sensor_fit','dof.use_dof','dof.aperture_fstop','dof.focus_distance']),animations(c.data)],'lights':lights,'world':node_tree(s.world.node_tree),'compositor':node_tree(s.node_tree)}
    for im in bpy.data.images:
        if im.packed_file:result['art'][im.name]=hashlib.sha256(im.packed_file.data).hexdigest()
    return result

def digest(x):return hashlib.sha256(json.dumps(x,sort_keys=True).encode()).hexdigest()
def key(ob,path,f):ob.keyframe_insert(data_path=path,frame=f)
def linear(ob):
    if ob.animation_data and ob.animation_data.action:
        for fc in ob.animation_data.action.fcurves:
            for k in fc.keyframe_points:k.interpolation='LINEAR'
        ob.animation_data.action.update_tag();ob.update_tag()

def translate(ob,delta):
    delta=V(delta)
    if ob.type=='CURVE' and ('curved stick arm' in ob.name or 'curved leg' in ob.name):
        for p in ob.data.splines[0].bezier_points:p.co+=delta
        owner=ob.data
        if owner.animation_data and owner.animation_data.action:
            for fc in owner.animation_data.action.fcurves:
                if fc.data_path.endswith('.co'):
                    for k in fc.keyframe_points:k.co.y+=delta[fc.array_index]
                    fc.update()
            owner.animation_data.action.update_tag();owner.update_tag()
    else:
        ob.location+=delta
        if ob.animation_data and ob.animation_data.action:
            for fc in ob.animation_data.action.fcurves:
                if fc.data_path=='location':
                    for k in fc.keyframe_points:k.co.y+=delta[fc.array_index]
                    fc.update()
            ob.animation_data.action.update_tag();ob.update_tag()

def matrix_at(ob,f):
    loc=V(channel(ob,'location',f));q=Quaternion(channel(ob,'rotation_quaternion',f)) if ob.rotation_mode=='QUATERNION' else Euler(channel(ob,'rotation_euler',f)).to_quaternion()
    m=Matrix.LocRotScale(loc,q,V(channel(ob,'scale',f)))
    return matrix_at(ob.parent,f)@m if ob.parent else m

def set_arm(arm,shoulder,elbow,target,f):
    for p,pos in zip(arm.data.splines[0].bezier_points,(shoulder,elbow,target)):p.co=pos;p.keyframe_insert('co',frame=f)

def macro_fix(row):
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;g=Stage(s)
    hair=next(o for o in s.objects if o.name.startswith('Hero curly hair'))
    tool=next(o for o in s.objects if o.name.startswith('Prop_Tweezers grip'))
    jaws=sorted([o for o in tool.children if o.type=='CURVE' and o.name.startswith('Chrome tweezer jaw')],key=lambda o:o.name)
    contact=V(hair.data.splines[0].bezier_points[51].co)
    caps=[g.ball('V4 pinching jaw contact cap',(0,0,0),(.018,.018,.018),jaw.data.materials[0],tool) for jaw in jaws]
    for f in range(s.frame_start,s.frame_end+1):
        if row['shot']=='1A':
            u=max(0,min(1,(f-1)/34));e=1-(1-u)**3;dz=0;stretch=1;approach=V((.18*(1-e),0,.20*(1-e)));half=.018+.045*(1-e)
        elif f<185:
            u=max(0,min(1,(f-169)/16));e=u*u*(3-2*u);dz=0;stretch=1+.45*e;approach=V((0,0,0));half=.018
        else:
            u=max(0,min(1,(f-185)/25));e=u*u*(3-2*u);dz=.025+.425*e;stretch=1.45-.45*e;approach=V((0,0,0));half=.018
        hair.location=(0,0,.05+dz);hair.scale=(1,1,stretch);key(hair,'location',f);key(hair,'scale',f)
        tip=V((contact.x,contact.y,.05+dz+contact.z*stretch));tool.location=tip+approach;key(tool,'location',f)
        for i,(jaw,cap) in enumerate(zip(jaws,caps)):
            sign=-1 if i==0 else 1;p=jaw.data.splines[0].bezier_points[0];p.co=(sign*half,0,0);p.keyframe_insert('co',frame=f);cap.location=p.co;key(cap,'location',f)
    hair['v4_grip_index']=51;hair['v4_tweezer']=tool.name;tool['v4_closed_tip_air_gap']=0.0
    linear(hair);linear(tool)
    for cap in caps:linear(cap)

def launch_fix(row):
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s
    pad=next(o for o in s.objects if o.name.startswith('Opened supporting palm'))
    drone=next(o for o in s.objects if o.name.startswith('V3_Drone'))
    oldpad=V(pad.location);desk=next(o for o in s.objects if o.name.startswith('Lab bench receiver'))
    desk_top=desk.location.z+max(v.co.z for v in desk.data.vertices)
    mat=pad.data.materials[0];bm=bmesh.new();bmesh.ops.create_cone(bm,cap_ends=True,cap_tris=False,segments=64,radius1=.29,radius2=.29,depth=.02)
    me=bpy.data.meshes.new('V4 circular desk launch pad');bm.to_mesh(me);bm.free();me.materials.append(mat);pad.data=me;pad.location.z=desk_top+.01
    for ob in pad.children:
        if 'thumb' in ob.name or 'finger articulation' in ob.name:ob.hide_render=True
        elif ob.type=='CURVE' and 'Ink boundary' in ob.name:
            pts=ob.data.splines[0].bezier_points
            for i,p in enumerate(pts):p.co=(.29*math.cos(i*math.tau/len(pts)),.29*math.sin(i*math.tau/len(pts)),.011)
    pad_top=pad.location.z+.01;drone_base=pad_top+.21*drone.scale.z
    original_base=channel(drone,'location',s.frame_start)[2];delta=drone_base-original_base;translate(drone,(0,0,delta))
    drone['support_plane_z']=pad_top;drone['v4_support_pad']=pad.name
    arms=sorted([o for o in s.objects if o.name.startswith('scientist curved stick arm')],key=lambda o:o.name)
    hands=sorted([o for o in s.objects if o.name.startswith('scientist rounded grip')],key=lambda o:o.name);body=next(o for o in s.objects if o.name.startswith('scientist torso pivot'))
    target=V((pad.location.x-.40,pad.location.y+.045,desk_top+.26))
    for f in range(s.frame_start,s.frame_end+1):
        if row['shot']=='3A':shoulder=V((-1.6,pad.location.y,desk_top+.16));elbow=V((-.55,pad.location.y,desk_top+.25))
        else:
            m=matrix_at(body,f);q=m.to_quaternion();shoulder=m@V((.18*.97,.18*.97,-.025*.97));elbow=shoulder.lerp(target,.5)+q@V((.16*.97,0,0));elbow.z=max(elbow.z,desk_top+.055)
        set_arm(arms[1],shoulder,elbow,target,f);hands[1].location=target;key(hands[1],'location',f)
    hands[1].scale.x=.066;hands[1]['v4_pose']='proud pointing gesture; not supporting pad'
    linear(hands[1]);pad['v4_desk_top']=desk_top;pad['v4_bottom_z']=desk_top

def wisp_fix(row):
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s
    m=bpy.data.materials.new('V4 translucent pale green gold human scent');m.use_nodes=True;m.surface_render_method='BLENDED';n=m.node_tree.nodes;n.clear();l=m.node_tree.links
    tx=n.new('ShaderNodeTexImage');tx.image=next(im for im in bpy.data.images if im.name.startswith('puff_gold'))
    # Use the existing soft radial alpha, multiplied by .22: no opaque sphere silhouettes.
    opacity=n.new('ShaderNodeMath');opacity.operation='MULTIPLY';opacity.inputs[1].default_value=.22;l.new(tx.outputs['Alpha'],opacity.inputs[0])
    p=n.new('ShaderNodeBsdfPrincipled');p.inputs['Base Color'].default_value=(.62,.87,.40,1);p.inputs['Roughness'].default_value=.9
    em=n.new('ShaderNodeEmission');em.inputs[0].default_value=(.67,.94,.42,1);em.inputs[1].default_value=2.5
    mix=n.new('ShaderNodeMixShader');mix.inputs[0].default_value=.5;l.new(p.outputs[0],mix.inputs[1]);l.new(em.outputs[0],mix.inputs[2])
    transparent=n.new('ShaderNodeBsdfTransparent');alpha=n.new('ShaderNodeMixShader');l.new(opacity.outputs[0],alpha.inputs[0]);l.new(transparent.outputs[0],alpha.inputs[1]);l.new(mix.outputs[0],alpha.inputs[2]);out=n.new('ShaderNodeOutputMaterial');l.new(alpha.outputs[0],out.inputs[0])
    for i,ob in enumerate([o for o in s.objects if o.name.startswith('Soft scent puff')]):
        ob.data=ob.data.copy();ob.data.materials.clear();ob.data.materials.append(m)
        for f in range(s.frame_start,s.frame_end+1):
            age=(f-s.frame_start)/(s.frame_end-s.frame_start);t=1.25*age-i/20*.65;clamp=max(0,min(1,t));fade=max(0,min(1,t*8,(1-t)*8))
            ob.location=V((.1,.64,.69)).lerp(V((.64,.39,1.74)),clamp)+V((.025*math.sin(i+age*2),.02*math.cos(i*2),.035*math.sin(i*.8)+.05*age))
            size=.65+.10*(i%4);ob.scale=(size*fade*.62,size*fade*1.80,size*fade);ob.rotation_euler.z=.10*math.sin(i+age*2)
            key(ob,'location',f);key(ob,'scale',f)
        linear(ob)
    m['alpha_ceiling']=.22;m['emission_strength']=2.5

def carry_fix(row):
    s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;sz=.67
    for ob in s.objects:
        if ob.name.startswith('victim') and ob.parent is None:translate(ob,(-.22,0,0))
    body=next(o for o in s.objects if o.name.startswith('victim torso pivot'));head=next(o for o in s.objects if o.name.startswith('victim independent billboard head'));aim=next(o for o in s.objects if o.name.startswith('victim parallel aim'))
    firebody=next(o for o in s.objects if o.name.startswith('firefighter torso pivot'))
    arms=sorted([o for o in s.objects if o.name.startswith('firefighter curved stick arm')],key=lambda o:o.name);hands=sorted([o for o in s.objects if o.name.startswith('firefighter rounded grip')],key=lambda o:o.name)
    victim_arms=sorted([o for o in s.objects if o.name.startswith('victim curved stick arm')],key=lambda o:o.name);victim_hands=sorted([o for o in s.objects if o.name.startswith('victim rounded grip')],key=lambda o:o.name)
    legs=sorted([o for o in s.objects if o.name.startswith('victim curved leg')],key=lambda o:o.name)
    for f in range(s.frame_start,s.frame_end+1):
        q=Euler(channel(s.camera,'rotation_euler',f)).to_quaternion();location=V(channel(body,'location',f));bq=q@Quaternion((0,0,1),-.22)
        body.rotation_quaternion=bq;key(body,'rotation_quaternion',f);head.location=location+bq@V((0,.75*sz,0));head.rotation_quaternion=q;aim.location=head.location+q@V((0,0,8));key(head,'location',f);key(head,'rotation_quaternion',f);key(aim,'location',f)
        B=Matrix.LocRotScale(location,bq,V((1,1,1)));F=matrix_at(firebody,f)
        # Actual rear torso surface and actual bent-knee centers own both grip anchors.
        torso=B@V((-.18*sz,-.10*sz,-.01))
        knees=[]
        for leg in legs:
            p=V([next(fc for fc in leg.data.animation_data.action.fcurves if fc.data_path=='splines[0].bezier_points[1].co' and fc.array_index==axis).evaluate(f) for axis in range(3)])
            knees.append(p)
        knee=(knees[0]+knees[1])/2-V((0,0,.028))
        for i,(side,target) in enumerate(zip((-1,1),(torso,knee))):
            shoulder=F@V((side*.18*1.02,.18*1.02,-.025*1.02));elbow=shoulder.lerp(target,.5)+q@V((side*.12,0,-.035));set_arm(arms[i],shoulder,elbow,target,f);hands[i].location=target;key(hands[i],'location',f)
        # Keep survivor's own arm roots attached after the supported torso roll.
        for i,side in enumerate((-1,1)):
            shoulder=B@V((side*.18*sz,.18*sz,-.025*sz));target=V(channel(victim_hands[i],'location',f));elbow=shoulder.lerp(target,.5)+q@V((side*.10,0,0));set_arm(victim_arms[i],shoulder,elbow,target,f)
    for ob in (body,head,aim,*hands):linear(ob)
    body['v4_x_shift']=-.22;body['v4_supported_carry']=True

before=invariant_snapshot()
for row in ROWS:
    shot=row['shot']
    if shot in ('1A','1C','1D'):macro_fix(row)
    elif shot in ('3A','3B'):launch_fix(row)
    elif shot=='4B':wisp_fix(row)
    elif shot=='4C':carry_fix(row)
after=invariant_snapshot()
assert digest(before)==digest(after),'STOP: protected timeline/camera/lighting/HUD/art changed'
for ob in bpy.data.objects:
    if ob.type=='CURVE' and ob.data.animation_data and ob.data.animation_data.action:
        ob.data.animation_data.action.update_tag();ob.data.update_tag()
(OUT/'v4_invariants.json').write_text(json.dumps({'unchanged':True,'before_sha256':digest(before),'after_sha256':digest(after),'protected':['21-cut timeline','cameras','lighting','world','compositor/HUD','packed character/art images'],'affected_shots':CHANGED},indent=2))
(OUT/'shots_v4.json').write_text(json.dumps(DATA,indent=2))
bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'hair_sensor_v4_master.blend'))
print('V4 CONTACT-ONLY PATCH SAVED; protected fields unchanged.',flush=True)
