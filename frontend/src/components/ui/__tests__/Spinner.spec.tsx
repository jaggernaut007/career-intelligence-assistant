/**
 * Tests for Spinner and LoadingOverlay components.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Spinner, LoadingOverlay } from '../Spinner';

describe('Spinner', () => {
  describe('Rendering', () => {
    it('renders with loading label', () => {
      render(<Spinner />);
      expect(screen.getByLabelText('Loading')).toBeInTheDocument();
    });

    it('has spin animation', () => {
      render(<Spinner />);
      expect(screen.getByLabelText('Loading')).toHaveClass('animate-spin');
    });
  });

  describe('Sizes', () => {
    it('renders small size', () => {
      render(<Spinner size="sm" />);
      expect(screen.getByLabelText('Loading')).toHaveClass('h-4', 'w-4');
    });

    it('renders medium size (default)', () => {
      render(<Spinner size="md" />);
      expect(screen.getByLabelText('Loading')).toHaveClass('h-6', 'w-6');
    });

    it('renders large size', () => {
      render(<Spinner size="lg" />);
      expect(screen.getByLabelText('Loading')).toHaveClass('h-8', 'w-8');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<Spinner className="custom-class" />);
      expect(screen.getByLabelText('Loading')).toHaveClass('custom-class');
    });
  });

  describe('Default color', () => {
    it('has blue color by default', () => {
      render(<Spinner />);
      expect(screen.getByLabelText('Loading')).toHaveClass('text-blue-600');
    });
  });
});

describe('LoadingOverlay', () => {
  describe('Rendering', () => {
    it('renders with default message', () => {
      render(<LoadingOverlay />);
      expect(screen.getByText('Loading...')).toBeInTheDocument();
    });

    it('renders with custom message', () => {
      render(<LoadingOverlay message="Please wait..." />);
      expect(screen.getByText('Please wait...')).toBeInTheDocument();
    });

    it('includes a spinner', () => {
      render(<LoadingOverlay />);
      expect(screen.getByLabelText('Loading')).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('has overlay styling', () => {
      const { container } = render(<LoadingOverlay />);
      const overlay = container.firstChild;
      expect(overlay).toHaveClass('absolute', 'inset-0');
    });

    it('has centered content', () => {
      const { container } = render(<LoadingOverlay />);
      const overlay = container.firstChild;
      expect(overlay).toHaveClass('flex', 'items-center', 'justify-center');
    });

    it('has high z-index', () => {
      const { container } = render(<LoadingOverlay />);
      const overlay = container.firstChild;
      expect(overlay).toHaveClass('z-10');
    });
  });

  describe('Spinner size', () => {
    it('uses large spinner', () => {
      render(<LoadingOverlay />);
      expect(screen.getByLabelText('Loading')).toHaveClass('h-8', 'w-8');
    });
  });
});
