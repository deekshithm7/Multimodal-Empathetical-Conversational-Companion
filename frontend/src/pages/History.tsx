import { useState } from 'react';
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
import { Input } from '../components/UI/Input';
import { EmotionBadge } from '../components/UI/EmotionBadge';
import { ConfirmationModal } from '../components/UI/ConfirmationModal';
import { useToast } from '../components/UI/Toast';

// Mock Data
const MOCK_SESSIONS = [
    { id: '1', date: 'Feb 17, 2026', time: '2:30 PM', duration: '12 min', emotion: 'calm', preview: "Discussed improving work-life balance and setting boundaries.", messages: 14 },
    { id: '2', date: 'Feb 16, 2026', time: '9:15 AM', duration: '8 min', emotion: 'sad', preview: "Feeling stressed about upcoming deadlines and project scope.", messages: 8 },
    { id: '3', date: 'Feb 12, 2026', time: '6:45 PM', duration: '15 min', emotion: 'happy', preview: "Shared good news about the project launch success.", messages: 22 },
    { id: '4', date: 'Feb 10, 2026', time: '11:20 AM', duration: '20 min', emotion: 'angry', preview: "Frustrated with team communication issues.", messages: 18 },
    { id: '5', date: 'Feb 08, 2026', time: '4:00 PM', duration: '10 min', emotion: 'neutral', preview: "General check-in and weekly planning.", messages: 12 },
];

export const History = () => {
    const navigate = useNavigate();
    const toast = useToast();
    const [searchTerm, setSearchTerm] = useState('');
    const [sessions, setSessions] = useState(MOCK_SESSIONS);
    const [deleteId, setDeleteId] = useState<string | null>(null);

    const filteredSessions = sessions.filter(session =>
        session.preview.toLowerCase().includes(searchTerm.toLowerCase()) ||
        session.emotion.includes(searchTerm.toLowerCase())
    );

    const handleDelete = () => {
        if (!deleteId) return;
        setSessions(prev => prev.filter(s => s.id !== deleteId));
        setDeleteId(null);
        toast.success('Session deleted successfully');
    };

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
                                        <EmotionBadge emotion={session.emotion as any} size="sm" showConfidence={false} />
                                        <span className="text-sm text-slate-400 flex items-center gap-1.5">
                                            <Calendar size={14} /> {session.date} • {session.time}
                                        </span>
                                    </div>

                                    <h3 className="text-lg font-medium text-slate-200 mb-2 leading-snug">
                                        "{session.preview}"
                                    </h3>

                                    <div className="flex items-center gap-4 text-xs text-slate-500">
                                        <span className="flex items-center gap-1.5">
                                            <Clock size={14} /> {session.duration}
                                        </span>
                                        <span className="flex items-center gap-1.5">
                                            <MessageSquare size={14} /> {session.messages} messages
                                        </span>
                                    </div>
                                </div>

                                {/* Right: Actions */}
                                <div className="flex items-center gap-3 self-start md:self-center mt-2 md:mt-0">
                                    <Button variant="ghost" size="sm" className="hidden md:flex">
                                        View Transcript
                                    </Button>
                                    <button
                                        onClick={() => setDeleteId(session.id)}
                                        className="p-2 rounded-lg text-slate-500 hover:text-red-400 hover:bg-red-500/10 transition-colors"
                                        title="Delete Session"
                                    >
                                        <Trash2 size={18} />
                                    </button>
                                    <button className="md:hidden p-2 rounded-lg text-teal-400 bg-teal-500/10">
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

        </div>
    );
};
