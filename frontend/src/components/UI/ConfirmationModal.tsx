import { motion, AnimatePresence } from 'framer-motion';
import { X, AlertCircle } from 'lucide-react';
import { Button } from './Button';

interface ConfirmationModalProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    title: string;
    message: string;
    confirmText?: string;
    cancelText?: string;
    variant?: 'warning' | 'danger';
    isLoading?: boolean;
}

export const ConfirmationModal = ({
    isOpen,
    onClose,
    onConfirm,
    title,
    message,
    confirmText = 'Confirm',
    cancelText = 'Cancel',
    variant = 'warning',
    isLoading = false
}: ConfirmationModalProps) => {
    return (
        <AnimatePresence>
            {isOpen && (
                <>
                    {/* Backdrop */}
                    <motion.div
                        initial={{ opacity: 0 }}
                        animate={{ opacity: 1 }}
                        exit={{ opacity: 0 }}
                        className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50"
                        onClick={onClose}
                    />

                    {/* Modal */}
                    <div className="fixed inset-0 flex items-center justify-center z-50 p-4">
                        <motion.div
                            initial={{ opacity: 0, scale: 0.95, y: 20 }}
                            animate={{ opacity: 1, scale: 1, y: 0 }}
                            exit={{ opacity: 0, scale: 0.95, y: 20 }}
                            className="glass-panel max-w-md w-full p-6 relative"
                            onClick={(e) => e.stopPropagation()}
                        >
                            {/* Close button */}
                            <button
                                onClick={onClose}
                                className="absolute top-4 right-4 text-slate-400 hover:text-slate-200 transition-colors"
                            >
                                <X size={20} />
                            </button>

                            {/* Icon */}
                            <div className={`w-12 h-12 rounded-full flex items-center justify-center mb-4 ${variant === 'danger' ? 'bg-red-500/20' : 'bg-amber-500/20'
                                }`}>
                                <AlertCircle
                                    size={24}
                                    className={variant === 'danger' ? 'text-red-400' : 'text-amber-400'}
                                />
                            </div>

                            {/* Content */}
                            <h3 className="text-xl font-semibold text-slate-100 mb-2">{title}</h3>
                            <p className="text-slate-300 mb-6 leading-relaxed">{message}</p>

                            {/* Actions */}
                            <div className="flex gap-3">
                                <Button
                                    variant="ghost"
                                    onClick={onClose}
                                    disabled={isLoading}
                                    className="flex-1"
                                >
                                    {cancelText}
                                </Button>
                                <Button
                                    variant={variant === 'danger' ? 'danger' : 'primary'}
                                    onClick={onConfirm}
                                    isLoading={isLoading}
                                    className="flex-1"
                                >
                                    {confirmText}
                                </Button>
                            </div>
                        </motion.div>
                    </div>
                </>
            )}
        </AnimatePresence>
    );
};
