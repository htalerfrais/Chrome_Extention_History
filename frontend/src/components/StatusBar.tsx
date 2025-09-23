// StatusBar component for showing loading/success/error states
// This will display the current status of the analysis

interface StatusBarProps {
  status: string;
  statusType: 'loading' | 'success' | 'error';
}

export default function StatusBar({ status, statusType }: StatusBarProps) {
  return (
    <div className="status-bar">
      <div className="status-content">
        <span className="status-text">{status}</span>
        <div className={`status-indicator ${statusType}`}></div>
      </div>
    </div>
  );
}
