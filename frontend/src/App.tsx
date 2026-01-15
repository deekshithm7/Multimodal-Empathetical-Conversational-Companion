import { useEffect, useState, useRef } from 'react';
import { AnimatePresence } from 'framer-motion';
import { ChatInterface } from './components/Chat/ChatInterface';
import { WaveVisualizer } from './components/AudioVisualizer/WaveVisualizer';
import { AvatarScene } from './components/Avatar/Scene';
import { VanishingCamera } from './components/Camera/VanishingCamera';
import { SessionSummary } from './components/Dashboard/SessionSummary';
import { useEmotionStore } from './store/useEmotionStore';
import { useSpeechRecognition } from './hooks/useSpeechRecognition';
import { useWebcamRecorder } from './hooks/useWebcamRecorder';

function App() {
  const { currentEmotion, setListening, isListening, addMessage, setEmotion, aiSpeaking, setAiSpeaking } = useEmotionStore();
  const { transcript, isListening: recognitionActive, startListening, stopListening, resetTranscript } = useSpeechRecognition();

  // Webcam Recording Hook (Records Camera + Audio)
  const { isRecordingSession, startRecording, stopRecording, stream } = useWebcamRecorder();

  // Dashboard Logic
  const [showSummary, setShowSummary] = useState(false);
  const wasRecordingRef = useRef(false);

  // Sync recognition state with store
  useEffect(() => {
    setListening(recognitionActive);
  }, [recognitionActive, setListening]);

  // Track recording state to trigger summary
  useEffect(() => {
    if (isRecordingSession) {
      wasRecordingRef.current = true;
    } else if (wasRecordingRef.current) {
      // Just stopped recording
      wasRecordingRef.current = false;
      setShowSummary(true);
    }
  }, [isRecordingSession]);

  // Combined Handler: Toggles both "Listening" (AI) and "Recording" (Camera)
  const toggleSession = () => {
    if (recognitionActive || isRecordingSession) {
      stopListening();
      stopRecording();
    } else {
      setShowSummary(false); // Hide summary if starting new
      startListening();
      startRecording();
    }
  };

  // Handle transcript processing & AI Mock Response
  useEffect(() => {
    if (!recognitionActive && transcript.trim()) {
      const text = transcript.toLowerCase();
      let detectedEmotion = currentEmotion;
      if (text.includes('happy') || text.includes('good') || text.includes('joy')) detectedEmotion = 'happy';
      else if (text.includes('sad') || text.includes('bad') || text.includes('cry')) detectedEmotion = 'sad';
      else if (text.includes('angry') || text.includes('hate') || text.includes('mad')) detectedEmotion = 'angry';

      setEmotion(detectedEmotion);
      addMessage({ id: Date.now().toString(), sender: 'user', text: transcript });
      resetTranscript();

      // Simulate AI Processing & Response
      setTimeout(() => {
        const responses: Record<string, string> = {
          happy: "That sounds wonderful. I'm glad you're feeling good.",
          sad: "I'm sorry to hear that. I'm here for you.",
          angry: "It sounds like you're frustrated. Let's talk about it.",
          neutral: "I see. Tell me more."
        };

        const responseText = responses[detectedEmotion] || "I'm listening.";
        addMessage({ id: (Date.now() + 1).toString(), sender: 'companion', text: responseText });

        // Trigger AI Speaking Visuals
        setAiSpeaking(true);
        // Mock speech duration based on text length
        setTimeout(() => {
          setAiSpeaking(false);
        }, 3000);

      }, 1000);
    }
  }, [recognitionActive, transcript, addMessage, currentEmotion, resetTranscript, setEmotion, setAiSpeaking]);


  useEffect(() => {
    // Update CSS variables for Dark Therapeutic Theme
    const root = document.documentElement;
    switch (currentEmotion) {
      case 'happy': root.style.setProperty('--theme-bg', '#1a1612'); break; // Warm Amber Dark
      case 'sad': root.style.setProperty('--theme-bg', '#0f131a'); break; // Deep Blue Dark
      case 'angry': root.style.setProperty('--theme-bg', '#1a1010'); break; // Deep Red Dark
      default: root.style.setProperty('--theme-bg', '#0a0a0c'); // Void
    }
  }, [currentEmotion]);

  return (
    <div className="h-screen w-screen overflow-hidden relative bg-[var(--theme-bg)] transition-colors duration-[4000ms] flex flex-col items-center justify-between">

      {/* 1. Ambient Background (WaveVisualizer) - Ducking handled internally */}
      <div className="absolute inset-0 z-0 pointer-events-none opacity-60">
        <WaveVisualizer isListening={isListening} isAiSpeaking={aiSpeaking} emotion={currentEmotion} />
      </div>

      {/* 2. Central Avatar (The "Analyst") */}
      <div className="absolute inset-0 z-10 flex items-center justify-center pointer-events-none">
        <div className="w-[400px] h-[400px] opacity-90 transition-opacity duration-1000">
          <AvatarScene />
        </div>
      </div>

      {/* 3. Header */}
      <div className="z-20 w-full max-w-3xl p-6 text-center mt-8 pointer-events-none">
        <h1 className="text-3xl font-serif text-slate-200 tracking-wide opacity-80 text-shadow-glow">MECC</h1>
        <p className="text-xs text-slate-500 uppercase tracking-widest mt-1">Empathetic Companion</p>
      </div>

      {/* 4. Interaction Area */}
      <div className="z-20 w-full max-w-2xl px-4 pb-8 mb-4">
        <ChatInterface
          onMicClick={toggleSession}
          isRecording={recognitionActive || isRecordingSession}
        />
      </div>

      {/* 5. Privacy-First Webcam View */}
      <VanishingCamera stream={stream} />

      {/* 6. Session Summary Dashboard */}
      <AnimatePresence>
        {showSummary && <SessionSummary onClose={() => setShowSummary(false)} />}
      </AnimatePresence>

    </div>
  );
}

export default App;
