"""
RAVDESS Text Feature Extraction

Extracts RoBERTa embeddings from RAVDESS text (only 2 sentences).
"""

import torch
from transformers import RobertaTokenizer, RobertaModel
from pathlib import Path
from tqdm import tqdm
import re

# 4-class emotion mapping (matching IEMOCAP)
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

# Text content (only 2 statements in RAVDESS)
TEXT_STATEMENTS = {
    '01': "Kids are talking by the door",
    '02': "Dogs are sitting by the door"
}

def parse_filename(filename):
    """
    Parse RAVDESS filename: Modality-VocalChannel-Emotion-Intensity-Statement-Repetition-Actor
    Example: 03-01-06-01-02-01-12.wav
    """
    parts = filename.stem.split('-')
    if len(parts) != 7:
        return None
    
    modality, vocal, emotion, intensity, statement, repetition, actor = parts
    
    # Only process speech (vocal channel 01), not song
    if vocal != '01':
        return None
    
    # Map to 4-class
    if emotion not in EMOTION_MAP:
        return None
    
    return {
        'emotion': EMOTION_MAP[emotion],
        'statement': statement,
        'actor': int(actor),
        'filename': filename.stem
    }

def extract_text_features(ravdess_dir, output_dir):
    """
    Extract text features for all RAVDESS files
    """
    ravdess_path = Path(ravdess_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize RoBERTa
    print("Loading RoBERTa...")
    tokenizer = RobertaTokenizer.from_pretrained('roberta-base')
    model = RobertaModel.from_pretrained('roberta-base')
    model.eval()
    
    # Find all video files (we'll extract text based on filenames)
    # Structure: Video_Speech_Actor_XX/Actor_XX/*.mp4
    audio_files = list(ravdess_path.rglob('*.mp4'))
    
    print(f"Found {len(audio_files)} audio files")
    
    processed = 0
    for audio_file in tqdm(audio_files, desc="Extracting text"):
        # Parse filename
        info = parse_filename(audio_file)
        if info is None:
            continue
        
        # Get text based on statement ID
        text = TEXT_STATEMENTS.get(info['statement'])
        if text is None:
            continue
        
        # Extract RoBERTa embedding
        inputs = tokenizer(text, return_tensors='pt', max_length=512, truncation=True)
        with torch.no_grad():
            outputs = model(**inputs)
            # Use [CLS] token embedding
            text_emb = outputs.last_hidden_state[:, 0, :].squeeze(0)  # (768,)
        
        # Save
        output_file = output_path / f"{info['filename']}.pt"
        torch.save(text_emb, output_file)
        processed += 1
    
    print(f"\nProcessed {processed} text features")
    print(f"Saved to: {output_path}")

if __name__ == '__main__':
    RAVDESS_DIR = r'D:\multimodal_companion\data\raw\ravdess'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features\ravdess\text'
    
    extract_text_features(RAVDESS_DIR, OUTPUT_DIR)
