import { useEffect, useState } from 'react';

interface Props {
  totalTokens: number;
  totalDurationMs: number;
  agentCount: number;
}

function AnimatedNumber({ value }: { value: number }) {
  const [display, setDisplay] = useState(0);

  useEffect(() => {
    if (value === 0) { setDisplay(0); return; }
    const steps = 20;
    const increment = value / steps;
    let current = 0;
    const timer = setInterval(() => {
      current += increment;
      if (current >= value) { setDisplay(value); clearInterval(timer); }
      else setDisplay(Math.floor(current));
    }, 30);
    return () => clearInterval(timer);
  }, [value]);

  return <>{display.toLocaleString()}</>;
}

export function MetricsBar({ totalTokens, totalDurationMs, agentCount }: Props) {
  return (
    <div className="flex gap-6 px-4 py-3 bg-[#0d1117] border border-gray-700/50 rounded-xl font-mono text-sm">
      <div className="flex flex-col items-center">
        <span className="text-gray-500 text-xs">Tokens</span>
        <span className="text-[#00FF9D] font-semibold">
          <AnimatedNumber value={totalTokens} />
        </span>
      </div>
      <div className="w-px bg-gray-700" />
      <div className="flex flex-col items-center">
        <span className="text-gray-500 text-xs">Duration</span>
        <span className="text-[#00FF9D] font-semibold">
          {totalDurationMs > 0 ? `${(totalDurationMs / 1000).toFixed(1)}s` : '—'}
        </span>
      </div>
      <div className="w-px bg-gray-700" />
      <div className="flex flex-col items-center">
        <span className="text-gray-500 text-xs">Agents</span>
        <span className="text-[#00FF9D] font-semibold">{agentCount}</span>
      </div>
    </div>
  );
}
