from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import get_db, User
from utils.auth import get_password_hash, verify_password, create_access_token, get_current_user
from datetime import timedelta
from typing import Optional

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
