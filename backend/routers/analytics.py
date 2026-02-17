from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from database import get_db, Conversation, EmotionTimeline, Message, User
from utils.auth import get_current_user
from typing import List, Dict
import datetime

router = APIRouter(
    prefix="/api/v1/analytics",
    tags=["Analytics"]
)

@router.get("/dashboard")
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # 1. Total Conversations
    total_conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).count()
    
    # 2. Total Messages
    # Join conversations to filter by user
    total_messages = db.query(func.sum(Conversation.total_messages)).filter(
        Conversation.user_id == current_user.id
    ).scalar() or 0
    
    # 3. Emotion Aggregate (Last 7 days)
    seven_days_ago = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    
    # Get all emotions from user's conversations
    # We need to join EmotionTimeline -> Message -> Conversation -> User
    # Or EmotionTimeline -> Conversation (since we assume we might link them, but ET has conversation_id)
    # Let's verify ET has conversation_id. Yes.
    
    # Check if we can filter ET by conversations belonging to user
    user_conversation_ids = db.query(Conversation.id).filter(
        Conversation.user_id == current_user.id
    ).subquery()
    
    emotion_stats = db.query(
        EmotionTimeline.emotion,
        func.count(EmotionTimeline.id)
    ).filter(
        EmotionTimeline.conversation_id.in_(user_conversation_ids),
        EmotionTimeline.timestamp >= seven_days_ago
    ).group_by(EmotionTimeline.emotion).all()
    
    emotion_distribution = {e: c for e, c in emotion_stats}
    
    # 4. Recent Activity (Last 5 conversations)
    recent_convos = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(Conversation.updated_at.desc()).limit(5).all()
    
    return {
        "overview": {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_duration_mins": 15 # Placeholder or calc
        },
        "emotion_distribution": emotion_distribution,
        "recent_activity": [c.to_dict() for c in recent_convos]
    }
