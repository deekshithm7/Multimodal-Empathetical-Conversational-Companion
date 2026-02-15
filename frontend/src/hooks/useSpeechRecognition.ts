import { useState, useEffect, useCallback } from 'react';

interface UseSpeechRecognitionReturn {
    isListening: boolean;
    transcript: string;
    startListening: () => void;
    stopListening: () => void;
    resetTranscript: () => void;
    hasRecognitionSupport: boolean;
}

export const useSpeechRecognition = (): UseSpeechRecognitionReturn => {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [recognition, setRecognition] = useState<SpeechRecognition | null>(null);

    useEffect(() => {
        if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {
            const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
            const recognitionInstance = new SpeechRecognition();
            recognitionInstance.continuous = true;
            recognitionInstance.interimResults = true;
            recognitionInstance.lang = 'en-US';

            recognitionInstance.onresult = (event: any) => {
                console.log('🎤 Speech recognition result:', event.results);
                let finalTranscript = '';
                for (let i = event.resultIndex; i < event.results.length; ++i) {
                    if (event.results[i].isFinal) {
                        finalTranscript += event.results[i][0].transcript;
                    } else {
                        // interim logic if needed
                    }
                }
                // Grab the latest transcript
                const current = Array.from(event.results)
                    .map((result: any) => result[0].transcript)
                    .join('');
                console.log('📝 Transcript updated:', current);
                setTranscript(current);
            };

            recognitionInstance.onend = () => {
                console.log('🛑 Speech recognition ended');
                setIsListening(false);
            };

            recognitionInstance.onerror = (event: any) => {
                console.error('❌ Speech recognition error:', event.error, event);
                setIsListening(false);
            };

            recognitionInstance.onstart = () => {
                console.log('🎙️ Speech recognition started');
            };

            setRecognition(recognitionInstance);
        } else {
            console.error('❌ Speech recognition NOT supported in this browser');
        }
    }, []);

    const startListening = useCallback(() => {
        console.log('▶️ Attempting to start listening...', { hasRecognition: !!recognition });
        if (recognition) {
            try {
                recognition.start();
                setIsListening(true);
            } catch (e) {
                console.error("❌ Error starting recognition:", e);
            }
        }
    }, [recognition]);

    const stopListening = useCallback(() => {
        if (recognition) {
            try {
                recognition.stop();
                setIsListening(false);
            } catch (e) {
                console.error("Error stopping recognition:", e);
            }
        }
    }, [recognition]);

    const resetTranscript = useCallback(() => {
        setTranscript('');
    }, []);

    return {
        isListening,
        transcript,
        startListening,
        stopListening,
        resetTranscript,
        hasRecognitionSupport: !!recognition
    };
};
