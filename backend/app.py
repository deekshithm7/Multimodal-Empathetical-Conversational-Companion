"""
MECC Backend API - Complete Version
Includes: Emotion Detection, LLM, TTS, Transcription, Database
"""

from fastapi import FastAPI, File, UploadFile, Form, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
import tempfile
import os
import json
import logging
from datetime import datetime
import uuid
import shutil

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Import services
# ... (imports)
from services.emotion_service import get_emotion_service
from services.llm_service import get_free_llm_service
from services.tts_service import get_free_tts_service
from services.transcription_service import get_whisper_service
from services.feature_service import get_feature_service
from database import (
    get_db, init_db, User, Conversation,
    create_conversation, save_message, get_conversation_history,
    end_conversation as db_end_conversation, get_emotion_timeline
)
from utils.auth import get_current_user

# Import Routers
from routers import auth, users, analytics

# Initialize FastAPI
app = FastAPI(
    title="MECC API",
    description="Multimodal Empathetical Conversational Companion",
    version="2.1.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include Routers
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(analytics.router)

# Global service instances
emotion_service = None
llm_service = None
tts_service = None
whisper_service = None

# Audio storage directory
AUDIO_STORAGE_DIR = os.environ.get('AUDIO_STORAGE_DIR', './audio_storage')
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)


# Pydantic models (retained for Start/End response)
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


# Startup
@app.on_event("startup")
async def startup_event():
    global emotion_service, llm_service, tts_service, whisper_service
    
    logger.info("🚀 Starting MECC Backend API v2.1...")
    
    try:
        # Initialize database
        init_db()
        
        # Initialize services
        checkpoint_path = os.environ.get('MODEL_CHECKPOINT_PATH', 'checkpoints/at.pth')
        device = os.environ.get('DEVICE', 'cuda')
        
        emotion_service = get_emotion_service(checkpoint_path=checkpoint_path, device=device)
        llm_service = get_free_llm_service(model_name="llama3.2:3b")
        
        tts_provider = os.environ.get('TTS_PROVIDER', 'openai')
        tts_service = get_free_tts_service(provider="piper", voice="voices/en_US-lessac-medium.onnx")
        
        use_whisper_api = os.environ.get('USE_WHISPER_API', 'false').lower() == 'true'
        whisper_model_size = os.environ.get('WHISPER_MODEL_SIZE', 'base')
        whisper_service = get_whisper_service(
            use_api=use_whisper_api,
            model_size=whisper_model_size,
            device=device
        )
        
        feature_service = get_feature_service()
        _ = feature_service.audio_encoder
        _ = feature_service.text_encoder
        logger.info("✅ Feature service encoders pre-loaded")
        
        logger.info("✅ All services initialized successfully")
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


# Helper functions
def save_audio_file(audio: UploadFile, conversation_id: str) -> Dict:
    """Save uploaded audio file and return metadata"""
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(audio.filename)[1] or '.wav'
    filename = f"{conversation_id}_{file_id}{file_ext}"
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    
    with open(file_path, 'wb') as f:
        content = audio.file.read()
        f.write(content)
    
    duration = 0.0
    try:
        import soundfile as sf
        info = sf.info(file_path)
        duration = info.duration
    except Exception as e:
        logger.warning(f"Failed to get audio duration: {e}")
    
    return {
        'path': file_path,
        'duration': duration,
        'size': len(content),
        'filename': filename
    }


def cleanup_temp_files(*files):
    for file_path in files:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass


# Endpoints

@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "version": "2.1.0",
        "services": {
            "emotion_model": "loaded" if emotion_service else "not loaded",
            "llm": "loaded" if llm_service else "not loaded",
            "tts": "loaded" if tts_service else "not loaded",
            "whisper": "loaded" if whisper_service else "not loaded"
        }
    }


@app.post("/api/v1/session/start", response_model=StartConversationResponse)
async def start_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Start a new conversation session (Authenticated)"""
    try:
        # Pass User ID (UUID)
        conversation = create_conversation(db, user_id=current_user.id)
        
        welcome_text = "Hello! I'm here to listen and support you. How are you feeling today?"
        
        audio_path = tts_service.generate_speech(welcome_text, emotion='neutral')
        
        stored_filename = f"{conversation.session_id}_welcome.mp3"
        stored_path = os.path.join(AUDIO_STORAGE_DIR, stored_filename)
        shutil.copy(audio_path, stored_path)
        
        save_message(
            db,
            conversation_id=str(conversation.id),
            role='assistant',
            content=welcome_text,
            audio_data={'path': stored_path, 'duration': 3.0}
        )
        
        cleanup_temp_files(audio_path)
        
        return {
            "conversation_id": str(conversation.id),
            "session_id": conversation.session_id,
            "welcome_message": welcome_text,
            "welcome_audio_url": f"/api/v1/audio/{stored_filename}"
        }
    
    except Exception as e:
        logger.error(f"Failed to start conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/session/message")
async def send_message(
    conversation_id: str = Form(...),
    audio: Optional[UploadFile] = File(None),
    text: Optional[str] = Form(None),
    background_tasks: BackgroundTasks = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Process user message (Authenticated)"""
    
    # Verify ownership
    convo = db.query(Conversation).filter(
        Conversation.id == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id
    ).first()
    
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found or access denied")
        
    start_time = datetime.now()
    logger.info(f"📨 Received message for conversation: {conversation_id}")
    
    if not audio and not text:
        raise HTTPException(status_code=400, detail="Must provide audio or text")
    
    audio_temp_path = None
    
    try:
        if audio:
            user_audio_data = save_audio_file(audio, conversation_id)
            audio_temp_path = user_audio_data['path']
        
        from services.conversation_service import get_conversation_service
        conversation_service = get_conversation_service()
        
        result = conversation_service.process_message(
            conversation_id=conversation_id,
            audio_path=audio_temp_path,
            text=text,
            db_session=db
        )
        
        if result['status'] == 'error':
            raise HTTPException(status_code=500, detail=result['error'])
        
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        return {
            "status": "success",
            "user_message": result['user_message'],
            "user_emotion": result['user_emotion'],
            "assistant_response": result['assistant_response'],
            "assistant_audio_url": result['assistant_audio_url'],
            "conversation_id": conversation_id,
            "processing_time_ms": processing_time
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Server error: {str(e)}")
    finally:
        if audio_temp_path and os.path.exists(audio_temp_path):
            cleanup_temp_files(audio_temp_path)


@app.post("/api/v1/session/end", response_model=EndConversationResponse)
async def end_session(
    conversation_id: str = Form(...),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """End conversation (Authenticated)"""
    
    # Verify ownership
    convo = db.query(Conversation).filter(
        Conversation.id == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id
    ).first()
    
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        history = get_conversation_history(db, conversation_id, limit=100)
        timeline = get_emotion_timeline(db, conversation_id)
        
        conversation_context = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in history
        ]
        
        summary_text = llm_service.generate_session_summary(
            conversation_history=conversation_context,
            emotion_timeline=timeline
        )
        
        summary_audio_path = tts_service.generate_speech(summary_text, emotion='neutral')
        
        summary_filename = f"{conversation_id}_summary.mp3"
        summary_stored_path = os.path.join(AUDIO_STORAGE_DIR, summary_filename)
        shutil.copy(summary_audio_path, summary_stored_path)
        
        db_end_conversation(db, conversation_id)
        
        duration_minutes = 0
        if convo.ended_at and convo.started_at:
            duration_minutes = (convo.ended_at - convo.started_at).total_seconds() / 60
        
        cleanup_temp_files(summary_audio_path)
        
        return {
            "summary": summary_text,
            "summary_audio_url": f"/api/v1/audio/{summary_filename}",
            "emotional_journey": timeline,
            "total_messages": len(history),
            "duration_minutes": round(duration_minutes, 2)
        }
    
    except Exception as e:
        logger.error(f"Failed to end conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/audio/{filename}")
async def get_audio(filename: str):
    """Serve audio files (Public for now, or use signed URLs in prod)"""
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    return FileResponse(file_path, media_type="audio/mpeg", filename=filename)


@app.get("/api/v1/conversation/{conversation_id}/history")
async def get_history(
    conversation_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get conversation history (Authenticated)"""
    # Verify ownership
    convo = db.query(Conversation).filter(
        Conversation.id == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id
    ).first()
    
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        history = get_conversation_history(db, conversation_id, limit=50)
        return {
            "conversation_id": conversation_id,
            "messages": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/conversation/{conversation_id}/emotions")
async def get_emotions(
    conversation_id: str, 
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get emotion timeline (Authenticated)"""
    # Verify ownership
    convo = db.query(Conversation).filter(
        Conversation.id == uuid.UUID(conversation_id),
        Conversation.user_id == current_user.id
    ).first()
    
    if not convo:
        raise HTTPException(status_code=404, detail="Conversation not found")

    try:
        timeline = get_emotion_timeline(db, conversation_id)
        return {
            "conversation_id": conversation_id,
            "emotion_timeline": timeline
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root():
    return {
        "message": "MECC API v2.1",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "auth": "/api/v1/auth",
            "users": "/api/v1/users",
            "analytics": "/api/v1/analytics",
            "session": "/api/v1/session"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    host = os.environ.get("HOST", "0.0.0.0")
    port = int(os.environ.get("PORT", 8000))
    reload = os.environ.get("RELOAD", "true").lower() == "true"
    
    uvicorn.run(
        "app:app",
        host=host,
        port=port,
        reload=reload,
        log_level="info"
    )
