'use client';
import { useState, useRef, useEffect } from 'react';
import Image from 'next/image';

export default function CosmereArchivistChat() {
  const [messages, setMessages] = useState([
    {
      id: 1,
      text: "Greetings, seeker of knowledge. I am the CosmereArchivist, keeper of the ancient archives. What wisdom do you seek from the depths of the Cosmere?",
      isBot: true,
      timestamp: null // No timestamp for the initial message to avoid hydration issues
    }
  ]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(scrollToBottom, [messages]);

  const sendMessage = async () => {
    if (!inputValue.trim() || isLoading) return;

    const userMessage = {
      id: Date.now(),
      text: inputValue,
      isBot: false,
      timestamp: new Date()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setIsLoading(true);

    try {
      const response = await fetch('https://loreGpt.onrender.com/ask', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ question: inputValue }),
      });

      if (!response.ok) {
        throw new Error('Failed to get response');
      }

      const data = await response.json();
      
      const botMessage = {
        id: Date.now() + 1,
        text: data.answer,
        isBot: true,
        timestamp: new Date()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error) {
      const errorMessage = {
        id: Date.now() + 1,
        text: "Forgive me, the connection to the archive seems to be severed. Please ensure the keeper's server is awakened.",
        isBot: true,
        timestamp: new Date()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  };

  return (
    <div className="h-screen flex flex-col">
      {/* Header */}
      <header className="bg-gradient-to-r from-amber-900/20 to-yellow-600/20 border-b-2 border-copper p-6 flex-shrink-0">
        <div className="max-w-4xl mx-auto flex items-center justify-center">
          <div className="flex items-center space-x-4">
            <div className="text-center">
              <h1 className="text-4xl font-bold text-gold glow-text" style={{fontFamily: 'var(--font-uncial)'}}>
                ⚬ CosmereArchivist ⚬
              </h1>
              <p className="text-bronze mt-2 text-lg">
                Archive of the Shards
              </p>
            </div>
          </div>
        </div>
      </header>

      {/* Chat Container */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto w-full p-4 min-h-0">
        {/* Messages Area */}
        <div className="flex-1 overflow-y-auto mb-4 ancient-border rounded-lg p-4 parchment-bg">
          <div className="space-y-4">
            {messages.map((message) => (
              <div
                key={message.id}
                className={`flex ${message.isBot ? 'justify-start' : 'justify-end'}`}
              >
                <div
                  className={`max-w-xs lg:max-w-md px-4 py-3 rounded-lg ${
                    message.isBot
                      ? 'bg-gradient-to-r from-amber-900/30 to-yellow-700/30 text-parchment border border-bronze'
                      : 'bg-gradient-to-r from-amber-600/40 to-yellow-500/40 text-white border border-gold'
                  }`}
                >
                  {message.isBot && (
                    <div className="flex items-center mb-2">
                      <span className="text-gold text-sm font-bold">⚬ CosmereArchivist ⚬</span>
                    </div>
                  )}
                  <p className="text-sm lg:text-base leading-relaxed whitespace-pre-wrap">
                    {message.text}
                  </p>
                  {message.timestamp && (
                    <div className="text-xs opacity-70 mt-2">
                      {message.timestamp.toLocaleTimeString()}
                    </div>
                  )}
                </div>
              </div>
            ))}
            
            {isLoading && (
              <div className="flex justify-start">
                <div className="max-w-xs lg:max-w-md px-4 py-3 rounded-lg bg-gradient-to-r from-amber-900/30 to-yellow-700/30 text-parchment border border-bronze">
                  <div className="flex items-center mb-2">
                    <span className="text-gold text-sm font-bold">⚬ CosmereArchivist ⚬</span>
                  </div>
                  <div className="flex items-center space-x-2">
                    <div className="flex space-x-1">
                      <div className="w-2 h-2 bg-gold rounded-full animate-pulse"></div>
                      <div className="w-2 h-2 bg-gold rounded-full animate-pulse" style={{animationDelay: '0.2s'}}></div>
                      <div className="w-2 h-2 bg-gold rounded-full animate-pulse" style={{animationDelay: '0.4s'}}></div>
                    </div>
                    <span className="text-sm text-bronze">Consulting the archives...</span>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        </div>

        {/* Input Area */}
        <div className="border-2 border-copper rounded-lg p-4 bg-gradient-to-r from-amber-900/10 to-yellow-600/10 flex-shrink-0">
          <div className="flex space-x-3">
            <textarea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="Speak your query to the ancient archive..."
              className="flex-1 resize-none rounded-lg px-4 py-3 bg-black/30 border border-bronze text-parchment placeholder-bronze/70 focus:outline-none focus:border-gold focus:ring-2 focus:ring-gold/20 min-h-[60px] max-h-32"
              disabled={isLoading}
            />
            <button
              onClick={sendMessage}
              disabled={!inputValue.trim() || isLoading}
              className="px-6 py-3 bg-gradient-to-r from-amber-600 to-yellow-500 text-black font-semibold rounded-lg hover:from-amber-500 hover:to-yellow-400 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200 border border-gold glow-text"
            >
              {isLoading ? '...' : 'Seek'}
            </button>
          </div>
        </div>
      </div>

      {/* Footer */}
      <footer className="border-t-2 border-copper p-4 text-center text-bronze text-sm flex-shrink-0">
        <p className="runic-accent">
          May the light of knowledge guide your path through the Cognitive Realm
        </p>
      </footer>
    </div>
  );
}
