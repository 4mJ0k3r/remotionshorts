"""Neckless stick-hybrid rigs, baked control curves, and conformed art."""
import math

from mathutils import Euler, Vector

from model import artwork, ball, empty, mesh, outline, skin, surface, tube, tube_pose

HEAD = (.24, .2112, .2256)
FACE_CENTER = 1.237
TORSO_CENTER = .831
RING = 48


def decal(name, col, parent, mat, half, center, radii):
    width, height = half
    nx, nz = 31, 29
    verts, faces, uv = [], [], []
    for j in range(nz):
        v = j/(nz-1)
        z = (2*v-1)*height
        for i in range(nx):
            u = i/(nx-1)
            x = (2*u-1)*width
            center_z = z + center
            if radii == HEAD:
                curve = (center_z/radii[2])**2
            else:
                curve = (max(0, abs(z)-.102)/.128)**2
            y = -radii[1]*math.sqrt(max(.035, 1-(x/radii[0])**2-curve))-.0033
            verts.append((x, y, center_z))
            uv.append((u, v))
            if i and j:
                k = len(verts)-1
                faces.append((k-nx-1,k-nx,k,k-1))
    obj = mesh(name, col, verts, faces, mat, parent, True, uv)
    obj.visible_shadow = False
    return obj


def scalp(name, col, head, mat):
    verts, faces = [], []
    for j in range(14):
        for i in range(RING):
            a = math.tau*i/RING
            front = max(0., -math.sin(a))
            contour = 1.87-.60*front + .12*math.sin(7*a+.5) + .08*math.sin(11*a)
            polar = .012+(contour-.012)*j/13
            verts.append((.251*math.sin(polar)*math.cos(a), .221*math.sin(polar)*math.sin(a)+.012,
                          .246*math.cos(polar)+.017))
            if j:
                k, nxt = j*RING+i, j*RING+(i+1)%RING
                faces.append((k-RING,k,nxt,nxt-RING))
    faces.extend((tuple(reversed(range(RING))), tuple(range(13*RING,14*RING))))
    return mesh(name, col, verts, faces, mat, head, True)


def hood(col, head, mat, seam):
    verts, faces = [], []
    rings = [(1.0,-.225,.025),(1.095,-.235,.028),(1.20,-.16,.038),(1.245,-.038,.046),
             (1.18,.10,.051),(.86,.218,.069),(.30,.251,.073),(.03,.264,.073)]
    for j,(radius, y, z) in enumerate(rings):
        for i in range(RING):
            a = math.tau*i/RING
            brow = max(0,math.sin(a))*(1-j/7)**2
            verts.append((.211*radius*math.cos(a),y-.17*brow,
                          z+.205*radius*math.sin(a)-.044*brow))
            if j:
                k, nxt = j*RING+i,j*RING+(i+1)%RING
                faces.append((k-RING,k,nxt,nxt-RING))
    faces.append(tuple(reversed(range(7*RING,8*RING))))
    obj = mesh("Broker | overhanging wool hood", col, verts, faces, mat, head, True)
    lip = [verts[i] for i in range(RING)] + [verts[0]]
    tube("Broker | roll of hood opening", col, lip[::2]+[lip[-1]], .010, seam, head)
    return obj


class Actor:
    def __init__(self, name, col, broker=False):
        self.name = name
        self.root = empty(name, col)
        self.body = empty(name+" | body control", col, (0,0,.59), self.root)
        self.head = empty(name+" | head control", col, (0,0,FACE_CENTER-.59), self.body)
        self.ink_modifiers = []
        ink = surface(name+" | matte stick ink", "#0A0A0E", .91)
        shader = next(node for node in ink.node_tree.nodes if node.type=="BSDF_PRINCIPLED")
        shader.inputs["Specular IOR Level"].default_value = .025
        tone = "#E8EAF2" if broker else "#F7F3EA"
        stops = ([(.025,"#11182B"),(.34,"#343954"),(.92,"#EAB66E")] if broker
                 else [(.025,"#414A80"),(.39,"#BEC4DF"),(.90,"#FFF3DC")])
        face = ball(name+" | ellipsoid head",col,(0,0,0),HEAD,skin(name+" | lit cel face",tone,stops),
                    self.head,48,32)
        self.ink_modifiers.append(outline(face,col))
        jacket = surface(name+" | costume", "#181A28" if broker else "#E5A928", .79, glow=.045)
        torso = ball(name+" | graphic pill torso",col,(0,0,TORSO_CENTER-.59),(.125,.085,.128),
                     jacket,self.body,48,32,stretch=.102)
        self.ink_modifiers.append(outline(torso,col))
        tuft = surface(name+" | silhouette cloth or layered chestnut", "#262944" if broker else "#542C24",.69,
                       glow=.042)
        accent = surface(name+" | hand-painted warm edging", "#424667" if broker else "#90543A",.72,glow=.14)
        if broker:
            cap = hood(col,self.head,tuft,accent)
            tube("Broker | piped cloak fold",col,[(-.058,-.076,.23),(.04,-.09,.18),(.078,-.067,.098)],
                 .008,accent,self.body)
            ball("Broker | antique closure",col,(.032,-.093,.30),(.02,.007,.02),accent,self.body,12,10)
        else:
            cap = scalp(name+" | shaped hair cap",col,self.head,tuft)
            for stripe in range(3):
                points = []
                for i in range(16):
                    a = 3.34+.078*i
                    polar = .80+.12*stripe+.053*math.sin(i/8)
                    points.append((.254*math.sin(polar)*math.cos(a),.225*math.sin(polar)*math.sin(a)+.012,
                                   .249*math.cos(polar)+.017))
                tube(name+" | brushed highlight",col,points,.0045-.0006*stripe,accent,self.head)
            mat, _ = artwork("jacket", glow=.23)
            decal(name+" | painted jacket, lanyard and badge", col, self.body, mat, (.102,.195),
                  TORSO_CENTER-.59,(.125,.085,.128))
        self.ink_modifiers.append(outline(cap,col))
        self.expressions = {}
        names = (("broker_neutral","broker_creepy_grin") if broker else
                 ("suspicious","excited_awe","smug_focus","sneaky","shock_terror"))
        for expr in names:
            mat, _ = artwork(expr, glow=1.2 if broker else .65)
            self.expressions[expr] = decal(name+" | "+expr,col,self.head,mat,(.175,.141),
                                           .013 if broker else -.024,HEAD)
        self.arms, self.legs, self.hands, self.feet = [],[],[],[]
        for side in (-1,1):
            side_name = "L" if side < 0 else "R"
            self.arms.append(tube(name+" | stick arm "+side_name,col,[(side*.11,0,.36),(side*.18,-.04,.24),
                                                                   (side*.21,-.16,.21)],.015,ink,self.body))
            self.hands.append(ball(name+" | dot hand "+side_name,col,(0,0,0),(.022,)*3,ink,self.body,14,10))
            self.legs.append(tube(name+" | stick leg "+side_name,col,[(side*.058,0,.65),(side*.084,-.04,.33),
                                                                   (side*.12,0,.029)],.015,ink,self.root))
            self.feet.append(ball(name+" | foot tick "+side_name,col,(0,0,0),(.027,.035,.017),
                                  ink,self.root,14,10))
        self.sweat = None
        if not broker:
            blue = surface(name+" | comic sweat cyan", "#51C8F2", .22, glow=.62)
            self.sweat = mesh(name+" | temple tear",col,
                              [(0,0,.046),(-.016,0,.014),(-.019,0,-.004),(-.013,0,-.021),
                               (0,0,-.025),(.014,0,-.019),(.019,0,-.004),(.014,0,.014)],
                              [(0,1,2,3,4,5,6,7)],blue,self.head)
            self.sweat.visible_shadow = False

    def display(self, expression, frame):
        if not expression or getattr(self,"last_expression",None) == expression:
            return
        self.last_expression = expression
        for name, obj in self.expressions.items():
            obj.hide_render = name != expression
            obj.hide_viewport = name != expression
            for channel in ("hide_render","hide_viewport"):
                obj.keyframe_insert(channel,frame=frame)

    def pose(self, frame, location, yaw, tilt, arms, legs, expression, *,
             bounce=0, head_tilt=0, head_yaw=0, squash=1, sweat=None):
        self.root.location, self.root.rotation_euler.z = location, yaw
        self.body.location.z, self.body.rotation_euler.x = .59+bounce, tilt
        self.body.scale.z = squash
        self.head.rotation_euler.x, self.head.rotation_euler.z = head_tilt, head_yaw
        for obj, channels in ((self.root,("location","rotation_euler")),
                              (self.body,("location","rotation_euler","scale")),
                              (self.head,("rotation_euler",))):
            for channel in channels:
                obj.keyframe_insert(channel,frame=frame)
        for i, side in enumerate((-1,1)):
            hand, elbow = arms[i]
            foot, knee = legs[i]
            tube_pose(self.arms[i],[(side*.106,-.003,.342),elbow,hand],frame)
            hip = (Euler((tilt,0,0)).to_matrix() @ Vector((side*.060,0,.070*squash))
                   + Vector((0,0,.59+bounce)))
            tube_pose(self.legs[i],[hip,knee,foot],frame)
            self.hands[i].location = hand
            self.hands[i].keyframe_insert("location",frame=frame)
            self.feet[i].location = Vector(foot)+Vector((0,-.021,-.010))
            self.feet[i].keyframe_insert("location",frame=frame)
        self.display(expression,frame)
        if self.sweat:
            self.sweat.hide_render = self.sweat.hide_viewport = sweat is None
            for prop in ("hide_render","hide_viewport"):
                self.sweat.keyframe_insert(prop,frame=frame)
            if sweat is not None:
                self.sweat.location = (-.162-.028*sweat,-.182+.026*sweat,.084-.078*sweat)
                self.sweat.rotation_euler.y = -.38
                self.sweat.keyframe_insert("location",frame=frame)
