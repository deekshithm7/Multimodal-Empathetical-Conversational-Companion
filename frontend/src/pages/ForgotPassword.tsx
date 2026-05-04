import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, CheckCircle, Mail, Copy, ExternalLink } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { useToast } from '../components/UI/Toast';
import { api } from '../api/client';

const forgotPasswordSchema = z.object({
    email: z.string().email('Invalid email address')
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export const ForgotPassword = () => {
    const { isLoading } = useAuthStore();
    const toast = useToast();
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [cooldown, setCooldown] = useState(0);
    const [resetToken, setResetToken] = useState<string | null>(null);
    const [resetUrl, setResetUrl] = useState<string | null>(null);

    const {
        register,
        handleSubmit,
        getValues,
        formState: { errors }
    } = useForm<ForgotPasswordFormData>({
        resolver: zodResolver(forgotPasswordSchema)
    });

    const onSubmit = async (data: ForgotPasswordFormData) => {
        try {
            const result = await api.forgotPassword(data.email);
            setIsSubmitted(true);
            if (result.token) {
                setResetToken(result.token);
                setResetUrl(result.reset_url || `/reset-password?token=${result.token}`);
            }
            startCooldown();
        } catch (err: any) {
            toast.error(err.message || 'Failed to request password reset');
        }
    };

    const startCooldown = () => {
        setCooldown(60);
        const interval = setInterval(() => {
            setCooldown((prev) => {
                if (prev <= 1) {
                    clearInterval(interval);
                    return 0;
                }
                return prev - 1;
            });
        }, 1000);
    };

    const handleResend = () => {
        onSubmit({ email: getValues('email') });
    };

    const copyToClipboard = (text: string) => {
        navigator.clipboard.writeText(text).then(() => {
            toast.success('Copied to clipboard!');
        });
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0D1B2A] via-[#1A2C3D] to-[#0D1B2A] p-4">
            <div className="glass-panel max-w-sm w-full p-8 relative z-10">
                <Link
                    to="/login"
                    className="inline-flex items-center text-slate-400 hover:text-slate-200 text-sm mb-6 transition-colors"
                >
                    <ArrowLeft size={16} className="mr-1" /> Back to Login
                </Link>

                {!isSubmitted ? (
                    <>
                        <h2 className="text-2xl font-semibold text-slate-100 mb-2">Forgot password?</h2>
                        <p className="text-slate-400 text-sm mb-6">
                            Enter your email address and we'll send you a link to reset your password.
                        </p>

                        <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                            <Input
                                {...register('email')}
                                type="email"
                                label="Email Address"
                                placeholder="alex@example.com"
                                error={errors.email?.message}
                                icon={<Mail size={18} className="text-slate-400" />}
                            />

                            <Button type="submit" className="w-full" isLoading={isLoading}>
                                Send Reset Link
                            </Button>
                        </form>
                    </>
                ) : (
                    <div className="text-center py-4">
                        <div className="w-16 h-16 bg-teal-500/20 rounded-full flex items-center justify-center mx-auto mb-4 animate-bounce-subtle">
                            <CheckCircle size={32} className="text-teal-400" />
                        </div>

                        <h2 className="text-xl font-semibold text-slate-100 mb-2">Reset Link Generated</h2>
                        <p className="text-slate-400 text-sm mb-4">
                            A password reset link has been generated for<br />
                            <span className="text-slate-200 font-medium">{getValues('email')}</span>.
                        </p>

                        {resetToken && resetUrl ? (
                            <div className="mb-4 space-y-3 text-left">
                                <div className="p-3 bg-amber-500/10 border border-amber-500/30 rounded-lg">
                                    <p className="text-xs text-amber-400 font-medium mb-1">⚠️ Email not configured — use this link directly:</p>
                                    <div className="flex items-center gap-2 mt-2">
                                        <code className="text-xs text-slate-300 bg-white/5 px-2 py-1 rounded flex-1 truncate">
                                            {window.location.origin}{resetUrl}
                                        </code>
                                        <button
                                            onClick={() => copyToClipboard(`${window.location.origin}${resetUrl}`)}
                                            className="p-1.5 rounded bg-white/5 hover:bg-white/10 text-slate-400 hover:text-white transition-colors flex-shrink-0"
                                            title="Copy link"
                                        >
                                            <Copy size={14} />
                                        </button>
                                        <a
                                            href={resetUrl}
                                            className="p-1.5 rounded bg-teal-500/10 hover:bg-teal-500/20 text-teal-400 hover:text-teal-300 transition-colors flex-shrink-0"
                                            title="Open reset page"
                                        >
                                            <ExternalLink size={14} />
                                        </a>
                                    </div>
                                </div>
                            </div>
                        ) : (
                            <p className="text-slate-500 text-xs mb-4">Check your inbox — it expires in 30 minutes.</p>
                        )}

                        <div className="space-y-4">
                            {resetUrl && (
                                <Button
                                    variant="outline"
                                    className="w-full justify-center"
                                    onClick={() => window.open(resetUrl, '_self')}
                                >
                                    Go to Reset Page
                                </Button>
                            )}

                            <div className="text-sm text-slate-400">
                                Didn't get it?{' '}
                                {cooldown > 0 ? (
                                    <span className="text-slate-500">Resend in {cooldown}s</span>
                                ) : (
                                    <button
                                        onClick={handleResend}
                                        className="text-teal-400 hover:text-teal-300 font-medium"
                                    >
                                        Click to resend
                                    </button>
                                )}
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};
