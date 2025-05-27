'use client';

import { useState, useRef, useEffect } from 'react';
import Link from 'next/link';
import { Send, MessageSquare, User, Bot, Loader2, Sparkles, Lightbulb, Users } from 'lucide-react'; // Added Users for general icon

const AI_AVATARS = {
  Sophia: <Sparkles className="h-full w-full text-pink-400" />,
  Leo: <Lightbulb className="h-full w-full text-blue-400" />,
  Maya: <Users className="h-full w-full text-green-400" />,
};

const FALLBACK_CLASSROOM_RESPONSE = {
  discussion: [
    { speaker: "Sophia", message: "Hello! I'm Sophia. I'm ready to discuss how AI can enhance creative writing. What are your thoughts?" },
    { speaker: "Leo", message: "Hi, I'm Leo! I believe AI could be a great tool for brainstorming and overcoming writer's block. For example, generating plot ideas!" },
    { speaker: "Maya", message: "I agree, Leo! Maya here. And AI can also help with editing, like checking grammar or suggesting stylistic improvements." },
    { speaker: "User", message: "That's interesting! I was wondering if AI could help in developing character arcs?" },
    { speaker: "Sophia", message: "Absolutely! AI could analyze existing character developments in literature and suggest patterns or even generate potential dialogues for a character based on their defined traits." },
  ],
};

export default function ClassroomPage() {
  const [topic, setTopic] = useState('');
  const [messages, setMessages] = useState([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleInputChange = (e) => {
    setTopic(e.target.value);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError('Please enter a topic to discuss.');
      return;
    }

    setIsLoading(true);
    setError(null);
    // Add user's topic as the first message for context, styled as a User message
    const userTopicMessage = { speaker: 'User', message: `Let's discuss: ${topic}` };
    setMessages([userTopicMessage]);

    try {
      const response = await fetch('http://localhost:8000/generate-classroom', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ topic }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'Failed to start classroom discussion.');
      }

      const data = await response.json();
      
      // Map the backend response format (name, statement) to frontend format (speaker, message)
      const formattedDiscussion = data.discussion.map(item => ({
        speaker: item.name,
        message: item.statement
      }));
      
      // Append AI discussion to the user's topic message
      setMessages(prevMessages => [...prevMessages, ...formattedDiscussion]);

    } catch (err) {
      console.error('Error fetching classroom discussion:', err);
      setError(err.message || 'An error occurred. Using fallback discussion.');
      // Append fallback discussion to user's topic message
      setMessages(prevMessages => [...prevMessages, ...FALLBACK_CLASSROOM_RESPONSE.discussion]);
    } finally {
      setIsLoading(false);
      setTopic(''); // Clear input after submission
    }
  };

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-start p-4 pt-16 md:pt-24">
      <div className="absolute top-6 left-6">
        <Link href="/" className="text-primary hover:underline flex items-center gap-2">
         <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-arrow-left"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
          Back to Home
        </Link>
      </div>

      <header className="mb-8 text-center">
        <div className="flex items-center justify-center gap-3 mb-2">
          <MessageSquare className="h-8 w-8 text-primary" />
          <h1 className="text-3xl md:text-4xl font-bold text-foreground">AI Classroom Simulation</h1>
        </div>
        <p className="text-md text-muted-foreground max-w-xl">
          Enter a topic and engage in a simulated discussion with our AI learning assistants.
        </p>
      </header>

      <div className="bg-card text-card-foreground rounded-xl shadow-2xl w-full max-w-2xl border border-border flex flex-col" style={{height: '70vh'}}>
        <div className="flex-grow p-6 space-y-6 overflow-y-auto scrollbar-thin scrollbar-thumb-secondary scrollbar-track-transparent">
          {messages.length === 0 && !isLoading && (
            <div className="flex flex-col items-center justify-center h-full text-center">
              <Users size={48} className="text-muted-foreground mb-4" />
              <p className="text-lg text-muted-foreground">
                Enter a topic below to start the discussion.
              </p>
            </div>
          )}
          {messages.map((msg, index) => (
            <div key={index} className={`flex items-start gap-3 ${msg.speaker === 'User' ? 'justify-end' : 'justify-start'}`}>
              {msg.speaker !== 'User' && (
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-secondary flex items-center justify-center border border-border shadow-sm">
                  {AI_AVATARS[msg.speaker] || <Bot className="h-6 w-6 text-muted-foreground" />}
                </div>
              )}
              <div 
                className={`max-w-[70%] p-3 rounded-lg shadow-sm ${ 
                  msg.speaker === 'User' 
                    ? 'bg-primary text-primary-foreground rounded-br-none' 
                    : 'bg-secondary text-secondary-foreground rounded-bl-none'
                }`}
              >
                {msg.speaker !== 'User' && <p className="text-xs font-semibold text-primary mb-1">{msg.speaker}</p>}
                <p className="text-sm whitespace-pre-wrap">{msg.message}</p>
              </div>
              {msg.speaker === 'User' && (
                <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center border border-border shadow-sm">
                  <User className="h-6 w-6 text-white" />
                </div>
              )}
            </div>
          ))}
          <div ref={messagesEndRef} /> 
          {isLoading && messages.length > 0 && (
            <div className="flex justify-center py-4">
              <Loader2 className="h-6 w-6 animate-spin text-primary" />
            </div>
          )}
        </div>
        
        <div className="border-t border-border p-4 bg-card rounded-b-xl">
          {error && (
            <p className="text-destructive text-xs mb-2 px-1">{error}</p>
          )}
          <form onSubmit={handleSubmit} className="flex items-center gap-3">
            <input
              type="text"
              value={topic}
              onChange={handleInputChange}
              placeholder="Enter a topic to discuss, e.g., 'The Future of AI'..."
              className="flex-grow p-3 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-primary shadow-sm disabled:opacity-50"
              disabled={isLoading}
            />
            <button 
              type="submit" 
              disabled={isLoading || !topic.trim()}
              className="p-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-card disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
            >
              {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
            </button>
          </form>
        </div>
      </div>
    </div>
  );
} 