import { useState } from 'react';
import { Plus, Trash2, CheckCircle2, Briefcase, AlertCircle } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useUploadJobDescription } from '@/api/hooks';
import { useAnalysisStore } from '@/store';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Spinner } from '@/components/ui/Spinner';
import { Alert } from '@/components/ui/Alert';
import { EmptyState } from '@/components/ui/EmptyState';

const MAX_JOBS = 5;

export function Step2Jobs() {
  const [jobText, setJobText] = useState('');
  const jobDescriptions = useAnalysisStore((s) => s.jobDescriptions);
  const removeJob = useAnalysisStore((s) => s.removeJob);
  const uploadMutation = useUploadJobDescription();

  const canAddMore = jobDescriptions.length < MAX_JOBS;
  const hasJobs = jobDescriptions.length > 0;

  const handleAddJob = async () => {
    if (!jobText.trim() || !canAddMore) return;

    try {
      await uploadMutation.mutateAsync(jobText.trim());
      setJobText('');
    } catch (err) {
      // Error handled by mutation
    }
  };

  const handleRemoveJob = (jobId: string) => {
    removeJob(jobId);
  };

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Add Job Descriptions</h2>
        <p className="text-gray-600">
          Paste job descriptions you're interested in to compare with your resume
        </p>
      </div>

      {/* Job Input */}
      <Card>
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <label htmlFor="job-description" className="text-sm font-medium text-gray-700">
              Job Description
            </label>
            <span className="text-sm text-gray-500">
              {jobDescriptions.length} of {MAX_JOBS} jobs
            </span>
          </div>

          <textarea
            id="job-description"
            value={jobText}
            onChange={(e) => setJobText(e.target.value)}
            placeholder="Paste a job description here..."
            disabled={!canAddMore || uploadMutation.isPending}
            className={cn(
              'w-full h-40 px-4 py-3 border border-gray-300 rounded-lg resize-none',
              'focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent',
              'placeholder:text-gray-400',
              (!canAddMore || uploadMutation.isPending) && 'opacity-50 cursor-not-allowed'
            )}
          />

          <div className="flex items-center justify-between mt-4">
            <div className="text-sm text-gray-500">
              {!canAddMore && (
                <span className="text-amber-600">
                  Maximum of {MAX_JOBS} job descriptions reached
                </span>
              )}
            </div>
            <div className="flex flex-col items-end gap-1">
              <Button
                onClick={handleAddJob}
                disabled={!jobText.trim() || !canAddMore || uploadMutation.isPending}
                isLoading={uploadMutation.isPending}
              >
                {uploadMutation.isPending ? (
                  <>
                    <Spinner size="sm" className="mr-2" data-testid="adding-spinner" />
                    Analyzing...
                  </>
                ) : (
                  <>
                    <Plus className="w-4 h-4 mr-2" />
                    Add Job
                  </>
                )}
              </Button>
              {uploadMutation.isPending && (
                <span className="text-xs text-gray-400">
                  Takes about 1-2 minutes
                </span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Error Display */}
      {uploadMutation.error && (
        <Alert variant="error">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{(uploadMutation.error as Error).message}</span>
          </div>
        </Alert>
      )}

      {/* Jobs List */}
      <div>
        <h3 className="text-sm font-medium text-gray-700 mb-4">
          Added Jobs ({jobDescriptions.length})
        </h3>

        {!hasJobs ? (
          <EmptyState
            icon={<Briefcase className="h-12 w-12" />}
            title="No jobs added yet"
            description="Paste a job description above to get started with the analysis"
          />
        ) : (
          <div className="space-y-4">
            {jobDescriptions.map((job) => (
              <Card key={job.id}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex items-start gap-3 flex-1">
                      <div
                        className="w-8 h-8 rounded-full bg-green-100 flex items-center justify-center shrink-0"
                        data-testid={`job-${job.id}-success`}
                      >
                        <CheckCircle2 className="w-4 h-4 text-green-600" />
                      </div>
                      <div className="flex-1 min-w-0">
                        <h4 className="font-medium text-gray-900 truncate">
                          {job.title || 'Untitled Position'}
                        </h4>
                        {job.company && (
                          <p className="text-sm text-gray-500">{job.company}</p>
                        )}

                        {/* Required Skills */}
                        {job.requiredSkills.length > 0 && (
                          <div className="flex flex-wrap gap-1.5 mt-3">
                            {job.requiredSkills.slice(0, 5).map((skill) => (
                              <Badge key={skill.name} variant="info" size="sm">
                                {skill.name}
                              </Badge>
                            ))}
                            {job.requiredSkills.length > 5 && (
                              <Badge variant="outline" size="sm">
                                +{job.requiredSkills.length - 5}
                              </Badge>
                            )}
                          </div>
                        )}
                      </div>
                    </div>

                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => handleRemoveJob(job.id)}
                      className="text-gray-400 hover:text-red-600"
                      aria-label={`Remove ${job.title}`}
                    >
                      <Trash2 className="w-4 h-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
