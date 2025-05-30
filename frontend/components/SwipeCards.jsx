'use client';

import { useState, useRef, useEffect } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, XCircle, Zap } from 'lucide-react';

// Helper function to convert difficulty value to readable label
const getDifficultyLabel = (difficulty) => {
  if (!difficulty && difficulty !== 0) return 'Medium';
  
  const difficultyNum = parseFloat(difficulty);
  if (difficultyNum <= 0.3) return 'Easy';
  if (difficultyNum <= 0.6) return 'Medium';
  return 'Hard';
};

// Helper function to get difficulty color class
const getDifficultyColorClass = (difficulty) => {
  if (!difficulty && difficulty !== 0) return 'text-gray-500';
  
  const difficultyNum = parseFloat(difficulty);
  if (difficultyNum <= 0.3) return 'text-green-500';
  if (difficultyNum <= 0.6) return 'text-yellow-500';
  return 'text-red-500';
};

const SwipeCards = ({ questions, onAnswer }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const cardRef = useRef(null);
  const startXRef = useRef(0);

  const currentQuestion = questions[currentQuestionIndex];

  // Clean up event listeners when component unmounts or when dragging state changes
  useEffect(() => {
    // Only add event listeners when actively dragging
    if (!isDragging || showFeedback) return;
    
    const handleMouseMove = (e) => {
        const currentX = e.clientX;
      const offset = currentX - startXRef.current;
        setDragOffset(offset);
    };
    
    const handleMouseUp = (e) => {
      setIsDragging(false);
      const endX = e.clientX;
      const swipeDistance = endX - startXRef.current;
      
      if (Math.abs(swipeDistance) > 80) {
        const selectedOption = swipeDistance < 0 ? 'a' : 'b';
        handleAnswer(selectedOption);
      }
      setDragOffset(0);
    };
    
    // Add listeners to document only when dragging
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    // Clean up
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  }, [isDragging, showFeedback]);

  const handleMouseDown = (e) => {
    // Only start dragging if we're clicking directly on the card element
    if (showFeedback || !cardRef.current || !cardRef.current.contains(e.target)) return;
    
    e.preventDefault(); // Prevent text selection
    setIsDragging(true);
    startXRef.current = e.clientX;
  };

  const handleTouchStart = (e) => {
    // Only start dragging if we're touching directly on the card element
    if (showFeedback || !cardRef.current || !cardRef.current.contains(e.target)) return;
    
    setIsDragging(true);
    startXRef.current = e.touches[0].clientX;
  };
  
  // Separate touch move/end handlers using useEffect
  useEffect(() => {
    if (!isDragging || showFeedback) return;
    
    const handleTouchMove = (e) => {
        const currentX = e.touches[0].clientX;
      const offset = currentX - startXRef.current;
        setDragOffset(offset);
    };
    
    const handleTouchEnd = (e) => {
      setIsDragging(false);
      const endX = e.changedTouches[0].clientX;
      const swipeDistance = endX - startXRef.current;
      
      if (Math.abs(swipeDistance) > 80) {
        const selectedOption = swipeDistance < 0 ? 'a' : 'b';
        handleAnswer(selectedOption);
      }
      setDragOffset(0);
    };
    
    document.addEventListener('touchmove', handleTouchMove);
    document.addEventListener('touchend', handleTouchEnd);
    
    return () => {
      document.removeEventListener('touchmove', handleTouchMove);
      document.removeEventListener('touchend', handleTouchEnd);
    };
  }, [isDragging, showFeedback]);

  useEffect(() => {
    // Reset state when questions change
    setCurrentQuestionIndex(0);
    setShowFeedback(false);
  }, [questions]);

  const handleAnswer = (selectedOption) => {
    if (showFeedback || !currentQuestion) return;

    const isAnswerCorrect = selectedOption === currentQuestion.correct_answer;
    setIsCorrect(isAnswerCorrect);
    setShowFeedback(true);
    
    // Immediately call onAnswer so the parent can process the answer
    onAnswer(currentQuestion, selectedOption);
    
    // Set a timeout to hide feedback and transition to next question
    setTimeout(() => {
      setShowFeedback(false);
      
      // Small delay before moving to the next question to avoid UI jank
      setTimeout(() => {
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        console.log("End of quiz reached");
      }
      }, 50);
    }, 1500); // Reduced from 2000ms to 1500ms for a snappier experience
  };

  if (!currentQuestion) {
    return (
      <div className="flex flex-col items-center justify-center h-96 bg-card text-card-foreground p-6 rounded-xl shadow-xl border border-border w-full max-w-md mx-auto">
        <Zap size={48} className="text-muted-foreground mb-4" />
        <h3 className="text-xl font-semibold text-muted-foreground">All questions answered!</h3>
        <p className="text-muted-foreground">You can upload new content to generate more.</p>
      </div>
    );
  }

  const rotation = dragOffset / 20;
  const opacity = Math.max(0, 1 - Math.abs(dragOffset) / 300);

  return (
    <div className="flex flex-col items-center justify-center gap-6 p-4 w-full max-w-md mx-auto">
      <div className="w-full text-center mb-2">
        <p className="text-sm text-muted-foreground">
          Concept: <span className="font-semibold text-primary">{currentQuestion.concept}</span>
          {currentQuestion.difficulty && (
            <span className="ml-2">• Difficulty: <span className={`font-semibold ${getDifficultyColorClass(currentQuestion.difficulty)}`}>{getDifficultyLabel(currentQuestion.difficulty)}</span></span>
          )}
        </p>
      </div>
      
      <div 
        ref={cardRef}
        className={`relative bg-card text-card-foreground p-8 rounded-xl shadow-2xl w-full transition-all duration-100 ease-out border border-border 
                    ${isDragging ? 'cursor-grabbing' : 'cursor-grab'}`}
        style={{ 
          transform: `translateX(${dragOffset}px) rotate(${rotation}deg)`,
          opacity: showFeedback ? 1 : opacity,
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        <h3 className="text-xl font-semibold mb-6 text-center min-h-[3em]">{currentQuestion.question}</h3>
        
        <div className="space-y-4">
          <button 
            onClick={() => handleAnswer('a')} 
            disabled={showFeedback}
            className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-3 px-4 rounded-lg font-medium transition-colors text-left flex items-center disabled:opacity-70"
          >
            <span className="bg-primary text-primary-foreground rounded-md h-6 w-6 flex items-center justify-center mr-3 text-xs">A</span>
            {currentQuestion.option_a}
          </button>
          <button 
            onClick={() => handleAnswer('b')} 
            disabled={showFeedback}
            className="w-full bg-secondary hover:bg-secondary/80 text-secondary-foreground py-3 px-4 rounded-lg font-medium transition-colors text-left flex items-center disabled:opacity-70"
          >
            <span className="bg-primary text-primary-foreground rounded-md h-6 w-6 flex items-center justify-center mr-3 text-xs">B</span>
            {currentQuestion.option_b}
          </button>
        </div>
        
        {showFeedback && (
          <div className={`absolute inset-0 flex flex-col items-center justify-center rounded-xl p-6 
                          ${isCorrect ? 'bg-green-500/20 border-green-500' : 'bg-red-500/20 border-red-500'} border-2 backdrop-blur-sm`}>
            <div className="text-center">
              {isCorrect ? 
                <CheckCircle2 size={48} className="text-green-400 mx-auto mb-3" /> : 
                <XCircle size={48} className="text-red-400 mx-auto mb-3" />
              }
              <h3 className={`text-2xl font-bold mb-2 ${isCorrect ? 'text-green-300' : 'text-red-300'}`}>
                {isCorrect ? 'Correct!' : 'Incorrect'}
              </h3>
              <p className="text-sm text-muted-foreground">
                {currentQuestion.explanation}
              </p>
            </div>
          </div>
        )}
      </div>
      
      <div className="flex gap-4 mt-2">
        <button
          onClick={() => handleAnswer('a')}
          disabled={showFeedback}
          title="Choose Option A (Swipe Left)"
          className="p-4 bg-secondary text-secondary-foreground rounded-full hover:bg-primary hover:text-primary-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background shadow-md disabled:opacity-50"
        >
          <ArrowLeft size={20} />
        </button>
        <button
          onClick={() => handleAnswer('b')}
          disabled={showFeedback}
          title="Choose Option B (Swipe Right)"
          className="p-4 bg-secondary text-secondary-foreground rounded-full hover:bg-primary hover:text-primary-foreground transition-colors focus:outline-none focus:ring-2 focus:ring-ring focus:ring-offset-2 focus:ring-offset-background shadow-md disabled:opacity-50"
        >
          <ArrowRight size={20} />
        </button>
      </div>
      
      <div className="w-full max-w-md flex justify-between items-center mt-4">
        <span className="text-xs text-muted-foreground">
          Question {currentQuestionIndex + 1} of {questions.length}
        </span>
        <div className="flex gap-1.5">
          {questions.map((_, index) => (
            <div 
              key={index} 
              className={`w-2.5 h-2.5 rounded-full transition-all ${index === currentQuestionIndex ? 'bg-primary scale-125' : 'bg-secondary'}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default SwipeCards; 