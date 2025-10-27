// services/tester.ts - Complete updated version with higher limits and pagination
import { apiClient } from './api';

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
  
  // Routing information
  routing_log_id?: string;
  llm_intent?: string;
  llm_confidence?: number;
  router_intent?: string;
  final_intent?: string;
  fallback_used?: boolean;
  
  // Context for understanding the issue
  issue_type: string;
  priority: number;
  
  // Additional context
  school_id?: string;
  user_id: string;
}

export interface ConversationMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  intent?: string;
  rating?: number;
  processing_time_ms?: number;
  is_problematic?: boolean;
}

export interface TesterSuggestionCreate {
  message_id?: string;
  routing_log_id?: string;
  suggestion_type: string;  // Will be mapped in submitSuggestion method
  title: string;
  description: string;
  handler: string;
  intent: string;
  pattern?: string;
  template_text?: string;
  priority?: 'low' | 'medium' | 'high' | 'critical';
  tester_note?: string;
}

export interface TesterSuggestion {
  id: string;
  title: string;
  suggestion_type: string;
  handler: string;
  intent: string;
  status: string;
  priority: string;
  created_at: string;
  reviewed_at?: string;
  admin_note?: string;
  description: string;
  pattern?: string;
  template_text?: string;
  tester_note?: string;
  chat_message_id?: string;
  routing_log_id?: string;
  original_message?: string;
  assistant_response?: string;
}

export interface TesterStats {
  total_messages: number;
  negative_ratings: number;
  fallback_used: number;
  low_confidence: number;
  unhandled: number;
  needs_attention: number;
  by_priority: {
    high: number;
    medium: number;
    low: number;
  };
  by_issue_type: {
    negative_rating: number;
    fallback: number;
    low_confidence: number;
    unhandled: number;
  };
}

export interface QueueFilters {
  priorities: number[];
  issue_types: string[];
  date_ranges: string[];
}

export interface GetQueueParams {
  priority?: number;
  issue_type?: string;
  limit?: number;
  days_back?: number;
  school_id?: string;
  show_suggested?: boolean;
}

export interface GetSuggestionsParams {
  limit?: number;
  status?: string;
  suggestion_type?: string;
  page?: number;
}

export interface GetStatsParams {
  days_back?: number;
  school_id?: string;
}

export interface SuggestionsPaginatedResponse {
  suggestions: TesterSuggestion[];
  total: number;
  page: number;
  limit: number;
  has_next: boolean;
}

class TesterService {
  async getQueue(params: GetQueueParams = {}): Promise<ProblematicMessage[]> {
    const searchParams = new URLSearchParams();
    
    if (params.priority) searchParams.append('priority', params.priority.toString());
    if (params.issue_type) searchParams.append('issue_type', params.issue_type);
    if (params.limit) searchParams.append('limit', params.limit.toString());
    if (params.days_back) searchParams.append('days_back', params.days_back.toString());
    if (params.school_id) searchParams.append('school_id', params.school_id);
    if (params.show_suggested !== undefined) searchParams.append('show_suggested', params.show_suggested.toString());
    
    const response = await apiClient.get(`/api/tester/queue?${searchParams.toString()}`);
    return response.data;
  }

  async getConversation(conversationId: string, messageId?: string): Promise<ConversationMessage[]> {
    try {
      const params = messageId ? `?message_id=${messageId}` : '';
      const response = await apiClient.get(`/api/tester/conversation/${conversationId}${params}`);
      return response.data;
    } catch (error: any) {
      if (error.response?.status === 404) {
        try {
          const fallbackResponse = await apiClient.get(`/api/chat/conversations/${conversationId}/messages`);
          const messages = fallbackResponse.data.map((msg: any) => ({
            id: msg.id || msg.message_id,
            content: msg.content || msg.user_message || msg.assistant_response,
            role: msg.message_type === 'USER' ? 'user' : 'assistant',
            timestamp: msg.created_at,
            intent: msg.intent,
            rating: msg.rating,
            processing_time_ms: msg.processing_time_ms,
            is_problematic: messageId ? (msg.id === messageId || msg.message_id === messageId) : false
          }));
          
          if (messageId) {
            const targetIndex = messages.findIndex((m: any) => m.id === messageId);
            if (targetIndex > 0) {
              const userMessage = messages.slice(0, targetIndex).reverse().find((m: any) => m.role === 'user');
              const targetMessage = messages[targetIndex];
              return userMessage ? [userMessage, targetMessage] : [targetMessage];
            }
            return messages.filter((m: any) => m.id === messageId);
          }
          
          return messages;
        } catch (fallbackError) {
          throw new Error('Unable to load conversation. This feature may not be available yet.');
        }
      }
      throw error;
    }
  }

  async submitSuggestion(suggestion: TesterSuggestionCreate): Promise<{
    message: string;
    suggestion_id: string;
    status: string;
    title: string;
    suggestion_type: string;
    priority: string;
    created_at: string;
  }> {
    // Map frontend suggestion types to backend expected values
    const suggestionTypeMapping: { [key: string]: string } = {
      'user_query': 'regex_pattern',      // User query issues -> regex patterns for better classification
      'ai_response': 'prompt_template',   // AI response issues -> prompt templates for better responses
      'regex_pattern': 'regex_pattern',   // Direct mapping
      'prompt_template': 'prompt_template', // Direct mapping
      'intent_mapping': 'intent_mapping', // Direct mapping
      'handler_improvement': 'handler_improvement' // Direct mapping
    };

    const backendSuggestionType = suggestionTypeMapping[suggestion.suggestion_type] || suggestion.suggestion_type;

    // Build the suggestion payload with backend-compatible structure
    const payload = {
      message_id: suggestion.message_id,
      routing_log_id: suggestion.routing_log_id,
      suggestion_type: backendSuggestionType,
      title: suggestion.title,
      description: suggestion.description,
      handler: suggestion.handler,
      intent: suggestion.intent,
      pattern: suggestion.pattern,
      template_text: suggestion.template_text,
      priority: suggestion.priority || 'medium',
      tester_note: suggestion.tester_note
    };

    const response = await apiClient.post('/api/tester/suggestions', payload);
    return response.data;
  }

  async getMySuggestions(params: GetSuggestionsParams = {}): Promise<TesterSuggestion[]> {
    const searchParams = new URLSearchParams();
    
    // Increased default and maximum limits
    const limit = params.limit ? Math.min(params.limit, 500) : 100;
    searchParams.append('limit', limit.toString());
    
    if (params.status) searchParams.append('status', params.status);
    if (params.suggestion_type) searchParams.append('suggestion_type', params.suggestion_type);
    if (params.page) searchParams.append('page', params.page.toString());
    
    const response = await apiClient.get(`/api/tester/suggestions?${searchParams.toString()}`);
    
    // Log the response to help debug count issues
    console.log(`getMySuggestions: Retrieved ${response.data.length} suggestions with limit ${limit}`);
    
    return response.data;
  }

  async getMySuggestionsPaginated(params: GetSuggestionsParams = {}): Promise<SuggestionsPaginatedResponse> {
    const searchParams = new URLSearchParams();
    
    // Support pagination with higher limits
    const limit = params.limit ? Math.min(params.limit, 500) : 100;
    searchParams.append('limit', limit.toString());
    
    if (params.status) searchParams.append('status', params.status);
    if (params.suggestion_type) searchParams.append('suggestion_type', params.suggestion_type);
    if (params.page) searchParams.append('page', params.page.toString());
    
    const response = await apiClient.get(`/api/tester/suggestions-paginated?${searchParams.toString()}`);
    return response.data;
  }

  async getAllMySuggestions(params: Omit<GetSuggestionsParams, 'limit' | 'page'> = {}): Promise<TesterSuggestion[]> {
    // Get all suggestions by making multiple paginated calls if needed
    let allSuggestions: TesterSuggestion[] = [];
    let page = 1;
    const limit = 100;
    let hasMore = true;

    while (hasMore && page <= 10) { // Safety limit of 10 pages (max 1000 suggestions)
      const suggestions = await this.getMySuggestions({ 
        ...params, 
        limit, 
        page 
      });

      if (suggestions.length === 0) {
        hasMore = false;
      } else {
        allSuggestions.push(...suggestions);
        hasMore = suggestions.length === limit; // If we got fewer than limit, we're done
        page++;
      }
    }

    console.log(`getAllMySuggestions: Retrieved ${allSuggestions.length} total suggestions across ${page - 1} pages`);
    return allSuggestions;
  }

  async getMySuggestionsCount(params: Omit<GetSuggestionsParams, 'limit' | 'page'> = {}): Promise<number> {
    try {
      // Try to get count from a dedicated endpoint if it exists
      const searchParams = new URLSearchParams();
      if (params.status) searchParams.append('status', params.status);
      if (params.suggestion_type) searchParams.append('suggestion_type', params.suggestion_type);
      
      try {
        const response = await apiClient.get(`/api/tester/suggestions/count?${searchParams.toString()}`);
        return response.data.count;
      } catch (error) {
        // Fallback: get all suggestions to count them
        console.log('No count endpoint available, using getAllMySuggestions fallback');
        const allSuggestions = await this.getAllMySuggestions(params);
        return allSuggestions.length;
      }
    } catch (error) {
      console.error('Failed to get suggestions count:', error);
      return 0;
    }
  }

  async getStats(params: GetStatsParams = {}): Promise<TesterStats> {
    const searchParams = new URLSearchParams();
    
    if (params.days_back) searchParams.append('days_back', params.days_back.toString());
    if (params.school_id) searchParams.append('school_id', params.school_id);
    
    const response = await apiClient.get(`/api/tester/stats?${searchParams.toString()}`);
    return response.data;
  }

  async getFilters(): Promise<QueueFilters> {
    const response = await apiClient.get('/api/tester/filters');
    return response.data;
  }

  // Utility methods for suggestion types
  getSuggestionTypes() {
    return [
      { value: 'regex_pattern', label: 'Regex Pattern', description: 'Add or improve message classification patterns' },
      { value: 'prompt_template', label: 'Prompt Template', description: 'Improve response templates for better answers' },
      { value: 'intent_mapping', label: 'Intent Mapping', description: 'Better intent classification for specific handlers' },
      { value: 'handler_improvement', label: 'Handler Improvement', description: 'General handler behavior improvements' }
    ];
  }

  getPriorityLevels() {
    return [
      { value: 'critical', label: 'Critical', description: 'Urgent fixes for broken responses' },
      { value: 'high', label: 'High', description: 'Important improvements for common issues' },
      { value: 'medium', label: 'Medium', description: 'General improvements and optimizations' },
      { value: 'low', label: 'Low', description: 'Minor enhancements and edge cases' }
    ];
  }

  getIssueTypeLabels() {
    return {
      negative_rating: 'User gave thumbs down',
      fallback: 'Fallback response used',
      low_confidence: 'Low classification confidence',
      unhandled: 'Unhandled intent'
    };
  }

  getPriorityLabels() {
    return {
      1: 'High',
      2: 'Medium', 
      3: 'Low'
    };
  }

  getPriorityColor(priority: number) {
    switch (priority) {
      case 1: return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      case 2: return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200';
      case 3: return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
      default: return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
    }
  }

  getIssueTypeColor(issueType: string) {
    switch (issueType) {
      case 'negative_rating': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      case 'fallback': return 'bg-orange-100 dark:bg-orange-900/30 text-orange-800 dark:text-orange-200';
      case 'low_confidence': return 'bg-yellow-100 dark:bg-yellow-900/30 text-yellow-800 dark:text-yellow-200';
      case 'unhandled': return 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200';
      default: return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
    }
  }

  getSuggestionStatusColor(status: string) {
    switch (status) {
      case 'pending': return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
      case 'approved': return 'bg-green-100 dark:bg-green-900/30 text-green-800 dark:text-green-200';
      case 'rejected': return 'bg-red-100 dark:bg-red-900/30 text-red-800 dark:text-red-200';
      case 'implemented': return 'bg-purple-100 dark:bg-purple-900/30 text-purple-800 dark:text-purple-200';
      default: return 'bg-gray-100 dark:bg-gray-900/30 text-gray-800 dark:text-gray-200';
    }
  }

  // Debug methods for troubleshooting suggestion count issues
  async debugSuggestionCounts(): Promise<{
    total: number;
    by_status: Record<string, number>;
    by_type: Record<string, number>;
    by_priority: Record<string, number>;
    recent_suggestions: Array<{
      id: string;
      title: string;
      status: string;
      created_at: string;
    }>;
  }> {
    try {
      const allSuggestions = await this.getAllMySuggestions();
      
      const counts = {
        total: allSuggestions.length,
        by_status: {} as Record<string, number>,
        by_type: {} as Record<string, number>,
        by_priority: {} as Record<string, number>,
        recent_suggestions: allSuggestions.slice(0, 10).map(s => ({
          id: s.id,
          title: s.title,
          status: s.status,
          created_at: s.created_at
        }))
      };

      // Count by status
      allSuggestions.forEach(s => {
        counts.by_status[s.status] = (counts.by_status[s.status] || 0) + 1;
        counts.by_type[s.suggestion_type] = (counts.by_type[s.suggestion_type] || 0) + 1;
        counts.by_priority[s.priority] = (counts.by_priority[s.priority] || 0) + 1;
      });

      console.log('Debug suggestion counts:', counts);
      return counts;
    } catch (error) {
      console.error('Failed to debug suggestion counts:', error);
      throw error;
    }
  }
}

export const testerService = new TesterService();