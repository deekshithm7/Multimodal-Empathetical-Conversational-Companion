import { Canvas } from '@react-three/fiber';
import { OrbitControls } from '@react-three/drei';
import { Avatar } from './Avatar';

export const AvatarScene = () => {
    return (
        <div className="w-full h-full relative">
            <Canvas camera={{ position: [0, 0, 6], fov: 50 }} gl={{ alpha: true }}>
                {/* Transparency enabled */}
                <ambientLight intensity={1} />
                <directionalLight position={[5, 5, 5]} intensity={0.8} />
                <Avatar />
                <OrbitControls enableZoom={false} enablePan={false} />
            </Canvas>
        </div>
    );
};
