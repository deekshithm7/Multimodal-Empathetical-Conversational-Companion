import { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { z } from 'zod';
import { Eye, EyeOff, X } from 'lucide-react';
import { useAuthStore } from '../store/useAuthStore';
import { Button } from '../components/UI/Button';
import { Input } from '../components/UI/Input';
import { useToast } from '../components/UI/Toast';

const registerSchema = z.object({
    fullName: z.string().min(2, 'Full name must be at least 2 characters'),
    email: z.string().email('Invalid email address'),
    password: z.string().min(8, 'Password must be at least 8 characters')
        .regex(/[A-Z]/, 'Must contain at least one uppercase letter')
        .regex(/[0-9]/, 'Must contain at least one number'),
    confirmPassword: z.string(),
    terms: z.boolean().refine((accepted) => accepted, {
        message: 'You must agree to the terms and privacy policy'
    })
}).refine((data) => data.password === data.confirmPassword, {
    message: "Passwords don't match",
    path: ["confirmPassword"],
});

type RegisterFormData = z.infer<typeof registerSchema>;

export const Register = () => {
    const navigate = useNavigate();
    const { register: registerUser, isLoading, clearError, error: authError } = useAuthStore();
    const toast = useToast();
    const [showPassword, setShowPassword] = useState(false);

    const {
        register,
        handleSubmit,
        watch,
        formState: { errors }
    } = useForm<RegisterFormData>({
        resolver: zodResolver(registerSchema),
        defaultValues: {
            fullName: '',
            email: '',
            password: '',
            confirmPassword: '',
            terms: false
        }
    });

    const password = watch('password', '');

    const getPasswordStrength = (pass: string) => {
        if (!pass) return 0;
        let score = 0;
        if (pass.length >= 8) score++;
        if (/[A-Z]/.test(pass)) score++;
        if (/[0-9]/.test(pass)) score++;
        if (/[^A-Za-z0-9]/.test(pass)) score++;
        return score;
    };

    const strength = getPasswordStrength(password);

    const getStrengthColor = (score: number) => {
        if (score <= 1) return 'bg-red-500';
        if (score === 2) return 'bg-amber-500';
        if (score >= 3) return 'bg-green-500';
        return 'bg-slate-700';
    };

    const getStrengthLabel = (score: number) => {
        if (score === 0) return '';
        if (score <= 1) return 'Weak';
        if (score === 2) return 'Moderate';
        return 'Strong';
    };

    const onSubmit = async (data: RegisterFormData) => {
        clearError();
        await registerUser(data.fullName, data.email, data.password);

        if (useAuthStore.getState().isAuthenticated) {
            toast.success('Account created successfully! Welcome to MindSculpt AI.');
            navigate('/dashboard');
        }
    };

    return (
        <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-[#0D1B2A] via-[#1A2C3D] to-[#0D1B2A] p-4 py-8">
            {/* Animated background */}
            <div className="absolute inset-0 overflow-hidden opacity-20 pointer-events-none">
                <div className="absolute inset-0 bg-[radial-gradient(circle_at_80%_20%,rgba(123,97,255,0.1),transparent_50%)]" />
            </div>

            <div className="glass-panel max-w-md w-full p-8 relative z-10">
                <div className="text-center mb-6">
                    <h1 className="text-3xl font-serif text-teal-400 mb-2">MindSculpt AI</h1>
                    <h2 className="text-2xl font-semibold text-slate-100 mb-1">Create your account</h2>
                    <p className="text-slate-400 text-sm">Start your empathetic AI journey</p>
                </div>

                {authError && (
                    <div className="mb-4 p-3 bg-red-500/20 border border-red-400 rounded-lg text-red-300 text-sm flex items-start gap-2">
                        <X size={16} className="mt-0.5 shrink-0" />
                        <span>{authError}</span>
                    </div>
                )}

                <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
                    <Input
                        {...register('fullName')}
                        label="Full Name"
                        placeholder="Alex Johnson"
                        error={errors.fullName?.message}
                        autoComplete="name"
                    />

                    <Input
                        {...register('email')}
                        type="email"
                        label="Email Address"
                        placeholder="alex@example.com"
                        error={errors.email?.message}
                        autoComplete="email"
                    />

                    <div className="relative">
                        <Input
                            {...register('password')}
                            type={showPassword ? 'text' : 'password'}
                            label="Password"
                            placeholder="Create a strong password"
                            error={errors.password?.message}
                            autoComplete="new-password"
                        />
                        <button
                            type="button"
                            onClick={() => setShowPassword(!showPassword)}
                            className="absolute right-3 top-[38px] text-slate-400 hover:text-slate-200"
                        >
                            {showPassword ? <EyeOff size={20} /> : <Eye size={20} />}
                        </button>

                        {/* Strength Indicator */}
                        {password && (
                            <div className="mt-2">
                                <div className="flex justify-between items-center mb-1 text-xs">
                                    <span className="text-slate-400">Password strength</span>
                                    <span className={strength <= 1 ? "text-red-400" : strength === 2 ? "text-amber-400" : "text-green-400"}>
                                        {getStrengthLabel(strength)}
                                    </span>
                                </div>
                                <div className="flex gap-1 h-1">
                                    <div className={`flex-1 rounded-full transition-colors ${strength >= 1 ? getStrengthColor(strength) : 'bg-slate-700'}`} />
                                    <div className={`flex-1 rounded-full transition-colors ${strength >= 2 ? getStrengthColor(strength) : 'bg-slate-700'}`} />
                                    <div className={`flex-1 rounded-full transition-colors ${strength >= 3 ? getStrengthColor(strength) : 'bg-slate-700'}`} />
                                    <div className={`flex-1 rounded-full transition-colors ${strength >= 4 ? getStrengthColor(strength) : 'bg-slate-700'}`} />
                                </div>
                            </div>
                        )}
                    </div>

                    <div className="relative">
                        <Input
                            {...register('confirmPassword')}
                            type={showPassword ? 'text' : 'password'}
                            label="Confirm Password"
                            placeholder="Confirm your password"
                            error={errors.confirmPassword?.message}
                            autoComplete="new-password"
                        />
                    </div>

                    <div className="flex items-start gap-3 mt-2">
                        <input
                            type="checkbox"
                            id="terms"
                            {...register('terms')}
                            className="mt-1 w-4 h-4 rounded border-slate-600 text-teal-500 bg-slate-800 focus:ring-teal-500"
                        />
                        <label htmlFor="terms" className="text-sm text-slate-300">
                            I agree to the <a href="#" className="text-teal-400 hover:underline">Privacy Policy</a> and <a href="#" className="text-teal-400 hover:underline">Terms of Use</a>
                        </label>
                    </div>
                    {errors.terms && <p className="text-xs text-red-400 mt-1">{errors.terms.message}</p>}

                    <Button type="submit" className="w-full mt-2" isLoading={isLoading}>
                        Create Account
                    </Button>
                </form>



                <p className="mt-6 text-center text-sm text-slate-400">
                    Already have an account?{' '}
                    <Link to="/login" className="text-teal-400 hover:text-teal-300 font-medium">
                        Sign in
                    </Link>
                </p>
            </div>
        </div>
    );
};
