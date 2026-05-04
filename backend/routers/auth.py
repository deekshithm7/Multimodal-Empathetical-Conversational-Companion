from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User
from utils.auth import get_password_hash, verify_password, create_access_token, get_current_user
from datetime import timedelta, datetime
from typing import Optional
import secrets

router = APIRouter(
    prefix="/api/v1/auth",
    tags=["Authentication"]
)

# --- Pydantic Models ---
class UserCreate(BaseModel):
    email: str
    password: str
    name: Optional[str] = None

class Token(BaseModel):
    access_token: str
    token_type: str
    user_name: str
    user_email: str

class UserResponse(BaseModel):
    id: str
    email: str
    name: Optional[str]
    is_active: bool

class ForgotPasswordRequest(BaseModel):
    email: str

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str

# --- Endpoints ---

@router.post("/register", response_model=UserResponse)
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    # Check existing
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create user
    hashed_pw = get_password_hash(user_data.password)
    new_user = User(
        email=user_data.email,
        hashed_password=hashed_pw,
        name=user_data.name
    )
    
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    
    return new_user.to_dict()

@router.post("/token", response_model=Token)
async def login_for_access_token(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: Session = Depends(get_db)
):
    # Authenticate
    user = db.query(User).filter(User.email == form_data.username).first()
    if not user or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Generate Token
    access_token_expires = timedelta(minutes=60 * 24) # 24 hours
    access_token = create_access_token(
        data={"sub": user.email}, expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_name": user.name or "User",
        "user_email": user.email
    }

@router.get("/me", response_model=UserResponse)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user.to_dict()


@router.post("/forgot-password")
async def forgot_password(request: ForgotPasswordRequest, db: Session = Depends(get_db)):
    """Generate a password reset token. Returns token in response (no email configured)."""
    user = db.query(User).filter(User.email == request.email).first()
    
    # Always return success to avoid email enumeration, but only generate token if user exists
    if not user:
        return {
            "message": "If an account exists for this email, a reset link has been generated.",
            "token": None  # Don't reveal if user exists
        }
    
    # Generate a secure token valid for 30 minutes
    token = secrets.token_urlsafe(32)
    expiry = datetime.utcnow() + timedelta(minutes=30)
    
    # Store token in user's preferences dict (simple approach - no separate table needed)
    prefs = user.preferences or {}
    prefs["_reset_token"] = token
    prefs["_reset_expiry"] = expiry.isoformat()
    user.preferences = prefs
    db.commit()
    
    return {
        "message": "Password reset link generated. Use the token below to reset your password.",
        "token": token,  # In production, send via email instead
        "expires_in": "30 minutes",
        "reset_url": f"/reset-password?token={token}"
    }


@router.post("/reset-password")
async def reset_password(request: ResetPasswordRequest, db: Session = Depends(get_db)):
    """Reset password using a valid token."""
    if not request.token or len(request.new_password) < 8:
        raise HTTPException(status_code=400, detail="Invalid token or password too short (min 8 chars)")
    
    # Find user with this token
    users = db.query(User).all()
    target_user = None
    for u in users:
        prefs = u.preferences or {}
        if prefs.get("_reset_token") == request.token:
            target_user = u
            break
    
    if not target_user:
        raise HTTPException(status_code=400, detail="Invalid or expired reset token")
    
    # Check expiry
    prefs = target_user.preferences or {}
    expiry_str = prefs.get("_reset_expiry")
    if expiry_str:
        expiry = datetime.fromisoformat(expiry_str)
        if datetime.utcnow() > expiry:
            raise HTTPException(status_code=400, detail="Reset token has expired. Please request a new one.")
    
    # Update password
    target_user.hashed_password = get_password_hash(request.new_password)
    # Clear the reset token
    prefs.pop("_reset_token", None)
    prefs.pop("_reset_expiry", None)
    target_user.preferences = prefs
    db.commit()
    
    return {"message": "Password reset successfully. You can now log in with your new password."}
