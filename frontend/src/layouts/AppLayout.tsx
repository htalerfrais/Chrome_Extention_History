import { Routes, Route, Navigate } from 'react-router-dom';
import Sidebar from './Sidebar';
import ChatPanel from '../features/chat/ChatPanel';
import SessionView from '../features/sessions/SessionView';
import QuizView from '../features/quiz/QuizView';
import TrackingView from '../features/tracking/TrackingView';
import { useUIStore } from '../stores/useUIStore';

export default function AppLayout() {
  const isChatOpen = useUIStore((s) => s.isChatOpen);

  return (
    <div className="flex h-screen bg-bg text-text font-sans">
      {/* Left sidebar */}
      <div className="w-56 flex-shrink-0">
        <Sidebar />
      </div>

      {/* Central content */}
      <div className="flex-1 min-w-0 overflow-y-auto thin-scrollbar border-l border-line">
        <Routes>
          <Route path="/sessions" element={<SessionView />} />
          <Route path="/quiz" element={<QuizView />} />
          <Route path="/tracking" element={<TrackingView />} />
          <Route path="*" element={<Navigate to="/sessions" replace />} />
        </Routes>
      </div>

      {/* Right chat sidebar */}
      <div
        className={`flex-shrink-0 border-l border-line bg-bg-raised transition-all duration-200 ${
          isChatOpen ? 'w-[480px]' : 'w-12'
        }`}
      >
        <ChatPanel />
      </div>
    </div>
  );
}
