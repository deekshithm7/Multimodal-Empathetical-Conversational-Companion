import os
import torch
import torchvision.models as models
import torchvision.transforms as transforms
import cv2
from pathlib import Path
from tqdm import tqdm
import numpy as np

def extract_video_features(iemocap_root, output_dir, device='cuda', fps=1):
    """
    Extract ResNet50 visual embeddings from IEMOCAP video files
    
    Args:
        iemocap_root: Path to IEMOCAP_full_release
        output_dir: Path to save cached features (e.g., ../features)
        device: 'cuda' or 'cpu'
        fps: Frames per second to extract (1 fps recommended)
    """
    print(f"Loading ResNet50 model on {device}...")
    
    # Load pretrained ResNet50 and remove final classification layer
    resnet = models.resnet50(pretrained=True)
    # Remove the final FC layer to get 2048-dim features
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
    
    # Process all 5 sessions
    for session_num in range(1, 6):
        session_name = f'Session{session_num}'
        
        # IEMOCAP has .avi files in dialog/avi folder
        avi_dir = iemocap_path / session_name / 'dialog' / 'avi'
        
        if not avi_dir.exists():
            # Some sessions might have different structure
            avi_dir = iemocap_path / session_name / 'sentences' / 'avi'
        
        if not avi_dir.exists():
            print(f"Warning: Video directory not found for {session_name}, skipping...")
            continue
        
        # Create output directory
        output_session_dir = output_path / session_name
        output_session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {session_name}...")
        
        # Get all .avi files (or .mp4 if converted)
        video_files = list(avi_dir.glob('**/*.avi')) + list(avi_dir.glob('**/*.mp4'))
        
        for video_file in tqdm(video_files, desc=f"Session {session_num}"):
            # For dialog-level videos, we'll need to handle them differently
            # For now, extract features from the entire video
            
            try:
                cap = cv2.VideoCapture(str(video_file))
                
                if not cap.isOpened():
                    print(f"Could not open video: {video_file}")
                    continue
                
                video_fps = cap.get(cv2.CAP_PROP_FPS)
                frame_interval = max(1, int(video_fps / fps))  # Extract every Nth frame
                
                frame_features = []
                frame_count = 0
                
                while True:
                    ret, frame = cap.read()
                    if not ret:
                        break
                    
                    # Extract features only at specified intervals
                    if frame_count % frame_interval == 0:
                        # Convert BGR to RGB
                        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                        
                        # Preprocess
                        frame_tensor = preprocess(frame_rgb).unsqueeze(0).to(device)
                        
                        # Extract features
                        with torch.no_grad():
                            features = resnet(frame_tensor)
                            features = features.squeeze().cpu()  # (2048,)
                            frame_features.append(features)
                    
                    frame_count += 1
                
                cap.release()
                
                if len(frame_features) == 0:
                    print(f"No frames extracted from {video_file}")
                    continue
                
                # Average pool across all frames
                video_embedding = torch.stack(frame_features).mean(dim=0)  # (2048,)
                
                # For dialog videos, use the video filename as base
                # For utterance-level videos (if they exist), use utterance ID
                utterance_id = video_file.stem
                
                # Save to file
                output_file = output_session_dir / f'{utterance_id}.pt'
                torch.save(video_embedding, output_file)
                
            except Exception as e:
                print(f"Error processing {video_file}: {e}")
                continue
    
    print(f"\n✓ Video feature caching complete! Saved to {output_path}")
    print("\nNote: IEMOCAP videos are at dialog level, not utterance level.")
    print("You may need to split videos by timestamp or use the same features for all utterances in a dialog.")


if __name__ == '__main__':
    # Configuration
    IEMOCAP_ROOT = r'D:\multimodal_companion\data\raw\iemocap\IEMOCAP_full_release'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features'
    
    # Check CUDA
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    extract_video_features(IEMOCAP_ROOT, OUTPUT_DIR, device=device, fps=1)
