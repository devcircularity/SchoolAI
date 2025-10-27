// app/tester/queue/components/QueueStatsCards.tsx - Clean version
import { ProblematicMessage } from "@/services/tester";
import { AlertTriangle, MessageSquare, Clock, User } from "lucide-react";

interface QueueStatsCardsProps {
  messages: ProblematicMessage[];
}

export function QueueStatsCards({ messages }: QueueStatsCardsProps) {
  // Calculate stats based on actual issue types
  const highPriorityCount = messages.filter(m => m.priority === 1).length;
  
  const negativeRatingCount = messages.filter(m => 
    m.issue_type === 'negative_rating' || m.rating === -1
  ).length;
  
  const fallbackCount = messages.filter(m => 
    m.issue_type === 'fallback_used' || 
    m.issue_type === 'intent_ollama_fallback' ||
    m.issue_type === 'routing_ollama_fallback' ||
    m.fallback_used === true
  ).length;
  
  const lowConfidenceCount = messages.filter(m => 
    m.issue_type === 'no_llm_confidence' ||
    m.issue_type === 'low_confidence' ||
    (m.llm_confidence && m.llm_confidence < 0.6)
  ).length;

  return (
    <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4 mb-4 sm:mb-6">
      <div className="card p-3 sm:p-4">
        <div className="flex items-center gap-2 mb-2">
          <AlertTriangle className="text-red-600 flex-shrink-0" size={14} />
          <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">High Priority</h3>
        </div>
        <p className="text-lg sm:text-2xl font-bold text-red-600">
          {highPriorityCount}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <div className="flex items-center gap-2 mb-2">
          <MessageSquare className="text-orange-600 flex-shrink-0" size={14} />
          <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">Negative Ratings</h3>
        </div>
        <p className="text-lg sm:text-2xl font-bold text-orange-600">
          {negativeRatingCount}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="text-yellow-600 flex-shrink-0" size={14} />
          <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">Fallback Used</h3>
        </div>
        <p className="text-lg sm:text-2xl font-bold text-yellow-600">
          {fallbackCount}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <div className="flex items-center gap-2 mb-2">
          <User className="text-purple-600 flex-shrink-0" size={14} />
          <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">Low Confidence</h3>
        </div>
        <p className="text-lg sm:text-2xl font-bold text-purple-600">
          {lowConfidenceCount}
        </p>
      </div>
    </div>
  );
}