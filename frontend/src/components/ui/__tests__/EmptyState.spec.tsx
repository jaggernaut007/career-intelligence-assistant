/**
 * Tests for EmptyState component.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { EmptyState } from '../EmptyState';

describe('EmptyState', () => {
  describe('Rendering', () => {
    it('renders title', () => {
      render(<EmptyState title="No results" />);
      expect(screen.getByText('No results')).toBeInTheDocument();
    });

    it('renders title as heading', () => {
      render(<EmptyState title="No data" />);
      expect(screen.getByRole('heading', { name: 'No data' })).toBeInTheDocument();
    });
  });

  describe('Description', () => {
    it('does not render description when not provided', () => {
      render(<EmptyState title="Empty" />);
      const description = screen.queryByText(/./);
      expect(screen.getByText('Empty')).toBeInTheDocument();
    });

    it('renders description when provided', () => {
      render(<EmptyState title="No items" description="Try adding some items" />);
      expect(screen.getByText('Try adding some items')).toBeInTheDocument();
    });
  });

  describe('Icon', () => {
    it('renders default icon when not provided', () => {
      const { container } = render(<EmptyState title="Empty" />);
      const icon = container.querySelector('svg');
      expect(icon).toBeInTheDocument();
    });

    it('renders custom icon when provided', () => {
      const CustomIcon = () => <svg data-testid="custom-icon" />;
      render(<EmptyState title="Empty" icon={<CustomIcon />} />);
      expect(screen.getByTestId('custom-icon')).toBeInTheDocument();
    });
  });

  describe('Action', () => {
    it('does not render action when not provided', () => {
      render(<EmptyState title="Empty" />);
      expect(screen.queryByRole('button')).not.toBeInTheDocument();
    });

    it('renders action when provided', () => {
      render(
        <EmptyState
          title="No results"
          action={<button>Add new</button>}
        />
      );
      expect(screen.getByRole('button', { name: 'Add new' })).toBeInTheDocument();
    });
  });

  describe('Styling', () => {
    it('centers content', () => {
      const { container } = render(<EmptyState title="Empty" />);
      expect(container.firstChild).toHaveClass('flex', 'flex-col', 'items-center', 'justify-center');
    });

    it('has text center alignment', () => {
      const { container } = render(<EmptyState title="Empty" />);
      expect(container.firstChild).toHaveClass('text-center');
    });

    it('has vertical padding', () => {
      const { container } = render(<EmptyState title="Empty" />);
      expect(container.firstChild).toHaveClass('py-12');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(<EmptyState title="Empty" className="custom-class" />);
      expect(container.firstChild).toHaveClass('custom-class');
    });
  });

  describe('Title styling', () => {
    it('title has proper styling', () => {
      render(<EmptyState title="No items" />);
      expect(screen.getByRole('heading')).toHaveClass('text-lg', 'font-medium', 'text-gray-900');
    });
  });

  describe('Description styling', () => {
    it('description has proper styling', () => {
      render(<EmptyState title="Empty" description="Some description" />);
      expect(screen.getByText('Some description')).toHaveClass('text-sm', 'text-gray-500');
    });

    it('description has max width', () => {
      render(<EmptyState title="Empty" description="Some description" />);
      expect(screen.getByText('Some description')).toHaveClass('max-w-sm');
    });
  });

  describe('Complete EmptyState', () => {
    it('renders all parts together', () => {
      const CustomIcon = () => <svg data-testid="icon" />;
      render(
        <EmptyState
          icon={<CustomIcon />}
          title="No results found"
          description="Try adjusting your search"
          action={<button>Clear filters</button>}
        />
      );

      expect(screen.getByTestId('icon')).toBeInTheDocument();
      expect(screen.getByText('No results found')).toBeInTheDocument();
      expect(screen.getByText('Try adjusting your search')).toBeInTheDocument();
      expect(screen.getByRole('button', { name: 'Clear filters' })).toBeInTheDocument();
    });
  });
});
