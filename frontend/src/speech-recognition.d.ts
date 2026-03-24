/** Web Speech API (Chromium prefixes) — not in default TypeScript DOM libs for all targets. */

interface SpeechRecognitionAlternative {
    transcript: string;
}

interface SpeechRecognitionResult {
    readonly isFinal: boolean;
    readonly length: number;
    item(index: number): SpeechRecognitionAlternative;
    [index: number]: SpeechRecognitionAlternative;
}

interface SpeechRecognitionResultList {
    readonly length: number;
    item(index: number): SpeechRecognitionResult;
    [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionEvent extends Event {
    readonly resultIndex: number;
    readonly results: SpeechRecognitionResultList;
}

interface SpeechRecognitionErrorEvent extends Event {
    readonly error: string;
}

interface SpeechRecognition extends EventTarget {
    continuous: boolean;
    interimResults: boolean;
    lang: string;
    start(): void;
    stop(): void;
    onresult: ((this: SpeechRecognition, ev: SpeechRecognitionEvent) => void) | null;
    onend: ((this: SpeechRecognition, ev: Event) => void) | null;
    onerror: ((this: SpeechRecognition, ev: SpeechRecognitionErrorEvent) => void) | null;
    onstart: ((this: SpeechRecognition, ev: Event) => void) | null;
}

interface SpeechRecognitionConstructor {
    new (): SpeechRecognition;
}

interface Window {
    SpeechRecognition: SpeechRecognitionConstructor;
    webkitSpeechRecognition: SpeechRecognitionConstructor;
}
