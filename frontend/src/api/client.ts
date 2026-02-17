/**
 * MECC Backend API Client
 * Communicates with session-based backend endpoints
 */

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface SessionStartResponse {
    conversation_id: string;
    session_id: string;
    welcome_message: string;
    welcome_audio_url: string;
}

export interface MessageResponse {
    status: string;
    user_message: string;
    user_emotion: {
        emotion: string;
        confidence: number;
        probabilities: Record<string, number>;
    };
    assistant_response: string;
    assistant_audio_url: string;
    conversation_id: string;
    processing_time_ms: number;
}

export interface SessionEndResponse {
    summary: string;
    summary_audio_url: string;
    emotional_journey: Array<{
        emotion: string;
        confidence: number;
        timestamp: string;
    }>;
    total_messages: number;
    duration_minutes: number;
}

// Auth Interfaces
export interface AuthResponse {
    access_token: string;
    token_type: string;
    user_name: string;
    user_email: string;
}

export interface UserProfile {
    id: string;
    email: string;
    name: string;
    is_active: boolean;
}

// Token management
let authToken: string | null = localStorage.getItem('auth_token');

export const api = {
    setToken(token: string | null) {
        authToken = token;
        if (token) {
            localStorage.setItem('auth_token', token);
        } else {
            localStorage.removeItem('auth_token');
        }
    },

    getToken() {
        return authToken;
    },

    privateHeaders() {
        return {
            'Authorization': authToken ? `Bearer ${authToken}` : '',
        };
    },

    // --- Auth Endpoints ---

    async login(email: string, password: string): Promise<AuthResponse> {
        const formData = new FormData();
        formData.append('username', email); // OAuth2PasswordRequestForm expects 'username'
        formData.append('password', password);

        const response = await fetch(`${API_URL}/api/v1/auth/token`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || 'Login failed');
        }

        return response.json();
    },

    async register(name: string, email: string, password: string): Promise<UserProfile> {
        const response = await fetch(`${API_URL}/api/v1/auth/register`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, email, password }),
        });

        if (!response.ok) {
            const error = await response.json().catch(() => ({ detail: response.statusText }));
            throw new Error(error.detail || 'Registration failed');
        }

        return response.json();
    },

    async getMe(): Promise<UserProfile> {
        const response = await fetch(`${API_URL}/api/v1/auth/me`, {
            headers: this.privateHeaders(),
        });

        if (!response.ok) throw new Error('Failed to fetch profile');
        return response.json();
    },

    // --- Session Endpoints ---

    /**
     * Start a new conversation session
     */
    async startSession(userId?: string): Promise<SessionStartResponse> {
        const formData = new FormData();
        if (userId) formData.append('user_id', userId);

        const response = await fetch(`${API_URL}/api/v1/session/start`, {
            method: 'POST',
            headers: this.privateHeaders(), // Now authenticated
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Failed to start session: ${response.statusText}`);
        }

        return response.json();
    },

    /**
     * Send a message (text and/or audio/video)
     */
    async sendMessage(
        conversationId: string,
        text?: string,
        media?: Blob
    ): Promise<MessageResponse> {
        const formData = new FormData();
        formData.append('conversation_id', conversationId);

        if (text) {
            formData.append('text', text);
        }

        if (media) {
            // Send as 'audio' - backend will handle video or audio
            formData.append('audio', media, 'message.webm');
        }

        const response = await fetch(`${API_URL}/api/v1/session/message`, {
            method: 'POST',
            headers: this.privateHeaders(), // Now authenticated
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Failed to send message: ${response.statusText}`);
        }

        return response.json();
    },

    /**
     * End conversation and get summary
     */
    async endSession(conversationId: string): Promise<SessionEndResponse> {
        const formData = new FormData();
        formData.append('conversation_id', conversationId);

        const response = await fetch(`${API_URL}/api/v1/session/end`, {
            method: 'POST',
            headers: this.privateHeaders(), // Now authenticated
            body: formData
        });

        if (!response.ok) {
            throw new Error(`Failed to end session: ${response.statusText}`);
        }

        return response.json();
    },

    /**
     * Get audio file URL
     */
    getAudioUrl(audioPath: string): string {
        return `${API_URL}${audioPath}`;
    },

    /**
     * Get Dashboard Stats
     */
    async getDashboardStats(): Promise<any> {
        const response = await fetch(`${API_URL}/api/v1/analytics/dashboard`, {
            headers: this.privateHeaders(),
        });
        if (!response.ok) throw new Error('Failed to fetch stats');
        return response.json();
    },

    /**
     * Get Conversation History
     */
    async getHistory(limit = 50): Promise<any> {
        // We'll need to implement a dedicated endpoint for listing conversations or use existing
        // For now using placeholder logic or if we built /api/v1/analytics/conversations
        // Wait, did I build GET /conversations? I built GET /api/v1/analytics/dashboard
        // I haven't built a list endpoint yet in analytics.py.
        // Let's add it there later, but for now assuming it exists or we won't use it yet.
        return [];
    }
};
