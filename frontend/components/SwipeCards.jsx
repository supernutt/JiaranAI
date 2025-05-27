'use client';

import { useState, useRef } from 'react';
import { ArrowLeft, ArrowRight, CheckCircle2, XCircle, Zap } from 'lucide-react';

const SwipeCards = ({ questions, onAnswer }) => {
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [showFeedback, setShowFeedback] = useState(false);
  const [isCorrect, setIsCorrect] = useState(false);
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const cardRef = useRef(null);

  const currentQuestion = questions[currentQuestionIndex];

  const handleMouseDown = (e) => {
    if (showFeedback) return;
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
      if (!isDragging) return;
      setIsDragging(false);
      const endX = e.clientX;
      const swipeDistance = endX - startX;
      
      if (Math.abs(swipeDistance) > 80) {
        const selectedOption = swipeDistance < 0 ? 'a' : 'b';
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
    if (showFeedback) return;
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
      if (!isDragging) return;
      setIsDragging(false);
      const endX = e.changedTouches[0].clientX;
      const swipeDistance = endX - startX;
      
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
  };

  const handleAnswer = (selectedOption) => {
    if (showFeedback || !currentQuestion) return;

    const isAnswerCorrect = selectedOption === currentQuestion.correct_answer;
    setIsCorrect(isAnswerCorrect);
    setShowFeedback(true);
    
    onAnswer(currentQuestion.concept, isAnswerCorrect);
    
    setTimeout(() => {
      setShowFeedback(false);
      if (currentQuestionIndex < questions.length - 1) {
        setCurrentQuestionIndex(currentQuestionIndex + 1);
      } else {
        console.log("End of quiz reached");
      }
    }, 2000);
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