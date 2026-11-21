import React from "react";
import {AbsoluteFill,useCurrentFrame} from "remotion";
import {ShortPlayer} from "../../engine";
import {GandhijiWorld} from "./world";
import {SHOTS,TOTAL,camAt,dofAt,hudAt} from "./story";
const createWorld=()=>new GandhijiWorld();
export const GANDHIJI_SCHOOL_FRAMES=TOTAL;
export const GandhijiSchoolShort:React.FC=()=>{
  const f=useCurrentFrame(),hud=hudAt(f);
  const pill:React.CSSProperties={maxWidth:"100%",boxSizing:"border-box",display:"inline-block",padding:"14px 30px",borderRadius:26,fontFamily:'"Arial Black",Arial,sans-serif',fontWeight:900,fontSize:34,lineHeight:1.25,whiteSpace:"normal",color:"#fffaf0",background:"#182135",border:"3px solid #d6b562",boxShadow:"0 6px 0 rgba(22,18,25,.25)"};
  return <AbsoluteFill>
    <ShortPlayer createWorld={createWorld} shots={SHOTS} camAt={camAt} dofAt={dofAt} audio="gandhiji_school/audio.mp3" subs={false} hud=""/>
    <div style={{position:"absolute",top:"6%",left:"8%",right:"8%",textAlign:"center",pointerEvents:"none"}}><span style={pill}>{hud.title}</span></div>
    {hud.secondary&&<div style={{position:"absolute",top:hud.stamp?"14%":hud.cta?"13%":"12%",left:"8%",right:"8%",textAlign:"center",pointerEvents:"none",transform:`scale(${hud.scale}) rotate(${hud.stamp?-2:0}deg)`}}>
      <span style={{...pill,fontSize:28,padding:"12px 22px",borderRadius:hud.stamp?6:18,background:hud.stamp?"#fff1df":hud.cta?"#8d202e":"#28334e",color:hud.stamp?"#ae2737":"#fff9df",border:`4px solid ${hud.stamp?"#ae2737":"#e7bd51"}`}}>{hud.secondary}</span>
    </div>}
  </AbsoluteFill>;
};
