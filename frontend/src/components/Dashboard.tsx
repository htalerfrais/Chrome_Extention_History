// Dashboard component - main content area
// This will contain the sessions tabs and clusters section

interface DashboardProps {
  currentSessionResults: any;
  activeSessionId: string | null;
  onSessionChange: (sessionId: string) => void;
}

export default function Dashboard({ currentSessionResults, activeSessionId, onSessionChange }: DashboardProps) {
  // Suppress unused parameter warnings for now - these will be used when we implement the dashboard content
  console.log('Dashboard props:', { currentSessionResults, activeSessionId, onSessionChange });
  
  return (
    <div className="dashboard-content">
      {/* Dashboard content will go here */}
      <p>Dashboard content will be implemented here</p>
    </div>
  );
}
