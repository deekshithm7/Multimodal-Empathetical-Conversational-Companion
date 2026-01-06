import { useRef, useEffect } from 'react';
import { AudioLines, Square } from 'lucide-react'; // Changed to AudioLines
import { useEmotionStore } from '../../store/useEmotionStore';
import { clsx } from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';

interface ChatInterfaceProps {
    onMicClick: () => void;
    isRecording: boolean;
}

export const ChatInterface = ({ onMicClick, isRecording }: ChatInterfaceProps) => {
    const { messages } = useEmotionStore();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    return (
        <div className="flex flex-col h-[500px] w-full max-w-xl mx-auto items-center justify-end pb-12 relative">

            {/* Messages Overlay (Translucent Bubbles) */}
            <div className="absolute top-0 w-full h-[380px] overflow-y-auto px-6 py-4 space-y-3 scrollbar-hide mask-gradient-top">
                <AnimatePresence mode="popLayout">
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            className={clsx(
                                "max-w-[85%] px-5 py-3 rounded-3xl text-sm leading-relaxed shadow-sm font-medium",
                                msg.sender === 'user'
                                    ? "ml-auto bg-white/70 text-slate-700 rounded-br-sm border border-white/50"
                                    : "mr-auto bg-[rgba(255,255,255,0.4)] text-slate-800 rounded-bl-sm border border-white/40"
                            )}
                        >
                            {msg.text}
                        </motion.div>
                    ))}
                </AnimatePresence>
                <div ref={messagesEndRef} />
            </div>

            {/* Central Multimodal Button */}
            <button
                onClick={onMicClick}
                className={clsx(
                    "relative z-50 p-6 rounded-full transition-all duration-500 flex items-center justify-center shadow-xl border-4 transform hover:scale-105 active:scale-95",
                    isRecording
                        ? "bg-red-500 text-white border-red-300 animate-pulse shadow-[0_10px_40px_rgba(239,68,68,0.4)]"
                        : "bg-white text-slate-700 border-white shadow-[0_10px_40px_rgba(200,195,180,0.4)] hover:shadow-[0_15px_50px_rgba(200,195,180,0.6)]"
                )}
            >
                {isRecording ? <Square size={32} fill="currentColor" /> : <AudioLines size={36} strokeWidth={2} />}
            </button>
            <p className="mt-4 text-xs font-semibold tracking-widest text-slate-400 uppercase opacity-60">
                {isRecording ? "Recording Session • Listening" : "Tap to Start Session"}
            </p>

        </div>
    );
};
