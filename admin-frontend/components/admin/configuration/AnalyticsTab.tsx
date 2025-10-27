// app/admin/configuration/components/AnalyticsTab.tsx
import Button from "@/components/ui/Button";

export default function AnalyticsTab() {
  return (
    <div className="space-y-6">
      <div className="card p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Configuration Analytics</h3>
        <p className="text-sm sm:text-base text-neutral-600 mb-3 sm:mb-4">
          View detailed routing logs and analytics in the Logs section.
        </p>
        <Button 
          onClick={() => window.location.href = '/admin/logs'}
          className="text-sm"
        >
          View Detailed Logs
        </Button>
      </div>
    </div>
  );
}