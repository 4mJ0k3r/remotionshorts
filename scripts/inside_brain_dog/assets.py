"""Stable cel artwork, screen graphics, and a frame-aligned speech envelope."""
from pathlib import Path
import json
import math
import subprocess
import wave

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'renders/inside_brain_dog'
ART = OUT / 'assets'
SOURCE = Path('C:/Users/lavis/Downloads/ElevenLabs_2026-11-14T07_11_11_Viraj - Rich, Confident and Expressive_pvc_s30_sim75_v4.mp3')
SIZE = 1024
INK = '#331c12'
CLEAR = (32, 20, 16, 0)


def crescent(image, mask, shift):
    moved = Image.new('L', image.size)
    moved.paste(mask, shift)
    shadow = ImageChops.subtract(mask, moved).filter(ImageFilter.GaussianBlur(8))
    amount = np.asarray(ImageChops.multiply(shadow, mask), dtype=float) / 255 * .15
    pixels = np.array(image)
    tint = np.array([.48, .60, .78])
    pixels[:, :, :3] = np.clip(pixels[:, :, :3] * (1 - amount[:, :, None] * (1 - tint)), 0, 255)
    return Image.fromarray(pixels)


def head():
    image = Image.new('RGBA', (SIZE, SIZE), CLEAR)
    draw = ImageDraw.Draw(image)
    outer, inner = [], []
    for i in range(300):
        angle = i * math.tau / 300
        radius = 366 * (1 + .022 * math.sin(2 * angle + .6) - .015 * math.cos(3 * angle - .8) + .008 * math.sin(5 * angle + 1.9))
        width = 15 * max(.25, 1 + .52 * math.cos(angle - 2.35) + .22 * math.sin(3 * angle + 1.1) + .14 * math.cos(5 * angle - .7))
        for contour, offset in [(outer, width / 2), (inner, -width / 2)]:
            contour.append((512 + (radius + offset) * math.cos(angle), 535 + (radius + offset) * math.sin(angle)))
    draw.polygon(outer, fill=INK)
    draw.polygon(inner, fill='#fdfaf2')
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).polygon(inner, fill=255)
    image = crescent(image, mask, (58, -40))
    draw = ImageDraw.Draw(image)
    hair = [(148,482),(158,396),(208,306),(292,225),(404,181),(524,170),(650,194),(753,255),(823,345),(865,461),(811,410),(756,428),(690,371),(620,399),(554,349),(487,382),(415,348),(340,411),(270,421),(213,474)]
    draw.polygon(hair, fill='#45230e', outline=INK, width=16)
    draw.line([(210,343),(295,277),(410,231),(523,219),(628,240)], fill='#9c5822', width=13, joint='curve')
    draw.line([(224,368),(305,309),(408,266),(501,253)], fill='#70401d', width=8, joint='curve')
    image.save(ART / 'head.png')


def body():
    image = Image.new('RGBA', (SIZE, SIZE), CLEAR)
    draw = ImageDraw.Draw(image)
    draw.rounded_rectangle((196,62,828,967), radius=181, fill=INK)
    draw.rounded_rectangle((212,78,812,951), radius=165, fill='#4895ef')
    mask = Image.new('L', image.size)
    ImageDraw.Draw(mask).rounded_rectangle((212,78,812,951), radius=165, fill=255)
    image = crescent(image, mask, (35,-25))
    draw = ImageDraw.Draw(image)
    draw.line([(281,192),(281,703),(301,811),(355,850),(665,850),(720,809),(744,702),(744,192)], fill='#edf7ff', width=13, joint='curve')
    draw.polygon([(358,95),(669,95),(512,325)], fill='#fdfaf2')
    draw.polygon([(510,155),(545,207),(522,249),(551,477),(511,540),(472,477),(497,249),(479,207)], fill='#e61919', outline=INK, width=8)
    image.save(ART / 'body.png')


def face(style, amount, blink):
    image = Image.new('RGBA', (SIZE, SIZE), CLEAR)
    draw = ImageDraw.Draw(image)
    for sign in [-1, 1]:
        x, y = 512 + sign * 125, 535
        if blink == 2:
            draw.line((x-33,y,x+33,y), fill='#1c1417', width=11)
        else:
            pupil = Image.new('L', image.size)
            ImageDraw.Draw(pupil).ellipse((x-34,y-46,x+34,y+46), fill=255)
            aperture = Image.new('L', image.size)
            ImageDraw.Draw(aperture).rectangle((x-35,y-(46 if blink == 0 else 10),x+35,y+46), fill=255)
            image.paste('#1c1417', (0,0,SIZE,SIZE), ImageChops.multiply(pupil, aperture))
        by = 416 - (43 if style == 'question' and sign == 1 else 0)
        tilt = -sign * (18 if style == 'serious' else -9)
        draw = ImageDraw.Draw(image)
        draw.line((x-49,by-tilt,x+49,by+tilt), fill=INK, width=19)
    if amount:
        half_w = 57 + amount * 9
        half_h = 12 + amount * 13
        draw.ellipse((512-half_w,669-half_h,512+half_w,669+half_h), fill='#28151b')
        if amount >= 3:
            draw.ellipse((477,678,550,669+half_h-7), fill='#d76374')
        if style == 'smirk':
            draw.rounded_rectangle((457,633,572,646), radius=6, fill='#fdfaf2')
    elif style == 'smirk':
        draw.arc((435,605,600,696), 7, 164, fill=INK, width=15)
    else:
        draw.line((466,664,559,667), fill=INK, width=14)
    image.save(ART / f'face_{style}_{amount}_{blink}.png')


def overlays():
    labels = ["DEEP BIOLOGY QUESTION: 99% DON'T KNOW", 'WHAT ACTUALLY HAPPENS INSIDE?!', 'LIVE INTERNAL FOOTAGE: WATCH THIS']
    for i, text in enumerate(labels):
        image = Image.new('RGBA', (1080,1920), (0,0,0,0))
        draw = ImageDraw.Draw(image)
        font = ImageFont.truetype('C:/Windows/Fonts/arialbd.ttf', 31)
        box = draw.textbbox((0,0), text, font=font)
        width = box[2] - box[0] + 66
        left = (1080-width)//2
        draw.rounded_rectangle((left,134,left+width,222), radius=30, fill='#0d1826', outline='#d4a359', width=4)
        draw.text((540,178), text, font=font, fill='white', anchor='mm')
        image.save(ART / f'hud_{i}.png')
    image = Image.new('RGBA',(1080,1920),'white')
    yy,xx = np.mgrid[:1920,:1080]
    radius = ((xx-540)/760)**2 + ((yy-960)/1340)**2
    value = 1 - .18*np.clip((radius-.45)/.65,0,1)
    pixels = np.array(image)
    pixels[:,:,:3] = (value[:,:,None]*255).astype('uint8')
    Image.fromarray(pixels).save(ART/'vignette.png')


def audio():
    subprocess.run(['ffmpeg','-v','error','-y','-i',str(SOURCE),'-af','atempo=1.01165,apad','-t','5.5','-ar','48000','-ac','1',str(OUT/'narration.wav')],check=True)
    with wave.open(str(OUT/'narration.wav')) as sound:
        samples = np.frombuffer(sound.readframes(sound.getnframes()),dtype='<i2').astype(float)/32768
    chunks = samples[:165*1600].reshape(165,1600)
    rms = np.sqrt(np.mean(chunks**2,axis=1))
    normal = np.clip((rms-.008)/max(.01,np.percentile(rms,92)-.008),0,1)
    envelope=[]
    previous=0
    for value in normal:
        previous = previous*.25 + float(value)*.75
        envelope.append(round(previous*4))
    (ART/'audio_envelope.json').write_text(json.dumps(envelope))


if __name__ == '__main__':
    ART.mkdir(parents=True, exist_ok=True)
    head()
    body()
    for style in ['serious','question','smirk']:
        for amount in range(5):
            for blink in range(3):
                face(style,amount,blink)
    overlays()
    audio()
    print('Created stable cels, three HUDs, and 165 real-audio envelope samples.')
