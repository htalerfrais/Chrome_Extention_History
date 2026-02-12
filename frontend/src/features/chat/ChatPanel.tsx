import { MessageSquare } from 'lucide-react';
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
          className="p-2 text-white/50 hover:text-white transition-colors"
          title="Open chat"
        >
          <MessageSquare size={20} />
        </button>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <div className="px-4 py-3 border-b border-white/10 flex items-center justify-between">
        <h2 className="text-sm uppercase tracking-widest text-white">Chat</h2>
        <button
          onClick={toggleChat}
          className="text-white/50 hover:text-white text-xs uppercase tracking-widest transition-colors"
        >
          Hide
        </button>
      </div>
      <div className="flex-1 min-h-0">
        <ChatWindow />
      </div>
    </div>
  );
}
