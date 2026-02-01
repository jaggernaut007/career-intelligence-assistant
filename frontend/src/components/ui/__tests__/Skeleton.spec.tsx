/**
 * Tests for Skeleton components.
 */

import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Skeleton, SkeletonCard, SkeletonList } from '../Skeleton';

describe('Skeleton', () => {
  describe('Rendering', () => {
    it('renders a div element', () => {
      const { container } = render(<Skeleton />);
      expect(container.firstChild?.nodeName).toBe('DIV');
    });

    it('has pulse animation', () => {
      const { container } = render(<Skeleton />);
      expect(container.firstChild).toHaveClass('animate-pulse');
    });

    it('has background color', () => {
      const { container } = render(<Skeleton />);
      expect(container.firstChild).toHaveClass('bg-gray-200');
    });

    it('has rounded corners', () => {
      const { container } = render(<Skeleton />);
      expect(container.firstChild).toHaveClass('rounded');
    });

    it('is hidden from accessibility tree', () => {
      const { container } = render(<Skeleton />);
      expect(container.firstChild).toHaveAttribute('aria-hidden', 'true');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      const { container } = render(<Skeleton className="h-10 w-full" />);
      expect(container.firstChild).toHaveClass('h-10', 'w-full');
    });
  });
});

describe('SkeletonCard', () => {
  describe('Rendering', () => {
    it('renders a card structure', () => {
      const { container } = render(<SkeletonCard />);
      expect(container.firstChild).toHaveClass('bg-white', 'rounded-xl', 'border');
    });

    it('contains multiple skeleton elements', () => {
      const { container } = render(<SkeletonCard />);
      const skeletons = container.querySelectorAll('.animate-pulse');
      expect(skeletons.length).toBeGreaterThan(0);
    });

    it('has avatar skeleton', () => {
      const { container } = render(<SkeletonCard />);
      const avatarSkeleton = container.querySelector('.rounded-full.h-12.w-12');
      expect(avatarSkeleton).toBeInTheDocument();
    });

    it('has text line skeletons', () => {
      const { container } = render(<SkeletonCard />);
      const textSkeletons = container.querySelectorAll('.h-4');
      expect(textSkeletons.length).toBeGreaterThan(0);
    });

    it('has badge skeletons', () => {
      const { container } = render(<SkeletonCard />);
      const badgeSkeletons = container.querySelectorAll('.h-6.rounded-full');
      expect(badgeSkeletons.length).toBe(3);
    });
  });
});

describe('SkeletonList', () => {
  describe('Rendering', () => {
    it('renders default 3 skeleton cards', () => {
      render(<SkeletonList />);
      const container = screen.getByTestId('results-skeleton');
      const cards = container.children;
      expect(cards.length).toBe(3);
    });

    it('renders custom count of skeleton cards', () => {
      render(<SkeletonList count={5} />);
      const container = screen.getByTestId('results-skeleton');
      const cards = container.children;
      expect(cards.length).toBe(5);
    });

    it('renders single skeleton card when count is 1', () => {
      render(<SkeletonList count={1} />);
      const container = screen.getByTestId('results-skeleton');
      const cards = container.children;
      expect(cards.length).toBe(1);
    });

    it('has test id for accessibility', () => {
      render(<SkeletonList />);
      expect(screen.getByTestId('results-skeleton')).toBeInTheDocument();
    });

    it('has spacing between cards', () => {
      render(<SkeletonList />);
      const container = screen.getByTestId('results-skeleton');
      expect(container).toHaveClass('space-y-4');
    });
  });
});
