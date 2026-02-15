import { useRef, useEffect } from 'react';
import { AudioLines, Square, Loader2, LogOut } from 'lucide-react';
import { useEmotionStore } from '../../store/useEmotionStore';
import { clsx } from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';

interface ChatInterfaceProps {
    onMicClick: () => void;
    isRecording: boolean;
}

export const ChatInterface = ({ onMicClick, isRecording }: ChatInterfaceProps) => {
    const { messages, isLoading, endSession, conversationId } = useEmotionStore();
    const messagesEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [messages]);

    const getEmotionColor = (emotion?: string) => {
        switch (emotion) {
            case 'happy': return 'bg-green-500/20 text-green-300 border-green-400';
            case 'sad': return 'bg-blue-500/20 text-blue-300 border-blue-400';
            case 'angry': return 'bg-red-500/20 text-red-300 border-red-400';
            default: return 'bg-gray-500/20 text-gray-300 border-gray-400';
        }
    };

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
                            <div>{msg.text}</div>
                            {/* Show emotion badge for user messages */}
                            {msg.emotion && msg.sender === 'user' && (
                                <div className={clsx(
                                    "mt-2 inline-block px-2 py-1 rounded-full text-xs border",
                                    getEmotionColor(msg.emotion.type)
                                )}>
                                    {msg.emotion.type} • {(msg.emotion.confidence * 100).toFixed(0)}%
                                </div>
                            )}
                        </motion.div>
                    ))}
                    {/* Loading indicator */}
                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="mr-auto bg-[rgba(255,255,255,0.4)] text-slate-800 rounded-bl-sm border border-white/40 px-5 py-3 rounded-3xl max-w-[85%]"
                        >
                            <Loader2 className="animate-spin" size={20} />
                        </motion.div>
                    )}
                </AnimatePresence>
                <div ref={messagesEndRef} />
            </div>

            {/* End Session Button (top right) */}
            {conversationId && messages.length > 1 && (
                <button
                    onClick={endSession}
                    disabled={isLoading}
                    className="absolute top-4 right-4 z-50 px-4 py-2 bg-white/20 hover:bg-white/30 text-white rounded-full text-xs font-medium border border-white/30 flex items-center gap-2 transition-all disabled:opacity-50"
                >
                    <LogOut size={14} />
                    End Session
                </button>
            )}

            {/* Central Multimodal Button */}
            <button
                onClick={onMicClick}
                disabled={isLoading}
                className={clsx(
                    "relative z-50 p-6 rounded-full transition-all duration-500 flex items-center justify-center shadow-xl border-4 transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed",
                    isRecording
                        ? "bg-red-500 text-white border-red-300 animate-pulse shadow-[0_10px_40px_rgba(239,68,68,0.4)]"
                        : "bg-white text-slate-700 border-white shadow-[0_10px_40px_rgba(200,195,180,0.4)] hover:shadow-[0_15px_50px_rgba(200,195,180,0.6)]"
                )}
            >
                {isRecording ? <Square size={32} fill="currentColor" /> : <AudioLines size={36} strokeWidth={2} />}
            </button>
            <p className="mt-4 text-xs font-semibold tracking-widest text-slate-400 uppercase opacity-60">
                {isLoading ? "Processing..." : isRecording ? "Recording • Listening" : "Tap to Start"}
            </p>

        </div>
    );
};

