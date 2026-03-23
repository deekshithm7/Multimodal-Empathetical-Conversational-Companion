import { useNavigate } from 'react-router-dom';
import {
    TrendingUp,
    MessageSquare,
    Mic,
    ArrowRight,
    Calendar,
    Clock
} from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { EmotionTimeline } from '../components/Dashboard/EmotionTimeline';
import { PersonalityRadar } from '../components/Dashboard/PersonalityRadar';
import { Button } from '../components/UI/Button';
import { EmotionBadge } from '../components/UI/EmotionBadge';
import { useEffect, useState } from 'react';
import { api } from '../api/client';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';

export const Dashboard = () => {
    const { user } = useAuthStore();
    const navigate = useNavigate();
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<any>(null);
    const [personalityData, setPersonalityData] = useState<any>(null);

    useEffect(() => {
        const fetchData = async () => {
            try {
                const [stats, personality] = await Promise.all([
                    api.getDashboardStats(),
                    api.getPersonalityProfile(),
                ]);
                setData(stats);
                setPersonalityData(personality);
            } catch (error) {
                console.error("Failed to load dashboard stats", error);
            } finally {
                setLoading(false);
            }
        };
        fetchData();
    }, []);

    const traits = personalityData?.ready && personalityData?.profile 
        ? Object.entries(personalityData.profile).map(([key, val]: any) => ({
            label: key.charAt(0).toUpperCase() + key.slice(1),
            score: Math.round(val.score * 100),
            desc: val.label
        }))
        : [
            { label: 'Openness', score: 0, desc: 'Needs more data' },
            { label: 'Conscientiousness', score: 0, desc: 'Needs more data' },
            { label: 'Extraversion', score: 0, desc: 'Needs more data' },
            { label: 'Agreeableness', score: 0, desc: 'Needs more data' },
            { label: 'Neuroticism', score: 0, desc: 'Needs more data' },
        ];

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <LoadingSpinner size="lg" />
            </div>
        );
    }

    // Process stats for display
    const topEmotion = data?.emotion_distribution
        ? Object.entries(data.emotion_distribution).sort(([, a]: any, [, b]: any) => b - a)[0]?.[0] || 'Neutral'
        : 'Neutral';

    const displayStats: any[] = [
        {
            label: "Dominant Emotion",
            value: topEmotion.charAt(0).toUpperCase() + topEmotion.slice(1),
            icon: <div className="text-2xl">😌</div>,
            sub: "All time"
        },
        {
            label: "Total Conversations",
            value: data?.overview?.total_conversations || 0,
            icon: <MessageSquare className="text-violet-400" size={24} />,
            sub: "Lifetime"
        },
        {
            label: "Avg Duration",
            value: `${Math.round(data?.overview?.average_duration_mins || 0)}m`,
            icon: <TrendingUp className="text-teal-400" size={24} />,
            sub: "Per session"
        },
        {
            label: "Total Messages",
            value: data?.overview?.total_messages || 0,
            icon: <Mic className="text-blue-400" size={24} />,
            sub: "Across all sessions"
        },
    ];

    return (
        <div className="container mx-auto px-4 py-8 pb-24 md:pb-8 max-w-7xl animate-in fade-in duration-500">

            {/* Header */}
            <div className="mb-8 flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h1 className="text-3xl font-serif text-slate-100 mb-1">
                        Welcome back, {user?.name?.split(' ')[0] || 'User'}
                    </h1>
                    <p className="text-slate-400">Here's your emotional insight summary.</p>
                </div>
                <Button onClick={() => navigate('/chat')}>
                    Start Conversation
                </Button>
            </div>

            {/* Stats Grid */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-8">
                {displayStats.map((stat, i) => (
                    <div key={i} className="glass-panel p-5 rounded-xl border border-white/5 bg-[#0f1115]/50 flex flex-col justify-between h-32">
                        <div className="flex justify-between items-start">
                            <span className="p-2 rounded-lg bg-white/5 text-slate-300">
                                {stat.icon}
                            </span>
                        </div>
                        <div>
                            <div className="text-2xl font-bold text-slate-100 mb-0.5">{stat.value}</div>
                            <div className="flex justify-between items-end">
                                <div className="text-xs text-slate-400 font-medium">{stat.label}</div>
                                <div className="text-[10px] text-slate-500">{stat.sub}</div>
                            </div>
                        </div>
                    </div>
                ))}
            </div>

            <div className="grid lg:grid-cols-3 gap-6 mb-8">
                {/* Emotion Timeline (Main Chart) */}
                <div className="lg:col-span-2 glass-panel p-6 rounded-2xl border border-white/5 bg-[#0f1115]/50 min-h-[400px] flex flex-col">
                    <EmotionTimeline data={data?.emotion_timeline || []} />
                </div>

                {/* Personality Profile */}
                <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-[#0f1115]/50 flex flex-col h-full relative">
                    <h3 className="text-lg font-semibold text-slate-200 mb-4">Personality Insights</h3>

                    {!personalityData?.ready && (
                        <div className="absolute inset-0 z-10 bg-[#0f1115]/80 backdrop-blur-sm rounded-2xl flex flex-col items-center justify-center p-6 text-center">
                            <h4 className="text-md font-medium text-slate-200 mb-2">Analyzing Personality...</h4>
                            <p className="text-xs text-slate-400 mb-4">Complete 5 sessions to unlock deep insights.</p>
                            <div className="w-full max-w-[200px] h-2 bg-white/10 rounded-full overflow-hidden">
                                <div 
                                    className="h-full bg-teal-500 rounded-full transition-all" 
                                    style={{ width: `${(Math.min((personalityData?.sessions_complete || 0), 5) / 5) * 100}%` }}
                                />
                            </div>
                            <p className="text-[10px] text-teal-400 mt-2">{personalityData?.sessions_complete || 0} / 5 Sessions</p>
                        </div>
                    )}

                    <div className="flex-1 w-full h-[250px] mb-6 relative">
                        <PersonalityRadar traits={traits} />
                    </div>

                    <div className="space-y-4">
                        {traits.slice(0, 3).map((trait) => (
                            <div key={trait.label} className="group">
                                <div className="flex justify-between text-xs mb-1.5">
                                    <span className="text-slate-300 font-medium group-hover:text-teal-400 transition-colors">{trait.label}</span>
                                    <span className="text-slate-400">{trait.score}%</span>
                                </div>
                                <div className="h-1.5 w-full bg-white/5 rounded-full overflow-hidden">
                                    <div
                                        className="h-full bg-teal-500/50 group-hover:bg-teal-400 transition-colors rounded-full"
                                        style={{ width: `${trait.score}%` }}
                                    />
                                </div>
                                <p className="text-[10px] text-slate-500 mt-1 line-clamp-1">{trait.desc}</p>
                            </div>
                        ))}

                        <button className="w-full mt-2 py-2 text-xs text-teal-400 hover:text-teal-300 hover:bg-teal-500/10 rounded-lg transition-all border border-transparent hover:border-teal-500/20">
                            View Detailed Analysis
                        </button>
                    </div>
                </div>
            </div>

            {/* Recent Sessions */}
            <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-[#0f1115]/50">
                <div className="flex items-center justify-between mb-6">
                    <h3 className="text-lg font-semibold text-slate-200">Recent Sessions</h3>
                    <Button variant="ghost" size="sm" onClick={() => navigate('/history')} className="text-xs">
                        View All History <ArrowRight size={14} className="ml-1" />
                    </Button>
                </div>

                <div className="grid md:grid-cols-3 gap-4">
                    {data?.recent_activity?.map((session: any) => (
                        <div
                            key={session.id}
                            className="p-5 rounded-xl bg-white/5 border border-white/5 hover:border-white/10 hover:bg-white/10 transition-all cursor-pointer group flex flex-col h-full"
                            onClick={() => navigate(`/history?id=${session.id}`)}
                        >
                            <div className="flex justify-between items-start mb-4">
                                <div className="flex items-center gap-2 text-xs text-slate-400">
                                    <Calendar size={14} /> {new Date(session.updated_at || session.created_at).toLocaleDateString()}
                                </div>
                                <EmotionBadge emotion={session.meta_data?.dominant_emotion || 'neutral'} size="sm" showConfidence={false} />
                            </div>

                            <div className="mb-4 flex-1">
                                <p className="text-sm text-slate-300 line-clamp-2 leading-relaxed italic opacity-80 group-hover:opacity-100 transition-opacity">
                                    "{session.meta_data?.summary || 'No summary available'}"
                                </p>
                            </div>

                            <div className="flex items-center justify-between pt-4 border-t border-white/5 mt-auto">
                                <div className="flex items-center gap-1.5 text-xs text-slate-500">
                                    <Clock size={12} /> {session.total_messages} msgs
                                </div>

                                <div className="transform translate-x-2 opacity-0 group-hover:translate-x-0 group-hover:opacity-100 transition-all duration-300 flex items-center text-xs text-teal-400 font-medium">
                                    Details <ArrowRight size={12} className="ml-1" />
                                </div>
                            </div>
                        </div>
                    ))}
                    {(!data?.recent_activity || data.recent_activity.length === 0) && (
                        <div className="col-span-3 text-center py-8 text-slate-500">
                            No recent sessions found. Start a conversation!
                        </div>
                    )}
                </div>
            </div>

        </div>
    );
};
