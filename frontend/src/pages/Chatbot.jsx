import React, { useState, useEffect, useRef } from 'react';
import { aiService } from '../services/ai';
import { Loader } from '../components/Common/Loader';
import { Sparkles, Send, Bot, User, ArrowRight } from 'lucide-react';
import './Chatbot.css';

export const Chatbot = () => {
  const [messages, setMessages] = useState([]);
  const [inputMsg, setInputMsg] = useState('');
  const [historyLoading, setHistoryLoading] = useState(true);
  const [isTyping, setIsTyping] = useState(false);
  const messagesEndRef = useRef(null);

  // Suggestions/FAQ Pills
  const suggestions = [
    "How do I file a grievance?",
    "Hostel mess timings & wardens",
    "What are the library hours?",
    "How to reopen a grievance?"
  ];

  const fetchChatHistory = async () => {
    try {
      const res = await aiService.getChatHistory();
      if (res.success) {
        setMessages(res.data.map(chat => ({
          id: chat.id,
          sender: chat.sender === 'user' ? 'user' : 'bot',
          text: chat.message,
          timestamp: chat.created_at
        })));
      }
    } catch (e) {
      console.error('Failed to load chat history:', e);
    } finally {
      setHistoryLoading(false);
    }
  };

  useEffect(() => {
    fetchChatHistory();
  }, []);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages, isTyping]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputMsg;
    if (!text.trim()) return;

    if (!textToSend) setInputMsg('');

    // Append user message immediately
    const userMsg = {
      id: Date.now(),
      sender: 'user',
      text: text,
      timestamp: new Date().toISOString()
    };
    
    setMessages((prev) => [...prev, userMsg]);
    setIsTyping(true);

    try {
      const res = await aiService.sendChatMessage(text);
      if (res.success) {
        setMessages((prev) => [
          ...prev, 
          {
            id: Date.now() + 1,
            sender: 'bot',
            text: res.data.bot_response,
            timestamp: new Date().toISOString(),
            engine: res.data.engine
          }
        ]);
      }
    } catch (e) {
      setMessages((prev) => [
        ...prev,
        {
          id: Date.now() + 1,
          sender: 'bot',
          text: "I apologize, but I am facing connectivity issues right now. Please try again in a few moments.",
          timestamp: new Date().toISOString()
        }
      ]);
    } finally {
      setIsTyping(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter') {
      handleSendMessage();
    }
  };

  return (
    <div className="chatbot-page-container animate-fade-in">
      <div className="chat-grid-layout">
        {/* Left Info Panel */}
        <div className="chat-info-panel glass-card">
          <div className="info-header">
            <Bot size={32} className="bot-logo-icon" />
            <h2>NBKR Assist</h2>
            <span className="online-badge">Online</span>
          </div>

          <p className="bot-intro">Your personal campus concierge. Ask me anything about university facilities, guidelines, timing lists, or grievance procedures.</p>
          
          <div className="capabilities-list">
            <h4>I can assist you with:</h4>
            <ul>
              <li><ArrowRight size={14} /> Hostel mess schedules & warden numbers</li>
              <li><ArrowRight size={14} /> Library operating hours & renewal policies</li>
              <li><ArrowRight size={14} /> College bus routes & schedules</li>
              <li><ArrowRight size={14} /> Guiding you to file support grievances</li>
              <li><ArrowRight size={14} /> Checking status of active tickets</li>
            </ul>
          </div>

          <div className="bot-engine-label">
            <Sparkles size={14} className="sparkle-gold" />
            <span>Campus Concierge Desk</span>
          </div>

          <div style={{ marginTop: 'auto', paddingTop: '16px', borderTop: '1px solid var(--border-color)', textAlign: 'center', fontSize: '0.82rem', color: 'var(--text-muted)' }}>
            Made with pride by <strong style={{ color: 'var(--color-primary)' }}>BALAJI NAGELLA</strong>
          </div>
        </div>

        {/* Right Chat Terminal */}
        <div className="chat-terminal-panel glass-card">
          <div className="chat-history-container">
            {historyLoading ? (
              <Loader message="Restoring conversation log..." />
            ) : messages.length === 0 ? (
              <div className="chat-empty-state">
                <Bot size={48} className="empty-bot-icon" />
                <h3>Welcome to NBKR Assist</h3>
                <p>Ask a question or select one of the suggestions below to start our conversation.</p>
                
                <div className="suggestions-grid">
                  {suggestions.map((sug, i) => (
                    <button 
                      key={i} 
                      onClick={() => handleSendMessage(sug)}
                      className="suggestion-pill"
                    >
                      {sug}
                    </button>
                  ))}
                </div>
              </div>
            ) : (
              <div className="messages-list">
                {messages.map((msg) => (
                  <div key={msg.id} className={`message-wrapper ${msg.sender}`}>
                    <div className="message-avatar">
                      {msg.sender === 'user' ? <User size={16} /> : <Bot size={16} />}
                    </div>
                    <div className="message-bubble-container">
                      <div className="message-bubble">
                        <p>{msg.text}</p>
                      </div>
                      <div className="message-meta">
                        <span>{new Date(msg.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}</span>
                        {msg.engine && <span className="meta-engine">{msg.engine.replace(/\bAI\b/gi, 'Assistant').replace(/gemini/gi, 'Campus Knowledge')}</span>}
                      </div>
                    </div>
                  </div>
                ))}
                
                {isTyping && (
                  <div className="message-wrapper bot">
                    <div className="message-avatar">
                      <Bot size={16} />
                    </div>
                    <div className="message-bubble-container">
                      <div className="message-bubble typing-bubble">
                        <div className="typing-dots">
                          <span></span>
                          <span></span>
                          <span></span>
                        </div>
                      </div>
                    </div>
                  </div>
                )}
                
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>

          {/* Quick FAQ Suggestion Bar when active */}
          {messages.length > 0 && (
            <div className="quick-suggestions-bar">
              {suggestions.map((sug, i) => (
                <button 
                  key={i} 
                  onClick={() => handleSendMessage(sug)}
                  className="quick-suggestion-pill"
                  disabled={isTyping}
                >
                  {sug}
                </button>
              ))}
            </div>
          )}

          {/* Text Input Footer */}
          <div className="chat-input-bar">
            <input 
              type="text" 
              placeholder="Type your campus concern here..."
              value={inputMsg}
              onChange={(e) => setInputMsg(e.target.value)}
              onKeyDown={handleKeyPress}
              disabled={isTyping}
              className="form-input chat-input"
            />
            <button 
              onClick={() => handleSendMessage()} 
              disabled={!inputMsg.trim() || isTyping}
              className="btn btn-primary send-msg-btn"
              aria-label="Send message"
            >
              <Send size={18} />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
};
export default Chatbot;
