'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import Link from 'next/link';
import { Send, MessageSquare, User, Bot, Loader2, Sparkles, Lightbulb, Users, Film, AlertTriangle, CheckCircle2 } from 'lucide-react';
import { marked } from 'marked';
import { useSearchParams } from 'next/navigation';

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

  // State for diagnostic data integration
  const [diagnosticData, setDiagnosticData] = useState(null);

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

  const abortControllerRef = useRef(null);

  // Add this ref at the top of ClassroomPage component
  const hasInitializedFromDiagnostic = useRef(false);

  // --- Helper function to display the current message in the Dialogue Overlay ---
  const displayNextMessageInOverlay = useCallback((script, turnIdx, messageInTurnIdx, activeRoster) => {
    if (!script || !script[turnIdx]) {
      console.error("Invalid script or turn index in displayNextMessageInOverlay", { script, turnIdx, messageInTurnIdx });
      // Potentially set an error state for the UI here
      setIsAwaitingUserOverlayInput(true); // Fallback to user input if script is bad
      return;
    }

    const currentTurn = script[turnIdx];
    const isTeacherTurn = messageInTurnIdx === 0;
    
    let authorName, authorAvatar, messageText;
    
    if (isTeacherTurn) {
      messageText = currentTurn.teacher;
      if (typeof messageText !== 'string' || !messageText.trim()) { // Added type check and trim
        console.error("Teacher message is invalid or empty", { teacherText: currentTurn.teacher });
        setDisplayedMessageInfo({ author: "System", text: "Error: Received invalid teacher message.", avatar_url: null });
        setIsAwaitingUserOverlayInput(true); // Fallback
        return;
      }
      const teacherPersona = activeRoster.find(p => p.role === "teacher");
      authorName = teacherPersona?.name || "Teacher";
      authorAvatar = teacherPersona?.avatarUrl || null;
    } else {
      const studentMessage = currentTurn.students[messageInTurnIdx - 1];
      if (!studentMessage || typeof studentMessage.text !== 'string' || !studentMessage.text.trim()) { // Added checks
        console.error("Student message is invalid or empty", { studentMsg: studentMessage });
        setDisplayedMessageInfo({ author: "System", text: "Error: Received invalid student message.", avatar_url: null });
        setIsAwaitingUserOverlayInput(true); // Fallback
        return;
      }
      authorName = studentMessage.author || "Student";
      messageText = studentMessage.text;
      const studentPersona = activeRoster.find(p => p.name === studentMessage.author);
      authorAvatar = studentPersona?.avatarUrl || null;
    }

    console.log("💬 Displaying message:", { authorName, textPreview: messageText.substring(0, 30) + "...", turnIdx, messageInTurnIdx, scriptLength: script.length });

    // THIS IS A KEY CHANGE: When we display a message, we are *not* awaiting user input (yet).
    // User input is only awaited *after* the entire script has been clicked through.
    setIsAwaitingUserOverlayInput(false);

    setDisplayedMessageInfo({
      author: authorName,
      text: messageText,
      avatar_url: authorAvatar
    });

    setCurrentTurnInScriptIndex(turnIdx);
    setCurrentMessageIndexInTurn(messageInTurnIdx);

    // The logic to set isAwaitingUserOverlayInput = true when the script ends is handled
    // by handleNextMessageOrInput when it detects no more messages to display.

  }, [roster]); // Removed dependencies that are passed as arguments (script, turnIdx, etc.)
                 // Roster is a dependency because it's used from closure.

  const scrollToBottom = useCallback(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, []); // No dependencies needed as it only uses ref

  useEffect(() => {
    // No longer using a separate timer, relying on React's render cycle and useEffect dependency
    scrollToBottom();
  }, [messages, scrollToBottom]);

  // Helper function for sleep
  function sleep(ms) { return new Promise(r => setTimeout(r, ms)); }

  // Function to add a message to the chat
  const addMessage = useCallback((newMessage) => {
    setMessages(prev => [...prev, newMessage]);
    // Scroll to bottom after message is added
    setTimeout(scrollToBottom, 100);
  }, [scrollToBottom]); // Add scrollToBottom as dependency

  // Renamed from startLecture to avoid confusion, this is for fetching the script
  const fetchLectureScript = useCallback(async (lectureTopic, currentSessionId, currentRoster) => {
    if (!lectureTopic || !currentSessionId) {
      console.error("Missing required parameters for fetchLectureScript");
      setError("Cannot fetch lecture: missing topic or session ID."); // Set user-facing error
      return Promise.reject(new Error("Missing parameters for fetchLectureScript")); // Return a rejected promise
    }
    // No setIsLoading here, as it's part of the broader initializeClassroomSession loading state
    try {
      console.log("📚 Fetching lecture script for topic:", lectureTopic, "Session:", currentSessionId);
      const response = await fetch(`${API_BASE_URL}/classroom/script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ 
          topic: lectureTopic,
          session_id: currentSessionId
        }),
      });

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        console.error("Failed to fetch lecture script:", errorData.detail);
        setError(errorData.detail || 'Failed to fetch lecture script');
        throw new Error(errorData.detail || 'Failed to fetch lecture script');
      }

      const { turns } = await response.json();
      
      if (!turns || turns.length === 0) {
        console.warn('No lecture content generated by API.');
        setError('No lecture content was generated for this topic. Try a different one?');
        // Still resolve as the API call was "successful" but empty, to avoid unhandled rejection upstream
        // but don't try to display an empty script.
        setIsDialogueOverlayActive(false); // Ensure overlay isn't active with no script
        return; // Don't proceed to displayNextMessageInOverlay
      }

      console.log(`🎬 Received ${turns.length} turns for the lecture script.`);
      setIsDialogueOverlayActive(true);
      setCurrentDialogueScriptTurns(turns);
      setCurrentTurnInScriptIndex(0); // Reset to start of new script
      setCurrentMessageIndexInTurn(0); // Reset to start of new script
      
      displayNextMessageInOverlay(turns, 0, 0, currentRoster);
      setError(null); // Clear any previous errors on success

    } catch (err) {
      console.error('Error in fetchLectureScript:', err);
      // Ensure error state is set for the UI
      setError(err.message || 'An error occurred fetching the lecture script.');
      const jiaranErrorAvatar = currentRoster.find(p => p.name === "Jiaran")?.avatarUrl;
      // Add a message to the main chat if overlay fails to load
      // addMessage({ author: "Jiaran", text: "Sorry, I ran into a problem delivering that lecture. Please try again.", avatar_url: jiaranErrorAvatar });
      setIsDialogueOverlayActive(false); // Don't show overlay if script fetch failed
      throw err; // Re-throw to be caught by initializeClassroomSession if needed
    }
  }, [displayNextMessageInOverlay, addMessage]); // addMessage removed if not used here for error

  // New reusable function to initialize a classroom session
  const initializeClassroomSession = useCallback(async (sessionTopic, masteryDistribution = null) => {
    console.log("🎓 Initializing classroom session with topic:", sessionTopic);
    
    if (!sessionTopic || !sessionTopic.trim()) {
      console.error("Topic cannot be empty.");
      setError('Topic cannot be empty.');
      return Promise.reject(new Error("Topic cannot be empty")); // Indicate failure
    }

    setIsLoading(true);
    setError(null);
    setMessages([]); 
    setSessionId(null); // Clear previous session ID before starting a new one
    setRoster([]);      // Clear previous roster
    setIsDialogueOverlayActive(false); // Ensure overlay is hidden during new init

    if (abortControllerRef.current) {
      abortControllerRef.current.abort();
    }
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    const requestBody = { 
      topic: sessionTopic,
      mastery_distribution: masteryDistribution
    };

    try {
      console.log("🚀 Calling /classroom/start API...");
      const response = await fetch(`${API_BASE_URL}/classroom/start`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(requestBody),
        signal: signal
      });

      if (signal.aborted) {
        console.log('/classroom/start fetch aborted (during call).');
        throw new DOMException('Aborted', 'AbortError');
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        console.error('Failed to start classroom session API error:', errorData.detail);
        setError(errorData.detail || 'Failed to start classroom session');
        throw new Error(errorData.detail || 'Failed to start classroom session');
      }

      const data = await response.json();
      if (signal.aborted) {
        console.log('/classroom/start fetch aborted (after response.json()).');
        throw new DOMException('Aborted', 'AbortError');
      }

      console.log("✅ /classroom/start API success:", { sessionId: data.sessionId, rosterLength: data.roster?.length });
      setSessionId(data.sessionId);
      setRoster(data.roster || []);
      
      // Now fetch the initial lecture script using the new session ID and roster
      await fetchLectureScript(sessionTopic, data.sessionId, data.roster || []);
      setError(null); // Clear general errors if all good
      
    } catch (err) {
      if (err.name === 'AbortError') {
        console.log('⏹️ Classroom session initialization aborted.');
        // Don't setError here as it might be a rapid re-render, let the next attempt handle it.
      } else {
        console.error('❌ Error during classroom session initialization process:', err);
        setError(err.message || 'An error occurred starting the session.');
        // No need to add chat message here, error banner is primary
        setSessionId(null); 
      }
      throw err; // Re-throw to be caught by the caller in useEffect, which handles hasInitializedFromDiagnostic.current
    } finally {
      // Only set isLoading to false if this specific operation is completing (not aborted by a new one)
      if (abortControllerRef.current && signal === abortControllerRef.current.signal) {
         setIsLoading(false);
      }
      console.log("🏁 Classroom initialization sequence finished (isLoading set to false if current op).");
    }
  }, [fetchLectureScript]); // Removed roster, addMessage from deps as they are not directly used or set here

  // Remove auto-initialization logic entirely
  const searchParams = useSearchParams();
  
  // Add effect to handle diagnostic data from URL params
  useEffect(() => {
    const fromDiagnostic = searchParams.get('fromDiagnostic');
    const diagnosticTopic = searchParams.get('topic');
    const masteryDataParam = searchParams.get('masteryData');
    const accuracy = searchParams.get('accuracy');
    const conceptsCoveredParam = searchParams.get('conceptsCovered');
    
    if (
      fromDiagnostic === 'true' &&
      diagnosticTopic &&
      !sessionId && // Only if no session ID yet, meaning not initialized or previous attempt failed to set it
      !hasInitializedFromDiagnostic.current // And we haven't successfully started initialization for this diagnostic flow
    ) {
      console.log("🎯 Initializing classroom from diagnostic data (Attempting once per diagnostic flow)");
      // Mark that an attempt is being made for this diagnostic flow.
      // This helps prevent re-entry from rapid re-renders before sessionId is set.
      hasInitializedFromDiagnostic.current = true; 
      
      let masteryDistribution = null;
      let conceptsCovered = [];
      
      try {
        if (masteryDataParam) {
          masteryDistribution = JSON.parse(masteryDataParam);
        }
        if (conceptsCoveredParam) {
          conceptsCovered = JSON.parse(conceptsCoveredParam);
        }
      } catch (e) {
        console.warn("Failed to parse diagnostic data from URL params:", e);
        hasInitializedFromDiagnostic.current = false; // Reset flag if parsing failed
        return; // Exit if params are bad
      }
      
      setDiagnosticData({
        accuracy: parseInt(accuracy) || 0,
        conceptsCovered,
        fromDiagnostic: true
      });
      
      const readableTopic = diagnosticTopic.length > 100 
        ? diagnosticTopic.substring(0, 100).trim() + "..."
        : diagnosticTopic;
      
      initializeClassroomSession(readableTopic, masteryDistribution)
        .then(() => {
          // Successfully initiated (or at least the promise resolved without an error being thrown to here).
          // hasInitializedFromDiagnostic.current remains true from before the call.
          // Actual success is determined by sessionId and dialogue overlay appearing.
          console.log("initializeClassroomSession promise resolved.");
        })
        .catch((err) => {
          console.error("Error caught by diagnostic useEffect's .catch() block:", err); 
          if (err.name === 'AbortError') {
            console.warn("Diagnostic initialization attempt was aborted. Current sessionId:", sessionId);
            // If an abort happens and we haven't successfully set a session ID from *this* attempt,
            // it implies this specific attempt was cut short before completion.
            // Resetting the flag allows the effect to re-trigger initialization 
            // if it runs again and sessionId is still null (e.g. StrictMode remount).
            if (!sessionId) { 
              hasInitializedFromDiagnostic.current = false;
            }
          } else {
            // For non-AbortErrors, this indicates a more definitive failure of the attempt.
            console.error("Classroom initialization failed due to a non-abort error:", err.message);
            setError(err.message || "Classroom setup failed."); // Ensure user sees an error
            hasInitializedFromDiagnostic.current = false; // Allow a full retry if conditions reset (e.g., navigation)
          }
        });
    }
  }, [searchParams, sessionId, initializeClassroomSession, diagnosticData]); // Added diagnosticData to dependencies

  // Removed auto-initialization useEffect to prevent loops
  // Users can manually start classroom sessions from the form below

  const handleInputChange = (e) => {
    setInput(e.target.value);
  };

  const handleTopicChange = (e) => {
    setTopic(e.target.value);
  };

  const handleVideoPromptChange = (e) => {
    setVideoPrompt(e.target.value);
  };

  // Modified handleSubmit to use the new reusable function
  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!topic.trim()) {
      setError('Please enter a topic to discuss.');
      return;
    }
    // No need to set isLoading here, initializeClassroomSession will handle it.
    // No need to clear messages or error here, initializeClassroomSession will handle it.
    await initializeClassroomSession(topic);
      setTopic(''); // Clear topic input after attempting to start
  };

  // sendTurn function (for user's interactive messages AFTER lecture or for Q&A)
  // This function was not provided in the original prompt but is implied for Task 2.3
  // Assuming a structure similar to the old sendTurn, but it might need to be created or adapted.
  // For now, let's stub it. Task 2.3 ensures this is used for the chat input.
  const sendTurn = async (userMessage) => {
    if (!sessionId) {
      setError('No active classroom session. Please start a new topic or lecture first.');
      // Potentially add a user-facing message to an error component if not using addMessage for system errors
      console.error("sendTurn called without sessionId");
      return;
    }
    if (!userMessage.trim()) return;

    console.log("🗣️ sendTurn: Sending user message - ", userMessage.substring(0, 50) + "...");
    setIsLoading(true);
    // When a new user message is sent, we are no longer awaiting input for *that* specific exchange.
    // We will await input again *after* the AI's new script finishes.
    setIsAwaitingUserOverlayInput(false); 

    // Add user message to chat log (optional, if you have a visible chat log outside the overlay)
    // addMessage({ author: "You", text: userMessage, avatar_url: null }); 
    
    // No need to clear overlayInput here, it's cleared in handleOverlaySubmit after sendTurn completes or errors

    try {
      const res = await fetch(`${API_BASE_URL}/classroom/script`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ topic: userMessage, session_id: sessionId }), // userMessage becomes the new 'topic' for continuation
      });
      
      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || 'Failed to send message.');
      }
      
      const { turns } = await res.json();

      if (!turns || turns.length === 0) {
        console.warn("sendTurn: API returned no turns for user message.");
        setDisplayedMessageInfo({
          author: "System",
          text: "I couldn't generate a continuation for that. Try rephrasing or a different question?",
          avatar_url: roster.find(p => p.name === "Jiaran")?.avatarUrl
        });
        setTimeout(() => {
          if(isDialogueOverlayActive) setIsAwaitingUserOverlayInput(true); // Allow user to try again
        }, 2500);
        return;
      }

      console.log(`💬 sendTurn: Received ${turns.length} new turns from API.`);
      // KEY FIX: Update the main script state with the new turns
      setCurrentDialogueScriptTurns(turns);
      // Now display the first message of this new script.
      // displayNextMessageInOverlay will also set currentTurnInScriptIndex and currentMessageIndexInTurn to 0,0
      displayNextMessageInOverlay(turns, 0, 0, roster); 

    } catch (err) {
      console.error('Error in sendTurn:', err);
      setDisplayedMessageInfo({
        author: "System",
        text: `Sorry, I encountered an issue: ${err.message || 'Could not process your message.'} Please try again.`,
        avatar_url: null 
      });
      setTimeout(() => {
        if(isDialogueOverlayActive) setIsAwaitingUserOverlayInput(true); // Allow user to try again
      }, 2500);
    } finally {
      setIsLoading(false); 
      console.log("🏁 sendTurn: Processing finished.");
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
    // This log is crucial to see if the function is being called as expected
    console.log("🖱️ handleNextMessageOrInput called. Current state:", 
                { currentTurnInScriptIndex, currentMessageIndexInTurn, isAwaitingUserOverlayInput });

    if (isAwaitingUserOverlayInput) {
      console.log("handleNextMessageOrInput: Awaiting user input, doing nothing.");
      return; 
    }

    let nextMessageInTurnIdx = currentMessageIndexInTurn + 1;
    let nextTurnIdx = currentTurnInScriptIndex;

    // Ensure currentDialogueScriptTurns and currentTurnData are valid
    if (!currentDialogueScriptTurns || currentDialogueScriptTurns.length === 0 || !currentDialogueScriptTurns[nextTurnIdx]) {
        console.error("handleNextMessageOrInput: Invalid script or turn index.", { currentDialogueScriptTurns, nextTurnIdx });
        setIsAwaitingUserOverlayInput(true); // Fallback to user input if script is suddenly bad
        return;
    }
    const currentTurnData = currentDialogueScriptTurns[nextTurnIdx];
    const totalMessagesInCurrentTurn = 1 + (currentTurnData.students?.length || 0);

    if (nextMessageInTurnIdx >= totalMessagesInCurrentTurn) {
      nextTurnIdx++;
      nextMessageInTurnIdx = 0; 
    }

    if (nextTurnIdx < currentDialogueScriptTurns.length) {
      console.log(`Advancing to next message: Turn ${nextTurnIdx}, Message ${nextMessageInTurnIdx}`);
      // setCurrentTurnInScriptIndex and setCurrentMessageIndexInTurn are now set by displayNextMessageInOverlay
      displayNextMessageInOverlay(currentDialogueScriptTurns, nextTurnIdx, nextMessageInTurnIdx, roster);
    } else {
      console.log("🏁 End of current script reached. Setting up for user input.");
      setDisplayedMessageInfo(null); 
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
    <div className="classroom-background-overlay relative min-h-screen text-foreground flex flex-col items-center justify-start p-4 pt-16 md:pt-24">
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

      {/* Diagnostic Data Banner */}
      {diagnosticData && diagnosticData.fromDiagnostic && (
        <div className="w-full max-w-2xl mb-6 p-4 bg-primary/10 border border-primary/30 rounded-lg">
          <div className="flex items-center gap-2 mb-2">
            <CheckCircle2 className="h-5 w-5 text-primary" />
            <h3 className="font-semibold text-primary">Continuing from Diagnostic Quiz</h3>
          </div>
          <div className="text-sm text-muted-foreground">
            <p className="mb-1">
              Your quiz results: <span className="font-medium text-foreground">{diagnosticData.accuracy}% accuracy</span>
            </p>
            {diagnosticData.conceptsCovered && diagnosticData.conceptsCovered.length > 0 && (
              <p>
                Concepts covered: <span className="font-medium text-foreground">
                  {diagnosticData.conceptsCovered.slice(0, 3).join(', ')}
                  {diagnosticData.conceptsCovered.length > 3 && ` +${diagnosticData.conceptsCovered.length - 3} more`}
                </span>
              </p>
            )}
          </div>
        </div>
      )}

      {/* Initial Topic Input Area - Hidden when coming from diagnostic, displayed when no session and no overlay */}
      {!sessionId && !isDialogueOverlayActive && !diagnosticData?.fromDiagnostic && (
        <div className="w-full max-w-xl mt-8 p-6 bg-card text-card-foreground rounded-xl shadow-2xl border border-border flex flex-col items-center">
          <Users size={48} className="text-muted-foreground mb-4" />
          <p className="text-lg text-muted-foreground mb-6 text-center">
            What fascinating subject would you like to explore today?
          </p>
          {error && (
            <p className="text-destructive text-sm mb-3 p-3 bg-destructive/10 rounded-md w-full text-center">{error}</p>
          )}
          <form onSubmit={handleSubmit} className="w-full flex flex-col items-center gap-4">
            <input
              type="text"
              value={topic}
              onChange={handleTopicChange}
              placeholder="e.g., 'The Mysteries of the Cosmos' or 'The Art of Storytelling'..."
              className="w-full p-4 border border-border rounded-lg bg-background text-foreground placeholder-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary shadow-sm disabled:opacity-50 text-base"
              disabled={isLoading}
              autoFocus
            />
            <button 
              type="submit" 
              disabled={isLoading || !topic.trim()}
              className="w-full p-4 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90 transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-card disabled:opacity-50 shadow-md text-base font-semibold flex items-center justify-center gap-2"
            >
              {isLoading ? <><Loader2 className="h-5 w-5 animate-spin" /> Starting Discussion...</> : <><Sparkles className="h-5 w-5" /> Begin Lecture</>}
            </button>
          </form>
        </div>
      )}

      {/* Original Chat UI - Conditionally Hidden if Overlay is Active OR if it's initial state and no session */}
      {sessionId && !isDialogueOverlayActive && (
        // This section is now less likely to be seen with the current flow, 
        // as starting a session immediately tries to launch the overlay.
        // It could serve as a fallback or if we re-introduce a way to see the old chat log.
        <div className="bg-card text-card-foreground rounded-xl shadow-2xl w-full max-w-2xl border border-border flex flex-col" style={{height: '70vh'}}>
          <div ref={chatContainerRef} className="flex-grow p-6 space-y-6 overflow-y-auto scrollbar-thin scrollbar-thumb-secondary scrollbar-track-transparent">
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
            {/* Input for the old chat - might be removed if this view is fully deprecated */}
            <form onSubmit={handleMessageSubmit} className="flex items-center gap-3">
                <input
                  type="text"
                  value={input}
                  onChange={handleInputChange}
                  placeholder="Type a question (fallback chat)..."
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