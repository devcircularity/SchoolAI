// components/admin/PatternBuilder.tsx
import React, { useState, useEffect } from 'react';
import { Plus, X, HelpCircle, Code, TestTube, CheckCircle, XCircle } from 'lucide-react';
import Button from '@/components/ui/Button';

interface PatternRule {
  id: string;
  type: 'exact' | 'contains' | 'starts_with' | 'ends_with' | 'any_of' | 'custom';
  value: string;
  optional?: boolean;
}

interface PatternBuilderProps {
  initialPattern?: string;
  onPatternChange: (pattern: string) => void;
  onTest?: (pattern: string, testMessage: string) => Promise<any>;
}

export function PatternBuilder({ initialPattern, onPatternChange, onTest }: PatternBuilderProps) {
  const [mode, setMode] = useState<'simple' | 'advanced'>('simple');
  const [rules, setRules] = useState<PatternRule[]>([]);
  const [customPattern, setCustomPattern] = useState(initialPattern || '');
  const [testMessage, setTestMessage] = useState('');
  const [testResult, setTestResult] = useState<any>(null);
  const [testing, setTesting] = useState(false);
  const [showHelp, setShowHelp] = useState(false);

  // Initialize from existing pattern
  useEffect(() => {
    if (initialPattern && rules.length === 0) {
      // Try to parse simple patterns, otherwise switch to advanced mode
      if (isSimplePattern(initialPattern)) {
        setRules(parseToRules(initialPattern));
      } else {
        setMode('advanced');
        setCustomPattern(initialPattern);
      }
    }
  }, [initialPattern]);

  // Generate pattern from rules
  useEffect(() => {
    if (mode === 'simple') {
      const generatedPattern = generatePattern(rules);
      setCustomPattern(generatedPattern);
      onPatternChange(generatedPattern);
    }
  }, [rules, mode]);

  // Handle custom pattern changes in advanced mode
  useEffect(() => {
    if (mode === 'advanced') {
      onPatternChange(customPattern);
    }
  }, [customPattern, mode]);

  const addRule = () => {
    const newRule: PatternRule = {
      id: Date.now().toString(),
      type: 'contains',
      value: '',
      optional: false
    };
    setRules([...rules, newRule]);
  };

  const updateRule = (id: string, updates: Partial<PatternRule>) => {
    setRules(rules.map(rule => 
      rule.id === id ? { ...rule, ...updates } : rule
    ));
  };

  const removeRule = (id: string) => {
    setRules(rules.filter(rule => rule.id !== id));
  };

  const handleTest = async () => {
    if (!testMessage.trim() || !onTest) return;
    
    try {
      setTesting(true);
      const result = await onTest(customPattern, testMessage);
      setTestResult(result);
    } catch (error) {
      setTestResult({
        matches: false,
        error: (error as Error).message
      });
    } finally {
      setTesting(false);
    }
  };

  const commonPatterns = [
    { name: 'Student count', pattern: '(how many|number of|count).*students?' },
    { name: 'Create student', pattern: '(create|add|register).*student' },
    { name: 'List students', pattern: '(list|show|display).*students?' },
    { name: 'School overview', pattern: '(school|overview|summary|dashboard)' },
    { name: 'Payment record', pattern: '(record|make|process).*payment' },
    { name: 'Generate invoice', pattern: '(generate|create|make).*invoice' },
    { name: 'Class management', pattern: '(class|classes).*(create|list|manage)' }
  ];

  return (
    <div className="space-y-6">
      {/* Mode Selector */}
      <div className="flex items-center gap-4">
        <div className="flex bg-gray-100 dark:bg-gray-800 rounded-lg p-1">
          <button
            onClick={() => setMode('simple')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              mode === 'simple' 
                ? 'bg-white dark:bg-gray-700 text-blue-600 shadow-sm' 
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            Simple Builder
          </button>
          <button
            onClick={() => setMode('advanced')}
            className={`px-3 py-1 rounded text-sm font-medium transition-colors ${
              mode === 'advanced' 
                ? 'bg-white dark:bg-gray-700 text-blue-600 shadow-sm' 
                : 'text-gray-600 dark:text-gray-400'
            }`}
          >
            Advanced (Regex)
          </button>
        </div>
        
        <button
          onClick={() => setShowHelp(!showHelp)}
          className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
        >
          <HelpCircle size={16} />
        </button>
      </div>

      {/* Help Section */}
      {showHelp && (
        <div className="bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg p-4">
          <h4 className="font-medium mb-2">Pattern Building Help</h4>
          <div className="text-sm space-y-2">
            <p><strong>Simple Builder:</strong> Build patterns using intuitive rules without regex knowledge.</p>
            <p><strong>Advanced Mode:</strong> Write custom regex patterns for complex matching.</p>
            <div className="mt-3">
              <p className="font-medium mb-1">Common Pattern Examples:</p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-2 text-xs">
                {commonPatterns.map((example, index) => (
                  <div key={index} className="bg-white dark:bg-gray-800 p-2 rounded border">
                    <div className="font-medium">{example.name}</div>
                    <code className="text-gray-600">{example.pattern}</code>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Simple Builder */}
      {mode === 'simple' && (
        <div className="space-y-4">
          <div className="flex justify-between items-center">
            <h4 className="font-medium">Pattern Rules</h4>
            <Button onClick={addRule} className="btn-sm flex items-center gap-2">
              <Plus size={14} />
              Add Rule
            </Button>
          </div>

          {rules.length === 0 && (
            <div className="text-center py-8 text-gray-500">
              <p>No rules defined yet. Add a rule to start building your pattern.</p>
            </div>
          )}

          {rules.map((rule, index) => (
            <div key={rule.id} className="border border-gray-200 dark:border-gray-700 rounded-lg p-4">
              <div className="flex items-center gap-4 mb-3">
                <span className="text-sm font-medium text-gray-500">
                  Rule {index + 1}
                </span>
                <button
                  onClick={() => removeRule(rule.id)}
                  className="text-red-500 hover:text-red-700"
                >
                  <X size={14} />
                </button>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">Match Type</label>
                  <select
                    value={rule.type}
                    onChange={(e) => updateRule(rule.id, { type: e.target.value as any })}
                    className="input"
                  >
                    <option value="contains">Contains word(s)</option>
                    <option value="exact">Exact phrase</option>
                    <option value="starts_with">Starts with</option>
                    <option value="ends_with">Ends with</option>
                    <option value="any_of">Any of these words</option>
                  </select>
                </div>

                <div>
                  <label className="block text-sm font-medium mb-1">Value</label>
                  <input
                    type="text"
                    value={rule.value}
                    onChange={(e) => updateRule(rule.id, { value: e.target.value })}
                    placeholder={getPlaceholder(rule.type)}
                    className="input"
                  />
                </div>

                <div className="flex items-end">
                  <label className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      checked={rule.optional || false}
                      onChange={(e) => updateRule(rule.id, { optional: e.target.checked })}
                      className="rounded"
                    />
                    <span className="text-sm">Optional</span>
                  </label>
                </div>
              </div>

              <div className="mt-2 text-xs text-gray-500">
                {getExplanation(rule)}
              </div>
            </div>
          ))}

          {/* Generated Pattern Preview */}
          {rules.length > 0 && (
            <div className="bg-gray-50 dark:bg-gray-800 p-4 rounded-lg">
              <div className="flex items-center gap-2 mb-2">
                <Code size={16} />
                <span className="font-medium">Generated Pattern:</span>
              </div>
              <code className="block bg-white dark:bg-gray-900 p-2 rounded border font-mono text-sm">
                {customPattern}
              </code>
            </div>
          )}
        </div>
      )}

      {/* Advanced Mode */}
      {mode === 'advanced' && (
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium mb-2">Regular Expression Pattern</label>
            <textarea
              value={customPattern}
              onChange={(e) => setCustomPattern(e.target.value)}
              placeholder="Enter your regex pattern..."
              className="input min-h-[100px] font-mono text-sm"
              rows={4}
            />
            <p className="text-xs text-gray-500 mt-2">
              Use JavaScript regex syntax. The pattern will be tested case-insensitively.
              <br />
              Examples: <code>(student|pupil)</code>, <code>create.*student</code>, <code>^how many</code>
            </p>
          </div>

          {/* Quick Insert Common Patterns */}
          <div>
            <p className="text-sm font-medium mb-2">Quick Insert:</p>
            <div className="flex flex-wrap gap-2">
              {commonPatterns.map((example, index) => (
                <button
                  key={index}
                  onClick={() => setCustomPattern(example.pattern)}
                  className="text-xs px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded hover:bg-blue-200 dark:hover:bg-blue-900/50"
                  title={`Insert pattern for ${example.name}`}
                >
                  {example.name}
                </button>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Test Section */}
      <div className="border-t pt-4">
        <h4 className="font-medium mb-3">Test Pattern</h4>
        <div className="flex gap-2 mb-3">
          <input
            type="text"
            value={testMessage}
            onChange={(e) => setTestMessage(e.target.value)}
            placeholder="Enter a test message..."
            className="input flex-1"
            onKeyPress={(e) => e.key === 'Enter' && handleTest()}
          />
          <Button
            onClick={handleTest}
            disabled={testing || !testMessage.trim() || !customPattern}
            className="flex items-center gap-2"
          >
            <TestTube size={14} />
            {testing ? 'Testing...' : 'Test'}
          </Button>
        </div>

        {testResult && (
          <div className="space-y-2">
            <div className={`flex items-center gap-2 text-sm ${
              testResult.matches ? 'text-green-700' : 'text-red-700'
            }`}>
              {testResult.matches ? <CheckCircle size={16} /> : <XCircle size={16} />}
              <span>{testResult.matches ? 'Pattern matches!' : 'No match'}</span>
            </div>

            {testResult.matches && testResult.match_text && (
              <div className="text-sm bg-green-50 dark:bg-green-900/20 p-2 rounded">
                <strong>Matched:</strong> "{testResult.match_text}"
                {testResult.match_start !== undefined && (
                  <span className="ml-2 text-xs text-gray-600">
                    (position {testResult.match_start}-{testResult.match_end})
                  </span>
                )}
              </div>
            )}

            {testResult.error && (
              <div className="text-sm bg-red-50 dark:bg-red-900/20 p-2 rounded text-red-700">
                <strong>Error:</strong> {testResult.error}
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}

// Helper functions
function getPlaceholder(type: string): string {
  switch (type) {
    case 'contains': return 'student, payment, class';
    case 'exact': return 'how many students';
    case 'starts_with': return 'create';
    case 'ends_with': return 'students';
    case 'any_of': return 'student,pupil,learner';
    default: return '';
  }
}

function getExplanation(rule: PatternRule): string {
  const optional = rule.optional ? ' (optional)' : '';
  switch (rule.type) {
    case 'contains':
      return `Matches messages containing "${rule.value}"${optional}`;
    case 'exact':
      return `Matches messages with exact phrase "${rule.value}"${optional}`;
    case 'starts_with':
      return `Matches messages starting with "${rule.value}"${optional}`;
    case 'ends_with':
      return `Matches messages ending with "${rule.value}"${optional}`;
    case 'any_of':
      return `Matches messages containing any of: ${rule.value.split(',').join(', ')}${optional}`;
    default:
      return '';
  }
}

function generatePattern(rules: PatternRule[]): string {
  if (rules.length === 0) return '';

  const patterns = rules.map(rule => {
    let pattern = '';
    
    switch (rule.type) {
      case 'contains':
        pattern = `.*${escapeRegex(rule.value)}.*`;
        break;
      case 'exact':
        pattern = escapeRegex(rule.value);
        break;
      case 'starts_with':
        pattern = `^${escapeRegex(rule.value)}.*`;
        break;
      case 'ends_with':
        pattern = `.*${escapeRegex(rule.value)}$`;
        break;
      case 'any_of':
        const words = rule.value.split(',').map(w => w.trim()).filter(w => w);
        pattern = `.*(${words.map(escapeRegex).join('|')}).*`;
        break;
    }

    return rule.optional ? `(${pattern})?` : `(${pattern})`;
  });

  return patterns.join('');
}

function escapeRegex(str: string): string {
  return str.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
}

function isSimplePattern(pattern: string): boolean {
  // Basic heuristic to determine if a pattern was likely generated by simple builder
  // This is imperfect but covers common cases
  return !pattern.includes('[') && !pattern.includes('{') && !pattern.includes('\\w') && !pattern.includes('\\d');
}

function parseToRules(pattern: string): PatternRule[] {
  // Basic parsing - this is complex and imperfect
  // For now, return empty array to force advanced mode for existing patterns
  return [];
}