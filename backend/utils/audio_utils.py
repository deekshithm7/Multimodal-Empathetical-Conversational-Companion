import subprocess
import librosa
import numpy as np
import os
import uuid

TARGET_SR = 16000
DURATION = 15.0
TEMP_DIR = "uploads/audio/tmp"
os.makedirs(TEMP_DIR, exist_ok=True)

def extract_audio(video_path: str, return_wav=False):
    temp_wav = os.path.join(TEMP_DIR, f"{uuid.uuid4().hex}.wav")

    try:
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-i", video_path,
                "-ac", "1",
                "-ar", str(TARGET_SR),
                "-t", str(DURATION),
                temp_wav
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=True
        )

        audio, _ = librosa.load(temp_wav, sr=TARGET_SR)

        target_len = int(TARGET_SR * DURATION)
        if len(audio) < target_len:
            audio = np.pad(audio, (0, target_len - len(audio)))
        else:
            audio = audio[:target_len]

        if return_wav:
            return audio.astype(np.float32), temp_wav

        return audio.astype(np.float32)

    finally:
        if not return_wav and os.path.exists(temp_wav):
            os.remove(temp_wav)
