import React from "react";
import { AbsoluteFill } from "remotion";
import { ThreeCanvas } from "@remotion/three";

const Probe: React.FC = () => (
  <AbsoluteFill style={{ background: "#0000ff" }}>
    <ThreeCanvas width={1080} height={1920} camera={{ position: [0, 0, 5], fov: 40 }}>
      <ambientLight intensity={1} />
      <mesh>
        <boxGeometry args={[2, 3, 2]} />
        <meshBasicMaterial color="red" />
      </mesh>
    </ThreeCanvas>
  </AbsoluteFill>
);

export const TestCanvas: React.FC = () => <Probe />;
