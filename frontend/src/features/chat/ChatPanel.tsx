import { MessageSquare, PanelRightClose } from 'lucide-react';
import ChatWindow from './components/ChatWindow';
import { useUIStore } from '../../stores/useUIStore';

export default function ChatPanel() {
  const isChatOpen = useUIStore((s) => s.isChatOpen);
  const toggleChat = useUIStore((s) => s.toggleChat);

  if (!isChatOpen) {
    return (
      <div className="flex flex-col items-center py-4">
        <button
          onClick={toggleChat}
          className="p-2 rounded-lg text-text-tertiary hover:text-accent hover:bg-accent-subtle transition-colors duration-150"
          title="Open chat"
        >
          <MessageSquare size={18} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-5 py-4 border-b border-line flex items-center justify-between">
        <h2 className="text-sm font-semibold tracking-wide text-text">Chat</h2>
        <button
          onClick={toggleChat}
          className="p-1.5 rounded-lg text-text-tertiary hover:text-text-secondary hover:bg-surface transition-colors duration-150"
          title="Hide chat"
        >
          <PanelRightClose size={16} />
        </button>
      </div>
      <div className="flex-1 min-h-0">
        <ChatWindow />
      </div>
    </div>
  );
}
