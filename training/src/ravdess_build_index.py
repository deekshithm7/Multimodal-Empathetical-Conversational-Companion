"""
RAVDESS Dataset Index Builder

Builds train/test split based on actor ID (odd=train, even=test).
Maps to 4-class emotions.
"""

import json
from pathlib import Path
from collections import Counter

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

EMOTION_NAMES = ['neutral', 'happy', 'sad', 'angry']

def parse_filename(filename):
    """Parse RAVDESS filename"""
    parts = filename.stem.split('-')
    if len(parts) != 7:
        return None
    
    modality, vocal, emotion, intensity, statement, repetition, actor = parts
    
    # Only speech
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

def build_index(features_dir, output_dir):
    """
    Build train/test index for RAVDESS
    """
    features_path = Path(features_dir)
    output_path = Path(output_dir)
    
    # Find all text features (use as reference)
    text_dir = features_path / 'text'
    text_files = sorted(list(text_dir.glob('*.pt')))
    
    print(f"Found {len(text_files)} text features")
    
    train_data = []
    test_data = []
    
    for text_file in text_files:
        info = parse_filename(text_file)
        if info is None:
            continue
        
        # Check if corresponding audio and vision features exist
        audio_file = features_path / 'audio' / f"{info['filename']}.pt"
        vision_file = features_path / 'vision' / f"{info['filename']}.pt"
        
        if not audio_file.exists():
            print(f"Warning: Missing audio for {info['filename']}")
            continue
        
        if not vision_file.exists():
            print(f"Warning: Missing vision for {info['filename']}")
            continue
        
        # Create index entry
        entry = {
            'text': str(text_file),
            'audio': str(audio_file),
            'vision': str(vision_file),
            'label': info['emotion'],
            'actor': info['actor']
        }
        
        # Split by actor: odd=train, even=test
        if info['actor'] % 2 == 1:
            train_data.append(entry)
        else:
            test_data.append(entry)
    
    # Save indexes
    train_file = output_path / 'ravdess_train_index.json'
    test_file = output_path / 'ravdess_test_index.json'
    
    with open(train_file, 'w') as f:
        json.dump(train_data, f, indent=2)
    
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Print statistics
    print(f"\n{'='*60}")
    print("RAVDESS Dataset Index")
    print(f"{'='*60}")
    print(f"\nTrain samples: {len(train_data)}")
    print(f"Test samples: {len(test_data)}")
    print(f"Total: {len(train_data) + len(test_data)}")
    
    # Class distribution
    train_labels = [entry['label'] for entry in train_data]
    test_labels = [entry['label'] for entry in test_data]
    
    train_dist = Counter(train_labels)
    test_dist = Counter(test_labels)
    
    print(f"\nTrain distribution:")
    for i, name in enumerate(EMOTION_NAMES):
        print(f"  {name}: {train_dist[i]}")
    
    print(f"\nTest distribution:")
    for i, name in enumerate(EMOTION_NAMES):
        print(f"  {name}: {test_dist[i]}")
    
    # Actor split
    train_actors = sorted(set(entry['actor'] for entry in train_data))
    test_actors = sorted(set(entry['actor'] for entry in test_data))
    
    print(f"\nTrain actors (odd): {train_actors}")
    print(f"Test actors (even): {test_actors}")
    
    print(f"\nSaved:")
    print(f"  {train_file}")
    print(f"  {test_file}")

if __name__ == '__main__':
    FEATURES_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features\ravdess'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training'
    
    build_index(FEATURES_DIR, OUTPUT_DIR)
