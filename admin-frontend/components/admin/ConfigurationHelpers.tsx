// components/admin/ConfigurationHelpers.tsx
import React, { useState } from 'react';
import { intentConfigService } from '@/services/intentConfig';
import Button from '@/components/ui/Button';
import { TestTube, Download, AlertTriangle, CheckCircle, XCircle } from 'lucide-react';

interface PatternTesterProps {
  patternId: string;
  pattern: string;
}

export function PatternTester({ patternId, pattern }: PatternTesterProps) {
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    if (!testMessage.trim()) return;
    
    try {
      setTesting(true);
      const result = await intentConfigService.testPattern(patternId, testMessage);
      setTestResult(result);
    } catch (error) {
      console.error('Pattern test failed:', error);
      setTestResult({
        matches: false,
        error: 'Test failed: ' + (error as Error).message
      });
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-3">
      <div>
        <label className="block text-sm font-medium mb-1">Test Message</label>
        <div className="flex gap-2">
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter message to test against pattern..."
            className="input flex-1"
            onKeyPress={(e) => e.key === 'Enter' && handleTest()}
          />
          <Button 
            onClick={handleTest}
            disabled={testing || !testMessage.trim()}
            className="btn-sm"
          >
            <TestTube size={14} />
            {testing ? 'Testing...' : 'Test'}
          </Button>
        </div>
      </div>
      
      <div className="text-xs bg-gray-100 dark:bg-gray-800 p-2 rounded font-mono">
        Pattern: {pattern}
      </div>
      
      {testResult && (
        <div className="space-y-2">
          <div className={`flex items-center gap-2 text-sm ${
            testResult.matches ? 'text-green-700' : 'text-red-700'
          }`}>
            {testResult.matches ? <CheckCircle size={16} /> : <XCircle size={16} />}
            <span>{testResult.matches ? 'Pattern matches!' : 'No match'}</span>
          </div>
          
          {testResult.matches && (
            <div className="text-sm space-y-1">
              <div><strong>Matched text:</strong> "{testResult.match_text}"</div>
              <div><strong>Position:</strong> {testResult.match_start} - {testResult.match_end}</div>
              {testResult.groups && testResult.groups.length > 0 && (
                <div><strong>Groups:</strong> {testResult.groups.join(', ')}</div>
              )}
              {testResult.named_groups && Object.keys(testResult.named_groups).length > 0 && (
                <div><strong>Named groups:</strong> {JSON.stringify(testResult.named_groups)}</div>
              )}
            </div>
          )}
          
          {testResult.error && (
            <div className="text-red-600 text-sm">
              Error: {testResult.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

interface SystemHealthIndicatorProps {
  health: 'healthy' | 'warning' | 'error' | 'critical';
  issues?: Array<{
    severity: string;
    component: string;
    message: string;
  }>;
}

export function SystemHealthIndicator({ health, issues = [] }: SystemHealthIndicatorProps) {
  const [showDetails, setShowDetails] = useState(false);

  const getHealthColor = (health: string) => {
    switch (health) {
      case 'healthy': return 'text-green-600';
      case 'warning': return 'text-yellow-600';
      case 'error': return 'text-orange-600';
      case 'critical': return 'text-red-600';
      default: return 'text-gray-600';
    }
  };

  const getHealthIcon = (health: string) => {
    switch (health) {
      case 'healthy': return <CheckCircle size={20} />;
      case 'warning': case 'error': case 'critical': return <AlertTriangle size={20} />;
      default: return <XCircle size={20} />;
    }
  };

  return (
    <div className="space-y-2">
      <div 
        className={`flex items-center gap-2 cursor-pointer ${getHealthColor(health)}`}
        onClick={() => setShowDetails(!showDetails)}
      >
        {getHealthIcon(health)}
        <span className="font-medium capitalize">{health}</span>
        {issues.length > 0 && (
          <span className="text-sm text-neutral-500">
            ({issues.length} issue{issues.length !== 1 ? 's' : ''})
          </span>
        )}
      </div>
      
      {showDetails && issues.length > 0 && (
        <div className="ml-6 space-y-1">
          {issues.map((issue, index) => (
            <div key={index} className="text-sm">
              <span className={`inline-block w-16 text-xs uppercase font-medium ${
                issue.severity === 'critical' ? 'text-red-600' :
                issue.severity === 'error' ? 'text-orange-600' :
                issue.severity === 'warning' ? 'text-yellow-600' :
                'text-blue-600'
              }`}>
                {issue.severity}
              </span>
              <span className="text-neutral-600">[{issue.component}]</span>
              <span className="ml-2">{issue.message}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

interface ExportConfigurationProps {
  versionId: string;
  versionName: string;
}

export function ExportConfiguration({ versionId, versionName }: ExportConfigurationProps) {
  const [exporting, setExporting] = useState(false);

  const handleExport = async (format: 'json' | 'yaml') => {
    try {
      setExporting(true);
      const blob = await intentConfigService.exportConfiguration(versionId, format);
      
      // Create download link
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `config_${versionName.replace(/\s+/g, '_')}_${versionId.slice(0, 8)}.${format}`;
      document.body.appendChild(a);
      a.click();
      window.URL.revokeObjectURL(url);
      document.body.removeChild(a);
    } catch (error) {
      console.error('Export failed:', error);
      alert('Export failed: ' + (error as Error).message);
    } finally {
      setExporting(false);
    }
  };

  return (
    <div className="flex gap-2">
      <Button
        onClick={() => handleExport('json')}
        disabled={exporting}
        className="btn-secondary btn-sm flex items-center gap-2"
      >
        <Download size={14} />
        Export JSON
      </Button>
      <Button
        onClick={() => handleExport('yaml')}
        disabled={exporting}
        className="btn-secondary btn-sm flex items-center gap-2"
      >
        <Download size={14} />
        Export YAML
      </Button>
    </div>
  );
}

interface ConfigValidatorProps {
  versionId: string;
  versionName: string;
}

export function ConfigValidator({ versionId, versionName }: ConfigValidatorProps) {
  const [validating, setValidating] = useState(false);
  const [validationResult, setValidationResult] = useState<any>(null);

  const handleValidate = async () => {
    try {
      setValidating(true);
      const result = await intentConfigService.validateConfiguration(versionId);
      setValidationResult(result);
    } catch (error) {
      console.error('Validation failed:', error);
      setValidationResult({
        overall_valid: false,
        error: (error as Error).message
      });
    } finally {
      setValidating(false);
    }
  };

  return (
    <div className="space-y-3">
      <Button
        onClick={handleValidate}
        disabled={validating}
        className="btn-secondary flex items-center gap-2"
      >
        <CheckCircle size={16} />
        {validating ? 'Validating...' : 'Validate Configuration'}
      </Button>
      
      {validationResult && (
        <div className="space-y-3">
          <div className={`flex items-center gap-2 ${
            validationResult.overall_valid ? 'text-green-600' : 'text-red-600'
          }`}>
            {validationResult.overall_valid ? <CheckCircle size={16} /> : <XCircle size={16} />}
            <span className="font-medium">
              {validationResult.overall_valid ? 'Configuration is valid' : 'Configuration has errors'}
            </span>
          </div>
          
          {validationResult.patterns && (
            <div className="text-sm">
              <div className="font-medium mb-1">Patterns:</div>
              <div className="ml-4 space-y-1">
                <div>Total: {validationResult.patterns.total}</div>
                <div className="text-green-600">Valid: {validationResult.patterns.valid}</div>
                {validationResult.patterns.invalid > 0 && (
                  <div className="text-red-600">Invalid: {validationResult.patterns.invalid}</div>
                )}
              </div>
              
              {validationResult.patterns.errors?.length > 0 && (
                <div className="mt-2">
                  <div className="font-medium text-red-600 mb-1">Pattern Errors:</div>
                  <div className="ml-4 space-y-1">
                    {validationResult.patterns.errors.map((error: any, index: number) => (
                      <div key={index} className="text-xs">
                        <div className="font-medium">{error.intent}</div>
                        <div className="text-red-600">{error.error}</div>
                        <div className="font-mono bg-gray-100 dark:bg-gray-800 p-1 rounded">
                          {error.pattern}
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
          )}
          
          {validationResult.error && (
            <div className="text-red-600 text-sm">
              Error: {validationResult.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}