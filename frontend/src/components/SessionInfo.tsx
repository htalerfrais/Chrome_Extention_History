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
  const dateLabel = startTime.toLocaleDateString();
  const startLabel = startTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  const endLabel = endTime.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  return (
    <div className="flex flex-wrap items-center gap-3 text-[10px] uppercase tracking-[0.25em] text-white/40">
      <span>{dateLabel}</span>
      <span>{startLabel}&nbsp;→&nbsp;{endLabel}</span>
      <span>{duration} min</span>
      <span>{clusterCount} topics</span>
    </div>
  );
}
