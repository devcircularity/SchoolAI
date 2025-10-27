// components/admin/configuration/ImplementationTab.tsx - Without fixed height
import { useState, useEffect } from "react";
import { suggestionsService, Suggestion, ActionItem } from "@/services/suggestions";
import { CheckCircle, Clock, User, AlertTriangle, Wrench, Eye, Plus, ExternalLink, Search } from "lucide-react";
import Button from "@/components/ui/Button";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import Modal from "@/components/ui/Modal";
import { SuggestionReviewModal } from "@/components/admin/suggestions/SuggestionReviewModal";

interface EnhancedSuggestion extends Suggestion {
  action_items?: ActionItem[];
  admin_analysis?: string;
  implementation_notes?: string;
}

interface ImplementationStatus {
  status: 'needs_items' | 'pending' | 'in_progress' | 'ready';
  label: string;
  color: string;
}

export default function ImplementationTab() {
  const [approvedSuggestions, setApprovedSuggestions] = useState<EnhancedSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedSuggestion, setSelectedSuggestion] = useState<EnhancedSuggestion | null>(null);
  const [showFullReview, setShowFullReview] = useState(false);
  const [filterStatus, setFilterStatus] = useState<string>('all');
  const [searchTerm, setSearchTerm] = useState<string>('');

  useEffect(() => {
    loadImplementationData();
  }, []);

  const loadImplementationData = async () => {
    try {
      setLoading(true);
      const suggestionsResponse = await suggestionsService.getSuggestions({
        status: 'approved',
        limit: 100
      });
      setApprovedSuggestions(suggestionsResponse.suggestions);
    } catch (error) {
      console.error('Failed to load implementation data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getImplementationStatus = (suggestion: EnhancedSuggestion): ImplementationStatus => {
    if (!suggestion.action_items || suggestion.action_items.length === 0) {
      return { 
        status: 'needs_items', 
        label: 'Needs Action Items', 
        color: 'bg-amber-100 text-amber-800 dark:bg-amber-900/30 dark:text-amber-200' 
      };
    }
    
    const completedItems = suggestion.action_items.filter(item => item.status === 'completed');
    const inProgressItems = suggestion.action_items.filter(item => item.status === 'in_progress');
    
    if (completedItems.length === suggestion.action_items.length) {
      return { 
        status: 'ready', 
        label: 'Ready to Complete', 
        color: 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200' 
      };
    } else if (inProgressItems.length > 0) {
      return { 
        status: 'in_progress', 
        label: 'In Progress', 
        color: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200' 
      };
    } else {
      return { 
        status: 'pending', 
        label: 'Pending Start', 
        color: 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200' 
      };
    }
  };

  const canQuickImplement = (suggestion: EnhancedSuggestion) => {
    return (suggestion.suggestion_type === 'regex_pattern' && suggestion.pattern) ||
           (suggestion.suggestion_type === 'prompt_template' && suggestion.template_text);
  };

  const handleQuickImplement = async (suggestion: EnhancedSuggestion) => {
    if (!confirm(`Quick implement this ${suggestion.suggestion_type.replace('_', ' ')}?`)) {
      return;
    }

    try {
      await suggestionsService.implementSuggestion(suggestion.id);
      await suggestionsService.markSuggestionAddressed(
        suggestion.id, 
        `Auto-implemented: ${suggestion.suggestion_type === 'regex_pattern' ? 'Pattern' : 'Template'} created in candidate configuration`
      );
      loadImplementationData();
      setSelectedSuggestion(null);
      alert('Suggestion implemented successfully! Check the candidate configuration version.');
    } catch (error) {
      console.error('Failed to implement suggestion:', error);
      alert('Failed to implement suggestion. Please try manual implementation.');
    }
  };

  const handleManualConfig = (suggestion: EnhancedSuggestion) => {
    const baseUrl = '/admin/configuration';
    const tab = suggestion.suggestion_type === 'regex_pattern' ? 'patterns' : 'templates';
    
    const params = new URLSearchParams({
      tab,
      action: 'add_new',
      from_suggestion: suggestion.id,
      ...(suggestion.pattern && { suggested_pattern: suggestion.pattern }),
      ...(suggestion.template_text && { suggested_template: suggestion.template_text }),
      ...(suggestion.handler && { suggested_handler: suggestion.handler }),
      ...(suggestion.intent && { suggested_intent: suggestion.intent }),
      ...(suggestion.title && { reference_title: suggestion.title })
    });
    
    window.location.href = `${baseUrl}?${params.toString()}`;
  };

  const handleFullReview = (suggestion: EnhancedSuggestion) => {
    setSelectedSuggestion(suggestion);
    setShowFullReview(true);
  };

  const handleReviewModalClose = () => {
    setShowFullReview(false);
    setSelectedSuggestion(null);
    loadImplementationData();
  };

  const filteredSuggestions = approvedSuggestions.filter(suggestion => {
    const matchesStatus = filterStatus === 'all' || getImplementationStatus(suggestion).status === filterStatus;
    const matchesSearch = !searchTerm || 
      suggestion.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
      suggestion.handler?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      suggestion.intent?.toLowerCase().includes(searchTerm.toLowerCase()) ||
      suggestion.created_by_name?.toLowerCase().includes(searchTerm.toLowerCase());
    
    return matchesStatus && matchesSearch;
  });

  const columns: TableColumn<EnhancedSuggestion>[] = [
    {
      key: 'title',
      label: 'Suggestion',
      render: (title: string, suggestion: EnhancedSuggestion) => (
        <div className="min-w-0">
          <div className="font-medium text-sm truncate">{title}</div>
          <div className="flex items-center gap-2 mt-1">
            <span className={`inline-flex items-center px-2 py-0.5 rounded-full text-xs font-medium ${
              suggestion.suggestion_type === 'regex_pattern' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' :
              suggestion.suggestion_type === 'prompt_template' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' :
              'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200'
            }`}>
              {suggestion.suggestion_type.replace('_', ' ')}
            </span>
            {suggestion.action_items && suggestion.action_items.length > 0 && (
              <span className="text-xs text-neutral-500">
                {suggestion.action_items.length} action item{suggestion.action_items.length > 1 ? 's' : ''}
              </span>
            )}
          </div>
        </div>
      ),
    },
    {
      key: 'created_by_name',
      label: 'Submitted By',
      render: (name: string) => (
        <div className="flex items-center gap-1 text-sm">
          <User size={12} className="text-neutral-400" />
          <span className="truncate">{name}</span>
        </div>
      ),
      width: '150px',
    },
    {
      key: 'created_at',
      label: 'Date',
      render: (date: string) => (
        <span className="text-sm">{new Date(date).toLocaleDateString()}</span>
      ),
      width: '120px',
    },
    {
      key: 'handler',
      label: 'Handler',
      render: (handler: string) => (
        <code className="text-xs bg-gray-100 dark:bg-gray-800 px-2 py-1 rounded">
          {handler}
        </code>
      ),
      width: '120px',
    },
    {
      key: 'intent',
      label: 'Intent',
      render: (intent: string) => (
        <span className="text-sm font-medium">{intent}</span>
      ),
      width: '120px',
    },
    {
      key: 'id',
      label: 'Status',
      render: (_, suggestion: EnhancedSuggestion) => {
        const status = getImplementationStatus(suggestion);
        return (
          <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${status.color}`}>
            {status.label}
          </span>
        );
      },
      width: '150px',
    },
  ];

  const actions: TableAction<EnhancedSuggestion>[] = [
    {
      label: 'View',
      icon: <Eye size={14} />,
      onClick: setSelectedSuggestion,
      variant: 'secondary',
    }
  ];

  const handleReview = async (suggestionId: string, reviewData: any) => {
    try {
      await suggestionsService.reviewSuggestionEnhanced(suggestionId, reviewData);
      handleReviewModalClose();
    } catch (error) {
      console.error('Failed to review suggestion:', error);
      throw error;
    }
  };

  const handleCreateActionItem = async (suggestionId: string, actionItem: any) => {
    try {
      await suggestionsService.createActionItem(suggestionId, actionItem);
      loadImplementationData();
    } catch (error) {
      console.error('Failed to create action item:', error);
      throw error;
    }
  };

  const handleMarkAddressed = async (suggestionId: string, notes: string) => {
    try {
      await suggestionsService.markSuggestionAddressed(suggestionId, notes);
      handleReviewModalClose();
    } catch (error) {
      console.error('Failed to mark as addressed:', error);
      throw error;
    }
  };

  return (
    <>
      <div className="space-y-4">
        {/* Single Row Filter and Search Bar */}
        <div className="card p-3 sm:p-4">
          <div className="flex flex-col lg:flex-row lg:items-center gap-3 lg:gap-4">
            {/* Status Filter */}
            <div className="flex items-center gap-2">
              <label className="text-sm font-medium whitespace-nowrap">Filter by Status:</label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="input w-48 text-sm"
              >
                <option value="all">All ({approvedSuggestions.length})</option>
                <option value="needs_items">
                  Needs Action Items ({approvedSuggestions.filter(s => getImplementationStatus(s).status === 'needs_items').length})
                </option>
                <option value="pending">
                  Pending Start ({approvedSuggestions.filter(s => getImplementationStatus(s).status === 'pending').length})
                </option>
                <option value="in_progress">
                  In Progress ({approvedSuggestions.filter(s => getImplementationStatus(s).status === 'in_progress').length})
                </option>
                <option value="ready">
                  Ready to Complete ({approvedSuggestions.filter(s => getImplementationStatus(s).status === 'ready').length})
                </option>
              </select>
            </div>

            {/* Search Bar - Flexible width */}
            <div className="relative flex-1 min-w-0">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-neutral-400" size={16} />
              <input
                type="text"
                placeholder="Search by title, handler, intent, or submitter..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="w-full pl-10 pr-4 py-2 border border-neutral-300 dark:border-neutral-600 rounded-lg 
                           bg-white dark:bg-neutral-800 focus:ring-2 focus:ring-[--color-brand] focus:border-transparent text-sm"
              />
            </div>
            
            {/* Refresh Button */}
            <Button
              onClick={loadImplementationData}
              className="btn-secondary text-sm whitespace-nowrap"
            >
              Refresh Queue
            </Button>
          </div>
        </div>

        {/* Table */}
        <DataTable
          data={filteredSuggestions}
          columns={columns}
          actions={actions}
          loading={loading}
          searchable={false}
          emptyMessage={
            filterStatus === 'all' && !searchTerm
              ? "No approved suggestions pending implementation"
              : `No suggestions found matching your filters`
          }
        />
      </div>

      {/* Implementation Details Modal */}
      <Modal
        isOpen={selectedSuggestion !== null && !showFullReview}
        onClose={() => setSelectedSuggestion(null)}
        title={selectedSuggestion?.title || ''}
        size="xl"
      >
        {selectedSuggestion && (
          <div className="space-y-6">
            <div className="bg-neutral-50 dark:bg-neutral-800/50 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <span className={`px-3 py-1 rounded-full text-sm font-medium ${getImplementationStatus(selectedSuggestion).color}`}>
                  {getImplementationStatus(selectedSuggestion).label}
                </span>
                <span className="text-sm text-neutral-500">•</span>
                <span className="text-sm text-neutral-600 dark:text-neutral-400">
                  {selectedSuggestion.created_by_name}
                </span>
                <span className="text-sm text-neutral-500">•</span>
                <span className="text-sm text-neutral-600 dark:text-neutral-400">
                  {new Date(selectedSuggestion.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h5 className="font-semibold">Implementation Details</h5>
                
                {selectedSuggestion.description && (
                  <div>
                    <h6 className="font-medium text-sm mb-2">Description:</h6>
                    <div className="bg-white dark:bg-neutral-800 p-3 rounded-lg border text-sm">
                      {selectedSuggestion.description}
                    </div>
                  </div>
                )}
                
                {selectedSuggestion.admin_analysis && (
                  <div>
                    <h6 className="font-medium text-sm mb-2">Admin Analysis:</h6>
                    <div className="bg-white dark:bg-neutral-800 p-3 rounded-lg border text-sm">
                      {selectedSuggestion.admin_analysis}
                    </div>
                  </div>
                )}
                
                {(selectedSuggestion.pattern || selectedSuggestion.template_text) && (
                  <div>
                    <h6 className="font-medium text-sm mb-2">
                      Proposed {selectedSuggestion.suggestion_type === 'regex_pattern' ? 'Pattern' : 'Template'}:
                    </h6>
                    <code className="block bg-white dark:bg-neutral-800 p-3 rounded-lg border text-sm overflow-x-auto font-mono">
                      {selectedSuggestion.pattern || selectedSuggestion.template_text}
                    </code>
                  </div>
                )}
              </div>
              
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <h5 className="font-semibold">Action Items</h5>
                  <Button
                    onClick={() => handleFullReview(selectedSuggestion)}
                    className="text-xs btn-secondary flex items-center gap-1"
                  >
                    <Plus size={12} />
                    Add Items
                  </Button>
                </div>
                
                {selectedSuggestion.action_items && selectedSuggestion.action_items.length > 0 ? (
                  <div className="space-y-2">
                    {selectedSuggestion.action_items.map((item) => (
                      <div key={item.id} className="bg-white dark:bg-neutral-800 p-3 rounded-lg border">
                        <div className="flex items-start justify-between mb-1">
                          <h6 className="font-medium text-sm">{item.title}</h6>
                          <span className={`px-2 py-0.5 rounded-full text-xs ml-2 whitespace-nowrap ${
                            item.status === 'completed' ? 'bg-green-100 text-green-800 dark:bg-green-900/30 dark:text-green-200' :
                            item.status === 'in_progress' ? 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-200' :
                            'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200'
                          }`}>
                            {item.status.replace('_', ' ')}
                          </span>
                        </div>
                        <p className="text-xs text-neutral-600 dark:text-neutral-400">{item.description}</p>
                      </div>
                    ))}
                  </div>
                ) : (
                  <div className="text-center py-6 text-neutral-500 bg-white dark:bg-neutral-800 rounded-lg border">
                    <AlertTriangle size={24} className="mx-auto mb-2 opacity-50" />
                    <p className="text-sm">No action items yet</p>
                  </div>
                )}
              </div>
            </div>
            
            <div className="flex gap-3 pt-4 border-t">
              {canQuickImplement(selectedSuggestion) && (
                <Button onClick={() => handleQuickImplement(selectedSuggestion)}>
                  <Wrench size={16} className="mr-2" />
                  Quick Implement
                </Button>
              )}
              <Button onClick={() => handleManualConfig(selectedSuggestion)} className="btn-secondary">
                <ExternalLink size={16} className="mr-2" />
                Manual Configuration
              </Button>
              <Button onClick={() => handleFullReview(selectedSuggestion)} className="btn-secondary">
                Full Review
              </Button>
            </div>
          </div>
        )}
      </Modal>

      {/* Full Review Modal */}
      {showFullReview && selectedSuggestion && (
        <SuggestionReviewModal
          suggestion={selectedSuggestion}
          onClose={handleReviewModalClose}
          onReview={handleReview}
          onCreateActionItem={handleCreateActionItem}
          onMarkAddressed={handleMarkAddressed}
        />
      )}
    </>
  );
}