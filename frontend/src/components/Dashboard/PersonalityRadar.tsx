import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip
} from 'recharts';

interface RadarProps {
    traits?: Array<{ label: string; score: number; desc: string }>;
}

export const PersonalityRadar = ({ traits }: RadarProps) => {
    // Recharts expects an array of objects like { subject: 'Math', A: 120, fullMark: 150 }
    // We map our 0-100 traits
    const defaultData = [
        { subject: 'Openness', A: 0, fullMark: 100 },
        { subject: 'Conscientious', A: 0, fullMark: 100 },
        { subject: 'Extraversion', A: 0, fullMark: 100 },
        { subject: 'Agreeableness', A: 0, fullMark: 100 },
        { subject: 'Neuroticism', A: 0, fullMark: 100 },
    ];

    const data = traits && traits.length > 0 
        ? traits.map(t => ({
            subject: t.label === 'Conscientiousness' ? 'Conscientious' : t.label, // shorten for radar viewing
            A: t.score,
            fullMark: 100
        }))
        : defaultData;

    return (
        <div className="w-full h-full flex flex-col items-center justify-center relative min-w-0">
            <ResponsiveContainer width="100%" height="100%">
                <RadarChart cx="50%" cy="50%" outerRadius="70%" data={data}>
                    <PolarGrid stroke="#334155" />
                    <PolarAngleAxis
                        dataKey="subject"
                        tick={{ fill: '#94a3b8', fontSize: 12 }}
                    />
                    <PolarRadiusAxis angle={30} domain={[0, 100]} tick={false} axisLine={false} />
                    <Radar
                        name="My Profile"
                        dataKey="A"
                        stroke="#00C9A7"
                        strokeWidth={2}
                        fill="#00C9A7"
                        fillOpacity={0.2}
                    />
                    <Tooltip
                        contentStyle={{ backgroundColor: '#1a1d24', borderColor: '#333', borderRadius: '8px' }}
                        itemStyle={{ color: '#00C9A7' }}
                    />
                </RadarChart>
            </ResponsiveContainer>
        </div>
    );
};
