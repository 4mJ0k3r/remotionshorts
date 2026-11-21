import * as THREE from "three";
import {Actor, Fx, Pool, q2, lidAt, talkAt, SU, PIV, handWorldPos, worldToCardPoint, kit3d} from "../../engine";
import {classroomPose,drawClassroomBody,drawClassroomHead,type ClassroomCelOpts} from "../../engine/classroom";
import {CHAR,TONE} from "../../engine/shaders/shade";
import {Pen} from "../../engine/shaders/pen";
import {buildClassroom} from "./build";
import {actingAt,ease,lightAt,SCALE,SPEAKER,STUDENT,PODIUM,PODIUM_TOP,speechAt} from "./story";
import {AUDIO_ENV} from "./audioEnv";

const HEAD_G=new THREE.PlaneGeometry(600*SU,600*SU);
const fade=(f:number,a:number,b:number,c:number,d:number)=>ease(f,a,b)*(1-ease(f,c,d));
export class GandhijiWorld {
  root=new THREE.Group();
  set=buildClassroom();
  pool=new Pool();
  cast=[0,1].map(()=>({body:new Actor(this.root),arms:new Actor(this.root),head:new Actor(this.root,HEAD_G)}));
  steam=[0,1,2].map(()=>new Fx(this.root));
  dust=new Fx(this.root);
  lastOptions:ClassroomCelOpts[]=[];
  constructor(){this.root.add(this.set.root);}
  update(id:number,f:number,cam:THREE.PerspectiveCamera,scene:THREE.Scene){
    const a=actingAt(f),mood=lightAt(f),s=this.set;
    const mystery=mood==="mystery",clinical=mood==="clinical";
    scene.background=new THREE.Color(mystery?"#1e2952":clinical?"#f0f6ff":"#e7cf9e");
    scene.fog=new THREE.Fog(mystery?"#1e2952":"#e1d8c5",9,24);
    s.keyLight.intensity=mystery?.28:clinical?2.0:3.8;
    s.keyLight.color.set(mystery?"#7b92de":clinical?"#f0f6ff":"#ffdfb0");s.keyLight.castShadow=!clinical;
    s.fill.color.set(mystery?"#52639d":clinical?"#f0f6ff":"#dceaff");s.fill.intensity=mystery?.65:clinical?1.5:1.0;
    for(const spot of s.spots){spot.light.intensity=mystery?10:0;spot.cone.visible=mystery;}
    TONE.uLitCol.value.set(...(mystery?[.72,.67,.90]:clinical?[1.1,1.13,1.2]:[1.46,1.24,.92]) as [number,number,number]);
    TONE.uShadeCol.value.set(...(mystery?[.20,.24,.46]:clinical?[.85,.89,.94]:[.56,.53,.62]) as [number,number,number]);
    TONE.uSat.value=mood==="vivid"?1.2:1;TONE.uBounce.value.set(.05,.04,.02);
    CHAR.uCharTint.value.set(1,1,1);CHAR.uCharShade.value=.96;CHAR.uGrad.value=.015;CHAR.uBodyGrad.value=.03;
    const voice=speechAt(f)?talkAt(f,AUDIO_ENV):0;
    const speaker:ClassroomCelOpts={role:"speaker",talk:voice,lid:f>=264&&f<363?.55:Math.max(.30*a.serious,lidAt(f,5)),serious:a.serious,smile:a.smile,turn:a.turn,gleam:a.gleam,tear:a.tear,glassesP:a.glasses,chinP:a.chin,pointP:a.point,wagP:a.wag};
    const student:ClassroomCelOpts={role:"student",talk:0,lid:lidAt(f,12),stress:a.stress,dizzy:a.dizzy,templesP:a.temples,plantP:a.plant};
    const opts=[speaker,student],positions=[SPEAKER,STUDENT];
    opts.forEach((o,i)=>{
      const pos=positions[i],fixture=i?s.deskHands:s.podiumHands;
      o.leftHand=worldToCardPoint(cam.position,pos,SCALE,fixture[0]);o.rightHand=worldToCardPoint(cam.position,pos,SCALE,fixture[1]);
      for(const k of Object.keys(o) as (keyof ClassroomCelOpts)[]){const v=o[k];if(typeof v==="number" && !["gleam","tear"].includes(k))Object.assign(o,{[k]:k==="talk"?v:q2(v)});}
      const pose=classroomPose(o),{body,arms,head}=this.cast[i];
      const yaw=Math.atan2(cam.position.x-pos[0],cam.position.z-pos[2]);
      const visible=i===0?id!==4:id===1||id===4||id===7;
      body.mesh.position.set(...pos);body.mesh.scale.setScalar(SCALE);body.mesh.rotation.set(0,yaw,0);body.mesh.visible=visible;
      head.mesh.position.set(pos[0]+Math.cos(yaw)*(pose.head[0]-300)*SU*SCALE,pos[1]+(PIV-pose.head[1])*SU*SCALE,pos[2]-Math.sin(yaw)*(pose.head[0]-300)*SU*SCALE+.008);
      head.mesh.scale.setScalar(SCALE);head.mesh.quaternion.copy(cam.quaternion);head.mesh.visible=visible;head.mesh.renderOrder=2;
      const normal=new THREE.Vector3(Math.sin(yaw),0,Math.cos(yaw)),origin=new THREE.Vector3(...pos);
      const depth=Math.max(...fixture.map(v=>v.clone().sub(origin).dot(normal)))+.005;
      const armPos=origin.clone().addScaledVector(normal,depth),armOrigin=armPos.toArray();
      arms.mesh.position.copy(armPos);arms.mesh.scale.setScalar(SCALE);arms.mesh.rotation.set(0,yaw,0);arms.mesh.visible=visible;arms.mesh.renderOrder=3;
      const armOpts:ClassroomCelOpts={...o,layer:'arms',headPoint:worldToCardPoint(cam.position,armOrigin,SCALE,head.mesh.position),
        shoulders:pose.shoulders.map(([x,y])=>worldToCardPoint(cam.position,armOrigin,SCALE,handWorldPos(cam.position,pos,SCALE,x,y,0))) as ClassroomCelOpts['shoulders'],
        finalHands:pose.hands.map(([x,y])=>worldToCardPoint(cam.position,armOrigin,SCALE,handWorldPos(cam.position,pos,SCALE,x,y,0))) as ClassroomCelOpts['finalHands']};
      body.r=this.pool.req(`classBody|${JSON.stringify(o)}`,1800,3000,3,p=>drawClassroomBody(p,{...o,layer:'body'}));
      arms.r=this.pool.req(`classArms|${JSON.stringify(armOpts)}`,1800,3000,3,p=>drawClassroomBody(p,armOpts));
      head.r=this.pool.req(`classHead|${JSON.stringify(o)}`,1800,1800,3,p=>drawClassroomHead(p,o));
    });
    this.lastOptions=opts;
    s.charkha.visible=f>=54&&f<105;s.charkha.position.set(-.72+.035*Math.sin((f-54)/18),1.25,.30);s.charkha.quaternion.copy(cam.quaternion);s.wheel.rotation.z=(f-54)*.055;
    s.gears.forEach((g,i)=>{g.visible=f>=105&&f<186;g.position.set(.18+i*.12,1.57+i*.16,.30);g.quaternion.copy(cam.quaternion);g.rotateZ((f-105)*(i?-.055:.04));});
    const studentHead=this.cast[1].head.mesh.position;
    this.steam.forEach((fx,i)=>{
      const alpha=fade(f,190,203,252,264);fx.use(true);fx.opacity(alpha*.65);fx.mesh.quaternion.copy(cam.quaternion);
      fx.mesh.position.copy(studentHead).add(new THREE.Vector3((i-1)*.14,.43,.012).applyQuaternion(cam.quaternion));fx.mesh.scale.set(.12,.36,1);
      fx.r=this.pool.req(`ribbon|${i}|${Math.round((f-190)/2)}`,180,600,1,p=>this.ribbon(p,f-190,i));
    });
    s.papers.forEach((paper,i)=>{
      const age=f-402;paper.visible=age>=0&&age<35;
      const u=Math.max(0,age/35);paper.position.set(STUDENT[0]+(i-1)*.30*u,.86+1.1*Math.sin(Math.PI*u),STUDENT[2]+.25+u*.15);paper.rotation.set(-.6+u*3,i+u*2,u*4+i);
    });
    s.book.visible=f>=476;
    const drop=ease(f,476,485),settle=1-ease(f,486,492);
    s.book.position.set(PODIUM[0],f<485?3.2+(PODIUM_TOP+.095-3.2)*drop:PODIUM_TOP+.095+(f>485?.055*settle:0),PODIUM[2]+.10);
    s.book.rotation.set(f<485?-.32*(1-drop):0,0,f<485?.06*(1-drop):0);
    this.dust.use(true);this.dust.opacity(fade(f,485,486,500,511));this.dust.mesh.position.set(PODIUM[0],PODIUM_TOP+.10,PODIUM[2]+.46);this.dust.mesh.quaternion.copy(cam.quaternion);this.dust.mesh.scale.set(1.6,.65,1);
    this.dust.r=this.pool.req(`chalkDust|${Math.round((f-485)/2)}`,600,300,1,p=>this.puffs(p,Math.max(0,(f-485)/27)));
    this.pool.flush();for(const c of this.cast){c.body.bind();c.arms.bind();c.head.bind();}for(const x of [...this.steam,this.dust])x.bind();
  }
  private ribbon(p:Pen,age:number,seed:number){
    const g=p.g;g.fillStyle="#fff8ed";const left:[number,number][]=[],right:[number,number][]=[];
    for(let j=0;j<=70;j++){const t=j/70,w=22*Math.sin(Math.PI*t),x=90+25*Math.sin(t*9-age*.07+seed*2),y=560-t*530;left.push([x-w,y]);right.push([x+w,y]);}
    const grad=g.createLinearGradient(0,560,0,30);grad.addColorStop(0,"rgba(255,250,238,0)");grad.addColorStop(.18,"rgba(255,250,238,.70)");grad.addColorStop(.70,"rgba(255,250,238,.40)");grad.addColorStop(1,"rgba(255,250,238,0)");
    g.fillStyle=grad;g.beginPath();[...left,...right.reverse()].forEach(([x,y],j)=>j?g.lineTo(x,y):g.moveTo(x,y));g.closePath();g.fill();
    g.save();g.translate(90,240);g.rotate(Math.sin(age*.035+seed)*.25);g.fillStyle="rgba(255,222,153,.6)";g.font="bold 31px Georgia";g.textAlign="center";g.fillText(["1947","?","E=mc²"][seed],0,0);g.restore();
  }
  private puffs(p:Pen,u:number){
    const g=p.g;g.save();g.globalAlpha=Math.max(0,1-u)*.85;
    for(let i=0;i<10;i++){const a=Math.PI+i/9*Math.PI,r=45+180*Math.sqrt(u),x=300+Math.cos(a)*r,y=235+Math.sin(a)*r*.48; p.ell(x,y,20+u*22,16+u*14,"#fff9eb",0);}
    g.restore();
  }
  dispose(){for(const c of this.cast){c.body.dispose();c.arms.dispose();c.head.dispose();}for(const x of [...this.steam,this.dust])x.dispose();this.pool.dispose();kit3d.disposeGeometry(this.set.root);}
}
