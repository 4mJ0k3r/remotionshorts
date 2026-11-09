import {makeShotCam,glide,type V3} from "../../engine/camera";
import type {KidOpts} from "../../engine/character";
export const FPS=30,TOTAL=2879;
export const clamp01=(x:number)=>Math.max(0,Math.min(1,x));
export const progress=(f:number,a:number,b:number)=>glide((f-a)/(b-a));
export type SetName="bathroom"|"bowl"|"science"|"hall";
export const CALIBRATION=[60,125,210,360,510,600,680,770,875,1050,1160,1270,1410,1700,1860,2180,2280,2360,2450,2580,2740];
const raw:[number,number,SetName,number,string][]=[
 [0,96,"bathroom",1,"💩 क्रश के घर पहाड़ जैसी टट्टी! 🏔️"],[96,156,"hall",1,"💖 उधर क्रश फोन पर बिज़ी है..."],[156,264,"bathroom",1,"💩 ये तो पहाड़ बन गया!"],[264,465,"bathroom",1,"🚽 फ्लश दबाया... कुछ नहीं हुआ!"],
 [465,555,"bathroom",2,"😱 पानी ऊपर आ रहा है! 🌊"],[555,645,"bowl",2,"🌊 और ऊपर... और ऊपर!"],[645,714,"bathroom",2,"😱 बस! बस! बस!"],[714,834,"bowl",2,"💀 किनारे पर अटक गया!"],
 [834,915,"bathroom",3,"🚪 बाहर आंटी खड़ी हैं! 😰"],[915,1110,"hall",3,"🚪 बेटा, अंदर सब ठीक है ना?"],[1110,1215,"bathroom",3,"😅 ह-हाँ आंटी जी... एकदम बढ़िया!"],[1215,1326,"bathroom",3,"🙏 आख़िरी बार... प्लीज़!"],
 [1326,1494,"bowl",4,"💩 ये वापस क्यों आ रही है?! 💖"],[1494,1614,"bathroom",4,"😭 एक और फ्लश... फिर वही!"],[1614,1776,"bowl",4,"💩 इसे तुमसे प्यार हो गया! 💖"],
 [1776,1935,"science",5,"🧪 अंदर गैस = ऊपर तैरना! 💨"],[1935,2046,"bowl",5,"🌀 पानी घूमे... ये न डूबे!"],
 [2046,2244,"hall",6,"💀 मम्मी, ये अभी तक अंदर ही है?"],[2244,2316,"bathroom",6,"🚪 हैंडल घूम रहा है..."],[2316,2406,"bathroom",6,"💀 आंटी ने दरवाज़ा खोल दिया!"],
 [2406,2505,"bathroom",7,"😱 अब क्या करूँ?!"],[2505,2655,"bathroom",7,"🪣 आख़िरी हथियार: गुलाबी मग्गा! ✨"],[2655,TOTAL,"bathroom",7,"✨ अब यही मग्गा ठिकाने लगाएगा!"],
];
export const SHOTS=raw.map(([a,b,set,scene,hud],i)=>({id:i+1,a,b,set,scene,hud,grade:set==="science"?"day":scene===4?"warm":"day",exposure:1}));
export const shotAt=(f:number)=>SHOTS.find(s=>f>=s.a&&f<s.b)??SHOTS[SHOTS.length-1];
export type CastState={pos:V3;scale:number;opts:KidOpts;speaker:boolean};
export const castAt=(f:number):CastState[]=>{
 const s=shotAt(f),id=s.id;
 const hero:CastState={pos:[0,0,0.66],scale:0.9,opts:{kind:"plaidHero",expr:"shyBlush",mode:"toiletSit",sitP:1,gazeY:0.5},speaker:true};
 const crush:CastState={pos:[-0.65,0,0.76],scale:0.86,opts:{kind:"crush",shirtColor:"#b388eb",outfitStyle:"top",expr:"happyProud",mode:"sofaPhone",sitP:1,lowerP:0,gazeY:0.6},speaker:false};
 const mom:CastState={pos:[0.05,0,-0.12],scale:0.86,opts:{kind:"mom",expr:"suspicious",mode:"knockDoor",knockP:(f%18)/18,gaze:0.6},speaker:f>=1000&&f<1110};
 if([6,8,13,15,16,17,19,22].includes(id))return [];
 if(id===2)return[crush];
 if(id===18){crush.opts.lowerP=progress(f,2046,2180);crush.opts.expr="suspicious";crush.speaker=f>=2150;return[crush];}
 if(id===10)return[mom];
 if(id===3){hero.pos[0]=-0.4;hero.opts.expr="brokeSad";hero.opts.bob=-3*progress(f,190,250);}
 if([4,5,12,14].includes(id)){
  hero.opts.mode="pressFlush";hero.opts.expr=id===5?"panicShock":id===12?"prayerUp":id===14?"brokeSad":"gentleConcern";
  hero.opts.flushP=id===5?0.5+0.5*Math.sin(f*0.9):id===12?progress(f,1215,1310):0.5+0.5*Math.sin(f*0.15);
  hero.opts.sweat=id===5||id===12?1:0;
 }
 if([7,21].includes(id)){hero.opts.expr="panicShock";hero.opts.pupilScale=0.48;hero.opts.sweat=1;hero.speaker=false;hero.opts.gazeY=id===21?0.8:0;}
 if(id===9){hero.opts.expr="panicShock";hero.opts.gaze=0.9;hero.opts.gazeY=0;}
 if(id===11){hero.opts.expr="strainGrin";hero.opts.sweat=1;hero.opts.gaze=0.8;hero.opts.gazeY=0;}
 if(id===20){hero.opts.expr="panicShock";hero.opts.gaze=0.9;hero.speaker=false;mom.pos=[1.7,0,-1.89];mom.opts.mode="peekDoor";mom.opts.peekP=progress(f,2316,2406);mom.speaker=false;return[hero,mom];}
 if(id===23){hero.opts={kind:"plaidHero",expr:"evilSmirk",mode:"liftMug",mugP:progress(f,2655,2730),gazeY:-0.1};hero.pos[0]=-0.1;}
 return[hero];
};
const definitions:[V3,V3,V3,number,number?][]=[
 [[-1.5,1.5,4.5],[-1.1,1.3,3.9],[0,0.82,0.3],46],
 [[1.4,1.5,4.2],[1.05,1.3,3.6],[-0.65,0.86,0.25],46],
 [[-1.6,1.6,4.6],[-1.2,1.35,3.9],[0,0.85,0.3],46],
 [[1.45,1.45,3.8],[1.05,1.25,3.2],[0,1.0,0.5],44],
 [[-1.25,1.3,3.35],[-0.95,1.15,2.9],[0,1.0,0.55],44],
 [[2.1,5.4,4.5],[1.7,4.9,3.9],[0,1.2,0],46],
 [[-0.85,1.25,2.95],[-0.65,1.15,2.6],[0,1.06,0.65],44,0.055],
 [[2.5,1.9,4.9],[1.98,1.705,4.12],[0,1.2,0],44],
 [[-1.5,1.7,4.7],[-1.15,1.5,4.0],[0.5,1.05,-0.2],46],
 [[2,1.6,4.1],[1.65,1.4,3.5],[0.2,1.2,-0.3],44],
 [[-1.05,1.3,3.2],[-0.78,1.2,2.75],[0,1.06,0.65],44],
 [[1.4,0.75,3.5],[1.05,0.85,2.95],[-0.1,0.8,0.4],44],
 [[-2.1,5.2,4.7],[-1.7,4.7,4.1],[0,1.15,0],46],
 [[1.65,1.7,4.5],[1.3,1.5,3.9],[0.05,0.9,0.35],44],
 [[-2.1,1.0,4.9],[-1.7,1.1,4.25],[0,1.25,0],44],
 [[2.1,1.7,6.3],[1.7,1.5,5.6],[0,1.15,0],44],
 [[-2.1,4.7,4.8],[-1.7,4.2,4.1],[0,1.2,0],46],
 [[1.6,1.6,4.3],[1.2,1.4,3.7],[-0.65,0.9,0.25],44],
 [[0.45,1.25,0.3],[1.2,1.15,-0.3],[1.65,1.04,-1.48],42],
 [[-1.6,1.7,4.4],[-1.2,1.5,3.8],[0.65,1.15,-0.6],46],
 [[1.0,1.3,3.1],[0.75,1.15,2.65],[0,1.06,0.65],44],
 [[-1.25,1.25,3.5],[-0.8,0.9,2.8],[0.9,0.58,0.5],42],
 [[1.6,1.25,4.6],[1.2,1.3,3.85],[-0.05,1.05,0.65],44],
];
export const KICKS=[{f:465,dur:10,amp:0.04,freq:2.1},{f:846,dur:12,amp:0.06,freq:2.4},{f:1425,dur:12,amp:0.10,freq:2.1},{f:2316,dur:10,amp:0.045,freq:1.8}];
const cameras=SHOTS.map((s,i)=>{const[from,to,look,fov,roll]=definitions[i];return makeShotCam({...s,from,to,look,fov,roll,kicks:KICKS,easeShare:s.id===8?0:s.id===10?0.25:[6,14,18,22].includes(s.id)?0.45:0.8,framing:[4,5,7,11,12,19,21,22,23].includes(s.id)?"close":"medium",focus:f=>focusAt(f)});});
export const cameraAt=(f:number)=>cameras[shotAt(f).id-1].camAt(f);
export const dofAt=(f:number)=>cameras[shotAt(f).id-1].dofAt(f);
export const focusAt=(f:number):V3=>{
 const s=shotAt(f),a=castAt(f)[0];
 if(s.id===19)return[1.65,1.04,-1.48];if(s.id===22)return[0.9,0.7,0.5];
 if(a)return[a.pos[0],a.pos[1]+(["toiletSit","pressFlush","sofaPhone"].includes(a.opts.mode)?1.04:1.42),a.pos[2]];
 return[0,s.set==="science"?1.1:1.4,0];
};
