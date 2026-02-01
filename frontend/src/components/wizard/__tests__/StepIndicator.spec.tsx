/**
 * Tests for StepIndicator component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { StepIndicator } from '../StepIndicator';
import type { WizardStep } from '@/types/specs';

describe('StepIndicator', () => {
  const renderStepIndicator = (
    currentStep: WizardStep = 1,
    completedSteps: Set<WizardStep> = new Set()
  ) => {
    return render(
      <StepIndicator currentStep={currentStep} completedSteps={completedSteps} />
    );
  };

  describe('Rendering', () => {
    it('renders navigation element', () => {
      renderStepIndicator();
      expect(screen.getByRole('navigation', { name: 'Progress' })).toBeInTheDocument();
    });

    it('renders all four steps', () => {
      renderStepIndicator();
      expect(screen.getByTestId('step-indicator-1')).toBeInTheDocument();
      expect(screen.getByTestId('step-indicator-2')).toBeInTheDocument();
      expect(screen.getByTestId('step-indicator-3')).toBeInTheDocument();
      expect(screen.getByTestId('step-indicator-4')).toBeInTheDocument();
    });

    it('renders step labels', () => {
      renderStepIndicator();
      expect(screen.getByText('Upload Resume')).toBeInTheDocument();
      expect(screen.getByText('Add Jobs')).toBeInTheDocument();
      expect(screen.getByText('Analysis')).toBeInTheDocument();
      expect(screen.getByText('Explore')).toBeInTheDocument();
    });
  });

  describe('Step States', () => {
    describe('Active Step', () => {
      it('marks current step as active', () => {
        renderStepIndicator(2);
        const step2 = screen.getByTestId('step-indicator-2');
        expect(step2).toHaveClass('active');
        expect(step2).toHaveAttribute('aria-current', 'step');
      });

      it('applies active styling', () => {
        renderStepIndicator(1);
        const step1 = screen.getByTestId('step-indicator-1');
        expect(step1).toHaveClass('bg-blue-600', 'text-white', 'ring-4');
      });

      it('shows step number for active step', () => {
        renderStepIndicator(2);
        expect(screen.getByTestId('step-indicator-2')).toHaveTextContent('2');
      });
    });

    describe('Completed Step', () => {
      it('marks step as completed when in completedSteps set', () => {
        renderStepIndicator(2, new Set([1] as WizardStep[]));
        const step1 = screen.getByTestId('step-indicator-1');
        expect(step1).toHaveClass('completed');
      });

      it('applies completed styling', () => {
        renderStepIndicator(2, new Set([1] as WizardStep[]));
        const step1 = screen.getByTestId('step-indicator-1');
        expect(step1).toHaveClass('bg-green-500', 'text-white');
      });

      it('shows checkmark for completed steps', () => {
        renderStepIndicator(2, new Set([1] as WizardStep[]));
        const step1 = screen.getByTestId('step-indicator-1');
        const checkmark = step1.querySelector('svg');
        expect(checkmark).toBeInTheDocument();
      });

      it('marks steps before current as completed', () => {
        renderStepIndicator(3);
        expect(screen.getByTestId('step-indicator-1')).toHaveClass('completed');
        expect(screen.getByTestId('step-indicator-2')).toHaveClass('completed');
      });
    });

    describe('Disabled Step', () => {
      it('marks future steps as disabled', () => {
        renderStepIndicator(1);
        const step3 = screen.getByTestId('step-indicator-3');
        expect(step3).toHaveClass('disabled');
        expect(step3).toBeDisabled();
      });

      it('applies disabled styling', () => {
        renderStepIndicator(1);
        const step4 = screen.getByTestId('step-indicator-4');
        expect(step4).toHaveClass('bg-gray-200', 'text-gray-500', 'cursor-not-allowed');
      });
    });
  });

  describe('Progress Lines', () => {
    it('shows green line for completed steps', () => {
      const { container } = renderStepIndicator(3);
      const lines = container.querySelectorAll('.bg-green-500.h-0\\.5');
      expect(lines.length).toBeGreaterThan(0);
    });

    it('shows gray line for incomplete steps', () => {
      const { container } = renderStepIndicator(1);
      const lines = container.querySelectorAll('.bg-gray-200.h-0\\.5');
      expect(lines.length).toBeGreaterThan(0);
    });
  });

  describe('Accessibility', () => {
    it('has accessible labels on step buttons', () => {
      renderStepIndicator(2);
      expect(screen.getByTestId('step-indicator-1')).toHaveAccessibleName(/Step 1: Upload Resume/);
      expect(screen.getByTestId('step-indicator-2')).toHaveAccessibleName(/Step 2: Add Jobs/);
    });

    it('includes step status in aria-label', () => {
      renderStepIndicator(2, new Set([1] as WizardStep[]));
      expect(screen.getByTestId('step-indicator-1')).toHaveAccessibleName(/completed/);
      expect(screen.getByTestId('step-indicator-2')).toHaveAccessibleName(/active/);
      expect(screen.getByTestId('step-indicator-3')).toHaveAccessibleName(/disabled/);
    });

    it('has screen reader announcement', () => {
      renderStepIndicator(2);
      expect(screen.getByText(/Currently on step 2/)).toBeInTheDocument();
    });

    it('announcement is only for screen readers', () => {
      const { container } = renderStepIndicator(2);
      const srOnly = container.querySelector('[aria-live="polite"]');
      expect(srOnly).toHaveClass('sr-only');
    });
  });

  describe('Label Colors', () => {
    it('active step label is blue', () => {
      renderStepIndicator(1);
      expect(screen.getByText('Upload Resume')).toHaveClass('text-blue-600');
    });

    it('completed step label is green', () => {
      renderStepIndicator(2, new Set([1] as WizardStep[]));
      expect(screen.getByText('Upload Resume')).toHaveClass('text-green-600');
    });

    it('disabled step label is gray', () => {
      renderStepIndicator(1);
      expect(screen.getByText('Explore')).toHaveClass('text-gray-400');
    });
  });

  describe('Step Progression', () => {
    it('correctly identifies all states at step 3', () => {
      renderStepIndicator(3, new Set([1, 2] as WizardStep[]));

      // Step 1 - completed
      expect(screen.getByTestId('step-indicator-1')).toHaveClass('completed');

      // Step 2 - completed
      expect(screen.getByTestId('step-indicator-2')).toHaveClass('completed');

      // Step 3 - active
      expect(screen.getByTestId('step-indicator-3')).toHaveClass('active');
      expect(screen.getByTestId('step-indicator-3')).toHaveAttribute('aria-current', 'step');

      // Step 4 - disabled
      expect(screen.getByTestId('step-indicator-4')).toHaveClass('disabled');
    });

    it('at final step, first 3 are completed', () => {
      renderStepIndicator(4, new Set([1, 2, 3] as WizardStep[]));

      expect(screen.getByTestId('step-indicator-1')).toHaveClass('completed');
      expect(screen.getByTestId('step-indicator-2')).toHaveClass('completed');
      expect(screen.getByTestId('step-indicator-3')).toHaveClass('completed');
      expect(screen.getByTestId('step-indicator-4')).toHaveClass('active');
    });
  });
});
