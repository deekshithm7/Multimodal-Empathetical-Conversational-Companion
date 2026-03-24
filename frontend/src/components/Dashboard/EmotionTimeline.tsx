import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer
} from 'recharts';
import { useState } from 'react';
import { clsx } from 'clsx';

export interface EmotionTimelineProps {
    data: Array<{
        date: string;
        happy?: number;
        sad?: number;
        angry?: number;
        calm?: number;
        fearful?: number;
        [key: string]: string | number | undefined;
    }>;
}

const emotionConfig = [
    { key: 'happy', color: '#4ade80', label: 'Happy' },
    { key: 'sad', color: '#a78bfa', label: 'Sad' },
    { key: 'angry', color: '#f87171', label: 'Angry' },
    { key: 'neutral', color: '#94a3b8', label: 'Neutral' },
];

export const EmotionTimeline = ({ data }: EmotionTimelineProps) => {
    const [visibleEmotions, setVisibleEmotions] = useState<string[]>(['happy', 'sad', 'angry', 'neutral']);

    const toggleEmotion = (emotion: string) => {
        setVisibleEmotions(prev =>
            prev.includes(emotion)
                ? prev.filter(e => e !== emotion)
                : [...prev, emotion]
        );
    };

    return (
        <div className="w-full h-full flex flex-col">
            <div className="flex flex-wrap items-center justify-between mb-6 gap-4">
                <h3 className="text-lg font-semibold text-slate-200">Emotion Timeline</h3>
            </div>

            {/* Legend / Toggles */}
            <div className="flex flex-wrap gap-3 mb-6">
                {emotionConfig.map((emotion) => (
                    <button
                        key={emotion.key}
                        onClick={() => toggleEmotion(emotion.key)}
                        className={clsx(
                            "flex items-center gap-2 px-3 py-1.5 rounded-full border text-xs font-medium transition-all",
                            visibleEmotions.includes(emotion.key)
                                ? "bg-white/5 border-white/10 text-slate-200"
                                : "bg-transparent border-transparent text-slate-500 opacity-50"
                        )}
                    >
                        <span className="w-2 h-2 rounded-full" style={{ backgroundColor: emotion.color }} />
                        {emotion.label}
                    </button>
                ))}
            </div>

            {/* Chart */}
            <div className="flex-1 min-h-[300px] w-full min-w-0">
                <ResponsiveContainer width="100%" height="100%">
                    <LineChart data={data} margin={{ top: 5, right: 20, bottom: 5, left: 0 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                        <XAxis
                            dataKey="date"
                            stroke="#64748b"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                            dy={10}
                        />
                        <YAxis
                            stroke="#64748b"
                            tick={{ fontSize: 12 }}
                            tickLine={false}
                            axisLine={false}
                            dx={-10}
                        />
                        <Tooltip
                            contentStyle={{ backgroundColor: '#1a1d24', borderColor: '#333', borderRadius: '12px' }}
                            itemStyle={{ fontSize: '12px', padding: 0 }}
                            labelStyle={{ color: '#94a3b8', marginBottom: '8px', fontSize: '12px' }}
                        />
                        {emotionConfig.map((emotion) => (
                            visibleEmotions.includes(emotion.key) && (
                                <Line
                                    key={emotion.key}
                                    type="monotone"
                                    dataKey={emotion.key}
                                    stroke={emotion.color}
                                    strokeWidth={2}
                                    dot={false}
                                    activeDot={{ r: 6, strokeWidth: 0 }}
                                />
                            )
                        ))}
                    </LineChart>
                </ResponsiveContainer>
            </div>
        </div>
    );
};
