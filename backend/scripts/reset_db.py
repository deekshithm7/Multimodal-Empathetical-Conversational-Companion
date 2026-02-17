import sys
import os

# Add parent directory to path to import modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database import Base, engine, init_db
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def reset_database():
    """Drop all tables and recreate them"""
    logger.info("🗑️  Dropping all tables...")
    try:
        Base.metadata.drop_all(bind=engine)
        logger.info("✅ Tables dropped.")
        
        logger.info("✨ Creating new schema...")
        init_db()
        logger.info("✅ Database reset complete!")
        
    except Exception as e:
        logger.error(f"❌ Error resetting database: {e}")

if __name__ == "__main__":
    reset_database()
