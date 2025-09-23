// Header component for the dashboard
// Contains logo, title, and action buttons

interface HeaderProps {
  onRefresh: () => void;
  onSettings: () => void;
}

export default function Header({ onRefresh, onSettings }: HeaderProps) {
  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div className="logo-section">
          <img src="/icons/Engrave2.png" alt="Engrave it" className="logo" />
          <h1>Engrave it Dashboard</h1>
        </div>
        <div className="header-actions">
          <button className="btn btn-primary" onClick={onRefresh}>
            <span className="icon">🔄</span>
            Refresh Analysis
          </button>
          <button className="btn btn-secondary" onClick={onSettings}>
            <span className="icon">⚙️</span>
            Settings
          </button>
        </div>
      </div>
    </header>
  );
}
