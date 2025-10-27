// app/tester/queue/components/ConversationModal.tsx
import { ProblematicMessage } from "@/services/tester";
import Button from "@/components/ui/Button";
import { AlertTriangle, User, Bot, X, MessageSquare } from "lucide-react";

interface ConversationModalProps {
  message: ProblematicMessage;
  onClose: () => void;
  onCreateSuggestion: () => void; // Simplified - no type parameter needed
}

export function ConversationModal({ 
  message, 
  onClose, 
  onCreateSuggestion 
}: ConversationModalProps) {
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-6">
          {/* Header */}
          <div className="flex items-center justify-between mb-6">
            <div>
              <h2 className="text-xl font-bold">Problem Context</h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                Review the conversation and suggest improvements
              </p>
            </div>
            <button 
              onClick={onClose}
              className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
            >
              <X size={20} />
            </button>
          </div>

          {/* Problem Info Banner */}
          <div className="mb-6 p-4 bg-orange-50 dark:bg-orange-900/20 border border-orange-200 dark:border-orange-800 rounded-lg">
            <div className="flex items-start gap-3">
              <AlertTriangle className="text-orange-600 flex-shrink-0 mt-0.5" size={16} />
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <span className="font-medium text-orange-800 dark:text-orange-200">
                    Issue: {message.issue_type.replace('_', ' ').toUpperCase()}
                  </span>
                  <span className={`inline-flex items-center px-2 py-1 rounded-full text-xs font-medium bg-red-100 text-red-800`}>
                    {message.priority === 1 ? 'HIGH' : message.priority === 2 ? 'MED' : 'LOW'} Priority
                  </span>
                </div>
                <p className="text-sm text-orange-700 dark:text-orange-300">
                  {message.intent && `Intent: ${message.intent} • `}
                  Created: {new Date(message.created_at).toLocaleDateString()}
                  {message.llm_confidence && ` • Confidence: ${(message.llm_confidence * 100).toFixed(0)}%`}
                </p>
              </div>
            </div>
          </div>

          {/* Conversation Messages */}
          <div className="space-y-4 mb-6">
            {/* User Message */}
            <div className="flex gap-3 justify-end">
              <div className="max-w-2xl p-4 bg-blue-500 text-white rounded-lg">
                <div className="whitespace-pre-wrap break-words">
                  {message.user_message}
                </div>
              </div>
              <div className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
                <User size={16} className="text-white" />
              </div>
            </div>

            {/* AI Response (Problematic) */}
            <div className="flex gap-3 justify-start">
              <div className="flex-shrink-0 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
                <Bot size={16} className="text-white" />
              </div>
              <div className="max-w-2xl p-4 bg-red-50 dark:bg-red-900/30 border-2 border-red-200 dark:border-red-800 rounded-lg relative">
                <div className="absolute -top-2 -right-2">
                  <span className="inline-flex items-center px-2 py-1 rounded-full bg-red-500 text-white text-xs font-medium">
                    <AlertTriangle size={12} className="mr-1" />
                    Problem
                  </span>
                </div>
                <div className="whitespace-pre-wrap break-words text-neutral-900 dark:text-neutral-100">
                  {message.assistant_response}
                </div>
                <div className="flex items-center gap-3 mt-3 pt-3 border-t border-red-200 dark:border-red-700 text-xs text-red-600 dark:text-red-400">
                  {message.processing_time_ms && (
                    <span>Processed in {message.processing_time_ms}ms</span>
                  )}
                  {message.rating === -1 && (
                    <span className="flex items-center gap-1">
                      👎 User disliked this response
                    </span>
                  )}
                  {message.fallback_used && (
                    <span>🔄 Fallback response used</span>
                  )}
                </div>
              </div>
            </div>
          </div>

          {/* Single Action Button */}
          <div className="flex justify-center pt-4 border-t">
            <Button 
              onClick={onCreateSuggestion}
              className="px-8 py-3 bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-3 text-base font-medium"
            >
              <MessageSquare size={18} />
              Create Improvement Suggestion
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}