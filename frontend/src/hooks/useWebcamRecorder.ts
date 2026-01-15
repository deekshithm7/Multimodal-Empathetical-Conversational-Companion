import { useState, useRef, useCallback } from 'react';

const BACKEND_URL = 'http://localhost:8000'; // Change to your backend URL

export const useWebcamRecorder = () => {
  const [isRecordingSession, setIsRecordingSession] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const [extractionResults, setExtractionResults] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);
  const [stream, setStream] = useState<MediaStream | null>(null);
  
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
    return 'video/webm'; // Fallback
  };

  const getFileExtension = (mimeType: string) => {
    if (mimeType.includes('webm')) return 'webm';
    if (mimeType.includes('mp4')) return 'mp4';
    return 'webm';
  };

  const uploadToBackend = async (blob: Blob, filename: string) => {
    setIsUploading(true);
    setError(null);
    
    try {
      const formData = new FormData();
      formData.append('video', blob, filename);

      const response = await fetch(
        `${BACKEND_URL}/extract/multimodal-features?fusion_type=simple`,
        {
          method: 'POST',
          body: formData,
        }
      );

      if (!response.ok) {
        throw new Error(`Server error: ${response.status}`);
      }

      const data = await response.json();
      setExtractionResults(data);
      console.log('✅ Feature extraction results:', data);
      
      return data;
    } catch (err: any) {
      const errorMsg = err.message || 'Failed to upload video';
      setError(errorMsg);
      console.error('❌ Upload error:', err);
      throw err;
    } finally {
      setIsUploading(false);
    }
  };

  const startRecording = useCallback(async () => {
    try {
      const mediaStream = await navigator.mediaDevices.getUserMedia({
        video: true,
        audio: true
      });
      
      streamRef.current = mediaStream;
      setStream(mediaStream); // Keep stream in state for video preview
      
      const mimeType = getSupportedMimeType();
      const options = mimeType ? { mimeType } : undefined;
      const mediaRecorder = new MediaRecorder(mediaStream, options);

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          chunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        const finalMimeType = mediaRecorder.mimeType || 'video/webm';
        const blob = new Blob(chunksRef.current, { type: finalMimeType });
        chunksRef.current = [];

        // Generate filename
        const extension = getFileExtension(finalMimeType);
        const filename = `session-${new Date().toISOString().slice(0, 19).replace(/:/g, '-')}.${extension}`;

        // Download locally
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        document.body.appendChild(a);
        a.style.display = 'none';
        a.href = url;
        a.download = filename;
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        // Upload to backend
        try {
          await uploadToBackend(blob, filename);
        } catch (err) {
          console.error('Backend upload failed:', err);
        }

        // Stop all tracks and clear stream
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
      alert("Could not access camera/microphone. Please check permissions.");
    }
  }, []);

  const stopRecording = useCallback(() => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      mediaRecorderRef.current.stop();
      setIsRecordingSession(false);
    }
  }, []);

  return {
    isRecordingSession,
    isUploading,
    extractionResults,
    error,
    stream, // Export stream for video preview
    startRecording,
    stopRecording
  };
};