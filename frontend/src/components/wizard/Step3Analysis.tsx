import { useState } from 'react';
import { ChevronDown, ChevronUp, Check, X, ArrowRight, Zap, MessageCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAnalysisStore, useWizardStore } from '@/store';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { ProgressBar, getScoreVariant } from '@/components/ui/ProgressBar';
import { SkeletonList } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ChatPanel } from '@/components/chat/ChatPanel';
import type { JobMatch, MissingSkill } from '@/types/specs';

const difficultyColors: Record<string, 'success' | 'warning' | 'danger'> = {
  easy: 'success',
  medium: 'warning',
  hard: 'danger',
};

interface JobMatchCardProps {
  match: JobMatch;
  isExpanded: boolean;
  onToggle: () => void;
}

function JobMatchCard({ match, isExpanded, onToggle }: JobMatchCardProps) {
  const scoreVariant = getScoreVariant(match.fitScore);

  return (
    <Card data-testid={`job-card-${match.jobId}`}>
      <CardContent className="p-6">
        {/* Header */}
        <div className="flex items-start justify-between mb-4">
          <div>
            <h3 className="font-semibold text-gray-900 text-lg">{match.jobTitle}</h3>
            {match.company && (
              <p className="text-gray-500">{match.company}</p>
            )}
          </div>
          <div className="text-right">
            <div
              data-testid={`fit-score-${match.jobId}`}
              className={cn(
                'text-2xl font-bold',
                scoreVariant === 'success' && 'text-green-600',
                scoreVariant === 'warning' && 'text-yellow-600',
                scoreVariant === 'danger' && 'text-red-600'
              )}
            >
              {Math.round(match.fitScore)}%
            </div>
            <p className="text-sm text-gray-500">Fit Score</p>
          </div>
        </div>

        {/* Fit Score Bar */}
        <div className="mb-6" data-testid={`fit-score-bar-${match.jobId}`}>
          <ProgressBar value={match.fitScore} variant={scoreVariant} size="lg" />
        </div>

        {/* Component Scores */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div>
            <p className="text-xs text-gray-500 mb-1">Skills</p>
            <ProgressBar
              value={match.skillMatchScore}
              variant={getScoreVariant(match.skillMatchScore)}
              size="sm"
            />
            <p className="text-sm font-medium mt-1">{Math.round(match.skillMatchScore)}%</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Experience</p>
            <ProgressBar
              value={match.experienceMatchScore}
              variant={getScoreVariant(match.experienceMatchScore)}
              size="sm"
            />
            <p className="text-sm font-medium mt-1">{Math.round(match.experienceMatchScore)}%</p>
          </div>
          <div>
            <p className="text-xs text-gray-500 mb-1">Education</p>
            <ProgressBar
              value={match.educationMatchScore}
              variant={getScoreVariant(match.educationMatchScore)}
              size="sm"
            />
            <p className="text-sm font-medium mt-1">{Math.round(match.educationMatchScore)}%</p>
          </div>
        </div>

        {/* Matching Skills */}
        {match.matchingSkills.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <Check className="w-4 h-4 text-green-600" />
              Matching Skills ({match.matchingSkills.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {match.matchingSkills.slice(0, isExpanded ? undefined : 5).map((skill) => (
                <Badge
                  key={skill.skillName}
                  variant="success"
                  data-testid={`skill-${skill.skillName}`}
                >
                  <Check className="w-3 h-3 mr-1" />
                  {skill.skillName}
                  {skill.matchQuality === 'exceeds' && (
                    <Zap className="w-3 h-3 ml-1 text-yellow-500" />
                  )}
                </Badge>
              ))}
              {!isExpanded && match.matchingSkills.length > 5 && (
                <Badge variant="outline">+{match.matchingSkills.length - 5}</Badge>
              )}
            </div>
          </div>
        )}

        {/* Missing Skills (Gaps) */}
        {match.missingSkills.length > 0 && (
          <div className="mb-4">
            <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
              <X className="w-4 h-4 text-red-600" />
              Skill Gaps ({match.missingSkills.length})
            </h4>
            <div className="flex flex-wrap gap-2">
              {match.missingSkills.slice(0, isExpanded ? undefined : 5).map((skill: MissingSkill) => (
                <Badge
                  key={skill.skillName}
                  variant={skill.importance === 'must_have' ? 'danger' : 'warning'}
                  data-testid={`gap-${skill.skillName}`}
                >
                  <X className="w-3 h-3 mr-1" />
                  {skill.skillName}
                  <span
                    className={cn(
                      'ml-1 text-xs opacity-75',
                      difficultyColors[skill.difficultyToAcquire]
                    )}
                  >
                    ({skill.difficultyToAcquire})
                  </span>
                </Badge>
              ))}
              {!isExpanded && match.missingSkills.length > 5 && (
                <Badge variant="outline">+{match.missingSkills.length - 5}</Badge>
              )}
            </div>
          </div>
        )}

        {/* Expand/Collapse Button */}
        <button
          onClick={onToggle}
          data-testid={`expand-job-${match.jobId}`}
          className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 mt-4"
        >
          {isExpanded ? (
            <>
              <ChevronUp className="w-4 h-4" />
              Show less
            </>
          ) : (
            <>
              <ChevronDown className="w-4 h-4" />
              Show more details
            </>
          )}
        </button>

        {/* Expanded Details */}
        {isExpanded && (
          <div data-testid={`job-details-${match.jobId}`} className="mt-4 pt-4 border-t">
            {/* Transferable Skills */}
            {match.transferableSkills.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-2 flex items-center gap-2">
                  <ArrowRight className="w-4 h-4 text-blue-600" />
                  Transferable Skills
                </h4>
                <div className="flex flex-wrap gap-2">
                  {match.transferableSkills.map((skill) => (
                    <Badge key={skill} variant="info">
                      {skill}
                    </Badge>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

// Friendly names for agents
const agentDisplayNames: Record<string, string> = {
  workflow: 'Overall Progress',
  resume_parser: 'Resume Analysis',
  jd_analyzer: 'Job Analysis',
  skill_matcher: 'Skill Matching',
  recommendation: 'Recommendations',
  interview_prep: 'Interview Prep',
  market_insights: 'Market Insights',
};

// Status icons
function StatusIcon({ status }: { status: string }) {
  if (status === 'completed') {
    return <Check className="w-4 h-4 text-green-600" />;
  }
  if (status === 'failed') {
    return <X className="w-4 h-4 text-red-600" />;
  }
  if (status === 'running') {
    return (
      <div className="w-4 h-4 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
    );
  }
  return <div className="w-4 h-4 rounded-full border-2 border-gray-300" />;
}

function AgentProgressDisplay() {
  const agentStatuses = useWizardStore((s) => s.agentStatuses);

  if (agentStatuses.length === 0) return null;

  // Find the currently running agent for the main status display
  const runningAgent = agentStatuses.find((a) => a.status === 'running');
  const currentStep = runningAgent?.currentStep || 'Processing...';

  return (
    <Card className="mb-6">
      <CardContent className="p-4">
        {/* Main status message */}
        <div className="mb-4 pb-4 border-b border-gray-100">
          <div className="flex items-center gap-2 mb-1">
            <div className="w-5 h-5 border-2 border-blue-600 border-t-transparent rounded-full animate-spin" />
            <span className="text-sm font-medium text-gray-900">Analysis in Progress</span>
          </div>
          <p className="text-sm text-blue-600 ml-7">{currentStep}</p>
          <p className="text-xs text-gray-400 ml-7 mt-1">
            Full analysis typically takes 3-5 minutes
          </p>
        </div>

        {/* Agent progress list */}
        <h4 className="text-xs font-medium text-gray-500 uppercase tracking-wide mb-3">
          Agent Status
        </h4>
        <div className="space-y-3">
          {agentStatuses
            .filter((a) => a.agentName !== 'workflow')
            .map((agent) => (
              <div key={agent.agentName}>
                <div className="flex items-center gap-3">
                  <StatusIcon status={agent.status} />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center justify-between mb-1">
                      <span className="text-sm font-medium text-gray-700 truncate">
                        {agentDisplayNames[agent.agentName] || agent.agentName}
                      </span>
                      <span className="text-xs text-gray-500 ml-2">
                        {agent.progress}%
                      </span>
                    </div>
                    <ProgressBar
                      value={agent.progress}
                      variant={
                        agent.status === 'completed'
                          ? 'success'
                          : agent.status === 'failed'
                          ? 'danger'
                          : 'default'
                      }
                      size="sm"
                    />
                  </div>
                </div>
                {/* Show current step for running agents */}
                {agent.status === 'running' && agent.currentStep && (
                  <p className="text-xs text-gray-500 mt-1 ml-7 truncate">
                    {agent.currentStep}
                  </p>
                )}
                {/* Show error for failed agents */}
                {agent.status === 'failed' && agent.error && (
                  <p className="text-xs text-red-500 mt-1 ml-7 truncate">
                    {agent.error}
                  </p>
                )}
              </div>
            ))}
        </div>
      </CardContent>
    </Card>
  );
}

export function Step3Analysis() {
  const [expandedJobs, setExpandedJobs] = useState<Set<string>>(new Set());
  const [isChatOpen, setIsChatOpen] = useState(false);
  const analysisResult = useAnalysisStore((s) => s.analysisResult);
  const isAnalyzing = useWizardStore((s) => s.isAnalyzing);

  const toggleExpanded = (jobId: string) => {
    setExpandedJobs((prev) => {
      const next = new Set(prev);
      if (next.has(jobId)) {
        next.delete(jobId);
      } else {
        next.add(jobId);
      }
      return next;
    });
  };

  // Sort by fit score (highest first)
  const sortedMatches = [...(analysisResult?.jobMatches || [])].sort(
    (a, b) => b.fitScore - a.fitScore
  );

  // Get the best match job for chat context
  const bestMatch = sortedMatches[0];

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Analysis Results</h2>
        <p className="text-gray-600">
          See how well your resume matches each job description
        </p>
      </div>

      {/* Chat Panel */}
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        jobId={bestMatch?.jobId}
        jobTitle={bestMatch?.jobTitle}
      />

      {/* Agent Progress */}
      {isAnalyzing && <AgentProgressDisplay />}

      {/* Loading State */}
      {isAnalyzing && !analysisResult && <SkeletonList count={3} />}

      {/* Empty State */}
      {!isAnalyzing && sortedMatches.length === 0 && (
        <EmptyState
          title="No analysis results"
          description="Complete the previous steps to see your job match analysis"
        />
      )}

      {/* Results */}
      {sortedMatches.length > 0 && (
        <div className="space-y-4">
          {sortedMatches.map((match) => (
            <JobMatchCard
              key={match.jobId}
              match={match}
              isExpanded={expandedJobs.has(match.jobId)}
              onToggle={() => toggleExpanded(match.jobId)}
            />
          ))}
        </div>
      )}

      {/* Action Bar - Expand All & Chat */}
      {sortedMatches.length > 0 && !isAnalyzing && (
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex items-center justify-center gap-4 flex-wrap">
            <Button
              variant="secondary"
              onClick={() => {
                // Expand all job cards
                setExpandedJobs(new Set(sortedMatches.map((m) => m.jobId)));
              }}
              className="flex items-center gap-2"
            >
              <ChevronDown className="w-4 h-4" />
              Expand All
            </Button>
            <Button
              variant="primary"
              onClick={() => setIsChatOpen(true)}
              className="flex items-center gap-2"
            >
              <MessageCircle className="w-4 h-4" />
              Chat with AI
            </Button>
          </div>
          <p className="text-center text-sm text-gray-500 mt-3">
            View detailed breakdowns or ask AI questions about your fit
          </p>
        </div>
      )}
    </div>
  );
}
