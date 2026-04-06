import ReactMarkdown from 'react-markdown';

interface Props {
  result: string | null;
  isLoading: boolean;
}

export function ResultPanel({ result, isLoading }: Props) {
  const handleCopy = () => {
    if (result) navigator.clipboard.writeText(result);
  };

  const handleDownload = () => {
    if (!result) return;
    const blob = new Blob([result], { type: 'text/plain' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = 'autocrew-report.txt';
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading && !result) {
    return (
      <div className="space-y-3 animate-pulse">
        {[...Array(6)].map((_, i) => (
          <div key={i} className={`h-4 rounded bg-gray-800 ${i % 3 === 0 ? 'w-3/4' : 'w-full'}`} />
        ))}
      </div>
    );
  }

  if (!result) {
    return (
      <div className="flex flex-col items-center justify-center h-64 text-gray-600">
        <span className="text-5xl mb-3">📋</span>
        <p className="font-mono text-sm">Report will appear here</p>
      </div>
    );
  }

  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button
          onClick={handleCopy}
          className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:border-[#00FF9D] hover:text-[#00FF9D] transition-colors"
        >
          📋 Copy
        </button>
        <button
          onClick={handleDownload}
          className="text-xs px-3 py-1.5 rounded-lg border border-gray-700 text-gray-400 hover:border-[#00FF9D] hover:text-[#00FF9D] transition-colors"
        >
          ⬇️ Download
        </button>
      </div>
      <div className="prose prose-invert prose-sm max-w-none">
        <ReactMarkdown>{result}</ReactMarkdown>
      </div>
    </div>
  );
}
