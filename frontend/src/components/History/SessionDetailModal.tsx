import { useEffect, useState } from 'react';
import { X, Clock, Calendar, MessageSquare, Play } from 'lucide-react';
import { api } from '../../api/client';
import { LoadingSpinner } from '../UI/LoadingSpinner';
import { EmotionBadge } from '../UI/EmotionBadge';
import { EmotionTimeline } from '../Dashboard/EmotionTimeline';

interface SessionDetailModalProps {
    isOpen: boolean;
    onClose: () => void;
    sessionId: string | null;
}

export const SessionDetailModal = ({ isOpen, onClose, sessionId }: SessionDetailModalProps) => {
    const [loading, setLoading] = useState(true);
    const [data, setData] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);
    const [playingAudio, setPlayingAudio] = useState<string | null>(null);

    useEffect(() => {
        if (isOpen && sessionId) {
            setLoading(true);
            setError(null);
            api.getSessionDetail(sessionId)
                .then(setData)
                .catch((err) => setError(err.message))
                .finally(() => setLoading(false));
        } else {
            setData(null);
        }
    }, [isOpen, sessionId]);

    if (!isOpen) return null;

    const handlePlayAudio = (path: string) => {
        if (playingAudio === path) {
            // Stop logic if we tracked audio element ref, for now just simple play
            // Actually let's assume simple play for now.
            return;
        }

        const audio = new Audio(api.getAudioUrl(path));
        audio.play();
        setPlayingAudio(path);
        audio.onended = () => setPlayingAudio(null);
    };

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-in fade-in duration-200">
            <div className="bg-[#0f1115] border border-white/10 rounded-2xl w-full max-w-4xl max-h-[90vh] flex flex-col shadow-2xl overflow-hidden glass-panel">

                {/* Header */}
                <div className="p-6 border-b border-white/10 flex justify-between items-center bg-white/5">
                    <div>
                        <h2 className="text-xl font-serif text-slate-100">Session Details</h2>
                        {data && (
                            <div className="flex items-center gap-3 mt-1 text-sm text-slate-400">
                                <span className="flex items-center gap-1"><Calendar size={14} /> {data.summary.started_at ? new Date(data.summary.started_at).toLocaleDateString() : 'Unknown Date'}</span>
                                <span className="flex items-center gap-1"><Clock size={14} /> {data.summary.started_at ? new Date(data.summary.started_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }) : ''}</span>
                            </div>
                        )}
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-lg text-slate-400 hover:text-white transition-colors">
                        <X size={24} />
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto p-6 space-y-8">
                    {loading ? (
                        <div className="flex justify-center py-20">
                            <LoadingSpinner size={48} />
                        </div>
                    ) : error ? (
                        <div className="text-center text-red-400 py-10">
                            Failed to load session details: {error}
                        </div>
                    ) : data ? (
                        <>
                            {/* Summary Card */}
                            <div className="grid md:grid-cols-3 gap-6">
                                <div className="md:col-span-2 space-y-6">
                                    <div className="bg-white/5 rounded-xl p-4 border border-white/10 h-[300px] flex flex-col">
                                        <EmotionTimeline data={(data.emotion_timeline || [])
                                            .filter((_: any, i: number, arr: any[]) => {
                                                const step = Math.max(1, Math.floor(arr.length / 100)); // Max ~100 points
                                                return i % step === 0;
                                            })
                                            .map((e: any) => ({
                                                date: new Date(e.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
                                                [e.emotion]: e.confidence * 100
                                            }))} />
                                    </div>

                                    {/* Transcript */}
                                    <div className="bg-white/5 rounded-xl p-6 border border-white/10">
                                        <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
                                            <MessageSquare size={18} /> Transcript
                                        </h3>
                                        <div className="space-y-6">
                                            {data.messages.map((msg: any) => (
                                                <div key={msg.id} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                                                    <div className={`w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 ${msg.role === 'user' ? 'bg-teal-500/20 text-teal-400' : 'bg-violet-500/20 text-violet-400'
                                                        }`}>
                                                        {msg.role === 'user' ? 'U' : 'AI'}
                                                    </div>
                                                    <div className={`flex-1 max-w-[80%] space-y-2`}>
                                                        <div className={`p-4 rounded-2xl ${msg.role === 'user'
                                                            ? 'bg-teal-500/10 border border-teal-500/20 text-slate-200 rounded-tr-none'
                                                            : 'bg-white/5 border border-white/10 text-slate-300 rounded-tl-none'
                                                            }`}>
                                                            <p className="whitespace-pre-wrap">{msg.content}</p>
                                                        </div>

                                                        {msg.role === 'user' && msg.detected_emotion && (
                                                            <div className="flex justify-end">
                                                                <EmotionBadge emotion={msg.detected_emotion} size="sm" />
                                                            </div>
                                                        )}

                                                        {msg.has_audio && msg.audio_path && (
                                                            <button
                                                                onClick={() => handlePlayAudio(msg.audio_path)}
                                                                className="flex items-center gap-2 text-xs text-slate-500 hover:text-teal-400 transition-colors"
                                                            >
                                                                <Play size={12} className={playingAudio === msg.audio_path ? 'text-teal-400 fill-teal-400' : ''} />
                                                                {msg.audio_duration ? `${msg.audio_duration.toFixed(1)}s Audio` : 'Play Audio'}
                                                            </button>
                                                        )}
                                                    </div>
                                                </div>
                                            ))}
                                        </div>
                                    </div>
                                </div>

                                {/* Sidebar Stats */}
                                <div className="space-y-4">
                                    <div className="bg-white/5 rounded-xl p-5 border border-white/10">
                                        <h4 className="text-sm font-medium text-slate-400 uppercase tracking-wider mb-4">Session Stats</h4>
                                        <dl className="space-y-4">
                                            <div>
                                                <dt className="text-xs text-slate-500 mb-1">Duration</dt>
                                                <dd className="text-lg font-medium text-slate-200">
                                                    {data.summary.ended_at && data.summary.started_at
                                                        ? Math.round((new Date(data.summary.ended_at).getTime() - new Date(data.summary.started_at).getTime()) / 60000)
                                                        : 0} mins
                                                </dd>
                                            </div>
                                            <div>
                                                <dt className="text-xs text-slate-500 mb-1">Messages</dt>
                                                <dd className="text-lg font-medium text-slate-200">{data.summary.total_messages}</dd>
                                            </div>
                                            <div>
                                                <dt className="text-xs text-slate-500 mb-1">Status</dt>
                                                <dd className="capitalize text-slate-200">{data.summary.status}</dd>
                                            </div>
                                        </dl>
                                    </div>
                                </div>
                            </div>
                        </>
                    ) : null}
                </div>
            </div>
        </div>
    );
};
