// services/chatMonitoring.ts
import { apiClient } from './api';

export interface ChatMessage {
  id: string;
  conversation_id: string;
  user_id: string;
  school_id?: string;
  content: string;
  message_type: 'user' | 'assistant';
  intent?: string;
  rating?: number;
  rated_at?: string;
  processing_time_ms?: number;
  created_at: string;
}

export interface ConversationSummary {
  conversation_id: string;
  user_id: string;
  school_id?: string;
  message_count: number;
  last_message_at: string;
  has_negative_rating: boolean;
  unresolved_issues: number;
}

export interface RealtimeStats {
  active_conversations: number;
  messages_today: number;
  average_response_time: number;
  satisfaction_rate: number;
  fallback_rate: number;
  top_intents_today: Array<{ intent: string; count: number }>;
}

class ChatMonitoringService {
  /**
   * Get recent chat messages across all conversations
   */
  async getRecentMessages(filters?: {
    limit?: number;
    school_id?: string;
    user_id?: string;
    has_rating?: boolean;
    message_type?: 'user' | 'assistant';
    hours_back?: number;
  }): Promise<ChatMessage[]> {
    const params = new URLSearchParams();
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.school_id) params.append('school_id', filters.school_id);
    if (filters?.user_id) params.append('user_id', filters.user_id);
    if (filters?.has_rating) params.append('has_rating', 'true');
    if (filters?.message_type) params.append('message_type', filters.message_type);
    if (filters?.hours_back) params.append('hours_back', filters.hours_back.toString());

    const response = await apiClient.get(`/api/admin/chat/messages?${params.toString()}`);
    return response.data;
  }

  /**
   * Get active conversations summary
   */
  async getActiveConversations(filters?: {
    school_id?: string;
    limit?: number;
    problems_only?: boolean;
  }): Promise<ConversationSummary[]> {
    const params = new URLSearchParams();
    if (filters?.school_id) params.append('school_id', filters.school_id);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.problems_only) params.append('problems_only', 'true');

    const response = await apiClient.get(`/api/admin/chat/conversations?${params.toString()}`);
    return response.data;
  }

  /**
   * Get real-time dashboard statistics
   */
  async getRealtimeStats(schoolId?: string): Promise<RealtimeStats> {
    const params = schoolId ? `?school_id=${schoolId}` : '';
    const response = await apiClient.get(`/api/admin/chat/stats/realtime${params}`);
    return response.data;
  }

  /**
   * Get conversation details with full message history
   */
  async getConversationDetails(conversationId: string): Promise<{
    conversation_id: string;
    messages: ChatMessage[];
    user_info: any;
    school_info: any;
    routing_logs: any[];
  }> {
    const response = await apiClient.get(`/api/admin/chat/conversations/${conversationId}`);
    return response.data;
  }

  /**
   * Flag a conversation for review
   */
  async flagConversation(conversationId: string, reason: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/chat/conversations/${conversationId}/flag`, {
      reason
    });
    return response.data;
  }

  /**
   * Get chat analytics for a time period
   */
  async getChatAnalytics(filters?: {
    start_date?: string;
    end_date?: string;
    school_id?: string;
    group_by?: 'hour' | 'day' | 'week';
  }): Promise<{
    message_volume: Array<{ date: string; count: number }>;
    intent_distribution: Array<{ intent: string; count: number; percentage: number }>;
    satisfaction_trends: Array<{ date: string; positive: number; negative: number; total: number }>;
    response_time_trends: Array<{ date: string; avg_time_ms: number }>;
    fallback_trends: Array<{ date: string; fallback_count: number; total_count: number }>;
  }> {
    const params = new URLSearchParams();
    if (filters?.start_date) params.append('start_date', filters.start_date);
    if (filters?.end_date) params.append('end_date', filters.end_date);
    if (filters?.school_id) params.append('school_id', filters.school_id);
    if (filters?.group_by) params.append('group_by', filters.group_by);

    const response = await apiClient.get(`/api/admin/chat/analytics?${params.toString()}`);
    return response.data;
  }
}

export const chatMonitoringService = new ChatMonitoringService();