from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import shutil, os
from utils.video_utils import extract_frames
from feature_extractors.visual_encoder import encode_visual
from utils.audio_utils import extract_audio
from feature_extractors.audio_encoder import encode_audio
from feature_extractors.speech_text_pipeline import speech_to_text_and_features
from feature_extractors.fusion import (
    simple_concatenation_fusion,
    normalized_concatenation_fusion,
    weighted_concatenation_fusion
)

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
async def extract_multimodal_features(
    video: UploadFile = File(...),
    fusion_type: str = "simple"  # Options: "simple", "normalized", "weighted"
):
    """
    Extract and fuse multimodal features from video
    
    Args:
        video: Uploaded video file
        fusion_type: Type of fusion ("simple", "normalized", "weighted")
    """
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
        
        # ================= FUSION =================
        if fusion_type == "simple":
            fusion_result = simple_concatenation_fusion(
                visual_features,
                audio_features,
                text_features
            )
        elif fusion_type == "normalized":
            fusion_result = normalized_concatenation_fusion(
                visual_features,
                audio_features,
                text_features
            )
        elif fusion_type == "weighted":
            # You can adjust these weights based on your use case
            weights = {"visual": 0.5, "audio": 0.3, "text": 0.2}
            fusion_result = weighted_concatenation_fusion(
                visual_features,
                audio_features,
                text_features,
                weights=weights
            )
        else:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid fusion_type: {fusion_type}. Use 'simple', 'normalized', or 'weighted'"
            )
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Multimodal extraction failed: {str(e)}"
        )
    finally:
        # Cleanup
        if os.path.exists(video_path):
            os.remove(video_path)
        if wav_path and os.path.exists(wav_path):
            os.remove(wav_path)
    
    return {
        "modality": "multimodal",
        "transcript": transcript,
        "fusion_type": fusion_type,
        "fused_features": fusion_result["fused_features"],
        "feature_dimension": fusion_result["dimension"],
        "component_dimensions": fusion_result["component_dims"],
        "individual_features": {
            "visual": visual_features,
            "audio": audio_features,
            "text": text_features
        },
        "metadata": fusion_result
    }


@app.get("/")
async def root():
    return {
        "message": "MECC Feature Extraction API",
        "endpoints": {
            "/extract/multimodal-features": "Extract and fuse video features",
        },
        "fusion_options": ["simple", "normalized", "weighted"]
    }