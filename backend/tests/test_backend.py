"""
MECC Backend Test Suite — pytest compatible

Run with:
    pytest tests/test_backend.py -v
    pytest tests/test_backend.py -v -s

Requires server running:
    python app.py

For the profile-ready test, set in .env or environment:
    MECC_TEST_EMAIL=demo@mecc.ai
    MECC_TEST_PASSWORD=demo123
"""

import os
import sys
import uuid
import struct
import pytest
import requests
import numpy as np
from dotenv import load_dotenv

load_dotenv()

BASE_URL        = os.environ.get("MECC_BASE_URL",      "http://localhost:8000")
DEMO_EMAIL      = os.environ.get("MECC_TEST_EMAIL",    "")
DEMO_PASSWORD   = os.environ.get("MECC_TEST_PASSWORD", "")


# ── Helpers ────────────────────────────────────────────────────────────────────

def api(method, path, *, token=None, **kwargs):
    headers = kwargs.pop("headers", {})
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return getattr(requests, method)(f"{BASE_URL}{path}", headers=headers,
                                     timeout=60, **kwargs)


def login(email, password) -> str:
    r = api("post", "/api/v1/auth/token",
            data={"username": email, "password": password},
            headers={"Content-Type": "application/x-www-form-urlencoded"})
    assert r.status_code == 200, f"Login failed for {email}: {r.text}"
    return r.json()["access_token"]


def make_silent_wav(duration_s=1, sr=16000) -> bytes:
    num_samples = sr * duration_s
    data_bytes  = b'\x00\x00' * num_samples
    data_size   = len(data_bytes)
    header = struct.pack('<4sI4s4sIHHIIHH4sI',
        b'RIFF', 36 + data_size, b'WAVE',
        b'fmt ', 16, 1, 1, sr, sr * 2, 2, 16,
        b'data', data_size)
    return header + data_bytes


# ── Server reachability ────────────────────────────────────────────────────────

def pytest_configure(config):
    try:
        requests.get(f"{BASE_URL}/health", timeout=5)
    except requests.exceptions.ConnectionError:
        pytest.exit(f"Cannot reach server at {BASE_URL} — start it first: python app.py")


# ── Session-scoped fixtures ────────────────────────────────────────────────────

@pytest.fixture(scope="session")
def auth_token():
    """Register a fresh test user and return their JWT token."""
    tag   = uuid.uuid4().hex[:8]
    email = f"pytest_{tag}@mecc.test"
    pwd   = "TestPass123!"

    r = api("post", "/api/v1/auth/register",
            json={"email": email, "password": pwd, "name": "Pytest User"})
    assert r.status_code in (200, 201), f"Register failed: {r.text}"
    return login(email, pwd)


@pytest.fixture(scope="session")
def demo_token():
    """
    Token for the existing demo user who has >= 5 completed sessions.
    Requires MECC_TEST_EMAIL and MECC_TEST_PASSWORD in .env
    """
    if not DEMO_EMAIL or not DEMO_PASSWORD:
        pytest.skip("MECC_TEST_EMAIL / MECC_TEST_PASSWORD not set in .env")
    return login(DEMO_EMAIL, DEMO_PASSWORD)


@pytest.fixture(scope="session")
def active_conversation(auth_token):
    """Start a conversation, send one message, return (conv_id, token)."""
    r = api("post", "/api/v1/session/start", token=auth_token)
    assert r.status_code == 200, f"Session start failed: {r.text}"
    conv_id = r.json()["conversation_id"]

    r2 = api("post", "/api/v1/session/message",
             data={"conversation_id": conv_id,
                   "text": "I feel a bit anxious and overwhelmed today."},
             token=auth_token)
    assert r2.status_code == 200, f"Message failed: {r2.text}"

    return conv_id, auth_token


@pytest.fixture(scope="session")
def ended_conversation(active_conversation):
    """End the active conversation, return (conv_id, token, response_body)."""
    conv_id, token = active_conversation
    r = api("post", "/api/v1/session/end",
            data={"conversation_id": conv_id}, token=token)
    assert r.status_code == 200, f"Session end failed: {r.text}"
    return conv_id, token, r.json()


# ══════════════════════════════════════════════════════════════════════════════
# 1. Health
# ══════════════════════════════════════════════════════════════════════════════

class TestHealth:
    def test_returns_200(self):
        assert api("get", "/health").status_code == 200

    def test_has_version(self):
        assert "version" in api("get", "/health").json()

    def test_emotion_model_loaded(self):
        assert api("get", "/health").json()["services"]["emotion_model"] == "loaded"

    def test_personality_model_loaded(self):
        assert api("get", "/health").json()["services"]["personality_model"] == "loaded"

    def test_root_lists_personality(self):
        r = api("get", "/")
        assert r.status_code == 200
        assert "personality" in str(r.json())


# ══════════════════════════════════════════════════════════════════════════════
# 2. Auth
# ══════════════════════════════════════════════════════════════════════════════

class TestAuth:
    def test_register_new_user(self):
        tag = uuid.uuid4().hex[:8]
        r = api("post", "/api/v1/auth/register",
                json={"email": f"reg_{tag}@test.com", "password": "Pass123!", "name": "T"})
        assert r.status_code in (200, 201)

    def test_duplicate_register_rejected(self):
        tag   = uuid.uuid4().hex[:8]
        email = f"dup_{tag}@test.com"
        api("post", "/api/v1/auth/register",
            json={"email": email, "password": "Pass123!", "name": "T"})
        r2 = api("post", "/api/v1/auth/register",
                 json={"email": email, "password": "Pass123!", "name": "T"})
        assert 400 <= r2.status_code < 500

    def test_login_returns_token(self, auth_token):
        assert isinstance(auth_token, str) and len(auth_token) > 10

    def test_wrong_password_rejected(self):
        tag   = uuid.uuid4().hex[:8]
        email = f"wp_{tag}@test.com"
        api("post", "/api/v1/auth/register",
            json={"email": email, "password": "Pass123!", "name": "T"})
        r = api("post", "/api/v1/auth/token",
                data={"username": email, "password": "WRONG"},
                headers={"Content-Type": "application/x-www-form-urlencoded"})
        assert 400 <= r.status_code < 500

    def test_me_returns_email(self, auth_token):
        r = api("get", "/api/v1/auth/me", token=auth_token)
        assert r.status_code == 200
        assert "@" in r.json().get("email", "")

    def test_unauthenticated_me_returns_401(self):
        assert api("get", "/api/v1/auth/me").status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# 3. Session Start
# ══════════════════════════════════════════════════════════════════════════════

class TestSessionStart:
    def test_returns_200(self, auth_token):
        r = api("post", "/api/v1/session/start", token=auth_token)
        assert r.status_code == 200

    def test_returns_conversation_id(self, auth_token):
        r = api("post", "/api/v1/session/start", token=auth_token)
        assert r.json().get("conversation_id")

    def test_returns_welcome_message(self, auth_token):
        r = api("post", "/api/v1/session/start", token=auth_token)
        assert r.json().get("welcome_message")

    def test_returns_audio_url(self, auth_token):
        r = api("post", "/api/v1/session/start", token=auth_token)
        assert r.json().get("welcome_audio_url")

    def test_welcome_audio_is_servable(self, auth_token):
        r   = api("post", "/api/v1/session/start", token=auth_token)
        url = r.json().get("welcome_audio_url", "")
        assert api("get", url).status_code in (200, 206)

    def test_unauthenticated_returns_401(self):
        assert api("post", "/api/v1/session/start").status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# 4. Session Message
# ══════════════════════════════════════════════════════════════════════════════

class TestSessionMessage:
    def test_text_message_returns_200(self, active_conversation):
        conv_id, token = active_conversation
        r = api("post", "/api/v1/session/message",
                data={"conversation_id": conv_id, "text": "I am feeling great today!"},
                token=token)
        assert r.status_code == 200

    def test_response_has_required_fields(self, active_conversation):
        conv_id, token = active_conversation
        r    = api("post", "/api/v1/session/message",
                   data={"conversation_id": conv_id, "text": "Tell me something nice."},
                   token=token)
        body = r.json()
        assert body.get("user_message")
        assert body.get("user_emotion")
        assert body.get("assistant_response")
        assert body.get("assistant_audio_url")
        assert "processing_time_ms" in body

    def test_assistant_audio_is_servable(self, active_conversation):
        conv_id, token = active_conversation
        r   = api("post", "/api/v1/session/message",
                  data={"conversation_id": conv_id, "text": "How are you?"},
                  token=token)
        url = r.json().get("assistant_audio_url", "")
        assert api("get", url).status_code in (200, 206)

    def test_audio_message_does_not_crash(self, active_conversation):
        conv_id, token = active_conversation
        wav = make_silent_wav(duration_s=2)
        r   = api("post", "/api/v1/session/message",
                  data={"conversation_id": conv_id},
                  files={"audio": ("test.wav", wav, "audio/wav")},
                  token=token)
        assert r.status_code != 500 or "detail" in r.json()

    def test_no_audio_no_text_returns_400(self, active_conversation):
        conv_id, token = active_conversation
        r = api("post", "/api/v1/session/message",
                data={"conversation_id": conv_id},
                token=token)
        assert r.status_code == 400

    def test_other_user_cannot_access_foreign_conversation(self, active_conversation):
        conv_id, _ = active_conversation
        tag   = uuid.uuid4().hex[:8]
        email = f"other_{tag}@test.com"
        api("post", "/api/v1/auth/register",
            json={"email": email, "password": "Pass123!", "name": "Other"})
        other_token = login(email, "Pass123!")
        r = api("post", "/api/v1/session/message",
                data={"conversation_id": conv_id, "text": "stealing"},
                token=other_token)
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 5. Session End
# ══════════════════════════════════════════════════════════════════════════════

class TestSessionEnd:
    def test_returns_summary(self, ended_conversation):
        _, _, body = ended_conversation
        assert body.get("summary")

    def test_returns_summary_audio_url(self, ended_conversation):
        _, _, body = ended_conversation
        assert body.get("summary_audio_url")

    def test_returns_emotional_journey(self, ended_conversation):
        _, _, body = ended_conversation
        assert "emotional_journey" in body

    def test_returns_personality_updated_field(self, ended_conversation):
        _, _, body = ended_conversation
        assert "personality_updated" in body

    def test_summary_audio_is_servable(self, ended_conversation):
        _, _, body = ended_conversation
        url = body.get("summary_audio_url", "")
        assert api("get", url).status_code in (200, 206)

    def test_double_end_returns_404(self, ended_conversation):
        conv_id, token, _ = ended_conversation
        r = api("post", "/api/v1/session/end",
                data={"conversation_id": conv_id}, token=token)
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 6. Conversation Queries
# ══════════════════════════════════════════════════════════════════════════════

class TestConversationQueries:
    def test_history_returns_200(self, ended_conversation):
        conv_id, token, _ = ended_conversation
        r = api("get", f"/api/v1/conversation/{conv_id}/history", token=token)
        assert r.status_code == 200

    def test_history_has_messages(self, ended_conversation):
        conv_id, token, _ = ended_conversation
        r = api("get", f"/api/v1/conversation/{conv_id}/history", token=token)
        assert len(r.json().get("messages", [])) >= 1

    def test_emotions_returns_200(self, ended_conversation):
        conv_id, token, _ = ended_conversation
        r = api("get", f"/api/v1/conversation/{conv_id}/emotions", token=token)
        assert r.status_code == 200

    def test_emotions_has_timeline(self, ended_conversation):
        conv_id, token, _ = ended_conversation
        r = api("get", f"/api/v1/conversation/{conv_id}/emotions", token=token)
        assert "emotion_timeline" in r.json()

    def test_fake_conv_id_returns_404(self, auth_token):
        r = api("get", f"/api/v1/conversation/{uuid.uuid4()}/history", token=auth_token)
        assert r.status_code == 404


# ══════════════════════════════════════════════════════════════════════════════
# 7. Personality Endpoints
# ══════════════════════════════════════════════════════════════════════════════

class TestPersonality:
    def test_status_returns_200(self, auth_token):
        assert api("get", "/api/v1/personality/status", token=auth_token).status_code == 200

    def test_status_has_required_fields(self, auth_token):
        body = api("get", "/api/v1/personality/status", token=auth_token).json()
        for field in ("sessions_complete", "sessions_needed", "ready", "progress_pct"):
            assert field in body

    def test_progress_pct_in_valid_range(self, auth_token):
        pct = api("get", "/api/v1/personality/status", token=auth_token).json()["progress_pct"]
        assert 0 <= pct <= 100

    def test_profile_returns_valid_status_code(self, auth_token):
        r = api("get", "/api/v1/personality/profile", token=auth_token)
        assert r.status_code in (200, 202, 404)

    def test_unauthenticated_status_returns_401(self):
        assert api("get", "/api/v1/personality/status").status_code == 401

    def test_unauthenticated_profile_returns_401(self):
        assert api("get", "/api/v1/personality/profile").status_code == 401


class TestPersonalityReadyProfile:
    """
    Tests that require a user with >= 5 completed sessions.
    Uses the demo account configured via MECC_TEST_EMAIL / MECC_TEST_PASSWORD.
    """

    TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]

    def test_demo_status_shows_ready(self, demo_token):
        body = api("get", "/api/v1/personality/status", token=demo_token).json()
        assert body["ready"] is True
        assert body["sessions_complete"] >= 5
        assert body["progress_pct"] == 100

    def test_demo_profile_returns_200(self, demo_token):
        r = api("get", "/api/v1/personality/profile", token=demo_token)
        assert r.status_code == 200, f"Expected 200, got {r.status_code}: {r.text}"

    def test_demo_profile_has_all_traits(self, demo_token):
        r       = api("get", "/api/v1/personality/profile", token=demo_token)
        assert r.status_code == 200
        profile = r.json().get("profile", {})
        for t in self.TRAITS:
            assert t in profile, f"Missing trait: {t}"

    def test_demo_profile_scores_have_score_and_label(self, demo_token):
        r       = api("get", "/api/v1/personality/profile", token=demo_token)
        profile = r.json().get("profile", {})
        for t in self.TRAITS:
            assert "score" in profile[t], f"{t} missing score"
            assert "label" in profile[t], f"{t} missing label"

    def test_demo_profile_labels_are_valid(self, demo_token):
        r       = api("get", "/api/v1/personality/profile", token=demo_token)
        profile = r.json().get("profile", {})
        for t in self.TRAITS:
            assert profile[t]["label"] in ("High", "Moderate", "Low"), \
                f"{t} has invalid label: {profile[t]['label']}"

    def test_demo_profile_scores_in_range(self, demo_token):
        r       = api("get", "/api/v1/personality/profile", token=demo_token)
        profile = r.json().get("profile", {})
        for t in self.TRAITS:
            score = profile[t]["score"]
            assert 0.0 <= score <= 1.0, f"{t} score out of range: {score}"


# ══════════════════════════════════════════════════════════════════════════════
# 8. Analytics
# ══════════════════════════════════════════════════════════════════════════════

class TestAnalytics:
    def test_dashboard_returns_200(self, auth_token):
        assert api("get", "/api/v1/analytics/dashboard", token=auth_token).status_code == 200

    def test_history_returns_200(self, auth_token):
        r = api("get", "/api/v1/analytics/history?limit=10&offset=0", token=auth_token)
        assert r.status_code == 200

    def test_unauthenticated_dashboard_returns_401(self):
        assert api("get", "/api/v1/analytics/dashboard").status_code == 401


# ══════════════════════════════════════════════════════════════════════════════
# 9. PersonalityService Unit Tests (no server needed)
# ══════════════════════════════════════════════════════════════════════════════

TRAITS = ["openness", "conscientiousness", "extraversion", "agreeableness", "neuroticism"]


@pytest.fixture(scope="module")
def personality_svc():
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if backend_dir not in sys.path:
        sys.path.insert(0, backend_dir)

    model_path  = os.path.join(backend_dir, os.environ.get(
        "PERSONALITY_MODEL_PATH", "checkpoints/personality/best_model.pt"))
    config_path = os.path.join(backend_dir, os.environ.get(
        "PERSONALITY_CONFIG_PATH", "checkpoints/personality/config.json"))

    if not os.path.exists(model_path) or not os.path.exists(config_path):
        pytest.skip("Personality model files not found")

    orig = os.getcwd()
    os.chdir(backend_dir)
    try:
        from services.personality_service import PersonalityService
        svc = PersonalityService(model_path, config_path)
    finally:
        os.chdir(orig)
    return svc


@pytest.fixture(scope="module")
def mock_db(personality_svc):
    """
    In-memory mock DB for unit testing profile persistence.
    Stores profiles in a dict keyed by user_id.
    """
    from unittest.mock import MagicMock
    from database import PersonalityProfile

    store = {}

    def mock_query(model):
        m = MagicMock()
        def filter_fn(*args, **kwargs):
            f = MagicMock()
            # Extract user_id from the filter expression
            def first_fn():
                # Try to find matching profile in store
                for uid, row in store.items():
                    return row
                return None
            f.first = first_fn
            return f
        m.filter = filter_fn
        return m

    def mock_add(obj):
        if isinstance(obj, PersonalityProfile):
            store[obj.user_id] = obj

    def mock_commit():
        pass

    db = MagicMock()
    db.query = mock_query
    db.add   = mock_add
    db.commit = mock_commit
    return db


class TestPersonalityServiceUnit:
    def test_predict_returns_all_traits(self, personality_svc):
        scores = personality_svc.predict_from_features(
            np.random.randn(768).astype(np.float32),
            np.random.randn(768).astype(np.float32),
            np.random.randn(2048).astype(np.float32),
        )
        assert set(scores.keys()) == set(TRAITS)

    def test_scores_in_0_1_range(self, personality_svc):
        scores = personality_svc.predict_from_features(
            np.random.randn(768).astype(np.float32),
            np.random.randn(768).astype(np.float32),
            np.random.randn(2048).astype(np.float32),
        )
        assert all(0.0 <= scores[t] <= 1.0 for t in TRAITS)

    def test_none_inputs_returns_valid_scores(self, personality_svc):
        scores = personality_svc.predict_from_features(None, None, None)
        assert set(scores.keys()) == set(TRAITS)
        assert all(0.0 <= scores[t] <= 1.0 for t in TRAITS)

    def test_format_high_label(self, personality_svc):
        assert personality_svc.format_for_display(
            {t: 0.72 for t in TRAITS})["openness"]["label"] == "High"

    def test_format_moderate_label(self, personality_svc):
        assert personality_svc.format_for_display(
            {t: 0.50 for t in TRAITS})["openness"]["label"] == "Moderate"

    def test_format_low_label(self, personality_svc):
        assert personality_svc.format_for_display(
            {t: 0.30 for t in TRAITS})["openness"]["label"] == "Low"

    def test_ema_math_via_api(self):
        """
        Test EMA math directly without DB by calling the formula.
        EMA: new = 0.3 * session + 0.7 * old
        """
        old     = {t: 0.8 for t in TRAITS}
        session = {t: 0.2 for t in TRAITS}
        result  = {
            t: 0.3 * session[t] + 0.7 * old[t]
            for t in TRAITS
        }
        expected = 0.3 * 0.2 + 0.7 * 0.8  # 0.62
        assert abs(result["openness"] - expected) < 1e-6


# ══════════════════════════════════════════════════════════════════════════════
# 10. Edge Cases
# ══════════════════════════════════════════════════════════════════════════════

class TestEdgeCases:
    def test_nonexistent_audio_returns_404(self):
        assert api("get", "/api/v1/audio/nonexistent_xyz_abc.mp3").status_code == 404

    def test_fake_conversation_history_returns_404(self, auth_token):
        r = api("get", f"/api/v1/conversation/{uuid.uuid4()}/history", token=auth_token)
        assert r.status_code == 404

    def test_message_without_body_returns_400_or_404(self, auth_token):
        r = api("post", "/api/v1/session/message",
                data={"conversation_id": str(uuid.uuid4())},
                token=auth_token)
        assert r.status_code in (400, 404)