"""
services/personality_service.py

Personality prediction service — OCEAN trait inference + profile management.

Architecture:
  - TransformerFusion imported from models/personality_model.py
  - All profile data stored in PostgreSQL (PersonalityProfile table)
  - No JSON files on disk
  - EMA update: profile = 0.3 * session_score + 0.7 * old_profile
  - Profile only "ready" after sessions_complete >= 5
"""

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

import numpy as np
import torch

from models.personality_model import TransformerFusion

logger = logging.getLogger(__name__)

TRAIT_KEYS         = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]
DEVICE             = "cuda" if torch.cuda.is_available() else "cpu"
EMA_ALPHA          = 0.3
MIN_SESSIONS_READY = 5


class PersonalityService:
    """
    Singleton service for personality prediction + PostgreSQL profile management.
    """

    def __init__(self, model_path: str, config_path: str):
        logger.info(f"Loading PersonalityService model from {model_path}...")

        with open(config_path) as f:
            cfg = json.load(f)

        self.model = TransformerFusion(
            proj_dim  = cfg.get("proj_dim",   256),
            num_heads = cfg.get("num_heads",    8),
            ff_dim    = cfg.get("ff_dim",     512),
            num_layers= cfg.get("num_layers",   3),
            dropout   = cfg.get("dropout",    0.3),
        ).to(DEVICE)

        ckpt  = torch.load(model_path, map_location=DEVICE, weights_only=False)
        state = ckpt.get("model_state_dict", ckpt)
        self.model.load_state_dict(state)
        self.model.eval()

        logger.info(f"✅ PersonalityService ready (epoch {ckpt.get('epoch', '?')})")

    # ── Core prediction ────────────────────────────────────────────────────────

    def predict_from_features(
        self,
        audio_feat:  Optional[np.ndarray],
        text_feat:   Optional[np.ndarray],
        visual_feat: Optional[np.ndarray],
    ) -> Dict[str, float]:
        """
        Run personality prediction from pre-extracted raw embeddings.
        Falls back to running model on zeros if any modality is None.
        Never raises — returns valid OCEAN dict always.
        """
        try:
            def to_tensor(arr, dim):
                if arr is None:
                    arr = np.zeros(dim, dtype=np.float32)
                return torch.from_numpy(np.array(arr, dtype=np.float32)).unsqueeze(0).to(DEVICE)

            a = to_tensor(audio_feat,  768)
            t = to_tensor(text_feat,   768)
            v = to_tensor(visual_feat, 2048)

            with torch.no_grad():
                preds = self.model(a, t, v)

            return {trait: float(preds[0, i]) for i, trait in enumerate(TRAIT_KEYS)}

        except Exception as e:
            logger.error(f"Personality prediction failed: {e}", exc_info=True)
            return {t: 0.5 for t in TRAIT_KEYS}

    # ── DB profile helpers ─────────────────────────────────────────────────────

    def _load_profile(self, user_id: str, db) -> dict:
        """Load profile from PostgreSQL. Returns empty profile dict if not found."""
        from database import PersonalityProfile
        row = db.query(PersonalityProfile).filter(
            PersonalityProfile.user_id == user_id
        ).first()
        if row:
            return {
                "user_id":           user_id,
                "sessions_complete": row.sessions_complete,
                "profile":           row.profile,
                "session_history":   row.session_history or [],
            }
        return {
            "user_id":           user_id,
            "sessions_complete": 0,
            "profile":           None,
            "session_history":   [],
        }

    def _save_profile(self, data: dict, db):
        """Upsert profile into PostgreSQL."""
        from database import PersonalityProfile
        row = db.query(PersonalityProfile).filter(
            PersonalityProfile.user_id == data["user_id"]
        ).first()
        if row:
            row.sessions_complete = data["sessions_complete"]
            row.profile           = data["profile"]
            row.session_history   = data["session_history"]
            row.updated_at        = datetime.utcnow()
        else:
            row = PersonalityProfile(
                user_id          = data["user_id"],
                sessions_complete= data["sessions_complete"],
                profile          = data["profile"],
                session_history  = data["session_history"],
            )
            db.add(row)
        db.commit()

    # ── Session / profile management ───────────────────────────────────────────

    def add_session_result(
        self,
        user_id:      str,
        session_id:   str,
        video_scores: List[Dict[str, float]],
        db=None,
    ) -> dict:
        """
        Average per-video OCEAN scores for this session, then EMA-update
        the user's running profile in PostgreSQL.
        """
        if db is None:
            raise ValueError("db session required for add_session_result")

        if not video_scores:
            data = self._load_profile(user_id, db)
            return {
                "profile":           data.get("profile"),
                "sessions_complete": data.get("sessions_complete", 0),
                "ready":             data.get("sessions_complete", 0) >= MIN_SESSIONS_READY,
            }

        # 1. Mean-average video scores → session_score
        session_score = {}
        for trait in TRAIT_KEYS:
            vals = [s[trait] for s in video_scores if trait in s]
            session_score[trait] = float(np.mean(vals)) if vals else 0.5

        # 2. Load existing profile
        data        = self._load_profile(user_id, db)
        old_profile = data.get("profile")

        # 3. EMA update
        if old_profile is None:
            new_profile = session_score
        else:
            new_profile = {
                trait: EMA_ALPHA * session_score[trait] + (1 - EMA_ALPHA) * old_profile[trait]
                for trait in TRAIT_KEYS
            }

        # 4. Update data
        data["sessions_complete"] = data.get("sessions_complete", 0) + 1
        data["profile"]           = new_profile
        data.setdefault("session_history", []).append({
            "session_id":    session_id,
            "timestamp":     datetime.utcnow().isoformat(),
            "session_score": session_score,
        })

        # 5. Save to DB
        self._save_profile(data, db)

        return {
            "profile":           new_profile,
            "sessions_complete": data["sessions_complete"],
            "ready":             data["sessions_complete"] >= MIN_SESSIONS_READY,
        }

    def get_user_profile(self, user_id: str, db=None) -> Optional[dict]:
        """
        Returns the user's personality profile dict, or None if no data.
        """
        if db is None:
            raise ValueError("db session required for get_user_profile")

        data = self._load_profile(user_id, db)
        if data.get("sessions_complete", 0) == 0:
            return None
        return {
            "profile":           data.get("profile"),
            "sessions_complete": data.get("sessions_complete", 0),
            "ready":             data.get("sessions_complete", 0) >= MIN_SESSIONS_READY,
            "session_history":   data.get("session_history", []),
        }

    def format_for_display(self, profile: Dict[str, float]) -> Dict[str, dict]:
        """Convert raw [0,1] scores to human-readable labels."""
        out = {}
        for trait in TRAIT_KEYS:
            score = profile.get(trait, 0.5)
            if score > 0.65:
                label = "High"
            elif score >= 0.40:
                label = "Moderate"
            else:
                label = "Low"
            out[trait] = {"score": round(score, 4), "label": label}
        return out


# ── Singleton ──────────────────────────────────────────────────────────────────
_personality_service_instance: Optional[PersonalityService] = None


def get_personality_service() -> Optional[PersonalityService]:
    return _personality_service_instance


def init_personality_service(model_path: str, config_path: str) -> PersonalityService:
    global _personality_service_instance
    if _personality_service_instance is None:
        _personality_service_instance = PersonalityService(model_path, config_path)
    return _personality_service_instance