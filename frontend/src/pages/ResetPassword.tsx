import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Lock, Eye, EyeOff, CheckCircle, AlertTriangle } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { useToast } from '../components/UI/Toast';

const resetSchema = z.object({
    password: z.string().min(8, 'Password must be at least 8 characters'),
    confirmPassword: z.string()
}).refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
});

type ResetFormData = z.infer<typeof resetSchema>;

export const ResetPassword = () => {
    const [searchParams] = useSearchParams();
    const navigate = useNavigate();
    const { resetPassword, isLoading, error: authError } = useAuthStore();
    const toast = useToast();

    const token = searchParams.get('token');
    const [showPassword, setShowPassword] = useState(false);
    const [isSuccess, setIsSuccess] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors }
    } = useForm<ResetFormData>({
        resolver: zodResolver(resetSchema)
    });

    const onSubmit = async (data: ResetFormData) => {
        if (!token) return;

        await resetPassword(token, data.password);

        // Check if store updated successfully (mock)
        if (!useAuthStore.getState().error) {
            setIsSuccess(true);
            toast.success('Your password has been successfully reset.');
        }
    };

    if (!token) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0D1B2A] via-[#1A2C3D] to-[#0D1B2A] p-4">
                <div className="glass-panel max-w-sm w-full p-8 text-center">
                    <div className="w-12 h-12 bg-red-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <AlertTriangle size={24} className="text-red-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-slate-100 mb-2">Invalid Link</h2>
                    <p className="text-slate-400 text-sm mb-6">
                        This password reset link is invalid or has expired.
                    </p>
                    <Button onClick={() => navigate('/forgot-password')} className="w-full">
                        Request New Link
                    </Button>
                </div>
            </div>
        );
    }

    if (isSuccess) {
        return (
            <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0D1B2A] via-[#1A2C3D] to-[#0D1B2A] p-4">
                <div className="glass-panel max-w-sm w-full p-8 text-center">
                    <div className="w-16 h-16 bg-green-500/20 rounded-full flex items-center justify-center mx-auto mb-4">
                        <CheckCircle size={32} className="text-green-400" />
                    </div>
                    <h2 className="text-xl font-semibold text-slate-100 mb-2">Password Reset!</h2>
                    <p className="text-slate-400 text-sm mb-6">
                        Your password has been updated successfully. You can now log in with your new password.
                    </p>
                    <Button onClick={() => navigate('/login')} className="w-full">
                        Back to Login
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0D1B2A] via-[#1A2C3D] to-[#0D1B2A] p-4">
            <div className="glass-panel max-w-sm w-full p-8 relative z-10">
                <h2 className="text-2xl font-semibold text-slate-100 mb-2">Set new password</h2>
                <p className="text-slate-400 text-sm mb-6">
                    Choose a strong password for your account.
                </p>

                {authError && (
                    <div className="mb-4 p-3 bg-red-500/20 border border-red-400 rounded-lg text-red-300 text-sm">
                        {authError}
                    </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div className="relative">
                        <Input
                            {...register('password')}
                            type={showPassword ? 'text' : 'password'}
                            label="New Password"
                            placeholder="Enter new password"
                            error={errors.password?.message}
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-[38px] text-slate-400 hover:text-slate-200"
                        >
                            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                        </button>
                    </div>

                    <Input
                        {...register('confirmPassword')}
                        type={showPassword ? 'text' : 'password'}
                        label="Confirm New Password"
                        placeholder="Repeat new password"
                        error={errors.confirmPassword?.message}
                    />

                    <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
                        Reset Password
                    </Button>
                </form>
            </div>
        </div>
    );
};
