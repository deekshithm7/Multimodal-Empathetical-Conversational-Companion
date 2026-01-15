import { useEffect, useRef, useState } from 'react';
import { motion } from 'framer-motion';
import { ShieldCheck } from 'lucide-react';

interface VanishingCameraProps {
    stream: MediaStream | null;
}

export const VanishingCamera = ({ stream }: VanishingCameraProps) => {
    const videoRef = useRef<HTMLVideoElement>(null);
    const [isInitial, setIsInitial] = useState(true); // "Pre-flight" state

    useEffect(() => {
        if (stream && videoRef.current) {
            videoRef.current.srcObject = stream;
        }
    }, [stream]);

    const currentState = isInitial ? 'centering' : 'expanded';

    // Auto-transition from "Centering" (Pre-flight) to "Expanded" (Corner)
    useEffect(() => {
        if (stream) {
            const timer = setTimeout(() => {
                setIsInitial(false);
            }, 3000); // 3 seconds pre-flight
            return () => clearTimeout(timer);
        } else {
            setIsInitial(true);
        }
    }, [stream]);

    if (!stream) return null;

    // Variants for animation
    const containerVariants = {
        initial: {
            width: '300px',
            height: '225px',
            borderRadius: '24px',
            bottom: '50%',
            right: '50%',
            x: '50%',
            y: '50%',
            opacity: 0,
            scale: 0.8
        },
        centering: {
            width: '400px',
            height: '300px',
            borderRadius: '24px',
            bottom: '50%',
            right: '50%',
            x: '50%',
            y: '50%',
            opacity: 1,
            scale: 1,
            zIndex: 50
        },
        expanded: {
            width: '280px',
            height: '210px',
            borderRadius: '16px',
            bottom: '0%',
            right: '0%',
            x: '-24px',
            y: '-24px',
            opacity: 1,
            zIndex: 50
        }
    };

    return (
        <motion.div
            className="absolute overflow-hidden bg-black/50 backdrop-blur-md border border-emerald-500/30 shadow-2xl transition-colors cursor-move"
            variants={containerVariants}
            initial="initial"
            animate={currentState}
            transition={{ type: 'spring', stiffness: 60, damping: 15 }} // Slightly softer spring
            drag
            dragConstraints={{ left: -1000, right: 0, top: -1000, bottom: 0 }}
        >
            {/* The Video Feed */}
            <video
                ref={videoRef}
                autoPlay
                muted
                playsInline
                className="w-full h-full object-cover"
            />

            {/* Always show overlay since it's never minimized now */}
            <div className="absolute inset-0 p-4 flex flex-col justify-between pointer-events-none">
                {/* Top Bar: Privacy Shield */}
                <div className="flex items-center space-x-2 text-emerald-400 bg-black/40 w-fit px-3 py-1 rounded-full backdrop-blur-sm">
                    <ShieldCheck size={14} />
                    <span className="text-[10px] font-bold tracking-wider uppercase">On-Device Encrypted</span>
                </div>

                {/* Initial State Prompt */}
                {isInitial && (
                    <div className="absolute inset-0 flex items-center justify-center">
                        <h3 className="text-white text-lg font-medium tracking-wide drop-shadow-lg bg-black/20 px-4 py-2 rounded-xl backdrop-blur-sm">
                            Establishing Secure Channel...
                        </h3>
                    </div>
                )}
            </div>
        </motion.div>
    );
};
