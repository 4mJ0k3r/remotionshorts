"""Cemetery, lonely walk, roadside memorial, and settled fade."""
import math
from pathlib import Path
import sys

HERE=Path(__file__).resolve().parent
sys.path[:0]=[str(HERE),str(HERE.parent)]

import bpy
from mathutils import Vector
from feature_scene import (act, block, clock, ease, fade_to_black, figure, finish, glide, k,
                           line, make_scene, route, stage, street, view, walk)
from sets import cemetery, spray

F=clock(4)


def empty_overcast_street(collection, mats):
    car,_=street(collection,mats)
    parked=next(obj for obj in collection.objects if obj.name.startswith("Parked dusty-blue car"))
    for root in (car,parked):
        for child in reversed(tuple(root.children_recursive)):
            bpy.data.objects.remove(child,do_unlink=True)
        bpy.data.objects.remove(root,do_unlink=True)
    for obj in collection.objects:
        if obj.type=="LIGHT":
            obj.data.color=k.look.rgba("#bac8dd")[:3]
            obj.data.energy*=.50
            if obj.data.type=="SUN":
                obj.data.angle=.24
                obj.data.use_shadow=False
    sky=next(obj for obj in collection.objects if obj.name.startswith("Continuous surrounding"))
    ramp=next(n.color_ramp for n in sky.data.materials[0].node_tree.nodes if n.type=="VALTORGB")
    for swatch,color in zip(ramp.elements,("#aaaeb8","#aebbcf","#8298ae","#688397")):
        swatch.color=k.look.rgba(color)


def memorial(c,m):
    grey=k.surface("Quiet galvanized crossing railing","#728594",.62,.24)
    for j in range(10):
        x=.43+(j-4.5)*.143
        line(c,"Upright of crosswalk safety railing",[(x,1.14,.10),(x,1.14,.88)],.017,grey)
    for z in (.24,.70,.89):
        line(c,"Horizontal grey pedestrian railing",[(-.24,1.14,z),(1.11,1.14,z)],.023,grey)
    for x in (-.249,1.117):
        line(c,"Grounded monument rail post",[(x,1.14,-.02),(x,1.14,.98)],.030,grey)
    for x,y,tilt,s,z in ((.29,1.055,-.41,.81,.614),(.50,1.05,.47,.71,.60),(.59,1.036,.20,.63,.647)):
        bouquet=spray(c,m,"Pale blue ribbon tied to the railing",(x,y,z),s,tilt)
        bouquet.rotation_euler.x=-.30
    for j in range(8):
        block(c,"Weathered white crossing mark",(.44,1.43+j*.134,.005),(.90,.080,.01),m["cream"])


def main():
    s,cam,m,length=make_scene(4,"Shoko Part 4")
    grave=stage(s,"Warm dappled cemetery",0)
    suburban=stage(s,"Cool desaturated neighborhood with memorial flowers",32)
    g,c=grave[0],suburban[0]
    cemetery(g,m)
    empty_overcast_street(c,m)
    memorial(c,m)
    cboy=figure(g,"Boy with bowed shoulders at the grave","boy",compact=True,expressions=("hollow_still",))
    wboy=figure(c,"Boy walking alone in the original hoodie","boy",compact=True,expressions=("hollow_still","deadpan_blush"),
                extra_expressions={"grief":HERE/"grief.png"})

    stone,whale,boy,walk_in,ear,lonely,turn,flowers,ending,settle,fade=map(F,
        (88.30,90.58,92.03,94.43,95.85,97.34,98.87,101.77,103.35,110.39,111.05))
    cuts=((1,"Cemetery after the black cut"),(stone,"Pale blue-gray grave"),(whale,"Carved whale"),
          (boy,"Boy bowed in silence"),(walk_in,"Overcast school walk"),(ear,"Silent earcup insert"),
          (lonely,"Walking without her"),(turn,"The same corner"),(flowers,"Lily bouquets and the whisper"),
          (ending,"Boy's still face"))
    path=route((-3.23,.444,0),walk_in,ending, (3.02,.23,0))
    for f in range(1,length+1):
        if f<walk_in:
            breath=.018*math.sin(.07*(f-boy))
            act(cboy,f,(.69,-.43,0),-2.36,.045,expression="hollow_still",head=(.26+breath,-.027))
            if f<stone:
                glide(cam,f,grave,1,stone-1,(1.02,-4.51,2.26),(.92,-3.95,2.02),
                      (.13,1.2,1.59),(.04,.70,1.26),26,stop=2.8)
            elif f<whale:
                glide(cam,f,grave,stone,whale-1,(-.89,-2.06,1.50),(-.62,-1.87,1.29),
                      (0,.40,.85),(0,.37,.60),28,stop=2.8)
            elif f<boy:
                glide(cam,f,grave,whale,boy-1,(-.31,-1.38,.79),(-.23,-1.25,.74),
                      (0,.315,.56),(0,.315,.55),47,stop=4.1)
            else:
                glide(cam,f,grave,boy,walk_in-1,(-.06,-2.22,1.43),(.41,-2.45,1.58),
                      (.30,.19,.83),(.36,.138,.88),28,stop=2.8)
        else:
            if f<ending:
                walk(wboy,f,path,math.pi/2,walk_in,ending,"hollow_still",face=(.087,.037))
            else:
                tension=ease(f,ending,settle)
                act(wboy,f,path(ending),1.42-.77*tension,.033,expression="grief",
                    head=(.061-.059*tension,0),bounce=.005*math.sin((f-ending)*.043)*(1-tension))
            here=path(f)
            if f<ear:
                view(cam,f,suburban,here+Vector((1.1,-2.77,1.67)),here+Vector((-.15,.063,1.10)),26)
            elif f<lonely:
                x=ease(f,ear,lonely-1)
                view(cam,f,suburban,here+Vector((.62-.032*x,-1.43+.12*x,1.34)),
                     here+Vector((.011,-.037,1.20)),44,stop=5.0)
            elif f<turn:
                x=ease(f,lonely,turn-1)
                view(cam,f,suburban,here+Vector((-.72+.28*x,-2.22,1.54)),
                     here+Vector((.32,.24,1.07)),25)
            elif f<flowers:
                glide(cam,f,suburban,turn,flowers-1,(1.27,-2.33,1.60),(1.09,-1.70,1.49),
                      (-.55,.72,1.13),(.17,.96,1.07),26)
            elif f<ending:
                glide(cam,f,suburban,flowers,ending-1,(.99,-.479,1.135),(.55,-.269,1.095),
                      (.48,1.046,.889),(.47,1.046,.881),47,stop=2.8)
            else:
                glide(cam,f,suburban,ending,settle,(.81,-.67,1.41),(.36,-.31,1.32),
                      (-.21,.587,1.20),(-.21,.593,1.213),30,stop=2.6)
    fade_to_black(s,((1,0),(fade,0),(length-1,1),(length,1)))
    proofs=tuple(map(F,(87.86,88.43,89.63,90.87,92.37,94.65,96.06,97.56,99.35,102.5,104.36,110.74)))
    finish(s,4,(cboy,wboy),((grave,((1,walk_in-1),)),(suburban,((walk_in,length),))),
           cuts,proofs,((fade-1,length-1),))


if __name__=="__main__":
    main()
