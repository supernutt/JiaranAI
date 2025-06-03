'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Send, MessageSquare, User, Bot, Loader2, Sparkles, Lightbulb, Users, Film, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { marked } from 'marked';

// API Base URL - can be updated based on environment
const API_BASE_URL = 'http://localhost:8000';

// These aren't needed with the new avatar URLs from the API
// const AI_AVATARS = {
//   Sophia: <Sparkles className="h-full w-full text-pink-400" />,
//   Leo: <Lightbulb className="h-full w-full text-blue-400" />,
//   Maya: <Users className="h-full w-full text-green-400" />,
// };

// Update the fallback response to match the new message format
const FALLBACK_CLASSROOM_RESPONSE = {
  messages: [
    { author: "Sophia", text: "Hello! I'm Sophia. I'm ready to discuss how AI can enhance creative writing. What are your thoughts?" },
    { author: "Leo", text: "Hi, I'm Leo! I believe AI could be a great tool for brainstorming and overcoming writer's block. For example, generating plot ideas!" },
    { author: "Maya", text: "I agree, Leo! Maya here. And AI can also help with editing, like checking grammar or suggesting stylistic improvements." },
  ],
};

const POLLING_INTERVAL = 3000; // 3 seconds
const MAX_POLL_ATTEMPTS = 20; // Max attempts (e.g., 20 * 3s = 1 minute)
const MAX_MESSAGE_LENGTH = 500; // Maximum characters for user input

export default function ClassroomPage() {
  // Original state
  const [topic, setTopic] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const messagesEndRef = useRef(null);
  const chatContainerRef = useRef(null); // Ref for the scrollable chat area
  
  // New state for dynamic classroom
  const [sessionId, setSessionId] = useState(null);
  const [roster, setRoster] = useState([]);
  const [messages, setMessages] = useState([]);
  const [input, setInput] = useState('');

  // --- State for Dialogue Overlay UI --- 
  const [isDialogueOverlayActive, setIsDialogueOverlayActive] = useState(false);
  const [currentDialogueScriptTurns, setCurrentDialogueScriptTurns] = useState([]);
  const [currentTurnInScriptIndex, setCurrentTurnInScriptIndex] = useState(0);
  const [currentMessageIndexInTurn, setCurrentMessageIndexInTurn] = useState(0);
  const [displayedMessageInfo, setDisplayedMessageInfo] = useState(null); // { author, text, avatar_url }
  const [isAwaitingUserOverlayInput, setIsAwaitingUserOverlayInput] = useState(false);
  const [overlayInput, setOverlayInput] = useState(''); // Input for the overlay
  // --- End of Dialogue Overlay UI State ---

  // --- State for Manim video generation ---
  const [videoPrompt, setVideoPrompt] = useState('');
  const [isVideoLoading, setIsVideoLoading] = useState(false); // For initial POST to /generate
  const [videoGenerationStatus, setVideoGenerationStatus] = useState(null); // PENDING, PROCESSING, SUCCESS, FAILURE, or custom messages
  const [videoResultUrl, setVideoResultUrl] = useState(null); // Stores the final, full video URL
  const [videoError, setVideoError] = useState(null); // For errors during generation or polling
  
  const [currentTaskId, setCurrentTaskId] = useState(null);
  const [pollingAttempts, setPollingAttempts] = useState(0);
  const pollingIntervalRef = useRef(null); // To store interval ID for cleanup
  const [currentBackoff, setCurrentBackoff] = useState(POLLING_INTERVAL); // Track current backoff time
  // --- End of video generation state ---

  // --- Helper function to display the current message in the Dialogue Overlay ---
  const displayNextMessageInOverlay = (script, turnIdx, messageInTurnIdx, activeRoster) => {
    if (!script || script.length === 0 || turnIdx >= script.length) {
      // No more turns or script is empty, prepare for user input or end dialogue
      setDisplayedMessageInfo(null); // Clear display
      setIsAwaitingUserOverlayInput(true); // Expect user input next
      // Potentially close overlay if no further interaction is planned after script ends without user input
      // For now, we'll assume user input will follow or a new script will be loaded.
      return;
    }

    const currentTurnData = script[turnIdx];
    let messageText = "";
    let authorName = "";
    let authorInfo = null;

    if (messageInTurnIdx === 0) { // Teacher's message
      authorName = "Jiaran"; // Assuming teacher's name is fixed or derived from turn data if available
      messageText = currentTurnData.teacher;
    } else { // Student's message
      const studentIndex = messageInTurnIdx - 1;
      if (currentTurnData.students && studentIndex < currentTurnData.students.length) {
        const student = currentTurnData.students[studentIndex];
        authorName = student.author;
        messageText = student.text;
      } else {
        // This means we've shown all students in this turn, move to next turn or await input
        // This specific case is handled by the click handler logic later
        // For now, if called directly, it might mean end of current turn's content
        displayNextMessageInOverlay(script, turnIdx + 1, 0, activeRoster); // Try next turn
        return;
      }
    }
    
    authorInfo = activeRoster.find(p => p.name === authorName);

    setDisplayedMessageInfo({
      author: authorName,
      text: messageText,
      avatar_url: authorInfo?.avatarUrl || null, // Fallback if avatar not found
    });
    setCurrentDialogueScriptTurns(script); // Ensure script is up to date
    setCurrentTurnInScriptIndex(turnIdx);
    setCurrentMessageIndexInTurn(messageInTurnIdx);
    setIsDialogueOverlayActive(true);
    setIsAwaitingUserOverlayInput(false); // AI/Student is "speaking"
  };
  // --- End Helper function ---

  const scrollToBottom = () => {
    if (chatContainerRef.current) {
      // Using scrollTo for smooth behavior on the specific container
      chatContainerRef.current.scrollTo({
        top: chatContainerRef.current.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  useEffect(() => {
    // No longer using a separate timer, relying on React's render cycle and useEffect dependency
    scrollToBottom();
  }, [messages]);

  // Helper function for sleep
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // Function to add a message to the chat
  const addMessage = (newMessage) => {
    setMessages(prevMessages => [...prevMessages, newMessage]);
  };

  // Modified startLecture function
  async function startLecture(lectureTopic, currentSessionId, currentRoster) {
    // Messages state is managed by handleSubmit before calling startLecture
    // setError(null); // error is managed by handleSubmit

    // Add to the hidden log if desired
    // addMessage({ author: "You", text: `Let's discuss: ${lectureTopic}`, avatar_url: null });

    try {
      const res = await fetch(`${API_BASE_URL}/classroom/script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: lectureTopic, session_id: currentSessionId })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        // Display error in the old way for now, or adapt for overlay
        setError(errorData.detail || 'Failed to fetch lecture script.');
        const jiaranErrorAvatar = currentRoster.find(p => p.name === "Jiaran")?.avatarUrl;
        addMessage({ author: "Jiaran", text: "I couldn't prepare a lecture on that topic right now. Maybe try another?", avatar_url: jiaranErrorAvatar });
        setIsLoading(false); // Ensure loading stops
        return;
      }
      const { turns } = await res.json();

      if (!turns || turns.length === 0) {
        const jiaranErrorAvatar = currentRoster.find(p => p.name === "Jiaran")?.avatarUrl;
        // Display error in the old way for now, or adapt for overlay
        addMessage({ author: "Jiaran", text: "I couldn't prepare a lecture on that topic right now. Maybe try another?", avatar_url: jiaranErrorAvatar });
        setError("Received no turns for the lecture.");
        setIsLoading(false); // Ensure loading stops
        return;
      }

      // Instead of looping and calling addMessage, set up for dialogue overlay
      displayNextMessageInOverlay(turns, 0, 0, currentRoster);
      
      // Clear the main chat input as interaction moves to overlay
      setTopic(''); 

    } catch (err) {
      console.error('Error during lecture script execution:', err);
      setError(err.message || 'An error occurred fetching the lecture script.');
      const jiaranErrorAvatar = currentRoster.find(p => p.name === "Jiaran")?.avatarUrl;
      addMessage({ author: "Jiaran", text: "Sorry, I ran into a problem delivering that lecture. Please try again.", avatar_url: jiaranErrorAvatar });
    } finally {
      // setIsLoading(false); // isLoading is managed by handleSubmit/sendTurn now
    }
  }

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleTopicChange = (e) => {
    setTopic(e.target.value);
  };

  const handleVideoPromptChange = (e) => {
    setVideoPrompt(e.target.value);
  };

  // Modified handleSubmit to manage session and then call startLecture
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError('Please enter a topic to discuss.');
      return;
    }

    setIsLoading(true);
    setError(null);
    setMessages([]); // Clear previous messages for a new lecture topic

    try {
      // 1. Start a new session or get roster
      const startRes = await fetch(`${API_BASE_URL}/classroom/start`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: topic }), // Use the actual topic for session start
      });
      if (!startRes.ok) {
        const errorData = await startRes.json().catch(() => ({ detail: startRes.statusText }));
        throw new Error(errorData.detail || 'Failed to initialize classroom session.');
      }
      const sessionData = await startRes.json();
      setSessionId(sessionData.sessionId);
      const currentRoster = sessionData.roster || []; // Get roster directly
      setRoster(currentRoster); // Set state for future use

      // 2. Add the initial "Let's discuss" message from the user
      addMessage({ author: "You", text: `Let's discuss: ${topic}`, avatar_url: null });
      
      // 3. Call startLecture with the new topic, sessionId, and currentRoster
      await startLecture(topic, sessionData.sessionId, currentRoster);

    } catch (err) {
      console.error('Error starting new classroom topic:', err);
      setError(err.message || 'An error occurred starting the new topic.');
      // Optionally, display a generic error message in chat via addMessage
    } finally {
      setIsLoading(false);
      setTopic(''); // Clear topic input after attempting to start
    }
  };

  // sendTurn function (for user's interactive messages AFTER lecture or for Q&A)
  // This function was not provided in the original prompt but is implied for Task 2.3
  // Assuming a structure similar to the old sendTurn, but it might need to be created or adapted.
  // For now, let's stub it. Task 2.3 ensures this is used for the chat input.
  const sendTurn = async (userMessage) => {
    if (!sessionId) {
      setError('No active classroom session. Please start a new topic or lecture first.');
      addMessage({author: "System", text: "Session not active. Please start a new topic.", avatar_url: null});
      return;
    }
    if (!userMessage.trim()) return;

    setIsLoading(true);
    addMessage({ author: "You", text: userMessage, avatar_url: null });
    setInput("");

    try {
      // Use the script endpoint instead of turn endpoint to generate full multi-turn conversations
      const res = await fetch(`${API_BASE_URL}/classroom/script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: userMessage, session_id: sessionId }),
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || 'Failed to send message.');
      }
      
      const { turns } = await res.json();

      if (!turns || turns.length === 0) {
        // Handle error in overlay - maybe show a temporary message in displayedMessageInfo
        setDisplayedMessageInfo({
          author: "System",
          text: "I couldn't continue the discussion on that point. Try rephrasing?",
          avatar_url: roster.find(p => p.name === "Jiaran")?.avatarUrl // Or a generic system avatar
        });
        // After a short delay, re-enable user input or guide them
        setTimeout(() => {
          if(isDialogueOverlayActive) setIsAwaitingUserOverlayInput(true);
        }, 2000);
        return;
      }

      // Display the new script turns in the overlay
      displayNextMessageInOverlay(turns, 0, 0, roster); 

    } catch (err) {
      console.error('Error sending message (turn):', err);
      // Display error in overlay
      setDisplayedMessageInfo({
        author: "System",
        text: `Error: ${err.message || 'Could not send message.'}`,
        avatar_url: null // Or a generic system error avatar
      });
      // After a short delay, re-enable user input or guide them
      setTimeout(() => {
        if(isDialogueOverlayActive) setIsAwaitingUserOverlayInput(true); // Allow user to try again
      }, 2000);
      // setError(err.message || 'An error occurred sending your message.'); // Old error handling
    } finally {
      setIsLoading(false); // Ensure loading state is reset
    }
  };

  // Ensure handleMessageSubmit uses sendTurn
  const handleMessageSubmit = (e) => {
    e.preventDefault();
    if (input.trim()) {
      sendTurn(input); // This will handle interactive follow-ups
    }
  };

  // --- Polling Logic --- 
  const pollTaskStatus = useCallback(async (taskId, statusUrl) => {
    if (!statusUrl) {
      setVideoError("Status URL not provided, cannot poll.");
      setVideoGenerationStatus("Error: Invalid status URL.");
      setIsVideoLoading(false); // Stop overall loading if status URL is bad
      return;
    }
    try {
      const response = await fetch(`${API_BASE_URL}${statusUrl}`); // Prepend base URL
      if (!response.ok) {
        // Handle 404 specially - the task might have been cleaned up or never existed
        if (response.status === 404) {
          const errData = await response.json().catch(() => ({ detail: "Task not found" }));
          throw new Error(`Polling failed: ${response.status} ${errData.detail || "Task not found"}`);
        }
        
        // Handle server errors (500+) with a more informative message
        if (response.status >= 500) {
          throw new Error(`Server error during polling: ${response.status}`);
        }
        
        // Handle other errors
        const errData = await response.json().catch(() => ({ detail: "Polling request failed"}));
        throw new Error(`Polling failed: ${response.status} ${errData.detail || response.statusText}`);
      }
      const data = await response.json();

      setVideoGenerationStatus(data.status + (data.message ? `: ${data.message}` : ''));

      if (data.status === "SUCCESS") {
        if (data.result_url) {
          setVideoResultUrl(`${API_BASE_URL}${data.result_url}`); // Prepend base for video src
          setVideoError(null);
        } else {
          setVideoError("Task succeeded but no video URL was provided.");
          setVideoResultUrl(null);
        }
        clearInterval(pollingIntervalRef.current);
        setCurrentTaskId(null); 
        setIsVideoLoading(false); // No longer loading overall
        setCurrentBackoff(POLLING_INTERVAL); // Reset backoff for next time
      } else if (data.status === "FAILURE") {
        setVideoError(data.error_detail || data.message || "Video generation failed.");
        setVideoResultUrl(null);
        clearInterval(pollingIntervalRef.current);
        setCurrentTaskId(null);
        setIsVideoLoading(false); // No longer loading overall
        setCurrentBackoff(POLLING_INTERVAL); // Reset backoff for next time
      } else if (pollingAttempts >= MAX_POLL_ATTEMPTS) {
        setVideoError("Video generation timed out. Please try again later.");
        setVideoResultUrl(null);
        clearInterval(pollingIntervalRef.current);
        setCurrentTaskId(null);
        setIsVideoLoading(false); // No longer loading overall
        setCurrentBackoff(POLLING_INTERVAL); // Reset backoff for next time
      } else {
        // Still PENDING or PROCESSING, continue polling with exponential backoff
        setPollingAttempts(prev => prev + 1);
        
        // Implement exponential backoff - double the interval each time up to a maximum
        if (pollingIntervalRef.current) {
          clearInterval(pollingIntervalRef.current);
          const newBackoff = Math.min(currentBackoff * 1.5, 15000); // Cap at 15 seconds
          setCurrentBackoff(newBackoff);
          
          // Set up new interval with increased backoff
          pollingIntervalRef.current = setInterval(() => {
            pollTaskStatus(currentTaskId, statusUrl);
          }, newBackoff);
        }
      }
    } catch (err) {
      console.error("Error polling task status:", err);
      setVideoError(err.message || "An error occurred while polling for status.");
      setVideoResultUrl(null);
      clearInterval(pollingIntervalRef.current);
      setCurrentTaskId(null);
      setIsVideoLoading(false); // No longer loading overall
      setCurrentBackoff(POLLING_INTERVAL); // Reset backoff for next time
    }
  }, []); // Dependency for pollTaskStatus

  useEffect(() => {
    if (currentTaskId && pollingIntervalRef.current == null) { // Start polling only if there's a task and not already polling
        const statusUrl = `/animations/status/${currentTaskId}`; // Construct status URL from task ID
        setPollingAttempts(0);
        setCurrentBackoff(POLLING_INTERVAL); // Reset backoff when starting new polling
        pollingIntervalRef.current = setInterval(() => {
            pollTaskStatus(currentTaskId, statusUrl);
        }, POLLING_INTERVAL);
        
        // Initial immediate poll
        pollTaskStatus(currentTaskId, statusUrl);
    }
    // Cleanup function to clear interval when component unmounts or task ID changes
    return () => {
        if (pollingIntervalRef.current) {
            clearInterval(pollingIntervalRef.current);
            pollingIntervalRef.current = null; // Reset ref
        }
    };
  }, [currentTaskId, pollTaskStatus]); // pollTaskStatus is now a dependency due to useCallback
  // --- End Polling Logic ---

  const handleVideoSubmit = async (e) => {
    e.preventDefault();
    if (!videoPrompt.trim()) {
      setVideoError('Please enter a concept to visualize.');
      return;
    }

    setIsVideoLoading(true);
    setVideoError(null);
    setVideoResultUrl(null);
    setVideoGenerationStatus("Initiating video generation...");
    setCurrentTaskId(null); // Clear previous task ID
    if (pollingIntervalRef.current) {
        clearInterval(pollingIntervalRef.current); // Clear any existing interval
        pollingIntervalRef.current = null;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/animations/generate`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ 
          prompt: videoPrompt, 
          scene_name: "UserRequestedScene", // Example, can be dynamic
          quality: "low", 
          api_choice: "openai" // Or "mock" or make it selectable
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        throw new Error(errorData.detail || 'Failed to initiate video generation.');
      }

      const data = await response.json(); // Expects { message, task_id, status_url }
      
      if (data.task_id && data.status_url) {
        setCurrentTaskId(data.task_id); // This will trigger the useEffect to start polling
        setVideoGenerationStatus("Generation request submitted. Waiting for progress...");
        // No need to call setIsVideoLoading(false) here if polling starts
      } else {
        throw new Error("Invalid response from generation initiation.");
      }

    } catch (err) {
      console.error('Error initiating video generation:', err);
      setVideoError(err.message || 'An error occurred during video generation initiation.');
      setVideoGenerationStatus("Error initiating generation.");
      setIsVideoLoading(false); // Stop loading if initiation failed
    }
    // No setIsVideoLoading(false) here; it's handled by polling logic or error in initiation
  };

  // Reset classroom session function
  const resetClassroom = () => {
    setSessionId(null);
    setRoster([]);
    setMessages([]);
    setInput('');
    setTopic(''); // Also clear topic input
    setError(null);
    setIsLoading(false); // Reset loading state

    // Reset Dialogue Overlay states
    setIsDialogueOverlayActive(false);
    setCurrentDialogueScriptTurns([]);
    setCurrentTurnInScriptIndex(0);
    setCurrentMessageIndexInTurn(0);
    setDisplayedMessageInfo(null);
    setIsAwaitingUserOverlayInput(false);
    setOverlayInput('');
  };

  const handleOverlayInputChange = (e) => {
    setOverlayInput(e.target.value);
  };

  // --- Click handler for speech bubble to advance dialogue ---
  const handleNextMessageOrInput = () => {
    if (isAwaitingUserOverlayInput) return; // Do nothing if waiting for user text input

    let nextMessageInTurnIdx = currentMessageIndexInTurn + 1;
    let nextTurnIdx = currentTurnInScriptIndex;

    const currentTurnData = currentDialogueScriptTurns[currentTurnInScriptIndex];
    const totalMessagesInCurrentTurn = 1 + (currentTurnData.students?.length || 0); // Teacher + students

    if (nextMessageInTurnIdx >= totalMessagesInCurrentTurn) {
      // Moved past all messages in the current turn, so advance to the next turn
      nextTurnIdx++;
      nextMessageInTurnIdx = 0; // Start with the teacher of the next turn
    }

    if (nextTurnIdx < currentDialogueScriptTurns.length) {
      // There are more turns or messages to display
      displayNextMessageInOverlay(currentDialogueScriptTurns, nextTurnIdx, nextMessageInTurnIdx, roster);
    } else {
      // No more turns in the script, set up for user input
      setDisplayedMessageInfo(null); // Clear current message
      setIsAwaitingUserOverlayInput(true);
    }
  };
  // --- End Click Handler ---

  // --- Submit handler for user input in the overlay ---
  const handleOverlaySubmit = async (e) => {
    e.preventDefault();
    if (!overlayInput.trim() || !sessionId) {
      // Basic validation or if session is not active (shouldn't happen if overlay is active)
      return;
    }

    setIsLoading(true); // For visual feedback on the submit button
    // No need to add "You: ..." to displayedMessageInfo, sendTurn will fetch new script
    
    // The actual message sending logic is now fully within sendTurn
    await sendTurn(overlayInput); 

    setOverlayInput(""); // Clear input after sending (sendTurn will handle isLoading)
    // isAwaitingUserOverlayInput will be set to false by displayNextMessageInOverlay via sendTurn
  };
  // --- End Overlay Submit Handler ---

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
        {sessionId && (
          <button 
            onClick={resetClassroom}
            className="mt-2 px-3 py-1 text-sm bg-secondary text-secondary-foreground rounded hover:bg-secondary/80 transition-colors"
          >
            Start New Discussion
          </button>
        )}
      </header>

      {/* Original Chat UI - Conditionally Hidden if Overlay is Active */}
      {!isDialogueOverlayActive && (
        <div className="bg-card text-card-foreground rounded-xl shadow-2xl w-full max-w-2xl border border-border flex flex-col" style={{height: '70vh'}}>
          <div ref={chatContainerRef} className="flex-grow p-6 space-y-6 overflow-y-auto scrollbar-thin scrollbar-thumb-secondary scrollbar-track-transparent">
            {messages.length === 0 && !isLoading && (
              <div className="flex flex-col items-center justify-center h-full text-center">
                <Users size={48} className="text-muted-foreground mb-4" />
                <p className="text-lg text-muted-foreground">
                  Enter a topic below to start the discussion.
                </p>
              </div>
            )}
            {messages.map((msg, index) => (
              <div key={index} className={`flex items-start gap-3 ${msg.author === 'You' ? 'justify-end' : 'justify-start'}`}>
                {msg.author !== 'You' && (
                  <div className="flex-shrink-0 h-10 w-10 rounded-full bg-secondary flex items-center justify-center border border-border shadow-sm overflow-hidden">
                    {msg.avatar_url ? (
                      <img 
                        src={msg.avatar_url} 
                        alt={msg.author} 
                        className="h-full w-full object-cover"
                      />
                    ) : (
                      <Bot className="h-6 w-6 text-muted-foreground" />
                    )}
                  </div>
                )}
                <div 
                  className={`max-w-[70%] p-3 rounded-lg shadow-sm ${ 
                    msg.author === 'You' 
                      ? 'bg-primary text-primary-foreground rounded-br-none' 
                      : 'bg-secondary text-secondary-foreground rounded-bl-none'
                  }`}
                >
                  {msg.author !== 'You' && <p className="text-xs font-semibold text-primary mb-1">{msg.author}</p>}
                  <div 
                    className="text-sm whitespace-pre-wrap"
                    dangerouslySetInnerHTML={{ __html: marked(msg.text) }}
                  />
                </div>
                {msg.author === 'You' && (
                  <div className="flex-shrink-0 h-10 w-10 rounded-full bg-blue-500 flex items-center justify-center border border-border shadow-sm">
                    <User className="h-6 w-6 text-white" />
                  </div>
                )}
              </div>
            ))}
            <div ref={messagesEndRef} /> 
            {isLoading && messages.length === 0 && (
              <div className="flex justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-primary" />
              </div>
            )}
          </div>
          
          <div className="border-t border-border p-4 bg-card rounded-b-xl">
            {error && (
              <p className="text-destructive text-xs mb-2 px-1">{error}</p>
            )}
            {!sessionId ? (
              // Topic submission form
            <form onSubmit={handleSubmit} className="flex items-center gap-3">
              <input
                type="text"
                value={topic}
                  onChange={handleTopicChange}
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
            ) : (
              // Message input form for ongoing conversation (original chat)
              <form onSubmit={handleMessageSubmit} className="flex items-center gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Type a question..."
                  className="flex-grow p-3 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-primary shadow-sm disabled:opacity-50"
                  disabled={isLoading}
                />
                <button 
                  type="submit" 
                  disabled={isLoading || !input.trim()}
                  className="p-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-card disabled:opacity-50 disabled:cursor-not-allowed shadow-md"
                >
                  {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />} 
                </button>
              </form>
            )}
          </div>
        </div>
      )}

      {/* --- Dialogue Overlay --- */}
      {isDialogueOverlayActive && (
        <div className="fixed inset-0 bg-black bg-opacity-75 flex flex-col items-center justify-center z-50 p-4 font-sans">
          {/* Main container for character and speech bubble */} 
          <div className="relative w-full max-w-3xl flex items-end justify-center" style={{ minHeight: '300px' }}>
            
            {/* Character Image Display */} 
            {displayedMessageInfo && displayedMessageInfo.avatar_url && (
              <div className="absolute right-0 bottom-0 transform translate-x-1/4 md:translate-x-1/3 z-10">
                 <img 
                  src={displayedMessageInfo.avatar_url} 
                  alt={displayedMessageInfo.author} 
                  className="h-64 w-auto md:h-80 lg:h-96 object-contain drop-shadow-xl"
                />
              </div>
            )}

            {/* Speech Bubble and Text (if a message is being displayed) */} 
            {displayedMessageInfo && !isAwaitingUserOverlayInput && (
              <div 
                className="relative bg-white p-6 rounded-xl shadow-2xl text-gray-800 w-full md:w-3/4 lg:w-2/3 cursor-pointer hover:shadow-3xl transition-shadow duration-300 min-h-[120px] flex flex-col justify-center z-20"
                onClick={handleNextMessageOrInput} 
                style={{ marginRight: displayedMessageInfo?.avatar_url ? '15%' : '0' }} // Offset if character is present
              >
                <p className="text-sm font-semibold text-purple-600 mb-1">{displayedMessageInfo.author}</p>
                <div 
                  className="text-base whitespace-pre-wrap" 
                  dangerouslySetInnerHTML={{ __html: marked(displayedMessageInfo.text) }}
                />
                {/* Simple tail - can be improved with more complex CSS/SVG */}
                <div className="absolute bottom-4 -right-3 w-0 h-0 border-l-[15px] border-l-white border-t-[10px] border-t-transparent border-b-[10px] border-b-transparent z-0"></div>
                <p className="text-xs text-gray-400 mt-2 text-right">Click to continue...</p>
              </div>
            )}
          </div>

          {/* User Input Area (if waiting for user input) */} 
          {isAwaitingUserOverlayInput && (
            <div className="mt-8 w-full max-w-xl p-4 bg-white rounded-lg shadow-xl z-30">
              <form onSubmit={handleOverlaySubmit} className="flex items-center gap-3">
                <input
                  type="text"
                  value={overlayInput} // Use new state for overlay input
                  onChange={handleOverlayInputChange} // Use new handler
                  placeholder="Your response..."
                  className="flex-grow p-3 border border-gray-300 rounded-lg text-gray-800 placeholder-gray-500 focus:outline-none focus:ring-2 focus:ring-purple-500 shadow-sm disabled:opacity-70" // Added disabled style
                  disabled={isLoading} // Disable input while loading next script
                  autoFocus
                />
                <button 
                  type="submit" 
                  disabled={isLoading || !overlayInput.trim()}
                  className="p-3 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition-colors focus:outline-none focus:ring-2 focus:ring-purple-500 focus:ring-offset-2 disabled:opacity-50 shadow-md"
                >
                  {isLoading ? <Loader2 className="h-5 w-5 animate-spin" /> : <Send className="h-5 w-5" />}
                </button>
              </form>
            </div>
          )}

          {/* Temporary Close Button for Debugging Overlay */} 
          {/* <button 
            onClick={() => {
              setIsDialogueOverlayActive(false); 
              resetClassroom(); // Full reset might be too much, just hide for now
            }}
            className="absolute top-4 right-4 px-3 py-1 text-sm bg-red-500 text-white rounded hover:bg-red-600 z-50"
          >
            Close Overlay (DEV)
          </button> */} 
        </div>
      )}
      {/* --- End Dialogue Overlay --- */}

      {/* --- Manim Video Generation Section --- */}
      <div className="bg-card text-card-foreground rounded-xl shadow-2xl w-full max-w-2xl border border-border flex flex-col mt-8 mb-8">
        <header className="p-4 border-b border-border text-center">
          <div className="flex items-center justify-center gap-3 mb-1">
            <Film className="h-7 w-7 text-primary" />
            <h2 className="text-xl font-semibold text-foreground">Concept Visualization Engine</h2>
          </div>
          <p className="text-sm text-muted-foreground">
            Have a concept you want to see visualized? Enter it below!
          </p>
        </header>
        <div className="p-6">
          {videoGenerationStatus && !videoResultUrl && !videoError && (
            <div className="text-sm mb-3 p-3 bg-blue-600/10 text-blue-700 rounded-md flex items-center gap-2">
                <Loader2 className="h-4 w-4 animate-spin" /> 
                <span>{videoGenerationStatus} (Attempt: {pollingAttempts}/{MAX_POLL_ATTEMPTS})</span>
            </div>
          )}
          {videoError && (
            <div className="text-sm mb-3 p-3 bg-destructive/10 text-destructive rounded-md flex items-center gap-2">
                <AlertTriangle className="h-4 w-4" /> 
                <span>Error: {videoError}</span>
            </div>
          )}
          {videoResultUrl && (
            <div className="text-sm mb-3 p-3 bg-green-600/10 text-green-700 rounded-md">
              <div className="flex items-center gap-2 mb-2">
                <CheckCircle2 className="h-4 w-4" /> 
                <span>Video generated successfully!</span>
              </div>
              <video controls src={videoResultUrl} className="mt-2 w-full rounded shadow-md border border-border" preload="metadata">
                Your browser does not support the video tag. Please <a href={videoResultUrl} download className="underline">download it here</a>.
              </video> 
            </div>
          )}
          <form onSubmit={handleVideoSubmit} className="flex flex-col gap-4">
            <textarea
              value={videoPrompt}
              onChange={handleVideoPromptChange}
              placeholder="e.g., 'Explain the water cycle visually' or 'Show me how sine and cosine waves relate'"
              className="flex-grow p-3 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-ring focus:border-primary shadow-sm disabled:opacity-50 min-h-[80px] resize-none"
              disabled={isVideoLoading} // isVideoLoading now tracks the whole process
              rows={3}
            />
            <button 
              type="submit" 
              disabled={isVideoLoading || !videoPrompt.trim() || currentTaskId != null} // Disable if loading or already polling a task
              className="p-3 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-card disabled:opacity-50 disabled:cursor-not-allowed shadow-md flex items-center justify-center gap-2"
            >
              {isVideoLoading ? (
                <React.Fragment>
                  <Loader2 className="h-5 w-5 animate-spin" /> Processing...
                </React.Fragment>
              ) : (
                <React.Fragment>
                  <Sparkles className="h-5 w-5" /> Generate Video
                </React.Fragment>
              )}
            </button>
          </form>
        </div>
      </div>
      {/* --- End of Manim Video Generation Section --- */}

    </div>
  );
} 