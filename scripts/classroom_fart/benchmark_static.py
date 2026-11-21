"""Join static opaque room geometry, preserving generated paint coordinates."""
import bpy,json,time,hashlib
from pathlib import Path
from mathutils import Vector as V
OUT=Path(r'D:\remotionshorts\renders\classroom_fart');scene=bpy.data.scenes['CF_1A'];bpy.context.window.scene=scene;scene.frame_set(1)
def animated(o):
    while o:
        if o.animation_data or o.constraints:return True
        o=o.parent
    return False
groups={}
for o in list(scene.objects):
    if o.type!='MESH' or o.hide_render or animated(o) or len(o.data.materials)!=1:continue
    m=o.data.materials[0]
    if m.surface_render_method=='BLENDED':continue
    groups.setdefault(m,[]).append(o)
dg=bpy.context.evaluated_depsgraph_get();before=sum(len(obs) for obs in groups.values());counts=[]
for material,objects in groups.items():
    if len(objects)<2:continue
    verts=[];faces=[];normals=[];coords=[];smooth=[]
    for o in objects:
        ev=o.evaluated_get(dg);mesh=ev.to_mesh(preserve_all_data_layers=True,depsgraph=dg);offset=len(verts)
        lo=V(tuple(min(p[i] for p in o.bound_box) for i in range(3)));hi=V(tuple(max(p[i] for p in o.bound_box) for i in range(3)));extent=hi-lo
        normal_matrix=o.matrix_world.to_3x3().inverted().transposed()
        for v in mesh.vertices:
            verts.append(tuple(o.matrix_world@v.co));coords.extend((v.co[i]-lo[i])/extent[i] if abs(extent[i])>1e-9 else .5 for i in range(3))
        for p in mesh.polygons:
            faces.append(tuple(offset+i for i in p.vertices));smooth.append(p.use_smooth)
            normals.extend(tuple((normal_matrix@mesh.corner_normals[i].vector).normalized()) for i in p.loop_indices)
        ev.to_mesh_clear()
    m=material.copy();m.name='OPT paint / '+material.name
    if m.use_nodes:
        n=m.node_tree.nodes;l=m.node_tree.links;attribute=n.new('ShaderNodeAttribute');attribute.attribute_name='original_generated'
        for link in list(l):
            if link.from_node.type=='TEX_COORD' and link.from_socket.name=='Generated':
                dest=link.to_socket;l.remove(link);l.new(attribute.outputs['Vector'],dest)
    mesh=bpy.data.meshes.new('Static merged / '+material.name);mesh.from_pydata(verts,[],faces);mesh.materials.append(m);mesh.update()
    for p,s in zip(mesh.polygons,smooth):p.use_smooth=s
    mesh.normals_split_custom_set(normals)
    attr=mesh.attributes.new('original_generated','FLOAT_VECTOR','POINT');attr.data.foreach_set('vector',coords)
    merged=bpy.data.objects.new('OPT_Static / '+material.name,mesh)
    for s in bpy.data.scenes:s.collection.objects.link(merged)
    for o in objects:bpy.data.objects.remove(o,do_unlink=True)
    counts.append({'material':material.name,'old_objects':len(objects),'vertices':len(verts),'faces':len(faces)})
    print('MERGED',material.name,len(objects),flush=True)
scene.frame_set(1);bpy.ops.wm.save_as_mainfile(filepath=str(OUT/'classroom_fart_v6_static_optimized.blend'))
bench=OUT/'benchmark_static';bench.mkdir(exist_ok=True);rows=json.loads((OUT/'shots.json').read_text())['shots'];times=[]
for f in [100,101,102,160,285,286,287,751,1007,1446,1580]:
    row=next(r for r in rows if r['start_frame']<=f<=r['end_frame']);s=bpy.data.scenes[row['scene']];bpy.context.window.scene=s;s.frame_set(f);s.render.filepath=str(bench/f'{f:04}.png')
    t=time.monotonic();bpy.ops.render.render(write_still=True);times.append({'frame':f,'seconds':time.monotonic()-t})
(OUT/'benchmark_static.json').write_text(json.dumps({'old_static_objects':before,'merged_groups':counts,'times':times,'source_sha256':hashlib.sha256((OUT/'classroom_fart_v6_static_optimized.blend').read_bytes()).hexdigest()},indent=2))
print('STATIC BENCHMARK',json.dumps(times),flush=True)
