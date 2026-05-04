from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, User
from utils.auth import get_current_user, get_password_hash, verify_password

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    current_password: Optional[str] = None
    password: Optional[str] = None
    preferences: Optional[dict] = None

@router.get("/me")
async def read_users_me(current_user: User = Depends(get_current_user)):
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "preferences": current_user.preferences
    }

@router.put("/me")
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.name is not None:
        current_user.name = user_update.name
    
    if user_update.email is not None:
        # Check uniqueness if email is changing
        if user_update.email != current_user.email:
            existing = db.query(User).filter(User.email == user_update.email).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already taken")
            current_user.email = user_update.email
            
    if user_update.password:
        if not user_update.current_password:
            raise HTTPException(status_code=400, detail="Current password is required to set a new password")
        if not verify_password(user_update.current_password, current_user.hashed_password):
            raise HTTPException(status_code=400, detail="Incorrect current password")
        current_user.hashed_password = get_password_hash(user_update.password)
        
    if user_update.preferences is not None:
        # Update preferences (merge or replace? user_update.preferences is likely the full new state or partial)
        # For simplicity, let's treat it as a merge if it's a dict, or full replace. 
        # Actually standard PUT is full replace of the resource, but here it's a huge object. 
        # Let's assume the frontend sends the specific keys to update or the full object.
        # SQLAlchemy JSON type handles dicts.
        current_user.preferences = user_update.preferences
        
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name,
        "preferences": current_user.preferences
    }
