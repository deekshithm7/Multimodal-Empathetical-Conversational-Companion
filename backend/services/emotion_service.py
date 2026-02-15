"""
MECC Emotion Recognition Service
Handles audio+text emotion detection using the trained IEMOCAP A+T model.
"""

import torch
import torch.nn.functional as F
import numpy as np
from typing import Dict
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
        
        Note: This service now uses centralized feature extraction from feature_service.
        It only loads the emotion classifier, not the encoders.
        
        Args:
            checkpoint_path: Path to the trained model checkpoint (at.pth)
            device: Device to run inference on ('cuda' or 'cpu')
        """
        self.device = torch.device(device if torch.cuda.is_available() else 'cpu')
        logger.info(f"Initializing EmotionRecognitionService on {self.device}")
        
        # Load trained emotion classifier ONLY
        # (Feature extraction handled by feature_service)
        logger.info(f"Loading emotion classifier from {checkpoint_path}...")
        from models.emotion_classifier import FusionMLP
        
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
    
    def predict_from_features(
        self,
        audio_features: np.ndarray,
        text_features: np.ndarray
    ) -> Dict[str, any]:
        """
        Predict emotion from pre-extracted features.
        
        This is the NEW METHOD for the refactored architecture.
        Use this when features are already extracted by feature_service.
        
        Args:
            audio_features: [768] audio embedding from WavLM
            text_features: [768] text embedding from RoBERTa
        
        Returns:
            Dictionary with emotion and confidence
        """
        try:
            # Ensure numpy arrays
            audio_features = np.array(audio_features, dtype=np.float32)
            text_features = np.array(text_features, dtype=np.float32)
            
            # L2 normalize (match training)
            audio_features = audio_features / (np.linalg.norm(audio_features) + 1e-8)
            text_features = text_features / (np.linalg.norm(text_features) + 1e-8)
            
            # Concatenate [audio(768) + text(768)] = 1536
            combined = np.concatenate([audio_features, text_features])
            
            # Convert to tensor
            input_tensor = torch.from_numpy(combined).float().unsqueeze(0)  # [1, 1536]
            input_tensor = input_tensor.to(self.device)
            
            # Predict
            with torch.no_grad():
                logits = self.classifier(input_tensor)  # [1, 4]
                probs = F.softmax(logits, dim=1)
                confidence, pred_class = torch.max(probs, dim=1)
            
            emotion_label = self.emotion_map[pred_class.item()]
            confidence_score = confidence.item()
            
            logger.info(f"Predicted emotion: {emotion_label} (confidence: {confidence_score:.2%})")
            
            return {
                'emotion': emotion_label,
                'confidence': confidence_score
            }
        
        except Exception as e:
            logger.error(f"Error predicting from features: {e}")
            raise
    

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
