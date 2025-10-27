// app/admin/configuration/components/ConfigurationTabs.tsx - Updated with Test Tab
import { useState, useEffect } from "react";
import { intentConfigService, IntentPattern, PromptTemplate, IntentConfigVersion } from "@/services/intentConfig";
import { TestTube } from "lucide-react";
import ConfigurationOverview from "./ConfigurationOverview";
import PatternsTab from "./PatternsTab";
import TemplatesTab from "./TemplatesTab";
import AnalyticsTab from "./AnalyticsTab";
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

// Enhanced Pattern interface with phrase support
interface EnhancedIntentPattern extends IntentPattern {
  phrases?: string[];
  regex_confidence?: number;
  regex_explanation?: string;
}

interface EditingItem {
  type: 'pattern' | 'template';
  item: EnhancedIntentPattern | PromptTemplate;
  isNew?: boolean;
}

interface ConfigurationTabsProps {
  activeTab: 'overview' | 'patterns' | 'templates' | 'analytics' | 'test';
  overview: ConfigOverview | null;
  onOverviewRefresh: () => void;
}

export default function ConfigurationTabs({ 
  activeTab, 
  overview, 
  onOverviewRefresh 
}: ConfigurationTabsProps) {
  const [patterns, setPatterns] = useState<EnhancedIntentPattern[]>([]);
  const [templates, setTemplates] = useState<PromptTemplate[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedVersion, setSelectedVersion] = useState<string>('');
  const [availableHandlers, setAvailableHandlers] = useState<string[]>([]);
  const [availableIntents, setAvailableIntents] = useState<string[]>([]);
  const [editingItem, setEditingItem] = useState<EditingItem | null>(null);

  useEffect(() => {
    if (overview?.activeVersion) {
      setSelectedVersion(overview.activeVersion.id);
    }
  }, [overview]);

  useEffect(() => {
    loadAvailableOptions();
  }, []);

  useEffect(() => {
    if (selectedVersion && (activeTab === 'patterns' || activeTab === 'templates')) {
      loadCurrentData();
    }
  }, [selectedVersion, activeTab]);

  const loadAvailableOptions = async () => {
    try {
      const [handlersRes, intentsRes] = await Promise.all([
        intentConfigService.getAvailableHandlers(),
        intentConfigService.getAvailableIntents()
      ]);
      setAvailableHandlers(handlersRes.handlers);
      setAvailableIntents(intentsRes.intents);
    } catch (error) {
      console.error('Failed to load available options:', error);
    }
  };

  const loadCurrentData = async () => {
    if (!selectedVersion) return;

    try {
      setLoading(true);
      
      if (activeTab === 'patterns') {
        const data = await intentConfigService.getPatterns(selectedVersion);
        setPatterns(data);
      } else if (activeTab === 'templates') {
        const data = await intentConfigService.getTemplates(selectedVersion);
        setTemplates(data);
      }
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveItem = async () => {
    if (!editingItem) return;

    try {
      if (editingItem.type === 'pattern') {
        const pattern = editingItem.item as EnhancedIntentPattern;
        if (editingItem.isNew) {
          await intentConfigService.createPattern(selectedVersion, {
            handler: pattern.handler,
            intent: pattern.intent,
            kind: pattern.kind,
            pattern: pattern.pattern,
            priority: pattern.priority,
            enabled: pattern.enabled,
            scope_school_id: pattern.scope_school_id,
            ...(pattern.phrases && { phrases: pattern.phrases })
          });
        } else {
          await intentConfigService.updatePattern(pattern.id, {
            handler: pattern.handler,
            intent: pattern.intent,
            kind: pattern.kind,
            pattern: pattern.pattern,
            priority: pattern.priority,
            enabled: pattern.enabled,
            scope_school_id: pattern.scope_school_id,
            ...(pattern.phrases && { phrases: pattern.phrases })
          });
        }
      } else {
        const template = editingItem.item as PromptTemplate;
        if (editingItem.isNew) {
          await intentConfigService.createTemplate(selectedVersion, {
            handler: template.handler,
            intent: template.intent,
            template_type: template.template_type,
            template_text: template.template_text,
            enabled: template.enabled
          });
        } else {
          await intentConfigService.updateTemplate(template.id, {
            handler: template.handler,
            intent: template.intent,
            template_type: template.template_type,
            template_text: template.template_text,
            enabled: template.enabled
          });
        }
      }

      setEditingItem(null);
      loadCurrentData();
      onOverviewRefresh();
    } catch (error) {
      console.error('Failed to save item:', error);
      alert('Failed to save changes');
    }
  };

  if (activeTab === 'overview' && overview) {
    return <ConfigurationOverview overview={overview} />;
  }

  if (activeTab === 'patterns') {
    return (
      <PatternsTab
        patterns={patterns}
        loading={loading}
        selectedVersion={selectedVersion}
        setSelectedVersion={setSelectedVersion}
        overview={overview}
        availableHandlers={availableHandlers}
        availableIntents={availableIntents}
        editingItem={editingItem}
        setEditingItem={setEditingItem}
        onSaveItem={handleSaveItem}
        onDataChange={loadCurrentData}
      />
    );
  }

  if (activeTab === 'templates') {
    return (
      <TemplatesTab
        templates={templates}
        loading={loading}
        selectedVersion={selectedVersion}
        setSelectedVersion={setSelectedVersion}
        overview={overview}
        availableHandlers={availableHandlers}
        availableIntents={availableIntents}
        editingItem={editingItem}
        setEditingItem={setEditingItem}
        onSaveItem={handleSaveItem}
        onDataChange={loadCurrentData}
      />
    );
  }

  if (activeTab === 'analytics') {
    return <AnalyticsTab />;
  }

  if (activeTab === 'test') {
    return <TestClassificationTab />;
  }

  return null;
}

// Test Classification Component
function TestClassificationTab() {
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);

  const handleTest = async () => {
    if (!testMessage.trim()) return;
    
    try {
      setTesting(true);
      const result = await intentConfigService.testClassify({
        message: testMessage,
      });
      setTestResult(result);
    } catch (error) {
      console.error('Test failed:', error);
      alert('Classification test failed. Please try again.');
    } finally {
      setTesting(false);
    }
  };

  return (
    <div className="space-y-4 sm:space-y-6">
      <div>
        <h3 className="text-base sm:text-lg font-semibold mb-3 sm:mb-4">Test Intent Classification</h3>
        <p className="text-sm sm:text-base text-neutral-600 mb-4">
          Test how messages are classified by the current active configuration. This helps validate your patterns and templates.
        </p>
      </div>

      <div className="card p-4 sm:p-6">
        <div className="space-y-4">
          <div>
            <label className="label text-sm">Test Message</label>
            <div className="flex flex-col sm:flex-row gap-2">
              <input
                type="text"
                value={testMessage}
                onChange={(e) => setTestMessage(e.target.value)}
                placeholder="Enter a message to test classification... (e.g., 'show me student details')"
                className="input flex-1 text-sm"
                onKeyPress={(e) => e.key === 'Enter' && handleTest()}
              />
              <Button 
                onClick={handleTest}
                disabled={testing || !testMessage.trim()}
                className="flex items-center gap-2 text-sm whitespace-nowrap"
              >
                <TestTube size={16} />
                {testing ? 'Testing...' : 'Test Classification'}
              </Button>
            </div>
            <p className="text-xs text-neutral-500 mt-1">
              Press Enter to test or click the button
            </p>
          </div>

          {testResult && (
            <div className="space-y-4">
              <h4 className="font-semibold mb-3 text-sm sm:text-base">Classification Results</h4>
              
              {/* Final Decision */}
              <div className="bg-green-50 dark:bg-green-900/20 p-3 sm:p-4 rounded-lg">
                <h5 className="font-medium text-green-800 dark:text-green-200 mb-2 text-sm">Final Decision:</h5>
                <pre className="text-xs sm:text-sm bg-white dark:bg-neutral-800 p-2 sm:p-3 rounded overflow-auto border">
                  {JSON.stringify(testResult.final_decision, null, 2)}
                </pre>
              </div>
              
              {/* Config Router Result */}
              {testResult.config_router_result && (
                <div className="bg-blue-50 dark:bg-blue-900/20 p-3 sm:p-4 rounded-lg">
                  <h5 className="font-medium text-blue-800 dark:text-blue-200 mb-2 text-sm">Config Router Result:</h5>
                  <pre className="text-xs sm:text-sm bg-white dark:bg-neutral-800 p-2 sm:p-3 rounded overflow-auto border">
                    {JSON.stringify(testResult.config_router_result, null, 2)}
                  </pre>
                </div>
              )}
              
              {/* LLM Classifier Result */}
              {testResult.llm_classifier_result && (
                <div className="bg-purple-50 dark:bg-purple-900/20 p-3 sm:p-4 rounded-lg">
                  <h5 className="font-medium text-purple-800 dark:text-purple-200 mb-2 text-sm">LLM Classifier Result:</h5>
                  <pre className="text-xs sm:text-sm bg-white dark:bg-neutral-800 p-2 sm:p-3 rounded overflow-auto border">
                    {JSON.stringify(testResult.llm_classifier_result, null, 2)}
                  </pre>
                </div>
              )}
              
              {/* Processing Steps */}
              <div className="bg-neutral-50 dark:bg-neutral-800 p-3 sm:p-4 rounded-lg">
                <h5 className="font-medium mb-2 text-sm">Processing Steps:</h5>
                <ol className="space-y-1">
                  {testResult.processing_steps?.map((step: string, index: number) => (
                    <li key={index} className="text-xs sm:text-sm text-neutral-600 dark:text-neutral-300">
                      <span className="font-medium">{index + 1}.</span> {step}
                    </li>
                  ))}
                </ol>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Example Test Cases */}
      <div className="card p-4 sm:p-6">
        <h4 className="font-semibold mb-3 text-sm sm:text-base">Example Test Cases</h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 sm:gap-3">
          {[
            "Show me student details",
            "What are the admission requirements?",
            "I want to pay school fees",
            "How do I register my child?",
            "What is the school calendar?",
            "Tell me about extracurricular activities"
          ].map((example, index) => (
            <button
              key={index}
              onClick={() => setTestMessage(example)}
              className="text-left p-2 sm:p-3 bg-neutral-100 dark:bg-neutral-700 rounded text-xs sm:text-sm hover:bg-neutral-200 dark:hover:bg-neutral-600 transition-colors"
            >
              "{example}"
            </button>
          ))}
        </div>
        <p className="text-xs text-neutral-500 mt-2">
          Click any example to use it as a test message
        </p>
      </div>
    </div>
  );
}