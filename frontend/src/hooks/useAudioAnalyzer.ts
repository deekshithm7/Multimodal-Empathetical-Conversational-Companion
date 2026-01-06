import { useState, useEffect, useRef } from 'react';

export const useAudioAnalyzer = (isListening: boolean) => {
    const [audioData, setAudioData] = useState<Uint8Array>(new Uint8Array(0));
    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const rafRef = useRef<number | null>(null);

    useEffect(() => {
        if (isListening) {
            const startAnalyzer = async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    audioContextRef.current = new (window.AudioContext || (window as any).webkitAudioContext)();
                    analyserRef.current = audioContextRef.current.createAnalyser();
                    analyserRef.current.fftSize = 256; // Good balance for visualizer
                    sourceRef.current = audioContextRef.current.createMediaStreamSource(stream);
                    sourceRef.current.connect(analyserRef.current);

                    const bufferLength = analyserRef.current.frequencyBinCount;
                    const dataArray = new Uint8Array(bufferLength);

                    const update = () => {
                        if (analyserRef.current) {
                            analyserRef.current.getByteFrequencyData(dataArray);
                            setAudioData(new Uint8Array(dataArray));
                            rafRef.current = requestAnimationFrame(update);
                        }
                    };
                    update();
                } catch (err) {
                    console.error("Error accessing microphone:", err);
                }
            };

            startAnalyzer();
        } else {
            // Cleanup
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
            if (sourceRef.current) sourceRef.current.disconnect();
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                audioContextRef.current.close();
            }
            setAudioData(new Uint8Array(0));
        }

        return () => {
            if (rafRef.current) cancelAnimationFrame(rafRef.current);
            if (audioContextRef.current && audioContextRef.current.state !== 'closed') {
                audioContextRef.current.close();
            }
        };
    }, [isListening]);

    return audioData;
};
