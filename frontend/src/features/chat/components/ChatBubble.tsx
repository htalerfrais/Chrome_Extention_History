import { useState } from 'react';
import ReactMarkdown from 'react-markdown';
import type { ChatMessage } from '../../../types/chat';

interface ChatBubbleProps {
  message: ChatMessage;
}

export default function ChatBubble({ message }: ChatBubbleProps) {
  const isUser = message.role === 'user';
  const hasSources = message.role === 'assistant' && (message.sources?.length || 0) > 0;
  const [showSources, setShowSources] = useState(false);
  
  const formatTime = (timestamp: Date): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString('en-US', { 
      hour: '2-digit', 
      minute: '2-digit' 
    });
  };

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div className={`max-w-[85%] space-y-2 ${isUser ? 'text-white' : 'text-white/70'}`}>
        <div className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        <span className="block text-[10px] uppercase tracking-[0.25em] text-white/40">
          {formatTime(message.timestamp)}
        </span>

        {hasSources && (
          <div className="border border-white/10 rounded-md overflow-hidden">
            <button
              type="button"
              className="w-full px-3 py-2 flex items-center justify-between text-xs uppercase tracking-widest text-white/70 bg-white/5 hover:bg-white/10 transition"
              onClick={() => setShowSources(prev => !prev)}
            >
              <span>Sources</span>
              <span className="text-white/50">{showSources ? 'Hide' : 'Show'}</span>
            </button>

            {showSources && (
              <div className="max-h-48 overflow-y-auto divide-y divide-white/5 bg-white/5">
                {message.sources?.map((source, idx) => {
                  const title = source.title || 'Untitled';
                  const domain =
                    source.url_hostname ||
                    (() => {
                      try {
                        return new URL(source.url).hostname;
                      } catch {
                        return '';
                      }
                    })();
                  const dateLabel = source.visit_time
                    ? new Date(source.visit_time).toLocaleDateString()
                    : '';

                  return (
                    <a
                      key={`${idx}-${source.url}`}
                      href={source.url}
                      target="_blank"
                      rel="noreferrer"
                      className="block px-3 py-2 hover:bg-white/10 transition"
                    >
                      <div className="text-sm text-white">{title}</div>
                      <div className="text-xs text-white/60">
                        {domain || source.url}
                      </div>
                      {dateLabel && (
                        <div className="text-[11px] text-white/50">
                          Visited: {dateLabel}
                        </div>
                      )}
                    </a>
                  );
                })}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
