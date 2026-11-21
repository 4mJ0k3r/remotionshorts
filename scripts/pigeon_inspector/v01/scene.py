"""Pose and camera bake for The Pigeon Inspector v01. Blender frames are one-based."""
import json
import math

import bpy
from mathutils import Euler, Vector

import assets
import ricks_camera as rc
import ricks_drawn_look as drawn
import ricks_v2_kit as kit


SIZE = (540,960)
END = 300
CUTS = (61,157,217)
PIN = 147
PECK = 160
PICKUP = 239
REST = (1.514,-.118,.009)
BIRD = (1.720,-.076,.205)
HOLE_LOCAL = Vector((*assets.HOLE[:2],0))
TRACK = rc.Track


def ease(f,a,b):
    return rc.ease5((f-a)/(b-a))


def loc(keys, mode="ease"):
    return TRACK(keys,mode)


def blend(a,b,t):
    return Vector(a).lerp(Vector(b),t)


def configure_camera():
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "Platform camera | four-shot edit"
    kit.setup_ricks_camera(camera, lens=28, fstop=5.6, clip_end=34)
    camera.data.clip_start = .028
    bpy.context.scene.camera = camera
    return camera


def card_air(f):
    position = AIR_POS(f)
    angles = AIR_ROT(f)
    if f >= 74:
        flutter = math.sin((f-74)*.61)*.040*(1-ease(f,101,140))
        angles = (flutter, angles[1], angles[2])
        position = (position[0],position[1],max(position[2],.003+.083*abs(math.sin(flutter))))
    return Vector(position),Euler(angles)


AIR_POS = loc([
    (48,(-.695,-.385,.980)),(53,(-.525,-.378,.90)),(61,(-.348,-.288,.36)),
    (70,(-.229,-.163,.058)),(75,(-.178,-.151,.011)),(96,(.266,-.119,.012)),
    (117,(.803,-.143,.010)),(137,(1.333,-.118,.009)),(145,(1.493,-.118,.009)),
    (PIN,REST),(300,REST),
],"carry")
AIR_ROT = loc([
    (48,(1.38,-.04,.06)),(53,(.76,.91,-.35)),(61,(.42,1.17,-.41)),
    (68,(.20,.47,-.22)),(74,(0,0,-.20)),(94,(0,0,.11)),(121,(0,0,-.074)),
    (140,(0,0,.036)),(PIN,(0,0,0)),
],"carry")
OPEN_CARD = loc([
    (1,(-.767,-.338,.763)),(21,(-.744,-.372,.928)),(34,(-.738,-.392,.945)),
    (48,(-.695,-.385,.980)),
])
OPEN_SPIN = loc([(1,(1.07,.15,-.20)),(24,(1.40,-.06,.05)),(48,(1.38,-.04,.06))])
HERO_ROUTE = loc([(79,(-1.00,-.04,0)),(105,(-.96,-.72,0)),(143,(.11,-.78,0)),
                  (182,(1.03,-.65,0)),(214,(1.30,.112,0))],"carry")
HERO_HEADING = loc([(79,-.02),(100,.29),(123,1.48),(162,1.55),(193,2.62),(214,.04)],"carry")
BIRD_PATH = loc([(181,BIRD),(194,(1.78,-.020,.205)),(206,(2.00,.012,.205)),
                 (218,(2.30,.057,.205)),(234,(2.94,.108,.205))],"carry")


def camera_program():
    rest_focus = (1.586,-.10,.13)
    landing_tilt = loc([(61,.242),(82,.113),(103,.106)])
    def card_subject(f):
        position,_ = card_air(f)
        return (position.x+.018,position.y,landing_tilt(f))
    anticipate = rc.lead(card_subject,frames=3,max_m=.10)
    pickup_aim = loc([(217,(1.457,-.10,.22)),(236,(1.45,-.153,.185)),
                      (249,(1.447,-.15,.48)),(266,(1.367,-.133,1.02)),
                      (281,(1.236,-.125,1.190)),(300,(1.236,-.125,1.190))],"carry")
    orbit = loc([(217,(1.439,-.78,.40)),(236,(1.462,-.78,.337)),
                (250,(1.46,-.92,.65)),(270,(1.37,-1.01,1.20)),
                (282,(1.239,-1.01,1.255)),(300,(1.239,-1.01,1.255))],"carry")
    return rc.CameraProgram([
        rc.Shot(1,60,name="Commuter and gust",
                pos=loc([(1,(-.73,-1.46,1.14)),(33,(-.84,-1.37,1.125)),
                         (48,(-.81,-1.40,1.10)),(60,(-.65,-1.42,.99))],"carry"),
                aim=loc([(1,(-.918,-.14,1.065)),(42,(-.922,-.17,1.073)),
                         (60,(-.803,-.19,.997))],"carry"), focus=(-.937,-.234,1.15),lens=28,fstop=5.6),
        rc.Shot(61,156,name="Under the bench",
                pos=loc([(61,(-.50,-.907,.423)),(77,(-.333,-.871,.357)),
                         (103,(.326,-.799,.281)),(124,(.858,-.755,.278)),
                         (143,(1.311,-.779,.308)),(156,(1.509,-.84,.353))],"carry"),
                aim=rc.handoff(anticipate,rest_focus,122,151),
                focus=rc.handoff(card_subject,rest_focus,126,153),lens=27,fstop=6.3),
        rc.Shot(157,216,name="Punch, inspect and strut",
                pos=loc([(157,(1.415,-.809,.455)),(168,(1.422,-.817,.473)),
                         (184,(1.469,-.862,.449)),(202,(1.648,-.952,.430)),(216,(1.739,-1.01,.426))],"carry"),
                aim=loc([(157,(1.646,-.078,.126)),(174,(1.646,-.086,.146)),
                         (194,(1.713,-.066,.147)),(206,(1.813,-.070,.155)),(216,(1.838,-.070,.151))],"carry"),
                focus=loc([(157,(1.57,-.12,.053)),(205,(1.55,-.116,.044))]),lens=loc([(157,31),(174,31),(205,26),(216,25)]),fstop=9),
        rc.Shot(217,300,name="Pickup and deadpan",pos=orbit,aim=pickup_aim,
                focus=loc([(217,(1.51,-.12,.025)),(240,(1.51,-.15,.045)),
                           (251,(1.48,-.22,.54)),(273,(1.34,-.125,1.265)),
                           (300,(1.34,-.125,1.265))],"carry"),lens=loc([(217,27),(262,28),(282,30)]),fstop=7.1),
    ])


def collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def set_keys(obj,frame,*props):
    for prop in props:
        obj.keyframe_insert(prop,frame=frame)


def make_linear(id_block):
    if id_block.animation_data and id_block.animation_data.action:
        for curve in id_block.animation_data.action.fcurves:
            for key in curve.keyframe_points:
                key.interpolation = "CONSTANT" if curve.data_path.startswith("hide_") else "LINEAR"


def bird_pose(f,root,head,collar,tip,feet):
    turn = math.pi*ease(f,180,195)
    stride = max(0,f-192)/7.5
    bob = .022*math.sin(math.tau*stride)*ease(f,191,197)*(1-ease(f,228,235))
    root.location = Vector(BIRD_PATH(f))+Vector((0,0,bob))
    root.rotation_euler.z = turn
    head_local = loc([(1,(-.137,0,.128)),(143,(-.143,-.011,.112)),
                      (155,(-.125,-.012,.147)),(160,(-.086,-.045,-.100)),
                      (168,(-.145,-.020,.112)),(181,(-.132,-.004,.144)),
                      (195,(-.136,0,.139))])(f)
    head.location = Vector(head_local)+Vector((.034*math.sin(math.tau*stride)*ease(f,193,200),0,0))
    head.rotation_euler.y = -.77*ease(f,155,160)*(1-ease(f,160,167))
    if PECK-1 <= f <= PECK+1:
        # Snap the strike through the actual opening in the card mesh.
        target = Vector(REST)+HOLE_LOCAL+Vector((0,0,-.002+abs(PECK-f)*.030))
        head.location = target-root.location-head.rotation_euler.to_matrix() @ tip
    set_keys(root,f,"location","rotation_euler")
    set_keys(head,f,"location","rotation_euler")
    base = Vector((-.103,-.005,.025))
    shoulder_to_head = head.location-base
    collar.location = base.lerp(head.location,.48)
    collar.rotation_mode = "QUATERNION"
    collar.rotation_quaternion = shoulder_to_head.to_track_quat("Z","Y")
    collar.scale = (1,.92,(shoulder_to_head.length+.065)/.184)
    set_keys(collar,f,"location","rotation_quaternion","scale")
    for i,(foot,shanks) in enumerate(feet):
        side = (-1,1)[i]
        if i == 0:
            toe = Vector(loc([(1,(1.676,-.138,0)),(137,(1.676,-.138,0)),
                              (142,(1.667,-.166,.055)),(PIN,(1.584,-.182,.011)),
                              (181,(1.584,-.182,.011)),(189,(1.818,-.068,0))])(f))
        else:
            toe = Vector((1.712,-.009,0))
        foot_turn = turn
        if f >= 190:
            offset = 190-i*4
            strike = offset+8*math.floor((f-offset)/8)
            phase = max(0,(f-strike-3)/5)
            a,b = (Vector(BIRD_PATH(g+3)) for g in (strike,strike+8))
            toe = a.lerp(b,rc.ease5(phase))
            toe += Vector((.030,side*.055,-.205+.058*math.sin(math.pi*phase)))
            foot_turn = math.pi
        foot.location,foot.rotation_euler.z = toe,foot_turn
        hip = root.location + root.rotation_euler.to_matrix() @ Vector((-.037,side*.062,-.078))
        knuckle = toe+Vector((0,0,.018))
        joint = hip.lerp(knuckle,.62)+Vector((.016,0,.005))
        for shank,a,b in zip(shanks,(hip,joint),(joint,knuckle)):
            axis = b-a
            shank.location = a.lerp(b,.5)
            shank.rotation_mode = "QUATERNION"
            shank.rotation_quaternion = axis.to_track_quat("Z","Y")
            shank.scale.z = axis.length*.5+.007
            set_keys(shank,f,"location","rotation_quaternion","scale")
        set_keys(foot,f,"location","rotation_euler")


def hero_pose(f,hero,hands):
    crouch = ease(f,212,234)*(1-ease(f,239,262))
    attention = ease(f,40,57)*(1-ease(f,73,94))
    place = Vector(HERO_ROUTE(f))
    walking = ease(f,79,91)*(1-ease(f,200,214))
    yaw = HERO_HEADING(f)+.16*attention-.065*crouch
    tilt, bounce = .04+.64*crouch+.17*attention, -.348*crouch
    neck_pitch = -.22*ease(f,4,25)+.34*attention+.19*crouch+.20*ease(f,255,281)
    neck_yaw = .27*attention-.08*ease(f,266,283)
    left = Vector((-.205,-.16,.18))
    right = Vector((.165,-.078,.085))
    elbows = [Vector((-.189,-.071,.225)),Vector((.173,-.029,.204))]
    legs = [((s*.107,-.032,.027),(s*.101,-.069-.20*crouch,.317-.117*crouch)) for s in (-1,1)]
    if 84 <= f <= 214:
        gait = kit.eval_stick_walk_cycle(f,HERO_ROUTE,yaw,start_frame=84,stop_frame=214,
                                        plant_yaw=HERO_HEADING,strength=walking)
        legs = [(blend(a,b,walking),blend(c,d,walking)) for (a,c),(b,d) in zip(legs,gait.legs)]
        left,right = [blend(a,b[0],walking) for a,b in zip((left,right),gait.arms)]
        elbows = [blend(a,b[1],walking) for a,b in zip(elbows,gait.arms)]
        tilt += gait.tilt
        bounce += gait.bounce
    body_rot = Euler((tilt,0,yaw)).to_matrix()
    # Keep the inverse transform identical to the rig's yaw-then-local-tilt chain.
    body_base = place+Vector((0,0,.59+bounce))
    head_rot = body_rot @ Euler((neck_pitch,0,neck_yaw)).to_matrix()
    head_center = body_base+body_rot @ Vector((0,0,kit.FACE_CENTER-.59))
    gap = .001
    if f <= 48:
        card,rot = Vector(OPEN_CARD(f)),Euler(OPEN_SPIN(f))
        gap = .017*ease(f,45,49)
    elif f < PICKUP:
        card,rot = card_air(f)
    else:
        settle = ease(f,257,281)
        eye = head_center+head_rot @ Vector((-.096,-.201,-.002))
        eye_card = eye+Vector((.020,-.078,-.005))
        lift = ease(f,PICKUP,269)
        rot = Euler((1.49*lift,-.18*lift,-.095*lift))
        destination = eye_card-rot.to_matrix() @ HOLE_LOCAL
        card = blend(REST,destination,lift)
        card.z += .040*math.sin(math.pi*lift)
        card.x += .035*math.sin(math.pi*lift)*(1-settle)

    grasp = card+rot.to_matrix() @ assets.GRIP
    pad = Vector((.044,.006,0))
    if f <= 48 or f >= PICKUP:
        left_rot = rot.copy()
        wrist = grasp-left_rot.to_matrix() @ pad
    elif f <= 84:
        frac = ease(f,48,79)
        left_rot = Euler((1.38-.83*frac,-.04-.54*frac,.06+.35*frac))
        last = Vector(OPEN_CARD(48))+Euler(OPEN_SPIN(48)).to_matrix() @ (assets.GRIP-pad)
        wrist = blend(last+Vector((.056*ease(f,48,57),-.014,0)),body_base+body_rot @ left,frac)
        gap = .021*(1-frac)
    elif f >= 217:
        left_rot = Euler((.58*(1-ease(f,217,235)),-.24*(1-ease(f,217,235)),0))
        reach = ease(f,217,PICKUP)
        wrist = blend(body_base+body_rot @ Vector((-.18,-.31,-.010)),grasp-pad,reach)
        wrist.z += .09*math.sin(math.pi*reach)
        gap = .030*ease(f,216,228)*(1-ease(f,234,PICKUP))
    else:
        left_rot = Euler((.55,-.58,yaw+.42))
        wrist = body_base+body_rot @ left
    left = body_rot.inverted() @ (wrist-body_base)
    if f <= 80 or f >= 216:
        elbows[0] = Vector((-.184,-.071,.214)).lerp(
            Vector((-.179,-.166,.205)),.56*ease(f,215,235)*(1-ease(f,241,275)))
        if f >= 245:
            elbows[0] = blend(elbows[0],(-.209,-.141,.314),ease(f,245,276))

    expr = {1:"reading",45:"gust",61:"following",217:"reach",259:"inspect",282:"deadpan"}.get(f)
    hero.pose(f,place,yaw,tilt,[(left,elbows[0]),(right,elbows[1])],legs,expr,
              bounce=bounce,head_tilt=neck_pitch,head_yaw=neck_yaw)
    hand,index,thumb = hands[0]
    hand.location, hand.rotation_euler = wrist,left_rot
    index.location.z = .0132+gap
    thumb.location.z = -.0132-gap*.74
    set_keys(hand,f,"location","rotation_euler")
    for item in (index,thumb):
        set_keys(item,f,"location")
    spare = hands[1][0]
    spare.location = body_base+body_rot @ right
    spare.rotation_euler = (.61,-.72,yaw-.82)
    set_keys(spare,f,"location","rotation_euler")
    return card,rot,grasp


def bake(out):
    import shorts_preflight as preflight
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.name = "The Pigeon Inspector | v01"
    kit.configure_ricks_scene(scene,width=SIZE[0],height=SIZE[1],fps=30,frame_end=END,samples=6)
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGB"
    scene.render.filepath = "//frames/frame_"
    bpy.context.preferences.filepaths.save_version = 0
    camera = configure_camera()
    kit.setup_ricks_compositor(scene,camera=camera)
    scene.world = bpy.data.worlds.new("Station ambient")
    scene.world.color = (.21,.23,.26)
    assets.platform(collection("01 | Station architecture"))
    hero,hands = assets.commuter(collection("02 | Commuter and pinch rig"))
    paper,plug = assets.ticket(collection("03 | Ticket geometry"))
    bird,head,collar,tip,feet = assets.pigeon(collection("04 | Pigeon, stride and peck"))
    program = camera_program()
    focus = kit.empty("Camera | focus handoff",scene.collection)
    kit.apply_portrait_dof(camera,focus,fstop=5.6)
    q, checks = None,[]
    for f in program.frames:
        scene.frame_set(f)
        card,rot,grasp = hero_pose(f,hero,hands)
        paper.location,paper.rotation_euler = card,rot
        set_keys(paper,f,"location","rotation_euler")
        if f in (1,PECK):
            plug.hide_render = plug.hide_viewport = f == PECK
            set_keys(plug,f,"hide_render","hide_viewport")
        bird_pose(f,bird,head,collar,tip,feet)
        q = rc.key_camera(camera,program.evaluate(f),f,focus,q)
        bpy.context.view_layer.update()
        drawn.update_ink(hero,camera,pixels=3.55,frame=f)
        if f in (34,48,PIN,PECK,PICKUP,248,280):
            anchors = drawn.contact_anchors(hero)
            wrist = hands[0][0].matrix_world
            row = {"frame":f,"time_seconds":round((f-1)/30,4),
                   "hand_anchor_error_m":round((anchors["hand_L"]-wrist.translation).length,7)}
            if f in (34,48,PICKUP,248,280):
                center = wrist @ Vector((.044,.006,0))
                row["pinch_midpoint_error_m"] = round((grasp-center).length,7)
                for label,part in zip(("index","thumb"),hands[0][1:]):
                    local = paper.matrix_world.inverted() @ part.matrix_world.translation
                    row[label+"_surface_gap_m"] = round(abs(local.z)-.0105-.0026,7)
            if f == PIN:
                # The middle forward toe lies within the rectangle on its upper plane.
                toe = feet[0][0].matrix_world @ Vector((-.051,0,.007))
                local = paper.matrix_world.inverted() @ toe
                row["pin_toe_ticket_local_m"] = list(local)
                row["pin_toe_surface_gap_m"] = round(local.z-.007-.0026,7)
            if f == PECK:
                row["peck_tip_to_hole_m"] = round((head.matrix_world @ tip
                     - paper.matrix_world @ HOLE_LOCAL).length,7)
            checks.append(row)
    hero.finish_bake()
    for obj in bpy.data.objects:
        make_linear(obj)
        if obj.data:
            make_linear(obj.data)
    for frame,label in ((1,"01 | Ticket in hand"),(48,"Gust separates fingers"),(61,"02 | Under the bench"),
                        (PIN,"Foot pins ticket"),(157,"03 | Cut on the peck"),(PECK,"Hole opens"),
                        (217,"04 | Retrieve"),(PICKUP,"Pinch closes"),(282,"Deadpan")):
        scene.timeline_markers.new(label,frame=frame)
    bpy.ops.file.pack_all()
    scene.frame_set(1)
    camera.select_set(True)
    bpy.context.view_layer.objects.active = camera
    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == "VIEW_3D":
                area.spaces.active.region_3d.view_perspective = "CAMERA"
    resources = preflight.validate_resources(scene)
    print("ASSETS", json.dumps(resources), flush=True)
    cuts = [f-1 for f in program.cuts]
    shot_edges = [0,*cuts,END]
    shots = [{"id":s.name,"a":a,"b":b} for s,a,b in zip(program.shots,shot_edges,shot_edges[1:])]
    for name,value in {
        "cuts.json":{"cuts":cuts,"cut_seconds":[f/30 for f in cuts]},
        "shots.json":{"schema":1,"shots":shots,"cuts":cuts,"continuous_junctions":[],"transitions":[],
                      "xfade":[],"action_ranges":[[43,60],[60,147],[153,167],[178,213],[218,281]],
                      "calibration_frames":[0,32,47,81,116,146,156,159,169,224,238,288],
                      "mad_ratio":3,"mad_floor":1,"mad_absolute":12},
        "contact_checks.json":{"contacts":checks,"resources":resources},
    }.items():
        (out/name).write_text(json.dumps(value,indent=2),encoding="utf-8")
    bpy.ops.wm.save_as_mainfile(filepath=str(out/"pigeon_inspector_v01.blend"))
