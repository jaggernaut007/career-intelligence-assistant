import { useEffect, useRef, useCallback } from 'react';
import { useWizardStore } from '@/store';
import { DEFAULT_API_CONFIG, type AgentStatusUpdate } from '@/types/specs';

interface UseWebSocketOptions {
  sessionId: string | null;
  enabled?: boolean;
  onComplete?: () => void;
}

export function useWebSocket({ sessionId, enabled = true, onComplete }: UseWebSocketOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const isConnectingRef = useRef(false);

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

    ws.onclose = () => {
      console.log('WebSocket closed');
      isConnectingRef.current = false;
      wsRef.current = null;
    };

    wsRef.current = ws;

    return () => {
      if (ws.readyState === WebSocket.OPEN || ws.readyState === WebSocket.CONNECTING) {
        ws.close();
      }
    };
  // Only reconnect when sessionId or enabled changes, not on callback changes
  }, [sessionId, enabled, updateAgentStatus, setAnalyzing, setError]);

  useEffect(() => {
    const cleanup = connect();
    return cleanup;
  }, [connect]);

  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    isConnectingRef.current = false;
  }, []);

  return { disconnect };
}
