import numpy as np
import torch
from transformers import WavLMModel, Wav2Vec2FeatureExtractor

# ---------------- CONFIG ----------------
TARGET_SR = 16000
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

# ---------------- LOAD ONCE ----------------
feature_extractor = Wav2Vec2FeatureExtractor.from_pretrained(
    "microsoft/wavlm-base"
)

wavlm = WavLMModel.from_pretrained(
    "microsoft/wavlm-base"
).to(DEVICE)

wavlm.eval()

# ---------------- FUNCTION ----------------
@torch.no_grad()
def encode_audio(audio: np.ndarray) -> list:
    """
    Input:
        audio: np.ndarray (N,) mono audio @ 16kHz
    Output:
        List[float] – WavLM embedding (768,)
    """

    # Ensure float32
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    # Feature extraction (NO processor)
    inputs = feature_extractor(
        audio,
        sampling_rate=TARGET_SR,
        return_tensors="pt",
        padding=True
    )

    input_values = inputs["input_values"].to(DEVICE)

    # Forward pass
    outputs = wavlm(input_values)

    # Mean pooling over time
    embedding = outputs.last_hidden_state.mean(dim=1)

    return embedding.squeeze(0).cpu().tolist()
