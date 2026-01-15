import subprocess
import librosa
import os
import uuid
import tempfile

TARGET_SR = 16000

def extract_audio(video_path, return_wav=False):
    tmp_dir = tempfile.gettempdir()
    wav_path = os.path.join(tmp_dir, f"{uuid.uuid4().hex}.wav")

    cmd = [
        "ffmpeg",
        "-y",
        "-i", video_path,
        "-vn",
        "-ac", "1",
        "-ar", str(TARGET_SR),
        "-acodec", "pcm_s16le",
        wav_path
    ]

    subprocess.run(cmd, check=True)

    audio, sr = librosa.load(wav_path, sr=TARGET_SR)

    if return_wav:
        return audio, wav_path

    os.remove(wav_path)
    return audio
