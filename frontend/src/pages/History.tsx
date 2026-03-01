import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
    Search,
    Calendar,
    Clock,
    Filter,
    Trash2,
    MessageSquare,
    ArrowRight
} from 'lucide-react';
import { Button } from '../components/UI/Button';
import { EmotionBadge } from '../components/UI/EmotionBadge';
import { ConfirmationModal } from '../components/UI/ConfirmationModal';
import { useToast } from '../components/UI/Toast';
import { api } from '../api/client';
import { LoadingSpinner } from '../components/UI/LoadingSpinner';
import { SessionDetailModal } from '../components/History/SessionDetailModal';

export const History = () => {
    const navigate = useNavigate();
    const toast = useToast();
    const [searchTerm, setSearchTerm] = useState('');
    const [sessions, setSessions] = useState<any[]>([]); // Use appropriate type if available
    const [loading, setLoading] = useState(true);
    const [deleteId, setDeleteId] = useState<string | null>(null);
    const [selectedSessionId, setSelectedSessionId] = useState<string | null>(null);

    useEffect(() => {
        const fetchHistory = async () => {
            try {
                const response = await api.getHistory(50); // Fetch last 50
                setSessions(response.items || []);
            } catch (error) {
                console.error("Failed to fetch history", error);
                // Note: toast intentionally omitted from deps to prevent infinite loop
            } finally {
                setLoading(false);
            }
        };
        fetchHistory();
    }, []); // eslint-disable-line react-hooks/exhaustive-deps

    const filteredSessions = sessions.filter(session => {
        const textToSearch = (session.meta_data?.preview || session.meta_data?.summary || '').toLowerCase();
        const emotion = (session.meta_data?.dominant_emotion || 'neutral').toLowerCase();
        const term = searchTerm.toLowerCase();
        return textToSearch.includes(term) || emotion.includes(term);
    });

    const handleDelete = async () => {
        if (!deleteId) return;
        try {
            await api.deleteSession(deleteId);
            setSessions(prev => prev.filter(s => s.id !== deleteId));
            toast.success("Session deleted successfully");
        } catch (error) {
            console.error("Failed to delete session", error);
            toast.error("Failed to delete session");
        } finally {
            setDeleteId(null);
        }
    };

    if (loading) {
        return (
            <div className="flex items-center justify-center h-screen">
                <LoadingSpinner size={48} />
            </div>
        );
    }

    return (
        <div className="container mx-auto px-4 py-8 pb-24 md:pb-8 max-w-5xl animate-in fade-in duration-500">

            {/* Header */}
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-serif text-slate-100 mb-1">Conversation History</h1>
                    <p className="text-slate-400">Review your past sessions and emotional journey.</p>
                </div>
                <Button onClick={() => navigate('/chat')}>
                    New Session
                </Button>
            </div>

            {/* Filters */}
            <div className="glass-panel p-4 rounded-xl border border-white/5 bg-[#0f1115]/50 mb-6 flex flex-col md:flex-row gap-4 items-center">
                <div className="relative flex-1 w-full">
                    <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={18} />
                    <input
                        type="text"
                        placeholder="Search by keyword, emotion, or date..."
                        className="w-full pl-10 pr-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-slate-200 placeholder:text-slate-500 focus:outline-none focus:border-teal-500/50 transition-colors"
                        value={searchTerm}
                        onChange={(e) => setSearchTerm(e.target.value)}
                    />
                </div>

                <div className="flex gap-2 w-full md:w-auto">
                    <button className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors">
                        <Filter size={18} />
                        <span>Filter</span>
                    </button>
                    <button className="flex-1 md:flex-none flex items-center justify-center gap-2 px-4 py-2.5 bg-white/5 border border-white/10 rounded-lg text-slate-300 hover:text-white hover:bg-white/10 transition-colors">
                        <Calendar size={18} />
                        <span>Date Range</span>
                    </button>
                </div>
            </div>

            {/* Session List */}
            <div className="space-y-4">
                {filteredSessions.length > 0 ? (
                    filteredSessions.map((session) => (
                        <div
                            key={session.id}
                            className="glass-panel p-5 rounded-xl border border-white/5 bg-[#0f1115]/50 hover:bg-white/[0.03] transition-colors group relative"
                        >
                            <div className="flex flex-col md:flex-row gap-4 justify-between">

                                {/* Left: Info */}
                                <div className="flex-1">
                                    <div className="flex items-center gap-3 mb-2">
                                        <EmotionBadge emotion={(session.meta_data?.dominant_emotion || 'neutral') as any} size="sm" showConfidence={false} />
                                        <span className="text-sm text-slate-400 flex items-center gap-1.5">
                                            <Calendar size={14} /> {new Date(session.created_at).toLocaleDateString()} • {new Date(session.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                        </span>
                                    </div>

                                    <h3 className="text-lg font-medium text-slate-200 mb-2 leading-snug">
                                        "{session.meta_data?.summary || 'No summary available'}"
                                    </h3>

                                    <div className="flex items-center gap-4 text-xs text-slate-500">
                                        <span className="flex items-center gap-1.5">
                                            <Clock size={14} /> {session.duration || '0 min'}
                                            {/* Duration calculation logic needed if not in metadata, but backend doesn't send duration in list? 
                                                Actually analytics.py list items are from .to_dict() which has ended_at.
                                                We can calc here or just show placeholder if null.
                                            */}
                                        </span>
                                        <span className="flex items-center gap-1.5">
                                            <MessageSquare size={14} /> {session.total_messages} messages
                                        </span>
                                    </div>
                                </div>

                                {/* Right: Actions */}
                                <div className="flex items-center gap-3 self-start md:self-center mt-2 md:mt-0">
                                    <Button
                                        variant="ghost"
                                        size="sm"
                                        className="hidden md:flex"
                                        onClick={() => setSelectedSessionId(session.id)}
                                    >
                                        View Transcript
                                    </Button>
                                    <button
                                        onClick={() => setDeleteId(session.id)}
                                        className="p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                        title="Delete Session"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                    <button
                                        className="md:hidden p-2 rounded-lg text-teal-400 bg-teal-500/10"
                                        onClick={() => setSelectedSessionId(session.id)}
                                    >
                                        <ArrowRight size={18} />
                                    </button>
                                </div>

                            </div>
                        </div>
                    ))
                ) : (
                    <div className="text-center py-12">
                        <div className="w-16 h-16 bg-white/5 rounded-full flex items-center justify-center mx-auto mb-4">
                            <MessageSquare size={32} className="text-slate-600" />
                        </div>
                        <h3 className="text-lg font-medium text-slate-300 mb-1">No sessions found</h3>
                        <p className="text-slate-500">Try adjusting your search or filters.</p>
                    </div>
                )}
            </div>

            <ConfirmationModal
                isOpen={!!deleteId}
                onClose={() => setDeleteId(null)}
                onConfirm={handleDelete}
                title="Delete Session"
                message="Are you sure you want to delete this session? This action cannot be undone and will remove it from your emotional timeline."
                confirmText="Delete"
                variant="danger"
            />

            <SessionDetailModal
                isOpen={!!selectedSessionId}
                onClose={() => setSelectedSessionId(null)}
                sessionId={selectedSessionId}
            />

        </div>
    );
};
