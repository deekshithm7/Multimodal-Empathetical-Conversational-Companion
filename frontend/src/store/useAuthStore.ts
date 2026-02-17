import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '../api/client';

export interface User {
    id: string;
    name: string;
    email: string;
    is_active?: boolean;
    avatar?: string;
}

interface AuthState {
    user: User | null;
    isAuthenticated: boolean;
    isLoading: boolean;
    error: string | null;

    // Actions
    login: (email: string, password: string) => Promise<void>;
    register: (name: string, email: string, password: string) => Promise<void>;
    logout: () => void;
    // forgotPassword: (email: string) => Promise<void>; // Pending backend implementation
    // resetPassword: (token: string, password: string) => Promise<void>; // Pending backend implementation
    updateProfile: (data: Partial<User>) => Promise<void>;
    clearError: () => void;
    checkAuth: () => Promise<void>; // New: Check if token is valid
}

export const useAuthStore = create<AuthState>()(
    persist(
        (set) => ({
            user: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,

            login: async (email: string, password: string) => {
                set({ isLoading: true, error: null });
                try {
                    const data = await api.login(email, password);
                    api.setToken(data.access_token);

                    const user: User = {
                        id: dateToId(), // Pending: get ID from /me or token response
                        name: data.user_name,
                        email: data.user_email
                    };

                    // Populate full profile
                    try {
                        const profile = await api.getMe();
                        user.id = profile.id;
                        user.name = profile.name;
                        user.email = profile.email;
                    } catch (e) {
                        console.warn('Failed to fetch full profile', e);
                    }

                    set({
                        user,
                        isAuthenticated: true,
                        isLoading: false
                    });
                } catch (err: any) {
                    set({
                        error: err.message || 'Login failed',
                        isLoading: false
                    });
                }
            },

            register: async (name: string, email: string, password: string) => {
                set({ isLoading: true, error: null });
                try {
                    await api.register(name, email, password);
                    // Auto-login after register
                    const data = await api.login(email, password);
                    api.setToken(data.access_token);

                    set({
                        user: { id: dateToId(), name, email }, // Temp ID until profile fetch
                        isAuthenticated: true,
                        isLoading: false
                    });

                    // Fetch real ID
                    const profile = await api.getMe();
                    set({ user: profile });

                } catch (err: any) {
                    set({
                        error: err.message || 'Registration failed',
                        isLoading: false
                    });
                }
            },

            logout: () => {
                api.setToken(null);
                set({
                    user: null,
                    isAuthenticated: false,
                    error: null
                });
            },

            checkAuth: async () => {
                const token = api.getToken();
                if (!token) return;

                try {
                    const user = await api.getMe();
                    set({ user, isAuthenticated: true });
                } catch (err) {
                    // Token expired or invalid
                    api.setToken(null);
                    set({ user: null, isAuthenticated: false });
                }
            },

            updateProfile: async (data: Partial<User>) => {
                set({ isLoading: true, error: null });
                // Pending backend endpoint for specific update or reuse /users/me
                set({ isLoading: false }); // Placeholder
            },

            forgotPassword: async (email: string) => {
                // Placeholder
                await new Promise(resolve => setTimeout(resolve, 500));
            },

            resetPassword: async (token: string, password: string) => {
                // Placeholder
                await new Promise(resolve => setTimeout(resolve, 500));
            },

            clearError: () => set({ error: null })
        }),
        {
            name: 'mecc-auth-storage',
            partialize: (state) => ({
                user: state.user,
                isAuthenticated: state.isAuthenticated
            }),
            onRehydrateStorage: () => (state) => {
                // Ensure API client has token from localStorage on reload
                const token = localStorage.getItem('auth_token');
                if (token) api.setToken(token);

                // Optionally verify token validity in background
                state?.checkAuth();
            }
        }
    )
);

// Helper
const dateToId = () => Date.now().toString();

// Unused methods commented out to match interface updates if needed,
// or implement placeholders if UI expects them:
/*
    forgotPassword: async (email: string) => {
        // ...
    },
    resetPassword: async (token: string, password: string) => {
        // ...
    },
*/
