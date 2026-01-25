"""
RAVDESS Audio Feature Extraction (Using pydub + ffmpeg)

This script extracts audio from MP4 video files and creates WavLM embeddings.

Requirements:
- pydub (installed)
- ffmpeg (must be installed separately and in PATH)

Installation for ffmpeg:
1. Download from https://ffmpeg.org/download.html
2. Extract to a folder (e.g., C:\\ffmpeg)
3. Add C:\\ffmpeg\\bin to system PATH
4. Restart terminal/IDE

Or use Chocolatey: choco install ffmpeg
"""

import torch
import torchaudio
from transformers import AutoFeatureExtractor, WavLMModel
from pathlib import Path
from tqdm import tqdm
import tempfile
import os

# Try to import pydub for audio extraction
try:
    from pydub import AudioSegment
    HAS_PYDUB = True
except ImportError:
    HAS_PYDUB = False
    print("ERROR: pydub not installed. Install with: pip install pydub")
    exit(1)

# 4-class emotion mapping
EMOTION_MAP = {
    '01': 0,  # neutral
    '02': 0,  # calm → neutral
    '03': 1,  # happy
    '04': 2,  # sad
    '05': 3,  # angry
    '06': 2,  # fearful → sad
    '07': 3,  # disgust → angry
    '08': 1   # surprised → happy
}

def parse_filename(filename):
    """Parse RAVDESS filename"""
    parts = filename.stem.split('-')
    if len(parts) != 7:
        return None
    
    modality, vocal, emotion, intensity, statement, repetition, actor = parts
    
    # Only speech, not song
    if vocal != '01':
        return None
    
    # Map to 4-class
    if emotion not in EMOTION_MAP:
        return None
    
    return {
        'emotion': EMOTION_MAP[emotion],
        'actor': int(actor),
        'filename': filename.stem
    }

def extract_audio_features(ravdess_dir, output_dir):
    """
    Extract audio features for all RAVDESS files
    """
    ravdess_path = Path(ravdess_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize WavLM
    print("Loading WavLM...")
    feature_extractor = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base')
    model = WavLMModel.from_pretrained('microsoft/wavlm-base', use_safetensors=True)
    model.eval()
    
    # Find all video files (RAVDESS has MP4, extract audio from them)
    # Structure: Video_Speech_Actor_XX/Actor_XX/*.mp4
    audio_files = list(ravdess_path.rglob('*.mp4'))
    
    print(f"Found {len(audio_files)} audio files")
    
    # Test if ffmpeg is available
    try:
        test_audio = AudioSegment.silent(duration=100)  # Test with 100ms silence
        print("✓ pydub + ffmpeg working correctly")
    except Exception as e:
        print(f"\n✗ ERROR: ffmpeg not found or not working!")
        print(f"Error: {e}")
        print("\nPlease install ffmpeg:")
        print("1. Download from https://ffmpeg.org/download.html")
        print("2. Add to system PATH")
        print("3. Or use: choco install ffmpeg")
        exit(1)
    
    processed = 0
    for audio_file in tqdm(audio_files, desc="Extracting audio"):
        # Parse filename
        info = parse_filename(audio_file)
        if info is None:
            continue
        
        try:
            # Extract audio from MP4 using pydub
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as tmp_file:
                tmp_wav_path = tmp_file.name
            
            try:
                # Load MP4 and extract audio
                audio = AudioSegment.from_file(str(audio_file), format="mp4")
                
                # Convert to mono and 16kHz
                audio = audio.set_channels(1).set_frame_rate(16000)
                
                # Export to temporary WAV
                audio.export(tmp_wav_path, format="wav")
                
                # Load with torchaudio
                waveform, sample_rate = torchaudio.load(tmp_wav_path)
            finally:
                # Clean up temp file
                if os.path.exists(tmp_wav_path):
                    os.remove(tmp_wav_path)
            
            # Extract WavLM features
            inputs = feature_extractor(
                waveform.squeeze(0).numpy(),
                sampling_rate=16000,
                return_tensors='pt'
            )
            
            with torch.no_grad():
                outputs = model(inputs.input_values)
                # Mean pool over time
                audio_emb = outputs.last_hidden_state.mean(dim=1).squeeze(0)  # (768,)
            
            # Save
            output_file = output_path / f"{info['filename']}.pt"
            torch.save(audio_emb, output_file)
            processed += 1
            
        except Exception as e:
            print(f"\nError processing {audio_file.name}: {e}")
            continue
    
    print(f"\nProcessed {processed} audio features")
    print(f"Saved to: {output_path}")

if __name__ == '__main__':
    RAVDESS_DIR = r'D:\multimodal_companion\data\raw\ravdess'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features\ravdess\audio'
    
    extract_audio_features(RAVDESS_DIR, OUTPUT_DIR)
