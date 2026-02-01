import React from 'react';
import { Card } from '../ui/Card';
import { ProgressBar } from '../ui/ProgressBar';
import { Badge } from '../ui/Badge';
import { JobMatch } from '../../types/specs';
import { CheckCircle, XCircle } from 'lucide-react';
import { cn } from '../../utils/cn'; // Assuming utils/cn exists or similar

interface FitScoreCardProps {
  jobMatch: JobMatch;
  className?: string; // Allow custom styling
}

export const FitScoreCard: React.FC<FitScoreCardProps> = ({ jobMatch, className }) => {
  const { 
    jobTitle, 
    company, 
    fitScore, 
    matchingSkills, 
    missingSkills 
  } = jobMatch;

  // Helper to categorize skills for display
  const exactMatches = matchingSkills.filter(s => s.matchQuality === 'exact' || s.matchQuality === 'exceeds');
  const partialMatches = matchingSkills.filter(s => s.matchQuality === 'partial');
  
  // Sort missing skills by importance
  const criticalMissing = missingSkills.filter(s => s.importance === 'must_have');
  const niceToHaveMissing = missingSkills.filter(s => s.importance === 'nice_to_have');

  return (
    <Card className={cn("p-6", className)} data-testid="fit-score-card">
      <div className="flex justify-between items-start mb-6">
        <div>
          <h3 className="text-xl font-bold text-gray-900">{jobTitle}</h3>
          {company && <p className="text-sm text-gray-500">{company}</p>}
        </div>
        <div className="text-right">
          <div className="text-3xl font-bold text-primary-600">{fitScore}%</div>
          <p className="text-xs text-gray-500 uppercase tracking-wide">Match Score</p>
        </div>
      </div>

      <div className="mb-6">
        <ProgressBar value={fitScore} className="h-3" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Matching Skills */}
        <div>
          <h4 className="flex items-center text-sm font-semibold text-gray-700 mb-3">
            <CheckCircle className="w-4 h-4 text-green-500 mr-2" />
            Matching Skills
          </h4>
          <div className="flex flex-wrap gap-2">
            {exactMatches.length > 0 ? (
              exactMatches.map((skill) => (
                <Badge key={skill.skillName} variant="success">
                  {skill.skillName}
                </Badge>
              ))
            ) : (
                <p className="text-sm text-gray-400 italic">No exact matches yet.</p>
            )}
             {partialMatches.map((skill) => (
                <Badge key={skill.skillName} variant="warning">
                  {skill.skillName} (Partial)
                </Badge>
              ))}
          </div>
        </div>

        {/* Missing Skills */}
        <div>
             <h4 className="flex items-center text-sm font-semibold text-gray-700 mb-3">
            <XCircle className="w-4 h-4 text-red-500 mr-2" />
             Missing Skills
          </h4>
          <div className="flex flex-wrap gap-2">
            {criticalMissing.length > 0 ? (
              criticalMissing.map((skill) => (
                <Badge key={skill.skillName} variant="danger">
                  {skill.skillName}
                </Badge>
              ))
            ) : niceToHaveMissing.length === 0 ? (
                 <p className="text-sm text-gray-400 italic">No missing skills!</p>
            ) : null}
            
            {niceToHaveMissing.map((skill) => (
                <Badge key={skill.skillName} variant="default">
                  {skill.skillName}
                </Badge>
              ))}
          </div>
        </div>
      </div>
    </Card>
  );
};
