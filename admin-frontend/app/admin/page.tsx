// app/admin/page.tsx - Reorganized admin dashboard with improved structure
"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/contexts/AuthContext";
import { RouteProtection } from "@/components/auth/RouteProtection";
import { HeaderTitleBus } from "@/components/layout/HeaderBar";
import { chatMonitoringService, RealtimeStats } from "@/services/chatMonitoring";
import { userService, UserStats } from "@/services/user";
import { suggestionsService, SuggestionStats } from "@/services/suggestions";
import { MessageSquare, Users, Clock, TrendingUp, AlertTriangle, Activity, UserCheck, UserPlus, CheckCircle, RefreshCw, School, EyeOff, Eye, Settings } from "lucide-react";
import { TesterRankings } from "@/components/admin/dashboard/TesterRankings";
import { schoolService, SchoolStats } from "@/services/school";
import { apiClient } from "@/services/api";

interface ImplementationStats {
  total_approved: number;
  pending_implementation: number;
  in_progress: number;
  completed_this_week: number;
  overdue_items: number;
}

export default function AdminDashboardPage() {
  return (
    <RouteProtection 
      requiredPermissions={["is_admin", "is_super_admin"]} 
      requiredRoles={["ADMIN", "SUPER_ADMIN"]}
      fallbackRoute="/dashboard"
    >
      <AdminDashboard />
    </RouteProtection>
  );
}

function AdminDashboard() {
  const { user } = useAuth();
  
  // State
  const [realtimeStats, setRealtimeStats] = useState<RealtimeStats | null>(null);
  const [userStats, setUserStats] = useState<UserStats | null>(null);
  const [implementationStats, setImplementationStats] = useState<ImplementationStats | null>(null);
  const [schoolStats, setSchoolStats] = useState<SchoolStats | null>(null);
  const [suggestionStats, setSuggestionStats] = useState<SuggestionStats | null>(null);
  const [hideQueueFromTesters, setHideQueueFromTesters] = useState<boolean>(false);
  
  // Loading states
  const [loadingChatStats, setLoadingChatStats] = useState(true);
  const [loadingUserStats, setLoadingUserStats] = useState(true);
  const [loadingImplementationStats, setLoadingImplementationStats] = useState(true);
  const [loadingSchoolStats, setLoadingSchoolStats] = useState(true);
  const [loadingSuggestionStats, setLoadingSuggestionStats] = useState(true);
  const [loadingQueueSetting, setLoadingQueueSetting] = useState(false);
  
  // Filters
  const [chatStatsTimeRange, setChatStatsTimeRange] = useState<string>('168'); // 7 days default
  
  // Set page title in header
  useEffect(() => {
    HeaderTitleBus.send({ 
      type: 'set', 
      title: 'Admin Dashboard',
      subtitle: 'System overview and management' 
    });
    
    return () => HeaderTitleBus.send({ type: 'clear' });
  }, []);

  useEffect(() => {
    loadAllStats();
    loadQueueVisibilitySetting();
  }, []);

  useEffect(() => {
    loadChatStats();
  }, [chatStatsTimeRange]);

  const loadAllStats = () => {
    loadChatStats();
    loadUserStats();
    loadImplementationStats();
    loadSchoolStats();
    loadSuggestionStats();
  };

  const loadQueueVisibilitySetting = async () => {
    try {
      const response = await apiClient.get('/api/admin/configuration/settings/hide-tester-queue');
      setHideQueueFromTesters(response.data.hidden);
    } catch (error) {
      console.error('Failed to load queue visibility setting:', error);
    }
  };

  const toggleQueueVisibility = async () => {
    try {
      setLoadingQueueSetting(true);
      const newValue = !hideQueueFromTesters;
      await apiClient.post('/api/admin/configuration/settings/hide-tester-queue', { 
        hidden: newValue 
      });
      setHideQueueFromTesters(newValue);
    } catch (error) {
      console.error('Failed to update queue visibility:', error);
      alert('Failed to update queue visibility setting');
    } finally {
      setLoadingQueueSetting(false);
    }
  };

  const loadChatStats = async () => {
    try {
      setLoadingChatStats(true);
      const stats = await chatMonitoringService.getRealtimeStats(chatStatsTimeRange);
      setRealtimeStats(stats);
    } catch (error) {
      console.error('Failed to load chat stats:', error);
    } finally {
      setLoadingChatStats(false);
    }
  };

  const loadUserStats = async () => {
    try {
      setLoadingUserStats(true);
      const stats = await userService.getUserStats();
      setUserStats(stats);
    } catch (error) {
      console.error('Failed to load user stats:', error);
    } finally {
      setLoadingUserStats(false);
    }
  };

  const loadImplementationStats = async () => {
    try {
      setLoadingImplementationStats(true);
      const suggestionsResponse = await suggestionsService.getSuggestions({
        status: 'approved',
        limit: 100
      });
      
      const approvedSuggestions = suggestionsResponse.suggestions;
      setImplementationStats({
        total_approved: approvedSuggestions.length,
        pending_implementation: approvedSuggestions.filter(s => 
          !s.action_items || s.action_items.length === 0
        ).length,
        in_progress: approvedSuggestions.filter(s => 
          s.action_items && s.action_items.some(item => item.status === 'in_progress')
        ).length,
        completed_this_week: 0,
        overdue_items: 0
      });
    } catch (error) {
      console.error('Failed to load implementation stats:', error);
    } finally {
      setLoadingImplementationStats(false);
    }
  };

  const loadSchoolStats = async () => {
    try {
      setLoadingSchoolStats(true);
      const stats = await schoolService.getSchoolStats();
      setSchoolStats(stats);
    } catch (error) {
      console.error('Failed to load school stats:', error);
    } finally {
      setLoadingSchoolStats(false);
    }
  };

  const loadSuggestionStats = async () => {
    try {
      setLoadingSuggestionStats(true);
      const stats = await suggestionsService.getSuggestionStats();
      setSuggestionStats(stats);
    } catch (error) {
      console.error('Failed to load suggestion stats:', error);
    } finally {
      setLoadingSuggestionStats(false);
    }
  };

  const getTimeRangeLabel = (hours: string) => {
    const hoursNum = parseInt(hours);
    if (hoursNum === 24) return 'Last 24h';
    if (hoursNum === 168) return 'Last 7 days';
    if (hoursNum === 336) return 'Last 14 days';
    if (hoursNum === 720) return 'Last 30 days';
    return `Last ${hoursNum}h`;
  };

  return (
    <div className="h-full overflow-y-auto">
      <div className="p-3 sm:p-6 max-w-[1600px] mx-auto">
        
        {/* Header Actions */}
        <div className="flex justify-end mb-6">
          <button
            onClick={loadAllStats}
            className="btn btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh All
          </button>
        </div>

        {/* Key Metrics Overview */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Key Metrics
          </h2>
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
            <div className="card p-4 border-l-4 border-blue-500">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-neutral-600">Total Schools</h3>
                <School size={20} className="text-blue-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                {loadingSchoolStats ? '--' : schoolStats?.total_schools || 0}
              </p>
            </div>

            <div className="card p-4 border-l-4 border-orange-500">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-neutral-600">Pending Suggestions</h3>
                <AlertTriangle size={20} className="text-orange-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                {loadingSuggestionStats ? '--' : suggestionStats?.pending || 0}
              </p>
              <button 
                onClick={() => window.location.href = '/admin/suggestions?status=pending'}
                className="text-xs text-orange-600 hover:underline mt-2"
              >
                Review now →
              </button>
            </div>

            <div className="card p-4 border-l-4 border-amber-500">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-neutral-600">Need Action Items</h3>
                <CheckCircle size={20} className="text-amber-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                {loadingImplementationStats ? '--' : implementationStats?.pending_implementation || 0}
              </p>
              <button 
                onClick={() => window.location.href = '/admin/suggestions?status=approved'}
                className="text-xs text-amber-600 hover:underline mt-2"
              >
                Create items →
              </button>
            </div>

            <div className="card p-4 border-l-4 border-green-500">
              <div className="flex items-center justify-between mb-2">
                <h3 className="text-sm font-medium text-neutral-600">Active Users</h3>
                <UserCheck size={20} className="text-green-600" />
              </div>
              <p className="text-3xl font-bold text-neutral-900 dark:text-neutral-100">
                {loadingUserStats ? '--' : userStats?.active_users || 0}
              </p>
              <p className="text-xs text-neutral-500 mt-1">
                of {userStats?.total_users || 0} total
              </p>
            </div>
          </div>
        </section>

        {/* Chat System Performance */}
        <section className="mb-8">
          <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center mb-4 gap-3">
            <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100">
              Chat System Performance
            </h2>
            <div className="flex gap-2 items-center">
              <select
                value={chatStatsTimeRange}
                onChange={(e) => setChatStatsTimeRange(e.target.value)}
                className="input text-sm"
              >
                <option value="24">Last 24 hours</option>
                <option value="168">Last 7 days</option>
                <option value="336">Last 14 days</option>
                <option value="720">Last 30 days</option>
              </select>
              <button 
                onClick={() => window.location.href = '/admin/monitoring'}
                className="btn btn-secondary text-sm"
              >
                View Details
              </button>
            </div>
          </div>
          
          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3">
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Users size={16} className="text-blue-600" />
                <h3 className="text-xs font-medium text-neutral-600">Active Now</h3>
              </div>
              <p className="text-2xl font-bold">
                {loadingChatStats ? '--' : realtimeStats?.active_conversations || 0}
              </p>
            </div>
            
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <MessageSquare size={16} className="text-green-600" />
                <h3 className="text-xs font-medium text-neutral-600">{getTimeRangeLabel(chatStatsTimeRange)}</h3>
              </div>
              <p className="text-2xl font-bold">
                {loadingChatStats ? '--' : realtimeStats?.messages_today || 0}
              </p>
            </div>
            
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Clock size={16} className="text-purple-600" />
                <h3 className="text-xs font-medium text-neutral-600">Avg Response</h3>
              </div>
              <p className="text-2xl font-bold">
                {loadingChatStats ? '--' : `${realtimeStats?.average_response_time || 0}ms`}
              </p>
            </div>
            
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <TrendingUp size={16} className="text-green-600" />
                <h3 className="text-xs font-medium text-neutral-600">Satisfaction</h3>
              </div>
              <p className="text-2xl font-bold">
                {loadingChatStats ? '--' : `${((realtimeStats?.satisfaction_rate || 0) * 100).toFixed(1)}%`}
              </p>
            </div>
            
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <AlertTriangle size={16} className="text-orange-600" />
                <h3 className="text-xs font-medium text-neutral-600">Fallback Rate</h3>
              </div>
              <p className="text-2xl font-bold">
                {loadingChatStats ? '--' : `${((realtimeStats?.fallback_rate || 0) * 100).toFixed(1)}%`}
              </p>
            </div>
            
            <div className="card p-4">
              <div className="flex items-center gap-2 mb-2">
                <Activity size={16} className="text-blue-600" />
                <h3 className="text-xs font-medium text-neutral-600">Top Intent</h3>
              </div>
              <p className="text-lg font-bold truncate">
                {loadingChatStats ? '--' : realtimeStats?.top_intents_today[0]?.intent || 'N/A'}
              </p>
              <p className="text-xs text-neutral-500">
                {loadingChatStats ? '' : `${realtimeStats?.top_intents_today[0]?.count || 0} uses`}
              </p>
            </div>
          </div>
        </section>

        {/* Management Sections */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Management Overview
          </h2>
          <div className="grid lg:grid-cols-2 gap-6">
            
            {/* Implementation Management */}
            <div className="card p-5">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  Implementation Queue
                </h3>
                <button 
                  onClick={() => window.location.href = '/admin/configuration?tab=implementation'}
                  className="btn btn-secondary text-xs"
                >
                  Manage →
                </button>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <CheckCircle size={16} className="text-blue-600" />
                    <span className="text-sm font-medium">Total Approved</span>
                  </div>
                  <span className="text-lg font-bold">
                    {loadingImplementationStats ? '--' : implementationStats?.total_approved || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-amber-50 dark:bg-amber-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <AlertTriangle size={16} className="text-amber-600" />
                    <span className="text-sm font-medium">Need Action Items</span>
                  </div>
                  <span className="text-lg font-bold text-amber-600">
                    {loadingImplementationStats ? '--' : implementationStats?.pending_implementation || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Activity size={16} className="text-blue-600" />
                    <span className="text-sm font-medium">In Progress</span>
                  </div>
                  <span className="text-lg font-bold">
                    {loadingImplementationStats ? '--' : implementationStats?.in_progress || 0}
                  </span>
                </div>
              </div>
            </div>

            {/* User Overview */}
            <div className="card p-5">
              <div className="flex justify-between items-center mb-4">
                <h3 className="text-lg font-semibold text-neutral-900 dark:text-neutral-100">
                  User Overview
                </h3>
                <button 
                  onClick={() => window.location.href = '/admin/users'}
                  className="btn btn-secondary text-xs"
                >
                  Manage →
                </button>
              </div>
              
              <div className="space-y-3">
                <div className="flex justify-between items-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <Users size={16} className="text-blue-600" />
                    <span className="text-sm font-medium">Total Users</span>
                  </div>
                  <span className="text-lg font-bold">
                    {loadingUserStats ? '--' : userStats?.total_users || 0}
                  </span>
                </div>
                
                <div className="flex justify-between items-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
                  <div className="flex items-center gap-2">
                    <UserCheck size={16} className="text-green-600" />
                    <span className="text-sm font-medium">Active Users</span>
                  </div>
                  <span className="text-lg font-bold text-green-600">
                    {loadingUserStats ? '--' : userStats?.active_users || 0}
                  </span>
                </div>
                
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <UserPlus size={14} className="text-blue-600" />
                      <span className="text-xs font-medium">This Week</span>
                    </div>
                    <span className="text-lg font-bold">
                      {loadingUserStats ? '--' : userStats?.new_users_this_week || 0}
                    </span>
                  </div>
                  
                  <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                    <div className="flex items-center gap-2 mb-1">
                      <UserPlus size={14} className="text-purple-600" />
                      <span className="text-xs font-medium">This Month</span>
                    </div>
                    <span className="text-lg font-bold">
                      {loadingUserStats ? '--' : userStats?.new_users_this_month || 0}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </section>

        {/* System Configuration */}
        <section className="mb-8">
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            System Configuration
          </h2>
          <div className="card p-5">
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-2">
                  <Settings size={20} className="text-neutral-600" />
                  <h3 className="text-base font-semibold text-neutral-900 dark:text-neutral-100">
                    Tester Queue Visibility
                  </h3>
                </div>
                <p className="text-sm text-neutral-600 dark:text-neutral-400">
                  Control whether testers can view the problem queue on their dashboard
                </p>
              </div>
              
              <div className="flex items-center gap-4">
                <div className={`flex items-center gap-2 px-3 py-1.5 rounded-lg text-sm font-medium ${
                  hideQueueFromTesters 
                    ? 'bg-orange-50 dark:bg-orange-900/20 text-orange-700 dark:text-orange-400' 
                    : 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-400'
                }`}>
                  {hideQueueFromTesters ? (
                    <>
                      <EyeOff size={16} />
                      <span>Hidden</span>
                    </>
                  ) : (
                    <>
                      <Eye size={16} />
                      <span>Visible</span>
                    </>
                  )}
                </div>
                
                <label className="relative inline-flex items-center cursor-pointer">
                  <input
                    type="checkbox"
                    checked={hideQueueFromTesters}
                    onChange={toggleQueueVisibility}
                    disabled={loadingQueueSetting}
                    className="sr-only peer"
                  />
                  <div className="w-11 h-6 bg-neutral-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-neutral-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-neutral-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-neutral-600 peer-checked:bg-orange-600"></div>
                </label>
              </div>
            </div>
          </div>
        </section>

        {/* Tester Rankings */}
        <section>
          <h2 className="text-xl font-semibold text-neutral-900 dark:text-neutral-100 mb-4">
            Tester Performance
          </h2>
          <TesterRankings period="last_30_days" limit={10} />
        </section>

      </div>
    </div>
  );
}