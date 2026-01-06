import { useEffect } from 'react';
import { ChatInterface } from './components/Chat/ChatInterface';
import { WaveVisualizer } from './components/AudioVisualizer/WaveVisualizer';
import { useEmotionStore } from './store/useEmotionStore';
import { useSpeechRecognition } from './hooks/useSpeechRecognition';
import { useWebcamRecorder } from './hooks/useWebcamRecorder';

function App() {
  const { currentEmotion, setListening, isListening, addMessage, setEmotion } = useEmotionStore();
  const { transcript, isListening: recognitionActive, startListening, stopListening, resetTranscript } = useSpeechRecognition();

  // Webcam Recording Hook (Records Camera + Audio)
  const { isRecordingSession, startRecording, stopRecording } = useWebcamRecorder();

  // Sync recognition state with store
  useEffect(() => {
    setListening(recognitionActive);
  }, [recognitionActive, setListening]);

  // Combined Handler: Toggles both "Listening" (AI) and "Recording" (Camera)
  const toggleSession = () => {
    if (recognitionActive || isRecordingSession) {
      // STOP everything
      stopListening();
      stopRecording();
    } else {
      // START everything
      startListening();
      startRecording();
    }
  };

  // Handle transcript processing
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

      setTimeout(() => {
        const responses: Record<string, string> = {
          happy: "That sounds wonderful. I'm glad you're feeling good.",
          sad: "I'm sorry to hear that. I'm here for you.",
          angry: "It sounds like you're frustrated. Let's talk about it.",
          neutral: "I see. Tell me more."
        };
        addMessage({ id: (Date.now() + 1).toString(), sender: 'companion', text: responses[detectedEmotion] || "I'm listening." });
      }, 1000);
    }
  }, [recognitionActive, transcript, addMessage, currentEmotion, resetTranscript, setEmotion]);


  useEffect(() => {
    // Update CSS variables for Dark Therapeutic Theme
    const root = document.documentElement;
    switch (currentEmotion) {
      case 'happy':
        // Warm Dark Gold/Amber
        root.style.setProperty('--theme-bg', '#1a1612');
        break;
      case 'sad':
        // Deep Deep Blue/Slate
        root.style.setProperty('--theme-bg', '#0f131a');
        break;
      case 'angry':
        // Deep Maroon/Charcoal
        root.style.setProperty('--theme-bg', '#1a1010');
        break;
      default: // neutral
        // Pure Deep Void
        root.style.setProperty('--theme-bg', '#0a0a0c');
    }
  }, [currentEmotion]);

  return (
    <div className="h-screen w-screen overflow-hidden relative bg-[var(--theme-bg)] transition-colors duration-1000 flex flex-col items-center justify-between">

      {/* Visualizer Area (Full background) */}
      <div className="absolute inset-0 z-0 pointer-events-none">
        <WaveVisualizer isListening={isListening} emotion={currentEmotion} />
      </div>

      {/* Header (Clean, no extra buttons) */}
      <div className="z-10 w-full max-w-3xl p-6 text-center mt-8">
        <h1 className="text-3xl font-serif text-slate-200 tracking-wide opacity-90 text-shadow-glow">MECC</h1>
        <p className="text-xs text-slate-500 uppercase tracking-widest mt-1">Empathetic Companion</p>
      </div>

      {/* Main Interaction Area */}
      <div className="z-10 w-full max-w-2xl px-4 pb-8 mb-4">
        <ChatInterface
          onMicClick={toggleSession}
          isRecording={recognitionActive || isRecordingSession}
        />
      </div>

    </div>
  );
}

export default App;
