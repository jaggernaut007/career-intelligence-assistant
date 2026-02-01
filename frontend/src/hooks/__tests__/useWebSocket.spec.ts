/**
 * Tests for useWebSocket hook.
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useWebSocket } from '../useWebSocket';

// Create stable mock functions that persist across calls
const mockUpdateAgentStatus = vi.fn();
const mockSetAnalyzing = vi.fn();
const mockSetError = vi.fn();

// Mock the wizard store with stable references
vi.mock('@/store', () => ({
  useWizardStore: vi.fn((selector) => {
    const state = {
      updateAgentStatus: mockUpdateAgentStatus,
      setAnalyzing: mockSetAnalyzing,
      setError: mockSetError,
    };
    return selector(state);
  }),
}));

describe('useWebSocket', () => {
  let mockWebSocket: {
    onopen: ((event: Event) => void) | null;
    onmessage: ((event: MessageEvent) => void) | null;
    onerror: ((event: Event) => void) | null;
    onclose: ((event: CloseEvent) => void) | null;
    send: ReturnType<typeof vi.fn>;
    close: ReturnType<typeof vi.fn>;
    addEventListener: ReturnType<typeof vi.fn>;
    removeEventListener: ReturnType<typeof vi.fn>;
    readyState: number;
  };

  beforeEach(() => {
    mockWebSocket = {
      onopen: null,
      onmessage: null,
      onerror: null,
      onclose: null,
      send: vi.fn(),
      close: vi.fn(),
      addEventListener: vi.fn(),
      removeEventListener: vi.fn(),
      readyState: WebSocket.CONNECTING,
    };

    const MockWebSocket = vi.fn(() => mockWebSocket) as unknown as typeof WebSocket;
    // Preserve WebSocket constants
    MockWebSocket.CONNECTING = 0;
    MockWebSocket.OPEN = 1;
    MockWebSocket.CLOSING = 2;
    MockWebSocket.CLOSED = 3;
    global.WebSocket = MockWebSocket;
    vi.spyOn(console, 'log').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});

    // Reset store mocks
    mockUpdateAgentStatus.mockClear();
    mockSetAnalyzing.mockClear();
    mockSetError.mockClear();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  describe('Connection', () => {
    it('creates WebSocket connection when sessionId is provided', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      expect(global.WebSocket).toHaveBeenCalledWith(
        expect.stringContaining('test-session')
      );
    });

    it('does not create connection when sessionId is null', () => {
      renderHook(() => useWebSocket({ sessionId: null }));

      expect(global.WebSocket).not.toHaveBeenCalled();
    });

    it('does not create connection when enabled is false', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session', enabled: false }));

      expect(global.WebSocket).not.toHaveBeenCalled();
    });

    it('logs on successful connection', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      act(() => {
        mockWebSocket.onopen?.(new Event('open'));
      });

      expect(console.log).toHaveBeenCalledWith('WebSocket connected');
    });
  });

  describe('Message Handling', () => {
    it('handles agent_update messages', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      const message = {
        type: 'agent_update',
        agent_name: 'resume_parser',
        status: 'running',
        progress: 50,
        current_step: 'Parsing skills',
      };

      act(() => {
        mockWebSocket.onmessage?.(new MessageEvent('message', {
          data: JSON.stringify(message),
        }));
      });

      expect(mockUpdateAgentStatus).toHaveBeenCalledWith({
        agentName: 'resume_parser',
        status: 'running',
        progress: 50,
        currentStep: 'Parsing skills',
        error: undefined,
      });
    });

    it('handles analysis_complete success messages', () => {
      const onComplete = vi.fn();

      renderHook(() => useWebSocket({
        sessionId: 'test-session',
        onComplete,
      }));

      const message = {
        type: 'analysis_complete',
        success: true,
      };

      act(() => {
        mockWebSocket.onmessage?.(new MessageEvent('message', {
          data: JSON.stringify(message),
        }));
      });

      expect(mockSetAnalyzing).toHaveBeenCalledWith(false);
      expect(onComplete).toHaveBeenCalled();
    });

    it('handles analysis_complete error messages', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      const message = {
        type: 'analysis_complete',
        success: false,
        error: 'Analysis failed',
      };

      act(() => {
        mockWebSocket.onmessage?.(new MessageEvent('message', {
          data: JSON.stringify(message),
        }));
      });

      expect(mockSetAnalyzing).toHaveBeenCalledWith(false);
      expect(mockSetError).toHaveBeenCalledWith('Analysis failed');
    });

    it('handles error messages', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      const message = {
        type: 'error',
        message: 'Something went wrong',
      };

      act(() => {
        mockWebSocket.onmessage?.(new MessageEvent('message', {
          data: JSON.stringify(message),
        }));
      });

      expect(mockSetError).toHaveBeenCalledWith('Something went wrong');
      expect(mockSetAnalyzing).toHaveBeenCalledWith(false);
    });

    it('handles JSON parse errors gracefully', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      act(() => {
        mockWebSocket.onmessage?.(new MessageEvent('message', {
          data: 'invalid json',
        }));
      });

      expect(console.error).toHaveBeenCalledWith(
        'WebSocket message parse error:',
        expect.any(Error)
      );
    });
  });

  describe('Error Handling', () => {
    it('logs WebSocket errors', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      act(() => {
        mockWebSocket.onerror?.(new Event('error'));
      });

      expect(console.error).toHaveBeenCalledWith('WebSocket error:', expect.any(Event));
    });
  });

  describe('Disconnection', () => {
    it('logs on close', () => {
      renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      act(() => {
        mockWebSocket.onclose?.(new CloseEvent('close'));
      });

      expect(console.log).toHaveBeenCalledWith('WebSocket closed');
    });

    it('returns disconnect function', () => {
      const { result } = renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      expect(typeof result.current.disconnect).toBe('function');
    });

    it('disconnect closes the WebSocket', () => {
      const { result } = renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      act(() => {
        result.current.disconnect();
      });

      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });

  describe('Cleanup', () => {
    it('closes WebSocket on unmount', () => {
      const { unmount } = renderHook(() => useWebSocket({ sessionId: 'test-session' }));

      unmount();

      expect(mockWebSocket.close).toHaveBeenCalled();
    });
  });
});
