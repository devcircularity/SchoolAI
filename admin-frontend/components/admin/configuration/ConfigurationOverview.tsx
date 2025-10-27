// app/admin/configuration/components/ConfigurationOverview.tsx
import { useState } from "react";
import { 
  Code, MessageSquare, Activity, Settings, Play, TestTube,
  CheckCircle, AlertCircle 
} from "lucide-react";
import { intentConfigService, IntentConfigVersion } from "@/services/intentConfig";
import Button from "@/components/ui/Button";

interface ConfigOverview {
  activeVersion: IntentConfigVersion | null;
  candidateVersion: IntentConfigVersion | null;
  totalPatterns: number;
  totalTemplates: number;
  enabledPatterns: number;
  enabledTemplates: number;
  systemHealth: 'healthy' | 'warning' | 'error';
  cacheStatus: 'loaded' | 'loading' | 'error';
}

interface ConfigurationOverviewProps {
  overview: ConfigOverview;
}

export default function ConfigurationOverview({ overview }: ConfigurationOverviewProps) {
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const handleTestClassify = async () => {
    if (!testMessage.trim()) return;
    
    try {
      setTesting(true);
      const result = await intentConfigService.testClassify({
        message: testMessage,
      });
      setTestResult(result);
    } catch (error) {
      console.error('Test failed:', error);
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      {/* Quick Stats - Responsive grid */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="card p-3 sm:p-4">
          <div className="flex items-center gap-2 mb-2">
            <Code size={14} className="text-blue-600 flex-shrink-0" />
            <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">Total Patterns</h3>
          </div>
          <p className="text-lg sm:text-2xl font-bold">{overview.totalPatterns}</p>
          <p className="text-xs text-neutral-500">{overview.enabledPatterns} enabled</p>
        </div>
        
        <div className="card p-3 sm:p-4">
          <div className="flex items-center gap-2 mb-2">
            <MessageSquare size={14} className="text-green-600 flex-shrink-0" />
            <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">Total Templates</h3>
          </div>
          <p className="text-lg sm:text-2xl font-bold">{overview.totalTemplates}</p>
          <p className="text-xs text-neutral-500">{overview.enabledTemplates} enabled</p>
        </div>
        
        <div className="card p-3 sm:p-4">
          <div className="flex items-center gap-2 mb-2">
            <Activity size={14} className="text-purple-600 flex-shrink-0" />
            <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">System Health</h3>
          </div>
          <div className="flex items-center gap-1 sm:gap-2">
            {overview.systemHealth === 'healthy' ? (
              <CheckCircle size={16} className="text-green-600 flex-shrink-0" />
            ) : (
              <AlertCircle size={16} className="text-orange-600 flex-shrink-0" />
            )}
            <span className="font-bold capitalize text-sm sm:text-base truncate">{overview.systemHealth}</span>
          </div>
        </div>
        
        <div className="card p-3 sm:p-4">
          <div className="flex items-center gap-2 mb-2">
            <Settings size={14} className="text-gray-600 flex-shrink-0" />
            <h3 className="text-xs sm:text-sm font-medium text-neutral-600 truncate">Cache Status</h3>
          </div>
          <p className="text-sm sm:text-lg font-bold capitalize truncate">{overview.cacheStatus}</p>
        </div>
      </div>

      {/* Version Information - Stack on mobile, side by side on desktop */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 sm:gap-6">
        <div className="card p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
            <Play size={16} className="text-green-600 flex-shrink-0" />
            <span className="truncate">Active Configuration</span>
          </h3>
          {overview.activeVersion ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <strong>Name:</strong> 
                <span className="truncate ml-2">{overview.activeVersion.name}</span>
              </div>
              <div className="flex justify-between">
                <strong>Patterns:</strong> 
                <span>{overview.activeVersion.pattern_count}</span>
              </div>
              <div className="flex justify-between">
                <strong>Templates:</strong> 
                <span>{overview.activeVersion.template_count}</span>
              </div>
              <div className="flex justify-between">
                <strong>Activated:</strong> 
                <span className="truncate ml-2">
                  {overview.activeVersion.activated_at ? new Date(overview.activeVersion.activated_at).toLocaleDateString() : 'N/A'}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-red-600 text-sm">No active configuration found!</p>
          )}
        </div>

        <div className="card p-4 sm:p-6">
          <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
            <Settings size={16} className="text-blue-600 flex-shrink-0" />
            <span className="truncate">Candidate Configuration</span>
          </h3>
          {overview.candidateVersion ? (
            <div className="space-y-2 text-sm">
              <div className="flex justify-between">
                <strong>Name:</strong> 
                <span className="truncate ml-2">{overview.candidateVersion.name}</span>
              </div>
              <div className="flex justify-between">
                <strong>Patterns:</strong> 
                <span>{overview.candidateVersion.pattern_count}</span>
              </div>
              <div className="flex justify-between">
                <strong>Templates:</strong> 
                <span>{overview.candidateVersion.template_count}</span>
              </div>
              <div className="flex justify-between">
                <strong>Created:</strong> 
                <span className="truncate ml-2">
                  {new Date(overview.candidateVersion.created_at).toLocaleDateString()}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-neutral-600 text-sm">No candidate configuration</p>
          )}
        </div>
      </div>

      {/* Quick Test - Mobile responsive */}
      <div className="card p-4 sm:p-6">
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4 flex items-center gap-2">
          <TestTube size={16} className="flex-shrink-0" />
          <span>Quick Classification Test</span>
        </h3>
        <div className="flex flex-col sm:flex-row gap-2 mb-4">
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter a message to test classification..."
            className="input flex-1 text-sm"
          />
          <Button 
            onClick={handleTestClassify}
            disabled={testing || !testMessage.trim()}
            className="flex items-center gap-2 whitespace-nowrap"
          >
            <TestTube size={16} />
            {testing ? 'Testing...' : 'Test'}
          </Button>
        </div>
        
        {testResult && (
          <div className="bg-neutral-50 dark:bg-neutral-800 p-3 sm:p-4 rounded-lg">
            <h4 className="font-semibold mb-2 text-sm sm:text-base">Result:</h4>
            <pre className="text-xs sm:text-sm overflow-auto">
              {JSON.stringify(testResult.final_decision, null, 2)}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
}