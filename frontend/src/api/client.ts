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

export const api = {
    /**
     * Start a new conversation session
     */
    async startSession(userId?: string): Promise<SessionStartResponse> {
        const formData = new FormData();
        if (userId) formData.append('user_id', userId);

        const response = await fetch(`${API_URL}/api/v1/session/start`, {
            method: 'POST',
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
    }
};
