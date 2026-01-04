from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil, os

from utils.video_utils import extract_frames
from feature_extractors.visual_encoder import encode_visual

from utils.audio_utils import extract_audio
from feature_extractors.audio_encoder import encode_audio

from feature_extractors.speech_text_pipeline import speech_to_text_and_features
app = FastAPI(title="MECC Feature Extraction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_DIR = "uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/extract/multimodal-features")
async def extract_multimodal_features(video: UploadFile = File(...)):
    video_path = os.path.join(UPLOAD_DIR, video.filename)
    wav_path = None

    try:
        # 1️⃣ Save uploaded video
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        # ================= VISUAL =================
        frames = extract_frames(video_path)
        visual_features = encode_visual(frames)

        # ================= AUDIO ==================
        audio_features_raw, wav_path = extract_audio(
            video_path,
            return_wav=True
        )
        audio_features = encode_audio(audio_features_raw)

        # ============== SPEECH + TEXT =============
        speech_text = speech_to_text_and_features(wav_path)
        text_features = speech_text["text_features"]
        transcript = speech_text["transcript"]

       

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal extraction failed: {str(e)}"
        )

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)

    return {
        "modality": "multimodal",
        "transcript": transcript,
        "dimensions": {
            "visual": len(visual_features),
            "audio": len(audio_features),
            "text": len(text_features)
        },
        
        "note": "Early fusion of visual + audio + text features"
    }