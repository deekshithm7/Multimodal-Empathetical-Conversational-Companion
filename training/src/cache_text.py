import os
import torch
from transformers import AutoTokenizer, AutoModel
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

def extract_text_features(iemocap_root, output_dir, device='cuda'):
    """
    Extract RoBERTa text embeddings from IEMOCAP transcripts
    
    Args:
        iemocap_root: Path to IEMOCAP_full_release
        output_dir: Path to save cached features (e.g., ../features)
        device: 'cuda' or 'cpu'
    """
    print(f"Loading RoBERTa model on {device}...")
    tokenizer = AutoTokenizer.from_pretrained('roberta-base')
    model = AutoModel.from_pretrained('roberta-base').to(device)
    model.eval()
    
    iemocap_path = Path(iemocap_root)
    output_path = Path(output_dir) / 'text'
    
    # Process all 5 sessions
    for session_num in range(1, 6):
        session_name = f'Session{session_num}'
        session_dir = iemocap_path / session_name / 'dialog' / 'transcriptions'
        
        if not session_dir.exists():
            print(f"Warning: {session_dir} not found, skipping...")
            continue
        
        # Create output directory
        output_session_dir = output_path / session_name
        output_session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {session_name}...")
        
        # Get all transcript files
        transcript_files = sorted(session_dir.glob('*.txt'))
        
        for transcript_file in tqdm(transcript_files, desc=f"Session {session_num}"):
            # Try different encodings to handle various file formats
            try:
                with open(transcript_file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
            except UnicodeDecodeError:
                try:
                    with open(transcript_file, 'r', encoding='latin-1') as f:
                        lines = f.readlines()
                except:
                    # Skip files that can't be read
                    print(f"\nWarning: Could not read {transcript_file}, skipping...")
                    continue
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Parse line: "Ses01F_impro01_F000 [006.2901-008.2357]: Excuse me."
                parts = line.split(']:', 1)
                if len(parts) != 2:
                    continue
                
                utterance_id = parts[0].split('[')[0].strip()
                text = parts[1].strip()
                
                if not text:
                    continue
                
                # Tokenize and get embeddings
                inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=512).to(device)
                
                with torch.no_grad():
                    outputs = model(**inputs)
                    # Use CLS token embedding (first token)
                    embedding = outputs.last_hidden_state[:, 0, :].squeeze(0).cpu()  # (768,)
                
                # Save to file
                output_file = output_session_dir / f'{utterance_id}.pt'
                torch.save(embedding, output_file)
    
    print(f"\n✓ Text feature caching complete! Saved to {output_path}")


if __name__ == '__main__':
    # Configuration
    IEMOCAP_ROOT = r'D:\multimodal_companion\data\raw\iemocap\IEMOCAP_full_release'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features'
    
    # Check CUDA
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    extract_text_features(IEMOCAP_ROOT, OUTPUT_DIR, device=device)
