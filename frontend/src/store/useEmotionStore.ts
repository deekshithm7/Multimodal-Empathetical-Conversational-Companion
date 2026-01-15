import { create } from 'zustand';

export type Emotion = 'neutral' | 'happy' | 'sad' | 'angry';

export interface Message {
    id: string;
    sender: 'user' | 'companion';
    text: string;
}

interface EmotionState {
    currentEmotion: Emotion;a
    messages: Message[];
    isListening: boolean;
    setEmotion: (emotion: Emotion) => void;
    addMessage: (message: Message) => void;
    setListening: (isListening: boolean) => void;
}

export const useEmotionStore = create<EmotionState>((set) => ({
    currentEmotion: 'neutral',
    messages: [
        { id: '1', sender: 'companion', text: 'Hello! How are you feeling today?' }
    ],
    isListening: false,
    setEmotion: (emotion) => set({ currentEmotion: emotion }),
    addMessage: (message) => set((state) => ({ messages: [...state.messages, message] })),
    setListening: (isListening) => set({ isListening }),
}));
