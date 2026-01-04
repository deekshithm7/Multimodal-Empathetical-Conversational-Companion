import librosa
import numpy as np

TARGET_SR = 16000
N_MFCC = 13

def encode_audio(audio: np.ndarray) -> list:
    """
    Input: audio (240000,)
    Output: MFCC + Δ + Δ² mean pooled (39,)
    """
    mfcc = librosa.feature.mfcc(
        y=audio,
        sr=TARGET_SR,
        n_mfcc=N_MFCC
    )

    delta = librosa.feature.delta(mfcc)
    delta2 = librosa.feature.delta(mfcc, order=2)

    features = np.vstack([mfcc, delta, delta2])  # (39, T)

    return np.mean(features, axis=1).astype(np.float32).tolist()
