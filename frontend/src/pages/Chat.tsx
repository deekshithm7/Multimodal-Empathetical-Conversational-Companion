import { useState, useEffect, useRef, useCallback } from 'react';
import { clsx } from 'clsx';
import { useEmotionStore } from '../store/useEmotionStore';
import { useAuthStore } from '../store/useAuthStore';
import { useWebcamRecorder } from '../hooks/useWebcamRecorder';
import { useSpeechRecognition } from '../hooks/useSpeechRecognition';
import { ChatInterface } from '../components/Chat/ChatInterface';
import { AvatarScene } from '../components/Avatar/Scene';
import { WaveVisualizer } from '../components/AudioVisualizer/WaveVisualizer';
import { InputMonitorPanel } from '../components/Chat/InputMonitorPanel';
import { EmotionPanel } from '../components/Chat/EmotionPanel';
import { SessionSummary } from '../components/Dashboard/SessionSummary';
import { AnimatePresence } from 'framer-motion';

export const Chat = () => {
    const { currentEmotion, setListening, isListening, startSession, conversationId, sendMessage, sessionSummary, endSession } = useEmotionStore();
    const { isAuthenticated } = useAuthStore();

    const [activeInputMode, setActiveInputMode] = useState<'multimodal' | 'audio-only' | 'text-only'>('multimodal');
    const [showSummary, setShowSummary] = useState(false);
    const [sending, setSending] = useState(false);

    // Trigger summary modal when session summary is populated
    useEffect(() => {
        if (sessionSummary) {
            setShowSummary(true);
        }
    }, [sessionSummary]);

    const transcriptRef = useRef('');

    // send handler
    const handleSend = useCallback(async (text: string, blob?: Blob) => {
        if (sending) return;
        if (!text.trim() && (!blob || blob.size === 0)) return;

        setSending(true);
        console.log("Sending message...", { text, blobSize: blob?.size });
        try {
            await sendMessage(text, blob);
            transcriptRef.current = ''; // Reset ref
        } catch (e) {
            console.error("Failed to send message:", e);
        } finally {
            setSending(false);
        }
    }, [sendMessage, sending]);

    const {
        isListening: recognitionActive,
        startListening,
        stopListening,
        transcript,
        resetTranscript
    } = useSpeechRecognition();

    // Update transcript ref whenever it changes
    useEffect(() => {
        transcriptRef.current = transcript;
    }, [transcript]);

    const {
        isRecordingSession,
        startRecording,
        stopRecording,
        stream
    } = useWebcamRecorder({
        onRecordingComplete: (blob) => {
            // When video recording stops, send immediately with captured blob and current transcript
            handleSend(transcriptRef.current, blob);
            resetTranscript();
        }
    });

    const sessionStartedRef = useRef(false);

    // Initialize session
    useEffect(() => {
        if (isAuthenticated && !sessionStartedRef.current && !conversationId) {
            sessionStartedRef.current = true;
            startSession();
        }
    }, [isAuthenticated, startSession, conversationId]);

    // Sync listening
    useEffect(() => {
        setListening(recognitionActive);
    }, [recognitionActive, setListening]);


    // Toggle Handler
    const handleToggleSession = () => {
        if (recognitionActive || isRecordingSession) {
            // STOPPING
            stopListening();

            if (activeInputMode === 'multimodal') {
                // This triggers onRecordingComplete -> handleSend
                stopRecording();
            } else {
                // Audio/Text only: Send immediately
                // Small delay to ensure final transcript fragment? 
                // Usually not needed if interim is good, but let's just send.
                handleSend(transcriptRef.current);
                resetTranscript();
            }
        } else {
            // STARTING
            resetTranscript();
            transcriptRef.current = '';
            startListening();
            if (activeInputMode === 'multimodal') {
                startRecording();
            }
        }
    };

    const isSessionActive = recognitionActive || isRecordingSession;

    return (
        <div className="h-[calc(100vh-64px)] w-full overflow-hidden bg-[#0D1B2A] relative flex flex-col md:flex-row">

            {/* Dynamic Background */}
            <div className="absolute inset-0 z-0 pointer-events-none transition-colors duration-[4000ms]">
                {/* Ambient Wave */}
                <div className="absolute inset-0 opacity-30">
                    <WaveVisualizer isListening={isListening} emotion={currentEmotion} />
                </div>

                {/* Avatar Layer */}
                <div className="absolute inset-0 flex items-center justify-center opacity-40 md:opacity-60 scale-75 md:scale-100">
                    <div className="w-[500px] h-[500px]">
                        <AvatarScene />
                    </div>
                </div>
            </div>

            {/* Left Panel - Input Monitor (Desktop) */}
            <div className="hidden md:block w-1/4 h-full p-6 z-10 relative">
                <InputMonitorPanel
                    stream={stream}
                    isRecording={isRecordingSession}
                    isListening={recognitionActive}
                    activeInputMode={activeInputMode}
                    onToggleCamera={() => setActiveInputMode(prev => prev === 'multimodal' ? 'audio-only' : 'multimodal')}
                    onToggleMic={handleToggleSession}
                />
            </div>

            {/* Center Panel - Conversation */}
            <div className="flex-1 h-full z-20 relative flex flex-col">
                <div className="flex-1 flex flex-col justify-end pb-4">
                    <ChatInterface
                        onMicClick={handleToggleSession}
                        isRecording={isSessionActive}
                        transcript={transcript}
                    />
                </div>
            </div>

            {/* Right Panel - Emotion Data (Desktop) */}
            <div className="hidden md:block w-1/4 h-full p-6 z-10 relative">
                <EmotionPanel />
            </div>

            {/* Session Summary Modal */}
            <AnimatePresence>
                {showSummary && <SessionSummary onClose={() => setShowSummary(false)} />}
            </AnimatePresence>
        </div>
    );
};
