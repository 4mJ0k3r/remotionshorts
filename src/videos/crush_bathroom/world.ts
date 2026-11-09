import * as THREE from "three";
import {Actor,Fx,Pool,makeChar,talkAt,lidAt,handWorldPos,worldToCardPoint,flushFist,q2,Pen,fxBlob,fxSparks,kit3d} from "../../engine";
import {TONE,CHAR} from "../../engine/shaders/shade";
import {buildSets} from "./build";
import {castAt,shotAt,progress,clamp01} from "./story";
import {AUDIO_ENV} from "./audioEnv";
export class World {
 root=new THREE.Group();private pool=new Pool();private actors:Actor[]=[];private effects:Fx[]=[];private sceneSets=buildSets();
 private sun=new THREE.DirectionalLight("#fff0d6",2.5);private fill=new THREE.HemisphereLight("#e2f7ff","#9a8595",1.5);
 constructor(){this.root.add(this.sceneSets.root,this.sun,this.fill);this.sun.position.set(-3,5,4);for(let i=0;i<2;i++)this.actors.push(new Actor(this.root));}
 update(id:number,f:number,cam:THREE.PerspectiveCamera,scene:THREE.Scene){
  const s=shotAt(f),sets=this.sceneSets;
  for(const[name,g]of Object.entries(sets.sets))g.visible=name===s.set;
  sets.sofa.visible=id!==10;
  scene.background=new THREE.Color(s.set==="science"?"#6087a4":"#aab7b5");
  const worldGain=s.set==="bowl"?(id===15?0.40:0.43):s.set==="bathroom"?0.55:0.62;
  const rose=s.id===15,panic=[5,7,9,19,20,21].includes(id);
  TONE.uLitCol.value.set(...(rose?[1.42,1.12,1.25]:panic?[1.34,1.15,1.10]:[1.30,1.28,1.24]) as [number,number,number]).multiplyScalar(worldGain);
  TONE.uShadeCol.value.set(0.62,0.66,0.76).multiplyScalar(0.75);TONE.uShadeLift.value.set(0.025,0.03,0.04);TONE.uLambert.value=0.28;TONE.uSideK.value=0.94;TONE.uTerm.value=0.22;TONE.uBounce.value.set(0.02,0.025,0.03);TONE.uSat.value=1.05;
  CHAR.uCharTint.value.set(1,0.985,0.96);CHAR.uCharShade.value=0.92;CHAR.uGrad.value=0.05;CHAR.uBodyGrad.value=0.12;CHAR.uSideTint.value.set(0.95,0.96,1.0);
  const wave=0.5+0.5*Math.sin(f*0.11),rise=progress(f,465,714);
  const level=f>=465&&f<1326?0.27+0.14*rise:0.27;
  for(const bowl of [sets.toilet,sets.macro]){
   bowl.clip.constant=-(bowl.root.position.y+level*bowl.root.scale.y);
   bowl.water.position.y=level+0.003*Math.sin(f*0.18);bowl.water.rotation.z=f*0.025;
   bowl.bulge.visible=id===8;bowl.bulge.position.y=level+0.012;
   const vortex=[13,17].includes(id);bowl.vortex.visible=vortex;bowl.vortex.rotation.y=f*0.22;bowl.vortex.position.y=level+0.008;
   bowl.poop.root.position.y=level+0.012*Math.sin(f*0.12)-(id===8?0.35:0);
   bowl.poop.root.visible=!(id===13&&f>=1395&&f<1425);
   if(id===13&&f<1395)bowl.poop.root.position.y=level-0.55*progress(f,1326,1395);
   if(id===13&&f>=1425)bowl.poop.root.position.y=level+0.32*Math.sin(Math.PI*clamp01((f-1425)/45));
   bowl.poop.root.rotation.y=(id===17?0.08:0.15)*Math.sin(f*0.07);bowl.poop.root.rotation.z=id===15?0.06*Math.sin(f*0.09):0;
   bowl.poop.face.visible=id===15;bowl.poop.face.rotation.y=Math.atan2(cam.position.x,cam.position.z)-bowl.poop.root.rotation.y;
  }
  sets.gas.forEach((b,i)=>b.scale.setScalar(0.82+0.18*Math.sin(f*0.15+i)));
  sets.bubbles.forEach((b,i)=>{b.position.y=0.35+((f*0.015+i*0.24)%1.5);b.position.x=Math.sin(i*1.7)*1.3+Math.sin(f*0.04+i)*0.03;});
  sets.arrows.forEach((g,i)=>{g.position.y=0.65+0.13*Math.sin(f*0.16+i*0.3);});
  sets.sciencePoop.root.rotation.y=0.12*Math.sin(f*0.045);
  sets.bathroomDoor.handlePivot.rotation.z=id===19?-0.6*progress(f,2244,2316):id===20?-0.6:0;
  sets.bathroomDoor.pivot.rotation.y=id===20?1.3*progress(f,2316,2390):0;
  sets.godRay.visible=id>=22;sets.godRay.material instanceof THREE.MeshBasicMaterial&&(sets.godRay.material.opacity=0.085+0.025*wave);
  sets.mug.visible=id!==23;sets.mug.rotation.y=id===22?0.12*Math.sin(f*0.06):0;
  const states=castAt(f),right=new THREE.Vector3(1,0,0).applyQuaternion(cam.quaternion);
  this.actors.forEach(a=>a.mesh.visible=false);
  states.forEach((st,i)=>{
   const bob=q2((st.opts.bob??0)+1.5*Math.sin(f*0.17+i));
   if(st.opts.mode==="knockDoor"){
    const target=new THREE.Vector3(0.48,1.0,-1.45+0.06*Math.sin(f*0.5));
    const [x,y]=worldToCardPoint(cam.position,st.pos,st.scale,target);st.opts.handRX=Math.max(45,Math.min(555,x));st.opts.handRY=Math.max(410,Math.min(600,y));
   }
   if(st.opts.mode==="peekDoor")st.opts.lean=-0.08*progress(f,2316,2406);
   const opts={...st.opts,bob,blink:lidAt(f,i+13),talk:st.speaker?talkAt(f,AUDIO_ENV):0};
   const place=makeChar({pos:cam.position,right,sun:this.sun.position.clone().normalize()},...st.pos,opts,st.scale),actor=this.actors[i];
   actor.r=this.pool.req(place.key,...place.size!,place.draw);actor.mesh.position.set(...st.pos);actor.mesh.scale.setScalar(st.scale);actor.mesh.rotation.y=Math.atan2(cam.position.x-st.pos[0],cam.position.z-st.pos[2]);actor.mesh.visible=true;
   if(st.opts.mode==="pressFlush"){
    const [dx,dy]=flushFist(q2(st.opts.flushP??1)),point=handWorldPos(cam.position,st.pos,st.scale,dx,dy,-0.08);
    sets.tank.position.copy(point).add(new THREE.Vector3(0,-0.093,0));
   }
  });
  if(!states.some(a=>a.opts.mode==="pressFlush"))sets.tank.position.set(-0.3,0.68,-0.1);
  const start=new THREE.Vector3(0,0.24,0.1),end=sets.tank.position.clone().add(new THREE.Vector3(0,-0.2,-0.08)),d=end.clone().sub(start);
  sets.pipe.position.copy(start).addScaledVector(d,0.5);sets.pipe.scale.y=d.length()/Math.hypot(-0.3,0.22,-0.22);sets.pipe.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());
  let used=0;
  const effect=(key:string,draw:(p:Pen)=>void,pos:[number,number,number],w:number,h:number,cw=500,ch=400,flat=false)=>{
   const fx=this.effects[used]??(this.effects[used]=new Fx(this.root));used++;fx.r=this.pool.req(key,cw,ch,1,draw);fx.use(!flat);fx.mesh.visible=true;fx.mesh.position.set(...pos);fx.mesh.scale.set(w,h,1);fx.mesh.rotation.set(flat?-Math.PI/2:0,flat?0:Math.atan2(cam.position.x-pos[0],cam.position.z-pos[2]),0);
  };
  states.forEach((a,i)=>effect('blob|#92858e',p=>fxBlob(p,"#92858e"),[a.pos[0],0.015,a.pos[2]],0.65,0.4,128,128,true));
  if([3,4,5,6,8,12,14,17].includes(id))effect(`stink|${f}`,p=>{
   for(let i=0;i<3;i++){const x=120+i*110;const pts:[number,number][]=[];for(let j=0;j<22;j++)pts.push([x+14*Math.sin(j*0.45-f*0.16+i),340-j*11]);p.stroke(pts,7,"#90c354");}
  },[id===6||id===8||id===17?0:0.25,id===6||id===8||id===17?1.8:0.95,id===6||id===8||id===17?0.85:0.20],id===6||id===8||id===17?1.3:0.7,1.05);
  if([2,15,18,22,23].includes(id))effect(`sparkle|${id}|${f}`,p=>{
   for(let i=0;i<9;i++){const x=30+((i*67+f*0.7)%440),y=35+((i*43-f*0.5)%320+320)%320;
    if(id===15)p.poly([[x,y+8],[x-12,y-3],[x-12,y-12],[x-5,y-16],[x,y-9],[x+8,y-16],[x+15,y-10],[x+12,y-1]],"#ff95b9",0);
    else{p.stroke([[x-7,y],[x+7,y]],3,"#fff4b0");p.stroke([[x,y-7],[x,y+7]],3,"#fff4b0");}}
  },[id===22?0.9:id===2||id===18?-0.65:0,id===22?1.0:1.3,0.9],id===15?2.4:1.9,1.8);
  if((id===9&&f<870)||(id===10&&f%18<10))effect(`knock|${f}`,p=>{const phase=(f%18)/18;for(let i=0;i<3;i++)p.arc(250,220,35+phase*70+i*22,35+phase*70+i*22,190,350,6,"#ffe2a4");},[0.65,1.45,-1.35],0.85,0.68);
  if(id===13&&f>=1425&&f<1460){const u=(f-1425)/35;effect(`splash|${f}`,p=>{for(let i=0;i<14;i++){const a=Math.PI+i/13*Math.PI,x=250+Math.cos(a)*(40+u*180),y=300+Math.sin(a)*(30+u*180)+u*u*100;p.ell(x,y,7,14,"#b7efff",2);}},[0,1.9,0.4],2.2,1.7);}
  for(let i=used;i<this.effects.length;i++)this.effects[i].mesh.visible=false;
  this.pool.flush();this.actors.forEach(a=>{if(a.mesh.visible)a.bind();});this.effects.slice(0,used).forEach(e=>e.bind());
  return new THREE.Vector3();
 }
 dispose(){this.actors.forEach(a=>a.dispose());this.effects.forEach(e=>e.dispose());this.pool.dispose();kit3d.disposeGeometry(this.sceneSets.root);this.sun.dispose();this.fill.dispose();}
}
