import { useState, useEffect, useCallback } from 'react';
import { AnimatePresence, motion } from 'framer-motion';
import { RefreshCw } from 'lucide-react';
import { useWizardStore, useSessionStore, useAnalysisStore } from '@/store';
import { useStartAnalysis, useAnalysisResults, useCreateSession } from '@/api/hooks';
import { useWebSocket } from '@/hooks/useWebSocket';
import { Button } from '@/components/ui/Button';
import { Alert } from '@/components/ui/Alert';
import { StepIndicator } from './StepIndicator';
import { Step1Upload } from './Step1Upload';
import { Step2Jobs } from './Step2Jobs';
import { Step3Analysis } from './Step3Analysis';
import { Step4Explore } from './Step4Explore';
import type { WizardStep } from '@/types/specs';

const stepVariants = {
  enter: (direction: number) => ({
    x: direction > 0 ? 100 : -100,
    opacity: 0,
  }),
  center: {
    x: 0,
    opacity: 1,
  },
  exit: (direction: number) => ({
    x: direction < 0 ? 100 : -100,
    opacity: 0,
  }),
};

interface WizardContainerProps {
  initialStep?: WizardStep;
}

export function WizardContainer({ initialStep }: WizardContainerProps) {
  const [direction, setDirection] = useState(0);
  const [completedSteps, setCompletedSteps] = useState<Set<WizardStep>>(new Set());
  const [isPolling, setIsPolling] = useState(false);

  const currentStep = useWizardStore((s) => s.currentStep);
  const setStep = useWizardStore((s) => s.setStep);
  const canProceed = useWizardStore((s) => s.canProceed);
  const isAnalyzing = useWizardStore((s) => s.isAnalyzing);
  const setAnalyzing = useWizardStore((s) => s.setAnalyzing);
  const setCanProceed = useWizardStore((s) => s.setCanProceed);
  const error = useWizardStore((s) => s.error);
  const setError = useWizardStore((s) => s.setError);
  const clearAgentStatuses = useWizardStore((s) => s.clearAgentStatuses);

  const session = useSessionStore((s) => s.session);
  const setSession = useSessionStore((s) => s.setSession);
  const clearSession = useSessionStore((s) => s.clearSession);
  const resume = useAnalysisStore((s) => s.resume);
  const jobDescriptions = useAnalysisStore((s) => s.jobDescriptions);
  const analysisResult = useAnalysisStore((s) => s.analysisResult);
  const clearAnalysis = useAnalysisStore((s) => s.clearAll);
  const resetWizard = useWizardStore((s) => s.reset);

  const startAnalysisMutation = useStartAnalysis();
  const createSessionMutation = useCreateSession();

  // Poll for analysis results
  useAnalysisResults(session?.sessionId || null, isPolling);

  // WebSocket for real-time updates
  useWebSocket({
    sessionId: session?.sessionId || null,
    enabled: isAnalyzing,
    onComplete: () => {
      setIsPolling(true);
    },
  });

  // Set initial step if provided
  useEffect(() => {
    if (initialStep) {
      setStep(initialStep);
    }
  }, [initialStep, setStep]);

  // Update canProceed based on current step state
  useEffect(() => {
    switch (currentStep) {
      case 1:
        setCanProceed(!!resume);
        break;
      case 2:
        setCanProceed(jobDescriptions.length > 0);
        break;
      case 3:
        // Can proceed when analysis is complete
        setCanProceed(!!analysisResult && !isAnalyzing);
        break;
      case 4:
        setCanProceed(false); // No next step
        break;
    }
  }, [currentStep, resume, jobDescriptions, analysisResult, isAnalyzing, setCanProceed]);

  // Auto-advance to Step 3 when analysis completes
  useEffect(() => {
    if (currentStep === 2 && analysisResult && !isAnalyzing) {
      setDirection(1);
      setCompletedSteps((prev) => new Set([...prev, 2]));
      setStep(3);
    }
  }, [currentStep, analysisResult, isAnalyzing, setStep]);

  const handleNext = useCallback(() => {
    if (!canProceed || currentStep === 4) return;

    setDirection(1);
    setCompletedSteps((prev) => new Set([...prev, currentStep]));
    setStep((currentStep + 1) as WizardStep);
    setError(null);
  }, [canProceed, currentStep, setStep, setError]);

  const handleBack = useCallback(() => {
    if (currentStep === 1) return;

    setDirection(-1);
    setStep((currentStep - 1) as WizardStep);
    setError(null);
  }, [currentStep, setStep, setError]);

  const handleAnalyze = useCallback(async () => {
    if (jobDescriptions.length === 0) return;

    setError(null);
    clearAgentStatuses();
    setAnalyzing(true);
    setIsPolling(true); // Start polling immediately

    try {
      await startAnalysisMutation.mutateAsync();
      // WebSocket will handle progress updates
      // Polling will check for completion
    } catch (err) {
      setError((err as Error).message);
      setAnalyzing(false);
      setIsPolling(false);
    }
  }, [jobDescriptions, startAnalysisMutation, setError, clearAgentStatuses, setAnalyzing]);

  const handleStartFresh = useCallback(async () => {
    // Clear all stores
    clearSession();
    clearAnalysis();
    resetWizard();
    setCompletedSteps(new Set());
    setIsPolling(false);

    // Create a new session
    try {
      const newSession = await createSessionMutation.mutateAsync();
      setSession(newSession);
    } catch (err) {
      console.error('Failed to create new session:', err);
    }
  }, [clearSession, clearAnalysis, resetWizard, createSessionMutation, setSession]);

  const renderStep = () => {
    switch (currentStep) {
      case 1:
        return <Step1Upload />;
      case 2:
        return <Step2Jobs />;
      case 3:
        return <Step3Analysis />;
      case 4:
        return <Step4Explore />;
      default:
        return null;
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-8 px-4">
      <div className="max-w-4xl mx-auto">
        {/* Step Indicator */}
        <div className="mb-8">
          <StepIndicator currentStep={currentStep} completedSteps={completedSteps} />
        </div>

        {/* Error Display */}
        {error && (
          <Alert variant="error" className="mb-6">
            {error}
          </Alert>
        )}

        {/* Step Content */}
        <div className="bg-white rounded-2xl shadow-sm border border-gray-200 p-8 min-h-[500px]">
          <AnimatePresence mode="wait" custom={direction}>
            <motion.div
              key={currentStep}
              custom={direction}
              variants={stepVariants}
              initial="enter"
              animate="center"
              exit="exit"
              transition={{ duration: 0.3, ease: 'easeInOut' }}
            >
              {renderStep()}
            </motion.div>
          </AnimatePresence>
        </div>

        {/* Navigation Buttons */}
        <div className="flex items-center justify-between mt-6">
          <div>
            {currentStep > 1 && (
              <Button
                variant="secondary"
                onClick={handleBack}
                disabled={isAnalyzing}
              >
                Back
              </Button>
            )}
          </div>

          <div className="flex items-center gap-3">
            {currentStep === 2 && (
              <Button
                onClick={handleAnalyze}
                disabled={jobDescriptions.length === 0 || isAnalyzing}
                isLoading={isAnalyzing}
              >
                {isAnalyzing ? 'Analyzing...' : 'Analyze'}
              </Button>
            )}

            {currentStep < 4 && currentStep !== 2 && (
              <Button
                onClick={handleNext}
                disabled={!canProceed || isAnalyzing}
              >
                Next
              </Button>
            )}

            {currentStep === 3 && (
              <Button
                onClick={handleNext}
                disabled={!canProceed || isAnalyzing}
              >
                Explore Results
              </Button>
            )}

            {currentStep === 4 && (
              <Button
                variant="primary"
                onClick={handleStartFresh}
                isLoading={createSessionMutation.isPending}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                Start Fresh
              </Button>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}
