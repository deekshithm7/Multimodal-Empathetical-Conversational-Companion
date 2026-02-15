# MECC - 100% FREE Implementation Guide

## Response Generation Flow - Detailed Explanation

### Current Flow (Uses Paid APIs)

```
User speaks → Backend detects emotion → 
Call Claude API ($$$) → Generate response → 
Call OpenAI TTS API ($$$) → Convert to speech → 
Return to user
```

**Cost:** ~$0.10 per conversation ❌

---

## FREE Alternative: Complete Replacement

### New Flow (100% Free)

```
User speaks → Backend detects emotion → 
Local LLM (Llama/Mistral) → Generate response → 
Local TTS (Coqui/piper) → Convert to speech → 
Return to user
```

**Cost:** $0 (just compute) ✅

---

## 1. Response Generation - FREE LLM Options

### Option A: Llama 3.2 (Recommended for MVP)

**Why Llama 3.2:**
- ✅ Completely free (Meta open source)
- ✅ Good quality responses
- ✅ Runs on your RTX 3050 (4GB VRAM)
- ✅ Fast inference (~1-2s per response)
- ✅ Instruction-tuned for conversations

**Setup:**

```python
# services/free_llm_service.py
"""
FREE LLM Service using Llama 3.2 via Ollama
No API costs, runs locally on your GPU
"""

import requests
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FreeLLMService:
    """
    Free LLM service using Llama 3.2 via Ollama.
    Completely free, runs locally on GPU.
    """
    
    def __init__(self, model_name: str = "llama3.2:3b"):
        """
        Initialize free LLM service.
        
        Models available (all FREE):
        - llama3.2:1b - Fastest (1B params, ~1GB VRAM)
        - llama3.2:3b - Recommended (3B params, ~2GB VRAM) ← BEST FOR MVP
        - llama3.1:8b - Best quality (8B params, ~5GB VRAM, won't fit RTX 3050)
        - mistral:7b - Alternative (7B params, ~4GB VRAM)
        - phi3:3.8b - Compact (3.8B params, ~2.5GB VRAM)
        """
        self.model_name = model_name
        self.base_url = "http://localhost:11434"  # Ollama default port
        
        logger.info(f"✅ Free LLM Service initialized with {model_name}")
        logger.info("💡 No API costs - running locally!")
    
    def generate_empathetic_response(
        self,
        user_message: str,
        detected_emotion: str,
        emotion_confidence: float,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate empathetic response using local LLM.
        
        Args:
            user_message: What the user said
            detected_emotion: neutral/happy/angry/sad
            emotion_confidence: 0-1 confidence score
            conversation_history: Previous messages
        
        Returns:
            Empathetic response text
        """
        
        # Build system prompt with emotion awareness
        system_prompt = self._build_system_prompt(detected_emotion, emotion_confidence)
        
        # Build conversation context
        messages = []
        
        if conversation_history:
            # Add last 5 messages for context (avoid too long prompts)
            for msg in conversation_history[-5:]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current message
        messages.append({
            "role": "user",
            "content": user_message
        })
        
        try:
            # Call Ollama API (local, free)
            response = requests.post(
                f"{self.base_url}/api/chat",
                json={
                    "model": self.model_name,
                    "messages": [
                        {"role": "system", "content": system_prompt},
                        *messages
                    ],
                    "stream": False,
                    "options": {
                        "temperature": 0.7,  # Slightly creative
                        "top_p": 0.9,
                        "max_tokens": 150    # Keep responses concise
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["message"]["content"].strip()
                
                logger.info(f"Generated response: {assistant_message[:50]}...")
                return assistant_message
            else:
                logger.error(f"Ollama API error: {response.status_code}")
                return self._get_fallback_response(detected_emotion)
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._get_fallback_response(detected_emotion)
    
    def _build_system_prompt(self, emotion: str, confidence: float) -> str:
        """
        Build emotion-aware system prompt.
        This is KEY to getting good empathetic responses!
        """
        
        confidence_level = "high" if confidence > 0.75 else "moderate"
        
        emotion_context = {
            "happy": "The user is feeling positive and upbeat. Share in their joy and be encouraging.",
            "sad": "The user is feeling down. Be compassionate, validate their feelings, and offer gentle support.",
            "angry": "The user is frustrated or upset. Stay calm, validate their frustration, and be understanding.",
            "neutral": "The user's emotional state is calm. Be warm and open, follow their conversational lead."
        }
        
        context = emotion_context.get(emotion, "Be supportive and understanding.")
        
        system_prompt = f"""You are an empathetic AI companion designed to provide emotional support.

DETECTED EMOTION: {emotion.upper()} (confidence: {confidence_level}, {confidence:.0%})
CONTEXT: {context}

YOUR ROLE:
- Be warm, supportive, and genuinely empathetic
- Keep responses SHORT (2-3 sentences max)
- Acknowledge their feelings authentically
- Don't be robotic or overly formal
- Use natural, conversational language
- Don't force solutions unless asked

EMOTION-SPECIFIC GUIDELINES:
- If ANGRY: Stay calm, validate frustration, don't dismiss
- If SAD: Show compassion, acknowledge pain, gentle support
- If HAPPY: Share joy, be encouraging, maintain positive energy
- If NEUTRAL: Be warm and open, follow their lead

IMPORTANT:
- Keep it concise (2-3 sentences)
- Be human-like and natural
- Don't mention you're an AI
- Focus on emotional support, not advice"""

        return system_prompt
    
    def _get_fallback_response(self, emotion: str) -> str:
        """
        Fallback responses if LLM fails.
        """
        fallbacks = {
            "happy": "That's wonderful! I'm glad you're feeling good. What's bringing you joy?",
            "sad": "I hear you, and I'm here for you. Sometimes things feel heavy. Want to talk about it?",
            "angry": "I can sense your frustration, and that's completely valid. What's going on?",
            "neutral": "I'm here and listening. What's on your mind today?"
        }
        
        return fallbacks.get(emotion, "I'm here to support you. How can I help?")
    
    def generate_session_summary(
        self,
        conversation_history: List[Dict],
        emotion_timeline: List[Dict]
    ) -> str:
        """
        Generate conversation summary using local LLM.
        """
        
        # Format conversation
        convo_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history[-10:]  # Last 10 messages
        ])
        
        # Format emotions
        emotions_text = " → ".join([
            f"{e['emotion']}({e['confidence']:.0%})"
            for e in emotion_timeline
        ])
        
        prompt = f"""Summarize this empathetic support conversation in 2-3 paragraphs.

Conversation:
{convo_text}

Emotional journey:
{emotions_text}

Create a warm, supportive summary that:
1. Captures what was discussed
2. Notes the emotional journey
3. Ends with an encouraging note

Keep it brief and personal."""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {"max_tokens": 200}
                },
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()["response"].strip()
            else:
                return "Thank you for sharing this time with me. Take care! 💙"
        
        except:
            return "Thank you for sharing this time with me. Take care! 💙"


# Singleton
_free_llm_service = None

def get_free_llm_service(model_name: str = "llama3.2:3b"):
    """Get free LLM service instance"""
    global _free_llm_service
    
    if _free_llm_service is None:
        _free_llm_service = FreeLLMService(model_name=model_name)
    
    return _free_llm_service
```

**Installation:**

```bash
# 1. Install Ollama (one-time setup)
# Windows:
# Download from: https://ollama.com/download/windows
# Run installer

# Mac/Linux:
curl -fsSL https://ollama.com/install.sh | sh

# 2. Pull Llama 3.2 model (one-time, ~2GB download)
ollama pull llama3.2:3b

# 3. Verify it's running
ollama list

# 4. Test it
ollama run llama3.2:3b "Hello, how are you?"
```

**That's it!** No API keys, no costs, runs forever for free.

---

## 2. Text-to-Speech - FREE Options

### Option A: Piper TTS (Recommended - Fastest)

**Why Piper:**
- ✅ Completely free
- ✅ Fast (real-time on CPU)
- ✅ Good quality voices
- ✅ Multiple voices available
- ✅ Works offline

**Setup:**

```python
# services/free_tts_service.py
"""
FREE Text-to-Speech using Piper
No API costs, runs locally
"""

import subprocess
import tempfile
import os
import logging
from typing import Optional

logger = logging.getLogger(__name__)


class FreeTTSService:
    """
    Free TTS using Piper.
    Completely free, runs locally.
    """
    
    def __init__(self, voice: str = "en_US-lessac-medium"):
        """
        Initialize Piper TTS.
        
        Available voices (all FREE):
        - en_US-lessac-medium - Clear, neutral (RECOMMENDED) ← BEST
        - en_US-amy-medium - Friendly female
        - en_US-ryan-medium - Male voice
        - en_GB-alan-medium - British male
        - en_US-libritts-high - High quality (slower)
        """
        self.voice = voice
        self.piper_path = "piper"  # Assumes piper in PATH
        
        # Download voice model on first use (automatic)
        logger.info(f"✅ Free TTS initialized with voice: {voice}")
        logger.info("💡 No API costs - running locally!")
    
    def generate_speech(
        self,
        text: str,
        emotion: Optional[str] = None
    ) -> str:
        """
        Convert text to speech using Piper.
        
        Args:
            text: Text to convert
            emotion: Detected emotion (for voice selection)
        
        Returns:
            Path to generated audio file (WAV)
        """
        
        # Select voice based on emotion (optional)
        voice = self._select_voice(emotion)
        
        # Create temp output file
        output_fd, output_path = tempfile.mkstemp(suffix='.wav')
        os.close(output_fd)
        
        try:
            # Run Piper (pipes text to piper command)
            command = [
                'piper',
                '--model', voice,
                '--output_file', output_path
            ]
            
            process = subprocess.Popen(
                command,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            
            # Send text to stdin
            stdout, stderr = process.communicate(input=text, timeout=30)
            
            if process.returncode == 0:
                logger.info(f"Generated speech: {output_path}")
                return output_path
            else:
                raise Exception(f"Piper failed: {stderr}")
        
        except Exception as e:
            logger.error(f"TTS generation failed: {e}")
            # Cleanup on failure
            if os.path.exists(output_path):
                os.unlink(output_path)
            raise
    
    def _select_voice(self, emotion: Optional[str]) -> str:
        """
        Select voice based on emotion.
        (All voices are same model, so we just use default for now)
        """
        # For MVP, use same voice for all emotions
        # Can add multiple voices later if desired
        return self.voice


# Singleton
_free_tts_service = None

def get_free_tts_service(voice: str = "en_US-lessac-medium"):
    """Get free TTS service instance"""
    global _free_tts_service
    
    if _free_tts_service is None:
        _free_tts_service = FreeTTSService(voice=voice)
    
    return _free_tts_service
```

**Installation:**

```bash
# Windows (using pip):
pip install piper-tts

# Download voice model (one-time, ~50MB):
piper --model en_US-lessac-medium --download

# Test it:
echo "Hello, this is a test" | piper --model en_US-lessac-medium --output_file test.wav
```

### Option B: Coqui TTS (Better Quality, Slower)

```python
# Alternative: Coqui TTS (if you want better quality)
class CoquiTTSService:
    """
    Free TTS using Coqui TTS.
    Better quality but slower than Piper.
    """
    
    def __init__(self):
        from TTS.api import TTS
        
        # Load free TTS model (downloads on first use)
        self.tts = TTS(model_name="tts_models/en/ljspeech/tacotron2-DDC")
        
        logger.info("✅ Coqui TTS initialized")
    
    def generate_speech(self, text: str, emotion: Optional[str] = None) -> str:
        # Create output file
        output_path = tempfile.mktemp(suffix='.wav')
        
        # Generate speech
        self.tts.tts_to_file(text=text, file_path=output_path)
        
        return output_path
```

**Installation:**

```bash
pip install TTS

# Model downloads automatically on first use (~100MB)
```

---

## 3. Speech-to-Text - FREE (Already Free!)

**Whisper is ALREADY FREE!** ✅

You can use it locally (no API needed):

```python
# services/whisper_service.py (already provided)
# Uses local Whisper model - completely free
import whisper

model = whisper.load_model("small")  # Free, runs locally
result = model.transcribe("audio.wav")
```

**No changes needed!** Your existing Whisper implementation is free.

---

## Complete FREE Stack Summary

| Component | FREE Solution | Cost | Setup Time |
|-----------|--------------|------|------------|
| Emotion Detection | Your trained model | $0 | ✅ Already done |
| Speech-to-Text | Whisper (local) | $0 | ✅ Already done |
| LLM Responses | Llama 3.2 (Ollama) | $0 | 5 minutes |
| Text-to-Speech | Piper TTS | $0 | 5 minutes |
| Database | PostgreSQL | $0 | ✅ Already setup |

**Total Cost:** $0 forever! ✅

---

## Updated Response Generation Flow (FREE)

### Complete Flow with FREE Tools

```
┌─────────────────────────────────────────────────────────┐
│  1. User speaks (video/audio recording)                │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  2. Extract audio from video (ffmpeg - FREE)           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  3. Transcribe audio (Whisper local - FREE)            │
│     Audio → Text: "I'm feeling stressed about work"    │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  4. Extract features (Your models - FREE)               │
│     - Audio → WavLM → 768-dim                          │
│     - Text → RoBERTa → 768-dim                         │
│     - Concatenate → 1536-dim                           │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  5. Predict emotion (Your trained model - FREE)        │
│     Output: {emotion: "sad", confidence: 0.82}         │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  6. Retrieve conversation history (PostgreSQL - FREE)  │
│     Get last 5-10 messages for context                 │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  7. Generate response (Llama 3.2 via Ollama - FREE)   │
│                                                         │
│  Input to Llama:                                       │
│  System: "User is SAD (82% confidence).               │
│           Be compassionate and supportive."            │
│                                                         │
│  History:                                              │
│  - User: "Hi, how are you?"                           │
│  - Assistant: "Hello! I'm here for you."              │
│                                                         │
│  Current:                                              │
│  - User: "I'm feeling stressed about work"            │
│                                                         │
│  Llama generates:                                      │
│  "I hear you. Work stress can feel overwhelming.      │
│   You're not alone in feeling this way. What's        │
│   weighing most heavily on your mind right now?"      │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  8. Convert to speech (Piper TTS - FREE)               │
│     Text → Audio WAV file                              │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  9. Save to database (PostgreSQL - FREE)               │
│     - Save user message + emotion                      │
│     - Save assistant response + audio path             │
└────────────────┬────────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────────┐
│  10. Return to frontend                                 │
│      {                                                  │
│        user_message: "I'm feeling stressed...",        │
│        user_emotion: {emotion: "sad", conf: 0.82},     │
│        assistant_response: "I hear you. Work...",      │
│        assistant_audio_url: "/audio/response.wav"      │
│      }                                                  │
└─────────────────────────────────────────────────────────┘
```

---

## Installation Guide - FREE Stack

### Step 1: Install Ollama (LLM)

```bash
# Windows:
# Download from: https://ollama.com/download
# Run installer

# After installation:
ollama pull llama3.2:3b

# Test:
ollama run llama3.2:3b "Tell me something encouraging"
```

### Step 2: Install Piper (TTS)

```bash
# Install via pip:
pip install piper-tts

# Download voice:
piper --model en_US-lessac-medium --download

# Test:
echo "Hello world" | piper --model en_US-lessac-medium --output_file test.wav
```

### Step 3: Update Backend Code

```bash
# Copy new FREE services:
cp free_llm_service.py backend/services/
cp free_tts_service.py backend/services/

# Update app_v2.py to use FREE services:
# Change:
from services.llm_service import get_llm_service
# To:
from services.free_llm_service import get_free_llm_service

# Change:
from services.tts_service import get_tts_service
# To:
from services.free_tts_service import get_free_tts_service
```

### Step 4: Update Environment Variables

```bash
# .env (NO API KEYS NEEDED!)
DATABASE_URL=postgresql://user:pass@localhost/mecc_db
MODEL_CHECKPOINT_PATH=checkpoints/at.pth
DEVICE=cuda

# FREE tools config:
OLLAMA_MODEL=llama3.2:3b
PIPER_VOICE=en_US-lessac-medium

# Remove these (not needed anymore):
# ANTHROPIC_API_KEY=...
# OPENAI_API_KEY=...
```

---

## Response Quality Comparison

| Feature | Paid (Claude) | FREE (Llama 3.2) |
|---------|---------------|------------------|
| Response Quality | ⭐⭐⭐⭐⭐ Excellent | ⭐⭐⭐⭐ Very Good |
| Empathy | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| Speed | ~1-2s | ~1-2s (similar!) |
| Context Understanding | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Cost** | **$0.01 per response** | **$0 (FREE!)** |

**Verdict:** Llama 3.2 is 80-90% as good as Claude, but completely FREE! Perfect for MVP.

---

## TTS Quality Comparison

| Feature | Paid (OpenAI) | FREE (Piper) |
|---------|---------------|--------------|
| Voice Quality | ⭐⭐⭐⭐⭐ Very Natural | ⭐⭐⭐⭐ Natural |
| Speed | ~1s | ~0.5s (faster!) |
| Emotion Control | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **Cost** | **$0.075 per response** | **$0 (FREE!)** |

**Verdict:** Piper is 70-80% as good as OpenAI, but FREE and faster!

---

## Complete Cost Comparison

### Per Conversation (10 message exchanges):

| Component | Paid Stack | FREE Stack |
|-----------|-----------|------------|
| Transcription | $0.01 | $0 (Whisper local) |
| LLM (10 responses) | $0.10 | $0 (Llama 3.2) |
| TTS (10 responses) | $0.75 | $0 (Piper) |
| **TOTAL** | **$0.86** | **$0** ✅ |

### Monthly Cost (100 users, 10 conversations each):

| Stack | Monthly Cost |
|-------|-------------|
| Paid (Claude + OpenAI) | **$860/month** ❌ |
| FREE (Llama + Piper) | **$0/month** ✅ |

**Savings:** $10,320 per year! 💰

---

## System Requirements (Updated)

### Hardware Needed:

**Your Current Setup:**
- ✅ RTX 3050 (4GB VRAM) - Perfect for Llama 3.2-3B!
- ✅ 16GB RAM
- ✅ Windows

**Storage:**
- Whisper small: ~466 MB ✅ (already have)
- Llama 3.2-3B: ~2 GB (new)
- Piper voice: ~50 MB (new)
- **Total new: ~2 GB**

**Your RTX 3050 can easily run:**
- ✅ Llama 3.2-3B (~2GB VRAM)
- ✅ Your emotion model (~1GB VRAM)
- ✅ Whisper small (~1GB VRAM when active)
- **Total: ~4GB fits perfectly!**

---

## Updated File Structure (FREE)

```
backend/
├── services/
│   ├── emotion_service.py      # Your model (FREE) ✅
│   ├── whisper_service.py      # Whisper (FREE) ✅
│   ├── free_llm_service.py     # Llama 3.2 (FREE) ← NEW
│   ├── free_tts_service.py     # Piper TTS (FREE) ← NEW
│   ├── video_processor.py      # ffmpeg (FREE) ✅
│   └── database.py             # PostgreSQL (FREE) ✅
├── app_free.py                  # Updated API (FREE) ← NEW
├── checkpoints/
│   └── at.pth                  # Your model (FREE) ✅
└── requirements_free.txt        # No paid APIs! ← NEW
```

---

## Next Steps

1. **Install Ollama** (5 minutes)
   ```bash
   # Download from ollama.com
   ollama pull llama3.2:3b
   ```

2. **Install Piper** (5 minutes)
   ```bash
   pip install piper-tts
   piper --model en_US-lessac-medium --download
   ```

3. **Test FREE stack** (10 minutes)
   ```bash
   # Test LLM:
   ollama run llama3.2:3b "Be empathetic to someone who is sad"
   
   # Test TTS:
   echo "I'm here to support you" | piper --output_file test.wav
   ```

4. **Update backend** (30 minutes)
   - Copy new FREE service files
   - Update app.py imports
   - Remove API key requirements

5. **Deploy & Test** (1 hour)
   - Run complete system
   - Test conversation flow
   - Verify 100% FREE operation!

---

## Summary

**Question:** How does response generation work?  
**Answer:** 

1. Detect emotion (your model)
2. Build emotion-aware prompt
3. Add conversation history
4. Generate response with LLM
5. Convert response to speech

**Question:** Can we use FREE models everywhere?  
**Answer:** **YES - 100% FREE!** ✅

- LLM: Llama 3.2 (FREE, good quality)
- TTS: Piper (FREE, fast, natural)
- STT: Whisper (already FREE)
- Everything else: Already FREE

**Total Cost:** $0 forever! 🎉

Let me create the actual implementation files next!
