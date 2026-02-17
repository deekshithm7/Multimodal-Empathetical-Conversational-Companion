import { motion } from 'framer-motion';
import { ArrowUpRight, BarChart2, Activity } from 'lucide-react';
import { useEmotionStore, type Emotion } from '../../store/useEmotionStore';
import { Link } from 'react-router-dom';
import { PieChart as RechartsPie, Pie, Cell, ResponsiveContainer, Tooltip } from 'recharts';

// Mock data helpers
const getEmotionBreakdown = (current: Emotion) => {
    const base = { neutral: 10, happy: 5, sad: 5, angry: 2, calm: 10, fearful: 1, surprised: 2, disgust: 0 };

    if (current !== 'neutral') {
        // Boost current emotion
        // @ts-ignore
        base[current] = (base[current] || 0) + 40;
    }

    // Normalize roughly
    return Object.entries(base).map(([key, value]) => ({
        label: key.charAt(0).toUpperCase() + key.slice(1),
        value,
        color: getEmotionColor(key as Emotion)
    })).sort((a, b) => b.value - a.value).slice(0, 5);
};

const getEmotionColor = (emotion: Emotion) => {
    switch (emotion) {
        case 'happy': return '#4ade80';
        case 'sad': return '#a78bfa';
        case 'angry': return '#f87171';
        case 'calm': return '#60a5fa';
        case 'fearful': return '#fb923c';
        case 'surprised': return '#facc15';
        default: return '#94a3b8';
    }
};

const ModalityData = [
    { name: 'Audio', value: 45, color: '#00C9A7' },
    { name: 'Visual', value: 30, color: '#7B61FF' },
    { name: 'Text', value: 25, color: '#60A5FA' },
];

export const EmotionPanel = () => {
    const { currentEmotion } = useEmotionStore();
    const breakdown = getEmotionBreakdown(currentEmotion);

    return (
        <div className="h-full flex flex-col gap-4 p-4 glass-panel rounded-2xl border border-white/5 bg-[#0f1115]/50">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">Emotional State</h3>
                <Activity size={14} className="text-slate-500" />
            </div>

            {/* Current Emotion Card */}
            <div className="p-4 rounded-xl bg-gradient-to-br from-white/5 to-transparent border border-white/5 flex items-center justify-between">
                <div>
                    <p className="text-xs text-slate-400 mb-1">Dominant Emotion</p>
                    <div className="flex items-center gap-2">
                        <span className="text-2xl capitalize font-serif text-slate-100">{currentEmotion}</span>
                        <span className="text-xs px-1.5 py-0.5 rounded bg-white/10 text-slate-300">78%</span>
                    </div>
                </div>
                <div
                    className="w-10 h-10 rounded-full flex items-center justify-center text-xl"
                    style={{ backgroundColor: `${getEmotionColor(currentEmotion)}20`, color: getEmotionColor(currentEmotion) }}
                >
                    {currentEmotion === 'happy' ? '😊' :
                        currentEmotion === 'sad' ? '😔' :
                            currentEmotion === 'angry' ? '😤' :
                                currentEmotion === 'calm' ? '😌' : '😐'}
                </div>
            </div>

            {/* Breakdown Chart */}
            <div className="flex-1 min-h-[140px]">
                <div className="flex items-center justify-between mb-3">
                    <p className="text-xs text-slate-400 font-medium">Live Breakdown</p>
                    <BarChart2 size={12} className="text-slate-600" />
                </div>

                <div className="space-y-3">
                    {breakdown.map((item) => (
                        <div key={item.label}>
                            <div className="flex justify-between text-[10px] text-slate-400 mb-1">
                                <span>{item.label}</span>
                                <span>{item.value}%</span>
                            </div>
                            <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                <motion.div
                                    initial={{ width: 0 }}
                                    animate={{ width: `${item.value}%` }}
                                    transition={{ duration: 0.5 }}
                                    className="h-full rounded-full"
                                    style={{ backgroundColor: item.color }}
                                />
                            </div>
                        </div>
                    ))}
                </div>
            </div>

            {/* Simple Modality Weights Donut */}
            <div className="h-48 relative w-full min-w-0 flex flex-col">
                <p className="text-xs text-slate-400 font-medium mb-2">Input Weights</p>
                <div className="flex-1 min-h-0 w-full relative">
                    <ResponsiveContainer width="100%" height="100%">
                        <RechartsPie>
                            <Pie
                                data={ModalityData}
                                cx="50%"
                                cy="50%"
                                innerRadius={30}
                                outerRadius={45}
                                paddingAngle={5}
                                dataKey="value"
                                stroke="none"
                            >
                                {ModalityData.map((entry, index) => (
                                    <Cell key={`cell-${index}`} fill={entry.color} />
                                ))}
                            </Pie>
                            <Tooltip
                                contentStyle={{ backgroundColor: '#1a1d24', borderColor: '#333', borderRadius: '8px', fontSize: '12px' }}
                                itemStyle={{ color: '#ccc' }}
                            />
                        </RechartsPie>
                    </ResponsiveContainer>
                </div>

                {/* Legend */}
                <div className="flex justify-center gap-3 text-[10px] text-slate-500 w-full mt-2">
                    {ModalityData.map(item => (
                        <div key={item.name} className="flex items-center gap-1">
                            <div className="w-1.5 h-1.5 rounded-full" style={{ backgroundColor: item.color }} />
                            {item.name}
                        </div>
                    ))}
                </div>
            </div>

            <Link
                to="/dashboard"
                className="mt-auto flex items-center justify-center gap-2 py-3 px-4 rounded-xl bg-white/5 hover:bg-white/10 transition-colors text-xs text-slate-300 font-medium border border-white/5 hover:border-white/20 group"
            >
                View Full Dashboard
                <ArrowUpRight size={14} className="opacity-50 group-hover:opacity-100 transition-opacity" />
            </Link>

        </div>
    );
};
