import { useState, useRef, useEffect } from 'react';
import { X, Send, MessageCircle, Loader2 } from 'lucide-react';
import { Button } from '@/components/ui/Button';
import { useChatMutation } from '@/api/hooks';
import type { ChatMessage } from '@/types/specs';
import { cn } from '@/utils/cn';
import { MarkdownContent } from '@/utils/markdown';

interface ChatPanelProps {
  isOpen: boolean;
  onClose: () => void;
  jobId?: string;
  jobTitle?: string;
}

const STARTER_QUESTIONS = [
  "What are my strongest skills for this role?",
  "What skills should I prioritize learning?",
  "Which of these jobs is the best fit for me?",
  "How should I prepare for an interview?",
];

export function ChatPanel({ isOpen, onClose, jobId, jobTitle }: ChatPanelProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [inputValue, setInputValue] = useState('');
  const [suggestedQuestions, setSuggestedQuestions] = useState<string[]>(STARTER_QUESTIONS);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  const chatMutation = useChatMutation();

  // Scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Focus input when panel opens
  useEffect(() => {
    if (isOpen) {
      setTimeout(() => inputRef.current?.focus(), 100);
    }
  }, [isOpen]);

  const handleSendMessage = async (message: string) => {
    if (!message.trim() || chatMutation.isPending) return;

    // Add user message
    const userMessage: ChatMessage = {
      id: `user-${Date.now()}`,
      role: 'user',
      content: message.trim(),
      timestamp: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, userMessage]);
    setInputValue('');

    try {
      const response = await chatMutation.mutateAsync({
        message: message.trim(),
        jobId,
      });

      // Add AI response
      const assistantMessage: ChatMessage = {
        id: `assistant-${Date.now()}`,
        role: 'assistant',
        content: response.response,
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, assistantMessage]);

      // Update suggested questions
      if (response.suggestedQuestions?.length > 0) {
        setSuggestedQuestions(response.suggestedQuestions);
      }
    } catch (error) {
      // Add error message
      const errorMessage: ChatMessage = {
        id: `error-${Date.now()}`,
        role: 'assistant',
        content: 'Sorry, I encountered an error processing your request. Please try again.',
        timestamp: new Date().toISOString(),
      };
      setMessages((prev) => [...prev, errorMessage]);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage(inputValue);
    }
  };

  const handleQuestionClick = (question: string) => {
    handleSendMessage(question);
  };

  if (!isOpen) return null;

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 bg-black/20 z-40 transition-opacity"
        onClick={onClose}
      />

      {/* Panel */}
      <div className="fixed right-0 top-0 h-full w-full sm:w-[420px] bg-white shadow-2xl z-50 flex flex-col animate-slide-in-right">
        {/* Header */}
        <div className="flex items-center justify-between px-4 py-3 border-b bg-blue-600 text-white">
          <div className="flex items-center gap-2">
            <MessageCircle className="w-5 h-5" />
            <div>
              <h2 className="font-semibold">Chat with AI</h2>
              {jobTitle && (
                <p className="text-xs text-blue-100 truncate max-w-[250px]">
                  About: {jobTitle}
                </p>
              )}
            </div>
          </div>
          <button
            onClick={onClose}
            className="p-1 hover:bg-blue-700 rounded transition-colors"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Messages */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="text-center py-8">
              <MessageCircle className="w-12 h-12 mx-auto text-gray-300 mb-4" />
              <p className="text-gray-500 mb-4">
                Ask me anything about your resume-job fit!
              </p>
              <p className="text-sm text-gray-400 mb-6">
                Try one of these questions:
              </p>
              <div className="space-y-2">
                {STARTER_QUESTIONS.map((question, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuestionClick(question)}
                    className="block w-full text-left px-3 py-2 text-sm bg-gray-50 hover:bg-blue-50 hover:text-blue-600 rounded-lg transition-colors border border-gray-200"
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <>
              {messages.map((msg) => (
                <div
                  key={msg.id}
                  className={cn(
                    'max-w-[85%] rounded-lg px-4 py-2',
                    msg.role === 'user'
                      ? 'ml-auto bg-blue-600 text-white'
                      : 'mr-auto bg-gray-100 text-gray-800'
                  )}
                >
                  {msg.role === 'user' ? (
                    <p className="text-sm whitespace-pre-wrap">{msg.content}</p>
                  ) : (
                    <MarkdownContent content={msg.content} className="text-sm" />
                  )}
                </div>
              ))}

              {chatMutation.isPending && (
                <div className="text-gray-500">
                  <div className="flex items-center gap-2">
                    <Loader2 className="w-4 h-4 animate-spin" />
                    <span className="text-sm">Thinking...</span>
                  </div>
                  <p className="text-xs text-gray-400 ml-6 mt-1">
                    Usually takes 15-30 seconds
                  </p>
                </div>
              )}

              {/* Suggested questions after conversation starts */}
              {messages.length > 0 && !chatMutation.isPending && suggestedQuestions.length > 0 && (
                <div className="pt-2">
                  <p className="text-xs text-gray-400 mb-2">Suggested:</p>
                  <div className="flex flex-wrap gap-2">
                    {suggestedQuestions.slice(0, 3).map((question, idx) => (
                      <button
                        key={idx}
                        onClick={() => handleQuestionClick(question)}
                        className="text-xs px-2 py-1 bg-gray-50 hover:bg-blue-50 hover:text-blue-600 rounded border border-gray-200 transition-colors truncate max-w-full"
                        title={question}
                      >
                        {question.length > 40 ? question.slice(0, 40) + '...' : question}
                      </button>
                    ))}
                  </div>
                </div>
              )}

              <div ref={messagesEndRef} />
            </>
          )}
        </div>

        {/* Input */}
        <div className="border-t p-4 bg-gray-50">
          <div className="flex gap-2">
            <input
              ref={inputRef}
              type="text"
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask about your fit..."
              className="flex-1 px-4 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              disabled={chatMutation.isPending}
            />
            <Button
              onClick={() => handleSendMessage(inputValue)}
              disabled={!inputValue.trim() || chatMutation.isPending}
              size="md"
            >
              {chatMutation.isPending ? (
                <Loader2 className="w-4 h-4 animate-spin" />
              ) : (
                <Send className="w-4 h-4" />
              )}
            </Button>
          </div>
        </div>
      </div>
    </>
  );
}
