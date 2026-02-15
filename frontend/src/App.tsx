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
  const { currentEmotion, setListening, isListening, startSession, sendMessage, conversationId, isLoading } = useEmotionStore();
  const { transcript, isListening: recognitionActive, startListening, stopListening, resetTranscript } = useSpeechRecognition();

  // Webcam Recording Hook (Records Camera + Audio)
  const { isRecordingSession, startRecording, stopRecording, stream, recordedBlob } = useWebcamRecorder();

  // Dashboard Logic
  const [showSummary, setShowSummary] = useState(false);
  const wasRecordingRef = useRef(false);
  const sessionInitializedRef = useRef(false);

  // Start backend session on mount (only once, even in StrictMode)
  useEffect(() => {
    if (!sessionInitializedRef.current) {
      sessionInitializedRef.current = true;
      startSession();
    }
  }, [startSession]);

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

  // Send video blob to backend when recording stops
  useEffect(() => {
    if (recordedBlob && conversationId) {
      console.log('✅ Sending video blob to backend:', {
        blobSize: recordedBlob.size,
        conversationId
      });

      // Send the video blob with a placeholder text
      // Backend will extract audio and transcribe it
      sendMessage('', recordedBlob);
    }
  }, [recordedBlob, conversationId, sendMessage]);


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
        <WaveVisualizer isListening={isListening} emotion={currentEmotion} />
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
