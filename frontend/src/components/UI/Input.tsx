import { forwardRef } from 'react';
import type { InputHTMLAttributes, ReactNode } from 'react';
import { clsx } from 'clsx';
import { twMerge } from 'tailwind-merge';

interface InputProps extends InputHTMLAttributes<HTMLInputElement> {
    label?: string;
    error?: string;
    helperText?: string;
    icon?: ReactNode;
}

export const Input = forwardRef<HTMLInputElement, InputProps>(
    ({ label, error, helperText, icon, className, ...props }, ref) => {
        return (
            <div className="w-full">
                {label && (
                    <label className="block text-sm font-medium text-slate-300 mb-2">
                        {label}
                    </label>
                )}
                <div className="relative">
                    {icon && (
                        <span className="absolute left-3 top-1/2 -translate-y-1/2 pointer-events-none z-10">
                            {icon}
                        </span>
                    )}
                    <input
                        ref={ref}
                        className={twMerge(
                            clsx(
                                'w-full px-4 py-3 rounded-lg bg-white/10 border border-white/20',
                                'text-slate-100 placeholder:text-slate-400',
                                'focus:outline-none focus:ring-2 focus:ring-teal-500 focus:border-transparent',
                                'transition-all duration-200',
                                error && 'border-red-400 focus:ring-red-400',
                                icon && 'pl-11',
                                className
                            )
                        )}
                        {...props}
                    />
                </div>
                {error && (
                    <p className="mt-1 text-sm text-red-400">{error}</p>
                )}
                {helperText && !error && (
                    <p className="mt-1 text-sm text-slate-400">{helperText}</p>
                )}
            </div>
        );
    }
);

Input.displayName = 'Input';
