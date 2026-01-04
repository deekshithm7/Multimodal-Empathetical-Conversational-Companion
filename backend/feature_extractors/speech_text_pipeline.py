import whisper
import torch
from transformers import AutoTokenizer, AutoModel

# ---------- Load models ONCE ----------
_whisper = whisper.load_model("base")

TOKENIZER = AutoTokenizer.from_pretrained("roberta-base")
TEXT_MODEL = AutoModel.from_pretrained("roberta-base")
TEXT_MODEL.eval()

# ---------- Pipeline ----------
def speech_to_text_and_features(wav_path):
    # 1️⃣ Speech → Text
    result = _whisper.transcribe(wav_path, fp16=False)
    text = result["text"]

    # 2️⃣ Text → Embeddings
    inputs = TOKENIZER(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    )

    with torch.no_grad():
        outputs = TEXT_MODEL(**inputs)

    embedding = outputs.last_hidden_state[:, 0, :]  # CLS token

    return {
        "transcript": text,
        "text_features": embedding.squeeze().numpy().tolist()
    }
