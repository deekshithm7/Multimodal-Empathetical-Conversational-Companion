"""
MECC Emotion Recognition Service
Handles audio+text emotion detection using the trained IEMOCAP A+T model.
"""

import torch
import torch.nn.functional as F
from transformers import AutoFeatureExtractor, AutoModel, AutoTokenizer
import librosa
import numpy as np
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


class EmotionRecognitionService:
    """
    Emotion recognition service using Audio (WavLM) + Text (RoBERTa) fusion.
    
    Achieves 70.7% accuracy on IEMOCAP 4-class emotion recognition:
    - Neutral (0)
    - Happy (1)
    - Angry (2)
    - Sad (3)
    """
    
    def __init__(self, checkpoint_path: str = 'checkpoints/at.pth', device: str = 'cuda'):
        """
        Initialize the emotion recognition service.
        
        Args:
            checkpoint_path: Path to the trained model checkpoint (at.pth)
            device: Device to run inference on ('cuda' or 'cpu')
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        logger.info(f"Initializing EmotionRecognitionService on {self.device}")
        
        # Load audio encoder (WavLM-base)
        logger.info("Loading WavLM audio encoder...")
        self.audio_processor = AutoFeatureExtractor.from_pretrained('microsoft/wavlm-base')
        self.audio_model = AutoModel.from_pretrained('microsoft/wavlm-base').to(self.device)
        self.audio_model.eval()
        
        # Load text encoder (RoBERTa-base)
        logger.info("Loading RoBERTa text encoder...")
        self.text_tokenizer = AutoTokenizer.from_pretrained('roberta-base')
        self.text_model = AutoModel.from_pretrained('roberta-base').to(self.device)
        self.text_model.eval()
        
        # Load trained emotion classifier
        logger.info(f"Loading emotion classifier from {checkpoint_path}...")
        from models.fusion_mlp import FusionMLP
        
        checkpoint = torch.load(checkpoint_path, map_location=self.device)
        self.classifier = FusionMLP(use_v=False, use_a=True, use_t=True, num_classes=4)
        self.classifier.load_state_dict(checkpoint['model'])
        self.classifier.to(self.device)
        self.classifier.eval()
        
        # Emotion mapping
        self.emotion_map = {
            0: 'neutral',
            1: 'happy',
            2: 'angry',
            3: 'sad'
        }
        
        logger.info("✅ EmotionRecognitionService initialized successfully")
    
    def extract_audio_features(self, audio_path: str) -> np.ndarray:
        """
        Extract 768-dimensional audio features using WavLM.
        
        Args:
            audio_path: Path to audio file (WAV, MP3, M4A, etc.)
        
        Returns:
            L2-normalized audio embedding [768]
        """
        try:
            # Load audio at 16kHz (WavLM's expected sample rate)
            waveform, sr = librosa.load(audio_path, sr=16000, mono=True)
            
            # Process with WavLM
            inputs = self.audio_processor(
                waveform,
                sampling_rate=16000,
                return_tensors='pt'
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.audio_model(**inputs)
                # Mean pooling over time dimension
                audio_emb = outputs.last_hidden_state.mean(dim=1).squeeze()  # [768]
            
            # L2 normalize (CRITICAL - matches training procedure)
            audio_emb = F.normalize(audio_emb, p=2, dim=0)
            
            return audio_emb.cpu().numpy()
        
        except Exception as e:
            logger.error(f"Error extracting audio features: {e}")
            raise
    
    def extract_text_features(self, text: str) -> np.ndarray:
        """
        Extract 768-dimensional text features using RoBERTa.
        
        Args:
            text: Input text string
        
        Returns:
            L2-normalized text embedding [768]
        """
        try:
            # Tokenize
            inputs = self.text_tokenizer(
                text,
                return_tensors='pt',
                max_length=128,
                truncation=True,
                padding='max_length'
            )
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
            
            with torch.no_grad():
                outputs = self.text_model(**inputs)
                # Mean pooling over sequence dimension
                text_emb = outputs.last_hidden_state.mean(dim=1).squeeze()  # [768]
            
            # L2 normalize (CRITICAL - matches training procedure)
            text_emb = F.normalize(text_emb, p=2, dim=0)
            
            return text_emb.cpu().numpy()
        
        except Exception as e:
            logger.error(f"Error extracting text features: {e}")
            raise
    
    def predict_emotion(
        self,
        audio_path: Optional[str] = None,
        text: Optional[str] = None
    ) -> Dict[str, any]:
        """
        Predict emotion from audio and/or text input.
        
        At least one input (audio or text) must be provided.
        
        Args:
            audio_path: Path to audio file (optional)
            text: Text string (optional)
        
        Returns:
            Dictionary containing:
                - emotion: Predicted emotion label (str)
                - confidence: Confidence score (float)
                - probabilities: Dict of all emotion probabilities
        
        Raises:
            ValueError: If neither audio nor text is provided
        """
        if audio_path is None and text is None:
            raise ValueError("At least one of audio_path or text must be provided")
        
        try:
            # Extract features
            if audio_path:
                audio_features = self.extract_audio_features(audio_path)
            else:
                # Zero padding if audio not provided
                audio_features = np.zeros(768, dtype=np.float32)
            
            if text:
                text_features = self.extract_text_features(text)
            else:
                # Zero padding if text not provided
                text_features = np.zeros(768, dtype=np.float32)
            
            # Concatenate features [1536-dim]
            fused_features = np.concatenate([audio_features, text_features])
            fused_tensor = torch.from_numpy(fused_features).float().unsqueeze(0).to(self.device)
            
            # Inference
            with torch.no_grad():
                logits = self.classifier(fused_tensor)
                probabilities = torch.softmax(logits, dim=1).squeeze()
                predicted_class = torch.argmax(logits, dim=1).item()
            
            # Format output
            emotion = self.emotion_map[predicted_class]
            confidence = probabilities[predicted_class].item()
            
            result = {
                'emotion': emotion,
                'confidence': float(confidence),
                'probabilities': {
                    self.emotion_map[i]: float(probabilities[i])
                    for i in range(4)
                }
            }
            
            logger.info(f"Predicted emotion: {emotion} (confidence: {confidence:.2%})")
            return result
        
        except Exception as e:
            logger.error(f"Error during emotion prediction: {e}")
            raise
    
    def predict_batch(
        self,
        audio_paths: list = None,
        texts: list = None
    ) -> list:
        """
        Batch prediction for multiple samples.
        
        Args:
            audio_paths: List of audio file paths
            texts: List of text strings
        
        Returns:
            List of prediction dictionaries
        """
        if audio_paths is None:
            audio_paths = [None] * len(texts)
        if texts is None:
            texts = [None] * len(audio_paths)
        
        results = []
        for audio_path, text in zip(audio_paths, texts):
            result = self.predict_emotion(audio_path=audio_path, text=text)
            results.append(result)
        
        return results


# Singleton instance for global access
_emotion_service_instance = None

def get_emotion_service(checkpoint_path: str = 'checkpoints/at.pth', device: str = 'cuda'):
    """
    Get or create the global emotion service instance (singleton pattern).
    
    Args:
        checkpoint_path: Path to model checkpoint
        device: Device to run on
    
    Returns:
        EmotionRecognitionService instance
    """
    global _emotion_service_instance
    
    if _emotion_service_instance is None:
        _emotion_service_instance = EmotionRecognitionService(
            checkpoint_path=checkpoint_path,
            device=device
        )
    
    return _emotion_service_instance
