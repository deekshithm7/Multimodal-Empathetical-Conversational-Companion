"""
MECC Backend API — with Personality Prediction Integration
Changes vs previous version:
  1. PersonalityService loaded at startup (once)
  2. stream_message dispatches a background personality task per video message
  3. end_session aggregates personality observations and runs EMA update
  4. /api/v1/personality/* router included
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import asyncio
import tempfile
import os
import json
import logging
from datetime import datetime
import uuid
import shutil

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# ── Service imports ────────────────────────────────────────────────────────────
from services.emotion_service       import get_emotion_service
from services.llm_service           import get_free_llm_service
from services.tts_service           import get_free_tts_service
from services.transcription_service import get_whisper_service
from services.feature_service       import get_feature_service
from services.personality_service   import init_personality_service, get_personality_service

from database import (
    get_db, init_db, User, Conversation,
    create_conversation, save_message, get_conversation_history,
    end_conversation as db_end_conversation, get_emotion_timeline,
    # Personality DB helpers (added in database_personality_additions.py merge)
    save_personality_observation, get_session_personality_observations,
)
from utils.auth import get_current_user

# ── Routers ────────────────────────────────────────────────────────────────────
from routers import auth, users, analytics
from routers.personality import router as personality_router

AUDIO_STORAGE_DIR = os.environ.get('AUDIO_STORAGE_DIR', './audio_storage')
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)


# ─────────────────────────────────────────────────────────────────────────────
# Lifespan
# ─────────────────────────────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    global emotion_service, llm_service, tts_service, whisper_service

    logger.info("🚀 Starting MECC Backend API v2.2...")

    try:
        init_db()

        checkpoint_path     = os.environ.get('MODEL_CHECKPOINT_PATH', 'checkpoints/at.pth')
        device              = os.environ.get('DEVICE', 'cuda')
        personality_model   = os.environ.get(
            'PERSONALITY_MODEL_PATH',
            'checkpoints/personality/best_model.pt'
        )
        personality_config  = os.environ.get(
            'PERSONALITY_CONFIG_PATH',
            'checkpoints/personality/config.json'
        )

        emotion_service = get_emotion_service(checkpoint_path=checkpoint_path, device=device)
        llm_service     = get_free_llm_service(model_name="llama3.2:3b")
        tts_service     = get_free_tts_service(provider="piper", voice="voices/en_US-lessac-medium.onnx")

        use_whisper_api     = os.environ.get('USE_WHISPER_API', 'false').lower() == 'true'
        whisper_model_size  = os.environ.get('WHISPER_MODEL_SIZE', 'base')
        whisper_service     = get_whisper_service(
            use_api=use_whisper_api,
            model_size=whisper_model_size,
            device=device
        )

        # Pre-load shared feature encoders (audio + text — visual loaded on first video)
        feature_service = get_feature_service()
        _ = feature_service.audio_encoder
        _ = feature_service.text_encoder
        logger.info("✅ Feature service encoders pre-loaded")

        # Load personality model (heavy — do it once here)
        if os.path.exists(personality_model) and os.path.exists(personality_config):
            init_personality_service(
                model_path  = personality_model,
                config_path = personality_config,
            )
            logger.info("✅ PersonalityService initialised")
        else:
            logger.warning(
                f"⚠️  Personality model files not found — service disabled.\n"
                f"   model:  {personality_model}\n"
                f"   config: {personality_config}"
            )

        logger.info("✅ All services initialised")

    except Exception as e:
        logger.error(f"❌ Failed to initialise services: {e}")
        raise

    yield

    logger.info("🛑 MECC Backend shutting down")


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="MECC API",
    description="Multimodal Empathetical Conversational Companion",
    version="2.2.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(analytics.router)
app.include_router(personality_router)          # ← NEW

# Global service references (set during lifespan)
emotion_service = None
llm_service     = None
tts_service     = None
whisper_service = None


# ─────────────────────────────────────────────────────────────────────────────
# Background personality task
# ─────────────────────────────────────────────────────────────────────────────

def _run_personality_prediction_bg(
    audio_feat:      "Optional[np.ndarray]",
    text_feat:       "Optional[np.ndarray]",
    visual_feat:     "Optional[np.ndarray]",
    user_id:         str,
    conversation_id: str,
    message_id:      str,
    db_session_factory,
):
    """
    Background task: run personality inference and persist the observation.
    Never raises — all failures are logged and swallowed.
    """
    try:
        svc = get_personality_service()
        if svc is None:
            logger.debug("Personality service not available — skipping bg prediction")
            return
        
        scores = svc.predict_from_features(audio_feat, text_feat, visual_feat)
        logger.info(f"🧠 Personality scores for msg {message_id}: {scores}")

        # Persist to DB
        db = db_session_factory()
        try:
            save_personality_observation(
                db              = db,
                user_id         = user_id,
                conversation_id = conversation_id,
                ocean_scores    = scores,
                message_id      = message_id,
            )
        finally:
            db.close()

    except Exception as e:
        logger.error(f"Personality bg task failed: {e}", exc_info=True)


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

def save_audio_file(audio: UploadFile, conversation_id: str) -> Dict:
    file_id  = str(uuid.uuid4())
    file_ext = os.path.splitext(audio.filename)[1] or '.wav'
    filename = f"{conversation_id}_{file_id}{file_ext}"
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)

    with open(file_path, 'wb') as f:
        content = audio.file.read()
        f.write(content)

    duration = 0.0
    if not file_path.endswith('.webm'):
        try:
            import soundfile as sf
            info = sf.info(file_path)
            duration = info.duration
        except Exception as e:
            logger.debug(f"Could not get audio duration: {e}")

    return {'path': file_path, 'duration': duration, 'size': len(content), 'filename': filename}


def cleanup_temp_files(*files):
    for fp in files:
        if fp and os.path.exists(fp):
            try: os.unlink(fp)
            except: pass


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class StartConversationResponse(BaseModel):
    conversation_id: str
    session_id: str
    welcome_message: str
    welcome_audio_url: str


class EndConversationResponse(BaseModel):
    summary: str
    summary_audio_url: str
    emotional_journey: List[Dict]
    total_messages: int
    duration_minutes: float
    personality_updated: bool          # ← NEW: did we update the profile?


# ─────────────────────────────────────────────────────────────────────────────
# Endpoints
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    svc = get_personality_service()
    return {
        "status": "healthy",
        "version": "2.2.0",
        "services": {
            "emotion_model":      "loaded" if emotion_service  else "not loaded",
            "llm":                "loaded" if llm_service      else "not loaded",
            "tts":                "loaded" if tts_service      else "not loaded",
            "whisper":            "loaded" if whisper_service  else "not loaded",
            "personality_model":  "loaded" if svc             else "not loaded",
        }
    }


@app.post("/api/v1/session/start", response_model=StartConversationResponse)
async def start_session(
    current_user: User   = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    try:
        conversation  = create_conversation(db, user_id=current_user.id)
        welcome_text  = "Hello! I'm here to listen and support you. How are you feeling today?"
        audio_path    = tts_service.generate_speech(welcome_text, emotion='neutral')

        stored_filename = f"{conversation.session_id}_welcome.mp3"
        stored_path     = os.path.join(AUDIO_STORAGE_DIR, stored_filename)
        shutil.copy(audio_path, stored_path)

        save_message(db, conversation_id=str(conversation.id),
                     role='assistant', content=welcome_text,
                     audio_data={'path': stored_path, 'duration': 3.0})

        cleanup_temp_files(audio_path)

        return {
            "conversation_id":  str(conversation.id),
            "session_id":       conversation.session_id,
            "welcome_message":  welcome_text,
            "welcome_audio_url": f"/api/v1/audio/{stored_filename}",
        }
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/session/message")
async def send_message(
    conversation_id:  str                    = Form(...),
    audio:            Optional[UploadFile]   = File(None),
    text:             Optional[str]          = Form(None),
    background_tasks: BackgroundTasks        = None,
    current_user:     User                   = Depends(get_current_user),
    db:               Session                = Depends(get_db),
):
    """
    Process a user message.

    If audio/video is provided, personality prediction runs in the background
    WITHOUT blocking the response — the user never waits for it.
    """
    convo = db.query(Conversation).filter(
        Conversation.id      == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id,
    ).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")

    if not audio and not text:
        raise HTTPException(status_code=400, detail="Must provide audio or text")

    start_time     = datetime.now()
    audio_temp_path = None

    try:
        if audio:
            user_audio_data  = save_audio_file(audio, conversation_id)
            audio_temp_path  = user_audio_data['path']

        from services.conversation_service import get_conversation_service
        conversation_service = get_conversation_service()

        result = conversation_service.process_message(
            conversation_id = conversation_id,
            audio_path      = audio_temp_path,
            text            = text,
            db_session      = db,
        )

        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])

        # ── Background personality task (non-blocking) ─────────────────────
        if audio_temp_path and get_personality_service() is not None:
            # Extract features needed for personality (we reuse feature_service)
            feature_service = get_feature_service()
            feats = feature_service.extract_parallel(
                audio_path = audio_temp_path,
                text       = result.get('user_message', ''),
                video_path = audio_temp_path,   # same file — audio+visual from it
            )

            message_id = result.get('message_id')  # ensure conversation_service returns this

            from database import SessionLocal
            background_tasks.add_task(
                _run_personality_prediction_bg,
                audio_feat      = feats.get('audio'),
                text_feat       = feats.get('text'),
                visual_feat     = feats.get('visual'),
                user_id         = str(current_user.id),
                conversation_id = conversation_id,
                message_id      = str(message_id) if message_id else None,
                db_session_factory = SessionLocal,
            )
            logger.info("🔄 Personality prediction dispatched to background")

        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)

        return {
            "status":               "success",
            "user_message":         result['user_message'],
            "user_emotion":         result['user_emotion'],
            "assistant_response":   result['assistant_response'],
            "assistant_audio_url":  result['assistant_audio_url'],
            "conversation_id":      conversation_id,
            "processing_time_ms":   processing_time,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    finally:
        # Do NOT delete audio_temp_path here — bg task may still need it.
        # The bg task is responsible for cleanup, or use a scheduled cleanup job.
        pass


@app.post("/api/v1/session/end", response_model=EndConversationResponse)
async def end_session(
    conversation_id: str   = Form(...),
    current_user:    User  = Depends(get_current_user),
    db:              Session = Depends(get_db),
):
    """
    End a conversation session.

    After building the summary, aggregates all personality observations for
    this session and runs an EMA update on the user's personality profile.
    """
    convo = db.query(Conversation).filter(
        Conversation.id      == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id,
    ).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    if convo.status == 'completed':
        raise HTTPException(status_code=404, detail="Conversation already ended")
    try:
        history  = get_conversation_history(db, conversation_id, limit=100)
        timeline = get_emotion_timeline(db, conversation_id)

        conversation_context = [
            {'role': m['role'], 'content': m['content']} for m in history
        ]

        summary_text = llm_service.generate_session_summary(
            conversation_history = conversation_context,
            emotion_timeline     = timeline,
        )

        summary_audio_path   = tts_service.generate_speech(summary_text, emotion='neutral')
        summary_filename     = f"{conversation_id}_summary.mp3"
        summary_stored_path  = os.path.join(AUDIO_STORAGE_DIR, summary_filename)
        shutil.copy(summary_audio_path, summary_stored_path)

        db_end_conversation(db, conversation_id)

        duration_minutes = 0.0
        if convo.ended_at and convo.started_at:
            duration_minutes = (convo.ended_at - convo.started_at).total_seconds() / 60

        cleanup_temp_files(summary_audio_path)

        # ── Personality EMA update ─────────────────────────────────────────
        personality_updated = False
        svc = get_personality_service()
        if svc is not None:
            try:
                video_scores = get_session_personality_observations(db, conversation_id)
                if video_scores:
                    svc.add_session_result(
                        user_id      = str(current_user.id),
                        session_id   = str(conversation_id),
                        video_scores = video_scores,
                        db           = db,
                    )
                    personality_updated = True
                    logger.info(f"✅ Personality profile updated for user {current_user.id}")
                else:
                    logger.info("No personality observations this session — skipping EMA update")
            except Exception as e:
                logger.error(f"Personality EMA update failed: {e}", exc_info=True)
                # Non-fatal — session end still succeeds

        return {
            "summary":              summary_text,
            "summary_audio_url":    f"/api/v1/audio/{summary_filename}",
            "emotional_journey":    timeline,
            "total_messages":       len(history),
            "duration_minutes":     round(duration_minutes, 2),
            "personality_updated":  personality_updated,
        }

    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/audio/{filename}")
async def get_audio(filename: str):
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)


@app.get("/api/v1/conversation/{conversation_id}/history")
async def get_history(
    conversation_id: str,
    current_user:    User    = Depends(get_current_user),
    db:              Session = Depends(get_db),
):
    convo = db.query(Conversation).filter(
        Conversation.id      == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id,
    ).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        return {"conversation_id": conversation_id,
                "messages": get_conversation_history(db, conversation_id, limit=50)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/conversation/{conversation_id}/emotions")
async def get_emotions(
    conversation_id: str,
    current_user:    User    = Depends(get_current_user),
    db:              Session = Depends(get_db),
):
    convo = db.query(Conversation).filter(
        Conversation.id      == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id,
    ).first()
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")
    try:
        return {"conversation_id": conversation_id,
                "emotion_timeline": get_emotion_timeline(db, conversation_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message":  "MECC API v2.2",
        "status":   "running",
        "docs":     "/docs",
        "endpoints": {
            "auth":        "/api/v1/auth",
            "users":       "/api/v1/users",
            "analytics":   "/api/v1/analytics",
            "session":     "/api/v1/session",
            "personality": "/api/v1/personality",
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app:app",
        host      = os.environ.get("HOST", "0.0.0.0"),
        port      = int(os.environ.get("PORT", 8000)),
        reload    = os.environ.get("RELOAD", "true").lower() == "true",
        log_level = "info",
    )