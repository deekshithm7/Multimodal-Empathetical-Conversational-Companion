import { useState, useEffect } from 'react';
import { Activity, TrendingUp, Shield } from 'lucide-react';
import { api } from '../api/client';
import { PersonalityRadar } from '../components/Dashboard/PersonalityRadar';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import {
    LineChart,
    Line,
    XAxis,
    YAxis,
    CartesianGrid,
    Tooltip,
    ResponsiveContainer,
    Legend
} from 'recharts';

export const Insights = () => {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<any>(null);

    useEffect(() => {
        api.getPersonalityProfile()
            .then(setData)
            .catch(console.error)
            .finally(() => setLoading(false));
    }, []);

    // Format session history for the chart
    const historyData = data?.session_history?.map((s: any) => ({
        date: new Date(s.timestamp).toLocaleDateString(),
        ...s.session_score
    })) || [];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-[calc(100vh-64px)]">
                <LoadingSpinner size={48} />
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 pb-24 md:pb-8 max-w-6xl animate-in fade-in duration-500">
            <div className="mb-8">
                <h1 className="text-3xl font-serif text-slate-100 mb-1 flex items-center gap-3">
                    <Activity className="text-teal-400" /> Advanced Personality Insights
                </h1>
                <p className="text-slate-400">Comprehensive analysis of your multimodal interactions over time.</p>
            </div>

            <div className="grid lg:grid-cols-2 gap-8">
                {/* Radar Chart (Stable Profile) */}
                <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-[#0f1115]/50 flex flex-col items-center">
                    <h3 className="text-xl font-medium text-slate-200 mb-6 self-start w-full border-b border-white/5 pb-4">
                        Current Stable Profile
                    </h3>
                    {data && data.profile ? (
                        <div className="w-full max-w-md h-[400px]">
                            <PersonalityRadar traits={Object.entries(data.profile).map(([k, v]: [string, any]) => ({
                                label: k.charAt(0).toUpperCase() + k.slice(1),
                                score: v.score * 100,
                                desc: v.label
                            }))} />
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-center p-8">
                            <Shield size={48} className="text-teal-500/50 mb-4" />
                            <h3 className="text-lg font-medium text-slate-200 mb-2">Insufficient Data</h3>
                            <p className="text-sm text-slate-400 max-w-xs">
                                Your stable personality profile will be generated after completing 5 sessions. You currently have {data?.sessions_complete || 0}.
                            </p>
                        </div>
                    )}
                </div>

                {/* Historical Line Chart */}
                <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-[#0f1115]/50 flex flex-col">
                    <h3 className="text-xl font-medium text-slate-200 mb-6 w-full border-b border-white/5 pb-4 flex items-center gap-2">
                        <TrendingUp size={20} className="text-violet-400" /> Traits Over Time
                    </h3>
                    {historyData.length > 0 ? (
                        <div className="flex-1 w-full min-h-[400px]">
                            <ResponsiveContainer width="100%" height="100%">
                                <LineChart data={historyData} margin={{ top: 20, right: 30, left: 0, bottom: 0 }}>
                                    <CartesianGrid strokeDasharray="3 3" stroke="#333" vertical={false} />
                                    <XAxis dataKey="date" stroke="#64748b" tick={{ fontSize: 12 }} />
                                    <YAxis stroke="#64748b" tick={{ fontSize: 12 }} domain={[0, 1]} />
                                    <Tooltip 
                                        contentStyle={{ backgroundColor: '#1a1d24', borderColor: '#333', borderRadius: '12px' }}
                                    />
                                    <Legend />
                                    <Line type="monotone" dataKey="openness" stroke="#4ade80" strokeWidth={2} name="Openness" />
                                    <Line type="monotone" dataKey="conscientiousness" stroke="#60a5fa" strokeWidth={2} name="Conscientious" />
                                    <Line type="monotone" dataKey="extraversion" stroke="#f87171" strokeWidth={2} name="Extraversion" />
                                    <Line type="monotone" dataKey="agreeableness" stroke="#a78bfa" strokeWidth={2} name="Agreeableness" />
                                    <Line type="monotone" dataKey="neuroticism" stroke="#fb923c" strokeWidth={2} name="Neuroticism" />
                                </LineChart>
                            </ResponsiveContainer>
                        </div>
                    ) : (
                        <div className="flex-1 flex items-center justify-center text-slate-400">
                            Complete a session to see your trait history.
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};
