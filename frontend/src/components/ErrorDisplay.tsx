import { AlertCircle, RotateCcw } from 'lucide-react';

interface ErrorDisplayProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="flex flex-col items-center justify-center gap-5 py-20">
      <div className="p-4 rounded-full bg-error/10">
        <AlertCircle size={32} strokeWidth={1.5} className="text-error" />
      </div>
      <div className="text-center space-y-2">
        <h3 className="text-sm font-semibold text-text">Something went wrong</h3>
        <p className="text-xs text-text-tertiary max-w-sm">{message}</p>
      </div>
      <button
        className="flex items-center gap-2 px-5 py-2.5 text-xs font-medium rounded-lg bg-surface hover:bg-surface-hover text-text-secondary hover:text-text transition-colors duration-150"
        onClick={onRetry}
      >
        <RotateCcw size={14} />
        Try Again
      </button>
    </div>
  );
}
