import { motion } from 'framer-motion';
import { useEmotionStore } from '../../store/useEmotionStore';
import { X } from 'lucide-react';

interface SessionSummaryProps {
    onClose: () => void;
}

export const SessionSummary = ({ onClose }: SessionSummaryProps) => {
    const { sessionSummary } = useEmotionStore();

    if (!sessionSummary) return null;

    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white/10 backdrop-blur-md p-8 rounded-2xl shadow-2xl border border-white/20 z-50 w-[600px] max-h-[80vh] overflow-y-auto text-center"
        >
            <button
                onClick={onClose}
                className="absolute top-4 right-4 text-white/60 hover:text-white transition-colors"
            >
                <X size={24} />
            </button>

            <h2 className="text-2xl font-serif text-white mb-4">Session Summary</h2>

            {/* Summary Text */}
            <div className="bg-white/5 rounded-lg p-4 mb-6 text-left">
                <p className="text-slate-200 leading-relaxed">{sessionSummary.summary}</p>
            </div>

            {/* Stats */}
            <div className="grid grid-cols-2 gap-4 mb-6">
                <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-2xl font-bold text-white">{sessionSummary.total_messages}</div>
                    <div className="text-xs text-slate-400 uppercase">Messages</div>
                </div>
                <div className="bg-white/5 rounded-lg p-3">
                    <div className="text-2xl font-bold text-white">{sessionSummary.duration_minutes.toFixed(1)} min</div>
                    <div className="text-xs text-slate-400 uppercase">Duration</div>
                </div>
            </div>

            {/* Emotional Journey */}
            {sessionSummary.emotional_journey.length > 0 && (
                <div className="mb-6 text-left">
                    <h3 className="text-sm font-semibold text-slate-300 uppercase mb-3">Emotional Journey</h3>
                    <div className="space-y-2">
                        {sessionSummary.emotional_journey.map((entry, idx) => (
                            <div key={idx} className="bg-white/5 rounded px-3 py-2 flex justify-between items-center">
                                <span className="text-slate-200 capitalize">{entry.emotion}</span>
                                <span className="text-slate-400 text-sm">{(entry.confidence * 100).toFixed(0)}%</span>
                            </div>
                        ))}
                    </div>
                </div>
            )}

            <button
                onClick={onClose}
                className="px-6 py-2 bg-white/20 hover:bg-white/30 text-white rounded-full transition-colors"
            >
                Close
            </button>
        </motion.div>
    );
};

