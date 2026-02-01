/**
 * Tests for ChatPanel component.
 */

import { describe, it, expect, vi, beforeEach, beforeAll, afterEach } from 'vitest';
import { render, screen, waitFor, cleanup } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ChatPanel } from '../ChatPanel';

// Mock scrollIntoView - not supported by jsdom
beforeAll(() => {
  Element.prototype.scrollIntoView = vi.fn();
});

// Cleanup after each test to prevent state leaking
afterEach(() => {
  cleanup();
});

// Mock the useChatMutation hook
const mockMutateAsync = vi.fn();
const mockMutation = {
  mutateAsync: mockMutateAsync,
  isPending: false,
};

vi.mock('@/api/hooks', () => ({
  useChatMutation: () => mockMutation,
}));

// Create a wrapper with QueryClientProvider
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false },
      mutations: { retry: false },
    },
  });
  return ({ children }: { children: React.ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  );
}

describe('ChatPanel', () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mockMutation.isPending = false;
  });

  describe('Rendering', () => {
    it('renders nothing when closed', () => {
      const { container } = render(
        <ChatPanel isOpen={false} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );
      expect(container.firstChild).toBeNull();
    });

    it('renders panel when open', () => {
      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );
      expect(screen.getByText('Chat with AI')).toBeInTheDocument();
    });

    it('renders backdrop when open', () => {
      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );
      // Backdrop has bg-black/20 class
      const backdrop = document.querySelector('.bg-black\\/20');
      expect(backdrop).toBeInTheDocument();
    });

    it('displays job title in header when provided', () => {
      render(
        <ChatPanel
          isOpen={true}
          onClose={vi.fn()}
          jobTitle="Software Engineer"
        />,
        { wrapper: createWrapper() }
      );
      expect(screen.getByText(/About: Software Engineer/i)).toBeInTheDocument();
    });

    it('shows starter questions when no messages', () => {
      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );
      expect(screen.getByText("What are my strongest skills for this role?")).toBeInTheDocument();
      expect(screen.getByText("What skills should I prioritize learning?")).toBeInTheDocument();
    });
  });

  describe('Interactions', () => {
    it('calls onClose when backdrop is clicked', async () => {
      const onClose = vi.fn();
      render(
        <ChatPanel isOpen={true} onClose={onClose} />,
        { wrapper: createWrapper() }
      );

      const backdrop = document.querySelector('.bg-black\\/20');
      await userEvent.click(backdrop!);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('calls onClose when close button is clicked', async () => {
      const onClose = vi.fn();
      render(
        <ChatPanel isOpen={true} onClose={onClose} />,
        { wrapper: createWrapper() }
      );

      // Find close button by its container with hover:bg-blue-700
      const closeButtons = document.querySelectorAll('button');
      const closeButton = Array.from(closeButtons).find(
        (btn) => btn.querySelector('svg.lucide-x')
      );
      expect(closeButton).toBeTruthy();
      await userEvent.click(closeButton!);
      expect(onClose).toHaveBeenCalledTimes(1);
    });

    it('sends message when starter question is clicked', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'You have strong Python skills',
        suggestedQuestions: ['Follow-up question?'],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const starterQuestion = screen.getByText("What are my strongest skills for this role?");
      await userEvent.click(starterQuestion);

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          message: "What are my strongest skills for this role?",
          jobId: undefined,
        });
      });
    });

    it('sends message when input is submitted', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'Test response',
        suggestedQuestions: [],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'What skills am I missing?');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          message: 'What skills am I missing?',
          jobId: undefined,
        });
      });
    });

    it('sends message with jobId when provided', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'Test response',
        suggestedQuestions: [],
      });

      render(
        <ChatPanel
          isOpen={true}
          onClose={vi.fn()}
          jobId="job-123"
        />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'Test message');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledWith({
          message: 'Test message',
          jobId: 'job-123',
        });
      });
    });

    it('does not send empty messages', async () => {
      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.click(input);
      await userEvent.keyboard('{Enter}');

      expect(mockMutateAsync).not.toHaveBeenCalled();
    });

    it('clears input after sending message', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'Test response',
        suggestedQuestions: [],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'Test message');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(input).toHaveValue('');
      });
    });
  });

  describe('Messages', () => {
    it('displays user message after sending', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'AI response',
        suggestedQuestions: [],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'My question');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('My question')).toBeInTheDocument();
      });
    });

    it('displays AI response after receiving', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'You are a great match!',
        suggestedQuestions: [],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'Am I a good fit?');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('You are a great match!')).toBeInTheDocument();
      });
    });

    it('displays error message on API failure', async () => {
      mockMutateAsync.mockRejectedValue(new Error('API Error'));

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'Test');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText(/error processing your request/i)).toBeInTheDocument();
      });
    });

    it('applies correct styling to user messages', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'Response',
        suggestedQuestions: [],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'User message');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        const userMsg = screen.getByText('User message');
        // User messages are wrapped in p > div (the container)
        const container = userMsg.closest('div');
        expect(container).toHaveClass('bg-blue-600', 'text-white', 'ml-auto');
      });
    });

    it('applies correct styling to AI messages', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'AI response text',
        suggestedQuestions: [],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'Question');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        const aiMsg = screen.getByText('AI response text');
        // AI messages have MarkdownContent wrapper, so need to go up 2 levels
        // p > div.markdown-content > div (the container)
        const markdownWrapper = aiMsg.closest('.markdown-content');
        const container = markdownWrapper?.parentElement;
        expect(container).toHaveClass('bg-gray-100', 'mr-auto');
      });
    });
  });

  describe('Suggested Questions', () => {
    it('shows suggested follow-up questions after response', async () => {
      mockMutateAsync.mockResolvedValue({
        response: 'Initial response',
        suggestedQuestions: ['Follow-up 1?', 'Follow-up 2?'],
      });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'First question');
      await userEvent.keyboard('{Enter}');

      await waitFor(() => {
        expect(screen.getByText('Suggested:')).toBeInTheDocument();
        // Questions are truncated to 40 chars
        expect(screen.getByText('Follow-up 1?')).toBeInTheDocument();
      });
    });

    it('sends suggested question when clicked', async () => {
      mockMutateAsync
        .mockResolvedValueOnce({
          response: 'First response',
          suggestedQuestions: ['Follow-up question?'],
        })
        .mockResolvedValueOnce({
          response: 'Second response',
          suggestedQuestions: [],
        });

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      // Send first message
      const input = screen.getByPlaceholderText('Ask about your fit...');
      await userEvent.type(input, 'Initial');
      await userEvent.keyboard('{Enter}');

      // Wait for suggested questions to appear
      await waitFor(() => {
        expect(screen.getByText('Follow-up question?')).toBeInTheDocument();
      });

      // Click suggested question
      await userEvent.click(screen.getByText('Follow-up question?'));

      await waitFor(() => {
        expect(mockMutateAsync).toHaveBeenCalledTimes(2);
        expect(mockMutateAsync).toHaveBeenLastCalledWith({
          message: 'Follow-up question?',
          jobId: undefined,
        });
      });
    });
  });

  describe('Loading State', () => {
    it('disables input and shows loader when pending', () => {
      // Make the mutation pending
      mockMutation.isPending = true;

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      // Check that input is disabled during loading
      const input = screen.getByPlaceholderText('Ask about your fit...');
      expect(input).toBeDisabled();

      // Check that send button shows loader (has animate-spin class)
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];
      expect(sendButton.querySelector('.animate-spin')).toBeInTheDocument();
    });

    it('disables input while loading', async () => {
      mockMutation.isPending = true;

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      const input = screen.getByPlaceholderText('Ask about your fit...');
      expect(input).toBeDisabled();
    });

    it('disables send button while loading', async () => {
      mockMutation.isPending = true;

      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      // Find the send button (last button with role=button in the input area)
      const buttons = screen.getAllByRole('button');
      const sendButton = buttons[buttons.length - 1];
      expect(sendButton).toBeDisabled();
    });
  });

  describe('Accessibility', () => {
    it('focuses input when panel opens', async () => {
      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      await waitFor(() => {
        const input = screen.getByPlaceholderText('Ask about your fit...');
        expect(document.activeElement).toBe(input);
      }, { timeout: 200 });
    });

    it('has descriptive heading', () => {
      render(
        <ChatPanel isOpen={true} onClose={vi.fn()} />,
        { wrapper: createWrapper() }
      );

      expect(screen.getByRole('heading', { level: 2, name: /chat with ai/i })).toBeInTheDocument();
    });
  });
});
