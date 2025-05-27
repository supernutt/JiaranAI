'use client';

import { useState, useEffect } from 'react';
import SwipeCards from '../../components/SwipeCards';
import Link from 'next/link';

export default function SwipePage() {
  const [questions, setQuestions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState({ correct: 0, total: 0 });

  useEffect(() => {
    const fetchDiagnosticQuestions = async () => {
      try {
        // Check if we have content from the upload page stored in sessionStorage
        const uploadedContent = sessionStorage.getItem('uploadedContent');
        
        // For demonstration, we'll use a mock topic if no uploaded content
        const mockTopic = "Artificial intelligence is the simulation of human intelligence processes by machines, especially computer systems. These processes include learning (the acquisition of information and rules for using the information), reasoning (using rules to reach approximate or definite conclusions) and self-correction.";
        
        // Use uploaded content if available, otherwise use mock topic
        const contentToUse = uploadedContent || mockTopic;
        
        const response = await fetch('http://localhost:8000/generate-diagnostic', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content: contentToUse }),
        });

        if (!response.ok) {
          throw new Error(`Server responded with status ${response.status}`);
        }

        const data = await response.json();
        setQuestions(data.questions);
        setLoading(false);
      } catch (err) {
        console.error('Error fetching diagnostic questions:', err);
        setError(err.message);
        setLoading(false);
        
        // Fallback to mock data in case of error
        setQuestions([
          {
            concept: "Definition of AI",
            question: "Which statement best defines artificial intelligence?",
            option_a: "The simulation of human intelligence processes by machines",
            option_b: "Robots with physical capabilities matching humans",
            correct_answer: "a",
            explanation: "AI refers to the simulation of human intelligence in machines, not necessarily physical robots."
          },
          {
            concept: "AI Processes",
            question: "Which is NOT one of the core processes of AI mentioned in the text?",
            option_a: "Learning",
            option_b: "Creativity",
            correct_answer: "b",
            explanation: "The text mentions learning, reasoning, and self-correction as the core processes, not creativity."
          },
          {
            concept: "Purpose of AI",
            question: "According to the description, what is the primary purpose of AI?",
            option_a: "To replace human workers",
            option_b: "To simulate human intelligence processes",
            correct_answer: "b",
            explanation: "The text clearly states that AI is about simulating human intelligence processes, not necessarily replacing humans."
          }
        ]);
      }
    };

    fetchDiagnosticQuestions();
  }, []);

  const handleAnswer = (concept, isCorrect) => {
    console.log(`Question about ${concept}: ${isCorrect ? 'Correct' : 'Incorrect'}`);
    setStats(prev => ({
      correct: prev.correct + (isCorrect ? 1 : 0),
      total: prev.total + 1
    }));
  };

  return (
    <div className="flex flex-col min-h-screen bg-zinc-950 text-white">
      <header className="bg-zinc-900 p-4 shadow-md">
        <div className="container mx-auto flex justify-between items-center">
          <h1 className="text-2xl font-bold">Diagnostic Quiz</h1>
          <Link href="/" className="text-violet-400 hover:text-violet-300">
            Home
          </Link>
        </div>
      </header>

      <main className="flex-grow flex flex-col items-center justify-center p-4">
        {loading ? (
          <div className="flex flex-col items-center justify-center p-4">
            <div className="w-16 h-16 border-t-4 border-violet-500 border-solid rounded-full animate-spin"></div>
            <p className="mt-4 text-lg text-zinc-300">Loading questions...</p>
          </div>
        ) : error && questions.length === 0 ? (
          <div className="flex flex-col items-center justify-center p-4">
            <div className="max-w-md p-6 bg-red-900/20 border border-red-800 rounded-lg">
              <h2 className="text-xl font-bold text-red-400 mb-2">Error</h2>
              <p className="text-zinc-300">{error}</p>
              <p className="mt-4 text-zinc-400">
                Please make sure the backend server is running at http://localhost:8000
                and your OpenAI API key is correctly configured.
              </p>
            </div>
          </div>
        ) : (
          <>
            {questions.length > 0 ? (
              <>
                <SwipeCards 
                  questions={questions} 
                  onAnswer={handleAnswer} 
                />
                
                {stats.total > 0 && (
                  <div className="mt-6 p-4 bg-zinc-800 rounded-lg shadow-sm">
                    <h3 className="font-medium text-zinc-200 mb-2">Progress</h3>
                    <div className="w-full bg-zinc-700 h-4 rounded-full mb-2 overflow-hidden">
                      <div 
                        className="bg-violet-600 h-4 rounded-full" 
                        style={{ width: `${Math.round((stats.correct / stats.total) * 100)}%` }}
                      ></div>
                    </div>
                    <p className="text-sm text-zinc-400">
                      {stats.correct} correct out of {stats.total} answered
                      {stats.total > 0 && ` (${Math.round((stats.correct / stats.total) * 100)}%)`}
                    </p>
                  </div>
                )}
              </>
            ) : (
              <p className="text-zinc-400">No questions available. Try refreshing the page.</p>
            )}
          </>
        )}
      </main>
    </div>
  );
} 