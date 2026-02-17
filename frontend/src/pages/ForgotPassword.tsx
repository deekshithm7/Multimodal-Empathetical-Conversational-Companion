import { useState } from 'react';
import { Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { ArrowLeft, CheckCircle, Mail } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';

const forgotPasswordSchema = z.object({
    email: z.string().email('Invalid email address')
});

type ForgotPasswordFormData = z.infer<typeof forgotPasswordSchema>;

export const ForgotPassword = () => {
    const { forgotPassword, isLoading } = useAuthStore();
    const [isSubmitted, setIsSubmitted] = useState(false);
    const [cooldown, setCooldown] = useState(0);

    const {
        register,
        handleSubmit,
        getValues,
        formState: { errors }
    } = useForm<ForgotPasswordFormData>({
        resolver: zodResolver(forgotPasswordSchema)
    });

    const onSubmit = async (data: ForgotPasswordFormData) => {
        await forgotPassword(data.email);
        setIsSubmitted(true);
        startCooldown();
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
        // Re-trigger the logic
        onSubmit({ email: getValues('email') });
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

                        <h2 className="text-xl font-semibold text-slate-100 mb-2">Check your inbox</h2>
                        <p className="text-slate-400 text-sm mb-6">
                            We've sent a password reset link to<br />
                            <span className="text-slate-200 font-medium">{getValues('email')}</span>.
                            <br />It expires in 30 minutes.
                        </p>

                        <div className="space-y-4">
                            <Button
                                variant="outline"
                                className="w-full justify-center"
                                onClick={() => window.open('https://gmail.com', '_blank')}
                            >
                                Open Email App
                            </Button>

                            <div className="text-sm text-slate-400">
                                Didn't receive the email?{' '}
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
