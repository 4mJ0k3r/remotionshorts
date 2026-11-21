"""Build the v02 contact strip and mux the supplied narration alone."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess
import sys

from PIL import Image, ImageDraw, ImageFont, ImageOps

HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
OUT=ROOT/"renders/broken_headphones_shoko/v02"
END=790
RATE=48000


def read(path):
    return json.loads(path.read_text(encoding="utf-8"))


def paste(canvas, source, location, size, crop=None):
    with Image.open(source) as im:
        sample=im.convert("RGB")
    if crop:
        sample=sample.crop(crop)
    canvas.paste(ImageOps.fit(sample,size,Image.Resampling.LANCZOS),location)


def verification():
    proof=OUT/"cast_stills"
    title=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",32)
    label=ImageFont.truetype("C:/Windows/Fonts/segoeuib.ttf",17)
    card=Image.new("RGB",(1488,754),"#1d1727")
    draw=ImageDraw.Draw(card)
    draw.text((23,18),"BROKEN HEADPHONES / SHOKO   •   V02 VERIFICATION",font=title,fill="#f8e1cd")
    crop=(0,475,1080,1423)
    paste(card,proof/"frame_0901.png",(20,79),(346,303),crop)
    paste(card,proof/"frame_0902.png",(20,384),(346,303),crop)
    for i,f in enumerate((47,449,903),1):
        paste(card,proof/f"frame_{f:04}.png",(20+i*366,79),(346,608))
    for i,text in enumerate(("Boy and Shoko / clean cel faces","f047 / low-lift stride",
                              "f449 / sunny brick street","Year 7 / plaster, lamp and puppy")):
        draw.text((20+i*366,708),text,font=label,fill="#efbfaa")
    card.save(OUT/"part1_v02_verification.png")
    report=read(OUT/"benchmark.json")
    checks=sorted((OUT/report["native_stills_dir"]).glob("frame_*.png"))
    grid=Image.new("RGB",(1056,660),"#1d1727")
    draw=ImageDraw.Draw(grid)
    for i,file in enumerate(checks):
        x,y=i%6*176,i//6*330
        paste(grid,file,(x,y),(176,313))
        draw.text((x+5,y+313),file.stem,font=label,fill="#efbfaa")
    grid.save(OUT/"motion_calibration.jpg",quality=78)


def ff(*args):
    subprocess.run(["ffmpeg","-nostdin","-v","error",*map(str,args)],check=True)


def mux():
    plan=read(HERE/"master_plan.json")
    narration=Path.home()/"Downloads"/plan["source_audio"]["file"]
    if sha256(narration.read_bytes()).hexdigest()!=plan["source_audio"]["sha256"]:
        raise ValueError("Narration checksum mismatch.")
    frames=OUT/"preview_540p_frames"
    missing=[i for i in range(1,END+1) if not (frames/f"frame_{i:04}.png").is_file()]
    if missing:
        raise ValueError(f"Incomplete frame sequence: {missing[:5]}")
    target=OUT/"part1_v02_540p.mp4"
    pending=target.with_stem(target.stem+".pending")
    ff("-y","-framerate",30,"-start_number",1,"-i",frames/"frame_%04d.png","-i",narration,
       "-map","0:v:0","-map","1:a:0","-af",f"aresample={RATE},atrim=end_sample={END*1600}",
       "-frames:v",END,"-c:v","libx264","-preset","fast","-crf",17,"-pix_fmt","yuv420p",
       "-c:a","aac","-b:a","192k","-video_track_timescale",15360,"-movie_timescale",RATE,
       "-movflags","+faststart",pending)
    probe=json.loads(subprocess.check_output(["ffprobe","-v","error","-count_frames","-show_streams",
                  "-of","json",str(pending)]))
    v,a=probe["streams"]
    assert (v["width"],v["height"],v["r_frame_rate"],int(v["nb_read_frames"]))==(540,960,"30/1",END)
    assert all(s["start_pts"]==0 and abs(float(s["duration"])-END/30)<.001 for s in (v,a))
    ff("-xerror","-i",pending,"-map","0:v","-map","0:a","-f","null","-")
    pending.replace(target)
    (OUT/"preview_decode_check.json").write_text(json.dumps(probe,indent=2))
    print(target)


if __name__=="__main__":
    verification()
    if "--proof-only" not in sys.argv:
        mux()
