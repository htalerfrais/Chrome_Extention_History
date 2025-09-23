// SessionInfo component - displays session metadata
// Shows duration, time range, and topic count for the current session

interface SessionData {
  session_start_time: string;
  session_end_time: string;
  clusters: any[];
}

interface SessionInfoProps {
  sessionData: SessionData | null;
}

export default function SessionInfo({ sessionData }: SessionInfoProps) {
  if (!sessionData) {
    return null;
  }

  const startTime = new Date(sessionData.session_start_time);
  const endTime = new Date(sessionData.session_end_time);
  const duration = Math.round((endTime.getTime() - startTime.getTime()) / (1000 * 60)); // minutes
  const clusterCount = sessionData.clusters?.length || 0;

  return (
    <div className="session-info">
      <div className="session-info-item">
        <strong>Duration:</strong> {duration} minutes
      </div>
      <div className="session-info-item">
        <strong>Time:</strong> {startTime.toLocaleString()} - {endTime.toLocaleString()}
      </div>
      <div className="session-info-item">
        <strong>Topics:</strong> {clusterCount}
      </div>
    </div>
  );
}
