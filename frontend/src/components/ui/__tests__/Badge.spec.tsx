/**
 * Tests for Badge component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Badge } from '../Badge';

describe('Badge', () => {
  describe('Rendering', () => {
    it('renders children correctly', () => {
      render(<Badge>New</Badge>);
      expect(screen.getByText('New')).toBeInTheDocument();
    });

    it('renders with default props', () => {
      render(<Badge>Default</Badge>);
      const badge = screen.getByText('Default');
      expect(badge).toHaveClass('bg-gray-100'); // default variant
      expect(badge).toHaveClass('rounded-full');
    });
  });

  describe('Variants', () => {
    it('renders default variant', () => {
      render(<Badge variant="default">Default</Badge>);
      expect(screen.getByText('Default')).toHaveClass('bg-gray-100', 'text-gray-800');
    });

    it('renders success variant', () => {
      render(<Badge variant="success">Success</Badge>);
      expect(screen.getByText('Success')).toHaveClass('bg-green-100', 'text-green-800');
    });

    it('renders warning variant', () => {
      render(<Badge variant="warning">Warning</Badge>);
      expect(screen.getByText('Warning')).toHaveClass('bg-yellow-100', 'text-yellow-800');
    });

    it('renders danger variant', () => {
      render(<Badge variant="danger">Danger</Badge>);
      expect(screen.getByText('Danger')).toHaveClass('bg-red-100', 'text-red-800');
    });

    it('renders info variant', () => {
      render(<Badge variant="info">Info</Badge>);
      expect(screen.getByText('Info')).toHaveClass('bg-blue-100', 'text-blue-800');
    });

    it('renders outline variant', () => {
      render(<Badge variant="outline">Outline</Badge>);
      expect(screen.getByText('Outline')).toHaveClass('border', 'bg-transparent');
    });
  });

  describe('Sizes', () => {
    it('renders small size', () => {
      render(<Badge size="sm">Small</Badge>);
      expect(screen.getByText('Small')).toHaveClass('px-2', 'py-0.5');
    });

    it('renders medium size', () => {
      render(<Badge size="md">Medium</Badge>);
      expect(screen.getByText('Medium')).toHaveClass('px-2.5', 'py-1');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<Badge className="custom-class">Custom</Badge>);
      expect(screen.getByText('Custom')).toHaveClass('custom-class');
    });
  });

  describe('HTML Attributes', () => {
    it('passes through HTML attributes', () => {
      render(<Badge data-testid="test-badge">Test</Badge>);
      expect(screen.getByTestId('test-badge')).toBeInTheDocument();
    });
  });
});
