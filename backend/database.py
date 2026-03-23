"""
MECC Database Models
SQLAlchemy models for conversations, messages, and emotion tracking.
"""

from sqlalchemy import create_engine, Column, String, Float, Integer, Boolean, DateTime, JSON, Text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid
from datetime import datetime
import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

logger = logging.getLogger(__name__)

# Database URL from environment
DATABASE_URL = os.environ.get(
    'DATABASE_URL',
    'postgresql://mecc_user:mecc_password@localhost:5432/mecc_db'
)

# Create engine
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


# Models
class User(Base):
    """User account"""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String(255), unique=True, index=True, nullable=False)
    name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    preferences = Column(JSON, default=dict)  # UI preferences (theme, voice, etc.)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': str(self.id),
            'email': self.email,
            'name': self.name,
            'is_active': self.is_active,
            'preferences': self.preferences
        }


class Conversation(Base):
    """Conversation session"""
    __tablename__ = "conversations"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(String(255), unique=True, nullable=False, index=True)
    
    # Linked to User (nullable for guest sessions if needed, though we will largely enforce auth)
    user_id = Column(UUID(as_uuid=True), index=True, nullable=True) # Keeping it loose for now to recognize strings vs uuids in transition, or strict? Let's go strict UUID for new system.
    
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    ended_at = Column(DateTime, nullable=True)
    
    total_messages = Column(Integer, default=0)
    status = Column(String(50), default='active')  # active, completed, abandoned
    
    meta_data = Column(JSON, default=dict)  # renamed from 'metadata' (reserved by SQLAlchemy)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'session_id': self.session_id,
            'user_id': str(self.user_id) if self.user_id else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'ended_at': self.ended_at.isoformat() if self.ended_at else None,
            'total_messages': self.total_messages,
            'status': self.status,
            'meta_data': self.meta_data
        }


class Message(Base):
    """Individual message in a conversation"""
    __tablename__ = "messages"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    role = Column(String(20), nullable=False)  # 'user' or 'assistant'
    content = Column(Text, nullable=False)
    
    # Emotion data (for user messages)
    detected_emotion = Column(String(50), nullable=True)
    emotion_confidence = Column(Float, nullable=True)
    emotion_probabilities = Column(JSON, nullable=True)
    
    # Audio metadata
    has_audio = Column(Boolean, default=False)
    audio_duration = Column(Float, nullable=True)
    audio_path = Column(String(500), nullable=True)
    audio_chunks = Column(Integer, default=1)  # Number of chunks if split
    
    # Processing metadata
    processing_time_ms = Column(Integer, nullable=True)
    model_version = Column(String(50), default='at-v1.0')
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'role': self.role,
            'content': self.content,
            'detected_emotion': self.detected_emotion,
            'emotion_confidence': self.emotion_confidence,
            'emotion_probabilities': self.emotion_probabilities,
            'has_audio': self.has_audio,
            'audio_duration': self.audio_duration,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class EmotionTimeline(Base):
    """Emotion tracking for analytics"""
    __tablename__ = "emotion_timeline"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id = Column(UUID(as_uuid=True), nullable=False)
    
    emotion = Column(String(50), nullable=False, index=True)
    confidence = Column(Float, nullable=False)
    
    timestamp = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'conversation_id': str(self.conversation_id),
            'message_id': str(self.message_id),
            'emotion': self.emotion,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat() if self.timestamp else None
        }


class AudioFile(Base):
    """Audio file storage tracking"""
    __tablename__ = "audio_files"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    message_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    
    file_path = Column(String(500), nullable=False)
    file_size_bytes = Column(Integer, nullable=True)
    duration_seconds = Column(Float, nullable=True)
    
    format = Column(String(20), default='wav')  # wav, mp3, m4a
    sample_rate = Column(Integer, default=16000)
    channels = Column(Integer, default=1)
    
    is_chunked = Column(Boolean, default=False)
    chunk_index = Column(Integer, nullable=True)
    
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': str(self.id),
            'message_id': str(self.message_id),
            'file_path': self.file_path,
            'file_size_bytes': self.file_size_bytes,
            'duration_seconds': self.duration_seconds,
            'format': self.format
        }


# Database initialization
def init_db():
    """Create all tables"""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


def get_db():
    """Dependency for FastAPI to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# Helper functions
def create_conversation(db, user_id: str = None) -> Conversation:
    """Create a new conversation"""
    session_id = str(uuid.uuid4())
    
    conversation = Conversation(
        session_id=session_id,
        user_id=user_id,
        status='active'
    )
    
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    
    logger.info(f"Created conversation: {conversation.id}")
    return conversation


def save_message(
    db,
    conversation_id: str,
    role: str,
    content: str,
    emotion_data: dict = None,
    audio_data: dict = None,
    processing_time: int = None
) -> Message:
    """Save a message to the database"""
    
    message = Message(
        conversation_id=uuid.UUID(conversation_id),
        role=role,
        content=content,
        processing_time_ms=processing_time
    )
    
    # Add emotion data if present
    if emotion_data:
        message.detected_emotion = emotion_data.get('emotion')
        message.emotion_confidence = emotion_data.get('confidence')
        message.emotion_probabilities = emotion_data.get('probabilities')
    
    # Add audio data if present
    if audio_data:
        message.has_audio = True
        message.audio_path = audio_data.get('path')
        message.audio_duration = audio_data.get('duration')
        message.audio_chunks = audio_data.get('chunks', 1)
    
    db.add(message)
    db.commit()
    db.refresh(message)
    
    # Update conversation message count
    conversation = db.query(Conversation).filter(
        Conversation.id == uuid.UUID(conversation_id)
    ).first()
    
    if conversation:
        conversation.total_messages += 1
        db.commit()
    
    # Save emotion timeline if user message
    if role == 'user' and emotion_data:
        emotion_entry = EmotionTimeline(
            conversation_id=uuid.UUID(conversation_id),
            message_id=message.id,
            emotion=emotion_data['emotion'],
            confidence=emotion_data['confidence']
        )
        db.add(emotion_entry)
        db.commit()
    
    logger.info(f"Saved message: {message.id}")
    return message


def get_conversation_history(db, conversation_id: str, limit: int = 20) -> list:
    """Get recent conversation history"""
    
    messages = db.query(Message).filter(
        Message.conversation_id == uuid.UUID(conversation_id)
    ).order_by(
        Message.created_at.desc()
    ).limit(limit).all()
    
    # Reverse to chronological order
    messages = list(reversed(messages))
    
    return [msg.to_dict() for msg in messages]


def end_conversation(db, conversation_id: str):
    """Mark conversation as completed"""
    
    conversation = db.query(Conversation).filter(
        Conversation.id == uuid.UUID(conversation_id)
    ).first()
    
    if conversation:
        conversation.ended_at = datetime.utcnow()
        conversation.status = 'completed'
        db.commit()
        
        logger.info(f"Ended conversation: {conversation_id}")


def get_emotion_timeline(db, conversation_id: str) -> list:
    """Get emotion timeline for a conversation"""
    
    timeline = db.query(EmotionTimeline).filter(
        EmotionTimeline.conversation_id == uuid.UUID(conversation_id)
    ).order_by(
        EmotionTimeline.timestamp
    ).all()
    
    return [entry.to_dict() for entry in timeline]

class PersonalityObservation(Base):  # noqa: F821
    """
    Raw OCEAN scores for a single video processed during a conversation.
    Linked to message_id, conversation_id, user_id for aggregation at session end.
    """
    __tablename__ = "personality_observations"
 
    id              = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id         = Column(UUID(as_uuid=True), nullable=False, index=True)
    conversation_id = Column(UUID(as_uuid=True), nullable=False, index=True)
    message_id      = Column(UUID(as_uuid=True), nullable=True,  index=True)
 
    openness          = Column(Float, nullable=False)
    conscientiousness = Column(Float, nullable=False)
    extraversion      = Column(Float, nullable=False)
    agreeableness     = Column(Float, nullable=False)
    neuroticism       = Column(Float, nullable=False)
 
    created_at = Column(DateTime, default=datetime.utcnow)
 
    def to_dict(self):
        return {
            "id":                str(self.id),
            "user_id":           str(self.user_id),
            "conversation_id":   str(self.conversation_id),
            "message_id":        str(self.message_id) if self.message_id else None,
            "openness":          self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion":      self.extraversion,
            "agreeableness":     self.agreeableness,
            "neuroticism":       self.neuroticism,
            "created_at":        self.created_at.isoformat() if self.created_at else None,
        }
 
    def ocean_dict(self):
        return {
            "openness":          self.openness,
            "conscientiousness": self.conscientiousness,
            "extraversion":      self.extraversion,
            "agreeableness":     self.agreeableness,
            "neuroticism":       self.neuroticism,
        }
 
class PersonalityProfile(Base):  # noqa: F821
    """
    Per-user running OCEAN personality profile stored in PostgreSQL.
    One row per user — upserted after each session completes.
    Replaces the previous JSON file approach.
    """
    __tablename__ = "personality_profiles"
 
    id                = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id           = Column(String(255), unique=True, nullable=False, index=True)
    sessions_complete = Column(Integer, default=0, nullable=False)
    profile           = Column(JSON, nullable=True)      # {"openness": 0.68, ...}
    session_history   = Column(JSON, default=list)       # [{session_id, timestamp, session_score}, ...]
    updated_at        = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_at        = Column(DateTime, default=datetime.utcnow)
 
    def to_dict(self):
        return {
            "id":                str(self.id),
            "user_id":           self.user_id,
            "sessions_complete": self.sessions_complete,
            "profile":           self.profile,
            "session_history":   self.session_history,
            "updated_at":        self.updated_at.isoformat() if self.updated_at else None,
        }
 
# ── Helper functions — add these alongside the existing helpers in database.py ─
 
def save_personality_observation(
    db,
    user_id:         str,
    conversation_id: str,
    ocean_scores:    dict,
    message_id:      str = None,
) -> "PersonalityObservation":
    obs = PersonalityObservation(
        user_id           = uuid.UUID(user_id),
        conversation_id   = uuid.UUID(conversation_id),
        message_id        = uuid.UUID(message_id) if message_id else None,
        openness          = ocean_scores.get("openness",          0.5),
        conscientiousness = ocean_scores.get("conscientiousness", 0.5),
        extraversion      = ocean_scores.get("extraversion",      0.5),
        agreeableness     = ocean_scores.get("agreeableness",     0.5),
        neuroticism       = ocean_scores.get("neuroticism",       0.5),
    )
    db.add(obs)
    db.commit()
    db.refresh(obs)
    return obs
 
 
def get_session_personality_observations(db, conversation_id: str) -> list:
    rows = (
        db.query(PersonalityObservation)
        .filter(PersonalityObservation.conversation_id == uuid.UUID(conversation_id))
        .order_by(PersonalityObservation.created_at)
        .all()
    )
    return [r.ocean_dict() for r in rows]