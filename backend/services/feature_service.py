"""
Feature Service - Coordinates Multimodal Feature Extraction

This service coordinates feature extraction from multiple modalities:
- Audio features (WavLM): 768 dimensions
- Text features (RoBERTa): 768 dimensions  
- Visual features (ResNet): 2048 dimensions

Key responsibilities:
1. Load feature encoders (singleton pattern)
2. Extract features from each modality
3. Optionally stack features for convenience (NOT fusion - just concatenation)
4. Return both individual and stacked features

Note: This does NOT perform fusion - it only extracts and optionally stacks.
True fusion happens in the emotion_classifier MLP.
"""

import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class FeatureService:
    """
    Coordinates feature extraction across all modalities.
    
    Ensures features are extracted efficiently and consistently.
    """
    
    def __init__(self):
        """Initialize feature service (encoders loaded lazily)."""
        self._audio_encoder = None
        self._text_encoder = None
        self._visual_encoder = None
        logger.info("FeatureService initialized")
    
    @property
    def audio_encoder(self):
        """Lazy load audio encoder (WavLM)."""
        if self._audio_encoder is None:
            from feature_extractors.audio_encoder import get_audio_encoder
            self._audio_encoder = get_audio_encoder()
            logger.info("Audio encoder loaded")
        return self._audio_encoder
    
    @property
    def text_encoder(self):
        """Lazy load text encoder (RoBERTa)."""
        if self._text_encoder is None:
            from feature_extractors.text_encoder import SpeechTextPipeline
            self._text_encoder = SpeechTextPipeline()
            logger.info("Text encoder loaded")
        return self._text_encoder
    
    @property
    def visual_encoder(self):
        """Lazy load visual encoder (ResNet)."""
        if self._visual_encoder is None:
            from feature_extractors.visual_encoder import get_visual_encoder
            self._visual_encoder = get_visual_encoder()
            logger.info("Visual encoder loaded")
        return self._visual_encoder
    
    def extract_and_stack_features(
        self,
        audio_path: Optional[str] = None,
        text: Optional[str] = None,
        image_path: Optional[str] = None,
        use_audio: bool = True,
        use_text: bool = True,
        use_visual: bool = False
    ) -> Dict:
        """
        Extract features from specified modalities and optionally stack them.
        
        Args:
            audio_path: Path to audio/video file
            text: Text string
            image_path: Path to image file
            use_audio: Whether to extract audio features
            use_text: Whether to extract text features
            use_visual: Whether to extract visual features
        
        Returns:
            Dictionary with:
            - 'audio': [768] audio features or None
            - 'text': [768] text features or None  
            - 'visual': [2048] visual features or None
            - 'stacked': Concatenated features (for convenience)
            - 'dimension': Total dimension of stacked features
        """
        logger.info(f"Extracting features (A={use_audio}, T={use_text}, V={use_visual})")
        
        features = {}
        feature_arrays = []
        
        # Extract audio features
        if use_audio and audio_path:
            logger.debug("Extracting audio features...")
            import torchaudio
            import torch
            
            try:
                # Handle .webm files: convert to . wav using ffmpeg first
                import subprocess
                import tempfile
                import os
                import soundfile as sf  # Direct soundfile usage (bypasses TorchCodec)
                import torch
                
                if audio_path.endswith('.webm'):
                    logger.info(f"Converting .webm to .wav: {audio_path}")
                    # Create temporary wav file
                    temp_wav = tempfile.mktemp(suffix='.wav')
                    
                    try:
                        # Convert webm to wav using ffmpeg (suppress verbose output)
                        result = subprocess.run([
                            'ffmpeg', 
                            '-i', audio_path,
                            '-ar', '16000',  # 16kHz sample rate
                            '-ac', '1',       # mono
                            '-y',             # overwrite
                            '-loglevel', 'error',  # suppress verbose logs
                            temp_wav
                        ], check=True, capture_output=True, text=True)
                        
                        logger.info(f"✅ Converted to wav: {temp_wav}")
                        
                        # Load with soundfile directly (FAST, no TorchCodec needed!)
                        audio_data, sr = sf.read(temp_wav, dtype='float32')
                        
                        # Clean up temp file
                        os.unlink(temp_wav)
                        
                    except subprocess.CalledProcessError as e:
                        logger.error(f"❌ ffmpeg conversion failed: {e.stderr}")
                        # Clean up if exists
                        if os.path.exists(temp_wav):
                            os.unlink(temp_wav)
                        raise
                else:
                    # Load audio directly with soundfile (FAST, no TorchCodec!)
                    audio_data, sr = sf.read(audio_path, dtype='float32')
                
                # Ensure it's a 1D numpy array (mono)
                if len(audio_data.shape) > 1:
                    audio_data = np.mean(audio_data, axis=1)
                
                # Resample to 16kHz if needed
                if sr != 16000:
                    # Use torch resampler
                    import torchaudio
                    waveform = torch.from_numpy(audio_data).unsqueeze(0)  # Add channel dim
                    resampler = torchaudio.transforms.Resample(sr, 16000)
                    waveform = resampler(waveform)
                    audio_data = waveform.squeeze().numpy()
                
                # Encode with WavLM
                audio_feat = self.audio_encoder.encode(audio_data)
                features['audio'] = audio_feat
                feature_arrays.append(audio_feat)
                logger.info("✅ Audio features extracted successfully")
                
            except Exception as e:
                logger.error(f"❌ Error loading audio: {e}")
                # Fallback to zero features
                features['audio'] = np.zeros(768, dtype=np.float32)
                feature_arrays.append(features['audio'])
                logger.warning("⚠️ Using zero audio features as fallback")
                
        elif use_audio:
            features['audio'] = np.zeros(768, dtype=np.float32)
            feature_arrays.append(features['audio'])
        else:
            features['audio'] = None
        
        # Extract text features
        if use_text and text:
            logger.debug("Extracting text features...")
            # Use text-only encoding (NO Whisper - we already transcribed in Step 1!)
            text_feat = self.text_encoder.encode_text(text)
            features['text'] = text_feat
            feature_arrays.append(text_feat)
        elif use_text:
            features['text'] = np.zeros(768, dtype=np.float32)
            feature_arrays.append(features['text'])
        else:
            features['text'] = None
        
        # Extract visual features
        if use_visual and image_path:
            logger.debug("Extracting visual features...")
            visual_feat = self.visual_encoder.encode(image_path)
            features['visual'] = visual_feat
            feature_arrays.append(visual_feat)
        elif use_visual:
            features['visual'] = np.zeros(2048, dtype=np.float32)
            feature_arrays.append(features['visual'])
        else:
            features['visual'] = None
        
        # Stack features (simple concatenation, NOT fusion)
        if feature_arrays:
            stacked = np.concatenate(feature_arrays)
            features['stacked'] = stacked
            features['dimension'] = stacked.shape[0]
            logger.info(f"Features stacked: {features['dimension']} dimensions")
        else:
            features['stacked'] = None
            features['dimension'] = 0
        
        return features


# Singleton instance
_feature_service_instance = None


def get_feature_service() -> FeatureService:
    """
    Get or create the global feature service instance (singleton).
    
    Returns:
        FeatureService instance
    """
    global _feature_service_instance
    
    if _feature_service_instance is None:
        _feature_service_instance = FeatureService()
    
    return _feature_service_instance
