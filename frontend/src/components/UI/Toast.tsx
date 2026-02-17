import { create } from 'zustand';
import { CheckCircle, AlertCircle, Info, X } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useEffect } from 'react';

type ToastType = 'success' | 'error' | 'info' | 'warning';

interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastState {
    toasts: Toast[];
    addToast: (type: ToastType, message: string, duration?: number) => void;
    removeToast: (id: string) => void;
}

export const useToastStore = create<ToastState>((set) => ({
    toasts: [],
    addToast: (type, message, duration = 4000) => {
        const id = Date.now().toString();
        set((state) => ({
            toasts: [...state.toasts, { id, type, message, duration }]
        }));

        // Auto remove after duration
        setTimeout(() => {
            set((state) => ({
                toasts: state.toasts.filter((t) => t.id !== id)
            }));
        }, duration);
    },
    removeToast: (id) => {
        set((state) => ({
            toasts: state.toasts.filter((t) => t.id !== id)
        }));
    }
}));

const ToastIcon = ({ type }: { type: ToastType }) => {
    const icons = {
        success: <CheckCircle size={20} />,
        error: <AlertCircle size={20} />,
        warning: <AlertCircle size={20} />,
        info: <Info size={20} />
    };
    return icons[type];
};

const Toast = ({ toast }: { toast: Toast }) => {
    const removeToast = useToastStore((state) => state.removeToast);

    const styles = {
        success: 'bg-green-500/20 border-green-400 text-green-300',
        error: 'bg-red-500/20 border-red-400 text-red-300',
        warning: 'bg-amber-500/20 border-amber-400 text-amber-300',
        info: 'bg-blue-500/20 border-blue-400 text-blue-300'
    };

    return (
        <motion.div
            initial={{ opacity: 0, y: 50, scale: 0.9 }}
            animate={{ opacity: 1, y: 0, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8, transition: { duration: 0.2 } }}
            className={`glass-panel px-4 py-3 border flex items-center gap-3 min-w-[300px] max-w-md ${styles[toast.type]}`}
        >
            <ToastIcon type={toast.type} />
            <p className="flex-1 text-sm font-medium">{toast.message}</p>
            <button
                onClick={() => removeToast(toast.id)}
                className="text-current opacity-60 hover:opacity-100 transition-opacity"
            >
                <X size={18} />
            </button>
        </motion.div>
    );
};

export const ToastContainer = () => {
    const toasts = useToastStore((state) => state.toasts);

    return (
        <div className="fixed bottom-6 right-6 z-[100] flex flex-col gap-2">
            <AnimatePresence mode="popLayout">
                {toasts.map((toast) => (
                    <Toast key={toast.id} toast={toast} />
                ))}
            </AnimatePresence>
        </div>
    );
};

// Hook for easy toast usage
export const useToast = () => {
    const addToast = useToastStore((state) => state.addToast);

    return {
        success: (message: string, duration?: number) => addToast('success', message, duration),
        error: (message: string, duration?: number) => addToast('error', message, duration),
        warning: (message: string, duration?: number) => addToast('warning', message, duration),
        info: (message: string, duration?: number) => addToast('info', message, duration)
    };
};
