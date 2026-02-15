# MECC Complete Setup Guide
**Answers to Your Questions + Full Implementation**

## Questions Answered

### 1. ✅ Audio/Video Length Handling

**Q: What length videos can the model handle?**

**A: Audio Length Constraints:**
- **Minimum:** 1 second (auto-padded with silence if shorter)
- **Optimal:** 5-15 seconds (best performance, fast processing)
- **Maximum single chunk:** 30 seconds
- **Maximum total:** 60 seconds (auto-chunked into 10s segments with 2s overlap)

**Implementation:**
- **< 1s:** Pad with silence
- **1-30s:** Process as single chunk (fast, ~200-400ms)
- **30-60s:** Split into chunks, aggregate predictions (weighted by confidence)
- **> 60s:** Frontend should prevent (show warning at 55s, auto-stop at 60s)

See `VIDEO_AUDIO_HANDLING.md` for complete details and code.

---

### 2. ✅ Complete Conversation Flow

**Q: How does the system-initiated conversation work?**

**A: Full Flow:**

```
START → SYSTEM WELCOMES → USER RECORDS → BACKEND PROCESSES → 
SYSTEM RESPONDS (TEXT + AUDIO) → USER RECORDS AGAIN → LOOP...
```

**Detailed Steps:**

1. **User visits app**
   - Frontend calls: `POST /api/v1/conversation/start`
   - Backend creates conversation in DB
   - Returns: welcome message (text + audio URL)
   - Frontend auto-plays welcome audio

2. **User clicks "Record" button**
   - Microphone activates
   - Visual waveform + timer shown
   - User speaks (1-60 seconds)
   - User clicks "Stop" or auto-stop at 60s

3. **Frontend sends to backend**
   ```javascript
   POST /api/v1/chat/message
   FormData:
     - conversation_id: "uuid"
     - audio: Blob (user recording)
     - text: null (will be transcribed)
   ```

4. **Backend processing**
   - Save audio file
   - Transcribe with Whisper → text
   - Extract audio features (WavLM)
   - Extract text features (RoBERTa)
   - Predict emotion (FusionMLP)
   - Retrieve conversation history from DB
   - Generate empathetic response (Claude LLM)
   - Convert response to speech (TTS)
   - Save everything to DB

5. **Frontend receives response**
   ```json
   {
     "user_message": "transcribed text",
     "user_emotion": {
       "emotion": "sad",
       "confidence": 0.82
     },
     "assistant_response": "I hear you...",
     "assistant_audio_url": "/api/v1/audio/xyz.mp3"
   }
   ```

6. **Frontend displays + plays**
   - Show user message with emotion badge
   - Show assistant text
   - Auto-play assistant audio
   - Enable "Record next response" button

7. **Conversation continues** (loop to step 2)

8. **End conversation**
   - User clicks "End Conversation"
   - Backend generates summary
   - Returns summary text + audio
   - Marks conversation as completed in DB

---

### 3. ✅ Text-to-Speech Integration

**Q: How to convert assistant responses to audio?**

**A: Three TTS Provider Options:**

**Option 1: OpenAI TTS (Recommended for MVP)**
- Pros: Fast, good quality, easy to use
- Cost: ~$15 per 1M characters
- Setup: Just need `OPENAI_API_KEY`
- Voice selection based on emotion:
  - Happy → Nova (warm, upbeat)
  - Sad → Echo (calm, soothing)
  - Angry → Onyx (steady, grounding)
  - Neutral → Alloy (balanced)

**Option 2: ElevenLabs**
- Pros: Very expressive, most emotional
- Cost: ~$0.30 per 1K characters (more expensive)
- Best for: Production after MVP validation

**Option 3: Azure Cognitive Services**
- Pros: Enterprise-grade, SSML control
- Best for: Enterprise deployments with Azure infrastructure

**Code (already implemented in `tts_service.py`):**
```python
from services.tts_service import get_tts_service

tts = get_tts_service(provider='openai')
audio_path = tts.generate_speech(
    text="I'm here to support you",
    emotion='sad'  # Adjusts voice tone
)
```

---

### 4. ✅ Database Integration

**Q: Do we need a database?**

**A: YES - Essential for:**
- Storing conversation history (for context-aware responses)
- Tracking emotion timeline (for analytics)
- Saving audio files metadata
- Generating session summaries

**Database Schema (PostgreSQL):**

```sql
-- conversations: Track each chat session
CREATE TABLE conversations (
    id UUID PRIMARY KEY,
    session_id VARCHAR UNIQUE,
    user_id VARCHAR,
    started_at TIMESTAMP,
    ended_at TIMESTAMP,
    total_messages INTEGER,
    status VARCHAR  -- 'active', 'completed', 'abandoned'
);

-- messages: All user/assistant messages
CREATE TABLE messages (
    id UUID PRIMARY KEY,
    conversation_id UUID REFERENCES conversations(id),
    role VARCHAR,  -- 'user' or 'assistant'
    content TEXT,
    
    -- Emotion data (user messages only)
    detected_emotion VARCHAR,
    emotion_confidence FLOAT,
    emotion_probabilities JSON,
    
    -- Audio metadata
    has_audio BOOLEAN,
    audio_path VARCHAR,
    audio_duration FLOAT,
    
    created_at TIMESTAMP
);

-- emotion_timeline: For visualization
CREATE TABLE emotion_timeline (
    id UUID PRIMARY KEY,
    conversation_id UUID,
    message_id UUID,
    emotion VARCHAR,
    confidence FLOAT,
    timestamp TIMESTAMP
);
```

**Setup:**
```bash
# Install PostgreSQL
brew install postgresql  # macOS
sudo apt install postgresql  # Linux

# Create database
createdb mecc_db

# Set environment variable
export DATABASE_URL="postgresql://user:pass@localhost:5432/mecc_db"
```

**Alternative: SQLite (for development only)**
```python
# In database.py, change:
DATABASE_URL = 'sqlite:///./mecc.db'
```

---

### 5. ✅ What We Missed (Now Implemented)

**Missing Pieces:**
1. ✅ **Database integration** - SQLAlchemy models created
2. ✅ **Whisper transcription** - Audio → text conversion
3. ✅ **Text-to-Speech** - Assistant responses → audio
4. ✅ **Audio length handling** - Chunking for >30s audio
5. ✅ **Session management** - Conversation context tracking
6. ✅ **Audio storage** - File storage and serving
7. ✅ **System-initiated flow** - Welcome message endpoint
8. ✅ **End session** - Summary generation

**All implemented in:**
- `database.py` - Database models & helpers
- `whisper_service.py` - Speech-to-text
- `tts_service.py` - Text-to-speech
- `app_v2.py` - Complete API with all flows
- `VIDEO_AUDIO_HANDLING.md` - Detailed specifications

---

## Complete File Structure

```
mecc-mvp/
├── backend/
│   ├── app_v2.py                     # ✅ NEW: Complete API
│   ├── models/
│   │   └── fusion_mlp.py            # Your trained model architecture
│   ├── services/
│   │   ├── emotion_service.py       # Emotion detection (A+T)
│   │   ├── llm_service.py           # LLM responses (Claude)
│   │   ├── tts_service.py           # ✅ NEW: Text-to-speech
│   │   └── whisper_service.py       # ✅ NEW: Audio transcription
│   ├── database.py                   # ✅ NEW: Database models
│   ├── checkpoints/
│   │   └── at.pth                   # Your trained model (70.7% acc)
│   ├── audio_storage/               # ✅ NEW: Audio files directory
│   ├── requirements_complete.txt    # ✅ NEW: All dependencies
│   └── .env
│
└── frontend/
    └── (your existing React app)
```

---

## Environment Variables (Complete List)

Create `backend/.env`:

```bash
# Required
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here  # For Whisper + TTS

# Database
DATABASE_URL=postgresql://mecc_user:mecc_password@localhost:5432/mecc_db

# Model Configuration
MODEL_CHECKPOINT_PATH=checkpoints/at.pth
DEVICE=cuda  # or 'cpu'

# TTS Provider
TTS_PROVIDER=openai  # or 'elevenlabs', 'azure'

# Whisper Configuration
USE_WHISPER_API=false  # true = use OpenAI API, false = local model
WHISPER_MODEL_SIZE=base  # tiny, base, small, medium, large

# Audio Storage
AUDIO_STORAGE_DIR=./audio_storage

# Server
HOST=0.0.0.0
PORT=8000
RELOAD=true

# Optional: For ElevenLabs TTS
# ELEVENLABS_API_KEY=your-key

# Optional: For Azure TTS
# AZURE_SPEECH_KEY=your-key
# AZURE_REGION=eastus
```

---

## Setup Instructions (Step-by-Step)

### Prerequisites
- Python 3.9+
- PostgreSQL 14+
- 8GB RAM (16GB recommended)
- GPU with CUDA (optional but recommended)
- Anthropic API key
- OpenAI API key

### Step 1: Database Setup

```bash
# Install PostgreSQL
brew install postgresql@14  # macOS
# OR
sudo apt install postgresql-14  # Ubuntu

# Start PostgreSQL
brew services start postgresql  # macOS
# OR
sudo systemctl start postgresql  # Linux

# Create database and user
createdb mecc_db
psql mecc_db

# In psql:
CREATE USER mecc_user WITH PASSWORD 'mecc_password';
GRANT ALL PRIVILEGES ON DATABASE mecc_db TO mecc_user;
\q
```

### Step 2: Backend Installation

```bash
cd backend

# Create virtual environment
python3.9 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements_complete.txt

# This will download (first run only):
# - WavLM-base (~400 MB)
# - RoBERTa-base (~500 MB)
# - Whisper-base (~142 MB)
# Total: ~1 GB

# Copy your trained model
cp ../training/checkpoints/at.pth checkpoints/

# Copy model architecture
cp /path/to/model.py models/fusion_mlp.py

# Create audio storage directory
mkdir -p audio_storage
```

### Step 3: Environment Configuration

```bash
# Copy environment template
cat > .env << 'EOF'
ANTHROPIC_API_KEY=sk-ant-your-actual-key
OPENAI_API_KEY=sk-your-actual-key
DATABASE_URL=postgresql://mecc_user:mecc_password@localhost:5432/mecc_db
MODEL_CHECKPOINT_PATH=checkpoints/at.pth
DEVICE=cuda
TTS_PROVIDER=openai
USE_WHISPER_API=false
WHISPER_MODEL_SIZE=base
AUDIO_STORAGE_DIR=./audio_storage
HOST=0.0.0.0
PORT=8000
EOF

# Edit .env with your actual API keys
nano .env
```

### Step 4: Initialize Database

```bash
# The database tables will be created automatically on first run
# Or manually initialize:
python -c "from database import init_db; init_db()"
```

### Step 5: Start Backend

```bash
# Run the server
python app_v2.py

# Expected output:
# 🚀 Starting MECC Backend API v2.0...
# ✅ Database tables created successfully
# Loading emotion model from: checkpoints/at.pth
# ✅ EmotionRecognitionService initialized
# ✅ LLMService initialized with Claude Sonnet 4
# ✅ OpenAI TTS initialized
# ✅ Whisper model 'base' loaded successfully
# ✅ All services initialized successfully
# INFO: Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Test the API

```bash
# In another terminal:

# 1. Health check
curl http://localhost:8000/health

# 2. Start conversation
curl -X POST http://localhost:8000/api/v1/conversation/start \
  -F "user_id=test_user"

# Save the conversation_id from response

# 3. Send a message (text only for testing)
curl -X POST http://localhost:8000/api/v1/chat/message \
  -F "conversation_id=<your-conversation-id>" \
  -F "text=I'm feeling really stressed about work"

# You should get back:
# - Detected emotion
# - Empathetic response text
# - URL to assistant audio

# 4. Download and play audio
curl http://localhost:8000/api/v1/audio/<filename> -o response.mp3
open response.mp3  # macOS, or: vlc response.mp3
```

---

## Frontend Integration

### Updated Frontend Flow

```typescript
// src/hooks/useConversation.ts
import { useState, useEffect } from 'react';

interface Conversation {
  id: string;
  sessionId: string;
  welcomeMessage: string;
  welcomeAudioUrl: string;
}

export function useConversation() {
  const [conversation, setConversation] = useState<Conversation | null>(null);
  const [isLoading, setIsLoading] = useState(false);

  const startConversation = async (userId?: string) => {
    setIsLoading(true);
    
    try {
      const formData = new FormData();
      if (userId) formData.append('user_id', userId);
      
      const response = await fetch('http://localhost:8000/api/v1/conversation/start', {
        method: 'POST',
        body: formData
      });
      
      const data = await response.json();
      
      setConversation({
        id: data.conversation_id,
        sessionId: data.session_id,
        welcomeMessage: data.welcome_message,
        welcomeAudioUrl: `http://localhost:8000${data.welcome_audio_url}`
      });
      
      // Auto-play welcome audio
      const audio = new Audio(`http://localhost:8000${data.welcome_audio_url}`);
      audio.play();
      
      return data;
    } finally {
      setIsLoading(false);
    }
  };

  const sendMessage = async (audioBlob: Blob) => {
    if (!conversation) throw new Error('No active conversation');
    
    const formData = new FormData();
    formData.append('conversation_id', conversation.id);
    formData.append('audio', audioBlob, 'recording.wav');
    
    const response = await fetch('http://localhost:8000/api/v1/chat/message', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    // Auto-play assistant response
    const audio = new Audio(`http://localhost:8000${data.assistant_audio_url}`);
    audio.play();
    
    return data;
  };

  const endConversation = async () => {
    if (!conversation) return;
    
    const formData = new FormData();
    formData.append('conversation_id', conversation.id);
    
    const response = await fetch('http://localhost:8000/api/v1/conversation/end', {
      method: 'POST',
      body: formData
    });
    
    const data = await response.json();
    
    // Play summary audio
    const audio = new Audio(`http://localhost:8000${data.summary_audio_url}`);
    audio.play();
    
    return data;
  };

  return {
    conversation,
    isLoading,
    startConversation,
    sendMessage,
    endConversation
  };
}
```

### Voice Recording Component

```typescript
// src/components/VoiceRecorder.tsx
import { useState, useRef } from 'react';
import { Mic, Square } from 'lucide-react';

interface Props {
  onRecordingComplete: (blob: Blob) => void;
  maxDuration?: number;  // seconds, default 60
}

export function VoiceRecorder({ onRecordingComplete, maxDuration = 60 }: Props) {
  const [isRecording, setIsRecording] = useState(false);
  const [duration, setDuration] = useState(0);
  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const timerRef = useRef<NodeJS.Timer | null>(null);

  const startRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      const mediaRecorder = new MediaRecorder(stream);
      
      mediaRecorderRef.current = mediaRecorder;
      chunksRef.current = [];
      
      mediaRecorder.ondataavailable = (e) => {
        if (e.data.size > 0) {
          chunksRef.current.push(e.data);
        }
      };
      
      mediaRecorder.onstop = () => {
        const blob = new Blob(chunksRef.current, { type: 'audio/wav' });
        onRecordingComplete(blob);
        
        // Stop all tracks
        stream.getTracks().forEach(track => track.stop());
      };
      
      mediaRecorder.start();
      setIsRecording(true);
      setDuration(0);
      
      // Start timer
      timerRef.current = setInterval(() => {
        setDuration(d => {
          const newDuration = d + 0.1;
          
          // Auto-stop at max duration
          if (newDuration >= maxDuration) {
            stopRecording();
          }
          
          return newDuration;
        });
      }, 100);
      
    } catch (error) {
      console.error('Failed to start recording:', error);
      alert('Could not access microphone');
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      
      if (timerRef.current) {
        clearInterval(timerRef.current);
      }
    }
  };

  return (
    <div className="flex items-center gap-4">
      <button
        onClick={isRecording ? stopRecording : startRecording}
        className={`p-4 rounded-full transition-colors ${
          isRecording
            ? 'bg-red-600 hover:bg-red-700 animate-pulse'
            : 'bg-blue-600 hover:bg-blue-700'
        }`}
      >
        {isRecording ? <Square size={24} /> : <Mic size={24} />}
      </button>
      
      {isRecording && (
        <div className="flex items-center gap-2">
          <div className="w-2 h-2 bg-red-500 rounded-full animate-pulse" />
          <span className="text-sm font-mono">
            {duration.toFixed(1)}s / {maxDuration}s
          </span>
          {duration > maxDuration - 5 && (
            <span className="text-xs text-yellow-400">
              Auto-stop in {(maxDuration - duration).toFixed(0)}s
            </span>
          )}
        </div>
      )}
    </div>
  );
}
```

---

## Cost Estimation

### Per Conversation (5-10 message exchanges)

**Emotion Detection:** Free (your trained model)

**Transcription (Whisper):**
- Local model: Free
- OpenAI API: $0.006 per minute → ~$0.01 per conversation

**LLM (Claude Sonnet 4):**
- Input: ~1K tokens × $3/1M = $0.003
- Output: ~500 tokens × $15/1M = $0.0075
- Total: ~$0.01 per conversation

**TTS (OpenAI):**
- ~500 characters per response × 10 responses = 5K chars
- $15 per 1M chars → $0.075 per conversation

**Total per conversation: ~$0.10**

**For 100 daily users:** $10/day = $300/month

---

## Troubleshooting

### Database Connection Failed
```bash
# Check PostgreSQL is running
pg_isready

# Check credentials
psql -U mecc_user -d mecc_db

# Reset password if needed
psql postgres
ALTER USER mecc_user WITH PASSWORD 'new_password';
```

### Whisper Model Too Slow
```bash
# Use API instead of local model
export USE_WHISPER_API=true

# Or use smaller model
export WHISPER_MODEL_SIZE=tiny  # Faster but less accurate
```

### Out of Memory
```bash
# Use CPU instead of GPU
export DEVICE=cpu

# Or reduce Whisper model size
export WHISPER_MODEL_SIZE=tiny
```

### Audio Not Playing in Frontend
```bash
# Check CORS settings in app_v2.py
# Make sure frontend URL is in allow_origins

# Check audio file exists
ls audio_storage/

# Test audio URL directly
curl http://localhost:8000/api/v1/audio/<filename>
```

---

## Next Steps

1. **Test locally** (30 minutes)
2. **Integrate frontend** (2-3 hours)
3. **User testing** (1 week)
4. **Deploy to cloud** (see separate deployment guide)

All implementation files are ready to use!
