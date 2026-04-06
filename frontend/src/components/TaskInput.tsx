import { useState } from 'react';

const EXAMPLES = [
  'Research Tesla Q4 2024 performance',
  'Analyze the AI chip market in 2025',
  'Compare top 5 cloud providers',
];

interface Props {
  onSubmit: (text: string) => void;
  isLoading: boolean;
}

export function TaskInput({ onSubmit, isLoading }: Props) {
  const [text, setText] = useState('');

  const handleSubmit = () => {
    if (text.trim() && !isLoading) {
      onSubmit(text.trim());
    }
  };

  return (
    <div className="space-y-3">
      <textarea
        value={text}
        onChange={e => setText(e.target.value)}
        onKeyDown={e => e.key === 'Enter' && e.metaKey && handleSubmit()}
        placeholder="What do you want AutoCrew to research?"
        rows={4}
        className="w-full bg-[#0d1117] border border-gray-700 rounded-xl p-4 text-white placeholder-gray-500 font-mono text-sm resize-none focus:outline-none focus:border-[#00FF9D] transition-colors"
        disabled={isLoading}
      />

      <button
        onClick={handleSubmit}
        disabled={!text.trim() || isLoading}
        className="w-full py-3 rounded-xl font-semibold text-sm transition-all duration-200 disabled:opacity-40 disabled:cursor-not-allowed bg-[#00FF9D] text-black hover:brightness-110 active:scale-[0.98]"
      >
        {isLoading ? (
          <span className="flex items-center justify-center gap-2">
            <svg className="animate-spin h-4 w-4" viewBox="0 0 24 24" fill="none">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
            </svg>
            Launching Crew…
          </span>
        ) : (
          'Launch Crew 🚀'
        )}
      </button>

      <div className="flex flex-wrap gap-2">
        {EXAMPLES.map(ex => (
          <button
            key={ex}
            onClick={() => setText(ex)}
            disabled={isLoading}
            className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:border-[#00FF9D] hover:text-[#00FF9D] transition-colors disabled:opacity-40"
          >
            {ex}
          </button>
        ))}
      </div>
    </div>
  );
}
