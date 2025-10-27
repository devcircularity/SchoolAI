// components/admin/suggestions/SuggestionReviewButtons.tsx
import { AlertCircle, Check, CheckCircle, X } from "lucide-react";
import Button from "@/components/ui/Button";

interface SuggestionReviewButtonsProps {
  suggestionStatus: string;
  reviewMode: boolean;
  currentTab: string;
  adminAnalysis: string;
  implementationNotes: string;
  onStartReview: () => void;
  onSwitchToAnalysis: () => void;
  onSwitchToActions: () => void;
  onApprove: () => void;
  onReject: () => void;
}

export function SuggestionReviewButtons({
  suggestionStatus,
  reviewMode,
  currentTab,
  adminAnalysis,
  implementationNotes,
  onStartReview,
  onSwitchToAnalysis,
  onSwitchToActions,
  onApprove,
  onReject
}: SuggestionReviewButtonsProps) {
  const hasCompletedAnalysis = adminAnalysis.trim().length > 0;

  return (
    <div className="flex flex-col sm:flex-row gap-2 sm:gap-4 pt-4 sm:pt-6 border-t border-neutral-200 dark:border-neutral-700">
      {suggestionStatus === 'pending' && (
        <>
          {!reviewMode ? (
            <Button onClick={onStartReview} className="flex-1 text-sm">
              Start Review
            </Button>
          ) : (
            <>
              {/* Guide user through proper review flow */}
              {currentTab === 'details' && (
                <div className="flex flex-col sm:flex-row gap-2 w-full">
                  <div className="text-xs sm:text-sm text-blue-600 dark:text-blue-400 flex items-center gap-2 flex-1">
                    <AlertCircle size={16} className="flex-shrink-0" />
                    Review the details, then proceed to Analysis tab to evaluate this suggestion
                  </div>
                  <Button 
                    onClick={onSwitchToAnalysis}
                    className="flex items-center gap-2 text-sm"
                  >
                    Proceed to Analysis
                  </Button>
                </div>
              )}

              {currentTab === 'analysis' && !hasCompletedAnalysis && (
                <div className="text-xs sm:text-sm text-amber-600 dark:text-amber-400 flex items-center gap-2">
                  <AlertCircle size={16} className="flex-shrink-0" />
                  Please provide your analysis above before making a final decision
                </div>
              )}

              {currentTab === 'analysis' && hasCompletedAnalysis && (
                <div className="flex flex-col gap-3 w-full">
                  <div className="text-xs sm:text-sm text-green-600 dark:text-green-400 flex items-center gap-2">
                    <CheckCircle size={16} className="flex-shrink-0" />
                    Analysis complete. Make your decision:
                  </div>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button 
                      onClick={onSwitchToActions}
                      className="flex items-center gap-2 text-sm"
                    >
                      <Check size={16} />
                      <span className="hidden sm:inline">Approve & Create Action Items</span>
                      <span className="sm:hidden">Approve</span>
                    </Button>
                    <Button 
                      onClick={onReject}
                      className="btn-danger flex items-center gap-2 text-sm"
                    >
                      <X size={16} />
                      Reject
                    </Button>
                  </div>
                </div>
              )}

              {currentTab === 'actions' && (
                <div className="flex flex-col gap-3 w-full">
                  <div className="text-xs sm:text-sm text-blue-600 dark:text-blue-400 flex items-center gap-2">
                    <AlertCircle size={16} className="flex-shrink-0" />
                    Create action items to track implementation, then finalize approval
                  </div>
                  <div className="flex flex-col sm:flex-row gap-2">
                    <Button 
                      onClick={onApprove}
                      className="flex items-center gap-2 text-sm"
                    >
                      <Check size={16} />
                      <span className="hidden sm:inline">Finalize Approval</span>
                      <span className="sm:hidden">Finalize</span>
                    </Button>
                    <Button 
                      onClick={onReject}
                      className="btn-danger flex items-center gap-2 text-sm"
                    >
                      <X size={16} />
                      Reject Instead
                    </Button>
                  </div>
                </div>
              )}
            </>
          )}
        </>
      )}

      {suggestionStatus === 'approved' && (
        <div className="text-xs sm:text-sm text-green-600 dark:text-green-400 flex items-center gap-2">
          <CheckCircle size={16} className="flex-shrink-0" />
          Approved - Create action items to track implementation
        </div>
      )}

      {suggestionStatus === 'implemented' && (
        <div className="text-xs sm:text-sm text-purple-600 dark:text-purple-400 flex items-center gap-2">
          <CheckCircle size={16} className="flex-shrink-0" />
          Suggestion has been addressed
        </div>
      )}
    </div>
  );
}