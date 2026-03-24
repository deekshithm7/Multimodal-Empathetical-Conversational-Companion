import { useRef, useEffect } from 'react';
import { AudioLines, Square, Loader2, LogOut } from 'lucide-react';
import { useEmotionStore } from '../../store/useEmotionStore';
import { clsx } from 'clsx';
import { AnimatePresence, motion } from 'framer-motion';

interface ChatInterfaceProps {
    onMicClick: () => void;
    isRecording: boolean;
    transcript?: string;
}

export const ChatInterface = ({ onMicClick, isRecording, transcript }: ChatInterfaceProps) => {
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
        <div className="flex flex-col w-full max-w-2xl mx-auto h-full relative min-h-0">

            {/* Messages Area */}
            <div className="flex-1 overflow-y-auto px-6 py-4 space-y-4 min-h-0 scroll-smooth">
                <AnimatePresence>
                    {messages.map((msg) => (
                        <motion.div
                            key={msg.id}
                            initial={{ opacity: 0, y: 10, scale: 0.95 }}
                            animate={{ opacity: 1, y: 0, scale: 1 }}
                            className={clsx(
                                "max-w-[85%] px-5 py-3 rounded-3xl text-sm leading-relaxed shadow-sm font-medium",
                                msg.sender === 'user'
                                    ? "ml-auto bg-white/70 text-slate-700 rounded-br-sm border border-white/50"
                                    : "mr-auto bg-white/10 backdrop-blur-md text-slate-100 rounded-bl-sm border border-white/10"
                            )}
                        >
                            <div>{msg.text}</div>
                            {/* Show emotion badge for user messages */}
                            {msg.emotion && msg.sender === 'user' && (
                                <div className={clsx(
                                    "mt-2 inline-block px-2 py-1 rounded-full text-xs border capitalize",
                                    getEmotionColor(msg.emotion.type)
                                )}>
                                    {msg.emotion.type}
                                </div>
                            )}
                        </motion.div>
                    ))}
                    {/* Loading indicator */}
                    {isLoading && (
                        <motion.div
                            initial={{ opacity: 0 }}
                            animate={{ opacity: 1 }}
                            className="mr-auto bg-white/10 backdrop-blur-md text-slate-100 rounded-bl-sm border border-white/10 px-5 py-3 rounded-3xl max-w-[85%]"
                        >
                            <Loader2 className="animate-spin" size={20} />
                        </motion.div>
                    )}
                </AnimatePresence>
                <div ref={messagesEndRef} className="h-4" />
            </div>

            {/* Controls Area */}
            <div className="flex flex-col items-center justify-center p-6 z-50 relative shrink-0">
                {/* Live Transcript Overlay */}
                <div className="h-8 mb-4">
                    <AnimatePresence>
                        {isRecording && transcript && (
                            <motion.div
                                initial={{ opacity: 0, y: 10 }}
                                animate={{ opacity: 1, y: 0 }}
                                exit={{ opacity: 0, y: -10 }}
                                className="px-4 py-2 bg-black/60 backdrop-blur-md rounded-full border border-white/10 max-w-md truncate text-center"
                            >
                                <p className="text-sm text-slate-200">{transcript}</p>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>

                {/* Central Multimodal Button */}
                <button
                    onClick={onMicClick}
                    disabled={isLoading}
                    className={clsx(
                        "relative p-6 rounded-full transition-all duration-500 flex items-center justify-center shadow-2xl border-4 transform hover:scale-105 active:scale-95 disabled:opacity-50 disabled:cursor-not-allowed",
                        isRecording
                            ? "bg-red-500 text-white border-red-400 animate-pulse shadow-red-500/20"
                            : "bg-white text-slate-800 border-slate-200 shadow-slate-200/20 hover:shadow-slate-200/40"
                    )}
                >
                    {isRecording ? <Square size={32} fill="currentColor" /> : <AudioLines size={36} strokeWidth={2} />}
                </button>
                <p className="mt-4 text-xs font-semibold tracking-widest text-slate-400 uppercase opacity-60">
                    {isLoading ? "Processing..." : isRecording ? "Recording • Listening" : "Tap to Start"}
                </p>

                {/* End Session Button (absolute in this container) */}
                {conversationId && messages.length > 1 && (
                    <button
                        onClick={endSession}
                        disabled={isLoading}
                        className="absolute right-0 bottom-10 px-4 py-2 text-slate-400 hover:text-white hover:bg-white/10 rounded-full text-xs font-medium flex items-center gap-2 transition-all"
                    >
                        <LogOut size={14} />
                        End Session
                    </button>
                )}
            </div>

        </div>
    );
};
