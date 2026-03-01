import { Mic, Video, Activity, Wifi } from 'lucide-react';
import { VanishingCamera } from '../Camera/VanishingCamera';
import { WaveVisualizer } from '../AudioVisualizer/WaveVisualizer';
import { clsx } from 'clsx';
import { useEmotionStore } from '../../store/useEmotionStore';

interface InputMonitorPanelProps {
    stream: MediaStream | null;
    isRecording: boolean;
    isListening: boolean;
    activeInputMode: 'multimodal' | 'audio-only' | 'text-only';
    onToggleCamera: () => void;
    onToggleMic: () => void;
}

export const InputMonitorPanel = ({
    stream,
    isRecording,
    isListening,
    activeInputMode,
    onToggleCamera,
    onToggleMic
}: InputMonitorPanelProps) => {
    const { currentEmotion } = useEmotionStore();

    return (
        <div className="h-full flex flex-col gap-4 p-4 glass-panel rounded-2xl border border-white/5 bg-[#0f1115]/50">
            <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-slate-300 uppercase tracking-wider">Live Input</h3>
                {isRecording && (
                    <div className="flex items-center gap-2 px-2 py-1 rounded-full bg-red-500/10 border border-red-500/20">
                        <span className="w-2 h-2 rounded-full bg-red-500 animate-pulse" />
                        <span className="text-[10px] font-bold text-red-400">LIVE</span>
                    </div>
                )}
            </div>

            {/* Camera Feed Card */}
            <div className="relative rounded-xl overflow-hidden bg-black/40 border border-white/10 aspect-video flex items-center justify-center group">
                {activeInputMode === 'text-only' ? (
                    <div className="flex flex-col items-center gap-2 text-slate-600">
                        <Video size={24} />
                        <span className="text-xs">Camera Disabled</span>
                    </div>
                ) : stream && stream.getVideoTracks().length > 0 ? (
                    <VanishingCamera stream={stream} />
                ) : (
                    <div className="flex flex-col items-center gap-2 text-slate-500">
                        {isRecording ? (
                            <div className="flex flex-col items-center animate-pulse text-teal-500">
                                <Activity size={32} />
                                <span className="text-xs mt-2 font-medium">Recording Audio Only</span>
                            </div>
                        ) : (
                            <>
                                <Video size={24} />
                                <span className="text-xs">Camera Active</span>
                            </>
                        )}
                    </div>
                )}

                {/* Detection Overlay */}
                {isRecording && stream && (
                    <div className="absolute top-2 left-2 px-2 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[10px] text-white flex items-center gap-1 border border-white/10">
                        <Activity size={10} className="text-teal-400" />
                        Face Detected
                    </div>
                )}
            </div>

            {/* Audio Monitor Card */}
            <div className="relative rounded-xl overflow-hidden bg-black/40 border border-white/10 h-32 flex items-center justify-center">
                {activeInputMode === 'text-only' ? (
                    <div className="flex flex-col items-center gap-2 text-slate-600">
                        <Mic size={24} />
                        <span className="text-xs">Audio Disabled</span>
                    </div>
                ) : (
                    <div className="w-full h-full opacity-80">
                        <WaveVisualizer isListening={isListening || isRecording} emotion={currentEmotion} />
                    </div>
                )}

                {isListening && (
                    <div className="absolute bottom-2 right-2 px-2 py-0.5 rounded bg-black/60 backdrop-blur-sm text-[10px] text-white flex items-center gap-1 border border-white/10">
                        <Wifi size={10} className="text-teal-400" />
                        Voice Active
                    </div>
                )}
            </div>

            {/* Controls */}
            <div className="grid grid-cols-2 gap-3 mt-auto">
                <button
                    onClick={onToggleCamera}
                    disabled={activeInputMode === 'text-only'}
                    className={clsx(
                        "p-3 rounded-xl border flex flex-col items-center gap-2 transition-all",
                        !stream || activeInputMode === 'text-only'
                            ? "bg-white/5 border-white/5 text-slate-500 hover:bg-white/10"
                            : "bg-teal-500/10 border-teal-500/30 text-teal-400"
                    )}
                >
                    <Video size={20} />
                    <span className="text-xs font-medium">Camera</span>
                </button>

                <button
                    onClick={onToggleMic}
                    disabled={activeInputMode === 'text-only'}
                    className={clsx(
                        "p-3 rounded-xl border flex flex-col items-center gap-2 transition-all",
                        !isListening && !isRecording
                            ? "bg-white/5 border-white/5 text-slate-500 hover:bg-white/10"
                            : "bg-violet-500/10 border-violet-500/30 text-violet-400"
                    )}
                >
                    <Mic size={20} />
                    <span className="text-xs font-medium">Mic</span>
                </button>
            </div>

        </div>
    );
};
