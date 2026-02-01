/**
 * Tests for Card components.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Card, CardHeader, CardContent, CardFooter } from '../Card';

describe('Card', () => {
  describe('Rendering', () => {
    it('renders children correctly', () => {
      render(<Card>Card content</Card>);
      expect(screen.getByText('Card content')).toBeInTheDocument();
    });

    it('renders with default variant', () => {
      render(<Card>Default</Card>);
      // The Card renders children directly inside the styled div
      const card = screen.getByText('Default');
      expect(card).toHaveClass('bg-white');
      expect(card).toHaveClass('border');
      expect(card).toHaveClass('shadow-sm');
    });
  });

  describe('Variants', () => {
    it('renders default variant', () => {
      render(<Card variant="default">Default</Card>);
      expect(screen.getByText('Default')).toHaveClass('shadow-sm');
    });

    it('renders bordered variant', () => {
      render(<Card variant="bordered">Bordered</Card>);
      expect(screen.getByText('Bordered')).toHaveClass('border-2');
    });

    it('renders elevated variant', () => {
      render(<Card variant="elevated">Elevated</Card>);
      expect(screen.getByText('Elevated')).toHaveClass('shadow-lg');
    });
  });

  describe('Custom className', () => {
    it('applies custom className', () => {
      render(<Card className="custom-class">Custom</Card>);
      expect(screen.getByText('Custom')).toHaveClass('custom-class');
    });
  });

  describe('Ref forwarding', () => {
    it('forwards ref to div element', () => {
      const ref = vi.fn();
      render(<Card ref={ref}>Ref</Card>);
      expect(ref).toHaveBeenCalled();
    });
  });
});

describe('CardHeader', () => {
  it('renders children correctly', () => {
    render(<CardHeader>Header content</CardHeader>);
    expect(screen.getByText('Header content')).toBeInTheDocument();
  });

  it('has border bottom', () => {
    render(<CardHeader>Header</CardHeader>);
    expect(screen.getByText('Header')).toHaveClass('border-b');
  });

  it('has correct padding', () => {
    render(<CardHeader>Header</CardHeader>);
    expect(screen.getByText('Header')).toHaveClass('px-6', 'py-4');
  });

  it('applies custom className', () => {
    render(<CardHeader className="custom">Header</CardHeader>);
    expect(screen.getByText('Header')).toHaveClass('custom');
  });

  it('forwards ref', () => {
    const ref = vi.fn();
    render(<CardHeader ref={ref}>Header</CardHeader>);
    expect(ref).toHaveBeenCalled();
  });
});

describe('CardContent', () => {
  it('renders children correctly', () => {
    render(<CardContent>Content</CardContent>);
    expect(screen.getByText('Content')).toBeInTheDocument();
  });

  it('has correct padding', () => {
    render(<CardContent>Content</CardContent>);
    expect(screen.getByText('Content')).toHaveClass('px-6', 'py-4');
  });

  it('applies custom className', () => {
    render(<CardContent className="custom">Content</CardContent>);
    expect(screen.getByText('Content')).toHaveClass('custom');
  });

  it('forwards ref', () => {
    const ref = vi.fn();
    render(<CardContent ref={ref}>Content</CardContent>);
    expect(ref).toHaveBeenCalled();
  });
});

describe('CardFooter', () => {
  it('renders children correctly', () => {
    render(<CardFooter>Footer content</CardFooter>);
    expect(screen.getByText('Footer content')).toBeInTheDocument();
  });

  it('has border top', () => {
    render(<CardFooter>Footer</CardFooter>);
    expect(screen.getByText('Footer')).toHaveClass('border-t');
  });

  it('has correct padding', () => {
    render(<CardFooter>Footer</CardFooter>);
    expect(screen.getByText('Footer')).toHaveClass('px-6', 'py-4');
  });

  it('applies custom className', () => {
    render(<CardFooter className="custom">Footer</CardFooter>);
    expect(screen.getByText('Footer')).toHaveClass('custom');
  });

  it('forwards ref', () => {
    const ref = vi.fn();
    render(<CardFooter ref={ref}>Footer</CardFooter>);
    expect(ref).toHaveBeenCalled();
  });
});

describe('Card Composition', () => {
  it('composes all card parts correctly', () => {
    render(
      <Card>
        <CardHeader>Title</CardHeader>
        <CardContent>Body</CardContent>
        <CardFooter>Actions</CardFooter>
      </Card>
    );

    expect(screen.getByText('Title')).toBeInTheDocument();
    expect(screen.getByText('Body')).toBeInTheDocument();
    expect(screen.getByText('Actions')).toBeInTheDocument();
  });
});
