import numpy as np
from typing import List, Dict

def simple_concatenation_fusion(
    visual_features: List[float],
    audio_features: List[float],
    text_features: List[float]
) -> Dict:
    """
    Simple early fusion: concatenate all modality features
    
    Args:
        visual_features: ResNet50 features (2048,)
        audio_features: MFCC features (39,)
        text_features: RoBERTa features (768,)
    
    Returns:
        Dictionary with fused features and metadata
    """
    # Convert to numpy arrays
    visual = np.array(visual_features, dtype=np.float32)
    audio = np.array(audio_features, dtype=np.float32)
    text = np.array(text_features, dtype=np.float32)
    
    # Concatenate all features
    fused = np.concatenate([visual, audio, text])  # (2855,)
    
    return {
        "fused_features": fused.tolist(),
        "dimension": len(fused),
        "component_dims": {
            "visual": len(visual),
            "audio": len(audio),
            "text": len(text)
        }
    }


def weighted_concatenation_fusion(
    visual_features: List[float],
    audio_features: List[float],
    text_features: List[float],
    weights: Dict[str, float] = None
) -> Dict:
    """
    Weighted fusion: apply weights before concatenation
    
    Args:
        visual_features: ResNet50 features (2048,)
        audio_features: MFCC features (39,)
        text_features: RoBERTa features (768,)
        weights: Dictionary with 'visual', 'audio', 'text' keys
    
    Returns:
        Dictionary with fused features and metadata
    """
    if weights is None:
        weights = {"visual": 1.0, "audio": 1.0, "text": 1.0}
    
    # Convert to numpy arrays and apply weights
    visual = np.array(visual_features, dtype=np.float32) * weights["visual"]
    audio = np.array(audio_features, dtype=np.float32) * weights["audio"]
    text = np.array(text_features, dtype=np.float32) * weights["text"]
    
    # Concatenate weighted features
    fused = np.concatenate([visual, audio, text])
    
    return {
        "fused_features": fused.tolist(),
        "dimension": len(fused),
        "weights_applied": weights,
        "component_dims": {
            "visual": len(visual),
            "audio": len(audio),
            "text": len(text)
        }
    }


def normalized_concatenation_fusion(
    visual_features: List[float],
    audio_features: List[float],
    text_features: List[float]
) -> Dict:
    """
    Normalized fusion: L2-normalize each modality before concatenation
    This helps balance features with different scales
    
    Args:
        visual_features: ResNet50 features (2048,)
        audio_features: MFCC features (39,)
        text_features: RoBERTa features (768,)
    
    Returns:
        Dictionary with fused features and metadata
    """
    # Convert to numpy arrays
    visual = np.array(visual_features, dtype=np.float32)
    audio = np.array(audio_features, dtype=np.float32)
    text = np.array(text_features, dtype=np.float32)
    
    # L2 normalize each modality
    visual_norm = visual / (np.linalg.norm(visual) + 1e-8)
    audio_norm = audio / (np.linalg.norm(audio) + 1e-8)
    text_norm = text / (np.linalg.norm(text) + 1e-8)
    
    # Concatenate normalized features
    fused = np.concatenate([visual_norm, audio_norm, text_norm])
    
    return {
        "fused_features": fused.tolist(),
        "dimension": len(fused),
        "normalization": "L2",
        "component_dims": {
            "visual": len(visual),
            "audio": len(audio),
            "text": len(text)
        }
    }