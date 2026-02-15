"""
MECC Audio Transcription Service
Uses OpenAI Whisper for accurate speech-to-text conversion.
"""

import whisper
import torch
import logging
from typing import Optional, Dict
import os

logger = logging.getLogger(__name__)


class WhisperService:
    """
    Audio transcription service using Whisper.
    Converts speech to text for emotion analysis.
    """
    
    def __init__(self, model_size: str = 'base', device: str = 'cuda'):
        """
        Initialize Whisper model.
        
        Args:
            model_size: 'tiny', 'base', 'small', 'medium', 'large'
                       tiny: fastest, least accurate (~39M params, ~74MB)
                       base: good balance (~74M params, ~142MB) ← RECOMMENDED for MVP
                       small: better accuracy (~244M params, ~466MB)
                       medium: high accuracy (~769M params, ~1.5GB)
                       large: best accuracy (~1550M params, ~2.9GB)
            
            device: 'cuda' or 'cpu'
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        
        logger.info(f"Loading Whisper model: {model_size} on {self.device}")
        
        try:
            self.model = whisper.load_model(model_size, device=str(self.device))
            logger.info(f"✅ Whisper model '{model_size}' loaded successfully")
        except Exception as e:
            logger.error(f"❌ Failed to load Whisper model: {e}")
            raise
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = 'en'
    ) -> Dict[str, any]:
        """
        Transcribe audio file to text.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, M4A, etc.)
            language: Language code (e.g., 'en', 'es', 'fr')
                     Set to None for automatic detection
        
        Returns:
            Dictionary containing:
                - text: Transcribed text
                - language: Detected language
                - segments: List of timestamped segments
                - confidence: Average confidence score
        """
        logger.info(f"Transcribing audio: {audio_path}")
        
        try:
            # Transcribe with Whisper
            result = self.model.transcribe(
                audio_path,
                language=language,
                fp16=(self.device.type == 'cuda'),  # Use FP16 on GPU for speed
                verbose=False
            )
            
            # Extract text
            text = result['text'].strip()
            
            # Calculate average confidence if segments available
            confidence = self._calculate_confidence(result.get('segments', []))
            
            logger.info(f"Transcription complete: '{text[:50]}...' (confidence: {confidence:.2f})")
            
            return {
                'text': text,
                'language': result.get('language', 'unknown'),
                'segments': result.get('segments', []),
                'confidence': confidence
            }
        
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            raise
    
    def transcribe_batch(self, audio_paths: list) -> list:
        """
        Transcribe multiple audio files.
        Useful for chunked audio processing.
        
        Args:
            audio_paths: List of audio file paths
        
        Returns:
            List of transcription results
        """
        results = []
        
        for audio_path in audio_paths:
            result = self.transcribe(audio_path)
            results.append(result)
        
        return results
    
    def _calculate_confidence(self, segments: list) -> float:
        """
        Calculate average confidence from segments.
        Whisper doesn't provide direct confidence scores,
        so we use average log probability as a proxy.
        """
        if not segments:
            return 0.0
        
        # Use average log probability (if available)
        try:
            log_probs = [seg.get('avg_logprob', 0) for seg in segments]
            avg_log_prob = sum(log_probs) / len(log_probs)
            
            # Convert log prob to approximate confidence (0-1)
            # Log probs are typically negative, closer to 0 is better
            confidence = min(1.0, max(0.0, 1.0 + avg_log_prob))  # Rough approximation
            
            return confidence
        except:
            return 0.5  # Default moderate confidence


# Alternative: OpenAI API-based Whisper (no local model needed)
class WhisperAPIService:
    """
    Whisper transcription using OpenAI API.
    Doesn't require local model download.
    """
    
    def __init__(self, api_key: Optional[str] = None):
        try:
            from openai import OpenAI
        except ImportError:
            raise ImportError("Install openai: pip install openai")
        
        api_key = api_key or os.environ.get('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY not set")
        
        self.client = OpenAI(api_key=api_key)
        logger.info("✅ Whisper API service initialized")
    
    def transcribe(
        self,
        audio_path: str,
        language: Optional[str] = 'en'
    ) -> Dict[str, any]:
        """
        Transcribe audio using OpenAI Whisper API.
        
        Args:
            audio_path: Path to audio file
            language: Language code (optional)
        
        Returns:
            Transcription result dictionary
        """
        logger.info(f"Transcribing audio via API: {audio_path}")
        
        try:
            with open(audio_path, 'rb') as audio_file:
                response = self.client.audio.transcriptions.create(
                    model="whisper-1",
                    file=audio_file,
                    language=language,
                    response_format="verbose_json"
                )
            
            text = response.text.strip()
            
            logger.info(f"Transcription complete: '{text[:50]}...'")
            
            return {
                'text': text,
                'language': response.language,
                'duration': response.duration,
                'segments': response.segments if hasattr(response, 'segments') else [],
                'confidence': 0.9  # API doesn't provide confidence, assume high
            }
        
        except Exception as e:
            logger.error(f"API transcription failed: {e}")
            raise
    
    def transcribe_batch(self, audio_paths: list) -> list:
        """Transcribe multiple audio files"""
        results = []
        
        for audio_path in audio_paths:
            result = self.transcribe(audio_path)
            results.append(result)
        
        return results


# Singleton instance
_whisper_service_instance = None

def get_whisper_service(use_api: bool = False, model_size: str = 'base', device: str = 'cuda'):
    """
    Get or create the global Whisper service instance.
    
    Args:
        use_api: If True, use OpenAI API instead of local model
        model_size: Model size for local Whisper
        device: Device for local model
    
    Returns:
        WhisperService or WhisperAPIService instance
    """
    global _whisper_service_instance
    
    if _whisper_service_instance is None:
        if use_api:
            _whisper_service_instance = WhisperAPIService()
        else:
            _whisper_service_instance = WhisperService(model_size=model_size, device=device)
    
    return _whisper_service_instance


# Utility function for integrated transcription + emotion analysis
def transcribe_and_analyze(audio_path: str, emotion_service) -> Dict:
    """
    Combined transcription and emotion analysis.
    
    Args:
        audio_path: Path to audio file
        emotion_service: EmotionRecognitionService instance
    
    Returns:
        Dictionary with transcription and emotion results
    """
    # Transcribe
    whisper = get_whisper_service()
    transcription = whisper.transcribe(audio_path)
    
    # Analyze emotion (audio + text)
    emotion_result = emotion_service.predict_emotion(
        audio_path=audio_path,
        text=transcription['text']
    )
    
    return {
        'transcript': transcription['text'],
        'language': transcription['language'],
        'transcription_confidence': transcription['confidence'],
        'emotion': emotion_result['emotion'],
        'emotion_confidence': emotion_result['confidence'],
        'emotion_probabilities': emotion_result['probabilities']
    }
