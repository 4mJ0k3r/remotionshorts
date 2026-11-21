"""Final framing and sharp HUD composite for the cinematic calibration."""
import bpy, math
from pathlib import Path
from mathutils import Vector, Quaternion


def finish(s, key):
    objects = bpy.data.objects
    cam = s.camera
    hud = objects['hud_rig']
    for frame, eye, target, lens, tilt in [
        (144,(-.72,-3.75,2.1),(0,0,1.93),39,0),
        (264,(-.62,-3.55,1.72),(.21,0,1.83),34,-.07),
        (378,(-.45,-8.45,.55),(.05,-5.6,.68),29,.025),
        (732,(1.05,-7.3,2.55),(0,0,2.04),28,0),
        (1446,(-.82,-6.15,2.2),(-.75,0,1.63),28,0),
        (1539,(-1.90,-4.3,2.52),(-1.21,0,2.30),38,.025),
        (1740,(.31,-3.52,2.14),(.20,0,2.05),38,-.025),
        (2095,(2.55,-8.65,4.2),(2.75,1.04,1.82),24,0),
    ]:
        direction = Vector(target)-Vector(eye)
        rotation = direction.to_track_quat('-Z','Y') @ Quaternion((0,0,1),tilt)
        key(cam,'location',frame,eye)
        key(cam,'rotation_euler',frame,rotation.to_euler())
        key(cam.data,'lens',frame,lens)
        cam.data.dof.focus_distance=direction.length
        cam.data.dof.keyframe_insert('focus_distance',frame=frame)
        scale = direction.length*24/lens/10
        key(hud,'scale',frame,(scale,)*3)
        key(hud,'location',frame,(0,0,-direction.length+scale))
    for curve in cam.data.animation_data.action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation='CONSTANT'
    # Keep the screen graphics independent of both focus and world geometry.
    overlay = bpy.data.scenes.new('Circle Challenge HUD pass')
    overlay.render.engine='BLENDER_EEVEE_NEXT'
    overlay.eevee.taa_render_samples=16
    overlay.render.film_transparent=True
    overlay.render.resolution_x=s.render.resolution_x
    overlay.render.resolution_y=s.render.resolution_y
    overlay.render.resolution_percentage=s.render.resolution_percentage
    overlay.frame_start=s.frame_start
    overlay.frame_end=s.frame_end
    overlay.collection.objects.link(cam)
    hud_cam=cam.copy()
    hud_cam.data=cam.data.copy()
    hud_cam.data.dof.use_dof=False
    overlay.collection.objects.link(hud_cam)
    overlay.camera=hud_cam
    overlay.collection.objects.link(hud)
    for card in hud.children:
        overlay.collection.objects.link(card)
        for collection in list(card.users_collection):
            if collection != overlay.collection:
                collection.objects.unlink(card)
    tree=s.node_tree
    composite=next(node for node in tree.nodes if node.type=='COMPOSITE')
    previous=composite.inputs['Image'].links[0].from_socket
    hud_pass=tree.nodes.new('CompositorNodeRLayers')
    hud_pass.scene=overlay
    over=tree.nodes.new('CompositorNodeAlphaOver')
    tree.links.new(previous,over.inputs[1])
    tree.links.new(hud_pass.outputs['Image'],over.inputs[2])
    tree.links.new(over.outputs['Image'],composite.inputs['Image'])
    # Load new cel art once, then pack. Each pose retains a dedicated texture.
    for image in bpy.data.images:
        if image.source!='FILE' or not image.filepath.endswith(('_body.png','_head.png')):
            continue
        path=Path(bpy.path.abspath(image.filepath))
        if path.is_file():
            if image.packed_file:
                image.unpack(method='REMOVE')
            image.reload()
            image.pack()
    for name in ('Chemical sphere SKATOLE','Chemical label SKATOLE'):
        objects[name].location.z-=.37
        objects[name].location.x+=.23
    ghost=objects['Rival ghost soul']
    for frame,scale in [(1539,.26),(1600,.65),(1614,.75)]:
        key(ghost,'scale',frame,(scale,)*3,'LINEAR')
    check=objects['Ignored cheque on grass']
    key(check,'location',2095,(1.2,-.6,.13))
    check.rotation_euler.x=.18
