import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';

interface WaveVisualizerProps {
    isListening: boolean;
    isAiSpeaking?: boolean; // New prop for AI state
    emotion: 'happy' | 'sad' | 'angry' | 'neutral';
}

export const WaveVisualizer = forwardRef<HTMLCanvasElement, WaveVisualizerProps>(({ isListening, isAiSpeaking = false, emotion }, ref) => {
    const internalCanvasRef = useRef<HTMLCanvasElement>(null);
    useImperativeHandle(ref, () => internalCanvasRef.current as HTMLCanvasElement);

    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const dataArrayRef = useRef<Uint8Array | null>(null);

    // Visualization State
    const particlesRef = useRef<any[]>([]);
    const phaseRef = useRef(0);

    // 1. Audio Setup (User Mic)
    useEffect(() => {
        if (isListening) {
            const initAudio = async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
                    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
                    const audioCtx = new AudioContextClass();
                    const analyser = audioCtx.createAnalyser();

                    // Better resolution for spectral mapping
                    analyser.fftSize = 512;
                    analyser.smoothingTimeConstant = 0.7; // Snappy response

                    const source = audioCtx.createMediaStreamSource(stream);
                    source.connect(analyser);

                    audioContextRef.current = audioCtx;
                    analyserRef.current = analyser;
                    sourceRef.current = source;
                    dataArrayRef.current = new Uint8Array(analyser.frequencyBinCount);
                } catch (err) {
                    console.error("Error initializing audio:", err);
                }
            };
            initAudio();
        } else {
            // Cleanup Logic
            if (sourceRef.current) { sourceRef.current.disconnect(); sourceRef.current = null; }
            if (analyserRef.current) { analyserRef.current = null; }
            if (audioContextRef.current) { audioContextRef.current.close(); audioContextRef.current = null; }
        }
        return () => {
            if (sourceRef.current) sourceRef.current.disconnect();
            if (audioContextRef.current) audioContextRef.current.close();
        };
    }, [isListening]);

    // 2. Render Loop
    useEffect(() => {
        const canvas = internalCanvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationId: number;

        // Init Particles
        if (particlesRef.current.length === 0) {
            for (let i = 0; i < 50; i++) {
                particlesRef.current.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    size: Math.random() * 2 + 0.5,
                    vx: (Math.random() - 0.5) * 0.5,
                    vy: (Math.random() - 0.5) * 0.5,
                    alpha: Math.random() * 0.5
                });
            }
        }

        const render = () => {
            // Resize
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();
            if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
                canvas.width = rect.width * dpr;
                canvas.height = rect.height * dpr;
                ctx.scale(dpr, dpr);
            }
            const w = rect.width;
            const h = rect.height;

            ctx.clearRect(0, 0, w, h);

            // Palette Definition
            let primary = '180, 160, 255';
            let secondary = '140, 100, 255';

            switch (emotion) {
                case 'happy': primary = '255, 200, 100'; secondary = '255, 140, 50'; break;
                case 'sad': primary = '100, 200, 255'; secondary = '50, 100, 200'; break;
                case 'angry': primary = '255, 80, 80'; secondary = '200, 40, 40'; break;
                default: primary = '200, 200, 220'; secondary = '120, 120, 140'; break;
            }

            // Audio Analysis
            let bass = 0; // Low freq
            let mid = 0;  // Mid freq
            let treble = 0; // High freq
            let totalEnergy = 0;

            if (isListening && analyserRef.current && dataArrayRef.current) {
                analyserRef.current.getByteFrequencyData(dataArrayRef.current as any);
                const bins = dataArrayRef.current.length;

                // Simple banding
                const bassBins = Math.floor(bins * 0.1);
                const midBins = Math.floor(bins * 0.5);

                let bSum = 0, mSum = 0, tSum = 0;

                for (let i = 0; i < bins; i++) {
                    const val = dataArrayRef.current[i];
                    if (i < bassBins) bSum += val;
                    else if (i < midBins) mSum += val;
                    else tSum += val;
                }

                bass = (bSum / bassBins) / 255;
                mid = (mSum / (midBins - bassBins)) / 255;
                treble = (tSum / (bins - midBins)) / 255;
                totalEnergy = (bass + mid + treble) / 3;
            } else if (isAiSpeaking) {
                // Mock AI Speaking Viz (Sine waves simulation)
                const mockTime = Date.now() / 1000;
                bass = 0.3 + Math.sin(mockTime * 10) * 0.2;
                mid = 0.3 + Math.sin(mockTime * 20) * 0.2;
                totalEnergy = 0.4;
            } else {
                // Idle / Breathing
                const breath = (Math.sin(phaseRef.current * 0.5) + 1) * 0.5;
                bass = 0.1 * breath;
                mid = 0.05;
                totalEnergy = 0.1 * breath;
            }

            // DUCKING LOGIC (Barge-In)
            // If User is Listening, AI presence is replaced by User's spectral data.
            // If isAiSpeaking is true BUT isListening is ALSO true, User wins.
            // Effectively handled by the `if (isListening)` block above taking precedence for data sources.
            // However, visually, we might want to dampen the "AI Blob" if we had a separate one.
            // Here, we share the wave, so the "Ducking" is actually "Mode Switching".

            // Particles (Ambient Field)
            particlesRef.current.forEach(p => {
                p.y -= 0.2 + (totalEnergy * 2); // Rise on energy
                p.x += Math.sin(phaseRef.current + p.y * 0.01) * 0.5;

                if (p.y < 0) p.y = h;
                if (p.x > w) p.x = 0;
                if (p.x < 0) p.x = w;

                ctx.beginPath();
                // Treble affects particle size/sharpness
                const sizeMod = 1 + (treble * 3);
                ctx.arc(p.x, p.y, p.size * sizeMod, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${primary}, ${p.alpha * (0.3 + totalEnergy)})`;
                ctx.fill();
            });

            // Fluid Wave Layer (Spectral)
            const drawWave = (offset: number, color: string, amp: number, speed: number) => {
                ctx.beginPath();
                ctx.moveTo(0, h);

                for (let x = 0; x <= w; x += 10) {
                    const normX = x / w;

                    // Wave Mechanics
                    const baseWave = Math.sin(normX * 10 + phaseRef.current * speed + offset);

                    // Spectral Modulation
                    // Bass affects large slow swells
                    // Mid affects ripple height
                    // Treble affects jagged noise

                    const spectralY =
                        (baseWave * 20) +
                        (Math.sin(normX * 20 + phaseRef.current * 2) * bass * 100 * amp) +
                        (Math.sin(normX * 50 - phaseRef.current * 4) * mid * 50 * amp);

                    const y = h / 2 + 50 + spectralY;

                    ctx.lineTo(x, y);
                }

                ctx.lineTo(w, h);
                ctx.lineTo(0, h);
                ctx.closePath();

                // Gradient
                const g = ctx.createLinearGradient(0, h / 2, 0, h);
                g.addColorStop(0, color);
                g.addColorStop(1, `rgba(${secondary}, 0.1)`);
                ctx.fillStyle = g;

                // Glow
                ctx.shadowBlur = 15 + (bass * 30);
                ctx.shadowColor = `rgba(${primary}, 0.5)`;
                ctx.fill();
                ctx.shadowBlur = 0;
            };

            // Back Wave (Bass-heavy, slow)
            // If isListening (User), this goes BIG. If AI, it's moderate.
            drawWave(0, `rgba(${secondary}, 0.2)`, 1.5, 0.5);

            // Front Wave (Mid/Treble, fast)
            drawWave(2, `rgba(${primary}, 0.6)`, 1.0, 1.2);

            phaseRef.current += 0.02 + (totalEnergy * 0.05); // Speed up with energy
            animationId = requestAnimationFrame(render);
        };
        render();

        return () => cancelAnimationFrame(animationId);
    }, [emotion, isListening, isAiSpeaking]);

    return <canvas ref={internalCanvasRef} className="w-full h-full absolute bottom-0 left-0 transition-opacity duration-1000" />;
});

WaveVisualizer.displayName = 'WaveVisualizer';
