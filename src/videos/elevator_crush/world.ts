import * as THREE from "three";
import {Pool,Actor,Fx,makeChar,lidAt,talkAt,handWorldPos,worldToCardPoint,q2,fxBlob,fxImpact,fxSparks,Pen,kit3d} from "../../engine";
import {TONE,CHAR} from "../../engine/shaders/shade";
import {NOINK} from "../../engine/shaders/ink";
import {buildSets} from "./build";
import {actorsAt,glide,lightAt,BHDAM_AT,CABLE_AT,DROP_AT,HUG_AT,SPARKLE_AT,COUGH_AT,GROWL_AT} from "./story";
import {LIGHTS} from "./lights";
import {AUDIO_ENV} from "./audioEnv";
export class World {
 root=new THREE.Group(); private pool=new Pool();private actors:Actor[]=[];private armOverlays:Actor[]=[];private fxs:Fx[]=[];
 private sets=buildSets();private sun=new THREE.DirectionalLight("#fff0cf",2.4);
 private hemi=new THREE.HemisphereLight("#fff4dd","#77647e",1.5);
 private fill=new THREE.DirectionalLight("#b4dfff",1.1);
 private fanRest=this.sets.cabin.buttons.FAN.position.clone();
 constructor(){this.root.add(this.sets.root,this.sun,this.hemi,this.fill);this.sun.position.set(-3,6,4);this.fill.position.set(3,3,5);for(let i=0;i<2;i++){
  this.actors.push(new Actor(this.root));
  const arms=new Actor(this.root);arms.mat.depthTest=false;arms.mesh.renderOrder=3;this.armOverlays.push(arms);
 }}
 update(id:number,f:number,cam:THREE.PerspectiveCamera,scene:THREE.Scene){
  const light=LIGHTS[lightAt(id,f)];
  this.sets.cabin.root.visible=id!==2;this.sets.corridor.root.visible=id===2;
  scene.background=new THREE.Color(lightAt(id,f)==="violetRim"?"#675c84":"#807982");
  TONE.uLitCol.value.set(...light.lit);TONE.uShadeCol.value.set(...light.shade).lerp(new THREE.Vector3(0.64,0.6,0.7),0.6);
  TONE.uShadeLift.value.set(...light.lift);TONE.uLambert.value=light.lambert;TONE.uSideK.value=0.9;TONE.uTerm.value=light.term;TONE.uSat.value=1.05;TONE.uBounce.value.set(0.035,0.025,0.04);
  CHAR.uCharTint.value.set(...light.charTint);CHAR.uCharShade.value=0.9;CHAR.uGrad.value=light.charGrad;CHAR.uBodyGrad.value=light.bodyGrad;CHAR.uSideTint.value.set(...light.sideTint);
  this.sun.color.set(light.sunCol);this.sun.intensity=light.sunI;this.hemi.intensity=1.4;
  this.fill.color.set(id===7?"#ff8bca":id===11?"#74efff":"#c9deff");
  let gap=0;
  if(id===1)gap=1-glide(f,0,90);
  if(id===2)gap=f<285?1-0.9*glide(f,230,283):1-glide(f,350,400);
  this.sets.cabin.setDoorGap(gap);
  this.sets.cabin.led.redraw(id<=2?"FLOOR 4":id>=10?"FLOOR 4":"4 / STUCK",id>=3&&id<10&&Math.floor(f/18)%2===1);
  const colors:Record<number,string>={1:"#ffe8be",2:"#e5f1ff",3:"#ff9e63",4:"#ff9e63",5:"#ff9e63",6:"#ff9e63",7:"#bd8dff",8:"#ff97bd",9:"#ffe3a2",10:"#ffe0cb",11:"#9affff"};
  this.sets.cabin.ceilingMat.color.set(colors[id]).multiplyScalar(id===7?1.15:1.4);
  this.sets.cabin.grate.rotation.z=id===7?Math.sin(f*1.7)*0.018:0;
  this.sets.cabin.cables.forEach((c,i)=>{c.rotation.z=id===7?Math.sin(f*0.7+i)*0.07:0;});
  if(id===2)this.sets.corridor.redrawRain(f/30);
  const states=actorsAt(id,f),right=new THREE.Vector3(1,0,0).applyQuaternion(cam.quaternion);
  const together=id>=8&&id<=10;
  for(let i=0;i<states.length;i++) states[i].opts={...states[i].opts,bob:1.4*Math.sin(f*0.15+i)};
  if(together)for(let i=0;i<2;i++){
   const st=states[i],partner=states[1-i];
   const target=(dx:number,dy:number)=>{
    const world=handWorldPos(cam.position,partner.pos,partner.scale,dx,dy+(partner.opts.bob??0),0);
    const point=worldToCardPoint(cam.position,st.pos,st.scale,world);
    return [Math.max(45,Math.min(555,point[0])),Math.max(420,Math.min(510,point[1]))];
   };
   const left=target(i===0?230:380,435),rightHand=target(i===0?240:390,480);
   st.opts={...st.opts,handLX:left[0],handLY:left[1],handRX:rightHand[0],handRY:rightHand[1]};
  }
  for(let i=0;i<states.length;i++){
   const st=states[i],a=this.actors[i];
   const amp=talkAt(f,AUDIO_ENV);
   const place=makeChar({pos:cam.position,right,sun:this.sun.position.clone().normalize()},...st.pos,{...st.opts,drawLayer:together?"body":"all",blink:lidAt(f,i+5),talk:amp},st.scale);
   a.r=this.pool.req(place.key,...place.size!,place.draw);a.mesh.position.set(...st.pos);a.mesh.scale.setScalar(st.scale);a.mesh.rotation.y=Math.atan2(cam.position.x-st.pos[0],cam.position.z-st.pos[2]);a.mesh.visible=true;
   const arms=this.armOverlays[i];arms.mesh.visible=together;
   if(together){
    const layer=makeChar({pos:cam.position,right,sun:this.sun.position.clone().normalize()},...st.pos,{...st.opts,drawLayer:"arms"},st.scale);
    arms.r=this.pool.req(layer.key,...layer.size!,layer.draw);
    arms.mesh.position.copy(a.mesh.position);arms.mesh.scale.copy(a.mesh.scale);arms.mesh.rotation.copy(a.mesh.rotation);
   }
  }
  const cabin=this.sets.cabin;cabin.buttons.FAN.position.copy(this.fanRest);this.sets.shaft.visible=id===5;
  if(id===5){
   const rest=cabin.buttonWorldPosition("FAN"),hero=states[0];
   // Use the quantized design fist that was actually drawn by makeChar.
   const rawP=q2(hero.opts.pointP??1), k=rawP*rawP*(3-2*rawP), baseY=596+q2(1.4*Math.sin(f*0.15))*0.4;
   const point=handWorldPos(cam.position,hero.pos,hero.scale,204+(145-204)*k,baseY+(565-baseY)*k,-0.08);
   cabin.pinButton("FAN",point);
   const d=point.clone().sub(rest),shaft=this.sets.shaft;
   shaft.position.copy(rest).addScaledVector(d,0.5);shaft.scale.y=d.length();shaft.quaternion.setFromUnitVectors(new THREE.Vector3(0,1,0),d.normalize());
  }
  let used=0;
  const fx=(key:string,w:number,h:number,draw:(p:Pen)=>void,pos:THREE.Vector3,size:[number,number],flat=false,soft=false)=>{
   const e=this.fxs[used]??(this.fxs[used]=new Fx(this.root));used++;
   e.r=this.pool.req(key,w,h,1,draw);e.use(soft);e.mesh.position.copy(pos);e.mesh.scale.set(size[0],size[1],1);
   e.mesh.rotation.set(flat?-Math.PI/2:0,flat?0:Math.atan2(cam.position.x-pos.x,cam.position.z-pos.z),0);e.mesh.visible=true;e.mesh.layers.set(NOINK);
  };
  for(const st of states)fx("blob|#786c80",128,128,p=>fxBlob(p,"#786c80"),new THREE.Vector3(st.pos[0],0.012,st.pos[2]),[0.65,0.42],true);
  const burst=(at:number,kind:"spark"|"dust",pos:[number,number,number])=>{if(f>=at&&f<at+24){const u=Math.round((f-at)/24*50)/50;fx(`${kind}|${u}`,kind==="spark"?500:600,400,kind==="spark"?fxSparks(u):fxImpact(u),new THREE.Vector3(...pos),[1.1,0.8],false,true);}};
  if(id===2)burst(310,"spark",[0.8,0.35,0.3]);
  if(id===3)burst(BHDAM_AT,"spark",[0.5,2.3,-0.4]);
  if(id===6){burst(COUGH_AT,"dust",[0.1,1.4,0.7]);burst(GROWL_AT,"dust",[0.1,0.7,0.7]);}
  if(id===7){burst(CABLE_AT,"spark",[0,3.3,-0.25]);burst(DROP_AT,"spark",[0.4,2.9,-0.25]);}
  if(id===8||id===9||id===10||id===11){
   const pink=id===8;
   fx(`aura|${id}|${f}`,500,400,p=>{
    const g=p.g;g.save();g.globalAlpha=0.65;for(let j=0;j<7;j++){const x=30+((j*79+f*0.8)%440),y=60+((j*53-f*0.5)%280+280)%280;
    if(pink){p.poly([[x,y+5],[x-9,y-5],[x-9,y-13],[x-3,y-15],[x,y-9],[x+5,y-15],[x+11,y-12],[x+10,y-4]],"#ff98b3",0);}else{p.stroke([[x-6,y],[x+6,y]],3,"#ffe68c");p.stroke([[x,y-6],[x,y+6]],3,"#ffe68c");}}
    g.restore();
   },new THREE.Vector3(0,1.25,0.85),[2.3,1.8],false,true);
  }
  for(let i=used;i<this.fxs.length;i++)this.fxs[i].mesh.visible=false;
  this.pool.flush();this.actors.forEach(a=>a.bind());this.armOverlays.forEach(a=>{if(a.mesh.visible)a.bind();});this.fxs.slice(0,used).forEach(e=>e.bind());
  return new THREE.Vector3(0,1.2,0.5);
 }
 dispose(){this.actors.forEach(a=>a.dispose());this.armOverlays.forEach(a=>a.dispose());this.fxs.forEach(e=>e.dispose());this.pool.dispose();this.sets.cabin.dispose();this.sets.corridor.dispose();this.sun.dispose();this.hemi.dispose();this.fill.dispose();}
}
