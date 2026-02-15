"""
Download Piper voice model for FREE TTS
Run this once to download the voice model locally.
"""
import requests
import os
import json

VOICE_NAME = "en_US-lessac-medium"
VOICES_DIR = "voices"

def download_piper_voice():
    """Download Piper TTS voice model from HuggingFace"""
    
    # Create voices directory
    os.makedirs(VOICES_DIR, exist_ok=True)
    
    # Voice URLs
    base_url = "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium"
    files = {
        "model": f"{VOICE_NAME}.onnx",
        "config": f"{VOICE_NAME}.onnx.json"
    }
    
    print("=" * 60)
    print("📥 Downloading Piper Voice Model")
    print("=" * 60)
    print(f"\nVoice: {VOICE_NAME}")
    print(f"Destination: {VOICES_DIR}/\n")
    
    for file_type, filename in files.items():
        url = f"{base_url}/{filename}"
        output_path = os.path.join(VOICES_DIR, filename)
        
        # Skip if already downloaded
        if os.path.exists(output_path):
            print(f"✓ {filename} already exists, skipping...")
            continue
        
        print(f"Downloading {filename}...")
        print(f"  URL: {url}")
        
        try:
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            # Get file size
            total_size = int(response.headers.get('content-length', 0))
            
            # Download with progress
            downloaded = 0
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
                        downloaded += len(chunk)
                        
                        # Show progress
                        if total_size > 0:
                            percent = (downloaded / total_size) * 100
                            print(f"  Progress: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='\r')
            
            print(f"\n✅ Downloaded {filename} ({total_size} bytes)")
        
        except Exception as e:
            print(f"❌ Error downloading {filename}: {e}")
            return False
    
    print("\n" + "=" * 60)
    print("✅ Voice model downloaded successfully!")
    print("=" * 60)
    print(f"\nUsage:")
    print(f'  echo "Hello world" | piper --model {VOICES_DIR}\\{VOICE_NAME}.onnx --output_file test.wav')
    print(f"\nOr in Python:")
    print(f'  tts_service = FreeTTSService(voice_path="voices/{VOICE_NAME}.onnx")')
    
    return True

if __name__ == "__main__":
    success = download_piper_voice()
    
    if not success:
        print("\n⚠️ Download failed. Please check your internet connection and try again.")
        exit(1)
