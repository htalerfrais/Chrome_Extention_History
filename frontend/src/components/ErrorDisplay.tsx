import { AlertCircle } from 'lucide-react';

interface ErrorDisplayProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-4 py-16 text-white/60">
      <AlertCircle size={48} strokeWidth={1.5} />
      <h3 className="text-sm uppercase tracking-[0.3em]">Analysis Failed</h3>
      <p className="text-xs text-white/40 max-w-sm text-center">{message}</p>
      <button
        className="px-6 py-2 text-[10px] uppercase tracking-[0.3em] bg-white/10 text-white/80 hover:text-white hover:bg-white/15 transition-colors"
        onClick={onRetry}
      >
        Try Again
      </button>
    </div>
  );
}
