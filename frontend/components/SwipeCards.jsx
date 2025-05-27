'use client';

import { useState, useRef } from 'react';
import { ArrowLeft, ArrowRight, Check, X } from 'lucide-react';

const SwipeCards = ({ questions, onAnswer }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const cardRef = useRef(null);

  const currentQuestion = questions[currentQuestionIndex];

  const handleMouseDown = (e) => {
    setIsDragging(true);
    const startX = e.clientX;
    
    const handleMouseMove = (e) => {
      if (isDragging) {
        const currentX = e.clientX;
        const offset = currentX - startX;
        setDragOffset(offset);
      }
    };
    
    const handleMouseUp = (e) => {
      setIsDragging(false);
      const endX = e.clientX;
      const swipeDistance = endX - startX;
      
      if (Math.abs(swipeDistance) > 100) {
        const selectedOption = swipeDistance > 0 ? 'a' : 'b';
        handleAnswer(selectedOption);
      }
      
      setDragOffset(0);
    };
    
    document.addEventListener('mousemove', handleMouseMove);
    document.addEventListener('mouseup', handleMouseUp);
    
    return () => {
      document.removeEventListener('mousemove', handleMouseMove);
      document.removeEventListener('mouseup', handleMouseUp);
    };
  };

  const handleTouchStart = (e) => {
    setIsDragging(true);
    const startX = e.touches[0].clientX;
    
    const handleTouchMove = (e) => {
      if (isDragging) {
        const currentX = e.touches[0].clientX;
        const offset = currentX - startX;
        setDragOffset(offset);
      }
    };
    
    const handleTouchEnd = (e) => {
      setIsDragging(false);
      const endX = e.changedTouches[0].clientX;
      const swipeDistance = endX - startX;
      
      if (Math.abs(swipeDistance) > 100) {
        const selectedOption = swipeDistance > 0 ? 'a' : 'b';
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
  };

  const handleAnswer = (selectedOption) => {
    const isAnswerCorrect = selectedOption === currentQuestion.correct_answer;
    setIsCorrect(isAnswerCorrect);
    setShowFeedback(true);
    
    // Call the onAnswer callback
    onAnswer(currentQuestion.concept, isAnswerCorrect);
    
    // Move to the next question after feedback
    setTimeout(() => {
      setShowFeedback(false);
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      }
    }, 1500);
  };

  if (!currentQuestion) {
    return <div className="flex justify-center items-center h-64 text-zinc-400">No questions available</div>;
  }

  return (
    <div className="flex flex-col items-center justify-center gap-6 p-4">
      {/* Swipe Instruction */}
      <div className="text-sm text-zinc-400 mb-2">
        Swipe right for option A, left for option B, or use the buttons below
      </div>
      
      {/* Card */}
      <div 
        ref={cardRef}
        className="relative bg-zinc-800 rounded-2xl shadow-lg p-6 w-full max-w-md transition-transform"
        style={{ 
          transform: `translateX(${dragOffset}px) rotate(${dragOffset * 0.05}deg)`,
          cursor: isDragging ? 'grabbing' : 'grab'
        }}
        onMouseDown={handleMouseDown}
        onTouchStart={handleTouchStart}
      >
        {/* Question */}
        <h2 className="text-xl font-semibold mb-4 text-white">{currentQuestion.question}</h2>
        
        {/* Options */}
        <div className="space-y-4">
          <div className="p-3 border border-zinc-700 rounded-lg hover:bg-zinc-700 cursor-pointer transition">
            <span className="font-medium text-violet-400">A:</span> 
            <span className="text-zinc-200">{currentQuestion.option_a}</span>
          </div>
          <div className="p-3 border border-zinc-700 rounded-lg hover:bg-zinc-700 cursor-pointer transition">
            <span className="font-medium text-violet-400">B:</span> 
            <span className="text-zinc-200">{currentQuestion.option_b}</span>
          </div>
        </div>
        
        {/* Feedback overlay */}
        {showFeedback && (
          <div className={`absolute inset-0 flex items-center justify-center rounded-2xl ${isCorrect ? 'bg-green-900/80' : 'bg-red-900/80'}`}>
            <div className="text-center p-4">
              <div className="flex justify-center mb-3">
                {isCorrect ? (
                  <Check size={40} className="text-green-400 p-2 bg-green-900 rounded-full" />
                ) : (
                  <X size={40} className="text-red-400 p-2 bg-red-900 rounded-full" />
                )}
              </div>
              <h3 className="text-2xl font-bold mb-2 text-white">
                {isCorrect ? 'Correct!' : 'Try Again'}
              </h3>
              <p className="text-sm text-zinc-200">
                {currentQuestion.explanation}
              </p>
            </div>
          </div>
        )}
      </div>
      
      {/* Button Controls */}
      <div className="flex gap-4">
        <button
          onClick={() => handleAnswer('b')}
          className="flex items-center px-6 py-3 bg-zinc-800 text-white rounded-xl hover:bg-zinc-700 transition-colors border border-zinc-700"
        >
          <ArrowLeft className="mr-2" size={18} />
          Option B
        </button>
        <button
          onClick={() => handleAnswer('a')}
          className="flex items-center px-6 py-3 bg-violet-600 text-white rounded-xl hover:bg-violet-700 transition-colors"
        >
          Option A
          <ArrowRight className="ml-2" size={18} />
        </button>
      </div>
      
      {/* Progress Indicator */}
      <div className="w-full max-w-md flex justify-between items-center mt-4">
        <span className="text-sm text-zinc-400">
          Question {currentQuestionIndex + 1} of {questions.length}
        </span>
        <div className="flex gap-1">
          {questions.map((_, index) => (
            <div 
              key={index} 
              className={`w-2 h-2 rounded-full ${index === currentQuestionIndex ? 'bg-violet-500' : 'bg-zinc-700'}`}
            />
          ))}
        </div>
      </div>
    </div>
  );
};

export default SwipeCards; 