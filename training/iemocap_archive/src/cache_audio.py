import os
import torch
import torchaudio
from transformers import AutoFeatureExtractor, WavLMModel
from pathlib import Path
from tqdm import tqdm

def extract_audio_features(iemocap_root, output_dir, device='cuda'):
    """
    Extract WavLM audio embeddings from IEMOCAP wav files
    
    Args:
        iemocap_root: Path to IEMOCAP_full_release
        output_dir: Path to save cached features (e.g., ../features)
        device: 'cuda' or 'cpu'
    """
    print(f"Loading WavLM model on {device}...")
    feature_extractor = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base')
    model = WavLMModel.from_pretrained('microsoft/wavlm-base', use_safetensors=True).to(device)
    model.eval()
    
    iemocap_path = Path(iemocap_root)
    output_path = Path(output_dir) / 'audio'
    
    # Process all 5 sessions
    for session_num in range(1, 6):
        session_name = f'Session{session_num}'
        wav_dir = iemocap_path / session_name / 'sentences' / 'wav'
        
        if not wav_dir.exists():
            print(f"Warning: {wav_dir} not found, skipping...")
            continue
        
        # Create output directory
        output_session_dir = output_path / session_name
        output_session_dir.mkdir(parents=True, exist_ok=True)
        
        print(f"\nProcessing {session_name}...")
        
        # Get all subdirectories (e.g., Ses01F_impro01, Ses01M_script01_1, etc.)
        subdirs = sorted([d for d in wav_dir.iterdir() if d.is_dir()])
        
        for subdir in tqdm(subdirs, desc=f"Session {session_num}"):
            # Get all wav files in this subdirectory
            wav_files = sorted(subdir.glob('*.wav'))
            
            for wav_file in wav_files:
                utterance_id = wav_file.stem  # e.g., "Ses01F_impro01_F000"
                
                try:
                    # Load audio
                    waveform, sample_rate = torchaudio.load(wav_file)
                    
                    # Resample to 16kHz if necessary
                    if sample_rate != 16000:
                        resampler = torchaudio.transforms.Resample(sample_rate, 16000)
                        waveform = resampler(waveform)
                    
                    # Convert stereo to mono if necessary
                    if waveform.shape[0] > 1:
                        waveform = torch.mean(waveform, dim=0, keepdim=True)
                    
                    # Process with WavLM
                    inputs = feature_extractor(waveform.squeeze(0).numpy(), sampling_rate=16000, return_tensors='pt')
                    input_values = inputs.input_values.to(device)
                    
                    with torch.no_grad():
                        outputs = model(input_values)
                        # Mean pool over time dimension
                        embedding = outputs.last_hidden_state.mean(dim=1).squeeze(0).cpu()  # (768,)
                    
                    # Save to file
                    output_file = output_session_dir / f'{utterance_id}.pt'
                    torch.save(embedding, output_file)
                    
                except Exception as e:
                    print(f"Error processing {wav_file}: {e}")
                    continue
    
    print(f"\n✓ Audio feature caching complete! Saved to {output_path}")


if __name__ == '__main__':
    # Configuration
    IEMOCAP_ROOT = r'D:\multimodal_companion\data\raw\iemocap\IEMOCAP_full_release'
    OUTPUT_DIR = r'd:\Multimodal-Empathetical-Conversational-Companion\training\features'
    
    # Check CUDA
    device = 'cuda' if torch.cuda.is_available() else 'cpu'
    print(f"Using device: {device}")
    
    extract_audio_features(IEMOCAP_ROOT, OUTPUT_DIR, device=device)
