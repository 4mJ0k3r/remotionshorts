"""Load the updated pose artwork into fresh Blender image datablocks."""
def refresh_art(bpy, assets):
    from pathlib import Path
    images={}
    for mat in bpy.data.materials:
        if not mat.use_nodes:
            continue
        for node in mat.node_tree.nodes:
            if node.type!='TEX_IMAGE' or not node.image:
                continue
            name=Path(bpy.path.abspath(node.image.filepath)).name
            if not name.endswith(('_body.png','_head.png')) and not name.startswith('hud_'):
                continue
            path=assets/name
            if not path.is_file():
                continue
            if name not in images:
                art=bpy.data.images.load(str(path),check_existing=False)
                art.pack()
                images[name]=art
            node.image=images[name]


def add_hats(bpy, assets):
    from pathlib import Path
    OUT=assets.parent
    for index in range(38):
        actor=bpy.data.objects[f'Contestant_{index:02d}']
        if index%5==0:
            continue
        for head in actor.children_recursive:
            if head.type!='MESH' or not head.name.endswith('_head'):
                continue
            original=head.active_material
            if not original or not original.use_nodes:
                continue
            tex=next((n for n in original.node_tree.nodes if n.type=='TEX_IMAGE'),None)
            if not tex or not tex.image:
                continue
            variant=Path(bpy.path.abspath(tex.image.filepath)).stem.removesuffix('_head')+f'_hat{index%3}.png'
            path=OUT/'assets'/variant
            if not path.exists():
                continue
            art=bpy.data.images.load(str(path),check_existing=True)
            if not art.packed_file:
                art.pack()
            hat_material=original.copy()
            head.active_material=hat_material
            hat_material.node_tree.nodes[tex.name].image=art
