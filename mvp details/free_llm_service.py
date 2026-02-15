"""
FREE LLM Service - Using Llama 3.2 via Ollama
100% Free, No API Costs, Runs Locally on Your GPU
"""

import requests
import json
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)


class FreeLLMService:
    """
    Free LLM service using Llama 3.2 via Ollama.
    
    Benefits:
    - Completely free (no API costs)
    - Runs locally on your RTX 3050
    - Good quality empathetic responses
    - Fast inference (~1-2s)
    - Private (data never leaves your machine)
    """
    
    def __init__(self, model_name: str = "llama3.2:3b", base_url: str = "http://localhost:11434"):
        """
        Initialize free LLM service.
        
        Args:
            model_name: Ollama model to use
                       - llama3.2:1b - Fastest (~1GB VRAM)
                       - llama3.2:3b - Recommended (~2GB VRAM) ← BEST FOR YOUR RTX 3050
                       - mistral:7b - Alternative (~4GB VRAM, slower)
            base_url: Ollama API endpoint (default: localhost:11434)
        """
        self.model_name = model_name
        self.base_url = base_url
        
        # Verify Ollama is running
        try:
            response = requests.get(f"{base_url}/api/tags", timeout=5)
            if response.status_code == 200:
                logger.info(f"✅ Connected to Ollama at {base_url}")
            else:
                raise ConnectionError("Ollama not responding")
        except Exception as e:
            logger.error(f"❌ Cannot connect to Ollama: {e}")
            logger.error("Make sure Ollama is running: 'ollama serve'")
            raise
        
        logger.info(f"✅ Free LLM Service initialized with {model_name}")
        logger.info("💰 No API costs - running locally on your GPU!")
    
    def generate_empathetic_response(
        self,
        user_message: str,
        detected_emotion: str,
        emotion_confidence: float,
        conversation_history: Optional[List[Dict]] = None
    ) -> str:
        """
        Generate empathetic response using local Llama model.
        
        Args:
            user_message: What the user said
            detected_emotion: neutral/happy/angry/sad
            emotion_confidence: 0-1 confidence score
            conversation_history: List of previous messages
        
        Returns:
            Empathetic response string
        """
        
        # Build emotion-aware system prompt
        system_prompt = self._build_system_prompt(detected_emotion, emotion_confidence)
        
        # Build message history
        messages = []
        
        if conversation_history:
            # Add last 5 messages for context (keep prompt short)
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
        
        logger.info(f"Generating response for emotion: {detected_emotion} ({emotion_confidence:.0%})")
        
        try:
            # Call Ollama API
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
                        "temperature": 0.7,      # Slightly creative
                        "top_p": 0.9,            # Nucleus sampling
                        "num_predict": 150,      # Max tokens (keep responses concise)
                        "stop": ["\n\n", "User:", "Assistant:"]  # Stop sequences
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                result = response.json()
                assistant_message = result["message"]["content"].strip()
                
                # Clean up response
                assistant_message = self._clean_response(assistant_message)
                
                logger.info(f"Generated: '{assistant_message[:50]}...'")
                return assistant_message
            else:
                logger.error(f"Ollama API error: {response.status_code} - {response.text}")
                return self._get_fallback_response(detected_emotion)
        
        except requests.Timeout:
            logger.error("Ollama request timeout")
            return self._get_fallback_response(detected_emotion)
        
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return self._get_fallback_response(detected_emotion)
    
    def _build_system_prompt(self, emotion: str, confidence: float) -> str:
        """
        Build emotion-aware system prompt.
        This is KEY to getting good empathetic responses!
        """
        
        confidence_level = "high" if confidence > 0.75 else "moderate" if confidence > 0.5 else "low"
        
        emotion_guidance = {
            "happy": """The user is feeling positive and joyful.
- Share in their happiness genuinely
- Be encouraging and supportive
- Match their positive energy
- Example: "That's wonderful! I'm so glad you're feeling good."
""",
            "sad": """The user is feeling down or sad.
- Be compassionate and gentle
- Validate their feelings without toxic positivity
- Offer support, not immediate solutions
- Sit with them in the difficult moment
- Example: "I hear you. It's okay to feel this way. I'm here with you."
""",
            "angry": """The user is frustrated or angry.
- Stay calm and centered
- Validate their frustration without judgment
- Don't dismiss or minimize their feelings
- Avoid phrases like "calm down"
- Example: "I can feel your frustration, and that's completely valid. What's going on?"
""",
            "neutral": """The user's emotional state is calm or unclear.
- Be warm and open
- Follow their conversational lead
- Don't force emotional content
- Be naturally supportive
- Example: "I'm here and listening. What's on your mind?"
"""
        }
        
        guidance = emotion_guidance.get(emotion, emotion_guidance["neutral"])
        
        system_prompt = f"""You are a warm, empathetic AI companion providing emotional support.

DETECTED EMOTION: {emotion.upper()}
CONFIDENCE: {confidence_level} ({confidence:.0%})

{guidance}

CORE PRINCIPLES:
- Keep responses SHORT (2-3 sentences maximum)
- Be genuine and human-like, not robotic
- Use natural conversational language
- Acknowledge feelings authentically
- Don't be overly formal or clinical
- Don't mention you're an AI
- Don't force advice unless asked

WHAT TO AVOID:
- Long responses (keep it brief!)
- Clichés ("everything happens for a reason")
- Toxic positivity ("just look on the bright side")
- Immediate problem-solving
- Being dismissive of feelings
- Robotic or template-like language

YOUR GOAL: Be a supportive friend who truly listens and cares."""

        return system_prompt
    
    def _clean_response(self, text: str) -> str:
        """Clean up LLM response"""
        # Remove extra whitespace
        text = " ".join(text.split())
        
        # Remove common artifacts
        text = text.replace("Assistant:", "").replace("User:", "")
        
        # Limit length (in case model ignores token limit)
        sentences = text.split(". ")
        if len(sentences) > 3:
            text = ". ".join(sentences[:3]) + "."
        
        return text.strip()
    
    def _get_fallback_response(self, emotion: str) -> str:
        """
        Fallback responses if LLM fails.
        Simple but empathetic responses for each emotion.
        """
        fallbacks = {
            "happy": "That's wonderful! I'm so glad you're feeling good. What's bringing you joy today?",
            "sad": "I hear you, and I'm here for you. It's okay to feel this way. Want to talk about what's weighing on you?",
            "angry": "I can sense your frustration, and that's completely valid. What's going on that's bothering you?",
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
        
        Args:
            conversation_history: Full conversation
            emotion_timeline: Emotion progression
        
        Returns:
            Summary text
        """
        
        # Format conversation (last 10 messages)
        convo_text = "\n".join([
            f"{msg['role'].upper()}: {msg['content']}"
            for msg in conversation_history[-10:]
        ])
        
        # Format emotion timeline
        emotions_text = " → ".join([
            f"{e['emotion']}({e['confidence']:.0%})"
            for e in emotion_timeline
        ])
        
        prompt = f"""Summarize this empathetic support conversation in 2-3 brief paragraphs.

Conversation:
{convo_text}

Emotional Journey:
{emotions_text}

Create a warm, supportive summary that:
1. Captures the main topics discussed
2. Notes how emotions evolved
3. Ends with an encouraging message

Keep it personal and concise (under 150 words)."""

        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "num_predict": 200
                    }
                },
                timeout=30
            )
            
            if response.status_code == 200:
                summary = response.json()["response"].strip()
                return self._clean_response(summary)
            else:
                return self._get_default_summary()
        
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return self._get_default_summary()
    
    def _get_default_summary(self) -> str:
        """Default summary if generation fails"""
        return "Thank you for sharing this time with me. I appreciated listening and being here with you. Remember, your feelings are valid and it's okay to reach out when you need support. Take care of yourself. 💙"


# Singleton instance
_free_llm_service = None

def get_free_llm_service(
    model_name: str = "llama3.2:3b",
    base_url: str = "http://localhost:11434"
) -> FreeLLMService:
    """
    Get or create the global free LLM service instance.
    
    Args:
        model_name: Ollama model to use
        base_url: Ollama API endpoint
    
    Returns:
        FreeLLMService instance
    """
    global _free_llm_service
    
    if _free_llm_service is None:
        _free_llm_service = FreeLLMService(
            model_name=model_name,
            base_url=base_url
        )
    
    return _free_llm_service
