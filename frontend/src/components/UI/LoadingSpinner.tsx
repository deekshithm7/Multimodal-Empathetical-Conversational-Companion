import { Loader2 } from 'lucide-react';

interface LoadingSpinnerProps {
    size?: number;
    className?: string;
    text?: string;
}

export const LoadingSpinner = ({ size = 32, className = '', text }: LoadingSpinnerProps) => {
    return (
        <div className={`flex flex-col items-center justify-center gap-3 ${className}`}>
            <Loader2 size={size} className="animate-spin text-teal-400" />
            {text && <p className="text-sm text-slate-400">{text}</p>}
        </div>
    );
};
