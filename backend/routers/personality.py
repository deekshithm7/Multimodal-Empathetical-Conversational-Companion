"""
routers/personality.py

Personality profile endpoints.

GET  /api/v1/personality/profile  — full formatted profile (ready after 5 sessions)
GET  /api/v1/personality/status   — progress indicator (always available)
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db, User
from utils.auth import get_current_user
from services.personality_service import get_personality_service

router = APIRouter(prefix="/api/v1/personality", tags=["personality"])


@router.get("/profile")
async def get_personality_profile(
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """
    Returns the user's formatted OCEAN personality profile.
    - sessions_complete >= 5 → full profile with labels
    - sessions_complete < 5  → 404 with progress info
    """
    svc = get_personality_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Personality service not initialised")

    user_id = str(current_user.id)
    data    = svc.get_user_profile(user_id, db=db)

    if data is None:
        raise HTTPException(
            status_code=404,
            detail={
                "ready":             False,
                "sessions_complete": 0,
                "sessions_needed":   5,
                "message":           "No personality data yet. Complete some sessions first.",
            }
        )

    if not data["ready"]:
        sessions_needed = 5 - data["sessions_complete"]
        
        # We can format the temporary profile if it exists
        temp_profile = None
        if data.get("profile"):
            temp_profile = svc.format_for_display(data["profile"])

        raise HTTPException(
            status_code=202,
            detail={
                "ready":             False,
                "sessions_complete": data["sessions_complete"],
                "sessions_needed":   sessions_needed,
                "message":           f"Complete {sessions_needed} more session(s) to unlock your personality profile.",
                "session_history":   data.get("session_history", []),
                "profile":           temp_profile
            }
        )

    formatted = svc.format_for_display(data["profile"])

    return {
        "ready":             True,
        "sessions_complete": data["sessions_complete"],
        "profile":           formatted,
        "session_history":   data.get("session_history", [])
    }


@router.get("/status")
async def get_personality_status(
    current_user: User    = Depends(get_current_user),
    db:           Session = Depends(get_db),
):
    """
    Always returns progress — safe to poll for a frontend progress bar.
    """
    svc = get_personality_service()
    if svc is None:
        raise HTTPException(status_code=503, detail="Personality service not initialised")

    user_id = str(current_user.id)
    data    = svc.get_user_profile(user_id, db=db)

    sessions_complete = data["sessions_complete"] if data else 0
    sessions_needed   = max(0, 5 - sessions_complete)

    return {
        "sessions_complete": sessions_complete,
        "sessions_needed":   sessions_needed,
        "ready":             sessions_complete >= 5,
        "progress_pct":      min(100, int(sessions_complete / 5 * 100)),
    }