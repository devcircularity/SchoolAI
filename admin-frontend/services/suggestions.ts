// services/suggestions.ts - Enhanced with action items workflow
import { apiClient } from './api';

export interface Suggestion {
  id: string;
  chat_message_id?: string;
  routing_log_id?: string;
  suggestion_type: 'regex_pattern' | 'prompt_template' | 'intent_mapping' | 'handler_improvement';
  title: string;
  description: string;
  handler: string;
  intent: string;
  pattern?: string;
  template_text?: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  tester_note?: string;
  admin_note?: string;
  status: 'pending' | 'approved' | 'rejected' | 'implemented' | 'needs_analysis';
  created_by: string;
  created_by_name: string;
  reviewed_by?: string;
  reviewed_by_name?: string;
  school_id?: string;
  created_at: string;
  updated_at: string;
  reviewed_at?: string;
  implemented_at?: string;
  original_message?: string;
  assistant_response?: string;
  
  // Enhanced fields for new workflow
  admin_analysis?: string;
  implementation_notes?: string;
  action_items?: ActionItem[];
}

export interface ActionItem {
  id: string;
  suggestion_id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  implementation_type: 'pattern' | 'template' | 'code_fix' | 'documentation' | 'other';
  assigned_to?: string;
  assigned_to_name?: string;
  created_by: string;
  created_by_name: string;
  due_date?: string;
  completed_at?: string;
  completion_notes?: string;
  created_at: string;
  updated_at: string;
}

export interface SuggestionListResponse {
  suggestions: Suggestion[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

export interface ReviewSuggestionRequest {
  status: 'approved' | 'rejected';
  admin_note?: string;
  auto_implement?: boolean;
}

// Enhanced review request
export interface EnhancedReviewSuggestionRequest {
  status: 'approved' | 'rejected' | 'needs_analysis';
  admin_note?: string;
  admin_analysis?: string;
  implementation_notes?: string;
  create_action_items?: boolean;
  action_items?: Array<{
    title: string;
    description: string;
    priority: 'low' | 'medium' | 'high' | 'critical';
    implementation_type: 'pattern' | 'template' | 'code_fix' | 'documentation' | 'other';
    due_date?: string;
    assigned_to?: string;
  }>;
}

export interface CreateActionItemRequest {
  suggestion_id: string;
  title: string;
  description: string;
  priority: 'low' | 'medium' | 'high' | 'critical';
  implementation_type: 'pattern' | 'template' | 'code_fix' | 'documentation' | 'other';
  assigned_to?: string;
  due_date?: string;
}

export interface SuggestionStats {
  total_suggestions: number;
  pending: number;
  approved: number;
  rejected: number;
  implemented: number;
  needs_analysis?: number;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
}

export interface EnhancedSuggestionStats extends SuggestionStats {
  action_items: {
    total: number;
    pending: number;
    in_progress: number;
    completed: number;
    overdue: number;
  };
  suggestions_with_action_items: number;
  avg_time_to_resolution?: number;
}

export interface TesterSuggestion {
  message_id?: string;
  routing_log_id?: string;
  suggestion_type: 'regex_pattern' | 'prompt_template' | 'intent_mapping' | 'handler_improvement';
  title: string;
  description: string;
  handler: string;
  intent: string;
  pattern?: string;
  template_text?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  tester_note?: string;
}

export interface ProblematicMessage {
  message_id: string;
  conversation_id: string;
  user_message: string;
  assistant_response: string;
  intent?: string;
  rating?: number;
  rated_at?: string;
  created_at: string;
  processing_time_ms?: number;
  routing_log_id?: string;
  llm_intent?: string;
  llm_confidence?: number;
  router_intent?: string;
  final_intent?: string;
  fallback_used?: boolean;
  issue_type: string;
  priority: number;
  school_id?: string;
  user_id: string;
}

export interface TesterStats {
  total_messages: number;
  negative_ratings: number;
  fallback_used: number;
  low_confidence: number;
  unhandled: number;
  needs_attention: number;
  by_priority: Record<string, number>;
  by_issue_type: Record<string, number>;
}

class SuggestionsService {
  // ADMIN: Suggestion Management
  async getSuggestions(filters?: {
    page?: number;
    limit?: number;
    status?: string;
    suggestion_type?: string;
    priority?: string;
    created_by?: string;
    school_id?: string;
    pending_only?: boolean;
  }): Promise<SuggestionListResponse> {
    const params = new URLSearchParams();
    if (filters?.page) params.append('page', filters.page.toString());
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.status) params.append('status', filters.status);
    if (filters?.suggestion_type) params.append('suggestion_type', filters.suggestion_type);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.created_by) params.append('created_by', filters.created_by);
    if (filters?.school_id) params.append('school_id', filters.school_id);
    if (filters?.pending_only) params.append('pending_only', 'true');

    const response = await apiClient.get(`/api/admin/suggestions?${params.toString()}`);
    return response.data;
  }

  async getSuggestionStats(): Promise<SuggestionStats> {
    const response = await apiClient.get('/api/admin/suggestions/stats');
    return response.data;
  }

  // NEW: Get enhanced stats with action items
  async getEnhancedSuggestionStats(): Promise<EnhancedSuggestionStats> {
    const response = await apiClient.get('/api/admin/suggestions/stats-enhanced');
    return response.data;
  }

  async getSuggestion(suggestionId: string): Promise<Suggestion> {
    const response = await apiClient.get(`/api/admin/suggestions/${suggestionId}`);
    return response.data;
  }

  // Legacy review method (kept for backward compatibility)
  async reviewSuggestion(
    suggestionId: string,
    data: ReviewSuggestionRequest
  ): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/suggestions/${suggestionId}/review`, data);
    return response.data;
  }

  // NEW: Enhanced review with action items
  async reviewSuggestionEnhanced(
    suggestionId: string,
    data: EnhancedReviewSuggestionRequest
  ): Promise<{ 
    message: string; 
    action_items_created?: Array<{ id: string; title: string }> 
  }> {
    const response = await apiClient.post(
      `/api/admin/suggestions/${suggestionId}/review-enhanced`, 
      data
    );
    return response.data;
  }

  // Legacy implement method (kept for backward compatibility)
  async implementSuggestion(suggestionId: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/suggestions/${suggestionId}/implement`);
    return response.data;
  }

  // NEW: Mark suggestion as manually addressed
  async markSuggestionAddressed(
    suggestionId: string, 
    completionNotes: string
  ): Promise<{ message: string; suggestion_id: string }> {
    const response = await apiClient.post(
      `/api/admin/suggestions/${suggestionId}/mark-addressed`,
      { completion_notes: completionNotes }
    );
    return response.data;
  }

  // ACTION ITEM MANAGEMENT

  // NEW: Create action item for a suggestion
  async createActionItem(
    suggestionId: string,
    data: CreateActionItemRequest
  ): Promise<{ id: string; title: string; message: string }> {
    const response = await apiClient.post(
      `/api/admin/suggestions/${suggestionId}/action-items`,
      data
    );
    return response.data;
  }

  // NEW: Get action items for a suggestion
  async getSuggestionActionItems(suggestionId: string): Promise<{
    suggestion_id: string;
    action_items: ActionItem[];
  }> {
    const response = await apiClient.get(`/api/admin/suggestions/${suggestionId}/action-items`);
    return response.data;
  }

  // NEW: Update action item status
  async updateActionItemStatus(
    actionItemId: string,
    status: 'pending' | 'in_progress' | 'completed' | 'cancelled',
    completionNotes?: string
  ): Promise<{ message: string; action_item_id: string }> {
    const response = await apiClient.patch(`/api/admin/suggestions/action-items/${actionItemId}`, {
      status,
      completion_notes: completionNotes
    });
    return response.data;
  }

  // NEW: Complete an action item
  async completeActionItem(
    actionItemId: string, 
    completionNotes?: string
  ): Promise<{ message: string; action_item_id: string }> {
    const response = await apiClient.post(
      `/api/admin/suggestions/action-items/${actionItemId}/complete`,
      { completion_notes: completionNotes }
    );
    return response.data;
  }

  // NEW: Get all action items (across suggestions)
  async getAllActionItems(filters?: {
    status?: string;
    priority?: string;
    implementation_type?: string;
    assigned_to?: string;
    due_date_before?: string;
    due_date_after?: string;
    limit?: number;
    page?: number;
  }): Promise<{
    action_items: ActionItem[];
    total: number;
    page: number;
    limit: number;
    has_next: boolean;
  }> {
    const params = new URLSearchParams();
    if (filters?.status) params.append('status', filters.status);
    if (filters?.priority) params.append('priority', filters.priority);
    if (filters?.implementation_type) params.append('implementation_type', filters.implementation_type);
    if (filters?.assigned_to) params.append('assigned_to', filters.assigned_to);
    if (filters?.due_date_before) params.append('due_date_before', filters.due_date_before);
    if (filters?.due_date_after) params.append('due_date_after', filters.due_date_after);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.page) params.append('page', filters.page.toString());

    const response = await apiClient.get(`/api/admin/suggestions/action-items?${params.toString()}`);
    return response.data;
  }

  // TESTER: Queue and Suggestions (unchanged)
  async getTesterQueue(filters?: {
    priority?: number;
    issue_type?: string;
    limit?: number;
    days_back?: number;
    school_id?: string;
  }): Promise<ProblematicMessage[]> {
    const params = new URLSearchParams();
    if (filters?.priority) params.append('priority', filters.priority.toString());
    if (filters?.issue_type) params.append('issue_type', filters.issue_type);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.days_back) params.append('days_back', filters.days_back.toString());
    if (filters?.school_id) params.append('school_id', filters.school_id);

    const response = await apiClient.get(`/api/tester/queue?${params.toString()}`);
    return response.data;
  }

  async submitTesterSuggestion(data: TesterSuggestion): Promise<{
    message: string;
    suggestion_id: string;
    status: string;
    title: string;
    suggestion_type: string;
    priority: string;
    created_at: string;
  }> {
    const response = await apiClient.post('/api/tester/suggestions', data);
    return response.data;
  }

  async getMyTesterSuggestions(filters?: {
    limit?: number;
    status?: string;
    suggestion_type?: string;
  }): Promise<Suggestion[]> {
    const params = new URLSearchParams();
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.status) params.append('status', filters.status);
    if (filters?.suggestion_type) params.append('suggestion_type', filters.suggestion_type);

    const response = await apiClient.get(`/api/tester/suggestions?${params.toString()}`);
    return response.data;
  }

  async getTesterStats(filters?: {
    days_back?: number;
    school_id?: string;
  }): Promise<TesterStats> {
    const params = new URLSearchParams();
    if (filters?.days_back) params.append('days_back', filters.days_back.toString());
    if (filters?.school_id) params.append('school_id', filters.school_id);

    const response = await apiClient.get(`/api/tester/stats?${params.toString()}`);
    return response.data;
  }

  async getTesterFilters(): Promise<{
    priorities: number[];
    issue_types: string[];
    date_ranges: string[];
  }> {
    const response = await apiClient.get('/api/tester/filters');
    return response.data;
  }
}

export const suggestionsService = new SuggestionsService();