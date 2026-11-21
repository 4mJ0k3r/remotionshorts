"""Part 2: analog observation room and a close call on a CRT."""
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from hook_continuation import *
from sets import war_room

s, cam, start, stop = begin(2)
frame = lambda second: ftime(second)-start
m = palette()
control = group(s, "Satellite command room", 0)
c = control[0]
boss = styled(c, "Control room CIA boss", "analyst")
cup = war_room(c, boss)
root = Vector((.04,.48,.065))
for j in range(4):
    x = -.75+j*.45
    box(c,"Console terminal stand",(x,.73,.88),(.13,.15,.17),m["steel"],True)
for x in (-.82, .85):
    label(c,"ORBITAL IMAGING",(x,2.14,2.46),.064,m["paper"])
label(c,"POKHRAN",(-.62,.02,1.30),.090,m["paper"])
label(c,"KEYHOLE",(.48,.12,1.535),.078,m["paper"])
analysis = group(s,"Archival image alert terminal",20)
ac = analysis[0]
command_wall(ac,m)
y=scan_panel(ac,m,(.31,1.38,1.42),1.76,1.43)
label(ac,"POKHRAN / IMAGE REVIEW",(.31,y,2.02),.076,m["paper"])
marker = k.empty("Crimson headline and detection marker",ac)
for left in (-.18,.18):
    for bottom in (-.13,.13):
        x,z=.48+left,1.39+bottom
        trace(ac,"Red alert bracket",[(x-.073*math.copysign(1,left),y-.014,z),(x,y-.014,z),
          (x,y-.014,z-.067*math.copysign(1,bottom))],.012,m["red"],marker)
tag=label(ac,"ALERT",(.48,y-.013,1.205),.088,m["red"])
tag.parent=marker
glass = styled(ac,"Screen analyst","analyst")
glroot=Vector((-.25,.46,.145))
cut=frame(23.78)
for f in range(1,s.frame_end+1):
    if f<cut:
        point=push(f,frame(17.35),frame(17.6),frame(17.85),frame(19.62),frame(20.13))
        point+=.42*push(f,frame(21.2),frame(21.55),frame(21.75),frame(23.15),cut)
        yaw=.12-.45*ease(f,1,cut-1)
        tilt=.05+.1*point
        arms=[((-.228,-.13-.09*point,.275+.18*point),(-.232,-.04,.265)),
              ((.208,-.17,.24),(.247,-.09,.27))]
        pose(boss,f,root,yaw,tilt,arms,"rest",(-.13,.07*point),desk_legs())
        mug_grip(cup,boss,f,root,yaw,tilt,0)
        camera_move(cam,f,control,1,cut-1,(-1.13,-2.20,1.60),(1.14,-1.93,1.71),
                    (-.16,.38,1.39),(.10,.54,1.49))
    else:
        alert=frame(25.23)
        amount=1+.018*math.sin((f-alert)*.26)*math.exp(-max(0,f-alert)*.058)
        marker.hide_render=f<alert
        marker.hide_viewport=f<alert
        marker.location=((1-amount)*.48,(1-amount)*y,(1-amount)*1.39)
        marker.scale=(amount,1,amount)
        key(marker,f,"hide_render","hide_viewport","location","scale")
        lean=.11*ease(f,cut,alert+5)
        pose(glass,f,glroot,.35,lean,REST,"rest" if f<alert else "EH",(.08,-.19),desk_legs())
        camera_move(cam,f,analysis,cut,cut+12,(.73,-2.31,1.65),(.34,-1.52,1.58),
                    (.13,1.12,1.45),(.14,1.30,1.45))
close(s,2,[boss,glass],[(control,1,cut-1),(analysis,cut,s.frame_end)],
      [1,cut],[1,frame(17.9),frame(20.05),frame(22.98),cut+12,frame(25.85),s.frame_end])
