import * as THREE from "three";
import {kit3d as K} from "../../engine";
import {twoTone} from "../../engine/shaders/shade";
import {tex} from "../../engine/shaders/paint";
const tile=(key:string,a:string,b:string,n=8)=>K.lam(`cb:${key}`,()=>({map:K.tx(`cb:${key}`,()=>tex(512,512,(g,w,h)=>{
 const s=w/n;for(let y=0;y<n;y++)for(let x=0;x<n;x++){g.fillStyle=(x+y)%2?a:b;g.fillRect(x*s,y*s,s,s);g.strokeStyle="#839c99";g.lineWidth=2;g.strokeRect(x*s+1,y*s+1,s-2,s-2);}
}))}));
const porcelain=()=>K.lit("cb:porcelain","#eee9df");
const sphere=(p:THREE.Object3D,r:number,m:THREE.Material,x:number,y:number,z:number,s:[number,number,number]=[1,1,1])=>{const o=K.mesh(p,new THREE.SphereGeometry(r,24,16),m,x,y,z);o.scale.set(...s);return o;};
const ring=(p:THREE.Object3D,r:number,t:number,m:THREE.Material,x:number,y:number,z:number)=>K.mesh(p,new THREE.TorusGeometry(r,t,12,64),m,x,y,z,0,Math.PI/2);
export const makePoop=(parent:THREE.Object3D,transparent=false,clip?:THREE.Plane)=>{
 const root=new THREE.Group();parent.add(root);
 const brown=transparent?new THREE.MeshLambertMaterial({color:"#996333",transparent:true,opacity:0.58,depthWrite:false}):twoTone(new THREE.MeshLambertMaterial({color:"#986638",clippingPlanes:clip?[clip]:null}));
 for(let i=0;i<4;i++){const r=0.33-i*0.068;sphere(root,r,brown,i%2?0.016:-0.015,0.12+i*0.15,0,[1,0.54,0.9]);}
 const tip=K.mesh(root,new THREE.ConeGeometry(0.09,0.22,18),brown,-0.025,0.69,0);tip.rotation.z=-0.2;
 const face=new THREE.Group();root.add(face);
 const dark=K.lit("cb:poop-eyes","#351f22"),pink=K.lit("cb:poop-blush","#ee8c96");
 for(const s of [-1,1]){sphere(face,0.025,dark,s*0.09,0.28,0.282,[0.7,1.1,0.3]);sphere(face,0.04,pink,s*0.16,0.24,0.254,[1,0.45,0.2]);}
 face.position.set(0,0.27,-0.13);face.visible=false;
 return {root,face};
};
export const makeBowl=(parent:THREE.Object3D,scale=1)=>{
 const root=new THREE.Group();root.scale.setScalar(scale);parent.add(root);
 const profile=[[0.18,0],[0.20,0.05],[0.17,0.16],[0.26,0.23],[0.40,0.33],[0.46,0.43],[0.43,0.48],[0.36,0.44],[0.31,0.33],[0.22,0.22]].map(([x,y])=>new THREE.Vector2(x,y));
 K.mesh(root,new THREE.LatheGeometry(profile,64),porcelain(),0,0,0);
 ring(root,0.407,0.052,porcelain(),0,0.46,0);
 const water=K.mesh(root,new THREE.CircleGeometry(0.35,64),new THREE.MeshLambertMaterial({color:"#64866c",transparent:true,opacity:0.93,side:THREE.DoubleSide}),0,0.27,0,0,-Math.PI/2);
 const bulge=sphere(root,0.35,new THREE.MeshLambertMaterial({color:"#739974",transparent:true,opacity:0.92}),0,0.42,0,[1,0.09,1]);bulge.visible=false;
 const clip=new THREE.Plane(new THREE.Vector3(0,1,0),0);
 const poop=makePoop(root,false,clip);poop.root.position.y=0.27;
 const vortex=new THREE.Group();root.add(vortex);vortex.position.y=0.38;
 for(let i=0;i<6;i++){const rr=0.07+i*0.047;const a=K.mesh(vortex,new THREE.TorusGeometry(rr,0.014,6,48,Math.PI*1.6),K.lit("cb:vortex","#54d6f4"),0,-i*0.008,0,i*0.7,Math.PI/2);a.rotation.z=i*0.8;}
 vortex.visible=false;
 return {root,water,bulge,poop,vortex,clip};
};
const door=(parent:THREE.Object3D,x:number,z:number)=>{
 const pivot=new THREE.Group();pivot.position.set(x,0,z);parent.add(pivot);
 const wood=K.lam("cb:doorwood",()=>({map:K.tx("cb:doorwood",()=>tex(512,512,g=>{g.fillStyle="#ab7855";g.fillRect(0,0,512,512);for(let x=20;x<512;x+=34){g.fillStyle=x%3?"#b9875d":"#996744";g.fillRect(x,0,3,512);}}))}));
 K.box(pivot,1.3,2.45,0.11,wood,0.65,1.225,0);
 for(const y of [0.58,1.78])K.box(pivot,0.98,0.82,0.035,K.lit("cb:door-panel","#bc8c68"),0.65,y,0.072);
 const metal=K.lit("cb:chrome","#aab9cb"),handlePivot=new THREE.Group();handlePivot.position.set(1.05,1.04,0.12);pivot.add(handlePivot);
 const plate=K.cyl(handlePivot,0.065,0.065,0.04,metal,0,0,0,24);plate.rotation.x=Math.PI/2;
 K.box(handlePivot,0.27,0.035,0.055,metal,-0.1,0,0.04);
 return {pivot,handlePivot};
};
export const buildSets=()=>{
 const root=new THREE.Group(),sets={bathroom:new THREE.Group(),bowl:new THREE.Group(),science:new THREE.Group(),hall:new THREE.Group()};
 for(const [name,g]of Object.entries(sets)){g.name=`cb-${name}`;root.add(g);}
 const B=sets.bathroom,W=sets.bowl,S=sets.science,H=sets.hall;
 const tiles=tile("wall","#b5d6cb","#8bbdb4"),floor=tile("floor","#a5c6bc","#d7d3bd",10);
 K.box(B,18,0.12,18,floor,0,-0.08,0);
 // Door aperture is real: back wall consists of jamb panels and a lintel.
 K.box(B,3.25,3.6,0.14,tiles,-1.0,1.8,-1.8);K.box(B,0.65,3.6,0.14,tiles,2.3,1.8,-1.8);K.box(B,1.4,1.1,0.14,tiles,1.3,3.05,-1.8);
 for(const side of [-1,1])K.box(B,0.12,3.6,5.2,tiles,side*2.65,1.8,0.8);
 for(const x of [0.6,2.0])K.box(B,0.12,2.5,0.2,K.lit("cb:door-jamb","#67514b"),x,1.25,-1.66);
 const bathroomDoor=door(B,0.65,-1.65);
 K.box(B,1.38,2.5,0.08,K.lit("cb:hall-backlight","#ddbf94"),1.3,1.25,-2.15);
 // Vanity, ceramic sink, mirror and a warm lamp. Camera sees a three-dimensional side wall.
 K.box(B,0.7,0.7,0.5,K.lit("cb:vanity","#b98f6d"),-1.8,0.35,-0.9);
 sphere(B,0.38,porcelain(),-1.8,0.78,-0.85,[1,0.18,0.7]);
 K.box(B,0.8,1.05,0.1,K.lit("cb:mirror-frame","#5c6f75"),-1.8,1.7,-1.69);
 K.box(B,0.66,0.9,0.03,K.lit("cb:mirror","#aad1db"),-1.8,1.7,-1.61);
 K.box(B,0.78,0.08,0.13,new THREE.MeshBasicMaterial({color:new THREE.Color("#ffe8aa").multiplyScalar(1.4)}),-1.8,2.32,-1.55);
 const toilet=makeBowl(B);toilet.root.position.set(0,0,0.25);
 const tank=new THREE.Group();B.add(tank);tank.position.set(-0.3,0.6,-0.12);
 K.box(tank,0.48,0.30,0.32,porcelain(),0,-0.13,-0.22);K.box(tank,0.51,0.045,0.35,porcelain(),0,0.04,-0.22);
 const flushPlate=K.box(tank,0.18,0.025,0.1,K.lit("cb:flushplate","#afbdc8"),0,0.075,0);
 for(const s of [-1,1])K.cyl(tank,0.035,0.035,0.012,K.lit("cb:flush-inlay","#e3edf1"),s*0.045,0.093,0,20);
 const pipe=K.strut(B,[0,0.23,0.1],[-0.3,0.45,-0.12],0.055,porcelain(),12);
 const bucket=new THREE.Group();bucket.position.set(0.9,0,0.5);B.add(bucket);
 K.mesh(bucket,new THREE.CylinderGeometry(0.30,0.25,0.48,36,1,true),K.lit("cb:bucket","#2b7de9"),0,0.25,0);ring(bucket,0.29,0.035,K.lit("cb:bucket-rim","#63a9fc"),0,0.49,0);
 K.mesh(bucket,new THREE.CircleGeometry(0.26,48),new THREE.MeshLambertMaterial({color:"#57c9ec",side:THREE.DoubleSide}),0,0.43,0,0,-Math.PI/2);
 const mug=new THREE.Group();mug.position.set(0,0.56,0);bucket.add(mug);
 K.mesh(mug,new THREE.CylinderGeometry(0.11,0.085,0.20,28,1,true),K.lit("cb:divine-mug","#ff5ca8"),0,0.1,0);
 ring(mug,0.11,0.015,K.lit("cb:mug-rim","#ff98c8"),0,0.20,0);
 K.mesh(mug,new THREE.TorusGeometry(0.07,0.017,10,24),K.lit("cb:mug-handle","#ff5ca8"),0.135,0.12,0);
 const godRay=K.mesh(bucket,new THREE.ConeGeometry(0.65,2.6,48,1,true),new THREE.MeshBasicMaterial({color:"#ffe394",transparent:true,opacity:0.10,side:THREE.DoubleSide,depthWrite:false}),0,1.82,0);godRay.visible=false;
 const macro=makeBowl(W,2.7);macro.root.position.y=0.08;macro.poop.root.scale.setScalar(0.65);
 K.box(W,18,0.12,18,K.lit("cb:macro-floor","#8caeae"),0,-0.08,0);
 const sciencePoop=makePoop(S,true);sciencePoop.root.scale.setScalar(1.8);sciencePoop.root.position.y=0.5;
 K.box(S,14,7,0.2,K.lit("cb:science-background","#6087a4"),0,2.6,-2.5);
 K.box(S,6,0.08,3.5,K.lit("cb:waterline","#73d1dd"),0,1.46,0);
 K.box(S,6,1.4,0.05,new THREE.MeshBasicMaterial({color:"#376d91",transparent:true,opacity:0.25,depthWrite:false}),0,0.74,0.8);
 const gas:THREE.Mesh[]=[],bubbles:THREE.Mesh[]=[],arrows:THREE.Group[]=[];
 for(let i=0;i<7;i++)gas.push(sphere(S,0.075,new THREE.MeshBasicMaterial({color:"#f7fbff"}),Math.sin(i*2.2)*0.27,0.75+i*0.09,0.15));
 for(let i=0;i<12;i++)bubbles.push(sphere(S,0.035+(i%3)*0.015,new THREE.MeshBasicMaterial({color:"#d9fbff",transparent:true,opacity:0.8}),Math.sin(i*1.7)*1.3,0.3+(i%6)*0.23,0.4));
 for(const side of [-1,1]){const g=new THREE.Group();g.position.set(side*0.95,0.65,0.2);S.add(g);K.box(g,0.10,0.63,0.07,K.lit("cb:arrow","#ffdf54"),0,0.2,0);K.mesh(g,new THREE.ConeGeometry(0.2,0.32,4),K.lit("cb:arrow","#ffdf54"),0,0.65,0);arrows.push(g);}
 // Cozy sofa and hall: own floor, own walls and exterior door.
 K.box(H,20,0.12,20,K.lit("cb:hall-floor","#b7a18e"),0,-0.08,0);
 K.box(H,7,3.6,0.15,K.lit("cb:hall-wall","#d5b99e"),0,1.8,-1.8);
 for(const side of [-1,1])K.box(H,0.12,3.6,5,K.lit("cb:hall-wall","#d5b99e"),side*3.5,1.8,0.5);
 const sofa=new THREE.Group();sofa.position.set(-0.65,0,0.1);H.add(sofa);
 const fabric=K.lit("cb:sofa","#9e83b4");K.box(sofa,1.75,0.29,0.85,fabric,0,0.2,0);K.box(sofa,1.85,0.74,0.22,fabric,0,0.62,-0.38);
 for(const side of [-1,1])K.box(sofa,0.20,0.52,0.94,fabric,side*0.9,0.3,0);
 for(const x of [-0.45,0.45])K.box(sofa,0.65,0.10,0.63,K.lit("cb:sofa-cushion","#bea0ce"),x,0.29,0.02);
 const hallDoor=door(H,0.6,-1.55);
 K.box(H,0.16,2.5,0.2,K.lit("cb:hall-jamb","#775b4a"),0.56,1.25,-1.6);K.box(H,0.16,2.5,0.2,K.lit("cb:hall-jamb","#775b4a"),1.94,1.25,-1.6);
 K.box(H,1.35,0.14,0.2,K.lit("cb:hall-jamb","#775b4a"),1.25,2.51,-1.6);
 K.box(H,1.2,1.3,0.05,K.lit("cb:window-frame","#6b7d8d"),-2.25,1.95,-1.65);
 K.box(H,1.04,1.15,0.03,new THREE.MeshBasicMaterial({color:"#83bfd4"}),-2.25,1.95,-1.59);
 for(const x of [-2.55,-2.0])K.box(H,0.04,1.15,0.04,K.lit("cb:window-frame","#6b7d8d"),x,1.95,-1.55);
 return {root,sets,toilet,tank,flushPlate,pipe,bathroomDoor,bucket,mug,godRay,macro,sciencePoop,gas,bubbles,arrows,hallDoor,sofa};
};
