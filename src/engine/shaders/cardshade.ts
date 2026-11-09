// Character card shading (lighting.md 9.2 / 9.5). Replaces the flat emissive "pasted-on" look: the card takes the
// scene light colour as a tint, keeps a bright floor where a cast shadow falls on it (charShade >=.90), and gets a soft
// side gradient toward the real sun (head ~charGrad, torso ~bodyGrad) with a lavender far side.
// Contract with WORLD: LFB (sun shadow visibility inside three's light loop) and CHAR (uniforms world.ts updates from
// LIGHTS every frame) come from shade.ts; the sun direction is three's own directional light 0.
// The drawing already carries a painted crescent (toon.ts shadedFill / gradFill), so the shader adds GRAD_K of the
// preset gradient, and the preset tint (measured on WHITE heads) is applied at TINT_K so peach skin stays clean
// (lighting.md 9.1 note: golden ~[1, .88, .76], day ~[1, .97, .96] for peach skin).
import * as THREE from "three";
import { LFB, CHAR } from "./shade";

export const GRAD_K = 2.4;   // gentle form shade; the drawing already contains a cream crescent
export const GRAD_KB = 0.9;
export const TINT_K = 0.55;

// Card zones in UV (v = 1 at the top): chin y ~380 -> v .62, centre y235 -> v .765.
// Organic HEAD_R145 silhouette retains the same card design box and shader chin transition.
const CARD = /* glsl */ `
vec3 tintK = mix( vec3( 1.0 ), uCharTint, uTintK );
tintK /= pow( max( dot( tintK, vec3( 0.2126, 0.7152, 0.0722 ) ), 0.2 ), uNorm );             // same face value day and golden
vec3 outgoingLight = diffuseColor.rgb * tintK;
#if NUM_DIR_LIGHTS > 0
{
  vec3 sunV = directionalLights[ 0 ].direction;                                          // view space, towards the sun
  vec3 upV = normalize( ( viewMatrix * vec4( 0.0, 1.0, 0.0, 0.0 ) ).xyz );
  float side = sign( sunV.x ) * smoothstep( 0.0, 0.35, abs( sunV.x ) );                     // saturates: even a near-frontal sun shades one side                                          // + = sun on screen right
  float head = smoothstep( 0.60, 0.64, vMapUv.y );                                       // HEAD_R = 145, centre y = 235, chin y ~380 (UV ~0.62)
  float hw = mix( 0.14, 0.245, head );                                                    // torso half 86 / head half 145 units
  float uu = clamp( ( vMapUv.x - 0.5 ) / hw, -1.0, 1.0 ) * sign( dFdx( vMapUv.x ) + 1e-7 ); // -1..1 screen left..right
  float t = uu * side;                                                                     // +1 = edge facing the sun
  float g = mix( uBodyGrad * uGradKB, min( uGrad * uGradK, 0.44 ), head );
  float dark = smoothstep( -0.65, 0.55, -t );                                             // soft form shadow: ramps over the far half, not only the rim
  vec3 sideK = mix( vec3( 1.0 ), uSideTint, dark * clamp( g / max( min( uGrad * uGradK, 0.44 ), 1e-3 ), 0.0, 1.5 ) * 0.85 );
  float top = 1.0 + 0.055 * clamp( ( vMapUv.y - 0.69 ) / 0.11, -1.0, 1.0 ) * clamp( dot( sunV, upV ) * 2.0, 0.0, 1.0 ) * head;
  float lift = 1.0 + 0.06 * smoothstep( 0.0, 0.9, t );
  outgoingLight *= mix( max( uCharShade, 0.90 ), 1.0, sunVis ) * ( 1.0 - g * dark ) * sideK * top * lift;
  #ifdef USE_MAP
  {
    // INNER warm rim, golden only: the outermost ~2 px (at 1080 wide) of the HEAD skin / TORSO silhouette on the
    // sun-facing edge. No offset copy: we only test whether the next pixels toward the sun are outside the card.
    // Hats, legs, rifles and other thin parts are skipped (inner sample must be skin, or torso at least ~40 units thick).
    float warm = smoothstep( 0.2, 0.4, 1.0 - uCharTint.b );
    float sl = length( sunV.xy );
    vec2 d2 = sunV.xy / max( sl, 1e-4 );
    vec2 duv = 2.0 * uPx * ( d2.x * dFdx( vMapUv ) + d2.y * dFdy( vMapUv ) );
    float edge = step( texture2D( map, vMapUv + duv ).a, 0.5 );
    vec2 dirU = normalize( duv + vec2( 1e-9 ) );
    vec4 c1 = texture2D( map, vMapUv - dirU * vec2( 0.027, 0.016 ) );   // ~16 design units inward (past the ink line)
    vec4 c2 = texture2D( map, vMapUv - dirU * vec2( 0.067, 0.04 ) );    // ~40 units inward: thick parts only
    float skin = step( 0.5, c1.a ) * step( 0.3, c1.r ) * step( c1.b + 0.12, c1.r ) * step( c1.g, c1.r + 0.02 );
    float torso = step( 0.27, vMapUv.y ) * step( vMapUv.y, 0.57 ) * step( 0.5, c1.a ) * step( 0.5, c2.a ) * step( 0.04, max( c1.r, max( c1.g, c1.b ) ) );
    float rim = warm * smoothstep( 0.1, 0.4, sl ) * edge * max( skin * head, torso ) * mix( 0.6, 1.0, sunVis );
    outgoingLight += vec3( 0.95, 0.52, 0.16 ) * rim;
  }
  #endif
}
#endif
outgoingLight *= uGain;
float cardLuma = dot( outgoingLight, vec3( 0.2126, 0.7152, 0.0722 ) );
outgoingLight = max( mix( vec3( cardLuma ), outgoingLight, 1.18 ), vec3( 0.0 ) );
`;

const DECL = "#include <common>\nuniform vec3 uCharTint; uniform float uCharShade; uniform float uGrad; uniform float uBodyGrad; uniform vec3 uSideTint;"
  + " uniform float uGradK; uniform float uGradKB; uniform float uTintK; uniform float uNorm; uniform float uGain; uniform float uPx;";
/** card-only constants (not per light): gradient share, tint share, overall gain (calibrated: faces ~.93 V) */
export const CARD_K = { uGradK: { value: GRAD_K }, uGradKB: { value: GRAD_KB }, uTintK: { value: TINT_K }, uNorm: { value: 0.7 }, uGain: { value: 1.12 }, uPx: { value: 0.5 } }; // uPx = render height / 1920

/** MeshLambertMaterial -> lit card: no emissive, scene tint, bright floor, side gradient toward the sun. */
export function cardShade(m: THREE.MeshLambertMaterial) {
  m.emissive.set(0x000000); m.emissiveIntensity = 0; m.emissiveMap = null;
  m.onBeforeCompile = (sh) => {
    Object.assign(sh.uniforms, CHAR, CARD_K);
    sh.fragmentShader = sh.fragmentShader
      .replace("#include <common>", DECL)
      .replace("#include <lights_fragment_begin>", "float sunVis = 1.0;\n" + LFB)
      .replace("vec3 outgoingLight = reflectedLight.directDiffuse + reflectedLight.indirectDiffuse + totalEmissiveRadiance;", CARD);
  };
  m.customProgramCacheKey = () => "card11-marker-vivid";
  return m;
}

/** ground contact blob: multiplies what is already drawn (the ground); drawn after the ground and before the cards */
export const blobMaterial = (map: THREE.Texture) => new THREE.MeshBasicMaterial({
  map, transparent: false, depthWrite: false, fog: false, toneMapped: false,
  blending: THREE.CustomBlending, blendEquation: THREE.AddEquation, blendSrc: THREE.ZeroFactor, blendDst: THREE.SrcColorFactor,
  polygonOffset: true, polygonOffsetFactor: -2, polygonOffsetUnits: -2, side: THREE.DoubleSide,
});
