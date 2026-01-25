"""
RAVDESS Video Feature Extraction

Extracts ResNet50 embeddings from RAVDESS video files.
"""

import torch
import torchvision
from torchvision import transforms
import cv2
from pathlib import Path
from tqdm import tqdm
import numpy as np

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

def extract_video_features(ravdess_dir, output_dir):
    """
    Extract video features for all RAVDESS files
    """
    ravdess_path = Path(ravdess_dir)
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    
    # Initialize ResNet50
    print("Loading ResNet50...")
    resnet = torchvision.models.resnet50(weights='ResNet50_Weights.DEFAULT')
    resnet = torch.nn.Sequential(*list(resnet.children())[:-1])  # Remove classifier
    resnet.eval()
    
    # Image preprocessing
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    #Find all video files
    # Structure: Video_Speech_Actor_XX/Actor_XX/*.mp4
    video_files = list(ravdess_path.rglob('*.mp4'))
    
    print(f"Found {len(video_files)} video files")
    
    processed = 0
    for video_file in tqdm(video_files, desc="Extracting video"):
        # Parse filename
        info = parse_filename(video_file)
        if info is None:
            continue
        
        try:
            # Open video
            cap = cv2.VideoCapture(str(video_file))
            
            frame_features = []
            frame_count = 0
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # Sample every 5th frame to reduce computational load
                if frame_count % 5 == 0:
                    # Convert BGR to RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    
                    # Preprocess
                    img_tensor = preprocess(frame_rgb).unsqueeze(0)
                    
                    # Extract features
                    with torch.no_grad():
                        features = resnet(img_tensor)
                        features = features.squeeze()  # (2048,)
                    
                    frame_features.append(features)
                
                frame_count += 1
            
            cap.release()
            
            if len(frame_features) == 0:
                print(f"\nWarning: No frames extracted from {video_file.name}")
                continue
            
            # Average frame features
            video_emb = torch.stack(frame_features).mean(dim=0)  # (2048,)
            
            # Save
            output_file = output_path / f"{info['filename']}.pt"
            torch.save(video_emb, output_file)
            processed += 1
            
        except Exception as e:
            print(f"\nError processing {video_file.name}: {e}")
            continue
    
    print(f"\nProcessed {processed} video features")
    print(f"Saved to: {output_path}")

if __name__ == '__main__':
    RAVDESS_DIR = r'D:\multimodal_companion\data\raw\ravdess'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features\ravdess\vision'
    
    extract_video_features(RAVDESS_DIR, OUTPUT_DIR)
