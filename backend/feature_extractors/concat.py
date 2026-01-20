import numpy as np
from typing import List, Dict

def concatenation_fusion(
    visual_features: List[float],
    audio_features: List[float],
    text_features: List[float]
) -> Dict:
    # convert to consistent float32 numpy
    V = np.array(visual_features, dtype=np.float32)
    A = np.array(audio_features, dtype=np.float32)
    T = np.array(text_features, dtype=np.float32)

    # sanity checks (optional but useful)
    assert V.ndim == 1 and A.ndim == 1 and T.ndim == 1
    assert V.shape[0] == 2048
    assert A.shape[0] == 768
    assert T.shape[0] == 768

    # concat
    fused = np.concatenate([V, A, T])

    return {
        "fused_features": fused,          # leave as numpy for MLP
        "dimension": fused.shape[0],      # should be 3584
        "component_dims": {
            "visual": V.shape[0],
            "audio": A.shape[0],
            "text": T.shape[0]
        }
    }
