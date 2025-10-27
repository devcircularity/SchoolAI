// app/tester/queue/components/SuggestionModal.tsx - Fixed with proper scrolling
import { useState } from "react";
import { ProblematicMessage, testerService } from "@/services/tester";
import Button from "@/components/ui/Button";
import { X, User, Bot, CheckCircle, AlertCircle } from "lucide-react";

type SuggestionType = 'user_query' | 'ai_response';

interface SuggestionModalProps {
  message: ProblematicMessage;
  suggestionType: SuggestionType;
  onClose: () => void;
  onSubmit: () => void;
}

export function SuggestionModal({ 
  message, 
  suggestionType,
  onClose, 
  onSubmit 
}: SuggestionModalProps) {
  const [step, setStep] = useState(1);
  const [userQueryIssue, setUserQueryIssue] = useState<boolean | null>(null);
  const [aiResponseIssue, setAiResponseIssue] = useState<boolean | null>(null);
  const [userQuerySuggestion, setUserQuerySuggestion] = useState('');
  const [aiResponseSuggestion, setAiResponseSuggestion] = useState('');
  const [submitting, setSubmitting] = useState(false);
  
  // Success/Error states
  const [submissionResult, setSubmissionResult] = useState<{
    success: boolean;
    message: string;
    suggestionsCount?: number;
    error?: string;
  } | null>(null);

  const handleNext = () => {
    if (step === 1) {
      setStep(2);
    } else if (step === 2) {
      setStep(3);
    }
  };

  const handleBack = () => {
    if (step === 2) setStep(1);
    if (step === 3) setStep(2);
  };

  const handleSubmit = async () => {
    const hasUserSuggestion = userQueryIssue && userQuerySuggestion.trim();
    const hasAiSuggestion = aiResponseIssue && aiResponseSuggestion.trim();
    
    if (!hasUserSuggestion && !hasAiSuggestion) {
      setSubmissionResult({
        success: false,
        message: "Please identify at least one issue and provide a suggestion.",
        error: "No suggestions provided"
      });
      return;
    }

    try {
      setSubmitting(true);
      setSubmissionResult(null);
      
      const submissions: Promise<any>[] = [];
      
      // Submit user query suggestion if provided
      if (hasUserSuggestion) {
        const userQuerySubmission = testerService.submitSuggestion({
          message_id: message.message_id,
          routing_log_id: message.routing_log_id,
          suggestion_type: 'user_query',
          title: 'User Query Classification Improvement',
          description: userQuerySuggestion,
          handler: message.intent || 'general',
          intent: message.intent || 'general',
          priority: 'medium',
          tester_note: 'Multi-step wizard: User query improvement'
        });
        submissions.push(userQuerySubmission);
      }

      // Submit AI response suggestion if provided  
      if (hasAiSuggestion) {
        const aiResponseSubmission = testerService.submitSuggestion({
          message_id: message.message_id,
          routing_log_id: message.routing_log_id,
          suggestion_type: 'ai_response',
          title: 'AI Response Improvement',
          description: aiResponseSuggestion,
          handler: message.intent || 'general', 
          intent: message.intent || 'general',
          priority: 'medium',
          tester_note: 'Multi-step wizard: AI response improvement'
        });
        submissions.push(aiResponseSubmission);
      }

      // Wait for all submissions to complete
      const results = await Promise.all(submissions);
      
      console.log('All submissions completed:', results);
      
      const suggestionCount = results.length;
      
      // Set success state
      setSubmissionResult({
        success: true,
        message: `Successfully submitted ${suggestionCount} suggestion${suggestionCount > 1 ? 's' : ''}!`,
        suggestionsCount: suggestionCount
      });
      
      // Call onSubmit to update parent (refresh queue)
      onSubmit();
      
      // Auto-close after showing success for 2 seconds
      setTimeout(() => {
        onClose();
      }, 2000);
      
    } catch (error) {
      console.error('Failed to submit suggestion:', error);
      
      // Show error in modal
      let errorMessage = 'Failed to submit suggestion. Please try again.';
      
      if (error instanceof Error) {
        errorMessage = error.message;
      } else if (error && typeof error === 'object' && 'response' in error) {
        const axiosError = error as any;
        if (axiosError.response?.data?.detail) {
          errorMessage = axiosError.response.data.detail;
        }
      }
      
      setSubmissionResult({
        success: false,
        message: errorMessage,
        error: errorMessage
      });
    } finally {
      setSubmitting(false);
    }
  };

  // Success/Error Message Component
  const SubmissionMessage = () => {
    if (!submissionResult) return null;

    return (
      <div className={`p-4 rounded-lg border mb-4 ${
        submissionResult.success 
          ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' 
          : 'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
      }`}>
        <div className="flex items-center gap-3">
          {submissionResult.success ? (
            <CheckCircle className="text-green-600 dark:text-green-400 flex-shrink-0" size={20} />
          ) : (
            <AlertCircle className="text-red-600 dark:text-red-400 flex-shrink-0" size={20} />
          )}
          <div>
            <p className={`font-medium ${
              submissionResult.success 
                ? 'text-green-800 dark:text-green-200' 
                : 'text-red-800 dark:text-red-200'
            }`}>
              {submissionResult.success ? 'Success!' : 'Error'}
            </p>
            <p className={`text-sm ${
              submissionResult.success 
                ? 'text-green-700 dark:text-green-300' 
                : 'text-red-700 dark:text-red-300'
            }`}>
              {submissionResult.message}
            </p>
            {submissionResult.success && (
              <p className="text-xs text-green-600 dark:text-green-400 mt-1">
                This modal will close automatically in a moment...
              </p>
            )}
          </div>
        </div>
      </div>
    );
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={submissionResult?.success ? undefined : onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-2xl w-full max-h-[90vh] flex flex-col">
        
        {/* Fixed Header */}
        <div className="p-6 flex-shrink-0 border-b border-neutral-200 dark:border-neutral-700">
          <div className="flex items-center justify-between mb-4">
            <div>
              <h2 className="text-xl font-bold">Improvement Suggestions</h2>
              <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                {submissionResult?.success ? 'Submission Complete!' : `Step ${step} of 3 • Help us improve the AI system`}
              </p>
            </div>
            <button 
              onClick={submissionResult?.success ? undefined : onClose}
              className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg transition-colors"
              disabled={submissionResult?.success}
            >
              <X size={20} />
            </button>
          </div>

          {/* Success/Error Message */}
          <SubmissionMessage />

          {/* Progress Indicator - Only show if not in success state */}
          {!submissionResult?.success && (
            <div className="flex">
              <div className={`flex-1 h-2 rounded-l-full ${step >= 1 ? 'bg-blue-500' : 'bg-neutral-200 dark:bg-neutral-700'}`} />
              <div className={`flex-1 h-2 ${step >= 2 ? 'bg-blue-500' : 'bg-neutral-200 dark:bg-neutral-700'}`} />
              <div className={`flex-1 h-2 rounded-r-full ${step >= 3 ? 'bg-blue-500' : 'bg-neutral-200 dark:bg-neutral-700'}`} />
            </div>
          )}
        </div>

        {/* Scrollable Content */}
        <div className="flex-1 overflow-y-auto p-6">
          {/* Don't show form steps if we have a successful submission */}
          {!submissionResult?.success && (
            <>
              {/* Step 1: User Query Analysis */}
              {step === 1 && (
                <div className="space-y-6">
                  <div className="p-4 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
                    <h3 className="font-medium text-blue-800 dark:text-blue-200 mb-2 flex items-center gap-2">
                      <User size={16} />
                      User Query Analysis
                    </h3>
                    <p className="text-sm text-blue-700 dark:text-blue-300 mb-3">
                      Does the user's question have issues that could be better understood by the AI?
                    </p>
                    <div className="bg-white dark:bg-blue-900/40 p-3 rounded border max-h-32 overflow-y-auto">
                      <p className="text-sm font-mono text-neutral-800 dark:text-neutral-200 whitespace-pre-wrap">
                        "{message.user_message}"
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <p className="font-medium">Does this user query have classification or understanding issues?</p>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 p-3 border rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 cursor-pointer">
                        <input
                          type="radio"
                          name="userQueryIssue"
                          value="yes"
                          checked={userQueryIssue === true}
                          onChange={() => setUserQueryIssue(true)}
                          className="w-4 h-4"
                        />
                        <div>
                          <div className="font-medium">Yes, there are issues</div>
                          <div className="text-sm text-neutral-600 dark:text-neutral-400">
                            The query is unclear, misclassified, or could be better understood
                          </div>
                        </div>
                      </label>
                      <label className="flex items-center gap-3 p-3 border rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 cursor-pointer">
                        <input
                          type="radio"
                          name="userQueryIssue"
                          value="no"
                          checked={userQueryIssue === false}
                          onChange={() => setUserQueryIssue(false)}
                          className="w-4 h-4"
                        />
                        <div>
                          <div className="font-medium">No, the query is fine</div>
                          <div className="text-sm text-neutral-600 dark:text-neutral-400">
                            The user's question is clear and properly understood
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>

                  {userQueryIssue === true && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        How should the system better understand this type of query?
                      </label>
                      <textarea
                        value={userQuerySuggestion}
                        onChange={(e) => setUserQuerySuggestion(e.target.value)}
                        className="input min-h-24 text-sm"
                        placeholder="Explain what's unclear about the user's question and how the AI should better classify or understand similar queries..."
                        required
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Step 2: AI Response Analysis */}
              {step === 2 && (
                <div className="space-y-6">
                  <div className="p-4 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
                    <h3 className="font-medium text-red-800 dark:text-red-200 mb-2 flex items-center gap-2">
                      <Bot size={16} />
                      AI Response Analysis
                    </h3>
                    <p className="text-sm text-red-700 dark:text-red-300 mb-3">
                      Does the AI's response have quality or helpfulness issues?
                    </p>
                    <div className="bg-white dark:bg-red-900/40 p-3 rounded border max-h-40 overflow-y-auto">
                      <p className="text-sm font-mono text-neutral-800 dark:text-neutral-200 whitespace-pre-wrap">
                        "{message.assistant_response}"
                      </p>
                    </div>
                  </div>

                  <div className="space-y-4">
                    <p className="font-medium">Does this AI response have quality or helpfulness issues?</p>
                    <div className="space-y-3">
                      <label className="flex items-center gap-3 p-3 border rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 cursor-pointer">
                        <input
                          type="radio"
                          name="aiResponseIssue"
                          value="yes"
                          checked={aiResponseIssue === true}
                          onChange={() => setAiResponseIssue(true)}
                          className="w-4 h-4"
                        />
                        <div>
                          <div className="font-medium">Yes, there are issues</div>
                          <div className="text-sm text-neutral-600 dark:text-neutral-400">
                            The response is unhelpful, inaccurate, or could be much better
                          </div>
                        </div>
                      </label>
                      <label className="flex items-center gap-3 p-3 border rounded-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 cursor-pointer">
                        <input
                          type="radio"
                          name="aiResponseIssue"
                          value="no"
                          checked={aiResponseIssue === false}
                          onChange={() => setAiResponseIssue(false)}
                          className="w-4 h-4"
                        />
                        <div>
                          <div className="font-medium">No, the response is appropriate</div>
                          <div className="text-sm text-neutral-600 dark:text-neutral-400">
                            The AI's answer is helpful and accurate given the context
                          </div>
                        </div>
                      </label>
                    </div>
                  </div>

                  {aiResponseIssue === true && (
                    <div>
                      <label className="block text-sm font-medium mb-2">
                        How should the AI response be improved?
                      </label>
                      <textarea
                        value={aiResponseSuggestion}
                        onChange={(e) => setAiResponseSuggestion(e.target.value)}
                        className="input min-h-24 text-sm"
                        placeholder="Explain what's wrong with the response and how it should be improved. What would a perfect answer contain?"
                        required
                      />
                    </div>
                  )}
                </div>
              )}

              {/* Step 3: Review and Submit */}
              {step === 3 && (
                <div className="space-y-6">
                  <div>
                    <h3 className="font-medium text-lg mb-4">Review Your Suggestions</h3>
                    <div className="space-y-4">
                      {/* User Query Summary */}
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <User size={16} className="text-blue-600" />
                          <span className="font-medium">User Query Classification</span>
                          <span className={`text-sm px-2 py-1 rounded-full ${
                            userQueryIssue ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                          }`}>
                            {userQueryIssue ? 'Has Issues' : 'No Issues'}
                          </span>
                        </div>
                        {userQueryIssue && userQuerySuggestion && (
                          <div className="text-sm text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-700 p-3 rounded max-h-32 overflow-y-auto">
                            {userQuerySuggestion}
                          </div>
                        )}
                      </div>

                      {/* AI Response Summary */}
                      <div className="p-4 border rounded-lg">
                        <div className="flex items-center gap-2 mb-2">
                          <Bot size={16} className="text-red-600" />
                          <span className="font-medium">AI Response Quality</span>
                          <span className={`text-sm px-2 py-1 rounded-full ${
                            aiResponseIssue ? 'bg-red-100 text-red-700' : 'bg-green-100 text-green-700'
                          }`}>
                            {aiResponseIssue ? 'Has Issues' : 'No Issues'}
                          </span>
                        </div>
                        {aiResponseIssue && aiResponseSuggestion && (
                          <div className="text-sm text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-700 p-3 rounded max-h-32 overflow-y-auto">
                            {aiResponseSuggestion}
                          </div>
                        )}
                      </div>
                    </div>

                    {!userQueryIssue && !aiResponseIssue && (
                      <div className="p-4 bg-green-50 dark:bg-green-900/20 border border-green-200 dark:border-green-800 rounded-lg">
                        <p className="text-sm text-green-800 dark:text-green-200">
                          You've indicated that both the user query and AI response are appropriate. 
                          This feedback helps us understand when the system is working correctly.
                        </p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </>
          )}
        </div>

        {/* Fixed Footer with Navigation Buttons */}
        {!submissionResult?.success && (
          <div className="p-6 border-t border-neutral-200 dark:border-neutral-700 flex-shrink-0">
            <div className="flex justify-between">
              <Button 
                onClick={step === 1 ? onClose : handleBack}
                className="btn-secondary"
                disabled={submitting}
              >
                {step === 1 ? 'Cancel' : 'Back'}
              </Button>

              {step < 3 ? (
                <Button 
                  onClick={handleNext}
                  disabled={
                    (step === 1 && userQueryIssue === null) ||
                    (step === 1 && userQueryIssue === true && !userQuerySuggestion.trim()) ||
                    (step === 2 && aiResponseIssue === null) ||
                    (step === 2 && aiResponseIssue === true && !aiResponseSuggestion.trim()) ||
                    submitting
                  }
                >
                  Next
                </Button>
              ) : (
                <Button 
                  onClick={handleSubmit}
                  disabled={submitting}
                >
                  {submitting ? 'Submitting...' : 'Submit Suggestions'}
                </Button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}