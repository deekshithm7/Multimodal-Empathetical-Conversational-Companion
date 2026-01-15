import whisper
import torch
from transformers import AutoTokenizer, AutoModel

DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

WHISPER_MODEL = whisper.load_model("base", device=DEVICE)

TOKENIZER = AutoTokenizer.from_pretrained("roberta-base")
TEXT_MODEL = AutoModel.from_pretrained("roberta-base").to(DEVICE)
TEXT_MODEL.eval()

def speech_to_text_and_features(wav_path: str):
    result = WHISPER_MODEL.transcribe(
        wav_path,
        language="en",
        fp16=torch.cuda.is_available(),
        temperature=0.0,
        best_of=5,
        beam_size=5,
        condition_on_previous_text=False,
        no_speech_threshold=0.1,
        logprob_threshold=-1.0,
        verbose=False
    )

    transcript = result["text"].strip()
    if not transcript:
        raise ValueError("Empty transcription")

    inputs = TOKENIZER(
        transcript,
        return_tensors="pt",
        truncation=True,
        padding=True,
        max_length=512
    ).to(DEVICE)

    with torch.no_grad():
        outputs = TEXT_MODEL(**inputs)

    text_embedding = outputs.last_hidden_state.mean(dim=1).squeeze()

    return {
        "transcript": transcript,
        "text_features": text_embedding.cpu().numpy().tolist()
    }
