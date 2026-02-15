"""
FREE Text-to-Speech Service - Using Piper TTS
100% Free, No API Costs, Runs Locally
"""

import subprocess
import tempfile
import os
import logging
from typing import Optional
import shutil

logger = logging.getLogger(__name__)


class FreeTTSService:
    """
    Free TTS service using Piper.
    
    Benefits:
    - Completely free (no API costs)
    - Fast (real-time on CPU, even faster on GPU)
    - Good quality natural voices
    - Multiple voices available
    - Works offline
    """
    
    def __init__(self, voice: str = "en_US-lessac-medium"):
        """
        Initialize Piper TTS.
        
        Args:
            voice: Voice model to use
                   Available voices (all FREE):
                   - en_US-lessac-medium - Clear, neutral (RECOMMENDED) ← BEST
                   - en_US-amy-medium - Friendly female
                   - en_US-ryan-medium - Male voice  
                   - en_GB-alan-medium - British male
                   - en_US-libritts-high - High quality (slower)
        """
        self.voice = voice
        
        # Check if piper is installed
        if not shutil.which('piper'):
            raise RuntimeError(
                "Piper TTS not found. Install it with: pip install piper-tts\n"
                "Then download voice: piper --model en_US-lessac-medium --download"
            )
        
        logger.info(f"✅ Free TTS initialized with voice: {voice}")
        logger.info("💰 No API costs - running locally!")
    
    def generate_speech(
        self,
        text: str,
        emotion: Optional[str] = None
    ) -> str:
        """
        Convert text to speech using Piper.
        
        Args:
            text: Text to convert to speech
            emotion: Detected emotion (for voice selection)
        
        Returns:
            Path to generated audio file (WAV format, 16kHz)
        """
        
        # Select voice based on emotion (if multiple voices configured)
        voice = self._select_voice(emotion)
        
        # Create temp output file
        output_fd, output_path = tempfile.mkstemp(suffix='.wav')
        os.close(output_fd)
        
        logger.info(f"Generating speech: '{text[:50]}...'")
        
        try:
            # Run Piper
            # We pipe text to stdin and output to file
            command = [
                'piper',
                '--model', voice,
                '--output_file', output_path
            ]
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send text to stdin
            stdout, stderr = process.communicate(input=text, timeout=30)
            
            if process.returncode == 0:
                logger.info(f"Speech generated: {output_path}")
                return output_path
            else:
                raise Exception(f"Piper failed: {stderr}")
        
        except subprocess.TimeoutExpired:
            process.kill()
            logger.error("Piper TTS timeout")
            raise
        
        except FileNotFoundError:
            raise RuntimeError(
                "Piper command not found. Make sure it's installed:\n"
                "pip install piper-tts\n"
                "piper --model en_US-lessac-medium --download"
            )
        
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            # Cleanup on failure
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise
    
    def _select_voice(self, emotion: Optional[str]) -> str:
        """
        Select voice based on emotion.
        
        For MVP, we use the same voice for all emotions.
        Can be extended to use different voices per emotion if desired.
        """
        # Emotion-based voice mapping (if you have multiple voices)
        voice_mapping = {
            'happy': 'en_US-amy-medium',      # Friendly, upbeat
            'sad': 'en_US-lessac-medium',     # Calm, soothing
            'angry': 'en_US-ryan-medium',     # Steady, grounding
            'neutral': 'en_US-lessac-medium'  # Neutral, clear
        }
        
        # For MVP, use default voice for all
        # Uncomment below to enable emotion-based voice selection:
        # return voice_mapping.get(emotion, self.voice)
        
        return self.voice
    
    def batch_generate(self, texts: list) -> list:
        """
        Generate speech for multiple texts.
        More efficient than calling generate_speech multiple times.
        
        Args:
            texts: List of text strings
        
        Returns:
            List of audio file paths
        """
        audio_paths = []
        
        for text in texts:
            try:
                audio_path = self.generate_speech(text)
                audio_paths.append(audio_path)
            except Exception as e:
                logger.error(f"Batch generation failed for text: {text[:30]}...")
                audio_paths.append(None)
        
        return audio_paths


# Alternative: Coqui TTS (better quality, slower)
class CoquiTTSService:
    """
    Alternative free TTS using Coqui TTS.
    Better quality but slower than Piper.
    """
    
    def __init__(self, model_name: str = "tts_models/en/ljspeech/tacotron2-DDC"):
        """
        Initialize Coqui TTS.
        
        Args:
            model_name: TTS model to use (downloads on first use)
        """
        try:
            from TTS.api import TTS
        except ImportError:
            raise ImportError("Install Coqui TTS: pip install TTS")
        
        logger.info(f"Loading Coqui TTS model: {model_name}")
        logger.info("(This may take a minute on first run...)")
        
        # Load model (downloads on first use)
        self.tts = TTS(model_name=model_name)
        
        logger.info("✅ Coqui TTS initialized")
        logger.info("💰 No API costs - running locally!")
    
    def generate_speech(
        self,
        text: str,
        emotion: Optional[str] = None
    ) -> str:
        """
        Generate speech using Coqui TTS.
        
        Args:
            text: Text to convert
            emotion: Detected emotion (not used in basic model)
        
        Returns:
            Path to generated audio file
        """
        # Create output file
        output_fd, output_path = tempfile.mkstemp(suffix='.wav')
        os.close(output_fd)
        
        logger.info(f"Generating speech (Coqui): '{text[:50]}...'")
        
        try:
            # Generate speech
            self.tts.tts_to_file(text=text, file_path=output_path)
            
            logger.info(f"Speech generated: {output_path}")
            return output_path
        
        except Exception as e:
            logger.error(f"Coqui TTS failed: {e}")
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise


# Singleton instance
_free_tts_service = None

def get_free_tts_service(
    provider: str = "piper",
    voice: str = "en_US-lessac-medium"
) -> FreeTTSService:
    """
    Get or create the global free TTS service instance.
    
    Args:
        provider: 'piper' (recommended) or 'coqui'
        voice: Voice model to use (for piper)
    
    Returns:
        FreeTTSService instance
    """
    global _free_tts_service
    
    if _free_tts_service is None:
        if provider == "piper":
            _free_tts_service = FreeTTSService(voice=voice)
        elif provider == "coqui":
            _free_tts_service = CoquiTTSService()
        else:
            raise ValueError(f"Unknown TTS provider: {provider}")
    
    return _free_tts_service
