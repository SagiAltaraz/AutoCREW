export type AgentStatus = 'waiting' | 'running' | 'done' | 'error';

export interface AgentUpdate {
  type: 'agent_update';
  agent: string;
  status: AgentStatus;
  timestamp: number;
  tokens_used: number;
  duration_ms: number;
  preview: string;
}

export interface TaskCompleteEvent {
  type: 'task_complete';
  output: string;
  duration_ms: number;
  total_tokens: number;
}

export type WsEvent = AgentUpdate | TaskCompleteEvent;

export interface AgentRun {
  agent_name: string;
  status: AgentStatus;
  duration_ms?: number;
  tokens_used?: number;
  output?: string;
}

export interface Task {
  id: string;
  input_text: string;
  status: string;
  created_at: string;
  completed_at?: string;
  agent_runs?: AgentRun[];
  result?: string;
}

export interface AgentInfo {
  name: string;
  label: string;
  emoji: string;
  status: AgentStatus;
  tokensUsed: number;
  durationMs: number;
  preview: string;
}
