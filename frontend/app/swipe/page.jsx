'use client';

import { useEffect, useState, useCallback, useRef } from 'react';
import { useRouter } from 'next/navigation';
import SwipeCards from '@/components/SwipeCards';
import MasteryChart from '@/components/MasteryChart';
import Link from 'next/link';
import { Loader2, AlertTriangle, BarChart3, Brain, RotateCw } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';
const USER_ID_FOR_QUIZ = "testUser123";
const MAX_QUESTIONS_IN_SESSION = 10;

export default function SwipePage() {
  const router = useRouter();
  
  const [currentBatchQuestions, setCurrentBatchQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  
  const [answeredInBatchCount, setAnsweredInBatchCount] = useState(0);
  const [totalQuestionsAnsweredInSession, setTotalQuestionsAnsweredInSession] = useState(0);
  const [sessionUserAnswers, setSessionUserAnswers] = useState([]);
  const [isQuizOver, setIsQuizOver] = useState(false);
  const [currentConceptForSummary, setCurrentConceptForSummary] = useState("");
  const [masteryHistory, setMasteryHistory] = useState([]);

  // Add ref to prevent duplicate API calls
  const hasInitialized = useRef(null);
  const abortControllerRef = useRef(null);

  // Debug logging for state changes
  console.log("SwipePage render state:", {
    isLoading,
    currentBatchQuestionsLength: currentBatchQuestions.length,
    error,
    isQuizOver,
    hasInitialized: hasInitialized.current
  });

  useEffect(() => {
    // Removed automatic classroom redirection logic
    // Quiz will now stay on the results page after completion
  }, [isQuizOver, router]);

  const fetchInitialBatch = useCallback(async () => {
    const uploadedContent = sessionStorage.getItem('uploadedContent');

    if (!uploadedContent) {
      console.log('No uploaded content found, redirecting to upload page.');
      router.push('/upload');
      return;
    }

    const contentKey = btoa(uploadedContent.substring(0, 100)).substring(0, 20);

    // If this specific contentKey has already been successfully processed AND questions are loaded, skip.
    // This check is more for subsequent calls/re-renders after a successful load,
    // rather than the StrictMode double-useEffect scenario.
    if (hasInitialized.current === contentKey && currentBatchQuestions.length > 0) {
      console.log("Content already processed and questions exist, skipping fetch.");
      return;
    }
    // If isLoading is true, it means a fetch is already in progress.
    // The AbortController will handle the old one if this new call proceeds.
    // Avoids queueing up multiple setIsLoading(true) -> setIsLoading(false) if not careful.
    // For now, let new calls proceed and abort old ones.

    console.log(`Fetching initial batch for contentKey: ${contentKey}. isLoading: ${isLoading}`);
    setIsLoading(true);
    setError(null);
    // Do not clear currentBatchQuestions here to avoid flicker if questions are successfully fetched.

    if (abortControllerRef.current) {
      abortControllerRef.current.abort(); // Abort previous request
      console.log("Aborted previous fetchInitialBatch request.");
    }
    abortControllerRef.current = new AbortController();
    const signal = abortControllerRef.current.signal;

    try {
      console.log("Initiating API call to /generate-diagnostic");
      const response = await fetch(`${API_BASE_URL}/generate-diagnostic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ content: uploadedContent }),
        signal: signal,
      });

      if (signal.aborted) {
        console.log('Fetch aborted after API call, before processing response.');
        return; // setIsLoading(false) will be handled by finally
      }

      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        setError(errorData.detail || 'Failed to load initial questions.');
        setCurrentBatchQuestions([]);
        hasInitialized.current = null; // Error occurred, allow this content to be fully retried.
        console.error('API response not OK:', errorData.detail || response.statusText);
      } else {
        const data = await response.json();
        if (signal.aborted) {
          console.log('Fetch aborted after response.json().');
          return; // setIsLoading(false) will be handled by finally
        }

        if (data && data.questions && data.questions.length > 0) {
          console.log(`Successfully fetched ${data.questions.length} questions.`);
          setCurrentBatchQuestions(data.questions);
          setAnsweredInBatchCount(0);
          setError(null); // Clear any previous error state
          hasInitialized.current = contentKey; // Mark this content as successfully processed
        } else {
          console.log('API call successful, but no questions were generated.');
          setError('No questions generated for this content. Please try different material.');
          setCurrentBatchQuestions([]);
          hasInitialized.current = contentKey; // Mark this content as processed (even if no questions)
        }
      }
    } catch (err) {
      if (err.name === 'AbortError' || signal.aborted) {
        console.log('Fetch operation was aborted (in catch block).');
      } else {
        console.error('Error fetching initial questions:', err);
        setError('An error occurred while fetching initial questions.');
        setCurrentBatchQuestions([]);
        hasInitialized.current = null; // Network or other error, allow this content to be fully retried.
      }
    } finally {
      // Only set isLoading to false if this specific fetch operation is the one completing
      // and hasn't been superseded by a new one (which would have its own AbortController signal).
      if (abortControllerRef.current && abortControllerRef.current.signal === signal) {
        setIsLoading(false);
        console.log("fetchInitialBatch finally block: setIsLoading(false) for the completed/aborted operation.");
      } else if (!abortControllerRef.current && signal.aborted){
        // This case handles if the controller was nulled by unmount cleanup and this was the aborted call
         setIsLoading(false);
         console.log("fetchInitialBatch finally block: setIsLoading(false) for operation aborted by unmount/cleanup.");
      } else {
         console.log("fetchInitialBatch finally block: setIsLoading(false) skipped as a new fetch might have started or this was superseded.");
      }
    }
  }, [router, isLoading, currentBatchQuestions.length]); // Added isLoading and currentBatchQuestions.length to deps for the guard condition.

  useEffect(() => {
    const uploadedContent = sessionStorage.getItem('uploadedContent');
    if (uploadedContent) {
      console.log("useEffect (mount/content change): Found uploadedContent, calling fetchInitialBatch. Current hasInitialized: ", hasInitialized.current);
      fetchInitialBatch();
    } else {
      console.log('useEffect (mount/content change): No content in sessionStorage, redirecting to /upload.');
      router.push('/upload');
    }

    return () => {
      console.log("useEffect (unmount/before re-run): Cleanup. Aborting fetch if active.");
      if (abortControllerRef.current) {
        abortControllerRef.current.abort();
        abortControllerRef.current = null; // Important to nullify for the finally block logic in fetchInitialBatch
      }
    };
  }, []); // Keep `[]` for mount/unmount. Re-fetching for *new* content is handled by navigating away and back.

  const handleAnswer = async (question, userAnswer) => {
    // Prevent processing answers during loading state or when quiz is over
    if (isLoading || isQuizOver) return;
    
    console.log("handleAnswer called with:", { question, userAnswer });
    const isCorrect = userAnswer === question.correct_answer;
    const answerOutcome = isCorrect ? 'correct' : 'incorrect';
    
    console.log("Answer evaluation:", { 
      isCorrect, 
      userAnswer,
      correct_answer: question.correct_answer,
      concept: question.concept
    });
    
    // Batch state updates to reduce re-renders
    const conceptDisplayTitle = (question.concept && typeof question.concept === 'string') 
      ? question.concept.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) 
      : 'Concept Details Missing';
    
    // Update state in batches to reduce flickering
    setCurrentConceptForSummary(conceptDisplayTitle);
    
    // Calculate next state values before updating state
    const nextAnsweredInBatch = answeredInBatchCount + 1;
    const nextTotalAnswered = totalQuestionsAnsweredInSession + 1;
    
    // Add the answer to session history
    setSessionUserAnswers(prev => [...prev, { 
      concept: question.concept, 
      isCorrect, 
      questionText: question.question 
    }]);
    
    try {
      console.log(`Sending answer for concept ${question.concept}: ${answerOutcome}, difficulty: ${question.difficulty}`);
      const response = await fetch(`${API_BASE_URL}/diagnostic-response`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          user_id: USER_ID_FOR_QUIZ,
          concept: question.concept,
          response: answerOutcome,
          difficulty: question.difficulty || 0.5, // Include question difficulty, default to 0.5 if not available
        }),
      });
      
      if (!response.ok) {
        console.error("Error response from /diagnostic-response:", await response.text());
      } else {
        const responseData = await response.json();
        console.log("Diagnostic response success (raw object):", responseData);
        console.log("Value of responseData.updated_belief:", responseData.updated_belief);
        console.log("Type of responseData.updated_belief:", typeof responseData.updated_belief);
        if (responseData.updated_belief) {
            console.log("Is responseData.updated_belief an array?:", Array.isArray(responseData.updated_belief));
            if (Array.isArray(responseData.updated_belief) && responseData.updated_belief.length > 0) {
                console.log("First element of responseData.updated_belief:", responseData.updated_belief[0]);
            }
        }
        
        // Add the updated belief distribution to the history chart
        setMasteryHistory(prev => [
          ...prev,
          {
            concept: question.concept,
            belief: responseData.updated_belief,
          }
        ]);
      }
    } catch (err) {
      console.error('Error submitting diagnostic answer:', err);
    }
    
    console.log("Navigation logic:", {
      nextAnsweredInBatch,
      batchSize: MAX_QUESTIONS_IN_SESSION,
      nextTotalAnswered,
      MAX_QUESTIONS_IN_SESSION,
      currentBatchQuestions: currentBatchQuestions.length
    });

    // Update counters after API calls to ensure synchronization
    setAnsweredInBatchCount(nextAnsweredInBatch);
    setTotalQuestionsAnsweredInSession(nextTotalAnswered);

    // Determine next action based on updated counters
    if (nextTotalAnswered >= MAX_QUESTIONS_IN_SESSION) {
      console.log("Quiz over - reached max questions (10)");
      setIsQuizOver(true);
    } else if (nextAnsweredInBatch >= currentBatchQuestions.length && currentBatchQuestions.length > 0) {
      // This condition implies all questions from the initial batch are answered, but we haven't hit MAX_QUESTIONS_IN_SESSION.
      // This should ideally not happen if initial batch fetches MAX_QUESTIONS_IN_SESSION.
      // If it does, it means initial fetch provided fewer than 10 questions. End quiz.
      console.log("All questions from initial batch answered. Ending quiz as no more fetching logic.");
      setIsQuizOver(true);
    }
  };
  
  // Fix accuracy calculation to ensure we don't get values over 100%
  const correctAnswersInSession = sessionUserAnswers.filter(ans => ans.isCorrect).length;
  const accuracy = totalQuestionsAnsweredInSession > 0 
    ? Math.min(100, Math.round((correctAnswersInSession / totalQuestionsAnsweredInSession) * 100)) 
    : 0;

  console.log("Accuracy calculation:", {
    correctAnswersInSession,
    totalQuestionsAnsweredInSession,
    accuracy,
    sessionUserAnswers
  });
  
  const uniqueConceptsCoveredInSession = [...new Set(
    sessionUserAnswers.map(q => 
      (q.concept && typeof q.concept === 'string') 
        ? q.concept.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) 
        : 'Unknown Concept'
    )
  )];

  // Helper function to create classroom URL with diagnostic data
  const createClassroomUrl = () => {
    const uploadedContent = sessionStorage.getItem('uploadedContent');
    if (!uploadedContent || !isQuizOver) return '/classroom';
    
    // Prepare mastery data from diagnostic results
    const masteryData = {};
    sessionUserAnswers.forEach(answer => {
      if (answer.concept) {
        if (!masteryData[answer.concept]) {
          masteryData[answer.concept] = { correct: 0, total: 0 };
        }
        masteryData[answer.concept].total++;
        if (answer.isCorrect) {
          masteryData[answer.concept].correct++;
        }
      }
    });

    // Convert mastery history to a simplified format for the classroom
    const masteryDistribution = {};
    masteryHistory.forEach(entry => {
      if (entry.concept && entry.belief) {
        masteryDistribution[entry.concept] = entry.belief;
      }
    });

    // Create URL with query parameters
    const params = new URLSearchParams({
      fromDiagnostic: 'true',
      topic: uploadedContent.substring(0, 200), // First 200 chars as topic
      accuracy: accuracy.toString(),
      conceptsCovered: JSON.stringify(uniqueConceptsCoveredInSession),
      masteryData: JSON.stringify(masteryDistribution)
    });

    return `/classroom?${params.toString()}`;
  };

  if (isLoading && currentBatchQuestions.length === 0 && !isQuizOver) {
    return (
      <div 
        className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-4 relative"
        style={{
          backgroundImage: "url('/assets/diagnostic-hallway.png')",
          backgroundSize: 'cover',
          backgroundPosition: 'center',
          backgroundRepeat: 'no-repeat',
          backgroundBlendMode: 'overlay',
          backgroundColor: 'rgba(0, 0, 0, 0.3)'
        }}
      >
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-lg text-muted-foreground">Generating your personalized quiz...</p>
      </div>
    );
  }

  return (
    <div 
      className="min-h-screen bg-background text-foreground flex flex-col items-center justify-start p-4 pt-16 md:pt-24 w-full relative"
      style={{
        backgroundImage: "url('/assets/diagnostic-hallway.png')",
        backgroundSize: 'cover',
        backgroundPosition: 'center',
        backgroundRepeat: 'no-repeat',
        backgroundBlendMode: 'overlay',
        backgroundColor: 'rgba(0, 0, 0, 0.3)'
      }}
    >
      <div className="absolute top-6 left-6">
        <Link href="/upload" className="text-primary hover:underline flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-arrow-left"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
          Upload New Content
        </Link>
      </div>
      
      <header className="mb-6 md:mb-8 text-center w-full max-w-2xl">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Brain className="h-8 w-8 text-primary" />
          <h1 className="text-3xl md:text-4xl font-bold text-foreground">Diagnostic Quiz</h1>
        </div>
        {!isQuizOver && (
           <p className="text-md text-muted-foreground">
             Question {Math.min(totalQuestionsAnsweredInSession + 1, MAX_QUESTIONS_IN_SESSION)} of {MAX_QUESTIONS_IN_SESSION}
             {currentBatchQuestions.length > 0 && currentConceptForSummary && 
              <span className="block text-sm">Current concept: <strong>{currentConceptForSummary}</strong></span>}
           </p>
        )}
      </header>

      {error && !isQuizOver && currentBatchQuestions.length === 0 && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/30 w-full max-w-md mb-6 flex flex-col items-center gap-3 text-center">
          <AlertTriangle className="h-8 w-8 text-destructive" />
          <h3 className="font-semibold">Could Not Load Quiz</h3>
            <p className="text-sm">{error}</p>
          <button 
            onClick={fetchInitialBatch} 
            className="mt-2 bg-destructive/20 hover:bg-destructive/30 text-destructive font-medium py-2 px-4 rounded-lg flex items-center gap-2"
          >
            <RotateCw className="h-4 w-4"/> Retry Initial Load
          </button>
          <Link href="/upload" className="mt-1 text-sm text-primary hover:underline">Or upload different content</Link>
        </div>
      )}

      {/* Main content area with improved layout */}
      <div className="w-full max-w-7xl mx-auto flex flex-col md:flex-row md:gap-8 items-stretch justify-center">
        {/* Left side: Mastery Chart */}
        <div className="md:w-2/5 lg:w-1/3 order-2 md:order-1 w-full md:sticky md:top-24">
          {masteryHistory.length > 0 ? (
            <MasteryChart history={masteryHistory} />
          ) : (
            <div className="bg-card border border-border rounded-lg p-6 mt-6 w-full max-w-md mx-auto h-[250px] flex items-center justify-center text-muted-foreground dark:bg-gray-800 dark:text-gray-400">
              Answer questions to see belief distributions
            </div>
          )}
        </div>
        
        {/* Right side: Questions and results */}
        <div className="md:w-3/5 lg:w-2/3 order-1 md:order-2 flex flex-col items-center">
          {!isQuizOver && currentBatchQuestions.length > 0 && (
            <div className="w-full max-w-xl mx-auto">
              <SwipeCards 
                  questions={currentBatchQuestions} 
                  onAnswer={handleAnswer} 
              />
            </div>
          )}
          
          {isQuizOver && (
            <div className="bg-card text-card-foreground p-6 md:p-8 rounded-xl shadow-2xl w-full max-w-xl mx-auto text-center border border-border">
              <BarChart3 size={48} className="text-primary mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-3">Quiz Session Complete!</h2>
              <p className="text-muted-foreground mb-4">
                You answered {totalQuestionsAnsweredInSession} questions with {accuracy}% accuracy.
              </p>
              <p className="text-md text-muted-foreground mb-4 italic">
                Great job! You can start a new quiz or explore other content.
              </p>
              {uniqueConceptsCoveredInSession.length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-medium mb-2">Concepts Covered:</h4>
                  <ul className="space-y-1 text-sm text-muted-foreground list-inside list-disc text-left max-h-32 overflow-y-auto">
                    {uniqueConceptsCoveredInSession.map(concept => <li key={concept}>{concept}</li>)}
                  </ul>
                </div>
                )}
              <div className="flex flex-col sm:flex-row gap-3 justify-center">
                <Link 
                  href="/upload" 
                  className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold py-2.5 px-6 rounded-lg transition-colors shadow-md text-base"
                >
                  Start a New Quiz
                </Link>
                <Link 
                  href={createClassroomUrl()} 
                  className="bg-secondary text-secondary-foreground hover:bg-secondary/90 font-semibold py-2.5 px-6 rounded-lg transition-colors shadow-md text-base"
                >
                  Visit Classroom
                </Link>
              </div>
            </div>
          )}
          
          {!isLoading && currentBatchQuestions.length === 0 && !error && !isQuizOver && (
             <div className="bg-card text-card-foreground p-8 rounded-xl shadow-2xl w-full max-w-xl mx-auto text-center border border-border">
              <AlertTriangle size={48} className="text-amber-500 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-3">No Questions Generated</h2>
              <p className="text-muted-foreground mb-6">
                We couldn't generate questions for the uploaded content. Please try different material.
              </p>
              <div className="flex flex-col gap-3">
                <button 
                  onClick={() => {
                    hasInitialized.current = null; // Reset to allow retry
                    fetchInitialBatch();
                  }}
                  className="bg-secondary text-secondary-foreground hover:bg-secondary/90 font-medium py-2 px-4 rounded-lg flex items-center justify-center gap-2"
                >
                  <RotateCw className="h-4 w-4"/> Retry Generation
                </button>
                <Link 
                  href="/upload" 
                  className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold py-2 px-6 rounded-lg transition-colors shadow-md"
                >
                  Upload New Content
                </Link>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 