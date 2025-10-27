// app/tester/queue/components/QueueFilters.tsx - Updated version
import Button from "@/components/ui/Button";
import { RefreshCw, X } from "lucide-react";

interface QueueFiltersProps {
  selectedPriority: string;
  selectedIssueType: string;
  selectedTimeframe: number;
  showSuggested?: boolean; // New prop
  onPriorityChange: (value: string) => void;
  onIssueTypeChange: (value: string) => void;
  onTimeframeChange: (value: number) => void;
  onShowSuggestedChange?: (show: boolean) => void; // New prop
  onClearFilters: () => void;
  onRefresh: () => void;
}

export function QueueFilters({
  selectedPriority,
  selectedIssueType,
  selectedTimeframe,
  showSuggested,
  onPriorityChange,
  onIssueTypeChange,
  onTimeframeChange,
  onShowSuggestedChange,
  onClearFilters,
  onRefresh
}: QueueFiltersProps) {
  return (
    <div className="bg-white dark:bg-neutral-800 rounded-lg border p-4 mb-6">
      <div className="flex flex-wrap items-center gap-4">
        {/* Priority Filter */}
        <div>
          <label className="block text-sm font-medium mb-1">Priority</label>
          <select
            value={selectedPriority}
            onChange={(e) => onPriorityChange(e.target.value)}
            className="input w-32"
          >
            <option value="">All</option>
            <option value="1">High</option>
            <option value="2">Medium</option>
            <option value="3">Low</option>
          </select>
        </div>

        {/* Issue Type Filter */}
        <div>
          <label className="block text-sm font-medium mb-1">Issue Type</label>
          <select
            value={selectedIssueType}
            onChange={(e) => onIssueTypeChange(e.target.value)}
            className="input w-40"
          >
            <option value="">All Types</option>
            <option value="negative_rating">Negative Rating</option>
            <option value="fallback">Fallback Used</option>
            <option value="low_confidence">Low Confidence</option>
            <option value="unhandled">Unhandled</option>
            <option value="error_intent">Error Intent</option>
            <option value="slow_response">Slow Response</option>
          </select>
        </div>

        {/* Timeframe Filter */}
        <div>
          <label className="block text-sm font-medium mb-1">Timeframe</label>
          <select
            value={selectedTimeframe}
            onChange={(e) => onTimeframeChange(parseInt(e.target.value))}
            className="input w-32"
          >
            <option value={1}>Today</option>
            <option value={3}>3 Days</option>
            <option value={7}>7 Days</option>
            <option value={14}>14 Days</option>
            <option value={30}>30 Days</option>
          </select>
        </div>

        {/* NEW: Show Suggested Toggle */}
        <div>
          <label className="block text-sm font-medium mb-1">Handled Messages</label>
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={showSuggested}
              onChange={(e) => onShowSuggestedChange?.(e.target.checked)}
              className="w-4 h-4 rounded"
            />
            <span className="text-sm">Include messages with suggestions</span>
          </label>
        </div>

        {/* Actions */}
        <div className="flex items-end gap-2 ml-auto">
          <Button 
            onClick={onRefresh}
            className="btn-secondary flex items-center gap-2"
          >
            <RefreshCw size={16} />
            Refresh
          </Button>
          
          <Button 
            onClick={onClearFilters}
            className="btn-secondary flex items-center gap-2"
          >
            <X size={16} />
            Clear Filters
          </Button>
        </div>
      </div>
    </div>
  );
}