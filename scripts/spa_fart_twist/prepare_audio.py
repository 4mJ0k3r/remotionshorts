"""Assemble the 14.90-second track and the speaking mouth envelope."""
from pathlib import Path
import subprocess
import numpy as np
import wave
import json
from timeline import FRAMES

OUT = Path(__file__).resolve().parents[2] / 'renders' / 'spa_fart_twist'
DOWNLOADS = Path(r'C:\Users\lavis\Downloads')
RATE = 48000

def decode(name):
    return np.frombuffer(subprocess.check_output([
        'ffmpeg', '-v', 'error', '-i', str(DOWNLOADS / name), '-ac', '1',
        '-ar', str(RATE), '-f', 'f32le', '-']), dtype='<f4').copy()

def insert(dest, source, source_start, length, dest_start, gain=1):
    count = round(length * RATE)
    start = round(source_start * RATE)
    segment = np.zeros(count, dtype=np.float32)
    available = source[start:start + count]
    segment[:len(available)] = available * gain
    edge = min(count // 2, 144)
    segment[:edge] *= np.linspace(0, 1, edge)
    segment[-edge:] *= np.linspace(1, 0, edge)
    target = round(dest_start * RATE)
    dest[target:target + count] += segment

def main():
    OUT.mkdir(parents=True, exist_ok=True)
    speech = decode('spa-fart-dialogue.mp3')
    effect = decode('fart-meme-sound.mp3')
    mix = np.zeros(FRAMES * (RATE // 30), dtype=np.float32)
    t = np.arange(2 * RATE) / RATE
    pad = sum(np.sin(2*np.pi*hz*t) * gain for hz,gain in [(130.81,.23),(196,.19),(261.63,.14)])
    chime = sum(np.sin(2*np.pi*hz*t)*np.exp(-3*t)*gain for hz,gain in [(523.25,.28),(1046.5,.12)])
    mix[:len(t)] = .12 * (pad + chime) * np.sin(np.pi*t/2)**.7
    insert(mix, effect, 0, 2, 2)
    # A descending resample of the supplied effect leads into a damped floor hit.
    t = np.arange(round(.45 * RATE)) / RATE
    cursor = .12 * RATE + np.cumsum(np.linspace(1.35,.53,len(t)))
    slide = np.interp(cursor,np.arange(len(effect)),effect) * np.sin(np.pi*t/.45)**.64
    insert(mix,slide,0,.45,10.85,.86)
    insert(mix,effect,.03,.23,11.35,.74)
    t = np.arange(round(.75 * RATE)) / RATE
    boom = .40*np.sin(2*np.pi*(41*t+2.6*(1-np.exp(-15*t))))*np.exp(-7*t)
    insert(mix,boom,0,.75,11.35)
    t = np.arange(round(1.35 * RATE)) / RATE
    room = .015*(np.sin(2*np.pi*130.81*t)+.6*np.sin(2*np.pi*196*t))
    insert(mix,room,0,1.35,10.75)
    voice_track = np.zeros_like(mix)
    for start, length, target in [(0,4.10,4), (4.15,2.65,8.10), (7,2.80,12.10)]:
        insert(voice_track, speech, start, length, target)
    mix += voice_track
    mix *= min(1, .93/max(.001, float(np.max(np.abs(mix)))))
    with wave.open(str(OUT/'audio_master.wav'), 'wb') as output:
        output.setparams((1,2,RATE,0,'NONE','not compressed'))
        output.writeframes((mix*32767).astype('<i2').tobytes())
    rms = np.sqrt(np.mean(voice_track.reshape(FRAMES,-1)**2, axis=1))
    reference = np.percentile(rms[rms>.005], 85)
    levels = np.clip((rms-.005)/max(.001,reference),0,1)
    (OUT/'mouth_envelope_v2.json').write_text(json.dumps(levels.tolist()))
    print(f'Prepared {len(mix)/RATE:.3f} s with slide at 10.85, impact at 11.35 and closing dialogue at 12.10')

if __name__ == '__main__':
    main()
