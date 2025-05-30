'use client';

import { useEffect, useState, useCallback } from 'react';
import { useRouter } from 'next/navigation';
import SwipeCards from '@/components/SwipeCards';
import MasteryChart from '@/components/MasteryChart';
import Link from 'next/link';
import { Loader2, AlertTriangle, BarChart3, Brain, RotateCw } from 'lucide-react';

const API_BASE_URL = 'http://localhost:8000';
const USER_ID_FOR_QUIZ = "testUser123";
const MAX_QUESTIONS_IN_SESSION = 20;
const BATCH_SIZE = 5;

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

  const fetchInitialBatch = useCallback(async () => {
    console.log("Fetching initial batch...");
      setIsLoading(true);
      setError(null);
      const uploadedContent = sessionStorage.getItem('uploadedContent');

      if (!uploadedContent) {
        console.log('No uploaded content found, redirecting to upload page.');
        router.push('/upload');
        return;
      }

      try {
      const response = await fetch(`${API_BASE_URL}/generate-diagnostic`, {
          method: 'POST',
        headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ content: uploadedContent }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
        setError(errorData.detail || 'Failed to load initial questions.');
        setCurrentBatchQuestions([]);
        } else {
          const data = await response.json();
          if (data && data.questions && data.questions.length > 0) {
          setCurrentBatchQuestions(data.questions);
          setAnsweredInBatchCount(0);
          } else {
          setError('No questions generated for this content. Try different material.');
          setCurrentBatchQuestions([]);
        }
      }
    } catch (err) {
      console.error('Error fetching initial questions:', err);
      setError('An error occurred while fetching initial questions.');
      setCurrentBatchQuestions([]);
    } finally {
      setIsLoading(false);
    }
  }, [router]);

  const fetchNextAdaptiveBatch = useCallback(async () => {
    // Prevent multiple simultaneous batch fetches
    if (isLoading || totalQuestionsAnsweredInSession >= MAX_QUESTIONS_IN_SESSION) {
      console.log("Already loading or max questions reached, not fetching next batch");
      if (totalQuestionsAnsweredInSession >= MAX_QUESTIONS_IN_SESSION) {
        setIsQuizOver(true);
      }
      return;
    }
    console.log("Fetching next adaptive batch...");
    setIsLoading(true);
    setError(null);
    try {
      console.log(`Calling API: ${API_BASE_URL}/next-question-batch/${USER_ID_FOR_QUIZ}?count=${BATCH_SIZE}`);
      const response = await fetch(`${API_BASE_URL}/next-question-batch/${USER_ID_FOR_QUIZ}?count=${BATCH_SIZE}`);
      
      console.log("API response status:", response.status);
      
      if (!response.ok) {
        const responseText = await response.text();
        console.error("Error response from next-question-batch:", responseText);
        
        let errorDetail;
        try {
          const errorData = JSON.parse(responseText);
          errorDetail = errorData.detail || response.statusText;
        } catch (e) {
          errorDetail = responseText || response.statusText;
        }
        
        setError(errorDetail || 'Failed to load next batch of questions.');
        setIsQuizOver(true);
        setCurrentBatchQuestions([]); 
      } else {
        const data = await response.json();
        console.log("Next batch data:", data);
        
        if (data && data.length > 0) {
          console.log(`Successfully fetched ${data.length} new questions`);
          setCurrentBatchQuestions(data);
          setAnsweredInBatchCount(0); // Reset batch count to 0 after getting new questions
        } else {
          console.warn("API returned empty question set");
          setError('No more adaptive questions available for your profile.');
          setIsQuizOver(true);
          setCurrentBatchQuestions([]);
          }
        }
      } catch (err) {
      console.error('Error fetching next adaptive batch:', err);
      setError('An error occurred while fetching adaptive questions.');
      setIsQuizOver(true);
      setCurrentBatchQuestions([]);
      } finally {
        setIsLoading(false);
      }
  }, [totalQuestionsAnsweredInSession, isLoading]);

  useEffect(() => {
    fetchInitialBatch();
  }, [fetchInitialBatch]);

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
      batchSize: BATCH_SIZE,
      nextTotalAnswered,
      MAX_QUESTIONS_IN_SESSION,
      currentBatchQuestions: currentBatchQuestions.length
    });

    // Update counters after API calls to ensure synchronization
    setAnsweredInBatchCount(nextAnsweredInBatch);
    setTotalQuestionsAnsweredInSession(nextTotalAnswered);

    // Determine next action based on updated counters
    if (nextTotalAnswered >= MAX_QUESTIONS_IN_SESSION) {
      console.log("Quiz over - reached max questions");
      setIsQuizOver(true);
    } else if (nextAnsweredInBatch >= Math.min(currentBatchQuestions.length, BATCH_SIZE)) {
      // Only fetch next batch if we've answered all questions in current batch
      // and we're not already loading (the useCallback dependency will check this)
      console.log("Fetching next batch");
      fetchNextAdaptiveBatch();
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

  if (isLoading && currentBatchQuestions.length === 0 && !isQuizOver) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-lg text-muted-foreground">Generating your personalized quiz...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-start p-4 pt-16 md:pt-24 w-full">
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
              {uniqueConceptsCoveredInSession.length > 0 && (
              <div className="mb-6">
                <h4 className="text-lg font-medium mb-2">Concepts Covered:</h4>
                  <ul className="space-y-1 text-sm text-muted-foreground list-inside list-disc text-left max-h-32 overflow-y-auto">
                    {uniqueConceptsCoveredInSession.map(concept => <li key={concept}>{concept}</li>)}
                  </ul>
                </div>
                )}
              <Link 
                href="/upload" 
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold py-2.5 px-6 rounded-lg transition-colors shadow-md text-base"
              >
                Start a New Quiz
              </Link>
            </div>
          )}
          
          {!isLoading && currentBatchQuestions.length === 0 && !error && !isQuizOver && (
             <div className="bg-card text-card-foreground p-8 rounded-xl shadow-2xl w-full max-w-xl mx-auto text-center border border-border">
              <AlertTriangle size={48} className="text-amber-500 mx-auto mb-4" />
              <h2 className="text-2xl font-semibold mb-3">No Questions Generated</h2>
              <p className="text-muted-foreground mb-6">
                We couldn't generate questions for the uploaded content. Please try different material.
              </p>
              <Link 
                href="/upload" 
                className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold py-2 px-6 rounded-lg transition-colors shadow-md"
              >
                Upload New Content
              </Link>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 