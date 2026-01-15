import { useRef, useEffect } from 'react';
import { motion } from 'framer-motion';

interface SessionSummaryProps {
    onClose: () => void;
}

export const SessionSummary = ({ onClose }: SessionSummaryProps) => {
    return (
        <motion.div
            initial={{ opacity: 0, y: 20 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 20 }}
            className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-white/10 backdrop-blur-md p-8 rounded-2xl shadow-2xl border border-white/20 z-50 w-96 text-center"
        >
            <h2 className="text-2xl font-serif text-white mb-4">Session Summary</h2>
            <p className="text-slate-300 mb-6">
                Your session has been recorded. The summary analysis will appear here.
            </p>
            <button
                onClick={onClose}
                className="px-6 py-2 bg-white/20 hover:bg-white/30 text-white rounded-full transition-colors"
            >
                Close
            </button>
        </motion.div>
    );
};
