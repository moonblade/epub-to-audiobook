#!/usr/bin/env python3
import sys
from pathlib import Path

import numpy as np
import soundfile as sf
from pydub import AudioSegment

from config import MODEL_FILE, VOICES_FILE, STATIC_PATH
from converter import download_models
from models import VoiceOption

SAMPLE_TEXT = "Hello! This is a sample of my voice. I hope you enjoy listening to audiobooks with me."

SAMPLES_DIR = STATIC_PATH / "samples"


def generate_samples():
    SAMPLES_DIR.mkdir(parents=True, exist_ok=True)
    
    if not MODEL_FILE.exists() or not VOICES_FILE.exists():
        print("Downloading TTS models...")
        if not download_models():
            print("Failed to download models")
            sys.exit(1)
    
    from kokoro_onnx import Kokoro
    kokoro = Kokoro(str(MODEL_FILE), str(VOICES_FILE))
    
    voices = [v.value for v in VoiceOption]
    total = len(voices)
    
    for i, voice in enumerate(voices, 1):
        mp3_path = SAMPLES_DIR / f"{voice}.mp3"
        if mp3_path.exists():
            print(f"[{i}/{total}] Skipping {voice} (exists)")
            continue
        
        print(f"[{i}/{total}] Generating {voice}...")
        
        lang = "en-gb" if voice.startswith("b") else "en-us"
        samples, sample_rate = kokoro.create(SAMPLE_TEXT, voice=voice, speed=1.0, lang=lang)
        
        wav_path = SAMPLES_DIR / f"{voice}.wav"
        sf.write(str(wav_path), np.array(samples), sample_rate)
        
        audio = AudioSegment.from_wav(str(wav_path))
        audio.export(str(mp3_path), format="mp3", bitrate="128k")
        wav_path.unlink()
        
        print(f"[{i}/{total}] Saved {mp3_path.name}")
    
    print(f"\nDone! Generated samples in {SAMPLES_DIR}")


if __name__ == "__main__":
    generate_samples()
