// components/admin/suggestions/SuggestionAnalysisTab.tsx
import { Lightbulb } from "lucide-react";
import { Suggestion } from "@/services/suggestions";

interface EnhancedSuggestion extends Suggestion {
  admin_analysis?: string;
  implementation_notes?: string;
}

interface SuggestionAnalysisTabProps {
  suggestion: EnhancedSuggestion;
  adminAnalysis: string;
  implementationNotes: string;
  onAdminAnalysisChange: (value: string) => void;
  onImplementationNotesChange: (value: string) => void;
  reviewMode: boolean;
}

export function SuggestionAnalysisTab({
  suggestion,
  adminAnalysis,
  implementationNotes,
  onAdminAnalysisChange,
  onImplementationNotesChange,
  reviewMode
}: SuggestionAnalysisTabProps) {
  return (
    <div className="space-y-4 sm:space-y-6">
      <div className="bg-yellow-50 dark:bg-yellow-900/20 border border-yellow-200 rounded-lg p-3 sm:p-4">
        <div className="flex items-start gap-2">
          <Lightbulb className="text-yellow-600 mt-0.5 flex-shrink-0" size={16} />
          <div>
            <h3 className="font-semibold text-yellow-800 dark:text-yellow-200 text-sm sm:text-base">
              Admin Analysis Required
            </h3>
            <p className="text-xs sm:text-sm text-yellow-700 dark:text-yellow-300">
              Analyze this suggestion and determine what action items are needed for implementation.
            </p>
          </div>
        </div>
      </div>

      <div>
        <h3 className="font-semibold mb-2 text-sm sm:text-base">Admin Analysis</h3>
        <textarea
          value={adminAnalysis}
          onChange={(e) => onAdminAnalysisChange(e.target.value)}
          placeholder="Analyze what this suggestion is asking for and what needs to be done to address it..."
          className="w-full p-3 sm:p-4 border border-neutral-200 rounded-lg min-h-[120px] text-xs sm:text-sm"
          disabled={!reviewMode && suggestion.status !== 'pending'}
        />
      </div>

      <div>
        <h3 className="font-semibold mb-2 text-sm sm:text-base">Implementation Notes</h3>
        <textarea
          value={implementationNotes}
          onChange={(e) => onImplementationNotesChange(e.target.value)}
          placeholder="Specific notes on how to implement this suggestion..."
          className="w-full p-3 sm:p-4 border border-neutral-200 rounded-lg min-h-[100px] text-xs sm:text-sm"
          disabled={!reviewMode && suggestion.status !== 'pending'}
        />
      </div>

      {suggestion.tester_note && (
        <div>
          <h3 className="font-semibold mb-2 text-sm sm:text-base">Tester Context</h3>
          <div className="p-3 sm:p-4 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="text-xs sm:text-sm">{suggestion.tester_note}</div>
          </div>
        </div>
      )}
    </div>
  );
}