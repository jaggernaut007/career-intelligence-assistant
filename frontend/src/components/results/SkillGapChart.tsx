import React from 'react';
import { Card } from '../ui/Card';
import { JobMatch, MissingSkill, SkillMatch } from '../../types/specs';
import { 
  BarChart, 
  Bar, 
  XAxis, 
  YAxis, 
  CartesianGrid, 
  Tooltip, 
  Legend, 
  ResponsiveContainer,
  Cell
} from 'recharts';

interface SkillGapChartProps {
  jobMatch: JobMatch;
}

export const SkillGapChart: React.FC<SkillGapChartProps> = ({ jobMatch }) => {
  const { matchingSkills, missingSkills } = jobMatch;

  // Transform data for the chart
  // We want to show a comparison of Resume Level vs Required Level (if available)
  // For matching skills, we have both. For missing, we might only have required (implied).

  // Helper to convert levels to numbers for charting
  const levelToScore = (level?: string) => {
    switch (level) {
      case 'beginner': return 25;
      case 'intermediate': return 50;
      case 'advanced': return 75;
      case 'expert': return 100;
      default: return 0;
    }
  };

  const chartData = [
    ...matchingSkills.map((s: SkillMatch) => ({
      name: s.skillName,
      resumeScore: levelToScore(s.resumeLevel),
      requiredScore: levelToScore(s.requiredLevel || 'intermediate'), // Default to intermediate if not specified
      type: 'match',
      quality: s.matchQuality
    })),
    ...missingSkills.map((s: MissingSkill) => ({
      name: s.skillName,
      resumeScore: 0, // Missing means 0 or very low
      requiredScore: 50, // Assume intermediate needed for missing ones usually
      type: 'missing',
      importance: s.importance
    }))
  ].slice(0, 10); // Limit to top 10 to avoid overcrowding

  return (
    <Card className="p-6 h-[400px] flex flex-col">
      <h3 className="text-lg font-bold text-gray-900 mb-4">Skill Alignment Analysis</h3>
        {chartData.length > 0 ? (
          <div className="flex-1 w-full min-h-0">
            <ResponsiveContainer width="100%" height="100%">
              <BarChart
                data={chartData}
                layout="vertical"
                margin={{ top: 5, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" horizontal={false} />
                <XAxis type="number" domain={[0, 100]} hide />
                <YAxis 
                    dataKey="name" 
                    type="category" 
                    width={100} 
                    tick={{fontSize: 12}}
                    interval={0}
                />
                <Tooltip 
                    formatter={(value: number) => {
                        if (value === 0) return 'Missing';
                        if (value === 25) return 'Beginner';
                        if (value === 50) return 'Intermediate';
                        if (value === 75) return 'Advanced';
                        if (value === 100) return 'Expert';
                        return value;
                    }}
                />
                <Legend />
                <Bar dataKey="resumeScore" name="Your Level" fill="#3b82f6" barSize={20}>
                    {chartData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.type === 'missing' ? '#ef4444' : '#3b82f6'} />
                    ))}
                </Bar>
                <Bar dataKey="requiredScore" name="Required Level" fill="#e5e7eb" barSize={20} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        ) : (
            <div className="flex items-center justify-center h-full text-gray-500">
                No skill data available to chart.
            </div>
        )}
    </Card>
  );
};
