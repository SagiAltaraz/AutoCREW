import { useState } from 'react';
import { createTask } from '../api/client';
import { useWebSocket } from '../hooks/useWebSocket';
import { AgentCard } from '../components/AgentCard';
import { TaskInput } from '../components/TaskInput';
import { ResultPanel } from '../components/ResultPanel';
import { MetricsBar } from '../components/MetricsBar';

export function Dashboard() {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const { agents, finalOutput, isConnected, totalTokens, totalDurationMs } = useWebSocket(taskId);

  const isRunning = isSubmitting || (taskId !== null && finalOutput === null);
  const doneCount = agents.filter(a => a.status === 'done').length;

  const handleSubmit = async (text: string) => {
    setError(null);
    setIsSubmitting(true);
    setTaskId(null);
    try {
      const { task_id } = await createTask(text);
      setTaskId(task_id);
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to create task');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#0A0E1A] text-white">
      {/* Header */}
      <header className="border-b border-gray-800 px-6 py-4 flex items-center justify-between">
        <div className="flex items-center gap-3">
          <span className="text-2xl font-bold font-mono text-[#00FF9D]">AutoCrew</span>
          <span className="text-xs text-gray-500 font-mono">Multi-Agent AI Platform</span>
        </div>
        <div className="flex items-center gap-2 text-xs font-mono">
          <span className={`w-2 h-2 rounded-full ${isConnected ? 'bg-[#00FF9D] animate-pulse' : 'bg-gray-600'}`} />
          <span className="text-gray-400">{isConnected ? 'Live' : 'Idle'}</span>
        </div>
      </header>

      <main className="max-w-6xl mx-auto px-6 py-8 flex gap-8">
        {/* LEFT — Input + Agents */}
        <div className="w-[40%] flex flex-col gap-6">
          <TaskInput onSubmit={handleSubmit} isLoading={isSubmitting} />

          {error && (
            <div className="text-red-400 text-sm font-mono border border-red-900 rounded-lg px-4 py-3 bg-red-950/30">
              {error}
            </div>
          )}

          <div className="space-y-3">
            {agents.map(agent => (
              <AgentCard
                key={agent.name}
                emoji={agent.emoji}
                label={agent.label}
                status={agent.status}
                tokensUsed={agent.tokensUsed}
                durationMs={agent.durationMs}
                preview={agent.preview}
              />
            ))}
          </div>

          {(totalTokens > 0 || isRunning) && (
            <MetricsBar
              totalTokens={totalTokens}
              totalDurationMs={totalDurationMs}
              agentCount={doneCount}
            />
          )}
        </div>

        {/* RIGHT — Result */}
        <div className="flex-1 bg-[#0d1117] rounded-2xl border border-gray-700/50 p-6 overflow-y-auto max-h-[calc(100vh-140px)]">
          <div className="flex items-center gap-2 mb-6">
            <span className="text-sm font-mono text-gray-400">Research Report</span>
            {isRunning && !finalOutput && (
              <span className="text-xs text-orange-400 font-mono animate-pulse">generating…</span>
            )}
          </div>
          <ResultPanel result={finalOutput} isLoading={isRunning} />
        </div>
      </main>
    </div>
  );
}
