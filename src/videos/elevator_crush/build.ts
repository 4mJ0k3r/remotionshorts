import * as THREE from "three";
import {kit3d} from "../../engine";
export const buildSets=()=>{
 const root=new THREE.Group();
 const cabin=kit3d.buildElevatorCabin({parent:root});
 const corridor=kit3d.buildRainCorridor({parent:root});
 const shaft=kit3d.cyl(cabin.root,0.018,0.018,1,kit3d.lit("fan-link","#d2b25b"),0,0,0,10);
 shaft.visible=false;
 return {root,cabin,corridor,shaft};
};
