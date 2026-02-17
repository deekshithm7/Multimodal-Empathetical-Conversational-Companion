import sys
import os
import random
from datetime import datetime, timedelta
import uuid

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import init_db, SessionLocal, User, Conversation, Message, EmotionTimeline
from utils.auth import get_password_hash
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def seed_database():
    """Seed database with dummy user and conversation data"""
    db = SessionLocal()
    
    try:
        # 1. Initialize Tables
        init_db()
        
        # 2. Create Dummy User
        email = "demo@mecc.ai"
        existing_user = db.query(User).filter(User.email == email).first()
        
        if existing_user:
            logger.info(f"User {email} already exists. Skipping user creation.")
            user = existing_user
        else:
            logger.info(f"Creating user {email}...")
            user = User(
                email=email,
                name="Demo User",
                hashed_password=get_password_hash("demo123")
            )
            db.add(user)
            db.commit()
            db.refresh(user)
            logger.info(f"✅ Created user: {user.email} (ID: {user.id})")

        # 3. Create Sample Conversations
        logger.info("Creating sample conversations...")
        
        emotions = ['happy', 'sad', 'neutral', 'angry', 'calm', 'fearful', 'surprised']
        
        # Past 7 days
        for i in range(5):
            # Create Conversation
            start_time = datetime.utcnow() - timedelta(days=i, hours=random.randint(1, 5))
            duration_mins = random.randint(5, 30)
            end_time = start_time + timedelta(minutes=duration_mins)
            
            convo = Conversation(
                session_id=str(uuid.uuid4()),
                user_id=user.id,
                started_at=start_time,
                ended_at=end_time,
                status='completed',
                total_messages=random.randint(10, 50)
            )
            db.add(convo)
            db.commit()
            
            # Create timeline data (simulated)
            for j in range(convo.total_messages):
                # Simulated message time
                msg_time = start_time + timedelta(minutes=(j * duration_mins / convo.total_messages))
                
                # Random emotion flow
                emotion = random.choice(emotions)
                confidence = random.uniform(0.6, 0.99)
                
                timeline_entry = EmotionTimeline(
                    conversation_id=convo.id,
                    message_id=uuid.uuid4(), # Mock message ID since we aren't generating full texts
                    emotion=emotion,
                    confidence=confidence,
                    timestamp=msg_time
                )
                db.add(timeline_entry)
            
            db.commit()
            
        logger.info("✅ Database seeded successfully with dummy data!")
        
    except Exception as e:
        logger.error(f"❌ Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_database()
