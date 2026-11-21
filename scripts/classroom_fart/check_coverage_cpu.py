"""Conservative CPU projection forecast; calibration remains the visual gate."""
import ast,json,math
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent;OUT=Path(r'D:\remotionshorts\renders\classroom_fart')
tree=ast.parse((HERE/'build_classroom_fart.py').read_text())
fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='camera_pose')
views=ast.literal_eval(next(n.value for n in ast.walk(fn) if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='views' for t in n.targets)))
rows=json.loads((OUT/'shots.json').read_text())['shots']
def e(a,b,f):u=np.clip((f-a)/(b-a),0,1);return float(u*u*(3-2*u))
def norm(a):return a/np.linalg.norm(a)
def camera(f,row):
    shot=row['shot'];u=(f-row['start_frame'])/max(1,row['end_frame']-row['start_frame']);p,t,l=views[shot]
    if shot=='3B' and f>=769:p,t,l=((1.15,2.55,1.8),(0,-.2,1.1),48);u=(f-769)/34
    if shot=='4B' and f>=1035:p,t,l=((1.3,0,.95),(0,-.25,.73),65);u=(f-1035)/47
    margin={'3B':1.5 if f<769 else 1.,'4A':1.25,'5B':1.25,'5C':1.5}.get(shot,1.)
    p,t=np.array(p),np.array(t);p=t+(p-t)*margin*(1-.1*u);p[0]+=.055*u
    fw=norm(t-p);right=norm(np.cross(fw,[0,0,1]));up=np.cross(right,fw)
    return p,fw,right,up,l
def hero(f,action):
    lean=0.;jump=0.;rock=0.
    if f>=971:lean=math.pi/4*e(975,1021,f)
    if f>=1299:lean*=1-e(1299,1318,f)
    if f>=1410:
        if f<1422:lean=-math.radians(8)*e(1410,1422,f)
        elif f<1446:jump=.94*e(1422,1446,f);lean=-math.radians(8)*(1-e(1422,1430,f))
        elif f<1466:jump=.94-.42*e(1446,1466,f)
        else:jump=.52+.025*(1-e(1466,1475,f))
    if 769<=f<804:rock=math.radians(7)*math.sin((f-769)/35*math.tau*2)*math.sin((f-769)/35*math.pi)
    r=np.array([[math.cos(rock),0,math.sin(rock)],[0,1,0],[-math.sin(rock),0,math.cos(rock)]])
    hip=np.array([0,-.2,0])+r@np.array([0,0,.71+jump]);axis=r@np.array([0,-math.sin(lean),math.cos(lean)])
    if action=='soul':axis=np.array([0,.27,.963]);hip[1]+=.02
    return hip,hip+axis*.84,axis
def project(pt,rad,cam):
    p,fw,rr,up,l=cam;v=pt-p;depth=v@fw;w=depth*36/l;h=w*1920/1080
    return [.5+(v@rr-rad)/w,.5+(v@rr+rad)/w,.5+(v@up-rad)/h,.5+(v@up+rad)/h]
flags=[];worst={}
for row in rows:
    shot=row['shot']
    for f in range(row['start_frame'],row['end_frame']+1):
        if shot=='2A' or (shot=='3B' and f<769) or (shot=='4B' and f>=1035):continue
        cam=camera(f,row);hip,head,axis=hero(f,row['action']);points=[('you',head,.51)]
        if shot in ['3C','4B','5C']:points.append(('friend',np.array([1.9,-.2,1.55]),.51))
        if shot in ['2E','4D']:points=[('teacher',np.array([-1.1+.18*e(490,579,f)-.18*e(1215,1250,f),3.25,1.52]),.54)]
        if shot in ['1C','4A','5C']:
            normal=norm(np.array([cam[0][0],cam[0][1]+.2,0]));right=norm(np.cross(axis,normal))
            if shot=='4A':points.append(('raised finger',head+right*.65+np.array([0,0,.23]),.04))
            if shot=='1C':
                points.extend([('head hand',head+right*sign*.48+np.array([0,0,.22]),.06) for sign in [-1,1]])
            if shot=='5C':points.append(('raised wave',head+right*.72+np.array([0,0,.43]),.065))
        for name,p,r in points:
            b=project(p,r,cam)
            if b[0]<.025 or b[1]>.975 or b[2]<.025 or b[3]>.90:flags.append({'shot':shot,'frame':f,'part':name,'bounds':b})
            k=shot+'/'+name
            if k not in worst:worst[k]=b
            else:worst[k]=[min(worst[k][0],b[0]),max(worst[k][1],b[1]),min(worst[k][2],b[2]),max(worst[k][3],b[3])]
result={'forecast_only':True,'flags':flags,'worst_bounds':worst};(OUT/'coverage_forecast.json').write_text(json.dumps(result,indent=2))
print(json.dumps({'flag_count':len(flags),'examples':flags[:8],'worst_bounds':worst},indent=2))
