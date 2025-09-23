// LoadingSpinner component for showing loading state
// This will display a spinner and loading message

export default function LoadingSpinner() {
  return (
    <div className="loading-container">
      <div className="loading-spinner" />
      <p className="status-text">Analyzing session...</p>
    </div>
  );
}
