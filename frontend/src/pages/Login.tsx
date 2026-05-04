import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { useToast } from '../components/UI/Toast';

const loginSchema = z.object({
    email: z.string().email('Invalid email address'),
    password: z.string().min(6, 'Password must be at least 6 characters')
});

type LoginFormData = z.infer<typeof loginSchema>;

export const Login = () => {
    const navigate = useNavigate();
    const { login, error: authError, clearError, isLoading } = useAuthStore();
    const toast = useToast();
    const [showPassword, setShowPassword] = useState(false);

    const {
        register,
        handleSubmit,
        formState: { errors }
    } = useForm<LoginFormData>({
        resolver: zodResolver(loginSchema)
    });

    const onSubmit = async (data: LoginFormData) => {
        clearError();
        await login(data.email, data.password);

        const isAuthenticated = useAuthStore.getState().isAuthenticated;
        if (isAuthenticated) {
            toast.success('Welcome back to MindSculpt AI!');
            navigate('/dashboard');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0D1B2A] via-[#1A2C3D] to-[#0D1B2A] p-4">
            {/* Animated background */}
            <div className="absolute inset-0 overflow-hidden opacity-20">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_50%,rgba(0,201,167,0.1),transparent_50%)]" />
            </div>

            {/* Login Card */}
            <div className="glass-panel max-w-md w-full p-8 relative z-10">
                {/* Logo */}
                <div className="text-center mb-8">
                    <h1 className="text-3xl font-serif text-teal-400 mb-2">MindSculpt AI</h1>
                    <h2 className="text-2xl font-semibold text-slate-100 mb-1">Welcome back</h2>
                    <p className="text-slate-400 text-sm">Sign in to continue your journey</p>
                </div>

                {/* Error Banner */}
                {authError && (
                    <div className="mb-4 p-3 bg-red-500/20 border border-red-400 rounded-lg text-red-300 text-sm">
                        {authError}
                    </div>
                )}

                {/* Form */}
                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <div>
                        <Input
                            {...register('email')}
                            type="email"
                            placeholder="alex@example.com"
                            label="Email address"
                            error={errors.email?.message}
                            autoComplete="email"
                        />
                    </div>

                    <div className="relative">
                        <Input
                            {...register('password')}
                            type={showPassword ? 'text' : 'password'}
                            placeholder="Enter your password"
                            label="Password"
                            error={errors.password?.message}
                            autoComplete="current-password"
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-[38px] text-slate-400 hover:text-slate-200"
                        >
                            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                        </button>
                    </div>

                    <div className="text-right">
                        <Link
                            to="/forgot-password"
                            className="text-sm text-teal-400 hover:text-teal-300 transition-colors"
                        >
                            Forgot your password?
                        </Link>
                    </div>

                    <Button
                        type="submit"
                        variant="primary"
                        className="w-full"
                        isLoading={isLoading}
                    >
                        Sign In
                    </Button>
                </form>



                {/* Sign Up Link */}
                <p className="mt-6 text-center text-sm text-slate-400">
                    Don't have an account?{' '}
                    <Link to="/register" className="text-teal-400 hover:text-teal-300 font-medium">
                        Sign up
                    </Link>
                </p>

                {/* Demo Credentials */}
                <div className="mt-6 p-3 bg-blue-500/10 border border-blue-400/30 rounded-lg">
                    <p className="text-xs text-blue-300 text-center">
                        <strong>Demo:</strong> demo@mindsculpt.ai / demo123
                    </p>
                </div>
            </div>
        </div>
    );
};
