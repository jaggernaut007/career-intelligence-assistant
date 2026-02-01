/**
 * Tests for Alert component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Alert } from '../Alert';

describe('Alert', () => {
  describe('Rendering', () => {
    it('renders children correctly', () => {
      render(<Alert>Alert message</Alert>);
      expect(screen.getByText('Alert message')).toBeInTheDocument();
    });

    it('has alert role', () => {
      render(<Alert>Message</Alert>);
      expect(screen.getByRole('alert')).toBeInTheDocument();
    });
  });

  describe('Title', () => {
    it('renders without title', () => {
      render(<Alert>No title</Alert>);
      expect(screen.getByText('No title')).toBeInTheDocument();
    });

    it('renders with title', () => {
      render(<Alert title="Error">Something went wrong</Alert>);
      expect(screen.getByText('Error')).toBeInTheDocument();
      expect(screen.getByText('Something went wrong')).toBeInTheDocument();
    });

    it('applies font-medium to title', () => {
      render(<Alert title="Title">Content</Alert>);
      expect(screen.getByText('Title')).toHaveClass('font-medium');
    });
  });

  describe('Variants', () => {
    it('renders info variant (default)', () => {
      render(<Alert variant="info">Info message</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-blue-50', 'border-blue-200', 'text-blue-800');
    });

    it('renders success variant', () => {
      render(<Alert variant="success">Success message</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-green-50', 'border-green-200', 'text-green-800');
    });

    it('renders warning variant', () => {
      render(<Alert variant="warning">Warning message</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-yellow-50', 'border-yellow-200', 'text-yellow-800');
    });

    it('renders error variant', () => {
      render(<Alert variant="error">Error message</Alert>);
      const alert = screen.getByRole('alert');
      expect(alert).toHaveClass('bg-red-50', 'border-red-200', 'text-red-800');
    });
  });

  describe('Icons', () => {
    it('renders info icon for info variant', () => {
      render(<Alert variant="info">Info</Alert>);
      const alert = screen.getByRole('alert');
      const icon = alert.querySelector('svg');
      expect(icon).toBeInTheDocument();
      expect(icon).toHaveClass('text-blue-500');
    });

    it('renders success icon for success variant', () => {
      render(<Alert variant="success">Success</Alert>);
      const alert = screen.getByRole('alert');
      const icon = alert.querySelector('svg');
      expect(icon).toHaveClass('text-green-500');
    });

    it('renders warning icon for warning variant', () => {
      render(<Alert variant="warning">Warning</Alert>);
      const alert = screen.getByRole('alert');
      const icon = alert.querySelector('svg');
      expect(icon).toHaveClass('text-yellow-500');
    });

    it('renders error icon for error variant', () => {
      render(<Alert variant="error">Error</Alert>);
      const alert = screen.getByRole('alert');
      const icon = alert.querySelector('svg');
      expect(icon).toHaveClass('text-red-500');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<Alert className="custom-class">Content</Alert>);
      expect(screen.getByRole('alert')).toHaveClass('custom-class');
    });
  });

  describe('HTML Attributes', () => {
    it('passes through HTML attributes', () => {
      render(<Alert data-testid="test-alert">Test</Alert>);
      expect(screen.getByTestId('test-alert')).toBeInTheDocument();
    });
  });
});
