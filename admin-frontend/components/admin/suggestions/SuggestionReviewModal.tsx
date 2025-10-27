// components/admin/suggestions/SuggestionReviewModal.tsx
import { useState } from "react";
import { X } from "lucide-react";
import Button from "@/components/ui/Button";
import { ActionItem, Suggestion } from "@/services/suggestions";
import { SuggestionDetailsTab } from "./SuggestionDetailsTab";
import { SuggestionAnalysisTab } from "./SuggestionAnalysisTab";
import { SuggestionActionsTab } from "./SuggestionActionsTab";
import { SuggestionReviewButtons } from "./SuggestionReviewButtons";

interface EnhancedSuggestion extends Suggestion {
  action_items?: ActionItem[];
  admin_analysis?: string;
  implementation_notes?: string;
  original_message?: string;
  assistant_response?: string;
}

interface ActionItemFormData {
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  implementation_type: 'pattern' | 'template' | 'code_fix' | 'documentation' | 'other';
  due_date: string;
}

interface SuggestionReviewModalProps {
  suggestion: EnhancedSuggestion;
  onClose: () => void;
  onReview: (suggestionId: string, reviewData: any) => Promise<void>;
  onCreateActionItem: (suggestionId: string, actionItem: any) => Promise<void>;
  onMarkAddressed: (suggestionId: string, notes: string) => Promise<void>;
}

export function SuggestionReviewModal({
  suggestion,
  onClose,
  onReview,
  onCreateActionItem,
  onMarkAddressed
}: SuggestionReviewModalProps) {
  const [activeTab, setActiveTab] = useState<'details' | 'analysis' | 'actions'>('details');
  const [reviewMode, setReviewMode] = useState(false);
  const [adminAnalysis, setAdminAnalysis] = useState(suggestion.admin_analysis || '');
  const [implementationNotes, setImplementationNotes] = useState(suggestion.implementation_notes || '');
  const [actionItems, setActionItems] = useState<ActionItem[]>(suggestion.action_items || []);
  const [newActionItem, setNewActionItem] = useState<ActionItemFormData>({
    title: '',
    description: '',
    priority: 'medium',
    implementation_type: 'other',
    due_date: ''
  });
  const [showAddAction, setShowAddAction] = useState(false);
  const [completionNotes, setCompletionNotes] = useState('');

  const handleStartReview = () => {
    setReviewMode(true);
    setActiveTab('analysis');
  };

  const handleEnhancedReview = async (status: 'approved' | 'rejected') => {
    try {
      // First, review the suggestion
      await onReview(suggestion.id, {
        status,
        admin_note: `Status: ${status}`,
        admin_analysis: adminAnalysis,
        implementation_notes: implementationNotes
      });

      // Then, create all action items that are new (temporary IDs)
      if (status === 'approved' && actionItems.length > 0) {
        for (const item of actionItems) {
          if (item.id.startsWith('temp-')) {
            await onCreateActionItem(suggestion.id, {
              title: item.title,
              description: item.description,
              priority: item.priority,
              implementation_type: item.implementation_type,
              due_date: item.due_date ? new Date(item.due_date).toISOString() : undefined,
              suggestion_id: suggestion.id
            });
          }
        }
      }
      
      onClose();
    } catch (error) {
      console.error('Failed to review suggestion:', error);
    }
  };

  const handleAddActionItem = () => {
    if (!newActionItem.title.trim()) return;

    // Create a temporary action item with local ID
    const tempActionItem: ActionItem = {
      id: `temp-${Date.now()}`,
      suggestion_id: suggestion.id,
      title: newActionItem.title,
      description: newActionItem.description,
      priority: newActionItem.priority,
      implementation_type: newActionItem.implementation_type,
      status: 'pending',
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
      due_date: newActionItem.due_date || undefined,
      assigned_to: undefined,
      completed_at: undefined,
      created_by: 'current-user', // Will be set by backend
      created_by_name: 'Current User' // Will be set by backend
    };

    // Add to local state
    setActionItems([...actionItems, tempActionItem]);
    
    // Reset form
    setNewActionItem({
      title: '',
      description: '',
      priority: 'medium',
      implementation_type: 'other',
      due_date: ''
    });
    
    // Close the form
    setShowAddAction(false);
  };

  const handleMarkAddressed = async () => {
    if (completionNotes.trim()) {
      try {
        await onMarkAddressed(suggestion.id, completionNotes);
        onClose();
      } catch (error) {
        console.error('Failed to mark as addressed:', error);
      }
    }
  };

  const handleNewActionItemChange = (data: ActionItemFormData) => {
    setNewActionItem(data);
  };

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'critical': return 'bg-red-100 text-red-800 border-red-200 dark:bg-red-900/30 dark:text-red-200 dark:border-red-800';
      case 'high': return 'bg-orange-100 text-orange-800 border-orange-200 dark:bg-orange-900/30 dark:text-orange-200 dark:border-orange-800';
      case 'medium': return 'bg-yellow-100 text-yellow-800 border-yellow-200 dark:bg-yellow-900/30 dark:text-yellow-200 dark:border-yellow-800';
      case 'low': return 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/30 dark:text-gray-200 dark:border-gray-800';
      default: return 'bg-gray-100 text-gray-800 border-gray-200 dark:bg-gray-900/30 dark:text-gray-200 dark:border-gray-800';
    }
  };

  const getTypeColor = (type: string) => {
    switch (type) {
      case 'pattern': return 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200';
      case 'template': return 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200';
      case 'code_fix': return 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200';
      case 'documentation': return 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-200';
      default: return 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200';
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-6xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          {/* Header */}
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-start mb-4 sm:mb-6 gap-3">
            <div className="min-w-0">
              <h2 className="text-lg sm:text-xl font-bold break-words">{suggestion.title}</h2>
              <p className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                Submitted by {suggestion.created_by_name} on {new Date(suggestion.created_at).toLocaleDateString()}
              </p>
              <div className="flex flex-wrap gap-2 mt-2">
                <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getPriorityColor(suggestion.priority)}`}>
                  {suggestion.priority}
                </span>
                <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200">
                  {suggestion.suggestion_type.replace('_', ' ')}
                </span>
              </div>
            </div>
            <Button onClick={onClose} className="btn-secondary text-neutral-500 flex-shrink-0">
              <X size={16} />
            </Button>
          </div>

          {/* Review Mode Indicator */}
          {reviewMode && (
            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <div className="flex items-center gap-2">
                <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
                <span className="text-sm font-medium text-blue-800 dark:text-blue-200">
                  Review Mode Active
                </span>
                <span className="text-xs text-blue-600 dark:text-blue-300">
                  - Follow the workflow to complete your review
                </span>
              </div>
            </div>
          )}

          {/* Tabs */}
          <div className="border-b border-neutral-200 dark:border-neutral-700 mb-4 sm:mb-6">
            <nav className="flex space-x-4 sm:space-x-8 overflow-x-auto">
              {['details', 'analysis', 'actions'].map((tab) => {
                let tabStatus = '';
                
                if (reviewMode) {
                  if (tab === 'details') tabStatus = '✓ Reviewed';
                  else if (tab === 'analysis' && adminAnalysis.trim()) tabStatus = '✓ Complete';
                  else if (tab === 'analysis') tabStatus = '⚠ Required';
                  else if (tab === 'actions' && actionItems.length > 0) tabStatus = `✓ ${actionItems.length} item${actionItems.length > 1 ? 's' : ''}`;
                }
                
                return (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab as any)}
                    className={`py-2 px-1 border-b-2 font-medium text-xs sm:text-sm capitalize whitespace-nowrap ${
                      activeTab === tab
                        ? 'border-blue-500 text-blue-600 dark:text-blue-400'
                        : 'border-transparent text-neutral-500 hover:text-neutral-700 dark:hover:text-neutral-300'
                    }`}
                  >
                    {tab}
                    {tabStatus && (
                      <span className="ml-1 text-xs opacity-75">
                        {tabStatus}
                      </span>
                    )}
                  </button>
                );
              })}
            </nav>
          </div>

          {/* Tab Content */}
          <div className="space-y-4 sm:space-y-6">
            {activeTab === 'details' && (
              <SuggestionDetailsTab suggestion={suggestion} />
            )}

            {activeTab === 'analysis' && (
              <SuggestionAnalysisTab
                suggestion={suggestion}
                adminAnalysis={adminAnalysis}
                implementationNotes={implementationNotes}
                onAdminAnalysisChange={setAdminAnalysis}
                onImplementationNotesChange={setImplementationNotes}
                reviewMode={reviewMode}
              />
            )}

            {activeTab === 'actions' && (
              <SuggestionActionsTab
                suggestionStatus={suggestion.status}
                actionItems={actionItems}
                showAddAction={showAddAction}
                newActionItem={newActionItem}
                completionNotes={completionNotes}
                onShowAddActionChange={setShowAddAction}
                onNewActionItemChange={handleNewActionItemChange}
                onCompletionNotesChange={setCompletionNotes}
                onAddActionItem={handleAddActionItem}
                onMarkAddressed={handleMarkAddressed}
                getPriorityColor={getPriorityColor}
                getTypeColor={getTypeColor}
              />
            )}
          </div>

          {/* Review Buttons */}
          <SuggestionReviewButtons
            suggestionStatus={suggestion.status}
            reviewMode={reviewMode}
            currentTab={activeTab}
            adminAnalysis={adminAnalysis}
            implementationNotes={implementationNotes}
            onStartReview={handleStartReview}
            onSwitchToAnalysis={() => setActiveTab('analysis')}
            onSwitchToActions={() => setActiveTab('actions')}
            onApprove={() => handleEnhancedReview('approved')}
            onReject={() => handleEnhancedReview('rejected')}
          />
        </div>
      </div>
    </div>
  );
}