import React from "react";
import { Composition } from "remotion";
import { BridgeShort, BRIDGE_FRAMES } from "./videos/bridge/Bridge";
import { PardonShort, PARDON_FRAMES } from "./videos/pardon/Bridge";
import { Age18Short, AGE18_FRAMES } from "./videos/age18/Age18";
import { SchoolHeroShort, SCHOOL_FRAMES } from "./videos/school/School";
import { CoasterShort, COASTER_FRAMES } from "./videos/coaster/Coaster";
import { TowerJumpShort, TOWER_JUMP_FRAMES } from "./videos/tower_jump/TowerJump";
import { TowerQwenShort, TOWER_QWEN_FRAMES } from "./videos/tower_qwen/TowerQwen";
import { HotelLiftShort, HOTEL_LIFT_FRAMES } from "./videos/hotel_lift/HotelLift";
import { MolassesTankShort, MOLASSES_TANK_FRAMES } from "./videos/molasses_tank/MolassesTank";
import { InstantSkillShort, INSTANT_SKILL_FRAMES } from "./videos/instant_skill/InstantSkill";
import { ElevatorCrushShort, ELEVATOR_CRUSH_FRAMES } from "./videos/elevator_crush/ElevatorCrush";
import { CrushBathroomShort, CRUSH_BATHROOM_FRAMES } from "./videos/crush_bathroom/CrushBathroom";
import { TestCanvas } from "./TestCanvas";
import { GandhijiSchoolShort, GANDHIJI_SCHOOL_FRAMES } from "./videos/gandhiji_school/GandhijiSchool";

export const RemotionRoot: React.FC = () => (
  <>
    <Composition
      id="BridgeShort"
      component={BridgeShort}
      durationInFrames={BRIDGE_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="PardonShort"
      component={PardonShort}
      durationInFrames={PARDON_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="Age18Short"
      component={Age18Short}
      durationInFrames={AGE18_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="SchoolHeroShort"
      component={SchoolHeroShort}
      durationInFrames={SCHOOL_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="CoasterShort"
      component={CoasterShort}
      durationInFrames={COASTER_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="TowerJumpShort"
      component={TowerJumpShort}
      durationInFrames={TOWER_JUMP_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="TowerQwenShort"
      component={TowerQwenShort}
      durationInFrames={TOWER_QWEN_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="HotelLiftShort"
      component={HotelLiftShort}
      durationInFrames={HOTEL_LIFT_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="MolassesTankShort"
      component={MolassesTankShort}
      durationInFrames={MOLASSES_TANK_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="InstantSkillShort"
      component={InstantSkillShort}
      durationInFrames={INSTANT_SKILL_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition
      id="ElevatorCrushShort"
      component={ElevatorCrushShort}
      durationInFrames={ELEVATOR_CRUSH_FRAMES}
      fps={30}
      width={1080}
      height={1920}
    />
    <Composition id="CrushBathroomShort" component={CrushBathroomShort} durationInFrames={CRUSH_BATHROOM_FRAMES} fps={30} width={1080} height={1920} />
    <Composition id="GandhijiSchoolShort" component={GandhijiSchoolShort} durationInFrames={GANDHIJI_SCHOOL_FRAMES} fps={30} width={1080} height={1920} />
    <Composition
      id="TestCanvas"
      component={TestCanvas}
      durationInFrames={30}
      fps={30}
      width={1080}
      height={1920}
    />
  </>
);
