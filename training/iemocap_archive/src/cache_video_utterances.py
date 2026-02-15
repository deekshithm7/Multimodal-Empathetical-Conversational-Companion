import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
from pathlib import Path
from tqdm import tqdm
import numpy as np
import re

def parse_transcript_timestamps(transcript_file):
    """
    Parse transcript file to get utterance IDs and their timestamps
    Returns: {utterance_id: {'start': float, 'end': float, 'text': str}}
    """
    utterances = {}
    
    try:
        with open(transcript_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except UnicodeDecodeError:
        with open(transcript_file, 'r', encoding='latin-1') as f:
            lines = f.readlines()
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
        
        # Parse: Ses01F_impro01_F000 [006.2901-008.2357]: Excuse me.
        match = re.match(r'(\S+)\s+\[(\d+\.\d+)-(\d+\.\d+)\]:\s*(.*)', line)
        if match:
            utterance_id = match.group(1)
            start_time = float(match.group(2))
            end_time = float(match.group(3))
            text = match.group(4)
            
            utterances[utterance_id] = {
                'start': start_time,
                'end': end_time,
                'text': text
            }
    
    return utterances


def extract_utterance_video_features(iemocap_root, output_dir, device='cuda', fps=1):
    """
    Extract ResNet50 visual embeddings from IEMOCAP video files by utterance
    
    Args:
        iemocap_root: Path to IEMOCAP_full_release
        output_dir: Path to save cached features (e.g., ../features)
        device: 'cuda' or 'cpu'
        fps: Frames per second to extract from each utterance clip
    """
    print(f"Loading ResNet50 model on {device}...")
    
    # Load pretrained ResNet50 and remove final classification layer
    resnet = models.resnet50(pretrained=True)
    resnet = torch.nn.Sequential(*list(resnet.children())[:-1])
    resnet = resnet.to(device)
    resnet.eval()
    
    # Image preprocessing
    preprocess = transforms.Compose([
        transforms.ToPILImage(),
        transforms.Resize(256),
        transforms.CenterCrop(224),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    
    iemocap_path = Path(iemocap_root)
    output_path = Path(output_dir) / 'vision'
    
    total_extracted = 0
    total_failed = 0
    
    # Process all 5 sessions
    for session_num in range(1, 6):
        session_name = f'Session{session_num}'
        
        # Get transcript directory
        transcript_dir = iemocap_path / session_name / 'dialog' / 'transcriptions'
        
        # Get video directory  
        avi_dir = iemocap_path / session_name / 'dialog' / 'avi' / 'DivX'
        if not avi_dir.exists():
            avi_dir = iemocap_path / session_name / 'dialog' / 'avi'
        
        if not (transcript_dir.exists() and avi_dir.exists()):
            print(f"Warning: Directories not found for {session_name}, skipping...")
            continue
        
        # Create output directory
        output_session_dir = output_path / session_name
        output_session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {session_name}...")
        
        # Get all transcript files
        transcript_files = sorted(transcript_dir.glob('*.txt'))
        
        for transcript_file in tqdm(transcript_files, desc=f"Session {session_num}"):
            # Parse timestamps
            utterances = parse_transcript_timestamps(transcript_file)
            
            if not utterances:
                continue
            
            # Find corresponding video file
            dialog_name = transcript_file.stem  # e.g., Ses01F_impro01
            video_file = avi_dir / f'{dialog_name}.avi'
            
            if not video_file.exists():
                # Try without gender prefix (some sessions have different naming)
                continue
            
            try:
                cap = cv2.VideoCapture(str(video_file))
                
                if not cap.isOpened():
                    total_failed += len(utterances)
                    continue
                
                video_fps = cap.get(cv2.CAP_PROP_FPS)
                
                # Process each utterance
                for utterance_id, info in utterances.items():
                    start_sec = info['start']
                    end_sec = info['end']
                    duration = end_sec - start_sec
                    
                    if duration <= 0:
                        total_failed += 1
                        continue
                    
                    # Set video position to start time
                    start_frame = int(start_sec * video_fps)
                    end_frame = int(end_sec * video_fps)
                    
                    cap.set(cv2.CAP_PROP_POS_FRAMES, start_frame)
                    
                    frame_features = []
                    current_frame = start_frame
                    
                    # Extract frames at specified fps within this utterance
                    frame_interval = max(1, int(video_fps / fps))
                    
                    while current_frame <= end_frame:
                        ret, frame = cap.read()
                        if not ret:
                            break
                        
                        # Extract features at intervals
                        if (current_frame - start_frame) % frame_interval == 0:
                            # Convert BGR to RGB
                            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                            
                            # Preprocess
                            frame_tensor = preprocess(frame_rgb).unsqueeze(0).to(device)
                            
                            # Extract features
                            with torch.no_grad():
                                features = resnet(frame_tensor)
                                features = features.squeeze().cpu()  # (2048,)
                                frame_features.append(features)
                        
                        current_frame += 1
                    
                    if len(frame_features) == 0:
                        # Use zero features if no frames extracted
                        video_embedding = torch.zeros(2048)
                        total_failed += 1
                    else:
                        # Average pool across all frames in this utterance
                        video_embedding = torch.stack(frame_features).mean(dim=0)  # (2048,)
                        total_extracted += 1
                    
                    # Save to file
                    output_file = output_session_dir / f'{utterance_id}.pt'
                    torch.save(video_embedding, output_file)
                
                cap.release()
                
            except Exception as e:
                print(f"\nError processing {video_file}: {e}")
                total_failed += len(utterances)
                continue
    
    print(f"\n{'='*60}")
    print(f"Video feature extraction complete!")
    print(f"{'='*60}")
    print(f"Successfully extracted: {total_extracted}")
    print(f"Failed/Zero features: {total_failed}")
    print(f"Saved to: {output_path}")


if __name__ == '__main__':
    # Configuration
    IEMOCAP_ROOT = r'D:\multimodal_companion\data\raw\iemocap\IEMOCAP_full_release'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features'
    
    # Check CUDA
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    # Clear previous dialog-level features
    vision_dir = Path(OUTPUT_DIR) / 'vision'
    if vision_dir.exists():
        print(f"\nClearing previous vision features from {vision_dir}...")
        import shutil
        shutil.rmtree(vision_dir)
    
    extract_utterance_video_features(IEMOCAP_ROOT, OUTPUT_DIR, device=device, fps=1)
