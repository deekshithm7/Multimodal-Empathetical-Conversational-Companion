from fastapi import APIRouter, Depends, HTTPException
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
    ).scalar_subquery()
    
    emotion_stats = db.query(
        EmotionTimeline.emotion,
        func.count(EmotionTimeline.id)
    ).filter(
        EmotionTimeline.conversation_id.in_(user_conversation_ids),
        EmotionTimeline.timestamp >= seven_days_ago
    ).group_by(EmotionTimeline.emotion).all()
    
    emotion_distribution = {e: c for e, c in emotion_stats}
    
    # 5. Emotion Timeline (Last 7 days daily for chart)
    # We want to group by Date and Emotion
    # Note: func.date() works in SQLite. For PostgreSQL use func.cast(timestamp, Date) or similar.
    # Assuming standard behavior or handling both might be tricky without dialect detection.
    # Let's try a safe approach: Fetch all recent data and aggregate in Python to avoid dialect issues.
    
    recent_emotions = db.query(EmotionTimeline).filter(
        EmotionTimeline.conversation_id.in_(user_conversation_ids),
        EmotionTimeline.timestamp >= seven_days_ago
    ).all()
    
    timeline_data = {} # { 'YYYY-MM-DD': {'happy': 0, 'sad': 0...} }
    
    for entry in recent_emotions:
        if not entry.timestamp:
            continue
        
        # Cross-database datetime handling
        if isinstance(entry.timestamp, str):
            try:
                dt = datetime.datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue
        else:
            dt = entry.timestamp
            
        date_str = dt.strftime('%b %d')
        if date_str not in timeline_data:
            timeline_data[date_str] = {}
        
        emotion = entry.emotion
        timeline_data[date_str][emotion] = timeline_data[date_str].get(emotion, 0) + 1
        
    # Convert to list for frontend
    formatted_timeline = []
    for date_str, counts in timeline_data.items():
        item = {'date': date_str}
        item.update(counts)
        formatted_timeline.append(item)
        
    # Sort by date
    formatted_timeline.sort(key=lambda x: x['date'])

    # 6. Recent Activity
    recent_convos = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(
        Conversation.started_at.desc()
    ).limit(3).all()

    return {
        "overview": {
            "total_conversations": total_conversations,
            "total_messages": total_messages,
            "average_duration_mins": 15
        },
        "emotion_distribution": emotion_distribution,
        "emotion_timeline": formatted_timeline,
        "recent_activity": [c.to_dict() for c in recent_convos]
    }

@router.get("/history")
async def get_history(
    limit: int = 20,
    offset: int = 0,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get manual conversation history list for History page"""
    conversations = db.query(Conversation).filter(
        Conversation.user_id == current_user.id
    ).order_by(
        Conversation.started_at.desc()
    ).offset(offset).limit(limit).all()
    
    total = db.query(Conversation).filter(Conversation.user_id == current_user.id).count()
    
    return {
        "total": total,
        "items": [c.to_dict() for c in conversations],
        "has_more": offset + len(conversations) < total
    }

@router.get("/session/{conversation_id}")
async def get_session_detail(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get full details of a specific session"""
    from uuid import UUID
    
    try:
        uuid_id = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    convo = db.query(Conversation).filter(
        Conversation.id == uuid_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not convo:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Get messages
    messages = db.query(Message).filter(
        Message.conversation_id == convo.id
    ).order_by(Message.created_at).all()
    
    # Get emotion timeline
    timeline = db.query(EmotionTimeline).filter(
        EmotionTimeline.conversation_id == convo.id
    ).order_by(EmotionTimeline.timestamp).all()
    
    return {
        "summary": convo.to_dict(),
        "messages": [m.to_dict() for m in messages],
        "emotion_timeline": [e.to_dict() for e in timeline]
    }

@router.delete("/session/{conversation_id}")
async def delete_session(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a session and all associated data"""
    from uuid import UUID
    
    try:
        uuid_id = UUID(conversation_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid session ID")

    convo = db.query(Conversation).filter(
        Conversation.id == uuid_id,
        Conversation.user_id == current_user.id
    ).first()
    
    if not convo:
        raise HTTPException(status_code=404, detail="Session not found")
        
    # Delete related messages and timeline entries
    # Cascading delete should handle this if configured, but let's be explicit or safe
    db.query(Message).filter(Message.conversation_id == convo.id).delete()
    db.query(EmotionTimeline).filter(EmotionTimeline.conversation_id == convo.id).delete()
    db.delete(convo)
    db.commit()
    
    return {"status": "success", "message": "Session deleted"}
