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
from services.emotion_service import get_emotion_service
from services.free_llm_service import get_free_llm_service
from services.free_tts_service import get_free_tts_service
from services.whisper_service import get_whisper_service
from database import (
    get_db, init_db,
    create_conversation, save_message, get_conversation_history,
    end_conversation as db_end_conversation, get_emotion_timeline
)

# Initialize FastAPI
app = FastAPI(
    title="MECC API",
    description="Multimodal Empathetical Conversational Companion",
    version="2.0.0"
)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global service instances
emotion_service = None
llm_service = None
tts_service = None
whisper_service = None

# Audio storage directory
AUDIO_STORAGE_DIR = os.environ.get('AUDIO_STORAGE_DIR', './audio_storage')
os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)


# Pydantic models
class StartConversationResponse(BaseModel):
    conversation_id: str
    session_id: str
    welcome_message: str
    welcome_audio_url: str


class ChatRequest(BaseModel):
    conversation_id: str
    text: Optional[str] = None


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
    
    logger.info("🚀 Starting MECC Backend API v2.0...")
    
    try:
        # Initialize database
        init_db()
        
        # Initialize services
        checkpoint_path = os.environ.get('MODEL_CHECKPOINT_PATH', 'checkpoints/at.pth')
        device = os.environ.get('DEVICE', 'cuda')
        
        emotion_service = get_emotion_service(checkpoint_path=checkpoint_path, device=device)
        llm_service = get_free_llm_service(model_name="llama3.2:3b")
        
        # TTS: Use OpenAI by default (set TTS_PROVIDER env var to change)
        tts_provider = os.environ.get('TTS_PROVIDER', 'openai')
        tts_service = get_free_tts_service(provider="piper", voice="voices/en_US-lessac-medium.onnx")
        
        # Whisper: Use local model by default (set USE_WHISPER_API=true to use API)
        use_whisper_api = os.environ.get('USE_WHISPER_API', 'false').lower() == 'true'
        whisper_model_size = os.environ.get('WHISPER_MODEL_SIZE', 'base')
        whisper_service = get_whisper_service(
            use_api=use_whisper_api,
            model_size=whisper_model_size,
            device=device
        )
        
        logger.info("✅ All services initialized successfully")
    
    except Exception as e:
        logger.error(f"❌ Failed to initialize services: {e}")
        raise


# Helper functions
def save_audio_file(audio: UploadFile, conversation_id: str) -> Dict:
    """Save uploaded audio file and return metadata"""
    
    # Generate unique filename
    file_id = str(uuid.uuid4())
    file_ext = os.path.splitext(audio.filename)[1] or '.wav'
    filename = f"{conversation_id}_{file_id}{file_ext}"
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    
    # Save file
    with open(file_path, 'wb') as f:
        content = audio.file.read()
        f.write(content)
    
    # Get duration (using librosa) with fallback
    duration = 0.0
    try:
        import librosa
        waveform, sr = librosa.load(file_path, sr=None)
        duration = len(waveform) / sr
    except Exception as e:
        logger.warning(f"Failed to load audio for duration calculation (possibly missing ffmpeg): {e}")
        # Continue without duration - not critical
    
    return {
        'path': file_path,
        'duration': duration,
        'size': len(content),
        'filename': filename
    }


def cleanup_temp_files(*files):
    """Clean up temporary files"""
    for file_path in files:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except:
                pass


# Endpoints

@app.get("/health")
async def health_check():
    """Health check"""
    return {
        "status": "healthy",
        "version": "2.0.0",
        "services": {
            "emotion_model": "loaded" if emotion_service else "not loaded",
            "llm": "loaded" if llm_service else "not loaded",
            "tts": "loaded" if tts_service else "not loaded",
            "whisper": "loaded" if whisper_service else "not loaded"
        }
    }


@app.post("/api/v1/session/start", response_model=StartConversationResponse)
async def start_session(
    user_id: Optional[str] = Form(None),
    db: Session = Depends(get_db)
):
    """
    Start a new conversation session.
    System initiates with a welcome message.
    """
    try:
        # Create conversation in DB
        conversation = create_conversation(db, user_id=user_id)
        
        # Generate welcome message
        welcome_text = "Hello! I'm here to listen and support you. How are you feeling today?"
        
        # Convert to speech
        audio_path = tts_service.generate_speech(welcome_text, emotion='neutral')
        
        # Move audio to storage
        stored_filename = f"{conversation.session_id}_welcome.mp3"
        stored_path = os.path.join(AUDIO_STORAGE_DIR, stored_filename)
        shutil.copy(audio_path, stored_path)
        
        # Save welcome message to DB
        save_message(
            db,
            conversation_id=str(conversation.id),
            role='assistant',
            content=welcome_text,
            audio_data={'path': stored_path, 'duration': 3.0}
        )
        
        # Cleanup temp file
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
    db: Session = Depends(get_db)
):
    """
    Process user message (audio and/or text) and generate empathetic response.
    """
    start_time = datetime.now()
    logger.info(f"Received message request for conversation: {conversation_id}")
    
    if not audio and not text:
        logger.error("No audio or text provided in request")
        raise HTTPException(status_code=400, detail="Must provide audio or text")
    
    audio_temp_path = None
    user_audio_data = None
    
    try:
        # Step 1: Handle audio input
        if audio:
            logger.info(f"Processing audio input: {audio.filename}, content_type={audio.content_type}")
            user_audio_data = save_audio_file(audio, conversation_id)
            audio_temp_path = user_audio_data['path']
            logger.info(f"Audio saved to: {audio_temp_path}")
            
            # Step 2: Transcribe audio
            if not text:  # If text not provided, transcribe audio
                logger.info("Transcribing audio...")
                transcription = whisper_service.transcribe(audio_temp_path)
                text = transcription['text']
                logger.info(f"Transcribed text: {text}")
            
        if not text or len(text.strip()) == 0:
            logger.error("No text content found after transcription")
            raise HTTPException(status_code=400, detail="No valid text input")
        
        logger.info(f"Final text to process: {text}")

        # Step 3: Detect emotion
        logger.info("Detecting emotion...")
        emotion_result = emotion_service.predict_emotion(
            audio_path=audio_temp_path if audio else None,
            text=text
        )
        logger.info(f"Emotion result: {emotion_result}")
        
        # Step 4: Get conversation history
        history = get_conversation_history(db, conversation_id, limit=10)
        conversation_context = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in history
        ]
        logger.info(f"Retrieved {len(history)} messages of context")
        
        # Step 5: Generate empathetic response
        logger.info("Generating LLM response...")
        assistant_text = llm_service.generate_empathetic_response(
            user_message=text,
            detected_emotion=emotion_result['emotion'],
            emotion_confidence=emotion_result['confidence'],
            conversation_history=conversation_context
        )
        logger.info(f"LLM Response: {assistant_text}")
        
        # Step 6: Convert response to speech
        logger.info("Generating TTS audio...")
        assistant_audio_path = tts_service.generate_speech(
            assistant_text,
            emotion=emotion_result['emotion']
        )
        logger.info(f"TTS Audio generated at: {assistant_audio_path}")
        
        # Move assistant audio to storage
        assistant_filename = f"{conversation_id}_{uuid.uuid4()}.mp3"
        assistant_stored_path = os.path.join(AUDIO_STORAGE_DIR, assistant_filename)
        shutil.copy(assistant_audio_path, assistant_stored_path)
        
        # Step 7: Save messages to DB
        processing_time = int((datetime.now() - start_time).total_seconds() * 1000)
        
        # Save user message
        save_message(
            db,
            conversation_id=conversation_id,
            role='user',
            content=text,
            emotion_data=emotion_result,
            audio_data=user_audio_data,
            processing_time=processing_time
        )
        
        # Save assistant message
        save_message(
            db,
            conversation_id=conversation_id,
            role='assistant',
            content=assistant_text,
            audio_data={'path': assistant_stored_path, 'duration': 5.0}  # Estimate
        )
        
        # Cleanup temp files in background
        if background_tasks:
            background_tasks.add_task(cleanup_temp_files, assistant_audio_path)
        
        logger.info(f"Chat completed in {processing_time}ms")
        
        # Step 8: Return response
        return {
            "status": "success",
            "user_message": text,
            "user_emotion": emotion_result,
            "assistant_response": assistant_text,
            "assistant_audio_url": f"/api/v1/audio/{assistant_filename}",
            "conversation_id": conversation_id,
            "processing_time_ms": processing_time
        }
    
    except Exception as e:
        logger.error(f"Chat processing failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/v1/session/end", response_model=EndConversationResponse)
async def end_session(
    conversation_id: str = Form(...),
    db: Session = Depends(get_db)
):
    """
    End conversation and generate summary.
    """
    try:
        logger.info(f"Ending session: {conversation_id}")
        
        # Get conversation history
        history = get_conversation_history(db, conversation_id, limit=100)
        logger.info(f"Retrieved {len(history)} messages from conversation")
        
        # Get emotion timeline
        timeline = get_emotion_timeline(db, conversation_id)
        logger.info(f"Retrieved {len(timeline)} emotion timeline entries")
        
        # Format for LLM
        conversation_context = [
            {'role': msg['role'], 'content': msg['content']}
            for msg in history
        ]
        logger.info(f"Prepared {len(conversation_context)} messages for summary")
        
        # Generate summary
        summary_text = llm_service.generate_session_summary(
            conversation_history=conversation_context,
            emotion_timeline=timeline
        )
        
        # Convert summary to speech
        summary_audio_path = tts_service.generate_speech(summary_text, emotion='neutral')
        
        # Store summary audio
        summary_filename = f"{conversation_id}_summary.mp3"
        summary_stored_path = os.path.join(AUDIO_STORAGE_DIR, summary_filename)
        shutil.copy(summary_audio_path, summary_stored_path)
        
        # Mark conversation as completed
        db_end_conversation(db, conversation_id)
        
        # Get conversation details
        from database import Conversation
        conversation = db.query(Conversation).filter(
            Conversation.id == uuid.UUID(conversation_id)
        ).first()
        
        duration_minutes = 0
        if conversation and conversation.ended_at and conversation.started_at:
            duration_minutes = (conversation.ended_at - conversation.started_at).total_seconds() / 60
        
        # Cleanup temp
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
    """Serve audio files"""
    file_path = os.path.join(AUDIO_STORAGE_DIR, filename)
    
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Audio file not found")
    
    return FileResponse(
        file_path,
        media_type="audio/mpeg",
        filename=filename
    )


@app.get("/api/v1/conversation/{conversation_id}/history")
async def get_history(conversation_id: str, db: Session = Depends(get_db)):
    """Get conversation history"""
    try:
        history = get_conversation_history(db, conversation_id, limit=50)
        return {
            "conversation_id": conversation_id,
            "messages": history
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/conversation/{conversation_id}/emotions")
async def get_emotions(conversation_id: str, db: Session = Depends(get_db)):
    """Get emotion timeline for a conversation"""
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
    """API root"""
    return {
        "message": "MECC API v2.0",
        "status": "running",
        "docs": "/docs",
        "endpoints": {
            "start_conversation": "/api/v1/conversation/start",
            "chat": "/api/v1/chat/message",
            "end_conversation": "/api/v1/conversation/end",
            "get_audio": "/api/v1/audio/{filename}",
            "history": "/api/v1/conversation/{id}/history",
            "emotions": "/api/v1/conversation/{id}/emotions"
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
