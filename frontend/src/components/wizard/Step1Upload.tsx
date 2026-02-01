import { useRef } from 'react';
import { Upload, FileText, CheckCircle2, AlertCircle, Shield } from 'lucide-react';
import { cn } from '@/utils/cn';
import { useFileUpload } from '@/hooks/useFileUpload';
import { useUploadResume } from '@/api/hooks';
import { useAnalysisStore } from '@/store';
import { formatFileSize } from '@/utils/validation';
import { Button } from '@/components/ui/Button';
import { Card, CardContent } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { ProgressBar } from '@/components/ui/ProgressBar';
import { Alert } from '@/components/ui/Alert';
import type { SkillLevel } from '@/types/specs';

const skillLevelColors: Record<SkillLevel, 'default' | 'info' | 'success' | 'warning'> = {
  beginner: 'default',
  intermediate: 'info',
  advanced: 'success',
  expert: 'warning',
};

export function Step1Upload() {
  const fileInputRef = useRef<HTMLInputElement>(null);
  const uploadMutation = useUploadResume();
  const resume = useAnalysisStore((s) => s.resume);

  const {
    file,
    isDragging,
    isUploading,
    uploadProgress,
    error,
    handleDragEnter,
    handleDragLeave,
    handleDragOver,
    handleDrop,
    handleFileSelect,
    reset,
  } = useFileUpload({
    onUpload: async (file) => {
      await uploadMutation.mutateAsync(file);
    },
  });

  const handleClick = () => {
    fileInputRef.current?.click();
  };

  const handleReplace = () => {
    reset();
    fileInputRef.current?.click();
  };

  const combinedError = error || (uploadMutation.error as Error)?.message;

  return (
    <div className="space-y-6">
      <div className="text-center mb-8">
        <h2 className="text-2xl font-bold text-gray-900 mb-2">Upload Your Resume</h2>
        <p className="text-gray-600">
          Upload your resume to get started with AI-powered analysis
        </p>
      </div>

      {/* PII Notice */}
      <Alert variant="info" title="Privacy Protection">
        <div className="flex items-start gap-2">
          <Shield className="w-4 h-4 mt-0.5 shrink-0" />
          <span>
            Your personal information (SSN, phone, email, address) will be automatically
            redacted to protect your privacy. Only relevant career information is analyzed.
          </span>
        </div>
      </Alert>

      {/* Upload Zone */}
      {!resume ? (
        <div
          data-testid="drop-zone"
          onDragEnter={handleDragEnter}
          onDragLeave={handleDragLeave}
          onDragOver={handleDragOver}
          onDrop={handleDrop}
          onClick={handleClick}
          className={cn(
            'border-2 border-dashed rounded-xl p-12 text-center cursor-pointer transition-all',
            isDragging
              ? 'drag-active border-blue-500 bg-blue-50'
              : 'border-gray-300 hover:border-blue-400 hover:bg-gray-50',
            isUploading && 'pointer-events-none opacity-60'
          )}
        >
          <input
            ref={fileInputRef}
            type="file"
            data-testid="file-input"
            accept=".pdf,.docx,.txt,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document,text/plain"
            onChange={handleFileSelect}
            className="hidden"
            aria-label="Upload resume file"
          />

          {isUploading ? (
            <div className="space-y-4">
              <div className="mx-auto w-12 h-12 rounded-full bg-blue-100 flex items-center justify-center">
                <Upload className="w-6 h-6 text-blue-600 animate-pulse" />
              </div>
              <div>
                <p className="font-medium text-gray-900">Processing your resume...</p>
                <p className="text-sm text-gray-500">{file?.name}</p>
              </div>
              <div className="max-w-xs mx-auto">
                <ProgressBar value={uploadProgress} showLabel />
              </div>
              <p className="text-xs text-gray-400">
                This typically takes 2-3 minutes while we analyze your skills and experience
              </p>
            </div>
          ) : (
            <>
              <div className="mx-auto w-12 h-12 rounded-full bg-gray-100 flex items-center justify-center mb-4">
                <Upload className="w-6 h-6 text-gray-600" />
              </div>
              <p className="text-gray-900 font-medium mb-1">
                Drag and drop your resume here
              </p>
              <p className="text-gray-500 text-sm mb-4">
                or click to browse files
              </p>
              <div className="flex items-center justify-center gap-2 text-xs text-gray-400">
                <Badge variant="outline" size="sm">PDF</Badge>
                <Badge variant="outline" size="sm">DOCX</Badge>
                <Badge variant="outline" size="sm">TXT</Badge>
                <span className="text-gray-300">|</span>
                <span>Max 10MB</span>
              </div>
            </>
          )}
        </div>
      ) : (
        /* Resume Preview */
        <Card>
          <CardContent className="p-6">
            <div className="flex items-start justify-between mb-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                  <CheckCircle2 className="w-5 h-5 text-green-600" />
                </div>
                <div>
                  <p className="font-medium text-gray-900">Resume uploaded successfully</p>
                  <p className="text-sm text-gray-500">
                    {file?.name} • {file && formatFileSize(file.size)}
                  </p>
                </div>
              </div>
              <Button variant="ghost" size="sm" onClick={handleReplace}>
                Replace
              </Button>
            </div>

            {resume.contactRedacted && (
              <div className="flex items-center gap-2 text-sm text-green-600 mb-6">
                <Shield className="w-4 h-4" />
                <span>Personal information has been redacted</span>
              </div>
            )}

            {/* Skills Preview */}
            {resume.skills.length > 0 && (
              <div className="mb-6">
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Extracted Skills ({resume.skills.length})
                </h4>
                <div className="flex flex-wrap gap-2">
                  {resume.skills.slice(0, 15).map((skill) => (
                    <Badge key={skill.name} variant={skillLevelColors[skill.level]}>
                      {skill.name}
                      {skill.yearsExperience && (
                        <span className="ml-1 opacity-70">{skill.yearsExperience}y</span>
                      )}
                    </Badge>
                  ))}
                  {resume.skills.length > 15 && (
                    <Badge variant="outline">+{resume.skills.length - 15} more</Badge>
                  )}
                </div>
              </div>
            )}

            {/* Experience Preview */}
            {resume.experiences.length > 0 && (
              <div>
                <h4 className="text-sm font-medium text-gray-700 mb-3">
                  Work Experience ({resume.experiences.length})
                </h4>
                <div className="space-y-3">
                  {resume.experiences.slice(0, 3).map((exp, idx) => (
                    <div key={idx} className="flex items-start gap-3">
                      <FileText className="w-4 h-4 text-gray-400 mt-1" />
                      <div>
                        <p className="font-medium text-gray-900">{exp.title}</p>
                        <p className="text-sm text-gray-500">
                          {exp.company} • {exp.duration}
                        </p>
                      </div>
                    </div>
                  ))}
                  {resume.experiences.length > 3 && (
                    <p className="text-sm text-gray-500 ml-7">
                      +{resume.experiences.length - 3} more positions
                    </p>
                  )}
                </div>
              </div>
            )}
          </CardContent>
        </Card>
      )}

      {/* Error Display */}
      {combinedError && (
        <Alert variant="error">
          <div className="flex items-center gap-2">
            <AlertCircle className="w-4 h-4" />
            <span>{combinedError}</span>
          </div>
        </Alert>
      )}
    </div>
  );
}
