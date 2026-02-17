import { useState } from 'react';
import {
    User,
    Settings,
    Shield,
    Bell,
    Download,
    Trash2,
    Save,
    Moon,
    Volume2,
    Globe,
    Clock
} from 'lucide-react';
import { useForm } from 'react-hook-form';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { ConfirmationModal } from '../components/UI/ConfirmationModal';
import { useToast } from '../components/UI/Toast';
import { clsx } from 'clsx';

export const Profile = () => {
    const { user, updateProfile, logout } = useAuthStore();
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'privacy'>('profile');
    const [isDeleting, setIsDeleting] = useState(false);

    const { register, handleSubmit } = useForm({
        defaultValues: {
            name: user?.name || '',
            email: user?.email || '',
        }
    });

    const onSubmitProfile = async (data: any) => {
        await updateProfile(data);
        toast.success('Profile updated successfully');
    };

    const tabs = [
        { id: 'profile', label: 'Personal Info', icon: User },
        { id: 'preferences', label: 'Preferences', icon: Settings },
        { id: 'privacy', label: 'Privacy & Data', icon: Shield },
    ];

    return (
        <div className="container mx-auto px-4 py-8 pb-24 md:pb-8 max-w-4xl animate-in fade-in duration-500">

            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-serif text-slate-100 mb-1">Settings</h1>
                <p className="text-slate-400">Manage your account and preferences.</p>
            </div>

            <div className="flex flex-col md:flex-row gap-8">

                {/* Sidebar Nav */}
                <div className="w-full md:w-64 flex-shrink-0">
                    <div className="glass-panel p-2 rounded-xl border border-white/5 bg-[#0f1115]/50 flex flex-row md:flex-col gap-1 overflow-x-auto md:overflow-visible">
                        {tabs.map((tab) => {
                            const Icon = tab.icon;
                            return (
                                <button
                                    key={tab.id}
                                    onClick={() => setActiveTab(tab.id as any)}
                                    className={clsx(
                                        "flex items-center gap-3 px-4 py-3 rounded-lg text-sm font-medium transition-all whitespace-nowrap",
                                        activeTab === tab.id
                                            ? "bg-teal-500/10 text-teal-400 border border-teal-500/20"
                                            : "text-slate-400 hover:text-slate-200 hover:bg-white/5 border border-transparent"
                                    )}
                                >
                                    <Icon size={18} />
                                    {tab.label}
                                </button>
                            );
                        })}
                    </div>
                </div>

                {/* Content Area */}
                <div className="flex-1">
                    <div className="glass-panel p-6 rounded-2xl border border-white/5 bg-[#0f1115]/50">

                        {/* Personal Info Tab */}
                        {activeTab === 'profile' && (
                            <form onSubmit={handleSubmit(onSubmitProfile)} className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">
                                <div className="flex items-center gap-4 mb-6">
                                    <div className="w-20 h-20 rounded-full bg-gradient-to-tr from-teal-500 to-violet-500 flex items-center justify-center text-3xl font-bold text-white uppercase shadow-xl">
                                        {user?.name?.charAt(0)}
                                    </div>
                                    <div>
                                        <h3 className="text-lg font-medium text-slate-200">{user?.name}</h3>
                                        <p className="text-sm text-slate-400">{user?.email}</p>
                                        <button type="button" className="text-xs text-teal-400 hover:text-teal-300 mt-1">Change Avatar</button>
                                    </div>
                                </div>

                                <div className="grid md:grid-cols-2 gap-4">
                                    <Input label="Full Name" {...register('name')} />
                                    <Input label="Email Address" {...register('email')} />
                                </div>

                                <div className="pt-4 border-t border-white/5">
                                    <h4 className="text-sm font-medium text-slate-300 mb-4">Change Password</h4>
                                    <div className="grid md:grid-cols-2 gap-4">
                                        <Input label="Current Password" type="password" placeholder="••••••••" />
                                        <Input label="New Password" type="password" placeholder="••••••••" />
                                    </div>
                                </div>

                                <div className="pt-4 flex justify-end">
                                    <Button type="submit">Save Changes</Button>
                                </div>
                            </form>
                        )}

                        {/* Preferences Tab */}
                        {activeTab === 'preferences' && (
                            <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-300">

                                {/* Response Style */}
                                <div>
                                    <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
                                        <MessageSquare size={20} className="text-violet-400" /> Response Style
                                    </h3>
                                    <div className="grid md:grid-cols-3 gap-3">
                                        {['Warm & Encouraging', 'Neutral & Objective', 'Direct & Concise'].map((style) => (
                                            <label key={style} className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5 cursor-pointer hover:bg-white/10 transition-colors">
                                                <span className="text-sm text-slate-300">{style}</span>
                                                <input type="radio" name="style" className="accent-teal-500" defaultChecked={style.includes('Warm')} />
                                            </label>
                                        ))}
                                    </div>
                                </div>

                                {/* System Settings */}
                                <div>
                                    <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
                                        <Settings size={20} className="text-blue-400" /> System
                                    </h3>
                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                                            <div className="flex items-center gap-3">
                                                <Moon size={20} className="text-slate-400" />
                                                <div>
                                                    <p className="text-sm font-medium text-slate-200">Dark Mode</p>
                                                    <p className="text-xs text-slate-500">Adaptive therapeutic dark theme</p>
                                                </div>
                                            </div>
                                            <div className="w-10 h-6 bg-teal-500/20 rounded-full relative cursor-pointer border border-teal-500/50">
                                                <div className="w-4 h-4 bg-teal-400 rounded-full absolute top-0.5 right-0.5 shadow-sm" />
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                                            <div className="flex items-center gap-3">
                                                <Volume2 size={20} className="text-slate-400" />
                                                <div>
                                                    <p className="text-sm font-medium text-slate-200">Voice Output</p>
                                                    <p className="text-xs text-slate-500">Enable AI voice responses</p>
                                                </div>
                                            </div>
                                            <div className="w-10 h-6 bg-teal-500/20 rounded-full relative cursor-pointer border border-teal-500/50">
                                                <div className="w-4 h-4 bg-teal-400 rounded-full absolute top-0.5 right-0.5 shadow-sm" />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex justify-end">
                                    <Button>Save Preferences</Button>
                                </div>

                            </div>
                        )}

                        {/* Privacy Tab */}
                        {activeTab === 'privacy' && (
                            <div className="space-y-8 animate-in fade-in slide-in-from-right-4 duration-300">

                                <div>
                                    <h3 className="text-lg font-medium text-slate-200 mb-4 flex items-center gap-2">
                                        <Shield size={20} className="text-green-400" /> Data & Privacy
                                    </h3>
                                    <p className="text-sm text-slate-400 mb-6 leading-relaxed">
                                        MECC is built with privacy-first principles. Your emotional data is processed locally whenever possible and stored securely. You have full control over your data.
                                    </p>

                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                                            <div>
                                                <p className="text-sm font-medium text-slate-200">Store Emotion History</p>
                                                <p className="text-xs text-slate-500">Allow storing emotional trends for dashboard analytics</p>
                                            </div>
                                            <div className="w-10 h-6 bg-teal-500/20 rounded-full relative cursor-pointer border border-teal-500/50">
                                                <div className="w-4 h-4 bg-teal-400 rounded-full absolute top-0.5 right-0.5 shadow-sm" />
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                                            <div>
                                                <p className="text-sm font-medium text-slate-200">Improve AI Model</p>
                                                <p className="text-xs text-slate-500">Share anonymized session data to improve empathy</p>
                                            </div>
                                            <div className="w-10 h-6 bg-white/10 rounded-full relative cursor-pointer border border-white/10">
                                                <div className="w-4 h-4 bg-slate-400 rounded-full absolute top-0.5 left-0.5 shadow-sm" />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-6 border-t border-white/5">
                                    <h3 className="text-sm font-medium text-red-400 mb-4">Danger Zone</h3>
                                    <div className="flex flex-col gap-3">
                                        <Button variant="outline" className="justify-start gap-3 border-white/10 text-slate-300 hover:text-white">
                                            <Download size={18} /> Download My Data
                                        </Button>
                                        <Button
                                            variant="danger"
                                            className="justify-start gap-3"
                                            onClick={() => setIsDeleting(true)}
                                        >
                                            <Trash2 size={18} /> Delete Account & Data
                                        </Button>
                                    </div>
                                </div>

                            </div>
                        )}

                    </div>
                </div>
            </div>

            <ConfirmationModal
                isOpen={isDeleting}
                onClose={() => setIsDeleting(false)}
                onConfirm={() => {
                    logout();
                    toast.success('Account deleted successfully');
                }}
                title="Delete Account"
                message="Are you sure you want to permanently delete your account? This action will remove all your data, session history, and personality capability. This cannot be undone."
                confirmText="Delete Account"
                variant="danger"
            />

        </div>
    );
};
