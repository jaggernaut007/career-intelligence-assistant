import { useEffect, useRef, useCallback } from 'react';
import { useWizardStore } from '@/store';
import { DEFAULT_API_CONFIG, type AgentStatusUpdate } from '@/types/specs';

interface UseWebSocketOptions {
  sessionId: string | null;
  enabled?: boolean;
  onComplete?: () => void;
}

const MAX_RECONNECT_ATTEMPTS = 5;
const RECONNECT_BASE_DELAY_MS = 1000;
const WS_NORMAL_CLOSURE = 1000;

export function useWebSocket({ sessionId, enabled = true, onComplete }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const isConnectingRef = useRef(false);
  const reconnectAttemptsRef = useRef(0);
  const reconnectTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // Store callbacks in refs to avoid dependency changes causing reconnects
  const onCompleteRef = useRef(onComplete);
  onCompleteRef.current = onComplete;

  // Get stable store selectors
  const updateAgentStatus = useWizardStore((s) => s.updateAgentStatus);
  const setAnalyzing = useWizardStore((s) => s.setAnalyzing);
  const setError = useWizardStore((s) => s.setError);

  const connect = useCallback(() => {
    // Avoid multiple simultaneous connections
    if (!sessionId || !enabled) return;
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    if (wsRef.current?.readyState === WebSocket.CONNECTING) return;
    if (isConnectingRef.current) return;

    isConnectingRef.current = true;

    const wsUrl = `${DEFAULT_API_CONFIG.wsUrl}/ws/progress/${sessionId}`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      console.log('WebSocket connected');
      isConnectingRef.current = false;
      reconnectAttemptsRef.current = 0;
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        // Handle agent progress updates (backend sends 'agent_update')
        if (data.type === 'agent_update') {
          const update: AgentStatusUpdate = {
            agentName: data.agent_name,
            status: data.status,
            progress: data.progress || 0,
            currentStep: data.current_step,
            error: data.error,
          };
          updateAgentStatus(update);
        }

        // Handle analysis completion
        if (data.type === 'analysis_complete') {
          setAnalyzing(false);
          if (data.success) {
            onCompleteRef.current?.();
          } else if (data.error) {
            setError(data.error);
          }
        }

        if (data.type === 'error') {
          setError(data.message);
          setAnalyzing(false);
        }
      } catch (err) {
        console.error('WebSocket message parse error:', err);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      isConnectingRef.current = false;
    };

    ws.onclose = (event) => {
      console.log('WebSocket closed', event.code, event.reason);
      isConnectingRef.current = false;
      wsRef.current = null;

      // Attempt reconnection with exponential backoff (skip on intentional close)
      if (enabled && sessionId && event.code !== WS_NORMAL_CLOSURE && reconnectAttemptsRef.current < MAX_RECONNECT_ATTEMPTS) {
        const delay = RECONNECT_BASE_DELAY_MS * Math.pow(2, reconnectAttemptsRef.current);
        reconnectAttemptsRef.current += 1;
        console.log(
          `WebSocket reconnecting in ${delay}ms (attempt ${reconnectAttemptsRef.current}/${MAX_RECONNECT_ATTEMPTS})`
        );
        reconnectTimerRef.current = setTimeout(() => {
          connect();
        }, delay);
      }
    };

    wsRef.current = ws;

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close(WS_NORMAL_CLOSURE, 'Component unmounted');
      }
    };
  // Only reconnect when sessionId or enabled changes, not on callback changes
  }, [sessionId, enabled, updateAgentStatus, setAnalyzing, setError]);

  useEffect(() => {
    reconnectAttemptsRef.current = 0;
    const cleanup = connect();
    return () => {
      // Cancel any pending reconnect timer
      if (reconnectTimerRef.current !== null) {
        clearTimeout(reconnectTimerRef.current);
        reconnectTimerRef.current = null;
      }
      cleanup?.();
    };
  }, [connect]);

  const disconnect = useCallback(() => {
    // Cancel any pending reconnect and prevent new reconnects
    if (reconnectTimerRef.current !== null) {
      clearTimeout(reconnectTimerRef.current);
      reconnectTimerRef.current = null;
    }
    reconnectAttemptsRef.current = MAX_RECONNECT_ATTEMPTS; // prevent further reconnects
    if (wsRef.current) {
      wsRef.current.close(WS_NORMAL_CLOSURE, 'Intentional disconnect');
      wsRef.current = null;
    }
    isConnectingRef.current = false;
  }, []);

  return { disconnect };
}
