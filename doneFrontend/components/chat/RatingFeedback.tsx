// components/chat/RatingFeedback.tsx - Optional toast notification for rating feedback
import React, { useEffect, useState } from 'react';
import { CheckCircle, XCircle } from 'lucide-react';

interface RatingFeedbackProps {
  message: string;
  type: 'success' | 'error';
  onClose: () => void;
  duration?: number;
}

export const RatingFeedback: React.FC<RatingFeedbackProps> = ({
  message,
  type,
  onClose,
  duration = 3000
}) => {
  const [isVisible, setIsVisible] = useState(true);

  useEffect(() => {
    const timer = setTimeout(() => {
      setIsVisible(false);
      setTimeout(onClose, 300); // Allow fade-out animation
    }, duration);

    return () => clearTimeout(timer);
  }, [duration, onClose]);

  const icon = type === 'success' ? 
    <CheckCircle size={16} className="text-green-600" /> : 
    <XCircle size={16} className="text-red-600" />;

  const bgColor = type === 'success' ? 
    'bg-green-50 border-green-200 dark:bg-green-900/20 dark:border-green-800' :
    'bg-red-50 border-red-200 dark:bg-red-900/20 dark:border-red-800';

  const textColor = type === 'success' ? 
    'text-green-800 dark:text-green-200' :
    'text-red-800 dark:text-red-200';

  return (
    <div className={`
      fixed top-20 right-4 z-50 max-w-sm p-3 rounded-lg border shadow-lg
      transition-all duration-300 ${isVisible ? 'opacity-100 translate-x-0' : 'opacity-0 translate-x-full'}
      ${bgColor}
    `}>
      <div className="flex items-center gap-2">
        {icon}
        <span className={`text-sm ${textColor}`}>{message}</span>
      </div>
    </div>
  );
};