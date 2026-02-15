# Video/Audio Length Handling & Conversation Flow

## Table of Contents
1. [Audio/Video Length Constraints](#audiovideo-length-constraints)
2. [Processing Pipeline](#processing-pipeline)
3. [Database Schema](#database-schema)
4. [Text-to-Speech Integration](#text-to-speech-integration)
5. [Complete Conversation Flow](#complete-conversation-flow)
6. [Implementation Updates](#implementation-updates)

---

## Audio/Video Length Constraints

### Current Model Capabilities

#### WavLM (Audio Encoder)
- **Maximum input length**: ~30 seconds (480,000 samples at 16kHz)
- **Optimal length**: 5-15 seconds
- **Minimum length**: 1 second
- **Processing**: Mean pooling over time → length-agnostic output (768-dim)

#### RoBERTa (Text Encoder)
- **Maximum tokens**: 512 (model limit)
- **Optimal tokens**: 50-128 tokens
- **Processing**: Truncation at 128 tokens in current implementation

#### Video (If/When Added)
- **Current implementation**: Per-frame processing
- **Frame rate**: Extract 1-3 fps for efficiency
- **Maximum duration**: 30 seconds (90 frames at 3fps)

### Length Handling Strategy

```python
class AudioLengthHandler:
    """Handle audio clips of varying lengths"""
    
    MIN_LENGTH = 1.0    # seconds
    MAX_LENGTH = 30.0   # seconds
    OPTIMAL_LENGTH = 10.0  # seconds
    
    @staticmethod
    def handle_audio_length(audio_path: str) -> List[str]:
        """
        Split or pad audio to optimal lengths.
        
        Returns:
            List of audio file paths (chunked if needed)
        """
        import librosa
        import soundfile as sf
        import numpy as np
        
        # Load audio
        waveform, sr = librosa.load(audio_path, sr=16000)
        duration = len(waveform) / sr
        
        # Case 1: Too short (<1s) - pad with silence
        if duration < AudioLengthHandler.MIN_LENGTH:
            padding_needed = int((AudioLengthHandler.MIN_LENGTH - duration) * sr)
            waveform = np.pad(waveform, (0, padding_needed), mode='constant')
            
            # Save padded audio
            temp_path = audio_path.replace('.wav', '_padded.wav')
            sf.write(temp_path, waveform, sr)
            return [temp_path]
        
        # Case 2: Optimal length (1-30s) - use as-is
        elif duration <= AudioLengthHandler.MAX_LENGTH:
            return [audio_path]
        
        # Case 3: Too long (>30s) - chunk into segments
        else:
            chunks = []
            chunk_length = int(AudioLengthHandler.OPTIMAL_LENGTH * sr)
            overlap = int(2.0 * sr)  # 2-second overlap for context
            
            start = 0
            chunk_idx = 0
            
            while start < len(waveform):
                end = min(start + chunk_length, len(waveform))
                chunk = waveform[start:end]
                
                # Save chunk
                chunk_path = audio_path.replace('.wav', f'_chunk{chunk_idx}.wav')
                sf.write(chunk_path, chunk, sr)
                chunks.append(chunk_path)
                
                start = end - overlap  # Overlap for context continuity
                chunk_idx += 1
                
                # Limit to 5 chunks (50s total) to prevent excessive processing
                if chunk_idx >= 5:
                    break
            
            return chunks
    
    @staticmethod
    def aggregate_chunked_predictions(predictions: List[Dict]) -> Dict:
        """
        Aggregate predictions from multiple audio chunks.
        Uses weighted average based on confidence.
        """
        if len(predictions) == 1:
            return predictions[0]
        
        # Weight by confidence
        total_weight = sum(p['confidence'] for p in predictions)
        
        aggregated_probs = {
            'neutral': 0.0,
            'happy': 0.0,
            'angry': 0.0,
            'sad': 0.0
        }
        
        for pred in predictions:
            weight = pred['confidence'] / total_weight
            for emotion, prob in pred['probabilities'].items():
                aggregated_probs[emotion] += prob * weight
        
        # Get final emotion
        final_emotion = max(aggregated_probs.items(), key=lambda x: x[1])
        
        return {
            'emotion': final_emotion[0],
            'confidence': final_emotion[1],
            'probabilities': aggregated_probs,
            'num_chunks': len(predictions)
        }
```

### Recommended User Experience

```
Duration Guidelines:
├─ < 1 second  → "Your message was too short. Please speak for at least 1 second."
├─ 1-15 seconds  → ✅ Optimal (fast processing, good quality)
├─ 15-30 seconds → ✅ Good (slightly slower, still single chunk)
├─ 30-60 seconds → ⚠️  Acceptable (chunked processing, longer latency)
└─ > 60 seconds  → ❌ "Please keep responses under 60 seconds for best results."
```

---

## Processing Pipeline

### Complete Audio/Video Processing Flow

```
User Records → Frontend Validation → Backend Processing → Response

┌─────────────────────────────────────────────────────────────────┐
│                    1. FRONTEND VALIDATION                       │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Recording Controls:                                       │  │
│  │ - Min: 1s (show timer)                                   │  │
│  │ - Max: 60s (auto-stop with warning at 55s)              │  │
│  │ - Visual feedback: waveform, duration counter            │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    2. BACKEND VALIDATION                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ Check audio quality:                                      │  │
│  │ - Format: WAV/MP3/M4A                                    │  │
│  │ - Sample rate: 16kHz (resample if needed)               │  │
│  │ - Channels: Mono (convert if stereo)                    │  │
│  │ - Duration: 1-60s                                        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    3. LENGTH HANDLING                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ If < 1s:   Pad with silence                              │  │
│  │ If 1-30s:  Process as single chunk                       │  │
│  │ If 30-60s: Split into 10s chunks with 2s overlap        │  │
│  │ If > 60s:  Reject (frontend should prevent this)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    4. FEATURE EXTRACTION                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ For each chunk:                                           │  │
│  │ - Audio → WavLM → 768-dim embedding                      │  │
│  │ - Transcribe (Whisper) → Text                           │  │
│  │ - Text → RoBERTa → 768-dim embedding                    │  │
│  │ - Concatenate → 1536-dim fused features                 │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────────┐
│                    5. EMOTION PREDICTION                        │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │ If multiple chunks:                                       │  │
│  │ - Aggregate predictions (weighted by confidence)         │  │
│  │ - Return dominant emotion                                │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Database Schema

### Required Database Tables

```sql
-- conversations table
CREATE TABLE conversations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255),  -- Optional: for user tracking
    session_id VARCHAR(255) UNIQUE NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    total_messages INTEGER DEFAULT 0,
    status VARCHAR(50) DEFAULT 'active',  -- active, completed, abandoned
    metadata JSONB,  -- Store additional context
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- messages table
CREATE TABLE messages (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,  -- 'user' or 'assistant'
    content TEXT NOT NULL,
    
    -- Emotion data (for user messages)
    detected_emotion VARCHAR(50),
    emotion_confidence FLOAT,
    emotion_probabilities JSONB,
    
    -- Media metadata
    has_audio BOOLEAN DEFAULT FALSE,
    audio_duration FLOAT,
    audio_path VARCHAR(500),  -- S3/local path to stored audio
    
    -- Processing metadata
    processing_time_ms INTEGER,
    model_version VARCHAR(50) DEFAULT 'at-v1.0',
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_created_at (created_at)
);

-- emotion_timeline table (for analytics)
CREATE TABLE emotion_timeline (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    conversation_id UUID REFERENCES conversations(id) ON DELETE CASCADE,
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    emotion VARCHAR(50) NOT NULL,
    confidence FLOAT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_conversation_id (conversation_id),
    INDEX idx_emotion (emotion)
);

-- audio_files table (optional: for tracking audio storage)
CREATE TABLE audio_files (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    message_id UUID REFERENCES messages(id) ON DELETE CASCADE,
    file_path VARCHAR(500) NOT NULL,
    file_size_bytes BIGINT,
    duration_seconds FLOAT,
    format VARCHAR(20),  -- wav, mp3, m4a
    sample_rate INTEGER DEFAULT 16000,
    channels INTEGER DEFAULT 1,
    uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_message_id (message_id)
);

-- system_metrics table (for monitoring)
CREATE TABLE system_metrics (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    metric_name VARCHAR(100) NOT NULL,
    metric_value FLOAT NOT NULL,
    metric_unit VARCHAR(50),
    metadata JSONB,
    recorded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    
    INDEX idx_metric_name (metric_name),
    INDEX idx_recorded_at (recorded_at)
);
```

### Database Connection (PostgreSQL example)

```python
# database.py
from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os

DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://user:password@localhost:5432/mecc_db'
)

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# Models
class Conversation(Base):
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String, unique=True, nullable=False, index=True)
    user_id = Column(String, nullable=True)
    started_at = Column(DateTime, default=datetime.utcnow)
    ended_at = Column(DateTime, nullable=True)
    total_messages = Column(Integer, default=0)
    status = Column(String, default='active')
    metadata = Column(JSON, default={})
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    role = Column(String, nullable=False)
    content = Column(String, nullable=False)
    
    detected_emotion = Column(String, nullable=True)
    emotion_confidence = Column(Float, nullable=True)
    emotion_probabilities = Column(JSON, nullable=True)
    
    has_audio = Column(Boolean, default=False)
    audio_duration = Column(Float, nullable=True)
    audio_path = Column(String, nullable=True)
    
    processing_time_ms = Column(Integer, nullable=True)
    model_version = Column(String, default='at-v1.0')
    
    created_at = Column(DateTime, default=datetime.utcnow)

class EmotionTimeline(Base):
    __tablename__ = "emotion_timeline"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    emotion = Column(String, nullable=False)
    confidence = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)

# Create tables
def init_db():
    Base.metadata.create_all(bind=engine)

# Dependency
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

---

## Text-to-Speech Integration

### Option 1: OpenAI TTS (Recommended)

```python
# tts_service.py
from openai import OpenAI
import os
from typing import Optional
import tempfile

class TTSService:
    """Text-to-Speech service using OpenAI TTS"""
    
    def __init__(self):
        self.client = OpenAI(api_key=os.environ.get('OPENAI_API_KEY'))
        self.voice = "alloy"  # Options: alloy, echo, fable, onyx, nova, shimmer
        self.model = "tts-1"  # or "tts-1-hd" for higher quality
    
    def text_to_speech(self, text: str, emotion: Optional[str] = None) -> str:
        """
        Convert text to speech audio.
        
        Args:
            text: Text to convert
            emotion: Detected emotion (used to select appropriate voice)
        
        Returns:
            Path to generated audio file
        """
        # Select voice based on emotion for more natural response
        voice = self._select_voice(emotion)
        
        # Generate speech
        response = self.client.audio.speech.create(
            model=self.model,
            voice=voice,
            input=text,
            response_format="mp3"  # or "opus", "aac", "flac"
        )
        
        # Save to temporary file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        response.stream_to_file(temp_file.name)
        
        return temp_file.name
    
    def _select_voice(self, emotion: Optional[str]) -> str:
        """Select voice based on emotion for more natural feel"""
        voice_mapping = {
            'happy': 'nova',      # Warm, upbeat
            'sad': 'echo',        # Calm, soothing
            'angry': 'onyx',      # Steady, grounding
            'neutral': 'alloy'    # Neutral, professional
        }
        return voice_mapping.get(emotion, 'alloy')
```

### Option 2: ElevenLabs (More Emotional)

```python
from elevenlabs import generate, play, set_api_key, Voice, VoiceSettings

class ElevenLabsTTS:
    """More expressive TTS with ElevenLabs"""
    
    def __init__(self):
        set_api_key(os.environ.get('ELEVENLABS_API_KEY'))
        self.voice_id = "EXAVITQu4vr4xnSDxMaL"  # Default voice
    
    def text_to_speech(self, text: str, emotion: Optional[str] = None) -> str:
        """Generate emotional speech"""
        
        # Adjust voice settings based on emotion
        settings = self._get_voice_settings(emotion)
        
        audio = generate(
            text=text,
            voice=Voice(
                voice_id=self.voice_id,
                settings=settings
            ),
            model="eleven_multilingual_v2"
        )
        
        # Save to file
        temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3')
        with open(temp_file.name, 'wb') as f:
            f.write(audio)
        
        return temp_file.name
    
    def _get_voice_settings(self, emotion: str) -> VoiceSettings:
        """Adjust voice parameters based on emotion"""
        settings = {
            'happy': VoiceSettings(stability=0.5, similarity_boost=0.8, speed=1.1),
            'sad': VoiceSettings(stability=0.7, similarity_boost=0.7, speed=0.9),
            'angry': VoiceSettings(stability=0.4, similarity_boost=0.6, speed=1.0),
            'neutral': VoiceSettings(stability=0.6, similarity_boost=0.75, speed=1.0)
        }
        return settings.get(emotion, VoiceSettings(stability=0.6, similarity_boost=0.75))
```

### Option 3: Azure TTS (Enterprise)

```python
import azure.cognitiveservices.speech as speechsdk

class AzureTTS:
    """Enterprise-grade TTS with Azure Cognitive Services"""
    
    def __init__(self):
        speech_config = speechsdk.SpeechConfig(
            subscription=os.environ.get('AZURE_SPEECH_KEY'),
            region=os.environ.get('AZURE_REGION')
        )
        
        # Set voice based on emotion
        speech_config.speech_synthesis_voice_name = "en-US-JennyNeural"
        
        self.speech_synthesizer = speechsdk.SpeechSynthesizer(
            speech_config=speech_config
        )
    
    def text_to_speech(self, text: str, emotion: Optional[str] = None) -> str:
        """Generate speech with SSML for emotion control"""
        
        # Use SSML to control emotion and prosody
        ssml = self._create_ssml(text, emotion)
        
        result = self.speech_synthesizer.speak_ssml_async(ssml).get()
        
        if result.reason == speechsdk.ResultReason.SynthesizingAudioCompleted:
            # Save audio
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix='.wav')
            with open(temp_file.name, 'wb') as f:
                f.write(result.audio_data)
            return temp_file.name
        else:
            raise Exception(f"TTS failed: {result.reason}")
    
    def _create_ssml(self, text: str, emotion: str) -> str:
        """Create SSML with emotion markup"""
        emotion_styles = {
            'happy': 'cheerful',
            'sad': 'sad',
            'angry': 'serious',
            'neutral': 'friendly'
        }
        
        style = emotion_styles.get(emotion, 'friendly')
        
        ssml = f"""
        <speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" 
               xmlns:mstts="https://www.w3.org/2001/mstts" xml:lang="en-US">
            <voice name="en-US-JennyNeural">
                <mstts:express-as style="{style}">
                    {text}
                </mstts:express-as>
            </voice>
        </speak>
        """
        return ssml
```

---

## Complete Conversation Flow

### Full End-to-End Flow

```
┌─────────────────────────────────────────────────────────────────┐
│                   SYSTEM INITIATES CONVERSATION                 │
│                                                                 │
│  1. User visits app                                            │
│  2. System: "Hello! I'm here to listen. How are you today?"   │
│  3. Create conversation_id in DB                                │
│  4. Play welcome audio (TTS)                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   USER RECORDS RESPONSE                         │
│                                                                 │
│  1. User clicks "Record" button                                │
│  2. Microphone activates                                        │
│  3. Visual feedback (waveform, timer)                          │
│  4. User speaks (1-60 seconds)                                 │
│  5. User clicks "Stop" or auto-stop at 60s                    │
│  6. Frontend validates duration (>1s)                          │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   SEND TO BACKEND                               │
│                                                                 │
│  POST /api/v1/chat/message                                     │
│  {                                                              │
│    audio: Blob (recorded audio),                              │
│    conversation_id: "uuid-here",                              │
│    session_context: {...previous messages...}                  │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   BACKEND PROCESSING                            │
│                                                                 │
│  1. Save audio to storage                                      │
│  2. Check audio length → chunk if needed                       │
│  3. Extract audio features (WavLM)                             │
│  4. Transcribe audio (Whisper)                                │
│  5. Extract text features (RoBERTa)                            │
│  6. Predict emotion (FusionMLP)                                │
│  7. Retrieve conversation history from DB                      │
│  8. Generate empathetic response (LLM)                         │
│  9. Convert response to speech (TTS)                           │
│  10. Save message to DB                                        │
│  11. Update emotion timeline                                   │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   RETURN RESPONSE                               │
│                                                                 │
│  {                                                              │
│    user_message: "transcribed text",                          │
│    user_emotion: {emotion, confidence, probabilities},        │
│    assistant_response: "empathetic text",                     │
│    assistant_audio_url: "https://.../response.mp3",          │
│    conversation_id: "uuid",                                    │
│    message_id: "uuid"                                          │
│  }                                                              │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   FRONTEND DISPLAYS RESPONSE                    │
│                                                                 │
│  1. Show user message with emotion badge                       │
│  2. Show assistant text response                               │
│  3. Auto-play assistant audio                                  │
│  4. Update emotion indicator                                   │
│  5. Enable "Record next response" button                       │
└─────────────────────────────────────────────────────────────────┘
                            ↓
┌─────────────────────────────────────────────────────────────────┐
│                   CONVERSATION CONTINUES                        │
│                                                                 │
│  User can:                                                      │
│  - Record another response (loop back to step 2)              │
│  - End conversation → Generate summary                         │
│  - View emotion history                                        │
└─────────────────────────────────────────────────────────────────┘
```

### Session Management Flow

```python
class ConversationManager:
    """Manages conversation sessions and context"""
    
    def __init__(self, db):
        self.db = db
    
    def start_conversation(self, user_id: Optional[str] = None) -> Dict:
        """
        Start a new conversation session.
        
        Returns:
            {
                'conversation_id': uuid,
                'session_id': str,
                'welcome_message': str,
                'welcome_audio_url': str
            }
        """
        session_id = str(uuid.uuid4())
        
        # Create conversation in DB
        conversation = Conversation(
            session_id=session_id,
            user_id=user_id,
            status='active'
        )
        self.db.add(conversation)
        self.db.commit()
        
        # Generate welcome message
        welcome_text = "Hello! I'm here to listen and support you. How are you feeling today?"
        
        # Convert to speech
        tts_service = TTSService()
        audio_path = tts_service.text_to_speech(welcome_text)
        
        # Save welcome message
        welcome_msg = Message(
            conversation_id=conversation.id,
            role='assistant',
            content=welcome_text,
            has_audio=True,
            audio_path=audio_path
        )
        self.db.add(welcome_msg)
        self.db.commit()
        
        return {
            'conversation_id': str(conversation.id),
            'session_id': session_id,
            'welcome_message': welcome_text,
            'welcome_audio_url': f'/api/v1/audio/{welcome_msg.id}'
        }
    
    def get_conversation_context(self, conversation_id: str, max_messages: int = 10) -> List[Dict]:
        """
        Retrieve recent conversation history for context.
        
        Args:
            conversation_id: UUID of conversation
            max_messages: Maximum number of recent messages to retrieve
        
        Returns:
            List of messages in format [{'role': 'user/assistant', 'content': '...'}]
        """
        messages = self.db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at.desc())\
            .limit(max_messages)\
            .all()
        
        # Reverse to chronological order
        messages = list(reversed(messages))
        
        return [
            {
                'role': msg.role,
                'content': msg.content,
                'emotion': msg.detected_emotion if msg.role == 'user' else None
            }
            for msg in messages
        ]
    
    def end_conversation(self, conversation_id: str) -> Dict:
        """
        End conversation and generate summary.
        
        Returns:
            {
                'summary': str,
                'summary_audio_url': str,
                'emotional_journey': List[Dict],
                'total_messages': int,
                'duration_minutes': float
            }
        """
        conversation = self.db.query(Conversation)\
            .filter(Conversation.id == conversation_id)\
            .first()
        
        if not conversation:
            raise ValueError("Conversation not found")
        
        # Update conversation status
        conversation.ended_at = datetime.utcnow()
        conversation.status = 'completed'
        
        # Get full conversation history
        messages = self.db.query(Message)\
            .filter(Message.conversation_id == conversation_id)\
            .order_by(Message.created_at)\
            .all()
        
        # Get emotion timeline
        emotions = self.db.query(EmotionTimeline)\
            .filter(EmotionTimeline.conversation_id == conversation_id)\
            .order_by(EmotionTimeline.timestamp)\
            .all()
        
        # Generate summary using LLM
        llm_service = get_llm_service()
        
        conversation_history = [
            {'role': msg.role, 'content': msg.content}
            for msg in messages
        ]
        
        emotion_timeline = [
            {
                'emotion': e.emotion,
                'confidence': e.confidence,
                'timestamp': e.timestamp.isoformat()
            }
            for e in emotions
        ]
        
        summary_text = llm_service.generate_session_summary(
            conversation_history=conversation_history,
            emotion_timeline=emotion_timeline
        )
        
        # Convert summary to speech
        tts_service = TTSService()
        summary_audio = tts_service.text_to_speech(summary_text)
        
        # Calculate duration
        duration_minutes = (conversation.ended_at - conversation.started_at).total_seconds() / 60
        
        self.db.commit()
        
        return {
            'summary': summary_text,
            'summary_audio_url': f'/api/v1/audio/summary/{conversation_id}',
            'emotional_journey': emotion_timeline,
            'total_messages': len(messages),
            'duration_minutes': round(duration_minutes, 2)
        }
```

---

## Implementation Updates

### Missing Components to Add

1. **Whisper Integration** (for audio transcription)
2. **TTS Service** (OpenAI/ElevenLabs/Azure)
3. **Database Layer** (SQLAlchemy + PostgreSQL)
4. **Audio Storage** (S3 or local filesystem)
5. **Session Management** (conversation context)
6. **Audio Length Validation**
7. **Chunked Audio Processing**

### Priority Implementation Order

**Week 1 - Critical:**
1. ✅ Database setup (PostgreSQL + SQLAlchemy)
2. ✅ Whisper transcription integration
3. ✅ TTS service (start with OpenAI TTS)
4. ✅ Session management endpoints

**Week 2 - Important:**
5. ✅ Audio length handling (chunking)
6. ✅ Audio storage (start with local, migrate to S3 later)
7. ✅ Conversation history retrieval
8. ✅ Frontend audio player integration

**Week 3 - Nice-to-have:**
9. ⚠️ Advanced emotion aggregation for long audio
10. ⚠️ Session analytics dashboard
11. ⚠️ Audio file cleanup/archival

---

## Summary of Missing Pieces

✅ **What You Have:**
- Emotion detection model (A+T, 70.7% accuracy)
- Basic API endpoints
- Frontend UI structure

❌ **What's Missing:**
1. **Database integration** - Store conversations, messages, emotions
2. **Audio transcription** - Whisper to convert speech to text
3. **Text-to-Speech** - Convert assistant responses to audio
4. **Audio length handling** - Chunking for >30s audio
5. **Session management** - Track conversation context across messages
6. **Audio storage** - Where to store uploaded/generated audio files
7. **Conversation initialization** - System-initiated welcome flow
8. **End session** - Generate summary and close conversation

I'll create implementation files for these missing pieces next.
