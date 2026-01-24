import os
import json
from pathlib import Path
from tqdm import tqdm

# 4-class emotion mapping
EMOTION_MAP = {
    'neu': 0,  # neutral
    'hap': 1,  # happy
    'exc': 1,  # excited -> happy
    'ang': 2,  # angry
    'sad': 3,  # sad
}

def parse_emotion_file(emotion_file):
    """
    Parse IEMOCAP emotion evaluation file
    Returns dict: {utterance_id: emotion_label}
    """
    emotion_dict = {}
    
    # Try different encodings
    try:
        with open(emotion_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        try:
            with open(emotion_file, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except:
            print(f"Warning: Could not read {emotion_file}, skipping...")
            return emotion_dict
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        
        # Look for lines with emotion labels: [START - END] UTTERANCE_ID EMOTION [V, A, D]
        if line.startswith('[') and '\t' in line:
            parts = line.split('\t')
            if len(parts) >= 3:
                utterance_id = parts[1].strip()
                emotion = parts[2].strip()
                
                # Only include emotions in our 4-class mapping
                if emotion in EMOTION_MAP:
                    emotion_dict[utterance_id] = EMOTION_MAP[emotion]
        
        i += 1
    
    return emotion_dict


def build_index(iemocap_root, features_dir, output_dir):
    """
    Build train/test index JSON files
    
    Args:
        iemocap_root: Path to IEMOCAP_full_release
        features_dir: Path to cached features directory
        output_dir: Where to save train_index.json and test_index.json
    """
    iemocap_path = Path(iemocap_root)
    features_path = Path(features_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    train_data = []
    test_data = []
    
    # Statistics
    total_utterances = 0
    mapped_utterances = 0
    excluded_emotions = 0
    
    # Process all 5 sessions
    for session_num in range(1, 6):
        session_name = f'Session{session_num}'
        emotion_dir = iemocap_path / session_name / 'dialog' / 'EmoEvaluation'
        
        if not emotion_dir.exists():
            print(f"Warning: {emotion_dir} not found, skipping...")
            continue
        
        print(f"\nProcessing {session_name}...")
        
        # Get all emotion evaluation files
        emotion_files = sorted(emotion_dir.glob('*.txt'))
        
        for emotion_file in tqdm(emotion_files, desc=f"Building index for {session_name}"):
            emotions = parse_emotion_file(emotion_file)
            
            for utterance_id, label in emotions.items():
                total_utterances += 1
                
                # Construct paths to cached features
                text_path = features_path / 'text' / session_name / f'{utterance_id}.pt'
                audio_path = features_path / 'audio' / session_name / f'{utterance_id}.pt'
                vision_path = features_path / 'vision' / session_name / f'{utterance_id}.pt'
                
                # Check if at least text and audio exist (vision might be missing)
                if not (text_path.exists() and audio_path.exists()):
                    continue
                
                mapped_utterances += 1
                
                entry = {
                    'id': utterance_id,
                    'session': session_num,
                    'text': str(text_path),
                    'audio': str(audio_path),
                    'vision': str(vision_path) if vision_path.exists() else None,
                    'label': label
                }
                
                # Session 5 is test, Sessions 1-4 are train (standard split)
                if session_num == 5:
                    test_data.append(entry)
                else:
                    train_data.append(entry)
    
    # Save index files
    train_file = output_path / 'train_index.json'
    test_file = output_path / 'test_index.json'
    
    with open(train_file, 'w') as f:
        json.dump(train_data, f, indent=2)
    
    with open(test_file, 'w') as f:
        json.dump(test_data, f, indent=2)
    
    # Print statistics
    print(f"\n{'='*60}")
    print(f"Index Building Complete!")
    print(f"{'='*60}")
    print(f"Total utterances found: {total_utterances}")
    print(f"Mapped to 4 classes: {mapped_utterances}")
    print(f"Train samples (Sessions 1-4): {len(train_data)}")
    print(f"Test samples (Session 5): {len(test_data)}")
    print(f"\nClass distribution:")
    
    # Count class distribution
    train_labels = [item['label'] for item in train_data]
    test_labels = [item['label'] for item in test_data]
    
    class_names = ['neutral', 'happy', 'angry', 'sad']
    print(f"\n{'Class':<10} {'Train':<10} {'Test':<10}")
    print(f"{'-'*30}")
    for idx, name in enumerate(class_names):
        train_count = train_labels.count(idx)
        test_count = test_labels.count(idx)
        print(f"{name:<10} {train_count:<10} {test_count:<10}")
    
    print(f"\nSaved:")
    print(f"  - {train_file}")
    print(f"  - {test_file}")


if __name__ == '__main__':
    # Configuration
    IEMOCAP_ROOT = r'D:\multimodal_companion\data\raw\iemocap\IEMOCAP_full_release'
    FEATURES_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training'
    
    build_index(IEMOCAP_ROOT, FEATURES_DIR, OUTPUT_DIR)
