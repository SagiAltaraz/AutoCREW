import { useEffect, useRef, useState, useCallback } from 'react';
import { AgentInfo, AgentStatus, WsEvent } from '../types';

const AGENT_DEFAULTS: AgentInfo[] = [
  { name: 'manager', label: 'Manager', emoji: '🧠', status: 'waiting', tokensUsed: 0, durationMs: 0, preview: '' },
  { name: 'research', label: 'Research', emoji: '🔍', status: 'waiting', tokensUsed: 0, durationMs: 0, preview: '' },
  { name: 'analyst', label: 'Analyst', emoji: '📊', status: 'waiting', tokensUsed: 0, durationMs: 0, preview: '' },
  { name: 'writer', label: 'Writer', emoji: '✍️', status: 'waiting', tokensUsed: 0, durationMs: 0, preview: '' },
];

export function useWebSocket(taskId: string | null) {
  const [agents, setAgents] = useState<AgentInfo[]>(AGENT_DEFAULTS);
  const [finalOutput, setFinalOutput] = useState<string | null>(null);
  const [isConnected, setIsConnected] = useState(false);
  const [totalTokens, setTotalTokens] = useState(0);
  const [totalDurationMs, setTotalDurationMs] = useState(0);
  const wsRef = useRef<WebSocket | null>(null);
  const retriesRef = useRef(0);

  const reset = useCallback(() => {
    setAgents(AGENT_DEFAULTS.map(a => ({ ...a })));
    setFinalOutput(null);
    setTotalTokens(0);
    setTotalDurationMs(0);
  }, []);

  useEffect(() => {
    if (!taskId) return;

    reset();
    retriesRef.current = 0;

    function connect() {
      const ws = new WebSocket(`ws://localhost:8000/ws/${taskId}`);
      wsRef.current = ws;

      ws.onopen = () => setIsConnected(true);

      ws.onmessage = (event) => {
        const data: WsEvent = JSON.parse(event.data);

        if (data.type === 'agent_update') {
          setAgents(prev =>
            prev.map(a =>
              a.name === data.agent
                ? {
                    ...a,
                    status: data.status as AgentStatus,
                    tokensUsed: data.tokens_used,
                    durationMs: data.duration_ms,
                    preview: data.preview,
                  }
                : a
            )
          );
        } else if (data.type === 'task_complete') {
          setFinalOutput(data.output);
          setTotalTokens(data.total_tokens);
          setTotalDurationMs(data.duration_ms);
        }
      };

      ws.onclose = () => {
        setIsConnected(false);
        if (retriesRef.current < 3) {
          retriesRef.current++;
          setTimeout(connect, 1500 * retriesRef.current);
        }
      };

      ws.onerror = () => ws.close();
    }

    connect();

    return () => {
      wsRef.current?.close();
      setIsConnected(false);
    };
  }, [taskId, reset]);

  return { agents, finalOutput, isConnected, totalTokens, totalDurationMs };
}
