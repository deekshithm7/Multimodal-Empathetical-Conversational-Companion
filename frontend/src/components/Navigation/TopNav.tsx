import { Link, useNavigate, useLocation } from 'react-router-dom';
import { useState, useRef, useEffect } from 'react';
import {
    LogOut,
    User,
    Settings,
    Menu,
    X,
    Activity,
    MessageSquare,
    LayoutDashboard,
    History
} from 'lucide-react';
import { useAuthStore } from '../../store/useAuthStore';
import { clsx } from 'clsx';
import { motion, AnimatePresence } from 'framer-motion';

export const TopNav = () => {
    const navigate = useNavigate();
    const location = useLocation();
    const { user, logout } = useAuthStore();
    const [isMenuOpen, setIsMenuOpen] = useState(false);
    const dropdownRef = useRef<HTMLDivElement>(null);

    const handleLogout = () => {
        logout();
        navigate('/login');
    };

    const navLinks = [
        { path: '/chat', label: 'Chat', icon: MessageSquare },
        { path: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        { path: '/history', label: 'History', icon: History },
    ];

    return (
        <header className="sticky top-0 z-50 w-full h-16 bg-[#0f1115]/80 backdrop-blur-md border-b border-white/5">
            <div className="container mx-auto px-4 h-full flex items-center justify-between">

                {/* Logo */}
                <Link to="/dashboard" className="flex items-center gap-2 group">
                    <div className="w-8 h-8 rounded-full bg-teal-500/20 flex items-center justify-center group-hover:bg-teal-500/30 transition-colors">
                        <Activity size={18} className="text-teal-400" />
                    </div>
                    <span className="font-serif text-xl text-slate-200 tracking-wide group-hover:text-white transition-colors">
                        MECC
                    </span>
                </Link>

                {/* Desktop Nav */}
                <nav className="hidden md:flex items-center gap-1">
                    {navLinks.map((link) => {
                        const isActive = location.pathname === link.path;
                        const Icon = link.icon;
                        return (
                            <Link
                                key={link.path}
                                to={link.path}
                                className={clsx(
                                    "px-4 py-2 rounded-lg text-sm font-medium transition-all flex items-center gap-2",
                                    isActive
                                        ? "bg-white/10 text-teal-400"
                                        : "text-slate-400 hover:text-slate-200 hover:bg-white/5"
                                )}
                            >
                                <Icon size={16} />
                                {link.label}
                            </Link>
                        );
                    })}
                </nav>

                {/* User Profile Dropdown */}
                <div className="relative" ref={dropdownRef}>
                    <button
                        onClick={() => setIsMenuOpen(!isMenuOpen)}
                        className="flex items-center gap-3 p-1.5 pr-3 rounded-full hover:bg-white/5 transition-colors border border-transparent hover:border-white/10"
                    >
                        <div className="w-8 h-8 rounded-full bg-gradient-to-tr from-teal-500 to-violet-500 flex items-center justify-center text-xs font-bold text-white uppercase">
                            {user?.name?.charAt(0) || 'U'}
                        </div>
                        <span className="hidden sm:block text-sm text-slate-300 font-medium max-w-[100px] truncate">
                            {user?.name || 'User'}
                        </span>
                    </button>

                    <AnimatePresence>
                        {isMenuOpen && (
                            <motion.div
                                initial={{ opacity: 0, y: 10, scale: 0.95 }}
                                animate={{ opacity: 1, y: 0, scale: 1 }}
                                exit={{ opacity: 0, y: 10, scale: 0.95 }}
                                className="absolute right-0 mt-2 w-56 rounded-xl glass-panel border border-white/10 shadow-xl py-2 overflow-hidden"
                            >
                                <div className="px-4 py-3 border-b border-white/5 mb-1">
                                    <p className="text-sm font-medium text-white">{user?.name}</p>
                                    <p className="text-xs text-slate-400 truncate">{user?.email}</p>
                                </div>

                                <Link
                                    to="/profile"
                                    onClick={() => setIsMenuOpen(false)}
                                    className="flex items-center gap-2 px-4 py-2.5 text-sm text-slate-300 hover:text-white hover:bg-white/5 transition-colors"
                                >
                                    <User size={16} /> Profile & Settings
                                </Link>

                                <div className="h-px bg-white/5 my-1" />

                                <button
                                    onClick={handleLogout}
                                    className="w-full flex items-center gap-2 px-4 py-2.5 text-sm text-red-400 hover:text-red-300 hover:bg-red-500/10 transition-colors"
                                >
                                    <LogOut size={16} /> Sign Out
                                </button>
                            </motion.div>
                        )}
                    </AnimatePresence>
                </div>
            </div>
        </header>
    );
};
