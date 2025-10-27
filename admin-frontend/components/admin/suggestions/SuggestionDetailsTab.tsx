// components/admin/suggestions/SuggestionDetailsTab.tsx
import { Suggestion } from "@/services/suggestions";
import { ConversationContext } from "./ConversationContext";

interface EnhancedSuggestion extends Suggestion {
  original_message?: string;
  assistant_response?: string;
}

interface SuggestionDetailsTabProps {
  suggestion: EnhancedSuggestion;
}

export function SuggestionDetailsTab({ suggestion }: SuggestionDetailsTabProps) {
  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Conversation Context */}
      <ConversationContext 
        originalMessage={suggestion.original_message}
        assistantResponse={suggestion.assistant_response}
      />

      {/* Description */}
      <div>
        <h3 className="font-semibold mb-2 text-sm sm:text-base">Tester's Analysis</h3>
        <div className="p-3 sm:p-4 bg-neutral-50 dark:bg-neutral-700 rounded-lg text-sm">
          {suggestion.description}
        </div>
      </div>

      {/* Handler and Intent */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
        <div>
          <h3 className="font-semibold mb-2 text-sm sm:text-base">Handler</h3>
          <code className="p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs sm:text-sm block break-all">
            {suggestion.handler}
          </code>
        </div>
        <div>
          <h3 className="font-semibold mb-2 text-sm sm:text-base">Intent</h3>
          <code className="p-2 bg-gray-100 dark:bg-gray-800 rounded text-xs sm:text-sm block break-all">
            {suggestion.intent}
          </code>
        </div>
      </div>

      {/* Proposed Solution */}
      {suggestion.pattern && (
        <div>
          <h3 className="font-semibold mb-2 text-sm sm:text-base">Proposed Pattern</h3>
          <div className="p-3 sm:p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200">
            <code className="text-xs sm:text-sm break-all">{suggestion.pattern}</code>
          </div>
        </div>
      )}

      {suggestion.template_text && (
        <div>
          <h3 className="font-semibold mb-2 text-sm sm:text-base">Proposed Template</h3>
          <div className="p-3 sm:p-4 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200">
            <div className="text-xs sm:text-sm whitespace-pre-wrap">{suggestion.template_text}</div>
          </div>
        </div>
      )}

      {/* Tester's Note */}
      {suggestion.tester_note && (
        <div>
          <h3 className="font-semibold mb-2 text-sm sm:text-base">Additional Notes</h3>
          <div className="p-3 sm:p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200">
            <div className="text-xs sm:text-sm">{suggestion.tester_note}</div>
          </div>
        </div>
      )}
    </div>
  );
}