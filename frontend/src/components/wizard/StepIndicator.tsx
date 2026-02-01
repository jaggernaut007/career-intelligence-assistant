import { Check } from 'lucide-react';
import { cn } from '@/utils/cn';
import type { WizardStep } from '@/types/specs';

interface Step {
  number: WizardStep;
  label: string;
}

const steps: Step[] = [
  { number: 1, label: 'Upload Resume' },
  { number: 2, label: 'Add Jobs' },
  { number: 3, label: 'Analysis' },
  { number: 4, label: 'Explore' },
];

interface StepIndicatorProps {
  currentStep: WizardStep;
  completedSteps: Set<WizardStep>;
}

export function StepIndicator({ currentStep, completedSteps }: StepIndicatorProps) {
  const getStepStatus = (stepNumber: WizardStep) => {
    if (completedSteps.has(stepNumber)) return 'completed';
    if (stepNumber === currentStep) return 'active';
    if (stepNumber < currentStep) return 'completed';
    return 'disabled';
  };

  return (
    <nav aria-label="Progress">
      <ol className="flex items-center justify-between w-full max-w-2xl mx-auto">
        {steps.map((step, index) => {
          const status = getStepStatus(step.number);
          const isLast = index === steps.length - 1;

          return (
            <li key={step.number} className="flex items-center flex-1">
              <div className="flex flex-col items-center">
                <button
                  data-testid={`step-indicator-${step.number}`}
                  aria-label={`Step ${step.number}: ${step.label}, ${status}`}
                  aria-current={status === 'active' ? 'step' : undefined}
                  disabled={status === 'disabled'}
                  className={cn(
                    'flex items-center justify-center w-10 h-10 rounded-full text-sm font-medium transition-all',
                    status === 'active' && 'active bg-blue-600 text-white ring-4 ring-blue-100',
                    status === 'completed' && 'completed bg-green-500 text-white',
                    status === 'disabled' && 'disabled bg-gray-200 text-gray-500 cursor-not-allowed'
                  )}
                >
                  {status === 'completed' ? (
                    <Check className="w-5 h-5" />
                  ) : (
                    step.number
                  )}
                </button>
                <span
                  className={cn(
                    'mt-2 text-xs font-medium',
                    status === 'active' && 'text-blue-600',
                    status === 'completed' && 'text-green-600',
                    status === 'disabled' && 'text-gray-400'
                  )}
                >
                  {step.label}
                </span>
              </div>

              {!isLast && (
                <div
                  className={cn(
                    'flex-1 h-0.5 mx-4',
                    completedSteps.has(step.number) || step.number < currentStep
                      ? 'bg-green-500'
                      : 'bg-gray-200'
                  )}
                />
              )}
            </li>
          );
        })}
      </ol>

      {/* Screen reader announcement */}
      <div aria-live="polite" className="sr-only">
        Currently on step {currentStep}: {steps[currentStep - 1]?.label}
      </div>
    </nav>
  );
}
