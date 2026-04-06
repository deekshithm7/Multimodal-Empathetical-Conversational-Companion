# 🧠 MECC — Multimodal Empathetical Conversational Companion

> An AI companion that truly *understands* you — detecting your emotions from your **voice**, **face**, and **words** simultaneously to deliver genuinely empathetic responses.

---

## ✨ What Makes MECC Different

Most chatbots read only your words. MECC analyses **three information channels at once**:

| Modality | What it captures |
|---|---|
| 🎙️ Voice | Tone, pitch, and emotional prosody |
| 📝 Words | Semantic meaning and sentiment |
| 👁️ Face | Facial expressions and visual cues |

These three streams are fused by a custom **ET-TACFN** (Emotion-aware Temporal Attentive Cross-modal Fusion Network) trained on the MER 2023 dataset, giving MECC a richer picture of your emotional state than any single-modality system can achieve.

On top of emotion detection, MECC builds a **long-term OCEAN personality profile** for each user by running a separate `TransformerFusion` model on every video conversation, tracking how your Big Five personality traits evolve over time.

---

## 🖥️ Screenshots

> Chat interface with live emotion detection, emotional journey analytics, and personality insights pages.

---

## 🚀 Features

### Core
- **True Multimodal Emotion Recognition** — Audio + Text + Video fused into one prediction
- **Empathetic LLM Responses** — Llama 3.2 (local, via Ollama) guided by detected emotion and confidence
- **Voice I/O** — Whisper STT + Piper TTS for a fully spoken conversation experience
- **Webcam Recording** — In-browser MediaRecorder captures video + audio into a single WebM blob

### Analytics & Memory
- **Session History** — Every conversation saved with emotional journey timeline
- **OCEAN Personality Profiling** — Big Five personality scores build up after 5+ sessions
- **Personality Insights Page** — Track stable vs. evolving traits over multiple conversations
- **Dashboard** — Recent sessions, dominant emotion stats, and session summaries

### Technical
- **Parallel Feature Extraction** — Audio, Text, and Visual encoders run concurrently via `ThreadPoolExecutor`
- **FFmpeg WebM Support** — Video blobs from the browser are automatically transcoded before OpenCV processing
- **JWT Authentication** — Secure per-user sessions, history, and personality profiles
- **100% Local & Free** — No external API costs; all models run on your own GPU

---

## 🏗️ Architecture

```
Browser (React + TypeScript)
        │   WebM blob (video + audio)
        ▼
FastAPI Backend
        │
        ├── Whisper STT  (extracts audio from WebM) ──────────► text
        │
        │   ╔══ EmotionFeatureService ══════════════════════╗
        │   ║  (Sequence-level outputs for temporal fusion) ║
        ├───║  WavLM-Base+            → [T_a, 768]          ║
        │   ║  RoBERTa-Large          → [128, 1024]         ║
        │   ║  ResNet50 + proj(256)   → [30, 256]           ║
        │   ╚══════════════════════╤════════════════════════╝
        │                          │
        │               ET-TACFN Classifier
        │                          │
        │               emotion label + confidence
        │
        │   ╔══ FeatureService (background) ═══════════════════════╗
        │   ║  (Pooled embeddings for holistic profiling)       ║
        ├───║  WavLM                  → 768-dim                 ║
        │   ║  RoBERTa                → 768-dim                 ║
        │   ║  ResNet50               → 2048-dim               ║
        │   ╚══════════════════════╤════════════════════════╝
        │                          │
        │           TransformerFusion → OCEAN scores → DB
        │
        ├── LLM (Llama 3.2 via Ollama)
        │     System prompt injected with emotion + guidance
        │     → empathetic response text
        │
        └── Piper TTS → WAV audio response
```

---

## 📦 Tech Stack

### Backend
| Component | Technology |
|---|---|
| API Framework | FastAPI |
| Deep Learning | PyTorch + CUDA |
| **Emotion Feature Extraction** | |
| └─ Audio encoder | WavLM-Base+ → sequence `[T_a, 768]` |
| └─ Text encoder | RoBERTa-Large → sequence `[128, 1024]` |
| └─ Visual encoder | ResNet50 + Linear(2048→256) + ReLU → `[30, 256]` |
| Emotion Classifier | ET-TACFN (custom, trained on MER 2023) |
| **Personality Feature Extraction** | |
| └─ Audio encoder | WavLM-Base+ → pooled `768-dim` |
| └─ Text encoder | RoBERTa → pooled `768-dim` |
| └─ Visual encoder | ResNet50 → pooled `2048-dim` |
| Personality Model | TransformerFusion (TACFN variant) |
| Speech-to-Text | OpenAI Whisper |
| Text-to-Speech | Piper TTS |
| Local LLM | Llama 3.2:3b via Ollama |
| Database | PostgreSQL + SQLAlchemy |
| Video Processing | FFmpeg + OpenCV |

### Frontend
| Component | Technology |
|---|---|
| Framework | React 18 + TypeScript |
| Build Tool | Vite |
| Styling | Tailwind CSS |
| Animations | Framer Motion |
| State Management | Zustand |
| Charts | Recharts |
| Icons | Lucide React |

---

## 📋 Prerequisites

| Requirement | Notes |
|---|---|
| Python 3.11+ | Backend runtime |
| Node.js 18+ | Frontend build |
| PostgreSQL 14+ | User data, sessions, emotion timeline |
| Ollama | Local LLM server — [ollama.com](https://ollama.com/download) |
| FFmpeg | Audio/video processing |
| NVIDIA GPU (CUDA) | Strongly recommended; RTX 3050 4GB minimum |

---

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/deekshithm7/Multimodal-Empathetical-Conversational-Companion.git
cd Multimodal-Empathetical-Conversational-Companion
```

### 2. Backend Setup

```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# macOS/Linux
# source venv/bin/activate

pip install -r requirements.txt
```

#### Configure Environment
Create a `.env` file inside the `backend/` folder:

```bash
# Windows
copy NUL backend\.env
# macOS/Linux
touch backend/.env
```

Key environment variables:
```env
DATABASE_URL=postgresql://postgres:password@localhost/mecc_db

# Model paths
MODEL_CHECKPOINT_PATH=checkpoints/atv_emotion.pth

# LLM
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434

# Whisper
WHISPER_MODEL_SIZE=base

# Storage
AUDIO_STORAGE_DIR=./audio_storage
KEEP_AUDIO=false

# Test credentials (optional, for development)
MECC_TEST_EMAIL=demo@mecc.ai
MECC_TEST_PASSWORD=demo123
```

#### Create Database
```bash
psql -U postgres -c "CREATE DATABASE mecc_db;"
```

#### Download Piper TTS Voice Model
```powershell
# Windows (PowerShell)
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" `
  -OutFile "backend\voices\en_US-lessac-medium.onnx"

Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" `
  -OutFile "backend\voices\en_US-lessac-medium.onnx.json"
```

```bash
# macOS / Linux
curl -L -o backend/voices/en_US-lessac-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx

curl -L -o backend/voices/en_US-lessac-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

#### Place Trained Model Checkpoints
```
backend/checkpoints/atv_emotion.pth             ← ET-TACFN emotion model
backend/checkpoints/personality/best_model.pt   ← Personality TransformerFusion model
```

#### Pull LLM
```bash
ollama pull llama3.2:3b
```

### 3. Frontend Setup
```bash
cd frontend
npm install
```

---

## ▶️ Running the Application

Open three terminals:

**Terminal 1 — Ollama (LLM Server)**
```bash
ollama serve
```

**Terminal 2 — Backend**
```bash
cd backend
venv\Scripts\activate   # Windows
python app.py
# → http://localhost:8000
# → API docs: http://localhost:8000/docs
```

**Terminal 3 — Frontend**
```bash
cd frontend
npm run dev
# → http://localhost:5173
```

---

## 🗂️ Project Structure

```
├── backend/
│   ├── app.py                   # FastAPI app entry point
│   ├── database.py              # SQLAlchemy models + helpers
│   ├── requirements.txt
│   ├── checkpoints/             # Trained model weights
│   ├── feature_extractors/      # Audio, Text, Visual encoder wrappers
│   ├── models/
│   │   ├── emotion_classifier.py    # ET-TACFN architecture
│   │   └── personality_model.py     # TransformerFusion architecture
│   ├── routers/
│   │   ├── analytics.py         # Session history, dashboard stats
│   │   └── personality.py       # OCEAN profile endpoints
│   ├── services/
│   │   ├── conversation_service.py  # Main message pipeline orchestrator
│   │   ├── emotion_feature_service.py  # ET-TACFN feature extraction
│   │   ├── feature_service.py      # Personality feature extraction
│   │   ├── emotion_service.py      # Emotion prediction
│   │   ├── llm_service.py          # Ollama / Llama 3.2
│   │   ├── tts_service.py          # Piper TTS
│   │   └── transcription_service.py # Whisper STT
│   └── voices/                  # Piper TTS voice files (download separately)
│
└── frontend/
    └── src/
        ├── api/client.ts        # All API calls
        ├── components/
        │   ├── Chat/            # ChatInterface, message bubbles
        │   ├── Dashboard/       # Session summary, personality radar
        │   └── UI/              # Shared components (EmotionBadge, etc.)
        ├── hooks/
        │   ├── useWebcamRecorder.ts    # MediaRecorder + WebM capture
        │   └── useSpeechRecognition.ts # Web Speech API
        ├── pages/
        │   ├── Chat.tsx         # Main conversation page
        │   ├── History.tsx      # Session history browser
        │   ├── Dashboard.tsx    # Stats overview
        │   └── PersonalityInsights.tsx  # OCEAN trait timeline
        └── store/
            ├── useEmotionStore.ts   # Session + message state
            └── useAuthStore.ts      # Auth state
```

---

## 📊 API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/v1/auth/register` | Register new user |
| `POST` | `/api/v1/auth/token` | Login, get JWT |
| `POST` | `/api/v1/session/start` | Start new conversation session |
| `POST` | `/api/v1/session/message` | Send message (multipart: text + WebM) |
| `POST` | `/api/v1/session/end` | End session, get summary |
| `GET`  | `/api/v1/analytics/dashboard` | Dashboard stats |
| `GET`  | `/api/v1/analytics/history` | Session history list |
| `GET`  | `/api/v1/analytics/session/{id}` | Session detail + emotion timeline |
| `GET`  | `/api/v1/personality/profile` | OCEAN personality profile |
| `GET`  | `/api/v1/personality/status` | Sessions complete / needed |

Full interactive docs available at `http://localhost:8000/docs`

---

## 🧬 Model Details

### ET-TACFN — Emotion Recognition

The core emotion model is a custom **Emotion-aware Temporal Attentive Cross-modal Fusion Network** trained on the MER 2023 multimodal emotion recognition dataset.

- **Emotions**: Neutral · Happy · Sad · Angry · Fearful · Disgust · Surprised · Calm
- **Feature extractor**: `EmotionFeatureService` — outputs **temporal sequences** for attention-based fusion:
  - WavLM-Base+ → `[T_a, 768]` hidden-state sequence
  - RoBERTa-Large → `[128, 1024]` token sequence
  - ResNet50 + Linear(2048→256) + ReLU → `[30, 256]` frame sequence
- **Why sequences?** ET-TACFN's cross-modal attention layers reason over the *order and timing* of audio frames and text tokens — essential for temporal emotion dynamics.
- **Missing Modality Handling**: Graceful zero-padded fallback for audio-only messages

### Personality OCEAN Profiling

A separate `TransformerFusion` model uses its own **`FeatureService`** (`feature_service.py`) which outputs *pooled* embeddings (not sequences) — because personality is about the overall character of the entire clip, not moment-to-moment variation:

- WavLM → pooled `768-dim` vector
- RoBERTa → pooled `768-dim` vector
- ResNet50 → raw `2048-dim` avgpool vector

Each video message generates one OCEAN observation (saved to DB). After **5+ completed sessions**, a stable profile is computed via Exponential Moving Average (α = 0.3). The **Personality Insights** page shows trait evolution over time and stable average scores.

---

## 📄 License

MIT License — see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

- [MER 2023](https://github.com/zeroQiaoba/MER2023-Baseline) — multimodal emotion recognition dataset and baseline
- [WavLM](https://github.com/microsoft/unilm/tree/master/wavlm) by Microsoft Research
- [RoBERTa](https://huggingface.co/roberta-large) by Facebook AI
- [Whisper](https://github.com/openai/whisper) by OpenAI
- [Llama 3.2](https://ai.meta.com/llama/) by Meta AI
- [Piper TTS](https://github.com/rhasspy/piper) by Rhasspy
