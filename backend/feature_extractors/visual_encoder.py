"""
Visual Encoder - ResNet50 Feature Extraction (Singleton Pattern)

Extracts visual features from video frames using ResNet50.
Model is loaded once and reused across all requests.
"""

import torch
import numpy as np
from torchvision import models, transforms
from torchvision.models import ResNet50_Weights
import logging

logger = logging.getLogger(__name__)

# Configuration
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"


class VisualEncoder:
    """
    Singleton visual encoder using ResNet50.
    
    Loads ResNet50 model once and reuses it for all encoding requests.
    """
    
    def __init__(self):
        """Initialize and load ResNet50 model."""
        logger.info(f"Loading ResNet50 model on {DEVICE}...")
        
        self.device = DEVICE
        
        # Load ResNet50
        self.model = models.resnet50(weights=ResNet50_Weights.DEFAULT)
        self.model.fc = torch.nn.Identity()  # Remove classification layer
        self.model = self.model.to(self.device)
        self.model.eval()
        
        # Image preprocessing
        self.transform = transforms.Compose([
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225]
            )
        ])
        
        logger.info("✅ ResNet50 model loaded successfully")
    
    @torch.no_grad()
    def encode(self, frames: list) -> np.ndarray:
        """
        Encode video frames to features using ResNet50.
        
        Args:
            frames: List of frames (H, W, C) in numpy format
        
        Returns:
            np.ndarray: ResNet50 features (2048,) averaged across frames
        """
        if not frames:
            logger.warning("No frames provided, returning zero features")
            return np.zeros(2048, dtype=np.float32)
        
        embeddings = []
        
        for frame in frames:
            # Transform and add batch dimension
            x = self.transform(frame).unsqueeze(0).to(self.device)
            
            # Extract features
            emb = self.model(x)
            embeddings.append(emb)
        
        # Average across frames
        features = torch.mean(torch.stack(embeddings), dim=0)
        
        # Return as numpy array
        return features.squeeze().cpu().numpy()


# Singleton instance
_visual_encoder_instance = None


def get_visual_encoder() -> VisualEncoder:
    """
    Get or create the global visual encoder instance (singleton).
    
    Returns:
        VisualEncoder instance
    """
    global _visual_encoder_instance
    
    if _visual_encoder_instance is None:
        _visual_encoder_instance = VisualEncoder()
        logger.info("Created VisualEncoder singleton")
    
    return _visual_encoder_instance


# Legacy function for backward compatibility
def encode_visual(frames: list) -> list:
    """
    Legacy function - redirects to singleton instance.
    
    Args:
        frames: List of frames (H, W, C)
    
    Returns:
        list: ResNet50 features (2048,) as list
    """
    encoder = get_visual_encoder()
    features = encoder.encode(frames)
    return features.tolist()
