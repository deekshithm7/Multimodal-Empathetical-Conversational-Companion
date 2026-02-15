# MECC MVP - Quick Start Guide

## 🚀 Deployment in 30 Minutes

This guide will get your MECC MVP up and running with emotion recognition + empathetic chat.

---

## Prerequisites

- Python 3.9+
- Node.js 16+ (for frontend)
- 8GB RAM minimum (16GB recommended)
- GPU with CUDA support (optional but recommended)
- Anthropic API key ([Get one here](https://console.anthropic.com/))

---

## Part 1: Backend Setup (15 minutes)

### Step 1: Project Structure

Create the following structure:

```
mecc-mvp/
├── backend/
│   ├── app.py                    # FastAPI application
│   ├── models/
│   │   └── fusion_mlp.py        # Model architecture
│   ├── services/
│   │   ├── emotion_service.py   # Emotion recognition
│   │   └── llm_service.py       # LLM integration
│   ├── checkpoints/
│   │   └── at.pth               # Trained model (8.4 MB)
│   ├── requirements.txt
│   └── .env
└── frontend/
    └── (your existing React app)
```

### Step 2: Copy Files

```bash
# Navigate to your project
cd mecc-mvp

# Copy model architecture
cp /mnt/user-data/uploads/model.py backend/models/fusion_mlp.py

# Copy implementation files (from Claude's workspace)
cp /home/claude/app.py backend/
cp /home/claude/emotion_service.py backend/services/
cp /home/claude/llm_service.py backend/services/
cp /home/claude/requirements.txt backend/

# Copy your trained model checkpoint
cp training/checkpoints/at.pth backend/checkpoints/
```

### Step 3: Environment Setup

```bash
cd backend

# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# This will auto-download:
# - microsoft/wavlm-base (~400 MB)
# - roberta-base (~500 MB)
# Total first-run download: ~900 MB
```

### Step 4: Configuration

Create `backend/.env`:

```bash
# API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here

# Model Configuration
MODEL_CHECKPOINT_PATH=checkpoints/at.pth
DEVICE=cuda  # or 'cpu' if no GPU

# Server Configuration
HOST=0.0.0.0
PORT=8000
RELOAD=true
```

### Step 5: Start Backend

```bash
# From backend/ directory
python app.py

# Or using uvicorn directly:
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Started server process
INFO:     Waiting for application startup.
🚀 Starting MECC Backend API...
INFO:     Loading emotion model from: checkpoints/at.pth
✅ All services initialized successfully
INFO:     Application startup complete.
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Step 6: Test Backend

Open another terminal:

```bash
# Health check
curl http://localhost:8000/health

# Test emotion detection (text only)
curl -X POST "http://localhost:8000/api/v1/emotion/predict" \
  -F "text=I'm so happy today!"

# Test chat endpoint
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -F "text=I'm feeling overwhelmed with work"
```

---

## Part 2: Frontend Integration (15 minutes)

### Step 1: Update API Base URL

In `frontend/.env`:

```bash
VITE_API_BASE_URL=http://localhost:8000
```

### Step 2: Install Dependencies

```bash
cd frontend
npm install
```

### Step 3: Update Emotion Store

Replace `frontend/src/store/useEmotionStore.ts` with the implementation from the MVP_DEFINITION.md document (Section 3.3).

Key changes:
- Connect to `/api/v1/chat/message` endpoint
- Send audio blob + text
- Include conversation history
- Parse emotion + response from API

### Step 4: Update Chat Component

Replace `frontend/src/components/ChatInterface.tsx` with the implementation from MVP_DEFINITION.md (Section 3.3).

Key features:
- Emotion indicator at top
- Voice recording button
- Message bubbles with emotion labels
- Processing state

### Step 5: Start Frontend

```bash
npm run dev
```

Open browser: `http://localhost:5173`

---

## Testing the Complete System

### Test 1: Text-only Chat

1. Type a message: "I'm so excited about this project!"
2. Click send
3. Observe:
   - Emotion detected: **Happy** (high confidence)
   - Response is enthusiastic and supportive

### Test 2: Voice Chat

1. Click the microphone button
2. Speak: "I'm feeling really frustrated right now"
3. Stop recording and send
4. Observe:
   - Emotion detected: **Angry** (moderate-high confidence)
   - Response validates frustration without dismissing

### Test 3: Multimodal (Audio + Text)

1. Click microphone and say something sad
2. Also type a sad message
3. Send both
4. Observe:
   - Emotion combines both cues
   - More confident prediction

---

## Performance Benchmarks

Run this Python script to test latency:

```python
import time
import requests

def test_emotion_latency():
    url = "http://localhost:8000/api/v1/emotion/predict"
    
    for i in range(10):
        start = time.time()
        response = requests.post(url, data={"text": "I'm feeling good!"})
        latency = (time.time() - start) * 1000
        
        print(f"Test {i+1}: {latency:.0f}ms - Emotion: {response.json()['data']['emotion']}")

def test_chat_latency():
    url = "http://localhost:8000/api/v1/chat/message"
    
    for i in range(5):
        start = time.time()
        response = requests.post(url, data={"text": "Tell me something encouraging"})
        latency = (time.time() - start) * 1000
        
        print(f"Chat {i+1}: {latency:.0f}ms")

# Run tests
print("🧪 Testing Emotion Detection Latency...")
test_emotion_latency()

print("\n🧪 Testing Full Chat Latency...")
test_chat_latency()
```

**Expected Performance:**
- Emotion detection: 150-400ms (CPU) or 50-150ms (GPU)
- Full chat (emotion + LLM): 1.5-3s (depends on LLM response time)

---

## Troubleshooting

### Issue: "ANTHROPIC_API_KEY not set"

**Solution:** 
```bash
export ANTHROPIC_API_KEY="sk-ant-your-key"
```

### Issue: "CUDA out of memory"

**Solution:** Use CPU instead:
```bash
export DEVICE=cpu
```

### Issue: "Model checkpoint not found"

**Solution:** Verify path:
```bash
ls -lh backend/checkpoints/at.pth
# Should show ~8.4 MB file
```

### Issue: Slow inference on CPU

**Expected:** ~300-400ms on CPU is normal  
**Optimization:** Use GPU, or implement model quantization

### Issue: LLM responses too slow

**Solution:** 
- Check your internet connection
- Consider caching common responses
- Implement streaming responses (advanced)

### Issue: CORS errors in frontend

**Solution:** Verify backend CORS settings in `app.py`:
```python
allow_origins=["http://localhost:5173"]
```

---

## Validation Checklist

Before considering MVP complete, verify:

- [ ] Backend starts without errors
- [ ] Health check returns `{"status": "healthy"}`
- [ ] Emotion detection works on text input
- [ ] Emotion detection works on audio input (if testing with files)
- [ ] Chat endpoint returns empathetic responses
- [ ] Responses vary based on detected emotion
- [ ] Frontend connects to backend successfully
- [ ] Can send text messages and receive responses
- [ ] Voice recording works (if implemented)
- [ ] Emotion indicator updates correctly
- [ ] Conversation history is maintained
- [ ] No console errors in browser or terminal

---

## Next Steps (Post-MVP)

Once MVP is validated:

1. **User Testing**
   - Get 5-10 people to use it
   - Collect qualitative feedback
   - Note edge cases and bugs

2. **Performance Optimization**
   - Profile slow endpoints
   - Implement caching
   - Consider model quantization
   - Add batch processing for audio

3. **Feature Additions**
   - Speech-to-text (Whisper integration)
   - Session summaries
   - Emotion history visualization
   - Export conversation logs

4. **Deployment**
   - Dockerize the application
   - Deploy to cloud (AWS/GCP/Azure)
   - Set up CI/CD pipeline
   - Add monitoring (Sentry, Datadog)

5. **Model Improvements**
   - Expand to more emotions
   - Train on additional datasets
   - Fine-tune on domain-specific data
   - Add personality inference (v2.0)

---

## Resources

- **API Documentation:** `http://localhost:8000/docs` (auto-generated by FastAPI)
- **Model Architecture:** See `model.py` for FusionMLP details
- **Training Results:** See `TRAINING_RESULTS.md` in training folder
- **Full MVP Spec:** See `MVP_DEFINITION.md`

---

## Getting Help

If you encounter issues:

1. Check logs in terminal where backend is running
2. Check browser console for frontend errors
3. Verify all environment variables are set
4. Test each endpoint individually with curl
5. Check that checkpoint file is valid (8.4 MB, not corrupted)

---

## Success Metrics

Your MVP is successful if:

✅ Users can have natural conversations  
✅ Emotion detection feels accurate (>70% user agreement)  
✅ Responses feel empathetic and supportive  
✅ System responds in <3 seconds  
✅ No crashes or major bugs in normal use  

---

**You're ready to deploy! 🎉**

Time to launch: ~30 minutes  
Time to first conversation: ~35 minutes  
Time to validated MVP: ~2-3 weeks (with user testing)
