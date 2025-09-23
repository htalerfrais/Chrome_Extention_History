// ErrorDisplay component for showing error states
// This will display error messages and retry button

interface ErrorDisplayProps {
  message: string;
  onRetry: () => void;
}

export default function ErrorDisplay({ message, onRetry }: ErrorDisplayProps) {
  return (
    <div className="error-container">
      <div className="error-icon">❌</div>
      <h3>Analysis Failed</h3>
      <p>{message}</p>
      <button className="btn btn-primary" onClick={onRetry}>
        Try Again
      </button>
    </div>
  );
}
