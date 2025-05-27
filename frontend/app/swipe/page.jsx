'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import SwipeCards from '@/components/SwipeCards';
import Link from 'next/link';
import { Loader2, AlertTriangle, BarChart3, Brain } from 'lucide-react';

export default function SwipePage() {
  const router = useRouter();
  const [questions, setQuestions] = useState([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [userAnswers, setUserAnswers] = useState([]);

  useEffect(() => {
    const fetchQuestions = async () => {
      setIsLoading(true);
      setError(null);
      const uploadedContent = sessionStorage.getItem('uploadedContent');

      if (!uploadedContent) {
        console.log('No uploaded content found, redirecting to upload page.');
        router.push('/upload');
        return;
      }

      try {
        const response = await fetch('http://localhost:8000/generate-diagnostic', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ content: uploadedContent }),
        });

        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: response.statusText }));
          console.error('Error fetching diagnostic questions:', errorData);
          setError(errorData.detail || 'Failed to load diagnostic questions. Please try uploading again.');
          setQuestions([]);
        } else {
          const data = await response.json();
          if (data && data.questions && data.questions.length > 0) {
            setQuestions(data.questions);
          } else {
            setError('No specific questions could be generated for this content. Displaying general knowledge questions.');
            setQuestions(data.questions || []);
            if (!data.questions || data.questions.length === 0) {
              setError("Couldn't generate questions. Try uploading different content or check server logs.");
            }
          }
        }
      } catch (err) {
        console.error('Network or parsing error fetching questions:', err);
        setError('An error occurred while fetching questions. Please check your connection and try again.');
        setQuestions([]);
      } finally {
        setIsLoading(false);
      }
    };

    fetchQuestions();
  }, [router]);

  const handleAnswer = (concept, isCorrect) => {
    setUserAnswers(prevAnswers => [...prevAnswers, { concept, isCorrect }]);
  };

  const allQuestionsAnswered = questions.length > 0 && userAnswers.length === questions.length;

  const correctAnswersCount = userAnswers.filter(ans => ans.isCorrect).length;
  const totalAnswered = userAnswers.length;
  const accuracy = totalAnswered > 0 ? Math.round((correctAnswersCount / totalAnswered) * 100) : 0;

  const conceptsCovered = [...new Set(questions.map(q => q.concept))];

  if (isLoading) {
    return (
      <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-center p-4">
        <Loader2 className="h-12 w-12 animate-spin text-primary mb-4" />
        <p className="text-lg text-muted-foreground">Generating your personalized quiz...</p>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-background text-foreground flex flex-col items-center justify-start p-4 pt-16 md:pt-24">
      <div className="absolute top-6 left-6">
        <Link href="/" className="text-primary hover:underline flex items-center gap-2">
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" className="lucide lucide-arrow-left"><path d="m12 19-7-7 7-7"/><path d="M19 12H5"/></svg>
          Back to Home
        </Link>
      </div>
      
      <header className="mb-8 text-center">
        <div className="flex items-center justify-center gap-2 mb-2">
          <Brain className="h-8 w-8 text-primary" />
          <h1 className="text-3xl md:text-4xl font-bold text-foreground">Diagnostic Quiz</h1>
        </div>
        <p className="text-md text-muted-foreground max-w-xl">
          Test your understanding with these swipe-style questions based on your uploaded material.
        </p>
      </header>

      {error && !allQuestionsAnswered && (
        <div className="bg-destructive/10 text-destructive p-4 rounded-lg border border-destructive/30 w-full max-w-md mb-6 flex items-start gap-3">
          <AlertTriangle className="h-5 w-5 mt-0.5 text-destructive" />
          <div>
            <h3 className="font-semibold">Error Loading Questions</h3>
            <p className="text-sm">{error}</p>
            {(questions.length === 0 || questions.every(q => q.concept === "General AI Knowledge")) && (
              <Link 
                href="/upload" 
                className="mt-2 inline-block text-sm text-primary hover:underline font-medium"
              >
                Try uploading different content?
              </Link>
            )}
          </div>
        </div>
      )}

      {(questions.length > 0 && !allQuestionsAnswered) && (
        <SwipeCards questions={questions} onAnswer={handleAnswer} />
      )}

      {allQuestionsAnswered && (
        <div className="bg-card text-card-foreground p-8 rounded-xl shadow-2xl w-full max-w-md text-center border border-border">
          <BarChart3 size={48} className="text-primary mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-3">Quiz Complete!</h2>
          <p className="text-muted-foreground mb-6">
            You answered {totalAnswered} questions with {accuracy}% accuracy.
          </p>
          <div className="mb-6">
            <h4 className="text-lg font-medium mb-2">Concepts Covered:</h4>
            {conceptsCovered.length > 0 ? (
              <ul className="space-y-1 text-sm text-muted-foreground list-inside list-disc">
                {conceptsCovered.map(concept => <li key={concept}>{concept}</li>)}
              </ul>
            ) : (
              <p className="text-sm text-muted-foreground">No specific concepts were identified.</p>
            )}
          </div>
          <Link 
            href="/upload" 
            className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold py-2 px-6 rounded-lg transition-colors shadow-md"
          >
            Upload New Material
          </Link>
        </div>
      )}

      {!isLoading && questions.length === 0 && !error && (
         <div className="bg-card text-card-foreground p-8 rounded-xl shadow-2xl w-full max-w-md text-center border border-border">
          <AlertTriangle size={48} className="text-amber-500 mx-auto mb-4" />
          <h2 className="text-2xl font-semibold mb-3">No Questions Available</h2>
          <p className="text-muted-foreground mb-6">
            We couldn't find or generate any questions based on the provided content. This might be due to the content format or a temporary issue.
          </p>
          <Link 
            href="/upload" 
            className="bg-primary text-primary-foreground hover:bg-primary/90 font-semibold py-2 px-6 rounded-lg transition-colors shadow-md"
          >
            Try Uploading Again
          </Link>
        </div>
      )}

    </div>
  );
} 