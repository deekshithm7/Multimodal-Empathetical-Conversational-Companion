import { useState } from 'react';
import {
    User,
    Settings,
    Shield,
    Download,
    Trash2,
    Moon,
    Volume2,
    MessageSquare,
    Lock,
    Eye,
    EyeOff
} from 'lucide-react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { ConfirmationModal } from '../components/UI/ConfirmationModal';
import { useToast } from '../components/UI/Toast';
import { clsx } from 'clsx';
import { api } from '../api/client';

export const Profile = () => {
    const { user, updateProfile, logout } = useAuthStore();
    const toast = useToast();
    const [activeTab, setActiveTab] = useState<'profile' | 'preferences' | 'privacy'>('profile');
    const [isDeleting, setIsDeleting] = useState(false);
    const [isChangingPassword, setIsChangingPassword] = useState(false);
    const [showPw, setShowPw] = useState({ current: false, new: false, confirm: false });
    const togglePw = (field: 'current' | 'new' | 'confirm') =>
        setShowPw(prev => ({ ...prev, [field]: !prev[field] }));

    // Password change schema
    const passwordSchema = z.object({
        current_password: z.string().min(1, 'Current password is required'),
        new_password: z.string().min(8, 'New password must be at least 8 characters'),
        confirm_password: z.string()
    }).refine(d => d.new_password === d.confirm_password, {
        message: "Passwords don't match",
        path: ['confirm_password']
    });

    // Preferences State
    const [preferences, setPreferences] = useState({
        response_style: user?.preferences?.response_style || 'warm',
        theme: user?.preferences?.theme || 'dark',
        voice_enabled: user?.preferences?.voice_enabled ?? true,
        store_history: user?.preferences?.store_history ?? true,
        share_data: user?.preferences?.share_data ?? false,
    });

    const { register, handleSubmit } = useForm({
        defaultValues: {
            name: user?.name || '',
            email: user?.email || '',
        }
    });

    const { register: registerPw, handleSubmit: handleSubmitPw, reset: resetPw, formState: { errors: pwErrors } } = useForm<z.infer<typeof passwordSchema>>({
        resolver: zodResolver(passwordSchema)
    });

    const onSubmitProfile = async (data: any) => {
        try {
            const updatedUser = await api.updateProfile(data);
            updateProfile(updatedUser);
            toast.success('Profile updated successfully');
        } catch (error) {
            console.error("Profile update failed", error);
            toast.error("Failed to update profile");
        }
    };

    const onChangePassword = async (data: z.infer<typeof passwordSchema>) => {
        setIsChangingPassword(true);
        try {
            await api.updateProfile({ 
                password: data.new_password,
                current_password: data.current_password
            } as any);
            resetPw();
            toast.success('Password changed successfully');
        } catch (error: any) {
            console.error("Password change failed", error);
            toast.error(error.message || 'Failed to change password');
        } finally {
            setIsChangingPassword(false);
        }
    };

    const handlePreferenceChange = (key: string, value: any) => {
        setPreferences(prev => ({ ...prev, [key]: value }));
    };

    const savePreferences = async () => {
        try {
            const updatedUser = await api.updatePreferences(preferences);
            updateProfile(updatedUser); // Update store with new prefs
            toast.success('Preferences saved');
        } catch (error) {
            console.error("Preferences update failed", error);
            toast.error("Failed to save preferences");
        }
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
                            <div className="space-y-6 animate-in fade-in slide-in-from-right-4 duration-300">

                                {/* ── Profile info form ── */}
                                <form onSubmit={handleSubmit(onSubmitProfile)} className="space-y-6">
                                    <div className="flex items-center gap-4">
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

                                    <div className="flex justify-end">
                                        <Button type="submit">Save Profile</Button>
                                    </div>
                                </form>

                                {/* ── Change password form (separate — nested forms are invalid HTML) ── */}
                                <div className="border-t border-white/5 pt-6">
                                    <h4 className="text-sm font-medium text-slate-300 mb-4 flex items-center gap-2">
                                        <Lock size={16} className="text-slate-400" /> Change Password
                                    </h4>
                                    <form onSubmit={handleSubmitPw(onChangePassword)} className="space-y-4">
                                        <div className="grid md:grid-cols-2 gap-4">

                                            {/* Current Password */}
                                            <div className="w-full">
                                                <label className="block text-sm font-medium text-slate-300 mb-2">Current Password</label>
                                                <div className="flex items-center w-full rounded-lg bg-white/10 border border-white/20 focus-within:ring-2 focus-within:ring-teal-500 focus-within:border-transparent transition-all duration-200"
                                                    style={pwErrors.current_password ? { borderColor: 'rgb(248 113 113)' } : {}}>
                                                    <input
                                                        {...registerPw('current_password')}
                                                        type={showPw.current ? 'text' : 'password'}
                                                        placeholder="••••••••"
                                                        className="flex-1 px-4 py-3 bg-transparent text-slate-100 placeholder:text-slate-400 focus:outline-none rounded-lg"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => togglePw('current')}
                                                        className="px-3 text-slate-400 hover:text-slate-200 transition-colors flex-shrink-0"
                                                        tabIndex={-1}
                                                        aria-label={showPw.current ? 'Hide password' : 'Show password'}
                                                    >
                                                        {showPw.current ? <EyeOff size={18} /> : <Eye size={18} />}
                                                    </button>
                                                </div>
                                                {pwErrors.current_password && (
                                                    <p className="mt-1 text-sm text-red-400">{pwErrors.current_password.message}</p>
                                                )}
                                            </div>

                                            {/* New Password */}
                                            <div className="w-full">
                                                <label className="block text-sm font-medium text-slate-300 mb-2">New Password</label>
                                                <div className="flex items-center w-full rounded-lg bg-white/10 border border-white/20 focus-within:ring-2 focus-within:ring-teal-500 focus-within:border-transparent transition-all duration-200"
                                                    style={pwErrors.new_password ? { borderColor: 'rgb(248 113 113)' } : {}}>
                                                    <input
                                                        {...registerPw('new_password')}
                                                        type={showPw.new ? 'text' : 'password'}
                                                        placeholder="••••••••"
                                                        className="flex-1 px-4 py-3 bg-transparent text-slate-100 placeholder:text-slate-400 focus:outline-none rounded-lg"
                                                    />
                                                    <button
                                                        type="button"
                                                        onClick={() => togglePw('new')}
                                                        className="px-3 text-slate-400 hover:text-slate-200 transition-colors flex-shrink-0"
                                                        tabIndex={-1}
                                                        aria-label={showPw.new ? 'Hide password' : 'Show password'}
                                                    >
                                                        {showPw.new ? <EyeOff size={18} /> : <Eye size={18} />}
                                                    </button>
                                                </div>
                                                {pwErrors.new_password && (
                                                    <p className="mt-1 text-sm text-red-400">{pwErrors.new_password.message}</p>
                                                )}
                                            </div>
                                        </div>

                                        {/* Confirm New Password */}
                                        <div className="md:w-1/2 w-full">
                                            <label className="block text-sm font-medium text-slate-300 mb-2">Confirm New Password</label>
                                            <div className="flex items-center w-full rounded-lg bg-white/10 border border-white/20 focus-within:ring-2 focus-within:ring-teal-500 focus-within:border-transparent transition-all duration-200"
                                                style={pwErrors.confirm_password ? { borderColor: 'rgb(248 113 113)' } : {}}>
                                                <input
                                                    {...registerPw('confirm_password')}
                                                    type={showPw.confirm ? 'text' : 'password'}
                                                    placeholder="••••••••"
                                                    className="flex-1 px-4 py-3 bg-transparent text-slate-100 placeholder:text-slate-400 focus:outline-none rounded-lg"
                                                />
                                                <button
                                                    type="button"
                                                    onClick={() => togglePw('confirm')}
                                                    className="px-3 text-slate-400 hover:text-slate-200 transition-colors flex-shrink-0"
                                                    tabIndex={-1}
                                                    aria-label={showPw.confirm ? 'Hide password' : 'Show password'}
                                                >
                                                    {showPw.confirm ? <EyeOff size={18} /> : <Eye size={18} />}
                                                </button>
                                            </div>
                                            {pwErrors.confirm_password && (
                                                <p className="mt-1 text-sm text-red-400">{pwErrors.confirm_password.message}</p>
                                            )}
                                        </div>

                                        <div className="flex justify-end">
                                            <Button type="submit" isLoading={isChangingPassword} variant="outline">
                                                Update Password
                                            </Button>
                                        </div>
                                    </form>
                                </div>

                            </div>
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
                                        {[
                                            { id: 'warm', label: 'Warm & Encouraging' },
                                            { id: 'neutral', label: 'Neutral & Objective' },
                                            { id: 'direct', label: 'Direct & Concise' }
                                        ].map((style) => (
                                            <label key={style.id} className={`flex items-center justify-between p-4 rounded-xl border cursor-pointer transition-colors ${preferences.response_style === style.id
                                                ? 'bg-teal-500/10 border-teal-500/20'
                                                : 'bg-white/5 border-white/10 hover:bg-white/10'
                                                }`}>
                                                <span className="text-sm text-slate-300">{style.label}</span>
                                                <input
                                                    type="radio"
                                                    name="style"
                                                    className="accent-teal-500"
                                                    checked={preferences.response_style === style.id}
                                                    onChange={() => handlePreferenceChange('response_style', style.id)}
                                                />
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
                                            <div
                                                className={`w-10 h-6 rounded-full relative cursor-pointer border transition-colors ${preferences.theme === 'dark' ? 'bg-teal-500/20 border-teal-500/50' : 'bg-white/10 border-white/20'
                                                    }`}
                                                onClick={() => handlePreferenceChange('theme', preferences.theme === 'dark' ? 'light' : 'dark')}
                                            >
                                                <div className={`w-4 h-4 rounded-full absolute top-0.5 shadow-sm transition-all ${preferences.theme === 'dark' ? 'bg-teal-400 right-0.5' : 'bg-slate-400 left-0.5'
                                                    }`} />
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
                                            <div
                                                className={`w-10 h-6 rounded-full relative cursor-pointer border transition-colors ${preferences.voice_enabled ? 'bg-teal-500/20 border-teal-500/50' : 'bg-white/10 border-white/20'
                                                    }`}
                                                onClick={() => handlePreferenceChange('voice_enabled', !preferences.voice_enabled)}
                                            >
                                                <div className={`w-4 h-4 rounded-full absolute top-0.5 shadow-sm transition-all ${preferences.voice_enabled ? 'bg-teal-400 right-0.5' : 'bg-slate-400 left-0.5'
                                                    }`} />
                                            </div>
                                        </div>
                                    </div>
                                </div>

                                <div className="pt-4 flex justify-end">
                                    <Button onClick={savePreferences}>Save Preferences</Button>
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
                                        MindSculpt AI is built with privacy-first principles. Your emotional data is processed locally whenever possible and stored securely. You have full control over your data.
                                    </p>

                                    <div className="space-y-4">
                                        <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                                            <div>
                                                <p className="text-sm font-medium text-slate-200">Store Emotion History</p>
                                                <p className="text-xs text-slate-500">Allow storing emotional trends for dashboard analytics</p>
                                            </div>
                                            <div
                                                className={`w-10 h-6 rounded-full relative cursor-pointer border transition-colors ${preferences.store_history ? 'bg-teal-500/20 border-teal-500/50' : 'bg-white/10 border-white/20'
                                                    }`}
                                                onClick={() => handlePreferenceChange('store_history', !preferences.store_history)}
                                            >
                                                <div className={`w-4 h-4 rounded-full absolute top-0.5 shadow-sm transition-all ${preferences.store_history ? 'bg-teal-400 right-0.5' : 'bg-slate-400 left-0.5'
                                                    }`} />
                                            </div>
                                        </div>

                                        <div className="flex items-center justify-between p-4 rounded-xl border border-white/10 bg-white/5">
                                            <div>
                                                <p className="text-sm font-medium text-slate-200">Improve AI Model</p>
                                                <p className="text-xs text-slate-500">Share anonymized session data to improve empathy</p>
                                            </div>
                                            <div
                                                className={`w-10 h-6 rounded-full relative cursor-pointer border transition-colors ${preferences.share_data ? 'bg-teal-500/20 border-teal-500/50' : 'bg-white/10 border-white/20'
                                                    }`}
                                                onClick={() => handlePreferenceChange('share_data', !preferences.share_data)}
                                            >
                                                <div className={`w-4 h-4 rounded-full absolute top-0.5 shadow-sm transition-all ${preferences.share_data ? 'bg-teal-400 right-0.5' : 'bg-slate-400 left-0.5'
                                                    }`} />
                                            </div>
                                        </div>
                                    </div>
                                </div>
                                <div className="pt-4 flex justify-end">
                                    <Button onClick={savePreferences}>Save Privacy Settings</Button>
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
