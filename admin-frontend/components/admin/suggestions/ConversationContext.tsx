// components/admin/suggestions/ConversationContext.tsx
import { User, Bot } from "lucide-react";

interface ConversationContextProps {
  originalMessage?: string;
  assistantResponse?: string;
}

export function ConversationContext({ 
  originalMessage, 
  assistantResponse 
}: ConversationContextProps) {
  if (!originalMessage && !assistantResponse) {
    return null;
  }

  return (
    <div className="space-y-4">
      <h3 className="font-semibold mb-2 text-sm sm:text-base">Problem Context</h3>
      
      {/* User Message */}
      {originalMessage && (
        <div className="flex gap-3 justify-end">
          <div className="max-w-2xl p-4 bg-blue-500 text-white rounded-lg">
            <div className="whitespace-pre-wrap break-words text-sm">
              {originalMessage}
            </div>
          </div>
          <div className="flex-shrink-0 w-8 h-8 bg-green-500 rounded-full flex items-center justify-center">
            <User size={16} className="text-white" />
          </div>
        </div>
      )}

      {/* AI Response */}
      {assistantResponse && (
        <div className="flex gap-3 justify-start">
          <div className="flex-shrink-0 w-8 h-8 bg-red-500 rounded-full flex items-center justify-center">
            <Bot size={16} className="text-white" />
          </div>
          <div className="max-w-2xl p-4 bg-red-50 dark:bg-red-900/30 border-2 border-red-200 dark:border-red-800 rounded-lg">
            <div className="whitespace-pre-wrap break-words text-neutral-900 dark:text-neutral-100 text-sm">
              {assistantResponse}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}