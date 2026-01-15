import whisper
import torch
from transformers import AutoTokenizer, AutoModel

# ---------- Device ----------
DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
print("Using device:", DEVICE)

# ---------- Load models ONCE ----------
WHISPER_MODEL = whisper.load_model("small", device=DEVICE)

TOKENIZER = AutoTokenizer.from_pretrained("roberta-base")
TEXT_MODEL = AutoModel.from_pretrained("roberta-base").to(DEVICE)
TEXT_MODEL.eval()

# ---------- Pipeline ----------
def speech_to_text_and_features(wav_path):
    """
    English-only Speech → Text → Embeddings
    FULL transcript guaranteed
    """

    # ---------- 1️⃣ Language Detection ----------
    audio = whisper.load_audio(wav_path)
    audio = whisper.pad_or_trim(audio)

    mel = whisper.log_mel_spectrogram(audio).to(DEVICE)
    _, probs = WHISPER_MODEL.detect_language(mel)
    detected_lang = max(probs, key=probs.get)

    if detected_lang != "en":
        raise ValueError(
            f"❌ Non-English audio detected ({detected_lang}). "
            "Only English audio is supported."
        )

    # ---------- 2️⃣ Speech → Text (FIXED) ----------
    result = WHISPER_MODEL.transcribe(
        wav_path,
        language="en",
        task="transcribe",
        fp16=(DEVICE == "cuda"),
        condition_on_previous_text=False,   # 🔥 IMPORTANT
        temperature=0.0,
        no_speech_threshold=0.6,             # 🔥 prevents early cut
        compression_ratio_threshold=2.4,
        verbose=False
    )

    # 🔥 COLLECT ALL SEGMENTS (FULL TEXT)
    segments = result.get("segments", [])
    text = " ".join(seg["text"].strip() for seg in segments).strip()

    if not text:
        return {
            "transcript": "",
            "text_features": [0.0] * 768
        }

    # ---------- 3️⃣ Text → Embeddings ----------
    inputs = TOKENIZER(
        transcript,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=128
    ).to(DEVICE)

    with torch.no_grad():
        outputs = TEXT_MODEL(**inputs)

    text_embedding = outputs.last_hidden_state.mean(dim=1).squeeze()

    return {
        "transcript": text,
        "text_features": embedding.squeeze(0).cpu().numpy().tolist()
    }

# ---------- Example Usage ----------
# result = speech_to_text_and_features("audio.wav")
# print(result["transcript"])
# print(len(result["text_features"]))
