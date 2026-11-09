import React from "react";
import {ShortPlayer} from "../../engine";
import {World} from "./world";
import {TOTAL,SHOTS,cameraAt,dofAt} from "./story";
const createWorld=()=>new World();
export const CRUSH_BATHROOM_FRAMES=TOTAL;
/** Subtitles intentionally disabled for this reel, including final export. */
export const CrushBathroomShort:React.FC=()=> <ShortPlayer createWorld={createWorld} shots={SHOTS} camAt={cameraAt} dofAt={dofAt} audio="crush_bathroom/audio.mp3" subs={false}/>;
