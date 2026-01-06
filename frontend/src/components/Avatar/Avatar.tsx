import { useRef } from 'react';
import { useFrame } from '@react-three/fiber';
import { useEmotionStore } from '../../store/useEmotionStore';
import * as THREE from 'three';

export const Avatar = () => {
    const meshRef = useRef<THREE.Mesh>(null);
    const emotion = useEmotionStore((state) => state.currentEmotion);

    useFrame((state) => {
        if (!meshRef.current) return;

        const time = state.clock.elapsedTime;

        // Simple pulsing
        const scale = 1 + Math.sin(time * 1.5) * 0.2;
        meshRef.current.scale.setScalar(scale);

        // Color based on emotion
        let color = '#b8a8e0';
        switch (emotion) {
            case 'happy': color = '#ffc870'; break;
            case 'sad': color = '#88b8e0'; break;
            case 'angry': color = '#d88898'; break;
        }

        (meshRef.current.material as THREE.MeshStandardMaterial).color.set(color);
    });

    return (
        <mesh ref={meshRef} position={[0, 0, 0]}>
            <sphereGeometry args={[2, 32, 32]} />
            <meshStandardMaterial
                color="#b8a8e0"
                roughness={0.3}
                metalness={0.2}
            />
        </mesh>
    );
};
