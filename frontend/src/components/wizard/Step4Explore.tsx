import { useState } from 'react';
import {
  TrendingUp,
  TrendingDown,
  Minus,
  ChevronDown,
  ChevronUp,
  ExternalLink,
  Download,
  MessageSquare,
  MessageCircle,
  BarChart3,
  Lightbulb,
} from 'lucide-react';
import { cn } from '@/utils/cn';
import { useAnalysisStore, useSessionStore } from '@/store';
import { useRecommendations, useInterviewPrep, useMarketInsights } from '@/api/hooks';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/Tabs';
import { Skeleton } from '@/components/ui/Skeleton';
import { EmptyState } from '@/components/ui/EmptyState';
import { ChatPanel } from '@/components/chat/ChatPanel';
import type {
  Recommendation,
  InterviewQuestion,
  Priority,
  RecommendationCategory,
  QuestionCategory,
  CareerPath,
} from '@/types/specs';

const priorityColors: Record<Priority, 'danger' | 'warning' | 'success'> = {
  high: 'danger',
  medium: 'warning',
  low: 'success',
};

const categoryLabels: Record<RecommendationCategory, string> = {
  skill_gap: 'Skill Gap',
  resume_improvement: 'Resume',
  experience_highlight: 'Experience',
  certification: 'Certification',
  networking: 'Networking',
};

const questionCategoryLabels: Record<QuestionCategory, string> = {
  behavioral: 'Behavioral',
  technical: 'Technical',
  situational: 'Situational',
  culture_fit: 'Culture Fit',
};

function JobSelector() {
  const analysisResult = useAnalysisStore((s) => s.analysisResult);
  const selectedJobId = useAnalysisStore((s) => s.selectedJobId);
  const setSelectedJob = useAnalysisStore((s) => s.setSelectedJob);

  const jobs = analysisResult?.jobMatches || [];

  if (jobs.length <= 1) return null;

  return (
    <div className="mb-6">
      <label htmlFor="job-selector" className="block text-sm font-medium text-gray-700 mb-2">
        Select Job
      </label>
      <select
        id="job-selector"
        role="combobox"
        value={selectedJobId || ''}
        onChange={(e) => setSelectedJob(e.target.value)}
        className="w-full max-w-xs px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
      >
        {jobs.map((job) => (
          <option key={job.jobId} value={job.jobId}>
            {job.jobTitle} {job.company && `at ${job.company}`}
          </option>
        ))}
      </select>
    </div>
  );
}

function RecommendationCard({ recommendation }: { recommendation: Recommendation }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant={priorityColors[recommendation.priority]} size="sm">
                {recommendation.priority}
              </Badge>
              <Badge variant="outline" size="sm">
                {categoryLabels[recommendation.category]}
              </Badge>
            </div>
            <h4 className="font-medium text-gray-900">{recommendation.title}</h4>
            <p className="text-sm text-gray-600 mt-1">{recommendation.description}</p>

            {isExpanded && (
              <div className="mt-4 space-y-4">
                {/* Action Items */}
                {recommendation.actionItems.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Action Items</h5>
                    <ul className="space-y-2">
                      {recommendation.actionItems.map((item, idx) => (
                        <li key={idx} className="flex items-start gap-2 text-sm text-gray-600">
                          <input type="checkbox" className="mt-1 rounded" />
                          <span>{item}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}

                {/* Estimated Time */}
                {recommendation.estimatedTime && (
                  <p className="text-sm text-gray-500">
                    Estimated time: {recommendation.estimatedTime}
                  </p>
                )}

                {/* Resources */}
                {recommendation.resources.length > 0 && (
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">Resources</h5>
                    <ul className="space-y-1">
                      {recommendation.resources.map((resource, idx) => (
                        <li key={idx}>
                          <a
                            href={resource}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="text-sm text-blue-600 hover:underline flex items-center gap-1"
                          >
                            {resource}
                            <ExternalLink className="w-3 h-3" />
                          </a>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </CardContent>
    </Card>
  );
}

function QuestionCard({ question }: { question: InterviewQuestion }) {
  const [isExpanded, setIsExpanded] = useState(false);

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <div className="flex items-center gap-2 mb-2">
              <Badge variant="info" size="sm">
                {questionCategoryLabels[question.category]}
              </Badge>
              <Badge
                variant={
                  question.difficulty === 'easy'
                    ? 'success'
                    : question.difficulty === 'medium'
                    ? 'warning'
                    : 'danger'
                }
                size="sm"
              >
                {question.difficulty}
              </Badge>
            </div>
            <h4 className="font-medium text-gray-900">{question.question}</h4>

            {isExpanded && (
              <div className="mt-4 space-y-4">
                {/* Suggested Answer */}
                <div>
                  <h5 className="text-sm font-medium text-gray-700 mb-2">Suggested Answer</h5>
                  <p className="text-sm text-gray-600 bg-gray-50 p-3 rounded-lg">
                    {question.suggestedAnswer}
                  </p>
                </div>

                {/* STAR Example */}
                {question.starExample && (
                  <div>
                    <h5 className="text-sm font-medium text-gray-700 mb-2">STAR Example</h5>
                    <div className="bg-blue-50 p-4 rounded-lg space-y-2 text-sm">
                      <p>
                        <strong className="text-blue-700">Situation:</strong>{' '}
                        {question.starExample.situation}
                      </p>
                      <p>
                        <strong className="text-blue-700">Task:</strong>{' '}
                        {question.starExample.task}
                      </p>
                      <p>
                        <strong className="text-blue-700">Action:</strong>{' '}
                        {question.starExample.action}
                      </p>
                      <p>
                        <strong className="text-blue-700">Result:</strong>{' '}
                        {question.starExample.result}
                      </p>
                    </div>
                  </div>
                )}

                {/* Related Experience */}
                {question.relatedExperience && (
                  <p className="text-sm text-gray-500">
                    <span className="font-medium">Related Experience:</span>{' '}
                    {question.relatedExperience}
                  </p>
                )}
              </div>
            )}
          </div>

          <button
            onClick={() => setIsExpanded(!isExpanded)}
            className="text-gray-400 hover:text-gray-600"
          >
            {isExpanded ? (
              <ChevronUp className="w-5 h-5" />
            ) : (
              <ChevronDown className="w-5 h-5" />
            )}
          </button>
        </div>
      </CardContent>
    </Card>
  );
}

function RecommendationsPanel() {
  const session = useSessionStore((s) => s.session);
  const selectedJobId = useAnalysisStore((s) => s.selectedJobId);
  const { data, isLoading } = useRecommendations(
    session?.sessionId || null,
    selectedJobId
  );

  if (isLoading) {
    return (
      <div className="space-y-4" data-testid="recommendations-loading">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  const recommendations = data?.recommendations || [];

  if (recommendations.length === 0) {
    return (
      <EmptyState
        icon={<Lightbulb className="h-12 w-12" />}
        title="No recommendations yet"
        description="Complete the analysis to get personalized recommendations"
      />
    );
  }

  // Sort by priority
  const priorityOrder: Record<Priority, number> = { high: 0, medium: 1, low: 2 };
  const sorted = [...recommendations].sort((a, b) => {
    return priorityOrder[a.priority] - priorityOrder[b.priority];
  });

  return (
    <div className="space-y-4">
      {sorted.map((rec) => (
        <RecommendationCard key={rec.id} recommendation={rec} />
      ))}
    </div>
  );
}

function InterviewPanel() {
  const session = useSessionStore((s) => s.session);
  const selectedJobId = useAnalysisStore((s) => s.selectedJobId);
  const { data, isLoading } = useInterviewPrep(
    session?.sessionId || null,
    selectedJobId
  );

  if (isLoading) {
    return (
      <div className="space-y-4" data-testid="interview-loading">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  const questions = data?.questions || [];

  if (questions.length === 0) {
    return (
      <EmptyState
        icon={<MessageSquare className="h-12 w-12" />}
        title="No interview prep yet"
        description="Complete the analysis to get interview preparation materials"
      />
    );
  }

  return (
    <div className="space-y-6">
      {/* Questions */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-4">
          Interview Questions ({questions.length})
        </h3>
        <div className="space-y-4">
          {questions.map((q: InterviewQuestion) => (
            <QuestionCard key={q.id} question={q} />
          ))}
        </div>
      </div>

      {/* Talking Points */}
      {data?.talkingPoints && data.talkingPoints.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h4 className="font-medium text-gray-900 mb-3">Key Talking Points</h4>
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
              {data.talkingPoints.map((point: string, idx: number) => (
                <li key={idx}>{point}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}

      {/* Questions to Ask */}
      {data?.questionsToAsk && data.questionsToAsk.length > 0 && (
        <Card>
          <CardContent className="p-4">
            <h4 className="font-medium text-gray-900 mb-3">Questions to Ask the Interviewer</h4>
            <ul className="list-disc list-inside space-y-2 text-sm text-gray-600">
              {data.questionsToAsk.map((q: string, idx: number) => (
                <li key={idx}>{q}</li>
              ))}
            </ul>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function MarketPanel() {
  const session = useSessionStore((s) => s.session);
  const selectedJobId = useAnalysisStore((s) => s.selectedJobId);
  const { data, isLoading } = useMarketInsights(
    session?.sessionId || null,
    selectedJobId
  );

  if (isLoading) {
    return (
      <div className="space-y-4" data-testid="market-loading">
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} className="h-32 w-full" />
        ))}
      </div>
    );
  }

  const insights = data?.insights;

  if (!insights) {
    return (
      <EmptyState
        icon={<BarChart3 className="h-12 w-12" />}
        title="No market insights yet"
        description="Complete the analysis to get market insights"
      />
    );
  }

  const TrendIcon =
    insights.demandTrend === 'increasing'
      ? TrendingUp
      : insights.demandTrend === 'decreasing'
      ? TrendingDown
      : Minus;

  const trendColor =
    insights.demandTrend === 'increasing'
      ? 'text-green-600'
      : insights.demandTrend === 'decreasing'
      ? 'text-red-600'
      : 'text-gray-600';

  const formatSalary = (value: number) =>
    new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: insights.salaryRange.currency,
      maximumFractionDigits: 0,
    }).format(value);

  return (
    <div className="space-y-6">
      {/* Salary Range */}
      <Card>
        <CardContent className="p-6">
          <h4 className="font-medium text-gray-900 mb-4">Salary Range</h4>
          <div className="flex items-end justify-between">
            <div>
              <p className="text-sm text-gray-500">Min</p>
              <p className="text-lg font-semibold">{formatSalary(insights.salaryRange.min)}</p>
            </div>
            <div className="text-center">
              <p className="text-sm text-gray-500">Median</p>
              <p className="text-2xl font-bold text-blue-600">
                {formatSalary(insights.salaryRange.median)}
              </p>
            </div>
            <div className="text-right">
              <p className="text-sm text-gray-500">Max</p>
              <p className="text-lg font-semibold">{formatSalary(insights.salaryRange.max)}</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Demand Trend */}
      <Card>
        <CardContent className="p-6">
          <h4 className="font-medium text-gray-900 mb-4">Market Demand</h4>
          <div className={cn('flex items-center gap-2', trendColor)}>
            <TrendIcon className="w-6 h-6" />
            <span className="text-lg font-semibold capitalize">{insights.demandTrend}</span>
          </div>
        </CardContent>
      </Card>

      {/* Top Skills */}
      {insights.topSkillsInDemand.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h4 className="font-medium text-gray-900 mb-4">Top Skills in Demand</h4>
            <div className="flex flex-wrap gap-2">
              {insights.topSkillsInDemand.map((skill: string) => (
                <Badge key={skill} variant="info">
                  {skill}
                </Badge>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Career Paths */}
      {insights.careerPaths.length > 0 && (
        <Card>
          <CardContent className="p-6">
            <h4 className="font-medium text-gray-900 mb-4">Career Progression</h4>
            <div className="space-y-4">
              {insights.careerPaths.map((path: CareerPath, idx: number) => (
                <div
                  key={idx}
                  className="flex items-center justify-between border-b border-gray-100 pb-3 last:border-0"
                >
                  <div>
                    <p className="font-medium text-gray-900">{path.title}</p>
                    <p className="text-sm text-gray-500">
                      ~{path.typicalYearsToReach} years to reach
                    </p>
                  </div>
                  {path.salaryIncreasePercent && (
                    <Badge variant="success">+{path.salaryIncreasePercent}% salary</Badge>
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Industry Insights */}
      {insights.industryInsights && (
        <Card>
          <CardContent className="p-6">
            <h4 className="font-medium text-gray-900 mb-4">Industry Insights</h4>
            <p className="text-gray-600">{insights.industryInsights}</p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

export function Step4Explore() {
  const [isChatOpen, setIsChatOpen] = useState(false);
  const analysisResult = useAnalysisStore((s) => s.analysisResult);
  const selectedJobId = useAnalysisStore((s) => s.selectedJobId);

  // Get the selected job for chat context
  const selectedJob = analysisResult?.jobMatches?.find((j) => j.jobId === selectedJobId)
    || analysisResult?.jobMatches?.[0];

  const handleExport = async () => {
    window.print();
  };

  return (
    <div className="space-y-6">
      {/* Chat Panel */}
      <ChatPanel
        isOpen={isChatOpen}
        onClose={() => setIsChatOpen(false)}
        jobId={selectedJob?.jobId}
        jobTitle={selectedJob?.jobTitle}
      />

      <div className="flex items-center justify-between mb-8">
        <div>
          <h2 className="text-2xl font-bold text-gray-900 mb-2">Explore Your Results</h2>
          <p className="text-gray-600">
            Get personalized recommendations, interview prep, and market insights
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button variant="primary" onClick={() => setIsChatOpen(true)}>
            <MessageCircle className="w-4 h-4 mr-2" />
            Chat with AI
          </Button>
          <Button variant="secondary" onClick={handleExport}>
            <Download className="w-4 h-4 mr-2" />
            Export PDF
          </Button>
        </div>
      </div>

      <JobSelector />

      <Tabs defaultValue="recommendations">
        <TabsList>
          <TabsTrigger value="recommendations">
            <Lightbulb className="w-4 h-4 mr-2" />
            Recommendations
          </TabsTrigger>
          <TabsTrigger value="interview">
            <MessageSquare className="w-4 h-4 mr-2" />
            Interview
          </TabsTrigger>
          <TabsTrigger value="market">
            <BarChart3 className="w-4 h-4 mr-2" />
            Market
          </TabsTrigger>
        </TabsList>

        <TabsContent value="recommendations">
          <RecommendationsPanel />
        </TabsContent>

        <TabsContent value="interview">
          <InterviewPanel />
        </TabsContent>

        <TabsContent value="market">
          <MarketPanel />
        </TabsContent>
      </Tabs>
    </div>
  );
}
