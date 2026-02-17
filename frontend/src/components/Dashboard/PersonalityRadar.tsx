import {
    Radar,
    RadarChart,
    PolarGrid,
    PolarAngleAxis,
    PolarRadiusAxis,
    ResponsiveContainer,
    Tooltip
} from 'recharts';

const data = [
    { subject: 'Openness', A: 85, fullMark: 100 },
    { subject: 'Conscientious', A: 65, fullMark: 100 },
    { subject: 'Extraversion', A: 45, fullMark: 100 },
    { subject: 'Agreeableness', A: 90, fullMark: 100 },
    { subject: 'Neuroticism', A: 30, fullMark: 100 },
];

export const PersonalityRadar = () => {
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
