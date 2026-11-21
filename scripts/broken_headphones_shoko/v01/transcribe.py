"""Decode the two supplied inputs and timestamp the original Hindi voice."""
from hashlib import sha256
import json
from pathlib import Path
import subprocess

from faster_whisper import WhisperModel
import numpy as np

HERE=Path(__file__).resolve().parent
DOWNLOADS=Path.home()/"Downloads"
NARRATION=DOWNLOADS/"ElevenLabs_2026-11-20T10_11_18_Viraj - Confident and Natural_pvc_s30_sim75_v4.mp3"
BRAKE=DOWNLOADS/"1_2SoyIDE.mp3"


def source_info(path):
    info=json.loads(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration",
                                             "-of","json",str(path)]))
    return {"file":path.name,"sha256":sha256(path.read_bytes()).hexdigest(),
            "container_seconds":float(info["format"]["duration"])}


if __name__=="__main__":
    raw=subprocess.check_output(["ffmpeg","-nostdin","-v","error","-i",str(NARRATION),"-ar","16000",
                                 "-ac","1","-f","f32le","-"])
    signal=np.frombuffer(raw,"<f4")
    model=WhisperModel("medium",device="cpu",compute_type="int8",cpu_threads=8,local_files_only=True)
    segments,_=model.transcribe(signal,language="hi",beam_size=5,word_timestamps=True,vad_filter=False,
                                 condition_on_previous_text=False)
    entries=[]
    for segment in segments:
        print(round(segment.start,2),round(segment.end,2),segment.text,flush=True)
        for word in segment.words:
            entries.append({"id":f"w{len(entries)+1:03}","text":word.word.strip(),
                            "start":round(word.start,2),"end":round(word.end,2),"kind":"other"})
    (HERE/"transcript.json").write_text(json.dumps({"words":entries,"audio_seconds":len(signal)/16000,
        "source_audio":source_info(NARRATION),"brake_effect":source_info(BRAKE)},indent=2,ensure_ascii=False),
        encoding="utf-8")
