// Header component for the dashboard
// Contains logo, title, navigation controls, and action buttons

interface HeaderProps {
  onSettings: () => void;
  onPreviousSession: () => void;
  onNextSession: () => void;
  currentSessionIndex: number;
  totalSessions: number;
  canGoPrevious: boolean;
  canGoNext: boolean;
}

export default function Header({ 
  onSettings, 
  onPreviousSession, 
  onNextSession, 
  currentSessionIndex, 
  totalSessions, 
  canGoPrevious, 
  canGoNext 
}: HeaderProps) {
  return (
    <header className="dashboard-header">
      <div className="header-content">
        <div className="logo-section">
          <img src="/icons/Engrave2.png" alt="Engrave it" className="logo" />
          <h1>Engrave it Dashboard</h1>
        </div>
        
        {/* Session Navigation */}
        {totalSessions > 0 && (
          <div className="session-navigation">
            <button 
              className="btn btn-nav" 
              onClick={onPreviousSession}
              disabled={!canGoPrevious}
              title="Previous Session"
            >
              <span className="icon">←</span>
            </button>
            <span className="session-counter">
              Session {currentSessionIndex + 1} of {totalSessions}
            </span>
            <button 
              className="btn btn-nav" 
              onClick={onNextSession}
              disabled={!canGoNext}
              title="Next Session"
            >
              <span className="icon">→</span>
            </button>
          </div>
        )}
        
        <div className="header-actions">
          <button className="btn btn-secondary" onClick={onSettings}>
            <span className="icon">⚙️</span>
            Settings
          </button>
        </div>
      </div>
    </header>
  );
}
