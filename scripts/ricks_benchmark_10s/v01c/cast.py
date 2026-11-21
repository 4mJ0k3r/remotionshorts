"""Neckless stick-hybrid rigs, baked control curves, and conformed art."""
import math

from mathutils import Euler, Vector

from model import artwork, ball, emission, empty, mesh, outline, skin, surface, tube, tube_pose

HEAD = (.24, .2112, .2256)
FACE_CENTER = 1.237
TORSO_CENTER = .831
RING = 48


def pose_arm(arm, shoulder, elbow, hand, frame):
    shoulder, elbow, hand = map(Vector,(shoulder,elbow,hand))
    upper = (elbow-shoulder).normalized()
    lower = (hand-elbow).normalized()
    turn = (upper+lower).normalized()
    positions = (shoulder,elbow,hand,hand+lower*.009,hand+lower*.016)
    tangents = (upper,turn,lower,lower,lower)
    # Key the handles as well as the knots. Auto handles left at a later pose
    # can jut past a moving elbow or curl a short tip back on itself.
    for i,(point,knot,tangent) in enumerate(zip(arm.data.splines[0].bezier_points,positions,tangents)):
        rest = len(positions)-1
        left = (knot-positions[i-1]).length/3 if i else 0
        right = (positions[i+1]-knot).length/3 if i<rest else 0
        if i==1:
            left=right=.29*min((elbow-shoulder).length,(hand-elbow).length)
        point.co = knot
        point.handle_left_type = point.handle_right_type = "FREE"
        point.handle_left = knot-tangent*left
        point.handle_right = knot+tangent*right
        for channel in ("co","handle_left","handle_right"):
            arm.data.keyframe_insert(f"splines[0].bezier_points[{i}].{channel}",frame=frame)


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


def hood(col, head, cloth, lining):
    verts, faces = [], []
    # Width, depth, top and hem for the lining, folded lip and outer cloth.
    # The narrow upper opening and flared lower panels create a bell profile.
    rings = [
        (.223,-.137,.185,-.205), (.225,-.247,.186,-.230),
        (.237,-.260,.194,-.246), (.255,-.228,.229,-.266),
        (.275,-.173,.279,-.287), (.285,-.090,.313,-.294),
        (.277,.014,.327,-.296), (.254,.109,.310,-.285),
        (.205,.186,.267,-.253), (.110,.244,.191,-.165),
        (.028,.268,.066,-.032), (.006,.274,.026,.010),
    ]
    for j,(width,y,top,hem) in enumerate(rings):
        for i in range(RING):
            a = math.tau*i/RING
            h = math.sin(a)
            brow = max(0,h)
            fall = max(0,-h)
            shoulder = 1-.22*brow+.23*fall
            drape = max(0,1-abs(j-5)/5)
            ripple = .018*drape*math.cos(6*a+.7)
            x = math.cos(a)*(width*shoulder+ripple)
            z = top*brow**.79+hem*fall**1.20 + .025*(1-abs(h))
            depth = y-(.093*brow**2+.027*fall)*max(0,1-j/8)
            depth += drape*.017*math.sin(5*a+.33)
            verts.append((x,depth,z))
            if j:
                k, nxt = j*RING+i,j*RING+(i+1)%RING
                faces.append((k-RING,k,nxt,nxt-RING))
    faces.append(tuple(reversed(range((len(rings)-1)*RING,len(verts)))))
    obj = mesh("Broker | draped pointed wool hood",col,verts,faces,cloth,head,True)
    obj.data.materials.append(lining)
    for panel in obj.data.polygons[:2*RING]:
        panel.material_index = 1
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
        face_material = skin(name+" | lit cel face",tone,stops,hood_shadow=broker)
        face = ball(name+" | ellipsoid head",col,(0,0,0),HEAD,face_material,
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
            lining = surface("Broker | matte black-indigo lining", "#0B0D18", .96, glow=.13)
            cap = hood(col,self.head,tuft,lining)
            tube("Broker | piped cloak fold",col,[(-.058,-.076,.23),(.04,-.09,.18),(.078,-.067,.098)],
                 .008,accent,self.body)
            ball("Broker | antique closure",col,(.032,-.093,.30),(.02,.007,.02),accent,self.body,12,10)
        else:
            cap = scalp(name+" | shaped hair cap",col,self.head,tuft)
            for stripe,(start,length,base,arc) in enumerate((
                (3.43,1.17,.87,.20), (3.49,.88,1.031,.22), (3.73,.61,1.137,.13)
            )):
                points = []
                for i in range(15):
                    t = i/14
                    a = start+length*t
                    polar = base-.26*t-arc*math.sin(math.pi*t)
                    points.append((.2525*math.sin(polar)*math.cos(a),.2225*math.sin(polar)*math.sin(a)+.012,
                                   .248*math.cos(polar)+.017))
                stroke = tube(name+" | swept chestnut highlight",col,points,.008-.0014*stripe,accent,self.head)
                for i,point in enumerate(stroke.data.splines[0].bezier_points):
                    point.radius = .09+.91*math.sin(math.pi*i/14)**.88
            mat, _ = artwork("jacket", glow=.23)
            decal(name+" | painted jacket, lanyard and badge", col, self.body, mat, (.102,.195),
                  TORSO_CENTER-.59,(.125,.085,.128))
        hull = outline(cap,col)
        self.ink_modifiers.append(hull)
        if not broker:
            for mesh_obj in (cap,hull.id_data):
                smooth = mesh_obj.modifiers.new("Smooth crown","SUBSURF")
                smooth.levels = smooth.render_levels = 2
                if mesh_obj != cap:
                    mesh_obj.modifiers.move(1,0)
        self.expressions = {}
        names = (("broker_neutral","broker_creepy_grin") if broker else
                 ("suspicious","excited_awe","smug_focus","sneaky","shock_terror"))
        for expr in names:
            mat, _ = artwork(expr, glow=1.2 if broker else .65)
            self.expressions[expr] = decal(name+" | "+expr,col,self.head,mat,(.175,.141),
                                           .013 if broker else -.024,HEAD)
        self.arms, self.legs, self.feet = [],[],[]
        for side in (-1,1):
            side_name = "L" if side < 0 else "R"
            end = Vector((side*.21,-.16,.21))
            arc = tube(name+" | round-tipped arm "+side_name,col,
                       [(side*.11,0,.36),(side*.18,-.04,.24),end,end+Vector((0,-.009,0)),
                        end+Vector((0,-.016,0))],.015,ink,self.body)
            for point,radius in zip(arc.data.splines[0].bezier_points,(1,1,1.1,.82,.015)):
                point.radius = radius
            self.arms.append(arc)
            self.legs.append(tube(name+" | stick leg "+side_name,col,[(side*.058,0,.65),(side*.084,-.04,.33),
                                                                   (side*.12,0,.029)],.015,ink,self.root))
            self.feet.append(ball(name+" | foot tick "+side_name,col,(0,0,0),(.027,.035,.017),
                                  ink,self.root,14,10))
        self.sweat = None
        if not broker:
            blue = surface(name+" | comic sweat cyan", "#51C8F2", .42, glow=.66)
            border = emission(name+" | comic sweat ink", "#0A0A0E", .85)
            contour = [(0,.033),(-.007,.024),(-.015,.013),(-.019,.002),(-.019,-.009),
                       (-.014,-.017),(-.006,-.022),(.005,-.022),(.014,-.018),(.019,-.011),
                       (.020,-.002),(.016,.008),(.007,.020)]
            outer = [(x,0,z) for x,z in contour]
            inner = [(x*.77,-.0008,z*.84-.0005) for x,z in contour]
            count = len(outer)
            strips = [(i,(i+1)%count,(i+1)%count+count,i+count) for i in range(count)]
            self.sweat = mesh(name+" | outlined temple drop",col,outer+inner,
                              [*strips,tuple(range(count,2*count))],border,self.head)
            self.sweat.data.materials.append(blue)
            self.sweat.data.polygons[-1].material_index = 1
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
            pose_arm(self.arms[i],(side*.106,-.003,.342),elbow,hand,frame)
            hip = (Euler((tilt,0,0)).to_matrix() @ Vector((side*.060,0,.070*squash))
                   + Vector((0,0,.59+bounce)))
            tube_pose(self.legs[i],[hip,knee,foot],frame)
            self.feet[i].location = Vector(foot)+Vector((0,-.021,-.010))
            self.feet[i].keyframe_insert("location",frame=frame)
        self.display(expression,frame)
        if self.sweat:
            self.sweat.hide_render = self.sweat.hide_viewport = sweat is None
            for prop in ("hide_render","hide_viewport"):
                self.sweat.keyframe_insert(prop,frame=frame)
            if sweat is not None:
                x,z = -.122-.024*sweat,.081-.060*sweat
                y = -HEAD[1]*math.sqrt(1-(x/HEAD[0])**2-(z/HEAD[2])**2)
                self.sweat.location = (x,y-.008,z)
                self.sweat.rotation_euler = (.10, -.24, -.44)
                self.sweat.keyframe_insert("location",frame=frame)
