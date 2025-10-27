// components/ui/LoadingSpinner.tsx
"use client";

interface LoadingSpinnerProps {
  size?: 'sm' | 'md' | 'lg';
  className?: string;
  text?: string;
}

export default function LoadingSpinner({ 
  size = 'md', 
  className = '',
  text = 'Loading...'
}: LoadingSpinnerProps) {
  const sizeClasses = {
    sm: 'h-4 w-4',
    md: 'h-8 w-8',
    lg: 'h-12 w-12'
  };

  return (
    <div className={`flex flex-col items-center justify-center p-4 ${className}`}>
      <div 
        className={`animate-spin rounded-full border-2 border-neutral-200 border-t-[--color-brand] ${sizeClasses[size]}`}
      />
      {text && (
        <p className="mt-2 text-sm text-neutral-600 dark:text-neutral-400">
          {text}
        </p>
      )}
    </div>
  );
}

// Page-level loading component
export function PageLoading({ text = 'Loading page...' }: { text?: string }) {
  return (
    <div className="flex items-center justify-center min-h-[50vh]">
      <LoadingSpinner size="lg" text={text} />
    </div>
  );
}

// Card-level loading component
export function CardLoading({ text = 'Loading...' }: { text?: string }) {
  return (
    <div className="card p-8">
      <LoadingSpinner text={text} />
    </div>
  );
}