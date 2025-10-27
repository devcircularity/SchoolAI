// services/testerRankings.ts
import { apiClient } from './api';

export interface TesterRanking {
  user_id: string;
  user_name: string;
  email: string;
  total_suggestions: number;
  approved_suggestions: number;
  implemented_suggestions: number;
  rejected_suggestions: number;
  pending_suggestions: number;
  approval_rate: number;
  implementation_rate: number;
  success_score: number;
  rank: number;
  last_suggestion_date?: string;
}

export interface TesterRankingsResponse {
  rankings: TesterRanking[];
  total_testers: number;
  period: string;
}

export interface TesterDetailedStats {
  user_id: string;
  user_name: string;
  email: string;
  total_suggestions: number;
  by_status: Record<string, number>;
  by_type: Record<string, number>;
  by_priority: Record<string, number>;
  recent_suggestions: Array<{
    id: string;
    title: string;
    status: string;
    type: string;
    created_at: string;
  }>;
  monthly_trend: Array<{
    month: string;
    total: number;
    approved: number;
    implemented: number;
  }>;
}

class TesterRankingsService {
  async getRankings(period: 'all_time' | 'last_30_days' | 'last_90_days' = 'all_time', limit: number = 20): Promise<TesterRankingsResponse> {
    const params = new URLSearchParams({ period, limit: limit.toString() });
    const response = await apiClient.get(`/api/admin/tester-rankings?${params.toString()}`);
    return response.data;
  }

  async getTesterDetailedStats(userId: string): Promise<TesterDetailedStats> {
    const response = await apiClient.get(`/api/admin/tester-rankings/${userId}/stats`);
    return response.data;
  }
}

export const testerRankingsService = new TesterRankingsService();