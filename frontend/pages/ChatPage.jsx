import React, { useState, useRef, useEffect } from 'react';
import { Send, Bot, User } from 'lucide-react';

const ChatPage = () => {
  // Generate or retrieve session ID
  const [sessionId] = useState(() => {
    // Try to get existing session ID from localStorage
    let storedSessionId = localStorage.getItem('chat_session_id');
    if (!storedSessionId) {
      // Generate new session ID
      storedSessionId = 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
      localStorage.setItem('chat_session_id', storedSessionId);
    }
    return storedSessionId;
  });

  const [messages, setMessages] = useState([
    {
      id: 1,
      type: 'assistant',
      content: 'Hello! I can help you analyze your YouTube analytics data. I\'ll remember our conversation, so feel free to ask follow-up questions. What would you like to know?',
      timestamp: new Date()
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);
  const inputRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      type: 'user',
      content: inputValue.trim(),
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          message: userMessage.content,
          csv_path: 'yt_analytics.csv', // Default CSV path
          session_id: sessionId
        }),
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();
      
      const assistantMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: data.response || 'Sorry, I couldn\'t process your request.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      
      const errorMessage = {
        id: Date.now() + 1,
        type: 'assistant',
        content: 'Sorry, there was an error processing your request. Please make sure the backend is running and try again. Your conversation history is preserved.',
        timestamp: new Date()
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
      inputRef.current?.focus();
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  const formatTime = (timestamp) => {
    return timestamp.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const clearSession = () => {
    // Clear session from localStorage and reset messages
    localStorage.removeItem('chat_session_id');
    setMessages([
      {
        id: 1,
        type: 'assistant',
        content: 'Hello! I can help you analyze your YouTube analytics data. I\'ll remember our conversation, so feel free to ask follow-up questions. What would you like to know?',
        timestamp: new Date()
      }
    ]);
    // Reload page to get new session ID
    window.location.reload();
  };

  return (
    <div className="flex flex-col h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-white border-b border-gray-200 px-4 py-3 shadow-sm">
        <div className="max-w-4xl mx-auto">
          <div className="flex items-center justify-between">
            <h1 className="text-xl font-semibold text-gray-800 flex items-center gap-2">
              <Bot className="w-6 h-6 text-blue-600" />
              YouTube Analytics Assistant
            </h1>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-500">
                Session: {sessionId.slice(-8)}
              </span>
              <button
                onClick={clearSession}
                className="text-sm text-gray-500 hover:text-red-600 transition-colors"
                title="Clear conversation history"
              >
                Clear Session
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Messages Container */}
      <div className="flex-1 overflow-y-auto px-4 py-6">
        <div className="max-w-4xl mx-auto space-y-6">
          {messages.map((message) => (
            <div
              key={message.id}
              className={`flex gap-3 ${
                message.type === 'user' ? 'justify-end' : 'justify-start'
              }`}
            >
              {message.type === 'assistant' && (
                <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                  <Bot className="w-5 h-5 text-white" />
                </div>
              )}
              
              <div
                className={`max-w-3xl rounded-2xl px-4 py-3 ${
                  message.type === 'user'
                    ? 'bg-blue-600 text-white ml-12'
                    : 'bg-white text-gray-800 shadow-sm border border-gray-200'
                }`}
              >
                <div className="whitespace-pre-wrap text-sm leading-relaxed">
                  {message.content}
                </div>
                <div
                  className={`text-xs mt-2 ${
                    message.type === 'user' ? 'text-blue-100' : 'text-gray-500'
                  }`}
                >
                  {formatTime(message.timestamp)}
                </div>
              </div>

              {message.type === 'user' && (
                <div className="flex-shrink-0 w-8 h-8 bg-gray-600 rounded-full flex items-center justify-center">
                  <User className="w-5 h-5 text-white" />
                </div>
              )}
            </div>
          ))}

          {/* Loading indicator */}
          {isLoading && (
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                <Bot className="w-5 h-5 text-white" />
              </div>
              <div className="bg-white rounded-2xl px-4 py-3 shadow-sm border border-gray-200">
                <div className="flex items-center gap-1">
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                  <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                </div>
              </div>
            </div>
          )}

          <div ref={messagesEndRef} />
        </div>
      </div>

      {/* Input Area */}
      <div className="bg-white border-t border-gray-200 px-4 py-4">
        <div className="max-w-4xl mx-auto">
          <form onSubmit={handleSubmit} className="relative">
            <div className="flex items-end gap-3">
              <div className="flex-1 relative">
                <textarea
                  ref={inputRef}
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  onKeyPress={handleKeyPress}
                  placeholder="Ask me about your YouTube analytics..."
                  className="w-full resize-none rounded-xl border border-gray-300 px-4 py-3 pr-12 focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 text-sm max-h-32 min-h-[48px]"
                  rows="1"
                  disabled={isLoading}
                  style={{
                    height: 'auto',
                    minHeight: '48px'
                  }}
                  onInput={(e) => {
                    e.target.style.height = 'auto';
                    e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px';
                  }}
                />
                <button
                  type="submit"
                  disabled={!inputValue.trim() || isLoading}
                  className="absolute right-2 bottom-2 p-2 text-gray-400 hover:text-blue-600 disabled:hover:text-gray-400 disabled:cursor-not-allowed transition-colors"
                >
                  <Send className="w-5 h-5" />
                </button>
              </div>
            </div>
          </form>
          
          {/* Helper text */}
          <div className="mt-2 text-xs text-gray-500 text-center">
            Press Enter to send, Shift+Enter for new line • Conversation history is preserved
          </div>
        </div>
      </div>
    </div>
  );
};

export default ChatPage;