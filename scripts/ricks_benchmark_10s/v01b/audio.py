"""Synthesize an original ten-second stereo bed on the 30 fps scene timeline."""
import math
from pathlib import Path
import wave

import numpy as np

RATE = 48000
SECONDS = 10
ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "renders/ricks_benchmark_10s/v01b/ricks_benchmark_sfx.wav"


def main():
    rng = np.random.default_rng(36811)
    mix = np.zeros((RATE*SECONDS,2))

    def layer(start, length, generator, gain, pan=0):
        first = round(start*RATE)
        duration = min(round(length*RATE),len(mix)-first)
        time = np.arange(duration)/RATE
        mono = generator(time)
        attack = np.minimum(1,time/.009)
        release = np.minimum(1,(duration/RATE-time)/.025)
        balance = np.sqrt((1+np.array([-pan,pan]))/2)
        mix[first:first+duration] += (mono*attack*release*gain)[:,None]*balance

    def osc(t, h):
        return np.sin(math.tau*h*t)

    def noise(t):
        return rng.normal(0,1,len(t))

    for tone, pan in [(49.0,-.3),(73.43,.23),(98.10,.1),(146.04,-.18)]:
        layer(0,9.94,lambda t,h=tone: osc(t,h)*(0.56+0.25*osc(t,.31))*
              (.46+.54*np.clip(t*.9,0,1))*np.where(t<8.75,1,.43),.061,pan)
    for i,start in enumerate(np.arange(.25,3.1,.51)):
        layer(float(start),.095,lambda t: np.exp(-55*t)*(.68*osc(t,1720)+.32*noise(t)),
              .095,(-1)**i*.19)
    for i in range(8):
        layer(3.13+i*.11,.38,lambda t,h=550+i*160: np.exp(-10*t)*(.6*osc(t,h)+.4*osc(t,1.503*h)),
              .070,math.sin(i)*.40)
    layer(3.32,1.39,lambda t: np.sin(np.pi*t/1.39)**1.3 *
          (.39*noise(t)+.61*np.sin(math.tau*(78*t+103*t**2))),.16)
    for pan in (-.65,.65):
        layer(4.43,5.57,lambda t: .23*(noise(t)-np.roll(noise(t),1))*
              (0.65+.35*np.minimum(1,t*3)),.085,pan)
    for i,start in enumerate(np.arange(4.66,7.26,.20)):
        layer(float(start),.14,lambda t: np.exp(-33*t)*(.62*osc(t,110)+.38*noise(t)),
              .122,(-1)**i*.24)
    layer(7.5,.87,lambda t: np.exp(-4.4*t)*np.sin(math.tau*(56*t-10*t**2)),.42)
    for note,pan in [(311,-.28),(466,.27),(698,.05)]:
        layer(8.10,1.,lambda t,h=note: np.exp(-3.6*t)*np.sin(math.tau*h*t+2*osc(t,8)),
              .106,pan)
    layer(8.82,.36,lambda t: np.exp(-6*t)*(.6*np.sin(math.tau*(460*t-360*t*t))+
                                           .4*np.sign(osc(t,178))*noise(t)),.24,-.1)
    layer(8.93,.26,lambda t: np.exp(-9*t)*(osc(t,236)+.28*osc(t,540)),.22,.06)
    peak = np.max(np.abs(mix))
    if peak > .70:
        mix *= .70/peak
    with wave.open(str(OUT),"wb") as file:
        file.setnchannels(2)
        file.setsampwidth(2)
        file.setframerate(RATE)
        file.writeframes(np.round(mix*32767).astype("<i2").tobytes())
    print(f"{OUT} | {len(mix)/RATE:.3f}s | peak {np.max(np.abs(mix)):.3f}")


if __name__ == "__main__":
    main()
