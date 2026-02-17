import { useState, useRef, useCallback } from 'react';

interface UseWebcamRecorderProps {
  onRecordingComplete?: (blob: Blob) => void;
}

export const useWebcamRecorder = ({ onRecordingComplete }: UseWebcamRecorderProps = {}) => {
  const [isRecordingSession, setIsRecordingSession] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  const [recordedBlob, setRecordedBlob] = useState<Blob | null>(null);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const streamRef = useRef<MediaStream | null>(null);

  const getSupportedMimeType = () => {
    const types = [
      'video/webm;codecs=vp9',
      'video/webm;codecs=vp8',
      'video/webm',
      'video/mp4',
    ];

    for (const type of types) {
      if (MediaRecorder.isTypeSupported(type)) {
        return type;
      }
    }
    return 'video/webm';
  };

  const startRecording = useCallback(async () => {
    try {
      setRecordedBlob(null);
      setError(null);

      let mediaStream: MediaStream;
      try {
        mediaStream = await navigator.mediaDevices.getUserMedia({
          video: true, // Try video first
          audio: true
        });
      } catch (err: any) {
        if (err.name === 'NotFoundError' || err.name === 'NotAllowedError') {
          console.warn("Video device not found or denied, falling back to audio only");
          // Fallback to audio only
          mediaStream = await navigator.mediaDevices.getUserMedia({
            video: false,
            audio: true
          });
        } else {
          throw err;
        }
      }

      streamRef.current = mediaStream;
      setStream(mediaStream);

      const mimeType = getSupportedMimeType();
      const options = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(mediaStream, options);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = () => {
        const finalMimeType = mediaRecorder.mimeType || 'video/webm';
        const blob = new Blob(chunksRef.current, { type: finalMimeType });
        chunksRef.current = [];

        // Save blob to state
        setRecordedBlob(blob);

        // Trigger callback if provided
        if (onRecordingComplete) {
          onRecordingComplete(blob);
        }

        // Stop all tracks
        if (streamRef.current) {
          streamRef.current.getTracks().forEach(track => track.stop());
          streamRef.current = null;
          setStream(null);
        }
      };

      mediaRecorder.start();
      mediaRecorderRef.current = mediaRecorder;
      setIsRecordingSession(true);
    } catch (error) {
      console.error("Failed to start webcam recording:", error);
      setError("Could not access camera/microphone. Please check permissions.");
    }
  }, [onRecordingComplete]);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecordingSession(false);
    }
  }, []);

  return {
    isRecordingSession,
    error,
    stream,
    recordedBlob,
    startRecording,
    stopRecording
  };
};