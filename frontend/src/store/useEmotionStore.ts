import { create } from 'zustand';
import { api } from '../api/client';
import type { MessageResponse, SessionEndResponse } from '../api/client';

export type Emotion = 'neutral' | 'happy' | 'sad' | 'angry' | 'calm' | 'fearful' | 'surprised' | 'disgust';

export interface Message {
    id: string;
    sender: 'user' | 'companion';
    text: string;
    emotion?: {
        type: Emotion;
        confidence: number;
    };
    audioUrl?: string;
}

interface EmotionState {
    // Conversation state
    conversationId: string | null;
    currentEmotion: Emotion;
    messages: Message[];

    // UI state
    isListening: boolean;
    isLoading: boolean;
    error: string | null;

    // Session summary
    sessionSummary: SessionEndResponse | null;

    // Actions
    startSession: () => Promise<void>;
    sendMessage: (text: string, mediaBlob?: Blob) => Promise<void>;
    endSession: () => Promise<void>;
    setListening: (isListening: boolean) => void;
    reset: () => void;
}

export const useEmotionStore = create<EmotionState>((set, get) => ({
    // Initial state
    conversationId: null,
    currentEmotion: 'neutral',
    messages: [],
    isListening: false,
    isLoading: false,
    error: null,
    sessionSummary: null,

    /**
     * Start a new conversation session
     */
    startSession: async () => {
        try {
            set({ isLoading: true, error: null, messages: [] });

            const response = await api.startSession();

            set({
                conversationId: response.conversation_id,
                messages: [{
                    id: '1',
                    sender: 'companion',
                    text: response.welcome_message,
                    audioUrl: response.welcome_audio_url
                }],
                isLoading: false
            });

            // Auto-play welcome audio
            const audioUrl = api.getAudioUrl(response.welcome_audio_url);
            const audio = new Audio(audioUrl);
            audio.play().catch(err => console.warn('Auto-play blocked:', err));

        } catch (error) {
            console.error('Failed to start session:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to start session',
                isLoading: false
            });
        }
    },

    /**
     * Send a message to the backend
     */
    sendMessage: async (text: string, mediaBlob?: Blob) => {
        const { conversationId, messages } = get();

        if (!conversationId) {
            console.error('No active conversation');
            return;
        }

        try {
            set({ isLoading: true, error: null });

            // Add user message to UI immediately
            const userMessage: Message = {
                id: Date.now().toString(),
                sender: 'user',
                text
            };

            set({ messages: [...messages, userMessage] });

            // Send to backend
            const response: MessageResponse = await api.sendMessage(
                conversationId,
                text,
                mediaBlob
            );

            // Update user message with emotion
            const updatedMessages = get().messages.map(msg =>
                msg.id === userMessage.id
                    ? {
                        ...msg,
                        emotion: {
                            type: response.user_emotion.emotion as Emotion,
                            confidence: response.user_emotion.confidence
                        }
                    }
                    : msg
            );

            // Add assistant response
            const assistantMessage: Message = {
                id: (Date.now() + 1).toString(),
                sender: 'companion',
                text: response.assistant_response,
                audioUrl: response.assistant_audio_url
            };

            set({
                messages: [...updatedMessages, assistantMessage],
                currentEmotion: response.user_emotion.emotion as Emotion,
                isLoading: false
            });

            // Play assistant audio response
            const audioUrl = api.getAudioUrl(response.assistant_audio_url);
            const audio = new Audio(audioUrl);
            audio.play().catch(err => console.warn('Auto-play blocked:', err));

        } catch (error) {
            console.error('Failed to send message:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to send message',
                isLoading: false
            });
        }
    },

    /**
     * End the current session
     */
    endSession: async () => {
        const { conversationId } = get();

        if (!conversationId) {
            console.error('No active conversation to end');
            return;
        }

        try {
            set({ isLoading: true, error: null });

            const summary = await api.endSession(conversationId);

            set({
                sessionSummary: summary,
                isLoading: false
            });

            // Play summary audio
            const audioUrl = api.getAudioUrl(summary.summary_audio_url);
            const audio = new Audio(audioUrl);
            audio.play().catch(err => console.warn('Auto-play blocked:', err));

        } catch (error) {
            console.error('Failed to end session:', error);
            set({
                error: error instanceof Error ? error.message : 'Failed to end session',
                isLoading: false
            });
        }
    },

    /**
     * Set listening state
     */
    setListening: (isListening: boolean) => set({ isListening }),

    /**
     * Reset to initial state
     */
    reset: () => set({
        conversationId: null,
        currentEmotion: 'neutral',
        messages: [],
        isListening: false,
        isLoading: false,
        error: null,
        sessionSummary: null
    })
}));
