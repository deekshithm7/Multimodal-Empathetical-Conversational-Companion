# Multimodal Empathetical Conversational Companion (MECC)

An AI-powered empathetic companion that uses multimodal emotion recognition (audio + text) to provide emotionally intelligent responses.

## 🚀 Features

- **Multimodal Emotion Recognition**: Analyzes both audio and text for accurate emotion detection
- **Empathetic Responses**: Context-aware, emotion-adaptive conversations
- **100% Free Stack**: No API costs - runs entirely locally on your GPU
- **Real-time Speech**: Voice input and output with Whisper + Piper TTS
- **Session Summaries**: Automatic conversation summaries with emotional journey tracking

## 📋 Prerequisites

### Required Software
1. **Python 3.11+**
2. **PostgreSQL** (database)
3. **Ollama** (local LLM server)
4. **FFmpeg** (audio processing)
5. **Node.js 18+** (frontend)

### Hardware
- **GPU**: NVIDIA GPU with CUDA support recommended (tested on RTX 3050)
- **RAM**: 8GB minimum, 16GB+ recommended
- **Disk**: 10GB free space

## 🛠️ Installation

### 1. Clone Repository
```bash
git clone https://github.com/deekshithm7/Multimodal-Empathetical-Conversational-Companion.git
cd Multimodal-Empathetical-Conversational-Companion
```

### 2. Backend Setup

#### Install Dependencies
```bash
cd backend
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Mac/Linux

pip install -r requirements.txt
```

#### Download Voice Model
Piper TTS voice is NOT included in the repository (60MB). Download it manually:

```bash
# Download voice model
curl -L -o backend/voices/en_US-lessac-medium.onnx \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx

# Download config
curl -L -o backend/voices/en_US-lessac-medium.onnx.json \
  https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json
```

**Windows (PowerShell):**
```powershell
Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx" -OutFile "backend\voices\en_US-lessac-medium.onnx"

Invoke-WebRequest -Uri "https://huggingface.co/rhasspy/piper-voices/resolve/main/en/en_US/lessac/medium/en_US-lessac-medium.onnx.json" -OutFile "backend\voices\en_US-lessac-medium.onnx.json"
```

#### Setup Database
```bash
# Create PostgreSQL database
createdb mecc_db

# Or via psql:
psql -U postgres
CREATE DATABASE mecc_db;
\q
```

#### Configure Environment
```bash
cp .env.example .env
# Edit .env with your database credentials
```

#### Install External Tools
```bash
# Ollama (for LLM)
# Download from: https://ollama.com/download
ollama pull llama3.2:3b

# FFmpeg (for audio)
# Windows: choco install ffmpeg
# Mac: brew install ffmpeg
# Linux: sudo apt install ffmpeg
```

### 3. Frontend Setup
```bash
cd ../frontend
npm install
```

## 🚀 Running the Application

### Start Backend
```bash
cd backend
venv\Scripts\activate
python app.py
# Backend runs on http://localhost:8000
```

### Start Ollama (separate terminal)
```bash
ollama serve
```

### Start Frontend
```bash
cd frontend
npm run dev
# Frontend runs on http://localhost:5173
```

## 📦 Tech Stack

### Backend
- **FastAPI** - REST API framework
- **PyTorch** - Deep learning (GPU acceleration)
- **Transformers** - WavLM, RoBERTa models
- **Whisper** - Speech-to-text
- **Piper TTS** - Text-to-speech
- **Ollama** - Local LLM (Llama 3.2)
- **PostgreSQL** - Database

### Frontend
- **React + TypeScript**
- **Vite** - Build tool
- **Tailwind CSS** - Styling

## 🔧 Configuration

### Environment Variables (`.env`)
```env
DATABASE_URL=postgresql://postgres:password@localhost/mecc_db
MODEL_CHECKPOINT_PATH=checkpoints/at.pth
OLLAMA_MODEL=llama3.2:3b
OLLAMA_BASE_URL=http://localhost:11434
WHISPER_MODEL_SIZE=base
AUDIO_STORAGE_DIR=./audio_storage
KEEP_AUDIO=false
```

## 📊 Performance

- **Message Processing**: ~15-20 seconds
- **GPU Utilization**: Auto-detected (CUDA/CPU fallback)
- **API Cost**: $0 (completely free!)

## 🤝 Contributing

Contributions welcome! Please open an issue or pull request.

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- Piper TTS voices from Rhasspy
- Whisper from OpenAI
- Llama models from Meta
- WavLM from Microsoft
