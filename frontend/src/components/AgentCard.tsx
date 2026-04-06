import { AgentStatus } from '../types';

interface Props {
  emoji: string;
  label: string;
  status: AgentStatus;
  tokensUsed: number;
  durationMs: number;
  preview: string;
}

const STATUS_CONFIG = {
  waiting:  { badge: 'text-gray-400 bg-gray-800',   dot: 'bg-gray-500',   label: 'Waiting'  },
  running:  { badge: 'text-orange-300 bg-orange-900/40', dot: 'bg-orange-400 animate-pulse', label: 'Running' },
  done:     { badge: 'text-green-400 bg-green-900/40',  dot: 'bg-green-400',  label: 'Done'    },
  error:    { badge: 'text-red-400 bg-red-900/40',   dot: 'bg-red-400',    label: 'Error'   },
};

export function AgentCard({ emoji, label, status, tokensUsed, durationMs, preview }: Props) {
  const cfg = STATUS_CONFIG[status];
  const isRunning = status === 'running';

  return (
    <div
      className={`rounded-xl border p-4 transition-all duration-300 ${
        isRunning
          ? 'border-orange-500 shadow-[0_0_15px_rgba(249,115,22,0.3)]'
          : 'border-gray-700/50'
      } bg-[#0d1117]`}
    >
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">{emoji}</span>
          <span className="font-mono font-semibold text-white">{label}</span>
        </div>
        <span className={`flex items-center gap-1.5 text-xs px-2 py-1 rounded-full font-medium ${cfg.badge}`}>
          <span className={`w-1.5 h-1.5 rounded-full ${cfg.dot}`} />
          {cfg.label}
        </span>
      </div>

      {isRunning && (
        <div className="mb-3 h-1 w-full bg-gray-800 rounded-full overflow-hidden">
          <div className="h-full bg-orange-500 rounded-full animate-[indeterminate_1.5s_ease-in-out_infinite]" style={{ width: '40%' }} />
        </div>
      )}

      {preview && status !== 'waiting' && (
        <p className="text-xs text-gray-400 font-mono leading-relaxed mb-3 line-clamp-2">
          {preview.slice(0, 100)}{preview.length > 100 ? '…' : ''}
        </p>
      )}

      {(tokensUsed > 0 || durationMs > 0) && (
        <div className="flex gap-4 text-xs text-gray-500 font-mono border-t border-gray-800 pt-2">
          {tokensUsed > 0 && <span>{tokensUsed.toLocaleString()} tokens</span>}
          {durationMs > 0 && <span>{(durationMs / 1000).toFixed(1)}s</span>}
        </div>
      )}
    </div>
  );
}
