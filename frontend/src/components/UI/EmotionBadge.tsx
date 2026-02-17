import { clsx } from 'clsx';

type Emotion = 'neutral' | 'calm' | 'happy' | 'sad' | 'angry' | 'fearful' | 'disgust' | 'surprised';

interface EmotionBadgeProps {
    emotion: Emotion;
    confidence?: number;
    size?: 'sm' | 'md' | 'lg';
    showConfidence?: boolean;
}

const emotionConfig: Record<Emotion, { color: string; bgColor: string; borderColor: string; emoji: string }> = {
    neutral: {
        color: 'text-gray-300',
        bgColor: 'bg-gray-500/20',
        borderColor: 'border-gray-400',
        emoji: '😐'
    },
    calm: {
        color: 'text-blue-300',
        bgColor: 'bg-blue-500/20',
        borderColor: 'border-blue-400',
        emoji: '😌'
    },
    happy: {
        color: 'text-green-300',
        bgColor: 'bg-green-500/20',
        borderColor: 'border-green-400',
        emoji: '😊'
    },
    sad: {
        color: 'text-purple-300',
        bgColor: 'bg-purple-500/20',
        borderColor: 'border-purple-400',
        emoji: '😔'
    },
    angry: {
        color: 'text-red-300',
        bgColor: 'bg-red-500/20',
        borderColor: 'border-red-400',
        emoji: '😤'
    },
    fearful: {
        color: 'text-orange-300',
        bgColor: 'bg-orange-500/20',
        borderColor: 'border-orange-400',
        emoji: '😨'
    },
    disgust: {
        color: 'text-amber-300',
        bgColor: 'bg-amber-500/20',
        borderColor: 'border-amber-400',
        emoji: '🤢'
    },
    surprised: {
        color: 'text-yellow-300',
        bgColor: 'bg-yellow-500/20',
        borderColor: 'border-yellow-400',
        emoji: '😲'
    }
};

export const EmotionBadge = ({
    emotion,
    confidence,
    size = 'md',
    showConfidence = true
}: EmotionBadgeProps) => {
    const config = emotionConfig[emotion];

    const sizeClasses = {
        sm: 'px-2 py-1 text-xs',
        md: 'px-3 py-1.5 text-sm',
        lg: 'px-4 py-2 text-base'
    };

    return (
        <span
            className={clsx(
                'inline-flex items-center gap-1.5 rounded-full border font-medium',
                config.color,
                config.bgColor,
                config.borderColor,
                sizeClasses[size]
            )}
        >
            <span>{config.emoji}</span>
            <span className="capitalize">{emotion}</span>
            {showConfidence && confidence !== undefined && (
                <span className="opacity-80">• {Math.round(confidence * 100)}%</span>
            )}
        </span>
    );
};
