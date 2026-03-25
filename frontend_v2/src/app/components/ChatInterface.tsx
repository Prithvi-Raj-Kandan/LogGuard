import { useState, useRef, useEffect } from 'react';
import { ChatMessage } from '../types';
import { Send, Bot, User } from 'lucide-react';

interface ChatInterfaceProps {
  messages: ChatMessage[];
  onSendMessage: (message: string) => void;
  isProcessing: boolean;
}

export function ChatInterface({ messages, onSendMessage, isProcessing }: ChatInterfaceProps) {
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (input.trim() && !isProcessing) {
      onSendMessage(input);
      setInput('');
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      if (input.trim() && !isProcessing) {
        onSendMessage(input);
        setInput('');
      }
    }
  };

  return (
    <div className="flex flex-col h-full bg-[#0d0d0d] rounded-lg border border-[#2a2a2a] overflow-hidden">
      {/* Chat Header */}
      <div className="bg-[#1a1a1a] px-4 py-3 border-b border-[#2a2a2a]">
        <h3 className="text-[#e0e0e0] font-mono flex items-center gap-2">
          <Bot className="w-4 h-4 text-[#8b5cf6]" />
          Log Analyzer Assistant
        </h3>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full text-[#666] font-mono text-sm">
            <div className="text-center">
              <Bot className="w-12 h-12 mx-auto mb-4 opacity-50" />
              <p>Upload a log file to begin analysis</p>
              <p className="text-xs mt-2">Or ask me anything about log analysis</p>
            </div>
          </div>
        ) : (
          <>
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex gap-3 ${
                  message.role === 'user' ? 'justify-end' : 'justify-start'
                }`}
              >
                {message.role === 'assistant' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#8b5cf6] flex items-center justify-center">
                    <Bot className="w-5 h-5 text-white" />
                  </div>
                )}

                <div
                  className={`max-w-[80%] rounded-lg p-3 ${
                    message.role === 'user'
                      ? 'bg-[#8b5cf6] text-white'
                      : 'bg-[#1a1a1a] text-[#e0e0e0] border border-[#2a2a2a]'
                  }`}
                >
                  <p className="font-mono text-sm whitespace-pre-wrap">
                    {message.content}
                  </p>
                  <span className="text-xs opacity-50 mt-2 block font-mono">
                    {message.timestamp.toLocaleTimeString()}
                  </span>
                </div>

                {message.role === 'user' && (
                  <div className="flex-shrink-0 w-8 h-8 rounded-full bg-[#2a2a2a] flex items-center justify-center">
                    <User className="w-5 h-5 text-[#e0e0e0]" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input */}
      <form onSubmit={handleSubmit} className="border-t border-[#2a2a2a] p-4">
        <div className="flex gap-2">
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask about the log analysis..."
            disabled={isProcessing}
            rows={2}
            className="flex-1 resize-none bg-[#1a1a1a] text-[#e0e0e0] border border-[#2a2a2a] rounded-lg px-4 py-2 font-mono text-sm focus:outline-none focus:ring-2 focus:ring-[#8b5cf6] placeholder:text-[#666] disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={!input.trim() || isProcessing}
            className="px-4 py-2 bg-[#8b5cf6] text-white rounded-lg font-mono hover:bg-[#7c3aed] transition-colors disabled:opacity-50 disabled:cursor-not-allowed flex items-center gap-2"
          >
            {isProcessing ? (
              <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
            ) : (
              <Send className="w-4 h-4" />
            )}
          </button>
        </div>
      </form>
    </div>
  );
}
