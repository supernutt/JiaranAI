'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Send } from 'lucide-react';

const avatars = {
  'Sophia': '🧠',
  'Leo': '🧐',
  'Maya': '📘',
  'User': '👤'
};

export default function ClassroomPage() {
  const router = useRouter();
  const [topic, setTopic] = useState('');
  const [discussions, setDiscussions] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [inputHistory, setInputHistory] = useState([]);
  const [historyIndex, setHistoryIndex] = useState(0);

  const fetchClassroomDiscussion = async (topicText) => {
    setIsLoading(true);
    setError(null);
    
    try {
      const response = await fetch('http://localhost:8000/generate-classroom', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic: topicText }),
      });
      
      if (!response.ok) {
        throw new Error(`Server responded with status ${response.status}`);
      }
      
      const data = await response.json();
      
      // Add user message first
      const newMessages = [
        {
          name: 'User',
          statement: `I'd like to discuss: ${topicText}`
        },
        ...data.discussion
      ];
      
      setDiscussions(prev => [...prev, ...newMessages]);
      
      // Add to input history if it's a new topic
      if (!inputHistory.includes(topicText)) {
        setInputHistory(prev => [...prev, topicText]);
        setHistoryIndex(inputHistory.length + 1);
      }
      
    } catch (err) {
      console.error('Error fetching classroom discussion:', err);
      setError(err.message);
      
      // Fallback messages if API fails
      const fallbackMessages = [
        {
          name: 'User',
          statement: `I'd like to discuss: ${topicText}`
        },
        {
          name: 'Sophia',
          statement: `I wonder how ${topicText} works and what implications it has for our understanding of the world?`
        },
        {
          name: 'Leo',
          statement: `I'm skeptical about some of the claims made about ${topicText} - we should examine the evidence carefully.`
        },
        {
          name: 'Maya',
          statement: `${topicText} can be understood as a system with interconnected parts that function together to achieve specific outcomes.`
        }
      ];
      
      setDiscussions(prev => [...prev, ...fallbackMessages]);
    } finally {
      setIsLoading(false);
      setTopic('');  // Clear the input field
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!topic.trim()) return;
    
    fetchClassroomDiscussion(topic);
  };

  const handleKeyDown = (e) => {
    // Handle up arrow for input history
    if (e.key === 'ArrowUp' && historyIndex > 0) {
      const newIndex = historyIndex - 1;
      setHistoryIndex(newIndex);
      setTopic(inputHistory[newIndex]);
    }
    
    // Handle down arrow for input history
    if (e.key === 'ArrowDown' && historyIndex < inputHistory.length - 1) {
      const newIndex = historyIndex + 1;
      setHistoryIndex(newIndex);
      setTopic(inputHistory[newIndex]);
    }
  };

  return (
    <div className="flex flex-col min-h-screen bg-zinc-950 text-white">
      <header className="bg-zinc-900 p-4 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">AI Classroom</h1>
          <Link href="/" className="text-violet-400 hover:text-violet-300">
            Home
          </Link>
        </div>
      </header>
      
      <main className="flex-grow container mx-auto p-4 flex flex-col">
        {/* Chat Container */}
        <div className="flex-grow bg-zinc-900 rounded-xl shadow-md p-6 mb-4 overflow-y-auto max-h-[70vh]">
          {discussions.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-64 text-zinc-400">
              <p className="text-xl mb-2">Welcome to the AI Classroom!</p>
              <p>Enter a topic below to start a discussion with our AI characters.</p>
            </div>
          ) : (
            <div className="space-y-4">
              {discussions.map((message, index) => (
                <div 
                  key={index} 
                  className={`flex ${message.name === 'User' ? 'justify-end' : 'justify-start'}`}
                >
                  <div 
                    className={`flex max-w-[75%] ${
                      message.name === 'User' 
                        ? 'flex-row-reverse bg-violet-900/30 rounded-bl-xl rounded-tl-xl rounded-tr-xl border border-violet-800' 
                        : 'bg-zinc-800 rounded-br-xl rounded-tr-xl rounded-tl-xl border border-zinc-700'
                    } p-3`}
                  >
                    <div className="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center text-2xl mr-2 bg-zinc-800 border border-zinc-700">
                      {avatars[message.name]}
                    </div>
                    <div>
                      <p className={`font-semibold text-sm ${
                        message.name === 'Sophia' ? 'text-purple-400' : 
                        message.name === 'Leo' ? 'text-amber-400' : 
                        message.name === 'Maya' ? 'text-blue-400' : 
                        'text-violet-300'
                      }`}>
                        {message.name}
                      </p>
                      <p className="text-zinc-200">{message.statement}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
        
        {/* Input Form */}
        <div className="bg-zinc-900 rounded-xl shadow-md p-6 border border-zinc-800">
          <form onSubmit={handleSubmit} className="flex flex-col gap-4">
            {error && (
              <div className="p-3 bg-red-900/30 text-red-300 rounded-md border border-red-800 text-sm">
                {error}
              </div>
            )}
            
            <div className="flex gap-2">
              <input
                type="text"
                value={topic}
                onChange={(e) => setTopic(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder="Enter a topic or ask a question..."
                className="flex-grow p-3 border border-zinc-700 rounded-lg bg-zinc-800 text-white placeholder-zinc-500 focus:outline-none focus:ring-2 focus:ring-violet-500"
                disabled={isLoading}
              />
              <button
                type="submit"
                disabled={isLoading || !topic.trim()}
                className="px-4 py-2 bg-violet-600 text-white rounded-lg hover:bg-violet-700 transition-colors disabled:bg-violet-900/50 disabled:text-violet-300"
              >
                {isLoading ? (
                  <div className="animate-spin h-6 w-6 border-2 border-white border-t-transparent rounded-full"></div>
                ) : (
                  <Send size={20} />
                )}
              </button>
            </div>
          </form>
          
          <div className="mt-4 text-sm text-zinc-400">
            <p className="font-medium mb-2">Your AI classmates:</p>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-2">
              <div className="p-2 bg-zinc-800 rounded-lg border border-zinc-700">
                <p className="font-semibold text-purple-400 flex items-center">
                  {avatars['Sophia']} <span className="ml-2">Sophia</span>
                </p>
                <p className="text-xs text-zinc-400">The curious one who asks insightful questions</p>
              </div>
              <div className="p-2 bg-zinc-800 rounded-lg border border-zinc-700">
                <p className="font-semibold text-amber-400 flex items-center">
                  {avatars['Leo']} <span className="ml-2">Leo</span>
                </p>
                <p className="text-xs text-zinc-400">The skeptical one who challenges assumptions</p>
              </div>
              <div className="p-2 bg-zinc-800 rounded-lg border border-zinc-700">
                <p className="font-semibold text-blue-400 flex items-center">
                  {avatars['Maya']} <span className="ml-2">Maya</span>
                </p>
                <p className="text-xs text-zinc-400">The explainer who clarifies concepts</p>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
} 