// components/admin/suggestions/SuggestionsStatsCards.tsx
import { SuggestionStats } from "@/services/suggestions";

interface SuggestionsStatsCardsProps {
  stats: SuggestionStats | null;
  loading?: boolean;
}

export function SuggestionsStatsCards({ stats, loading }: SuggestionsStatsCardsProps) {
  if (!stats) return null;

  return (
    <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 sm:gap-4 mb-4 sm:mb-6">
      <div className="card p-3 sm:p-4">
        <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Total</h3>
        <p className="text-lg sm:text-2xl font-bold">
          {loading ? '--' : stats.total_suggestions}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Pending</h3>
        <p className="text-lg sm:text-2xl font-bold text-orange-600">
          {loading ? '--' : stats.pending}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Approved</h3>
        <p className="text-lg sm:text-2xl font-bold text-green-600">
          {loading ? '--' : stats.approved}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">Need Analysis</h3>
        <p className="text-lg sm:text-2xl font-bold text-yellow-600">
          {loading ? '--' : (stats.needs_analysis || 0)}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Rejected</h3>
        <p className="text-lg sm:text-2xl font-bold text-red-600">
          {loading ? '--' : stats.rejected}
        </p>
      </div>
      
      <div className="card p-3 sm:p-4">
        <h3 className="text-xs sm:text-sm font-medium text-neutral-600">Addressed</h3>
        <p className="text-lg sm:text-2xl font-bold text-purple-600">
          {loading ? '--' : stats.implemented}
        </p>
      </div>
    </div>
  );
}