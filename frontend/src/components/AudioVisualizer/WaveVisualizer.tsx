import { useEffect, useRef, forwardRef, useImperativeHandle } from 'react';

interface WaveVisualizerProps {
    isListening: boolean;
    emotion: 'happy' | 'sad' | 'angry' | 'neutral';
}

export const WaveVisualizer = forwardRef<HTMLCanvasElement, WaveVisualizerProps>(({ isListening, emotion }, ref) => {
    const internalCanvasRef = useRef<HTMLCanvasElement>(null);
    // Expose internal ref to parent
    useImperativeHandle(ref, () => internalCanvasRef.current as HTMLCanvasElement);

    const audioContextRef = useRef<AudioContext | null>(null);
    const analyserRef = useRef<AnalyserNode | null>(null);
    const sourceRef = useRef<MediaStreamAudioSourceNode | null>(null);
    const dataArrayRef = useRef<Uint8Array | null>(null);
    const particlesRef = useRef<any[]>([]); // Store particles

    // ... (rest of the logic uses internalCanvasRef)

    // Initialize/Cleanup Audio Context based on listening state
    useEffect(() => {
        if (isListening) {
            const initAudio = async () => {
                try {
                    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });

                    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
                    const audioCtx = new AudioContextClass();
                    const analyser = audioCtx.createAnalyser();

                    analyser.fftSize = 256;
                    analyser.smoothingTimeConstant = 0.8;

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
            // Cleanup
            if (sourceRef.current) {
                sourceRef.current.disconnect();
                sourceRef.current = null;
            }
            if (analyserRef.current) {
                analyserRef.current = null;
            }
            if (audioContextRef.current) {
                audioContextRef.current.close();
                audioContextRef.current = null;
            }
            dataArrayRef.current = null;
        }

        return () => {
            // Cleanup on unmount or change
            if (sourceRef.current) sourceRef.current.disconnect();
            if (audioContextRef.current) audioContextRef.current.close();
        };
    }, [isListening]);

    // Animation Loop
    useEffect(() => {
        const canvas = internalCanvasRef.current;
        if (!canvas) return;
        const ctx = canvas.getContext('2d');
        if (!ctx) return;

        let animationId: number;
        let phase = 0;

        // Initialize particles
        if (particlesRef.current.length === 0) {
            for (let i = 0; i < 30; i++) {
                particlesRef.current.push({
                    x: Math.random() * canvas.width,
                    y: Math.random() * canvas.height,
                    size: Math.random() * 2 + 0.5,
                    speedX: (Math.random() - 0.5) * 0.5,
                    speedY: (Math.random() - 0.5) * 0.5,
                    alpha: Math.random()
                });
            }
        }

        const render = () => {
            // 1. Resize Handling
            const dpr = window.devicePixelRatio || 1;
            const rect = canvas.getBoundingClientRect();

            if (canvas.width !== rect.width * dpr || canvas.height !== rect.height * dpr) {
                canvas.width = rect.width * dpr;
                canvas.height = rect.height * dpr;
                ctx.scale(dpr, dpr);
            }

            const width = rect.width;
            const height = rect.height;

            ctx.clearRect(0, 0, width, height);

            // 2. Colors & Parameters (Glowing Bioluminescent Colors)
            // Using solid rgb values for the base
            let color1 = '180, 160, 255'; // Lavender Glow
            let color2 = '140, 100, 255'; // Deep Purple
            let baseAmplitude = 30;

            switch (emotion) {
                case 'happy':
                    color1 = '255, 200, 100'; // Golden Glow
                    color2 = '255, 140, 50';  // Warm Amber
                    baseAmplitude = 40;
                    break;
                case 'sad':
                    color1 = '100, 200, 255'; // Cyan/Ice Glow
                    color2 = '50, 100, 200';  // Deep Ocean Blue
                    baseAmplitude = 20;
                    break;
                case 'angry':
                    color1 = '255, 100, 100'; // Neon Red
                    color2 = '200, 50, 50';   // Deep Crimson
                    baseAmplitude = 45;
                    break;
                default: // neutral
                    color1 = '200, 200, 220'; // Starlight White
                    color2 = '100, 100, 120'; // Soft Gray
            }

            // 3. Audio Data Processing
            let energy = 0; // 0 to 1
            if (isListening && analyserRef.current && dataArrayRef.current) {
                analyserRef.current.getByteFrequencyData(dataArrayRef.current as any);

                let sum = 0;
                const binCount = dataArrayRef.current.length;
                for (let i = 0; i < binCount; i++) {
                    sum += dataArrayRef.current[i];
                }
                const average = sum / binCount;
                energy = Math.min(average / 100, 1.0);
            }

            // 4. Draw Particles (Background)
            particlesRef.current.forEach(p => {
                p.y -= 0.2 + energy; // Particles float up faster with voice
                p.x += Math.sin(phase + p.y * 0.01) * 0.2;
                p.alpha -= 0.002;

                if (p.y < 0 || p.alpha <= 0) {
                    p.y = height;
                    p.x = Math.random() * width;
                    p.alpha = 1;
                }

                ctx.beginPath();
                ctx.arc(p.x, p.y, p.size * (1 + energy), 0, Math.PI * 2);
                ctx.fillStyle = `rgba(${color1}, ${p.alpha * 0.5})`;
                ctx.fill();
            });


            // 5. Draw Volumetric Waves
            const drawFluidLayer = (offset: number, rgbaColor: string, yOffset: number, ampMod: number) => {
                ctx.beginPath();
                ctx.moveTo(0, height); // Start bottom left

                // Draw curve
                for (let x = 0; x <= width; x += 5) {
                    const xScaled = x * 0.002;

                    // Simpler, more "blobby" equation
                    const wave = Math.sin(xScaled + phase + offset) *
                        Math.cos(xScaled * 0.5 + phase * 0.5);

                    // Voice disturbance adds organic noise/ripples
                    const voice = Math.sin(xScaled * 10 - phase * 2) * energy * 0.5;

                    const yRaw = wave + voice;
                    const y = height / 2 + yOffset - (yRaw * baseAmplitude * ampMod * (1 + energy));

                    ctx.lineTo(x, y);
                }

                ctx.lineTo(width, height); // To bottom right
                ctx.lineTo(0, height); // To bottom left
                ctx.closePath();

                // Gradient Fill
                const gradient = ctx.createLinearGradient(0, height / 2, 0, height);
                gradient.addColorStop(0, rgbaColor);
                gradient.addColorStop(1, `rgba(${color2}, 0.1)`);

                ctx.fillStyle = gradient;

                // Glow
                ctx.shadowBlur = 20;
                ctx.shadowColor = `rgba(${color1}, 0.5)`;

                ctx.fill();
                ctx.shadowBlur = 0;
            };

            // Back Layer - Less opaque, bigger waves
            drawFluidLayer(0, `rgba(${color2}, 0.3)`, 20, 1.2);

            // Middle Layer
            drawFluidLayer(2, `rgba(${color1}, 0.5)`, 10, 1.0);

            // Front Layer - Stronger color
            drawFluidLayer(4, `rgba(${color1}, 0.7)`, 0, 0.8);

            // Phase increment
            phase += 0.015; // Slow, oozing speed

            animationId = requestAnimationFrame(render);
        };

        render();

        return () => {
            cancelAnimationFrame(animationId);
        };
    }, [emotion, isListening]);

    return <canvas ref={internalCanvasRef} className="w-full h-full absolute bottom-0 left-0" />;
});

WaveVisualizer.displayName = 'WaveVisualizer';
