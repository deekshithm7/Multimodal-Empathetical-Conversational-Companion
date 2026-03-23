"""
Conversation Service - Main Business Logic Orchestrator (THE BOSS 👑)

Changes vs previous version:
  - Emotion feature extraction now uses EmotionFeatureService
    (WavLM-Base+, RoBERTa-large, ResNet50+proj256 — sequence outputs)
    instead of the shared FeatureService.
  - predict_from_features() now receives all 3 modalities.
  - Personality pipeline (via FeatureService) is completely untouched.
"""

import logging
import os
import uuid
import shutil
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class ConversationService:

    def __init__(self):
        self._transcription           = None
        self._emotion_feature_service = None   # NEW — emotion-specific extractor
        self._feature_service         = None   # KEPT — personality pipeline only
        self._emotion                 = None
        self._llm                     = None
        self._tts                     = None
        logger.info("ConversationService initialized")

    # ── lazy service properties ───────────────────────────────────────────────

    @property
    def transcription(self):
        if self._transcription is None:
            from services.transcription_service import get_whisper_service
            self._transcription = get_whisper_service()
            logger.info("Transcription service loaded")
        return self._transcription

    @property
    def emotion_feature_service(self):
        """Emotion-specific feature extractor (WavLM-Base+, RoBERTa-large, ResNet50+proj256)."""
        if self._emotion_feature_service is None:
            from services.emotion_feature_service import get_emotion_feature_service
            self._emotion_feature_service = get_emotion_feature_service()
            logger.info("EmotionFeatureService loaded")
        return self._emotion_feature_service

    @property
    def feature_service(self):
        """Shared feature extractor — used by personality pipeline only."""
        if self._feature_service is None:
            from services.feature_service import get_feature_service
            self._feature_service = get_feature_service()
            logger.info("FeatureService (personality) loaded")
        return self._feature_service

    @property
    def emotion(self):
        if self._emotion is None:
            from services.emotion_service import get_emotion_service
            self._emotion = get_emotion_service()
            logger.info("Emotion service loaded")
        return self._emotion

    @property
    def llm(self):
        if self._llm is None:
            from services.llm_service import get_free_llm_service
            self._llm = get_free_llm_service()
            logger.info("LLM service loaded")
        return self._llm

    @property
    def tts(self):
        if self._tts is None:
            from services.tts_service import get_free_tts_service
            self._tts = get_free_tts_service()
            logger.info("TTS service loaded")
        return self._tts

    # ── main processing pipeline ──────────────────────────────────────────────

    def process_message(
        self,
        conversation_id: str,
        audio_path:      Optional[str] = None,
        text:            Optional[str] = None,
        db_session=None,
    ) -> Dict:
        logger.info(f"📨 Processing message for conversation {conversation_id}")

        try:
            # ── Step 1: Transcription ──────────────────────────────────────────
            if audio_path and not text:
                logger.info("🎙️ Step 1: Transcribing audio…")
                transcription_result = self.transcription.transcribe(audio_path)
                text = transcription_result["text"]
                logger.info(f"✅ Transcribed: '{text}'")
            elif not text:
                raise ValueError("No text or audio provided")

            # ── Step 2: Emotion feature extraction (ET-TACFN pipeline) ────────
            #
            # EmotionFeatureService uses:
            #   WavLM-Base+   → audio  [T_a, 1024]
            #   RoBERTa-large → text   [128, 1024]
            #   ResNet50+256  → visual [30,  256]
            #
            # visual is only extracted when a video file is available.
            # For audio-only messages visual will be None — the model's
            # MissingModalityHandler handles this gracefully.
            logger.info("🎨 Step 2: Extracting emotion features (ET-TACFN pipeline)…")
            emotion_features = self.emotion_feature_service.extract_parallel(
                audio_path = audio_path,
                text       = text,
                video_path = audio_path,   # same file — works for webm/mp4/wav
                                           # VisualEncoder falls back to zeros for pure audio
            )
            logger.info(
                f"✅ Emotion features — "
                f"audio: {emotion_features['audio'].shape if emotion_features['audio'] is not None else None}, "
                f"text: {emotion_features['text'].shape   if emotion_features['text']  is not None else None}, "
                f"visual: {emotion_features['visual'].shape if emotion_features['visual'] is not None else None}"
            )

            # ── Step 3: Predict emotion ────────────────────────────────────────
            logger.info("😊 Step 3: Predicting emotion (ET-TACFN)…")
            emotion_result = self.emotion.predict_from_features(
                audio_features  = emotion_features["audio"],
                text_features   = emotion_features["text"],
                visual_features = emotion_features["visual"],   # may be None — handled
            )
            logger.info(
                f"✅ Emotion: {emotion_result['emotion']} "
                f"({emotion_result['confidence']:.2%})"
            )

            # ── Step 4: Conversation history ───────────────────────────────────
            logger.info("📚 Step 4: Retrieving conversation history…")
            from database import get_conversation_history
            history = get_conversation_history(db_session, conversation_id, limit=30)
            logger.info(f"✅ Retrieved {len(history)} previous messages")

            # ── Step 5: LLM response ───────────────────────────────────────────
            logger.info("🤖 Step 5: Generating LLM response…")
            response_text = self.llm.generate_empathetic_response(
                user_message         = text,
                detected_emotion     = emotion_result["emotion"],
                emotion_confidence   = emotion_result["confidence"],
                conversation_history = history,
            )
            logger.info(f"✅ Generated response: '{response_text[:50]}…'")

            # ── Step 6: TTS ────────────────────────────────────────────────────
            logger.info("🔊 Step 6: Synthesizing speech…")
            tts_audio_path = self.tts.generate_speech(
                text    = response_text,
                emotion = emotion_result["emotion"],
            )
            logger.info(f"✅ Audio generated: {tts_audio_path}")

            # ── Step 7: Persist to database ────────────────────────────────────
            logger.info("💾 Step 7: Saving to database…")
            from database import save_message

            user_message = save_message(
                db_session,
                conversation_id = conversation_id,
                role            = "user",
                content         = text,
                emotion_data    = {
                    "emotion":    emotion_result["emotion"],
                    "confidence": emotion_result["confidence"],
                },
            )

            AUDIO_STORAGE_DIR = os.environ.get("AUDIO_STORAGE_DIR", "./audio_storage")
            os.makedirs(AUDIO_STORAGE_DIR, exist_ok=True)

            assistant_filename    = f"{conversation_id}_{uuid.uuid4()}.wav"
            assistant_stored_path = os.path.join(AUDIO_STORAGE_DIR, assistant_filename)
            shutil.copy(tts_audio_path, assistant_stored_path)

            save_message(
                db_session,
                conversation_id = conversation_id,
                role            = "assistant",
                content         = response_text,
                audio_data      = {"path": assistant_stored_path, "duration": 5.0},
            )
            logger.info("✅ Messages saved to database")

            # Cleanup temp TTS file
            keep_audio = os.environ.get("KEEP_AUDIO", "false").lower() == "true"
            if not keep_audio:
                try:
                    if os.path.exists(tts_audio_path):
                        os.unlink(tts_audio_path)
                        logger.info("🗑️ Deleted temp TTS file (KEEP_AUDIO=false)")
                except Exception as e:
                    logger.warning(f"Failed to delete temp TTS file: {e}")
            else:
                logger.info("📁 KEEP_AUDIO=true — audio files retained")

            logger.info("✅ Message processing complete!")

            return {
                "status":              "success",
                "user_message":        text,
                "user_emotion":        {
                    "emotion":    emotion_result["emotion"],
                    "confidence": emotion_result["confidence"],
                },
                "assistant_response":  response_text,
                "assistant_audio_url": f"/api/v1/audio/{assistant_filename}",
                "message_id":          str(user_message.id),
            }

        except Exception as e:
            logger.error(f"❌ Error processing message: {str(e)}", exc_info=True)
            return {
                "status":              "error",
                "error":               str(e),
                "user_message":        text or "",
                "user_emotion":        None,
                "assistant_response":  None,
                "assistant_audio_url": None,
                "message_id":          None,
            }


# ─────────────────────────────────────────────────────────────────────────────
# Singleton
# ─────────────────────────────────────────────────────────────────────────────

_conversation_service_instance = None


def get_conversation_service() -> ConversationService:
    global _conversation_service_instance
    if _conversation_service_instance is None:
        _conversation_service_instance = ConversationService()
        logger.info("Created ConversationService singleton")
    return _conversation_service_instance