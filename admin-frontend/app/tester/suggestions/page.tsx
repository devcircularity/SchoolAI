// app/tester/suggestions/page.tsx - Updated with header title management
"use client";
import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { canAccessTesterQueue } from "@/utils/permissions";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { testerService, TesterSuggestion } from "@/services/tester";
import DataTable, { TableColumn, TableAction } from "@/components/ui/DataTable";
import { Eye, Plus, Filter, RefreshCw, Clock, CheckCircle, XCircle, AlertTriangle, Zap, X } from "lucide-react";
import Button from "@/components/ui/Button";

interface SuggestionWithDetails extends Omit<TesterSuggestion, 'description'> {
  description?: string;
  pattern?: string;
  template_text?: string;
  tester_note?: string;
  original_message?: string;
  assistant_response?: string;
}

export default function TesterSuggestionsPage() {
  const { user } = useAuth();
  const [suggestions, setSuggestions] = useState<TesterSuggestion[]>([]);
  const [loading, setLoading] = useState(true);
  const [selectedStatus, setSelectedStatus] = useState<string>('');
  const [selectedType, setSelectedType] = useState<string>('');
  const [selectedSuggestion, setSelectedSuggestion] = useState<SuggestionWithDetails | null>(null);

  // Set header title on mount
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'My Suggestions', 
      subtitle: 'Track and manage your submitted suggestions' 
    });
    
    return () => {
      HeaderTitleBus.send({ type: 'clear' });
    };
  }, []);

  // Update subtitle with count and filters when data changes
  useEffect(() => {
    let subtitle = `Track and manage your submitted suggestions (${suggestions.length} total)`;
    
    const activeFilters = [];
    if (selectedStatus) {
      const statusLabels = { 'pending': 'Pending', 'approved': 'Approved', 'rejected': 'Rejected', 'implemented': 'Implemented' };
      activeFilters.push((statusLabels as Record<string, string>)[selectedStatus] || selectedStatus);
    }
    if (selectedType) {
      const typeLabels = { 'regex_pattern': 'Pattern', 'prompt_template': 'Template', 'intent_mapping': 'Intent', 'handler_improvement': 'Handler' };
      activeFilters.push((typeLabels as Record<string, string>)[selectedType] || selectedType);
    }
    
    if (activeFilters.length > 0) {
      subtitle += ` • Filtered: ${activeFilters.join(', ')}`;
    }

    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'My Suggestions', 
      subtitle 
    });
  }, [suggestions.length, selectedStatus, selectedType]);

  useEffect(() => {
    loadSuggestions();
  }, [selectedStatus, selectedType]);

  const loadSuggestions = async () => {
    try {
      setLoading(true);
      const params = {
        limit: 50,
        ...(selectedStatus && { status: selectedStatus }),
        ...(selectedType && { suggestion_type: selectedType })
      };
      
      const data = await testerService.getMySuggestions(params);
      setSuggestions(data);
    } catch (error) {
      console.error('Failed to load suggestions:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleViewSuggestion = (suggestion: TesterSuggestion) => {
    setSelectedSuggestion(suggestion as SuggestionWithDetails);
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'pending': return <Clock className="text-gray-500" size={12} />;
      case 'approved': return <CheckCircle className="text-green-600" size={12} />;
      case 'rejected': return <XCircle className="text-red-600" size={12} />;
      case 'implemented': return <Zap className="text-purple-600" size={12} />;
      default: return <AlertTriangle className="text-yellow-600" size={12} />;
    }
  };

  const columns: TableColumn<TesterSuggestion>[] = [
    {
      key: 'created_at',
      label: 'Time',
      render: (date: string) => {
        const submitDate = new Date(date);
        const now = new Date();
        const diffDays = Math.floor((now.getTime() - submitDate.getTime()) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return <span className="text-xs">Today</span>;
        if (diffDays === 1) return <span className="text-xs">Yesterday</span>;
        if (diffDays < 7) return <span className="text-xs">{diffDays}d</span>;
        return <span className="text-xs">{submitDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>;
      },
      width: '70px',
      sortable: true,
    },
    {
      key: 'title',
      label: 'Title',
      render: (title: string) => (
        <div className="max-w-xs truncate text-xs font-medium" title={title}>
          {title}
        </div>
      ),
    },
    {
      key: 'suggestion_type',
      label: 'Type',
      render: (type: string) => {
        const typeLabels = {
          'regex_pattern': 'Pattern',
          'prompt_template': 'Template',
          'intent_mapping': 'Intent',
          'handler_improvement': 'Handler'
        };
        const typeColors = {
          'regex_pattern': 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200',
          'prompt_template': 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200',
          'intent_mapping': 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200',
          'handler_improvement': 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200'
        };
        return (
          <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${(typeColors as Record<string, string>)[type] || typeColors.handler_improvement}`}>
            {(typeLabels as Record<string, string>)[type] || type}
          </span>
        );
      },
      width: '80px',
    },
    {
      key: 'handler',
      label: 'Handler',
      render: (handler: string) => (
        <code className="text-xs bg-gray-100 dark:bg-gray-800 px-1.5 py-0.5 rounded truncate" title={handler}>
          {handler.length > 12 ? handler.substring(0, 12) + '...' : handler}
        </code>
      ),
      width: '100px',
    },
    {
      key: 'priority',
      label: 'Pri',
      render: (priority: string) => {
        const priorityLabels = { 'critical': 'C', 'high': 'H', 'medium': 'M', 'low': 'L' };
        const priorityColors = {
          'critical': 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-200',
          'high': 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-200',
          'medium': 'bg-yellow-100 text-yellow-800 dark:bg-yellow-900/30 dark:text-yellow-200',
          'low': 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-200'
        };
        return (
          <span className={`inline-flex items-center justify-center w-5 h-5 rounded text-xs font-medium ${(priorityColors as Record<string, string>)[priority] || priorityColors.low}`}>
            {(priorityLabels as Record<string, string>)[priority] || 'M'}
          </span>
        );
      },
      width: '40px',
    },
    {
      key: 'status',
      label: 'Status',
      render: (status: string) => {
        const statusLabels = { 'pending': 'Pending', 'approved': 'Approved', 'rejected': 'Rejected', 'implemented': 'Live' };
        return (
          <div className="flex items-center gap-1">
            {getStatusIcon(status)}
            <span className={`inline-flex items-center px-1.5 py-0.5 rounded text-xs font-medium ${testerService.getSuggestionStatusColor(status)}`}>
              {(statusLabels as Record<string, string>)[status] || status}
            </span>
          </div>
        );
      },
      width: '100px',
    },
    {
      key: 'reviewed_at',
      label: 'Reviewed',
      render: (date: string) => {
        if (!date) return <span className="text-gray-400 text-xs">-</span>;
        const reviewDate = new Date(date);
        const now = new Date();
        const diffDays = Math.floor((now.getTime() - reviewDate.getTime()) / (1000 * 60 * 60 * 24));
        
        if (diffDays === 0) return <span className="text-xs">Today</span>;
        if (diffDays === 1) return <span className="text-xs">Yesterday</span>;
        if (diffDays < 7) return <span className="text-xs">{diffDays}d</span>;
        return <span className="text-xs">{reviewDate.toLocaleDateString('en-US', { month: 'short', day: 'numeric' })}</span>;
      },
      width: '70px',
    },
  ];

  const actions: TableAction<TesterSuggestion>[] = [
    {
      label: 'View',
      icon: <Eye size={12} />,
      onClick: handleViewSuggestion,
      variant: 'secondary',
    },
  ];

  if (!canAccessTesterQueue(user)) {
    return (
      <div className="p-4 sm:p-6">
        <div className="text-center">
          <h1 className="text-xl sm:text-2xl font-bold mb-4">Access Denied</h1>
          <p className="text-neutral-600">You don't have permission to access tester suggestions.</p>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen flex flex-col">
      <div className="flex-1 p-4 sm:p-6 overflow-auto">
        {/* Action buttons - Simplified since title is now in HeaderBar */}
        <div className="flex justify-end gap-2 mb-6">
          <Button 
            onClick={loadSuggestions}
            className="flex items-center gap-2 btn-secondary text-sm"
          >
            <RefreshCw size={16} />
            <span>Refresh</span>
          </Button>
          <Button 
            onClick={() => window.location.href = '/tester/queue'}
            className="flex items-center gap-2 text-sm"
          >
            <Plus size={16} />
            <span className="sm:hidden">New</span>
            <span className="hidden sm:inline">Create New</span>
          </Button>
        </div>

        {/* Filters - More compact layout */}
        <div className="card p-3 mb-4">
          <div className="flex flex-col gap-3">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              <div>
                <label className="block text-xs font-medium mb-1">Status</label>
                <select
                  value={selectedStatus}
                  onChange={(e) => setSelectedStatus(e.target.value)}
                  className="input w-full text-sm"
                >
                  <option value="">All Statuses</option>
                  <option value="pending">Pending</option>
                  <option value="approved">Approved</option>
                  <option value="rejected">Rejected</option>
                  <option value="implemented">Implemented</option>
                </select>
              </div>
              
              <div>
                <label className="block text-xs font-medium mb-1">Type</label>
                <select
                  value={selectedType}
                  onChange={(e) => setSelectedType(e.target.value)}
                  className="input w-full text-sm"
                >
                  <option value="">All Types</option>
                  <option value="regex_pattern">Pattern</option>
                  <option value="prompt_template">Template</option>
                  <option value="intent_mapping">Intent</option>
                  <option value="handler_improvement">Handler</option>
                </select>
              </div>
            </div>
            
            <Button 
              onClick={() => {
                setSelectedStatus('');
                setSelectedType('');
              }}
              className="flex items-center gap-2 btn-secondary text-sm w-full"
            >
              <Filter size={16} />
              Clear Filters
            </Button>
          </div>
        </div>

        {/* Data Table - Flexible height */}
        <div className="flex-1 min-h-[500px]">
          <DataTable
            data={suggestions}
            columns={columns}
            actions={actions}
            loading={loading}
            searchable
            searchPlaceholder="Search suggestions..."
            emptyMessage="No suggestions found"
            className="text-xs"
          />
        </div>
      </div>

      {/* Suggestion Detail Modal */}
      {selectedSuggestion && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div className="absolute inset-0 bg-black/50" onClick={() => setSelectedSuggestion(null)} />
          <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl w-full max-w-2xl max-h-[90vh] overflow-y-auto">
            <div className="p-4 sm:p-6">
              <div className="flex justify-between items-start mb-4">
                <div className="flex-1 pr-4">
                  <h2 className="text-lg font-bold">{selectedSuggestion.title}</h2>
                  <p className="text-xs text-neutral-600 dark:text-neutral-400 mt-1">
                    Submitted {new Date(selectedSuggestion.created_at).toLocaleDateString()}
                  </p>
                </div>
                <button 
                  onClick={() => setSelectedSuggestion(null)}
                  className="p-2 hover:bg-neutral-100 dark:hover:bg-neutral-700 rounded-lg transition-colors flex-shrink-0"
                >
                  <X size={16} />
                </button>
              </div>

              <div className="space-y-4">
                {/* Status */}
                <div className={`p-3 rounded-lg border flex items-center gap-2 ${
                  selectedSuggestion.status === 'pending' ? 'bg-blue-50 dark:bg-blue-900/20 border-blue-200 dark:border-blue-800' :
                  selectedSuggestion.status === 'approved' ? 'bg-green-50 dark:bg-green-900/20 border-green-200 dark:border-green-800' :
                  selectedSuggestion.status === 'implemented' ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-200 dark:border-purple-800' :
                  'bg-red-50 dark:bg-red-900/20 border-red-200 dark:border-red-800'
                }`}>
                  {getStatusIcon(selectedSuggestion.status)}
                  <div className="flex-1">
                    <div className="flex flex-col sm:flex-row sm:items-center gap-1 sm:gap-2">
                      <span className={`font-medium text-sm ${
                        selectedSuggestion.status === 'pending' ? 'text-blue-800 dark:text-blue-200' :
                        selectedSuggestion.status === 'approved' ? 'text-green-800 dark:text-green-200' :
                        selectedSuggestion.status === 'implemented' ? 'text-purple-800 dark:text-purple-200' :
                        'text-red-800 dark:text-red-200'
                      }`}>
                        {selectedSuggestion.status === 'pending' && 'Pending Review'}
                        {selectedSuggestion.status === 'approved' && 'Approved'}
                        {selectedSuggestion.status === 'implemented' && 'Implemented'}
                        {selectedSuggestion.status === 'rejected' && 'Rejected'}
                      </span>
                      <span className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-medium ${
                        selectedSuggestion.suggestion_type === 'regex_pattern' ? 'bg-blue-100 dark:bg-blue-900/30 text-blue-800 dark:text-blue-200' :
                        selectedSuggestion.suggestion_type === 'prompt_template' ? 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200' :
                        'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200'
                      }`}>
                        {selectedSuggestion.suggestion_type.replace('_', ' ')}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Description */}
                <div>
                  <h3 className="font-medium text-sm mb-2">Your Analysis</h3>
                  <div className="text-sm bg-neutral-50 dark:bg-neutral-700 p-3 rounded">
                    {selectedSuggestion.description || 'Detailed analysis of the issue and suggested improvements.'}
                  </div>
                </div>

                {/* Proposed Solution */}
                {(selectedSuggestion.pattern || selectedSuggestion.template_text) && (
                  <div>
                    <h3 className="font-medium text-sm mb-2">Proposed Solution</h3>
                    {selectedSuggestion.pattern && (
                      <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded border border-blue-200 dark:border-blue-800">
                        <code className="text-xs font-mono block break-all">
                          {selectedSuggestion.pattern}
                        </code>
                      </div>
                    )}
                    {selectedSuggestion.template_text && (
                      <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded border border-green-200 dark:border-green-800">
                        <div className="text-xs whitespace-pre-wrap">
                          {selectedSuggestion.template_text}
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Admin Feedback */}
                {selectedSuggestion.admin_note && (
                  <div>
                    <h3 className="font-medium text-sm mb-2">Admin Feedback</h3>
                    <div className="text-sm bg-neutral-50 dark:bg-neutral-700 p-3 rounded">
                      {selectedSuggestion.admin_note}
                    </div>
                  </div>
                )}

                {/* Bottom info */}
                <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-2 pt-3 border-t text-xs text-neutral-500">
                  <span>Priority: {selectedSuggestion.priority}</span>
                  {selectedSuggestion.reviewed_at && (
                    <span>Reviewed {new Date(selectedSuggestion.reviewed_at).toLocaleDateString()}</span>
                  )}
                </div>

                {/* Action only for rejected */}
                {selectedSuggestion.status === 'rejected' && (
                  <div className="pt-2">
                    <Button 
                      onClick={() => {
                        alert('Feature coming soon: Create revised suggestion based on feedback');
                      }}
                      className="w-full text-sm"
                    >
                      Create Revised Version
                    </Button>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}