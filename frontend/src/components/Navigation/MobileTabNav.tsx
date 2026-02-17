import { useNavigate, useLocation } from 'react-router-dom';
import { MessageSquare, LayoutDashboard, History, User } from 'lucide-react';
import { clsx } from 'clsx';

export const MobileTabNav = () => {
    const navigate = useNavigate();
    const location = useLocation();

    const tabs = [
        { path: '/chat', label: 'Chat', icon: MessageSquare },
        { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { path: '/history', label: 'History', icon: History },
        { path: '/profile', label: 'Profile', icon: User },
    ];

    return (
        <div className="md:hidden fixed bottom-0 left-0 right-0 h-16 bg-[#0f1115]/95 backdrop-blur-lg border-t border-white/10 z-50 flex items-center justify-around px-2">
            {tabs.map((tab) => {
                const isActive = location.pathname === tab.path;
                const Icon = tab.icon;

                return (
                    <button
                        key={tab.path}
                        onClick={() => navigate(tab.path)}
                        className="flex flex-col items-center justify-center w-full h-full gap-1"
                    >
                        <div className={clsx(
                            "p-1.5 rounded-full transition-all",
                            isActive ? "bg-teal-500/20 text-teal-400" : "text-slate-500"
                        )}>
                            <Icon size={20} />
                        </div>
                        <span className={clsx(
                            "text-[10px] font-medium block",
                            isActive ? "text-teal-400" : "text-slate-500"
                        )}>
                            {tab.label}
                        </span>
                    </button>
                );
            })}
        </div>
    );
};
