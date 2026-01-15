import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useEmotionStore } from '../../store/useEmotionStore';
import * as THREE from 'three';

export const Avatar = () => {
    const meshRef = useRef<THREE.Mesh>(null);
    const emotion = useEmotionStore((state) => state.currentEmotion);
    const aiSpeaking = useEmotionStore((state) => state.aiSpeaking);

    useFrame((state) => {
        if (!meshRef.current) return;

        const time = state.clock.elapsedTime;

        // Breathing / Pulse Logic
        let pulseFreq = 0.5; // Idle
        let pulseAmp = 0.05;

        if (aiSpeaking) {
            pulseFreq = 5.0; // Talking
            pulseAmp = 0.15;
        }

        const scale = 1 + Math.sin(time * pulseFreq) * pulseAmp;
        meshRef.current.scale.setScalar(scale);

        // Color Logic with Lerp (Smooth transition)
        const targetColor = new THREE.Color();
        switch (emotion) {
            case 'happy': targetColor.set('#ffc870'); break; // Warm Amber
            case 'sad': targetColor.set('#88b8e0'); break;   // Cool Blue
            case 'angry': targetColor.set('#e63946'); break; // Red
            default: targetColor.set('#e2e2e5'); break;      // Neutral
        }

        // Access material properly
        const mat = meshRef.current.material as THREE.MeshStandardMaterial;
        mat.color.lerp(targetColor, 0.05); // Smooth morph
    });

    return (
        <mesh ref={meshRef} position={[0, 0, 0]}>
            <sphereGeometry args={[2, 64, 64]} />
            <meshStandardMaterial
                color="#e2e2e5"
                roughness={0.4}
                metalness={0.3}
                emissive="#000000"
                emissiveIntensity={0}
            />
        </mesh>
    );
};
