import { useState } from 'react';
import { ChevronDown, ChevronUp } from 'lucide-react';
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
    <div className={`flex animate-fade-in-up ${isUser ? 'justify-end' : 'justify-start'}`}>
      <div
        className={`max-w-[85%] space-y-2 rounded-xl px-4 py-3 ${
          isUser
            ? 'bg-accent text-white'
            : 'bg-bg-elevated text-text-secondary'
        }`}
      >
        <div className="text-sm leading-relaxed prose prose-invert prose-sm max-w-none">
          <ReactMarkdown>{message.content}</ReactMarkdown>
        </div>
        <span className="block text-xxs opacity-50">
          {formatTime(message.timestamp)}
        </span>

        {hasSources && (
          <div className="border border-line-strong rounded-lg overflow-hidden mt-2">
            <button
              type="button"
              className="w-full px-3 py-2 flex items-center justify-between text-xs text-text-tertiary bg-surface hover:bg-surface-hover transition-colors duration-150"
              onClick={() => setShowSources(prev => !prev)}
            >
              <span className="font-medium">Sources ({message.sources?.length})</span>
              {showSources ? <ChevronUp size={14} /> : <ChevronDown size={14} />}
            </button>

            {showSources && (
              <div className="max-h-48 overflow-y-auto divide-y divide-line thin-scrollbar">
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
                      className="block px-3 py-2.5 hover:bg-surface-hover transition-colors duration-150"
                    >
                      <div className="text-sm text-text">{title}</div>
                      <div className="text-xs text-text-tertiary mt-0.5">
                        {domain || source.url}
                      </div>
                      {dateLabel && (
                        <div className="text-xxs text-text-ghost mt-0.5">
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
