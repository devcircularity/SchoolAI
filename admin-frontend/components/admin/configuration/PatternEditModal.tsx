// app/admin/configuration/components/PatternEditModal.tsx
import { useState, useEffect } from "react";
import { Save, X, Plus, Trash2, Wand2, ExternalLink } from "lucide-react";
import { intentConfigService, IntentPattern } from "@/services/intentConfig";
import Button from "@/components/ui/Button";

// Enhanced Pattern interface with phrase support
interface EnhancedIntentPattern extends IntentPattern {
  phrases?: string[];
  regex_confidence?: number;
  regex_explanation?: string;
}

interface EditingItem {
  type: 'pattern' | 'template';
  item: EnhancedIntentPattern;
  isNew?: boolean;
}

interface PatternEditModalProps {
  item: EditingItem;
  availableHandlers: string[];
  availableIntents: string[];
  onSave: () => void;
  onClose: () => void;
  onChange: (item: EditingItem) => void;
  suggestionContext?: {
    suggestionId: string;
    title: string;
    handler: string;
    intent: string;
    pattern: string;
  } | null;
}

export default function PatternEditModal({
  item,
  availableHandlers,
  availableIntents,
  onSave,
  onClose,
  onChange,
  suggestionContext
}: PatternEditModalProps) {
  const [generatingRegex, setGeneratingRegex] = useState(false);
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [loadingIntents, setLoadingIntents] = useState(false);
  const [filteredIntents, setFilteredIntents] = useState<string[]>(availableIntents);

  // Show advanced section if we have a pre-existing pattern from suggestion
  useEffect(() => {
    if (suggestionContext && suggestionContext.pattern) {
      setShowAdvanced(true);
    }
  }, [suggestionContext]);

  // Filter intents when handler changes
  useEffect(() => {
    const loadIntentsForHandler = async () => {
      if (item.item.handler) {
        setLoadingIntents(true);
        try {
          const response = await intentConfigService.getAvailableIntents(item.item.handler);
          setFilteredIntents(response.intents);
        } catch (error) {
          console.error('Failed to load intents for handler:', error);
          setFilteredIntents(availableIntents);
        } finally {
          setLoadingIntents(false);
        }
      } else {
        setFilteredIntents(availableIntents);
      }
    };

    loadIntentsForHandler();
  }, [item.item.handler, availableIntents]);

  const updateItem = (field: string, value: any) => {
    onChange({
      ...item,
      item: { ...item.item, [field]: value }
    });
  };

  const handleAddPhrase = () => {
    const pattern = item.item as EnhancedIntentPattern;
    const currentPhrases = pattern.phrases || [];
    updateItem('phrases', [...currentPhrases, '']);
  };

  const handleUpdatePhrase = (index: number, value: string) => {
    const pattern = item.item as EnhancedIntentPattern;
    const currentPhrases = pattern.phrases || [];
    const newPhrases = [...currentPhrases];
    newPhrases[index] = value;
    updateItem('phrases', newPhrases);
  };

  const handleRemovePhrase = (index: number) => {
    const pattern = item.item as EnhancedIntentPattern;
    const currentPhrases = pattern.phrases || [];
    const newPhrases = currentPhrases.filter((_, i) => i !== index);
    updateItem('phrases', newPhrases);
  };

  const handleGenerateRegex = async () => {
    const pattern = item.item as EnhancedIntentPattern;
    const phrases = pattern.phrases?.filter(p => p.trim()) || [];
    
    if (phrases.length === 0) {
      alert('Please add at least one phrase before generating regex');
      return;
    }

    setGeneratingRegex(true);
    try {
      const result = await intentConfigService.generateRegexFromPhrases({
        phrases,
        intent: pattern.intent,
        pattern_kind: pattern.kind
      });
      
      if (result.errors && result.errors.length > 0) {
        console.warn('Regex generation warnings:', result.errors);
        alert(`Regex generation warnings: ${result.errors.join(', ')}`);
      }

      const generatedRegex = result.generated_regex || '';
      const confidence = result.confidence || 0;
      const explanation = result.explanation || '';

      const updatedItem = {
        ...item,
        item: {
          ...item.item,
          pattern: generatedRegex,
          regex_confidence: confidence,
          regex_explanation: explanation,
        } as EnhancedIntentPattern
      };

      onChange(updatedItem);
      
      if (generatedRegex) {
        setShowAdvanced(true);
      }
      
    } catch (error) {
      console.error('Failed to generate regex:', error);
      alert('Failed to generate regex. Please try again or enter manually.');
    } finally {
      setGeneratingRegex(false);
    }
  };

  const handleViewOriginalSuggestion = () => {
    if (suggestionContext) {
      window.open(`/admin/configuration?tab=implementation&suggestion=${suggestionContext.suggestionId}`, '_blank');
    }
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
      <div className="absolute inset-0 bg-black/50" onClick={onClose} />
      <div className="relative bg-white dark:bg-neutral-800 rounded-2xl shadow-2xl max-w-4xl w-full max-h-[90vh] overflow-y-auto">
        <div className="p-4 sm:p-6">
          {/* Header */}
          <div className="flex justify-between items-start mb-4 sm:mb-6">
            <div className="min-w-0">
              <h2 className="text-lg sm:text-xl font-bold">
                {item.isNew ? 'Add' : 'Edit'} Pattern
              </h2>
              {suggestionContext && (
                <p className="text-sm text-neutral-600 dark:text-neutral-400 mt-1">
                  From implementation suggestion: {suggestionContext.title}
                </p>
              )}
            </div>
            <div className="flex gap-2 flex-shrink-0">
              {suggestionContext && (
                <Button 
                  onClick={handleViewOriginalSuggestion}
                  className="text-sm btn-secondary flex items-center gap-1"
                >
                  <ExternalLink size={14} />
                  <span className="hidden sm:inline">View Original</span>
                </Button>
              )}
              <Button onClick={onClose} className="text-sm btn-secondary">
                <X size={16} />
              </Button>
            </div>
          </div>

          {/* Suggestion Context Banner */}
          {suggestionContext && (
            <div className="mb-4 p-3 bg-blue-50 dark:bg-blue-900/20 border border-blue-200 dark:border-blue-800 rounded-lg">
              <h4 className="text-sm font-medium text-blue-800 dark:text-blue-200 mb-1">
                Implementation Context
              </h4>
              <p className="text-xs text-blue-700 dark:text-blue-300">
                This pattern is being created from suggestion "{suggestionContext.title}". 
                The form has been pre-populated with suggested values - review and adjust as needed.
              </p>
            </div>
          )}

          <div className="space-y-4 sm:space-y-6">
            {/* Common Fields - Mobile responsive */}
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 sm:gap-4">
              <div>
                <label className="label text-sm">Handler</label>
                <select
                  value={item.item.handler}
                  onChange={(e) => updateItem('handler', e.target.value)}
                  className="input text-sm"
                >
                  <option value="">Select handler...</option>
                  {availableHandlers.map(handler => (
                    <option key={handler} value={handler}>{handler}</option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="label text-sm">Intent</label>
                <div className="relative">
                  <select
                    value={item.item.intent}
                    onChange={(e) => updateItem('intent', e.target.value)}
                    className="input text-sm"
                    disabled={loadingIntents}
                  >
                    <option value="">
                      {loadingIntents ? 'Loading intents...' : 
                       !item.item.handler ? 'Select handler first...' : 
                       'Select intent...'}
                    </option>
                    {filteredIntents.map(intent => (
                      <option key={intent} value={intent}>{intent}</option>
                    ))}
                  </select>
                  {loadingIntents && (
                    <div className="absolute right-3 top-1/2 transform -translate-y-1/2">
                      <div className="animate-spin rounded-full h-4 w-4 border-b-2 border-blue-600"></div>
                    </div>
                  )}
                </div>
              </div>
            </div>

            {/* Pattern-specific fields - Mobile responsive */}
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 sm:gap-4">
              <div>
                <label className="label text-sm">Kind</label>
                <select
                  value={item.item.kind}
                  onChange={(e) => updateItem('kind', e.target.value)}
                  className="input text-sm"
                >
                  <option value="positive">Positive</option>
                  <option value="negative">Negative</option>
                  <option value="synonym">Synonym</option>
                </select>
              </div>
              
              <div>
                <label className="label text-sm">Priority</label>
                <input
                  type="number"
                  value={item.item.priority}
                  onChange={(e) => updateItem('priority', parseInt(e.target.value))}
                  className="input text-sm"
                />
              </div>
              
              <div>
                <label className="label text-sm">School Scope (Optional)</label>
                <input
                  type="text"
                  value={item.item.scope_school_id || ''}
                  onChange={(e) => updateItem('scope_school_id', e.target.value || undefined)}
                  placeholder="Leave empty for global"
                  className="input text-sm"
                />
              </div>
            </div>

            {/* Phrases Section */}
            <div className="space-y-3 sm:space-y-4">
              <div className="flex flex-col sm:flex-row sm:justify-between sm:items-center gap-2">
                <div>
                  <label className="label text-sm">Example Phrases (Recommended)</label>
                  <p className="text-xs text-neutral-500">
                    Add natural language examples. We'll automatically generate the regex for you.
                  </p>
                </div>
                <Button
                  onClick={() => setShowAdvanced(!showAdvanced)}
                  className="text-xs btn-secondary"
                >
                  {showAdvanced ? 'Hide Advanced' : 'Show Advanced'}
                </Button>
              </div>

              {/* Phrases List and Add Phrase Button */}
              <div className="space-y-3">
                <Button
                  onClick={handleAddPhrase}
                  className="flex items-center gap-2 text-sm btn-secondary"
                >
                  <Plus size={14} />
                  Add Phrase
                </Button>
                
                <div className="space-y-2">
                  {(item.item.phrases || ['']).map((phrase, index) => (
                    <div key={index} className="flex gap-2">
                      <input
                        type="text"
                        value={phrase}
                        onChange={(e) => handleUpdatePhrase(index, e.target.value)}
                        placeholder={`Example: "show me student details"`}
                        className="input flex-1 text-sm"
                      />
                      {(item.item.phrases || []).length > 1 && (
                        <Button
                          onClick={() => handleRemovePhrase(index)}
                          className="px-2 text-sm btn-secondary"
                        >
                          <Trash2 size={14} />
                        </Button>
                      )}
                    </div>
                  ))}
                </div>

                {/* Generate Regex Button */}
                {(item.item.phrases || []).some(p => p.trim()) && (
                  <div className="flex justify-center">
                    <Button
                      onClick={handleGenerateRegex}
                      disabled={generatingRegex}
                      className="flex items-center gap-2 text-sm"
                    >
                      <Wand2 size={16} />
                      {generatingRegex ? 'Generating...' : 'Generate Regex from Phrases'}
                    </Button>
                  </div>
                )}
              </div>
            </div>

            {/* Advanced Regex Section */}
            {showAdvanced && (
              <div className="space-y-3">
                <div>
                  <label className="label text-sm">Regex Pattern</label>
                  <textarea
                    value={item.item.pattern}
                    onChange={(e) => updateItem('pattern', e.target.value)}
                    placeholder="Enter regex pattern or generate from phrases above..."
                    className="input font-mono text-sm"
                    rows={3}
                  />
                  
                  {/* Confidence and Explanation Display */}
                  {item.item.regex_confidence && (
                    <div className="mt-2 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium">Confidence:</span>
                        <span className={`px-2 py-1 rounded text-xs ${
                          item.item.regex_confidence >= 0.8 ? 'bg-green-100 text-green-700' :
                          item.item.regex_confidence >= 0.6 ? 'bg-yellow-100 text-yellow-700' :
                          'bg-red-100 text-red-700'
                        }`}>
                          {Math.round(item.item.regex_confidence * 100)}%
                        </span>
                      </div>
                      {item.item.regex_explanation && (
                        <p className="text-sm text-blue-700 dark:text-blue-300">
                          {item.item.regex_explanation}
                        </p>
                      )}
                    </div>
                  )}

                  <p className="text-xs text-neutral-500 mt-2">
                    Advanced: You can manually edit the regex pattern here. Use phrases above for easier pattern creation.
                  </p>
                </div>
              </div>
            )}

            {/* Common enabled checkbox */}
            <div>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={item.item.enabled}
                  onChange={(e) => updateItem('enabled', e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm">Enabled</span>
              </label>
            </div>
          </div>
          
          <div className="flex flex-col sm:flex-row gap-3 mt-4 sm:mt-6 pt-4 border-t">
            <Button onClick={onSave} className="flex-1 text-sm">
              <Save size={16} className="mr-2" />
              {item.isNew ? 'Create Pattern' : 'Save Changes'}
            </Button>
            <Button onClick={onClose} className="flex-1 text-sm btn-secondary">
              Cancel
            </Button>
          </div>
        </div>
      </div>
    </div>
  );
}