"""Part 2: analysts, optical snap insert, and an escalating image-review alert."""
from staging import *

s,cam,F=opening(2)
m=palette()
room=group(s,"CIA console action",0)
c=room[0]
console(c,m)
crew=[actor(c,name,"analyst",small=True) for name in ("CIA Boss","CIA Analyst One","CIA Analyst Two")]
roots=[desk(c,m,x,y,rig.name) for (x,y),rig in zip(((0,.14),(-.93,.77),(.93,.81)),crew)]
glasses(c,crew[0],m["ink"])
for x,title in ((-.60,"KEYHOLE"),(.62,"ORBITAL IMAGING")):
    label(c,title,(x,2.130,2.982),.091,m["paper"])
label(c,"POKHRAN FEED",(0,2.126,2.405),.081,m["paper"])

lens=group(s,"Keyhole aperture and clock",24)
o=lens[0]
sat,scan,beam=orbit(o)
clock=k.empty("Graphic orbital clock",o,(.132,-.63,1.577))
ring=k.cylinder("Gold clock body",o,(0,0,0),.131,.039,m["wood"],clock,length_segments=32)
ring.rotation_euler.x=pi/2
for j in range(22):
    a=j*tau/22
    trace(o,"Engraved fine clock ticks",[(.091*sin(a),-.024,.091*cos(a)),(.119*sin(a),-.024,.119*cos(a))],
          .0038,m["paper"],clock)
hand=k.empty("Spinning clock hand",o,(0,-.028,0),clock)
trace(o,"Gold countdown hand",[(0,0,0),(.10,0,.016)],.008,m["red"],hand)
ring=oval(o,"Electronic aperture flare",0,-.675,-.06,.165,.165,m["cyan"],.011)
ring.parent=sat
for j in range(5):
    r=.155+j*.017
    oval(o,"Curved milled aperture groove",0,-.680,-.06,r,r,m["paper"] if j%2==0 else m["cyan"],
         .004).parent=sat
inside=k.emission("Tinted lens iris blade","#25354d")
for j in range(11):
    angle=j*tau/11
    points=[(.045,-.682,-.06),(.081,-.682,.027),(.149,-.682,-.020),(.133,-.682,-.076)]
    feature=k.empty("Dark optical iris blade",o,(0,0,-.06),sat)
    feature.rotation_euler.y=angle+.13
    vertices=[(x,y,z+.06) for x,y,z in points]
    k.mesh("Dark overlapping aperture blade",o,vertices,[(0,1,2,3)],inside,parent=feature)
    trace(o,"Machined blade edge",[(.049,-.684,.004),(.119,-.684,.057)],.0039,m["cyan"],feature)
surface_marks=Random(1245)
for index in range(174):
    x,z=surface_marks.uniform(-.292,.292),surface_marks.uniform(-.297,.297)
    if math.hypot(x,z+.06)>.23:
        trace(o,"Warm and dark camera casing hatch lines",[(x,-.355,z),(x+.018,-.355,z+.007)],.0031,
              m["ink"] if index%3 else m["paper"],sat)
photograms=[]
for j in range(2):
    card=k.empty("Desert negative print",o,(-.17+.26*j,-.682,1.18))
    box(o,"Framed aerial photo",(0,0,0),(.21,.020,.145),m["paper"],parent=card)
    box(o,"Photo warm soil", (0,-.011,0),(.179,.006,.111),m["wood"],parent=card)
    for row in range(6):
        trace(o,"Aerial strip pattern",[(q*.018-.077,-.016,.014*row-.037+.006*sin(row+q)) for q in range(9)],
              .0025,m["cyan"],card)
    photograms.append(card)

review=group(s,"Side-lit desert image review",48)
d=review[0]
console(d,m)
y=scan_panel(d,m,(.26,1.32,1.38),1.46,1.24)
label(d,"POKHRAN / IMAGE REVIEW",(.26,y-.006,1.893),.070,m["paper"])
label(d,"TIME INDEX / 00:04",(.26,y-.006,.848),.059,m["paper"])
reviewer=actor(d,"Nervous image analyst","analyst",small=True)
review_root=desk(d,m,-.46,.31,"Image review")
glasses(d,reviewer,m["ink"])
scope=k.empty("Moving image magnifier",d)
oval(d,"Circular magnification reticle",0,0,0,.136,.136,m["green"],.009).parent=scope
for a in (0,pi/2):
    trace(d,"Fine magnifier crosshair",[(-.18*cos(a),0,-.18*sin(a)),(.18*cos(a),0,.18*sin(a))],.004,m["green"],scope)

alert=group(s,"Crimson track alert",72)
a=alert[0]
console(a,m)
boss=actor(a,"Alert CIA boss","analyst",small=True)
root=desk(a,m,-.53,.30,"Alert console")
glasses(a,boss,m["ink"])
ya=scan_panel(a,m,(.37,1.39,1.40),1.53,1.30)
red=k.emission("Track lock bloom","#ff294c",1.4)
box(a,"Opaque red alert title background",(.37,ya-.022,1.70),(1.19,.030,.22),m["navy"])
label(a,"ALERT: TRACK DETECTED?",(.37,ya-.041,1.668),.064,m["paper"])
for sx in (-1,1):
    for sz in (-1,1):
        x=.38+sx*.30
        z=1.40+sz*.184
        trace(a,"Pulsing red target box",[(x-sx*.107,ya-.035,z),(x,ya-.035,z),(x,ya-.035,z-sz*.084)],.012,red)
red_socket=next(n for n in red.node_tree.nodes if n.type=="EMISSION").inputs[1]
refl=k.make_ricks_light("CRT red spill on glasses",a,(-.58,.20,1.61),(-.52,.77,1.45),"#ff283d",48,.44)

c1,c2,c3,c4,c5=map(F,(17.47,19.40,20.20,23.81,26.53))
snap1,snap2=F(19.6),F(19.87)
for f in range(1,s.frame_end+1):
    if f<c2:
        for j,(rig,seat) in enumerate(zip(crew,roots)):
            wave=sin(f*.47+j*1.8)
            point=ease(f,c1-9+j*3,c1+4+j*3)-ease(f,c1+19,c1+30)
            yaw=(-.12,.27,-.24)[j]
            tilt=.044+.025*wave
            left=grip(seat+Vector((-.16,-.384,.575+.022*(1+wave))),seat,yaw,tilt)
            right=grip(seat+Vector((.20+.12*point,-.38+.20*point,.57+.53*point)),seat,yaw,tilt)
            seated(rig,f,seat,yaw,tilt,[(left,(-.18,-.20,.20)),(right,(.21,-.14,.30))],
                   "rest",(.018*wave,-.12*point))
        if f<c1:
            camera_move(cam,f,room,1,c1-1,(-1.86,-3.11,2.03),(-1.60,-2.96,1.97),
                        (-.06,.59,1.34),(0,.55,1.36))
        else:
            camera_move(cam,f,room,c1,c2-1,(1.32,-2.69,1.87),(.96,-2.26,1.85),
                        (.25,.50,1.38),(.23,.58,1.42))
    elif f<c3:
        phase=ease(f,c2,c3-1)
        hand.rotation_euler.y=-1.7*pi*phase
        key(hand,f,"rotation_euler")
        pulse=sum(1 if snap<=f<snap+2 else .0001 for snap in (snap1,snap2))
        ring.scale=(pulse,)*3
        key(ring,f,"scale")
        aim_scan(beam,f,(0,-.44,1.30),(0,.8,-.14),1.15,.30)
        for card,shutter in zip(photograms,(snap1,snap2)):
            t=ease(f,shutter,shutter+7)
            card.scale=(.001+t,)*3
            card.location.z=1.16-.15*t
            key(card,f,"scale","location")
        camera_move(cam,f,lens,c2,c3-1,(-.10,-1.94,1.43),(-.04,-1.77,1.40),
                    (.02,-.48,1.39),(.048,-.48,1.39),52)
    elif f<c4:
        work=ease(f,c3,c4-1)
        lean=.09*work+.025*sin(f*.102)
        seated(reviewer,f,review_root,.38,lean,
               [((-.14,-.20,.24),(-.16,-.08,.23)),((.22,-.14,.34+.21*work),(.22,-.075,.28))],
               "rest",(.06,-.14*work))
        scope.location=(.1+.37*work,y-.016,1.39+.11*sin(work*pi))
        key(scope,f,"location")
        camera_move(cam,f,review,c3,c4-1,(-1.04,-1.92,1.70),(-.73,-1.65,1.59),
                    (-.06,.81,1.38),(-.06,.90,1.45))
    else:
        pulse=.55+.45*cos((f-c4)*.31) if f<s.frame_end-14 else .65
        red_socket.default_value=.9+1.56*pulse
        refl.data.energy=28+70*pulse
        key(red_socket,f,"default_value")
        key(refl.data,f,"energy")
        panic=ease(f,c5,c5+14)
        seated(boss,f,root,.30,.03-.10*panic,
               [((-.18,-.12,.23+.19*panic),(-.21,-.08,.29)),REST[1]],
               "EH" if f<c5+9 else "shock",(-.07*panic,.05))
        if f<c5:
            camera_move(cam,f,alert,c4,c4+12,(.81,-2.19,1.81),(.54,-1.68,1.61),
                        (.29,1.05,1.53),(.33,1.27,1.49))
        else:
            camera_move(cam,f,alert,c5,c5+34,(-1.19,-1.44,1.73),(-.95,-1.33,1.65),
                        (-.37,.80,1.47),(-.40,.76,1.49))

finish(s,2,[*crew,reviewer,boss],[(room,1,c2-1),(lens,c2,c3-1),(review,c3,c4-1),
       (alert,c4,s.frame_end)],[1,c1,c2,c3,c4,c5],
       [1,F(16.2),c1+7,c2,snap1,snap2,c3+15,F(22.85),c4+12,c5+12,F(27.7),s.frame_end])
