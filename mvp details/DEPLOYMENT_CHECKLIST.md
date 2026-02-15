# MECC MVP Deployment Checklist

## Pre-Deployment Checklist

### 1. Backend Requirements
- [ ] Python 3.9+ installed
- [ ] Virtual environment created
- [ ] All dependencies installed (`pip install -r requirements.txt`)
- [ ] Model checkpoint downloaded (at.pth, 8.4 MB)
- [ ] Model architecture file copied (`model.py` → `models/fusion_mlp.py`)
- [ ] Anthropic API key obtained
- [ ] `.env` file created with API key

### 2. Model Files
- [ ] `checkpoints/at.pth` exists (8.4 MB)
- [ ] `models/fusion_mlp.py` exists
- [ ] WavLM and RoBERTa will auto-download (~900 MB total)

### 3. Service Implementation
- [ ] `services/emotion_service.py` created
- [ ] `services/llm_service.py` created
- [ ] `app.py` FastAPI application created

### 4. Configuration
- [ ] Environment variables set:
  - `ANTHROPIC_API_KEY`
  - `MODEL_CHECKPOINT_PATH`
  - `DEVICE` (cuda/cpu)
- [ ] CORS origins configured for frontend
- [ ] Port 8000 available (or changed in config)

### 5. Frontend Requirements
- [ ] Node.js 16+ installed
- [ ] Frontend dependencies installed (`npm install`)
- [ ] API base URL configured in `.env`
- [ ] Emotion store updated with API integration
- [ ] Chat component updated with new endpoints

---

## Deployment Steps

### Backend Deployment

```bash
# 1. Navigate to backend directory
cd backend

# 2. Activate virtual environment
source venv/bin/activate

# 3. Set environment variables
export ANTHROPIC_API_KEY="your-key-here"
export MODEL_CHECKPOINT_PATH="checkpoints/at.pth"
export DEVICE="cuda"  # or "cpu"

# 4. Start the server
python app.py
# OR
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

Expected output:
```
INFO:     Started server process
🚀 Starting MECC Backend API...
Loading emotion model from: checkpoints/at.pth
✅ All services initialized successfully
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### Frontend Deployment

```bash
# 1. Navigate to frontend directory
cd frontend

# 2. Set API URL
echo "VITE_API_BASE_URL=http://localhost:8000" > .env

# 3. Start development server
npm run dev

# 4. For production build
npm run build
npm run preview
```

---

## Post-Deployment Testing

### 1. Automated Tests

```bash
# Run test suite
python test_mvp.py

# Test specific URL
python test_mvp.py --url http://your-server:8000
```

Expected: All tests should pass (✓)

### 2. Manual Tests

#### Test 1: Health Check
```bash
curl http://localhost:8000/health
```
Expected: `{"status": "healthy", "emotion_model": "loaded", ...}`

#### Test 2: Emotion Detection
```bash
curl -X POST "http://localhost:8000/api/v1/emotion/predict" \
  -F "text=I'm so happy today!"
```
Expected: `{"status": "success", "data": {"emotion": "happy", ...}}`

#### Test 3: Chat
```bash
curl -X POST "http://localhost:8000/api/v1/chat/message" \
  -F "text=I'm feeling stressed"
```
Expected: Empathetic response acknowledging stress

#### Test 4: Frontend
1. Open `http://localhost:5173` in browser
2. Type a message and send
3. Verify emotion is detected
4. Verify empathetic response is shown

### 3. Performance Validation

Run 10 predictions and measure latency:
- [ ] Average latency < 500ms (emotion detection only)
- [ ] Average latency < 3s (full chat with LLM)
- [ ] No timeouts or errors
- [ ] Memory usage stable (no leaks)

### 4. Accuracy Validation

Test with known emotional samples:
- [ ] Happy samples mostly classified as happy
- [ ] Sad samples mostly classified as sad
- [ ] Angry samples mostly classified as angry
- [ ] Neutral samples mostly classified as neutral
- [ ] Overall subjective accuracy feels good (>70%)

---

## Production Checklist

### Security
- [ ] API key stored securely (not in code)
- [ ] HTTPS enabled (if deploying publicly)
- [ ] Rate limiting implemented (optional)
- [ ] Input validation in place
- [ ] CORS restricted to known origins

### Monitoring
- [ ] Health check endpoint working
- [ ] Error logging configured
- [ ] Performance metrics tracked
- [ ] API usage monitored

### Scalability
- [ ] Can handle expected load (test with concurrent requests)
- [ ] GPU utilized if available
- [ ] Model loaded once and reused (singleton pattern)
- [ ] Efficient temporary file cleanup

### Documentation
- [ ] API documentation accessible (`/docs`)
- [ ] README with deployment instructions
- [ ] Known issues documented
- [ ] Support contact information provided

---

## Troubleshooting Checklist

### Backend Won't Start

Check:
- [ ] Python version (must be 3.9+)
- [ ] Virtual environment activated
- [ ] All dependencies installed
- [ ] `at.pth` checkpoint exists and is valid
- [ ] `model.py` architecture file exists
- [ ] Port 8000 not already in use
- [ ] Sufficient RAM (8GB minimum)

### Emotion Detection Errors

Check:
- [ ] Model checkpoint loaded successfully (see startup logs)
- [ ] WavLM and RoBERTa downloaded correctly
- [ ] Input text is valid UTF-8
- [ ] Audio files are in supported format
- [ ] GPU memory sufficient (if using CUDA)

### LLM Response Errors

Check:
- [ ] `ANTHROPIC_API_KEY` is set correctly
- [ ] API key is valid and has credits
- [ ] Internet connection is working
- [ ] No rate limiting issues
- [ ] Fallback responses work (if API fails)

### Frontend Connection Errors

Check:
- [ ] Backend is running and accessible
- [ ] CORS origins include frontend URL
- [ ] API base URL is correct in frontend `.env`
- [ ] No network firewall blocking requests
- [ ] Browser console for specific errors

### Performance Issues

Check:
- [ ] GPU is being used (if available): check `nvidia-smi`
- [ ] Model is in eval mode (not training mode)
- [ ] Singleton pattern working (model not reloading)
- [ ] Temporary files being cleaned up
- [ ] No memory leaks (monitor with `htop`)

---

## Validation Metrics

### Functional Metrics
- [ ] Health endpoint: 100% uptime
- [ ] Emotion prediction: >95% success rate
- [ ] Chat completion: >95% success rate
- [ ] Error handling: Graceful degradation

### Performance Metrics
- [ ] P50 latency (emotion): <200ms
- [ ] P95 latency (emotion): <500ms
- [ ] P50 latency (chat): <2s
- [ ] P95 latency (chat): <5s

### Quality Metrics
- [ ] Emotion accuracy: ~70% (matches IEMOCAP test)
- [ ] User satisfaction: Responses feel empathetic
- [ ] No offensive or inappropriate responses
- [ ] Context maintained across conversation

---

## Sign-Off Criteria

MVP is ready for launch when:

✅ All automated tests pass  
✅ Manual testing shows expected behavior  
✅ Performance meets targets  
✅ No critical bugs identified  
✅ Documentation is complete  
✅ Monitoring is in place  

---

## Post-Launch Monitoring

### Week 1
- [ ] Monitor error rates daily
- [ ] Check latency metrics
- [ ] Gather initial user feedback
- [ ] Fix any critical bugs immediately

### Week 2-4
- [ ] Analyze usage patterns
- [ ] Identify most common emotions
- [ ] Collect qualitative feedback
- [ ] Plan feature improvements

### Ongoing
- [ ] Track API usage and costs
- [ ] Monitor model accuracy in production
- [ ] Update documentation based on feedback
- [ ] Plan v2.0 features

---

## Emergency Rollback Plan

If critical issues arise:

1. **Stop the backend:**
   ```bash
   # Find process
   ps aux | grep uvicorn
   
   # Kill it
   kill -9 <PID>
   ```

2. **Check logs:**
   ```bash
   # Review error logs
   tail -f logs/error.log
   ```

3. **Restore previous version:**
   ```bash
   git checkout <previous-commit>
   python app.py
   ```

4. **Notify users:**
   - Display maintenance message in frontend
   - Update status page if available

---

## Success Metrics (30 Days)

After 30 days, evaluate:

- **Usage:**
  - Number of conversations
  - Average conversation length
  - Active users

- **Quality:**
  - User satisfaction score
  - Emotion detection accuracy (user feedback)
  - Response quality rating

- **Technical:**
  - Uptime percentage
  - Average latency
  - Error rate
  - API costs

**Target for MVP Success:**
- 10+ daily active users
- 70%+ positive feedback
- 95%+ uptime
- <3s average response time

---

## Document Version

- Version: 1.0
- Last Updated: February 15, 2026
- Author: MECC Development Team
- Next Review: March 15, 2026
