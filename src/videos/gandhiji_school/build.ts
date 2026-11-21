import * as THREE from "three";
import {kit3d} from "../../engine";
import {PODIUM, DESK, PODIUM_TOP, DESK_TOP, SEAT_TOP} from "./story";
const {box,mesh,strut,cyl,lit,lam,tx}=kit3d;
const key=(s:string)=>`gandhiji|${s}`;
const texture=(w:number,h:number,draw:(g:CanvasRenderingContext2D,w:number,h:number)=>void)=>{
  const cv=document.createElement("canvas"); cv.width=w;cv.height=h;
  draw(cv.getContext("2d")!,w,h);
  const t=new THREE.CanvasTexture(cv);t.colorSpace=THREE.SRGBColorSpace;t.anisotropy=8;return t;
};
const timber=()=>tx(key("oak"),()=>texture(512,512,(g,w,h)=>{
  g.fillStyle="#c88a4b";g.fillRect(0,0,w,h);
  for(let n=0;n<54;n++){g.strokeStyle=n%3?"#af763e":"#d79b5e";g.lineWidth=1;g.beginPath();g.moveTo(0,n*10);g.bezierCurveTo(w*.3,n*10+4,w*.6,n*10-4,w,n*10);g.stroke();}
}));
const parquet=()=>tx(key("parquet"),()=>texture(1536,2048,(g,w,h)=>{
  g.fillStyle="#c88a4b";g.fillRect(0,0,w,h);g.translate(w/2,h/2);g.rotate(Math.PI/4);
  const cell=48,colors=["#c58a4f","#cc9255","#c18a50","#d0995c"];
  for(let axis=0;axis<2;axis++)for(let row=-45;row<45;row++)for(let k=-12;k<12;k++){
    const x=(axis?row:row+8*k)*cell,y=(axis?row-7+8*k:row)*cell;
    const pw=(axis?1:4)*cell,ph=(axis?4:1)*cell;
    g.fillStyle=colors[Math.abs(row*7+k*3+axis)%colors.length];g.fillRect(x,y,pw,ph);
    g.strokeStyle="rgba(92,56,30,.32)";g.lineWidth=1.3;g.strokeRect(x+.6,y+.6,pw-1.2,ph-1.2);
    g.strokeStyle="rgba(111,68,34,.14)";g.lineWidth=.7;
    for(let j=1;j<5;j++){g.beginPath();if(axis){g.moveTo(x+j*cell/5,y+3);g.lineTo(x+j*cell/5+2,y+ph-3);}else{g.moveTo(x+3,y+j*cell/5);g.lineTo(x+pw-3,y+j*cell/5+2);}g.stroke();}
  }
}));
const oak=()=>lam(key("oakMat"),()=>({map:timber()}));
const dark=()=>lit(key("trim"),"#55372c");
const chalk=()=>tx(key("blackboard"),()=>texture(1536,768,(g,w,h)=>{
  g.fillStyle="#1e4d4a";g.fillRect(0,0,w,h);
  for(let i=0;i<1200;i++){g.fillStyle=`rgba(212,232,207,${.012+(i%7)*.002})`;g.fillRect((i*101)%w,(i*173)%h,7,2);}
  g.fillStyle="#e3eee1";g.textAlign="left";
  g.font="italic 62px Georgia";g.fillText("HISTORY  /  CIVICS",100,104);
  g.font="56px Georgia";g.fillText("1942  →  1947",100,230);g.fillText("E = mc²",905,245);
  g.font="bold 72px Georgia";g.fillText("UPSC",1025,440);
  g.font="italic 39px Georgia";g.fillText("Truth · Non-violence · Freedom",100,654);
  g.strokeStyle="rgba(235,244,226,.8)";g.lineWidth=4;
  g.beginPath();g.moveTo(106,438);g.lineTo(178,303);g.lineTo(360,453);g.closePath();g.stroke();
  g.beginPath();g.moveTo(100,265);g.lineTo(650,265);g.moveTo(470,390);g.lineTo(820,390);g.moveTo(650,320);g.lineTo(650,535);g.stroke();
  g.beginPath();g.arc(650,428,104,0,Math.PI*2);g.stroke();
}));
const cover=()=>tx(key("bookCover"),()=>texture(1024,768,(g,w,h)=>{
  g.fillStyle="#1c3f94";g.fillRect(0,0,w,h);g.strokeStyle="#e3b94e";g.lineWidth=12;g.strokeRect(35,35,w-70,h-70);
  g.lineWidth=3;g.strokeRect(56,56,w-112,h-112);g.fillStyle="#f1d476";g.textAlign="center";
  g.font="bold 94px Georgia";g.fillText("HISTORY",w/2,260);g.font="bold 72px Georgia";g.fillText("& CIVICS",w/2,365);
  g.font="bold 66px Arial";g.fillText("GO STUDY!",w/2,548);g.font="24px Georgia";g.fillText("A CLASSROOM COMPANION",w/2,658);
}));
const bevelBox=(p:THREE.Object3D,w:number,h:number,d:number,m:THREE.Material,x:number,y:number,z:number)=>{
  const r=.025,s=new THREE.Shape();s.moveTo(-w/2+r,-h/2);s.lineTo(w/2-r,-h/2);s.quadraticCurveTo(w/2,-h/2,w/2,-h/2+r);
  s.lineTo(w/2,h/2-r);s.quadraticCurveTo(w/2,h/2,w/2-r,h/2);s.lineTo(-w/2+r,h/2);s.quadraticCurveTo(-w/2,h/2,-w/2,h/2-r);
  s.lineTo(-w/2,-h/2+r);s.quadraticCurveTo(-w/2,-h/2,-w/2+r,-h/2);
  const geo=new THREE.ExtrudeGeometry(s,{depth:d-.02,bevelEnabled:true,bevelSegments:2,steps:1,bevelSize:.01,bevelThickness:.01,curveSegments:3});
  geo.translate(0,0,-d/2+.01);return mesh(p,geo,m,x,y,z);
};
const contact=(p:THREE.Object3D,x:number,z:number,sx:number,sz:number)=>{
  const t=tx(key("contact"),()=>texture(128,128,(g,w,h)=>{const r=g.createRadialGradient(w/2,h/2,0,w/2,h/2,w/2);r.addColorStop(0,"rgba(27,20,32,.30)");r.addColorStop(1,"rgba(27,20,32,0)");g.fillStyle=r;g.fillRect(0,0,w,h);}));
  const m=new THREE.MeshBasicMaterial({map:t,transparent:true,depthWrite:false});
  const o=mesh(p,new THREE.PlaneGeometry(sx,sz),m,x,.009,z,0,-Math.PI/2);o.castShadow=false;return o;
};
export const buildClassroom=()=>{
  const root=new THREE.Group(), mOak=oak(),mDark=dark(),wall=lit(key("wall"),"#e7d8b4"),teal=lit(key("wallTeal"),"#456b64");
  const floorMat=new THREE.MeshPhongMaterial({map:parquet(),color:"#ffffff",shininess:35,specular:new THREE.Color("#3f2a17")});
  const floor=mesh(root,new THREE.PlaneGeometry(6,8),floorMat,0,0,-.8,0,-Math.PI/2);floor.castShadow=false;
  box(root,6,.04,8,mDark,0,-.025,-.8);
  box(root,5.8,3.5,.16,teal,0,1.75,-3.75);
  box(root,.16,3.5,7,wall,2.92,1.75,-.3);
  box(root,5.8,.12,.11,mDark,0,.08,-3.63);box(root,.11,.12,7,mDark,2.80,.08,-.3);
  const board=mesh(root,new THREE.PlaneGeometry(4.5,2.05),lam(key("boardMat"),()=>({map:chalk()})),0,1.94,-3.65);board.castShadow=false;
  for(const x of [-2.3,2.3])box(root,.12,2.17,.10,mDark,x,1.94,-3.6);
  for(const y of [.89,2.99])box(root,4.68,.12,.10,mDark,0,y,-3.6);
  box(root,4.65,.05,.2,mOak,0,.86,-3.48);
  for(let n=0;n<5;n++)box(root,.095,.02,.022,lit(key("chalkStick"),"#e9f2df"),-1.8+n*.2,.91,-3.44);
  box(root,.17,1.0,7,wall,-2.92,.5,-.3);box(root,.17,.4,7,wall,-2.92,3.3,-.3);
  for(const z of [-3.65,-1.95,-.25,1.45,3.1])box(root,.20,2.1,.22,wall,-2.92,2.0,z);
  const sky=new THREE.MeshBasicMaterial({color:"#b8dded",side:THREE.DoubleSide});
  for(const z of [-2.8,-1.1,.6,2.3]){
    const glass=mesh(root,new THREE.PlaneGeometry(1.42,1.95),sky,-3.06,2.0,z,Math.PI/2);glass.castShadow=false;
    for(const y of [1,2,3])box(root,.25,.055,1.5,mDark,-2.82,y,z);
    box(root,.24,2.0,.055,mDark,-2.82,2,z);box(root,.32,.08,1.5,mOak,-2.80,.98,z);
  }
  const podium=new THREE.Group();podium.position.set(...PODIUM);root.add(podium);
  bevelBox(podium,.75,.83,.49,mOak,0,.45,0);box(podium,.87,.08,.59,mDark,0,.05,0);
  bevelBox(podium,.60,.52,.025,lit(key("podiumPanel"),"#a76e36"),0,.43,.25);
  for(const x of [-.315,.315])box(podium,.055,.62,.04,lit(key("panelRim"),"#dbac64"),x,.45,.275);
  const top=bevelBox(podium,.91,.07,.61,mOak,0,PODIUM_TOP-.035,0);top.rotation.x=-.09;
  podium.updateMatrixWorld(true);
  const podiumHands=[[-.31,.035+.031,.15],[.31,.035+.031,.15]].map(p=>top.localToWorld(new THREE.Vector3(...p as [number,number,number])));
  contact(root,PODIUM[0],PODIUM[2],1.0,.8);
  const desk=new THREE.Group();desk.position.set(...DESK);root.add(desk);
  bevelBox(desk,.88,.07,.52,mOak,0,DESK_TOP-.035,.10);
  box(desk,.74,.14,.04,mDark,0,DESK_TOP-.13,.32);
  for(const x of [-.35,.35])for(const z of [-.10,.31]){
    box(desk,.055,.76,.055,mDark,x,.38,z);contact(root,DESK[0]+x,DESK[2]+z,.2,.2);
  }
  const bench=box(desk,.82,.055,.26,mOak,0,SEAT_TOP-.0275,-.035);
  for(const x of [-.33,.33])box(desk,.055,.49,.12,mDark,x,.245,-.035);
  const deskHands=[new THREE.Vector3(DESK[0]-.27,DESK_TOP+.032,DESK[2]+.30),new THREE.Vector3(DESK[0]+.27,DESK_TOP+.032,DESK[2]+.30)];
  const book=new THREE.Group();root.add(book);book.visible=false;
  const blue=lit(key("bookBlue"),"#1c3f94"),gold=lit(key("gold"),"#dcb249");
  box(book,.95,.095,.68,lit(key("pages"),"#fbf0d7"),0,0,0);
  for(const y of [-.06,.06])box(book,1.00,.024,.73,blue,0,y,0);
  box(book,.038,.145,.73,blue,-.49,0,0);
  const title=mesh(book,new THREE.PlaneGeometry(.94,.68),lam(key("cover"),()=>({map:cover()})),0,.073,0,0,-Math.PI/2);title.castShadow=false;
  for(let i=0;i<8;i++)box(book,.003,.002,.65,lit(key("pageLines"),"#c2ad83"),.477,-.04+i*.012,0);
  const spine=tx(key("bookSpine"),()=>texture(1024,200,(g,w,h)=>{
    g.fillStyle="#1c3f94";g.fillRect(0,0,w,h);g.strokeStyle="#e3b94e";g.lineWidth=10;g.strokeRect(12,12,w-24,h-24);
    g.fillStyle="#f1d476";g.textAlign="center";g.font="bold 62px Georgia";g.fillText("HISTORY & CIVICS",w/2,85);
    g.font="bold 50px Arial";g.fillText("GO STUDY!",w/2,152);
  }));
  const spineLabel=mesh(book,new THREE.PlaneGeometry(.98,.14),lam(key("spineMat"),()=>({map:spine})),0,0,.367);spineLabel.castShadow=false;
  const charkha=new THREE.Group();root.add(charkha);
  const wheel=new THREE.Group();charkha.add(wheel);
  mesh(wheel,new THREE.TorusGeometry(.18,.012,6,40),gold,0,0,0);
  for(let i=0;i<12;i++){const a=i*Math.PI/6;strut(wheel,[0,0,0],[Math.cos(a)*.18,Math.sin(a)*.18,0],.006,gold);}
  box(charkha,.46,.035,.08,gold,0,-.24,0);strut(charkha,[-.18,-.22,0],[0,0,0],.01,gold);strut(charkha,[.18,-.22,0],[0,0,0],.01,gold);
  const gears=[0,1].map(i=>{
    const g=new THREE.Group();root.add(g);mesh(g,new THREE.TorusGeometry(i?.085:.105,.018,6,30),gold,0,0,0);
    for(let j=0;j<10;j++){const a=j*Math.PI/5;box(g,.035,.05,.026,gold,Math.cos(a)*(i?.105:.125),Math.sin(a)*(i?.105:.125),0,0,0,a-Math.PI/2);}
    cyl(g,.025,.025,.03,gold,0,0,0).rotation.x=Math.PI/2;return g;
  });
  const papers=[0,1,2].map(()=>{const p=mesh(root,new THREE.PlaneGeometry(.22,.29),lit(key("paper"),"#fff9e7"),0,0,0);p.visible=false;return p;});
  const keyLight=new THREE.DirectionalLight("#ffddaa",3.8);keyLight.position.set(-5,7,1);keyLight.target.position.set(0,0,-1);
  keyLight.castShadow=true;keyLight.shadow.mapSize.set(2048,2048);Object.assign(keyLight.shadow.camera,{left:-5,right:5,top:5,bottom:-5,near:.1,far:20});keyLight.shadow.bias=-.0004;keyLight.shadow.normalBias=.015;
  root.add(keyLight,keyLight.target);
  const fill=new THREE.HemisphereLight("#c8dcff","#9f7958",1.0);root.add(fill);
  const spots=[SPEAKER_PLACE(),new THREE.Vector3(DESK[0],1,DESK[2])].map(pos=>{
    const light=new THREE.SpotLight("#ffd785",15,5,Math.PI/12,.75,1);light.position.set(pos.x,3.25,pos.z+.1);light.target.position.copy(pos);root.add(light,light.target);
    const cone=mesh(root,new THREE.ConeGeometry(.63,2.4,40,1,true),new THREE.MeshBasicMaterial({color:"#ffcd72",transparent:true,opacity:.045,depthWrite:false,side:THREE.DoubleSide}),pos.x,2.0,pos.z+.1);
    cone.castShadow=false;return {light,cone};
  });
  return {root,podium,desk,bench,podiumHands,deskHands,book,charkha,wheel,gears,papers,keyLight,fill,spots};
};
function SPEAKER_PLACE(){return new THREE.Vector3(PODIUM[0],1.0,PODIUM[2]);}
export type ClassroomSet=ReturnType<typeof buildClassroom>;
