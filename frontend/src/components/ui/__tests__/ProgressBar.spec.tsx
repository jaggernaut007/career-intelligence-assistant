/**
 * Tests for ProgressBar component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { ProgressBar, getScoreVariant } from '../ProgressBar';

describe('ProgressBar', () => {
  describe('Rendering', () => {
    it('renders with required value prop', () => {
      render(<ProgressBar value={50} />);
      expect(screen.getByRole('progressbar')).toBeInTheDocument();
    });

    it('sets correct aria attributes', () => {
      render(<ProgressBar value={50} max={100} />);
      const progressbar = screen.getByRole('progressbar');
      expect(progressbar).toHaveAttribute('aria-valuenow', '50');
      expect(progressbar).toHaveAttribute('aria-valuemin', '0');
      expect(progressbar).toHaveAttribute('aria-valuemax', '100');
    });
  });

  describe('Progress Calculation', () => {
    it('calculates correct percentage', () => {
      render(<ProgressBar value={25} max={100} />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveStyle({ width: '25%' });
    });

    it('calculates percentage with custom max', () => {
      render(<ProgressBar value={5} max={10} />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveStyle({ width: '50%' });
    });

    it('clamps value to 0 minimum', () => {
      render(<ProgressBar value={-10} />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveStyle({ width: '0%' });
    });

    it('clamps value to 100 maximum', () => {
      render(<ProgressBar value={150} />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveStyle({ width: '100%' });
    });
  });

  describe('Sizes', () => {
    it('renders small size', () => {
      render(<ProgressBar value={50} size="sm" />);
      expect(screen.getByRole('progressbar')).toHaveClass('h-1.5');
    });

    it('renders medium size', () => {
      render(<ProgressBar value={50} size="md" />);
      expect(screen.getByRole('progressbar')).toHaveClass('h-2.5');
    });

    it('renders large size', () => {
      render(<ProgressBar value={50} size="lg" />);
      expect(screen.getByRole('progressbar')).toHaveClass('h-4');
    });
  });

  describe('Variants', () => {
    it('renders default variant', () => {
      render(<ProgressBar value={50} variant="default" />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveClass('bg-blue-600');
    });

    it('renders success variant', () => {
      render(<ProgressBar value={50} variant="success" />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveClass('bg-green-500');
    });

    it('renders warning variant', () => {
      render(<ProgressBar value={50} variant="warning" />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveClass('bg-yellow-500');
    });

    it('renders danger variant', () => {
      render(<ProgressBar value={50} variant="danger" />);
      const progressFill = screen.getByRole('progressbar').firstChild;
      expect(progressFill).toHaveClass('bg-red-500');
    });
  });

  describe('Label', () => {
    it('does not show label by default', () => {
      render(<ProgressBar value={50} />);
      expect(screen.queryByText('50%')).not.toBeInTheDocument();
    });

    it('shows label when showLabel is true', () => {
      render(<ProgressBar value={50} showLabel />);
      expect(screen.getByText('50%')).toBeInTheDocument();
    });

    it('rounds percentage in label', () => {
      render(<ProgressBar value={33} max={100} showLabel />);
      expect(screen.getByText('33%')).toBeInTheDocument();
    });
  });

  describe('Custom className', () => {
    it('applies custom className to container', () => {
      render(<ProgressBar value={50} className="custom-class" />);
      expect(screen.getByRole('progressbar').parentElement).toHaveClass('custom-class');
    });
  });
});

describe('getScoreVariant', () => {
  it('returns success for scores >= 70', () => {
    expect(getScoreVariant(70)).toBe('success');
    expect(getScoreVariant(85)).toBe('success');
    expect(getScoreVariant(100)).toBe('success');
  });

  it('returns warning for scores >= 40 and < 70', () => {
    expect(getScoreVariant(40)).toBe('warning');
    expect(getScoreVariant(55)).toBe('warning');
    expect(getScoreVariant(69)).toBe('warning');
  });

  it('returns danger for scores < 40', () => {
    expect(getScoreVariant(0)).toBe('danger');
    expect(getScoreVariant(20)).toBe('danger');
    expect(getScoreVariant(39)).toBe('danger');
  });
});
