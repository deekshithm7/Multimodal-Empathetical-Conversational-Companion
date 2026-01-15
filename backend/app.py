from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil, os

from utils.video_utils import extract_frames
from utils.audio_utils import extract_audio
from feature_extractors.visual_encoder import encode_visual
from feature_extractors.audio_encoder import encode_audio
from feature_extractors.speech_text_pipeline import speech_to_text_and_features
from feature_extractors.fusion import *

app = FastAPI(title="MECC Feature Extraction API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"]
)

UPLOAD_DIR = "uploads/videos"
os.makedirs(UPLOAD_DIR, exist_ok=True)

@app.post("/extract/multimodal-features")
async def extract_multimodal_features(
    video: UploadFile = File(...),
    fusion_type: str = "simple"
):
    video_path = os.path.join(UPLOAD_DIR, video.filename)
    wav_path = None

    try:
        with open(video_path, "wb") as buffer:
            shutil.copyfileobj(video.file, buffer)

        frames = extract_frames(video_path)
        visual_features = encode_visual(frames)

        audio_raw, wav_path = extract_audio(video_path, return_wav=True)
        audio_features = encode_audio(audio_raw)

        speech_text = speech_to_text_and_features(wav_path)

        if fusion_type == "simple":
            fusion = simple_concatenation_fusion(
                visual_features, audio_features, speech_text["text_features"]
            )
        elif fusion_type == "normalized":
            fusion = normalized_concatenation_fusion(
                visual_features, audio_features, speech_text["text_features"]
            )
        elif fusion_type == "weighted":
            fusion = weighted_concatenation_fusion(
                visual_features, audio_features, speech_text["text_features"],
                weights={"visual": 0.5, "audio": 0.3, "text": 0.2}
            )
        else:
            raise HTTPException(status_code=400, detail="Invalid fusion type")

        return {
            "modality": "multimodal",
            "transcript": speech_text["transcript"],
            "fusion_type": fusion_type,
            "fused_features": fusion["fused_features"],
            "feature_dimension": fusion["dimension"],
            "component_dimensions": fusion["component_dims"]
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if os.path.exists(video_path):
            os.remove(video_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)

@app.get("/")
def root():
    return {"message": "MECC Feature Extraction API"}
