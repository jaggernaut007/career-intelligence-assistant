/**
 * Tests for Tabs components.
 */

import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '../Tabs';

describe('Tabs', () => {
  const renderTabs = (onChange?: (value: string) => void) => {
    return render(
      <Tabs defaultValue="tab1" onChange={onChange}>
        <TabsList>
          <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          <TabsTrigger value="tab2">Tab 2</TabsTrigger>
          <TabsTrigger value="tab3">Tab 3</TabsTrigger>
        </TabsList>
        <TabsContent value="tab1">Content 1</TabsContent>
        <TabsContent value="tab2">Content 2</TabsContent>
        <TabsContent value="tab3">Content 3</TabsContent>
      </Tabs>
    );
  };

  describe('Rendering', () => {
    it('renders all tab triggers', () => {
      renderTabs();
      expect(screen.getByRole('tab', { name: 'Tab 1' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Tab 2' })).toBeInTheDocument();
      expect(screen.getByRole('tab', { name: 'Tab 3' })).toBeInTheDocument();
    });

    it('renders tab list with tablist role', () => {
      renderTabs();
      expect(screen.getByRole('tablist')).toBeInTheDocument();
    });

    it('shows default tab content', () => {
      renderTabs();
      expect(screen.getByText('Content 1')).toBeInTheDocument();
      expect(screen.queryByText('Content 2')).not.toBeInTheDocument();
    });
  });

  describe('Tab Selection', () => {
    it('shows active tab as selected', () => {
      renderTabs();
      expect(screen.getByRole('tab', { name: 'Tab 1' })).toHaveAttribute('aria-selected', 'true');
      expect(screen.getByRole('tab', { name: 'Tab 2' })).toHaveAttribute('aria-selected', 'false');
    });

    it('changes content when tab is clicked', async () => {
      renderTabs();

      await userEvent.click(screen.getByRole('tab', { name: 'Tab 2' }));

      expect(screen.queryByText('Content 1')).not.toBeInTheDocument();
      expect(screen.getByText('Content 2')).toBeInTheDocument();
    });

    it('updates aria-selected when tab changes', async () => {
      renderTabs();

      await userEvent.click(screen.getByRole('tab', { name: 'Tab 2' }));

      expect(screen.getByRole('tab', { name: 'Tab 1' })).toHaveAttribute('aria-selected', 'false');
      expect(screen.getByRole('tab', { name: 'Tab 2' })).toHaveAttribute('aria-selected', 'true');
    });
  });

  describe('onChange callback', () => {
    it('calls onChange when tab is clicked', async () => {
      const onChange = vi.fn();
      renderTabs(onChange);

      await userEvent.click(screen.getByRole('tab', { name: 'Tab 2' }));

      expect(onChange).toHaveBeenCalledWith('tab2');
    });
  });

  describe('Accessibility', () => {
    it('has correct aria-controls on triggers', () => {
      renderTabs();
      expect(screen.getByRole('tab', { name: 'Tab 1' })).toHaveAttribute('aria-controls', 'panel-tab1');
      expect(screen.getByRole('tab', { name: 'Tab 2' })).toHaveAttribute('aria-controls', 'panel-tab2');
    });

    it('has correct id on triggers', () => {
      renderTabs();
      expect(screen.getByRole('tab', { name: 'Tab 1' })).toHaveAttribute('id', 'tab-tab1');
    });

    it('has correct aria-labelledby on content panels', () => {
      renderTabs();
      expect(screen.getByRole('tabpanel')).toHaveAttribute('aria-labelledby', 'tab-tab1');
    });

    it('content panel has correct id', () => {
      renderTabs();
      expect(screen.getByRole('tabpanel')).toHaveAttribute('id', 'panel-tab1');
    });
  });

  describe('Styling', () => {
    it('applies active styles to selected tab', () => {
      renderTabs();
      expect(screen.getByRole('tab', { name: 'Tab 1' })).toHaveClass('bg-white', 'shadow-sm');
    });

    it('applies inactive styles to unselected tabs', () => {
      renderTabs();
      expect(screen.getByRole('tab', { name: 'Tab 2' })).toHaveClass('text-gray-600');
    });
  });

  describe('Custom className', () => {
    it('applies custom className to Tabs container', () => {
      render(
        <Tabs defaultValue="tab1" className="custom-tabs">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      );
      expect(screen.getByRole('tablist').parentElement).toHaveClass('custom-tabs');
    });

    it('applies custom className to TabsList', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList className="custom-list">
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      );
      expect(screen.getByRole('tablist')).toHaveClass('custom-list');
    });

    it('applies custom className to TabsTrigger', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1" className="custom-trigger">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1">Content</TabsContent>
        </Tabs>
      );
      expect(screen.getByRole('tab')).toHaveClass('custom-trigger');
    });

    it('applies custom className to TabsContent', () => {
      render(
        <Tabs defaultValue="tab1">
          <TabsList>
            <TabsTrigger value="tab1">Tab 1</TabsTrigger>
          </TabsList>
          <TabsContent value="tab1" className="custom-content">Content</TabsContent>
        </Tabs>
      );
      expect(screen.getByRole('tabpanel')).toHaveClass('custom-content');
    });
  });
});

describe('TabsContext Error', () => {
  it('throws error when TabsTrigger is used outside Tabs', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TabsTrigger value="test">Test</TabsTrigger>);
    }).toThrow('Tabs components must be used within a Tabs provider');

    consoleError.mockRestore();
  });

  it('throws error when TabsContent is used outside Tabs', () => {
    const consoleError = vi.spyOn(console, 'error').mockImplementation(() => {});

    expect(() => {
      render(<TabsContent value="test">Content</TabsContent>);
    }).toThrow('Tabs components must be used within a Tabs provider');

    consoleError.mockRestore();
  });
});
