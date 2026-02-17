from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from typing import Optional
from database import get_db, User
from utils.auth import get_current_user, get_password_hash

router = APIRouter(
    prefix="/api/v1/users",
    tags=["Users"]
)

class UserUpdate(BaseModel):
    name: Optional[str] = None
    email: Optional[str] = None
    password: Optional[str] = None

@router.put("/me")
async def update_user_me(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    if user_update.name:
        current_user.name = user_update.name
    
    if user_update.email:
        # Check uniqueness
        if user_update.email != current_user.email:
            existing = db.query(User).filter(User.email == user_update.email).first()
            if existing:
                raise HTTPException(status_code=400, detail="Email already taken")
            current_user.email = user_update.email
            
    if user_update.password:
        current_user.hashed_password = get_password_hash(user_update.password)
        
    db.commit()
    db.refresh(current_user)
    
    return {
        "id": str(current_user.id),
        "email": current_user.email,
        "name": current_user.name
    }
