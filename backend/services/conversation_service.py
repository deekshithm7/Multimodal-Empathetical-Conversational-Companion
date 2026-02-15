"""
Conversation Service - Main Business Logic Orchestrator (THE BOSS 👑)

This service orchestrates the entire conversation processing pipeline:
1. Transcription (audio → text)
2. Feature extraction (multimodal)
3. Emotion prediction
4. [Future] Personality prediction
5. LLM response generation
6. TTS synthesis
7. Database persistence

This is the "boss" that coordinates all other services.
app.py delegates to this service for all business logic.
"""

import logging
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversationService:
    """
    Main orchestrator for conversation processing.
    
    Coordinates all services to process a user message and generate a response.
    """
    
    def __init__(self):
        """Initialize conversation service (services loaded lazily)."""
        self._transcription = None
        self._feature_service = None
        self._emotion = None
        self._llm = None
        self._tts = None
        logger.info("ConversationService initialized")
    
    @property
    def transcription(self):
        """Lazy load transcription service."""
        if self._transcription is None:
            from services.transcription_service import get_whisper_service
            self._transcription = get_whisper_service()
            logger.info("Transcription service loaded")
        return self._transcription
    
    @property
    def feature_service(self):
        """Lazy load feature service."""
        if self._feature_service is None:
            from services.feature_service import get_feature_service
            self._feature_service = get_feature_service()
            logger.info("Feature service loaded")
        return self._feature_service
    
    @property
    def emotion(self):
        """Lazy load emotion service."""
        if self._emotion is None:
            from services.emotion_service import get_emotion_service
            self._emotion = get_emotion_service()
            logger.info("Emotion service loaded")
        return self._emotion
    
    @property
    def llm(self):
        """Lazy load LLM service."""
        if self._llm is None:
            from services.llm_service import get_free_llm_service
            self._llm = get_free_llm_service()
            logger.info("LLM service loaded")
        return self._llm
    
    @property
    def tts(self):
        """Lazy load TTS service."""
        if self._tts is None:
            from services.tts_service import get_free_tts_service
            self._tts = get_free_tts_service()
            logger.info("TTS service loaded")
        return self._tts
    
    def process_message(
        self,
        conversation_id: str,
        audio_path: Optional[str] = None,
        text: Optional[str] = None,
        db_session = None
    ) -> Dict:
        """
        Process a user message through the complete pipeline.
        
        This is the MAIN ORCHESTRATION METHOD that coordinates all services.
        
        Args:
            conversation_id: Unique conversation ID
            audio_path: Path to audio/video file (optional)
            text: User text message (optional)
            db_session: Database session for persistence
        
        Returns:
            Dictionary with:
            - 'status': 'success' or 'error'
            - 'user_message': Transcribed/provided text
            - 'user_emotion': Detected emotion result
            - 'assistant_response': Generated response text
            - 'assistant_audio_url': URL to TTS audio
        """
        logger.info(f"📨 Processing message for conversation {conversation_id}")
        
        try:
            # Step 1: Transcription (if audio provided and no text)
            if audio_path and not text:
                logger.info("🎙️ Step 1: Transcribing audio...")
                transcription_result = self.transcription.transcribe(audio_path)
                text = transcription_result['text']
                logger.info(f"✅ Transcribed: '{text}'")
            elif not text:
                raise ValueError("No text or audio provided")
            
            # Step 2: Extract multimodal features (ONCE!)
            logger.info("🎨 Step 2: Extracting multimodal features...")
            if not hasattr(self, '_feature_service') or self._feature_service is None:
                from services.feature_service import get_feature_service
                self._feature_service = get_feature_service()
                logger.info("Feature service loaded")
            
            # Extract features using the centralized service
            features_result = self._feature_service.extract_and_stack_features(
                audio_path=audio_path,
                text=text,
                use_audio=True,
                use_text=True,
                use_visual=False  # Not needed for emotion detection
            )
            
            # Get individual features
            features = {
                'audio': features_result['audio'],
                'text': features_result['text']
            }
            logger.info(f"✅ Extracted features: audio={features['audio'].shape}, text={features['text'].shape}")
            
            # Step 3: Predict emotion from pre-extracted features
            logger.info("😊 Step 3: Predicting emotion from features...")
            
            # Use the NEW predict_from_features method
            emotion_result = self.emotion.predict_from_features(
                audio_features=features['audio'],
                text_features=features['text']
            )
            logger.info(f"✅ Emotion detected: {emotion_result['emotion']} ({emotion_result['confidence']:.2%})")
            
            # Step 4: Get conversation history
            logger.info("📚 Step 4: Retrieving conversation history...")
            from database import get_conversation_history
            history = get_conversation_history(db_session, conversation_id, limit=30)
            logger.info(f"✅ Retrieved {len(history)} previous messages")
            
            # Step 5: Generate empathetic response
            logger.info("🤖 Step 5: Generating LLM response...")
            response_text = self.llm.generate_empathetic_response(
                user_message=text,
                detected_emotion=emotion_result['emotion'],
                emotion_confidence=emotion_result['confidence'],
                conversation_history=history
            )
            logger.info(f"✅ Generated response: '{response_text[:50]}...'")
            
            # Step 6: Synthesize speech
            logger.info("🔊 Step 6: Synthesizing speech...")
            if not hasattr(self, '_tts_service'):
                self._tts_service = self.tts
                logger.info("TTS service loaded")
            
            audio_path = self.tts.generate_speech(
                text=response_text,
                emotion=emotion_result['emotion']
            )
            logger.info(f"✅ Audio generated: {audio_path}")
            
            # Step 7: Save to database
            logger.info("💾 Step 7: Saving to database...")
            from database import save_message
            
            # Save user message
            save_message(
                db_session,
                conversation_id=conversation_id,
                role='user',
                content=text,
                emotion_data={
                    'emotion': emotion_result['emotion'],
                    'confidence': emotion_result['confidence']
                }
            )
            
            # Save assistant message with audio
            import os
            import uuid
            import shutil
            
            # Get audio storage directory
            AUDIO_STORAGE_DIR = os.environ.get('AUDIO_STORAGE_DIR', './audio_storage')
            os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)
            
            # Copy audio to storage
            assistant_filename = f"{conversation_id}_{uuid.uuid4()}.wav"
            assistant_stored_path = os.path.join(AUDIO_STORAGE_DIR, assistant_filename)
            shutil.copy(audio_path, assistant_stored_path)
            
            save_message(
                db_session,
                conversation_id=conversation_id,
                role='assistant',
                content=response_text,
                audio_data={'path': assistant_stored_path, 'duration': 5.0}
            )
            logger.info("✅ Messages saved to database")
            
            # Cleanup audio files (unless KEEP_AUDIO=true for debugging)
            import os as cleanup_os
            keep_audio = cleanup_os.environ.get('KEEP_AUDIO', 'false').lower() == 'true'
            
            if not keep_audio:
                # Delete user audio file after processing
                try:
                    if cleanup_os.path.exists(audio_path):
                        cleanup_os.unlink(audio_path)
                        logger.info(f"🗑️ Deleted user audio (KEEP_AUDIO=false)")
                except Exception as e:
                    logger.warning(f"Failed to delete user audio: {e}")
            else:
                logger.info("📁 KEEP_AUDIO=true, audio files retained")
            
            logger.info("✅ Message processing complete!")
            
            # Step 8: Return complete result
            result = {
                'status': 'success',
                'user_message': text,
                'user_emotion': {
                    'emotion': emotion_result['emotion'],
                    'confidence': emotion_result['confidence']
                },
                'assistant_response': response_text,
                'assistant_audio_url': f"/api/v1/audio/{assistant_filename}"
            }
            
            logger.info("✅ Message processing complete!")
            return result
            
        except Exception as e:
            logger.error(f"❌ Error processing message: {str(e)}", exc_info=True)
            return {
                'status': 'error',
                'error': str(e),
                'user_message': text or '',
                'user_emotion': None,
                'assistant_response': None,
                'assistant_audio_url': None
            }


# Singleton instance
_conversation_service_instance = None


def get_conversation_service() -> ConversationService:
    """
    Get or create the global conversation service instance (singleton).
    
    Returns:
        ConversationService instance
    """
    global _conversation_service_instance
    
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService()
        logger.info("Created ConversationService singleton")
    
    return _conversation_service_instance
