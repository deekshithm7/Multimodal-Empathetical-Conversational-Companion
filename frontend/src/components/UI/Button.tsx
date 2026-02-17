import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';
import { ButtonHTMLAttributes, forwardRef } from 'react';
import { Loader2 } from 'lucide-react';

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
    variant?: 'primary' | 'secondary' | 'outline' | 'danger' | 'ghost';
    size?: 'sm' | 'md' | 'lg';
    isLoading?: boolean;
    children: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
    ({ variant = 'primary', size = 'md', isLoading, className, children, disabled, ...props }, ref) => {
        const baseStyles = 'inline-flex items-center justify-center gap-2 font-medium rounded-full transition-all duration-200 disabled:opacity-50 disabled:cursor-not-allowed';

        const variants = {
            primary: 'bg-teal-500 hover:bg-teal-600 text-white shadow-lg hover:shadow-xl',
            secondary: 'bg-violet-500 hover:bg-violet-600 text-white shadow-lg hover:shadow-xl',
            outline: 'border-2 border-slate-300 hover:border-teal-500 text-slate-300 hover:text-teal-400 bg-transparent',
            danger: 'bg-red-500/80 hover:bg-red-600 text-white shadow-lg hover:shadow-xl',
            ghost: 'bg-white/10 hover:bg-white/20 text-slate-200 backdrop-blur-sm'
        };

        const sizes = {
            sm: 'px-4 py-2 text-sm',
            md: 'px-6 py-3 text-base',
            lg: 'px-8 py-4 text-lg'
        };

        return (
            <button
                ref={ref}
                className={twMerge(clsx(baseStyles, variants[variant], sizes[size], className))}
                disabled={disabled || isLoading}
                {...props}
            >
                {isLoading && <Loader2 className="animate-spin" size={18} />}
                {children}
            </button>
        );
    }
);

Button.displayName = 'Button';
