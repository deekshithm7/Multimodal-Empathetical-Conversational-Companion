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
    timeframe: str = "4weeks",
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
    
    # 3. Emotion window — driven by timeframe param
    now = datetime.datetime.utcnow()
    if timeframe == "all":
        cutoff = None
    elif timeframe == "6months":
        cutoff = now - datetime.timedelta(days=180)
    else:  # default: 4weeks
        cutoff = now - datetime.timedelta(days=28)

    # Get all emotions from user's conversations
    user_conversation_ids = db.query(Conversation.id).filter(
        Conversation.user_id == current_user.id
    ).scalar_subquery()

    timeline_filter = [EmotionTimeline.conversation_id.in_(user_conversation_ids)]
    if cutoff:
        timeline_filter.append(EmotionTimeline.timestamp >= cutoff)

    emotion_stats = db.query(
        EmotionTimeline.emotion,
        func.count(EmotionTimeline.id)
    ).filter(*timeline_filter).group_by(EmotionTimeline.emotion).all()

    emotion_distribution = {e: c for e, c in emotion_stats}

    # 5. Emotion Timeline chart — aggregate by day, sort by real date
    recent_emotions = db.query(EmotionTimeline).filter(*timeline_filter).all()

    timeline_data = {}  # { datetime.date: {'happy': 0, ...} }

    for entry in recent_emotions:
        if not entry.timestamp:
            continue
        if isinstance(entry.timestamp, str):
            try:
                dt = datetime.datetime.fromisoformat(entry.timestamp.replace("Z", "+00:00"))
            except ValueError:
                continue
        else:
            dt = entry.timestamp

        day = dt.date()  # real date object — sorts correctly
        if day not in timeline_data:
            timeline_data[day] = {}
        emotion = entry.emotion
        timeline_data[day][emotion] = timeline_data[day].get(emotion, 0) + 1

    # Sort by real date ascending, then format label
    formatted_timeline = []
    for day in sorted(timeline_data.keys()):
        item = {'date': day.strftime('%b %d')}
        item.update(timeline_data[day])
        formatted_timeline.append(item)

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
