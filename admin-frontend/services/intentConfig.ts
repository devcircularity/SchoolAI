// services/intentConfig.ts - Updated with phrase support and missing methods
import { apiClient } from './api';

export interface IntentConfigVersion {
  id: string;
  name: string;
  status: 'candidate' | 'active' | 'archived';
  notes?: string;
  created_at: string;
  updated_at: string;
  activated_at?: string;
  pattern_count: number;
  template_count: number;
}

// Enhanced with phrase support
export interface IntentPattern {
  id: string;
  handler: string;
  intent: string;
  kind: 'positive' | 'negative' | 'synonym';
  pattern: string;
  priority: number;
  enabled: boolean;
  scope_school_id?: string;
  created_at: string;
  updated_at: string;
  // NEW: Phrase support fields
  phrases?: string[];
  regex_confidence?: number;
  regex_explanation?: string;
}

export interface PromptTemplate {
  id: string;
  handler: string;
  intent?: string;
  template_type: 'system' | 'user' | 'fallback_context';
  template_text: string;
  enabled: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConfigurationOverview {
  active_version?: IntentConfigVersion;
  candidate_version?: IntentConfigVersion;
  total_patterns: number;
  total_templates: number;
  enabled_patterns: number;
  enabled_templates: number;
  system_health: 'healthy' | 'warning' | 'error';
  cache_status: 'loaded' | 'loading' | 'error';
}

export interface CreateVersionRequest {
  name: string;
  notes?: string;
  copy_from?: string;
}

// Enhanced with phrase support
export interface CreatePatternRequest {
  handler: string;
  intent: string;
  kind: 'positive' | 'negative' | 'synonym';
  pattern?: string; // Now optional when phrases are provided
  priority?: number;
  enabled?: boolean;
  scope_school_id?: string;
  // NEW: Phrase support
  phrases?: string[];
}

// Enhanced with phrase support
export interface UpdatePatternRequest {
  handler?: string;
  intent?: string;
  kind?: string;
  pattern?: string;
  priority?: number;
  enabled?: boolean;
  scope_school_id?: string;
  // NEW: Phrase support
  phrases?: string[];
  regenerate_regex?: boolean; // Force regeneration even if pattern exists
}

export interface CreateTemplateRequest {
  handler: string;
  intent?: string;
  template_type: 'system' | 'user' | 'fallback_context';
  template_text: string;
  enabled?: boolean;
}

export interface UpdateTemplateRequest {
  handler?: string;
  intent?: string;
  template_type?: string;
  template_text?: string;
  enabled?: boolean;
}

export interface TestClassifyRequest {
  message: string;
  school_id?: string;
}

export interface TestClassifyResponse {
  message: string;
  config_router_result?: any;
  llm_classifier_result?: any;
  final_decision: any;
  processing_steps: string[];
}

// NEW: Regex generation interfaces
export interface GenerateRegexRequest {
  phrases: string[];
  intent: string;
  pattern_kind?: string;
}

export interface GenerateRegexResponse {
  phrases: string[];
  intent: string;
  pattern_kind: string;
  generated_regex: string;
  confidence: number;
  explanation: string;
  test_matches: string[];
  errors: string[];
}

export interface TestPatternWithPhrasesRequest {
  test_messages: string[];
}

export interface TestPatternWithPhrasesResponse {
  pattern_id: string;
  pattern: string;
  phrases?: string[];
  test_results: {
    regex: string;
    matches: Array<{
      phrase: string;
      match_text: string;
      start: number;
      end: number;
    }>;
    non_matches: string[];
    errors: string[];
  };
  summary: {
    total_tested: number;
    matches: number;
    non_matches: number;
    match_rate: number;
  };
}

export interface ImprovePatternRequest {
  missed_phrases: string[];
  false_positives?: string[];
}

export interface ImprovePatternResponse {
  pattern_id: string;
  current_regex: string;
  suggested_regex: string;
  confidence: number;
  explanation: string;
  improvements: {
    missed_phrases: string[];
    false_positives: string[];
  };
}

// NEW: Validation interfaces
export interface ValidationResult {
  overall_valid: boolean;
  patterns?: {
    total: number;
    valid: number;
    invalid: number;
    errors?: Array<{
      intent: string;
      error: string;
      pattern: string;
    }>;
  };
  templates?: {
    total: number;
    valid: number;
    invalid: number;
    errors?: Array<{
      intent: string;
      error: string;
      template: string;
    }>;
  };
  error?: string;
}

class IntentConfigService {
  // CONFIGURATION OVERVIEW AND MANAGEMENT
  async getConfigurationOverview(): Promise<ConfigurationOverview> {
    const response = await apiClient.get('/api/admin/configuration/overview');
    return response.data;
  }

  async getCacheStats(): Promise<any> {
    const response = await apiClient.get('/api/admin/configuration/cache/stats');
    return response.data;
  }

  async reloadCache(): Promise<{ message: string; cache_stats: any }> {
    const response = await apiClient.post('/api/admin/configuration/cache/reload');
    return response.data;
  }

  // VERSION MANAGEMENT
  async getVersions(): Promise<IntentConfigVersion[]> {
    const response = await apiClient.get('/api/admin/intent-config/versions');
    return response.data;
  }

  async createVersion(data: CreateVersionRequest): Promise<IntentConfigVersion> {
    const response = await apiClient.post('/api/admin/intent-config/versions', data);
    return response.data;
  }

  async promoteVersion(versionId: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/intent-config/versions/${versionId}/promote`);
    return response.data;
  }

  async archiveVersion(versionId: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/intent-config/versions/${versionId}/archive`);
    return response.data;
  }

  // ENHANCED PATTERN MANAGEMENT WITH PHRASE SUPPORT
  async getPatterns(
    versionId: string,
    filters?: {
      handler?: string;
      intent?: string;
      kind?: string;
    }
  ): Promise<IntentPattern[]> {
    const params = new URLSearchParams();
    if (filters?.handler) params.append('handler', filters.handler);
    if (filters?.intent) params.append('intent', filters.intent);
    if (filters?.kind) params.append('kind', filters.kind);

    const response = await apiClient.get(
      `/api/admin/intent-config/versions/${versionId}/patterns?${params.toString()}`
    );
    return response.data;
  }

  async createPattern(versionId: string, data: CreatePatternRequest): Promise<IntentPattern> {
    const response = await apiClient.post(
      `/api/admin/intent-config/versions/${versionId}/patterns`,
      data
    );
    return response.data;
  }

  async updatePattern(patternId: string, data: UpdatePatternRequest): Promise<IntentPattern> {
    const response = await apiClient.put(`/api/admin/intent-config/patterns/${patternId}`, data);
    return response.data;
  }

  async deletePattern(patternId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/admin/intent-config/patterns/${patternId}`);
    return response.data;
  }

  async enablePattern(patternId: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/intent-config/patterns/${patternId}/enable`);
    return response.data;
  }

  // NEW: Enhanced pattern testing with phrases
  async testPatternWithPhrases(
    patternId: string, 
    testMessages: string[]
  ): Promise<TestPatternWithPhrasesResponse> {
    const response = await apiClient.post(
      `/api/admin/intent-config/patterns/${patternId}/test-phrases`,
      testMessages
    );
    return response.data;
  }

  // NEW: Pattern improvement suggestions
  async improvePattern(
    patternId: string,
    missedPhrases: string[],
    falsePositives?: string[]
  ): Promise<ImprovePatternResponse> {
    const response = await apiClient.post(
      `/api/admin/intent-config/patterns/${patternId}/improve`,
      {
        missed_phrases: missedPhrases,
        false_positives: falsePositives
      }
    );
    return response.data;
  }

  // Legacy pattern test (for backward compatibility)
  async testPattern(patternId: string, testMessage: string): Promise<{
    pattern_id: string;
    pattern: string;
    test_message: string;
    matches: boolean;
    match_text?: string;
    match_start?: number;
    match_end?: number;
    groups?: string[];
    named_groups?: Record<string, string>;
  }> {
    const response = await apiClient.post(
      `/api/admin/intent-config/patterns/${patternId}/test`,
      { test_message: testMessage }
    );
    return response.data;
  }

  // TEMPLATE MANAGEMENT
  async getTemplates(
    versionId: string,
    filters?: {
      handler?: string;
      template_type?: string;
    }
  ): Promise<PromptTemplate[]> {
    const params = new URLSearchParams();
    if (filters?.handler) params.append('handler', filters.handler);
    if (filters?.template_type) params.append('template_type', filters.template_type);

    const response = await apiClient.get(
      `/api/admin/intent-config/versions/${versionId}/templates?${params.toString()}`
    );
    return response.data;
  }

  async createTemplate(versionId: string, data: CreateTemplateRequest): Promise<PromptTemplate> {
    const response = await apiClient.post(
      `/api/admin/intent-config/versions/${versionId}/templates`,
      data
    );
    return response.data;
  }

  async updateTemplate(templateId: string, data: UpdateTemplateRequest): Promise<PromptTemplate> {
    const response = await apiClient.put(`/api/admin/intent-config/templates/${templateId}`, data);
    return response.data;
  }

  async deleteTemplate(templateId: string): Promise<{ message: string }> {
    const response = await apiClient.delete(`/api/admin/intent-config/templates/${templateId}`);
    return response.data;
  }

  async enableTemplate(templateId: string): Promise<{ message: string }> {
    const response = await apiClient.post(`/api/admin/intent-config/templates/${templateId}/enable`);
    return response.data;
  }

  // TESTING
  async testClassify(data: TestClassifyRequest): Promise<TestClassifyResponse> {
    const response = await apiClient.post('/api/admin/intent-config/test-classify', data);
    return response.data;
  }

  // LEGACY SUPPORT
  async reloadConfig(): Promise<{ message: string; cache_stats: any }> {
    const response = await apiClient.post('/api/admin/intent-config/reload');
    return response.data;
  }

  async getStats(): Promise<any> {
    const response = await apiClient.get('/api/admin/intent-config/stats');
    return response.data;
  }

  // UTILITY ENDPOINTS
  async getAvailableHandlers(): Promise<{ handlers: string[] }> {
    const response = await apiClient.get('/api/admin/intent-config/handlers');
    return response.data;
  }

  async getAvailableIntents(handler?: string): Promise<{ intents: string[] }> {
    const params = handler ? `?handler=${handler}` : '';
    const response = await apiClient.get(`/api/admin/intent-config/intents${params}`);
    return response.data;
  }

  async getPatternKinds(): Promise<{ kinds: Array<{ value: string; label: string }> }> {
    const response = await apiClient.get('/api/admin/intent-config/pattern-kinds');
    return response.data;
  }

  async getTemplateTypes(): Promise<{ types: Array<{ value: string; label: string }> }> {
    const response = await apiClient.get('/api/admin/intent-config/template-types');
    return response.data;
  }

  // NEW: Generate regex from phrases
  async generateRegexFromPhrases(data: GenerateRegexRequest): Promise<GenerateRegexResponse> {
    console.log('🔍 Sending regex generation request:', data);
    
    try {
      const response = await apiClient.post('/api/admin/intent-config/generate-regex', data);
      console.log('🔍 Raw API response:', response.data);
      
      // Make sure the response has the expected structure
      const result: GenerateRegexResponse = {
        phrases: response.data.phrases || data.phrases,
        intent: response.data.intent || data.intent,
        pattern_kind: response.data.pattern_kind || data.pattern_kind || 'positive',
        generated_regex: response.data.generated_regex || response.data.regex || '',
        confidence: response.data.confidence || 0,
        explanation: response.data.explanation || '',
        test_matches: response.data.test_matches || [],
        errors: response.data.errors || []
      };
      
      console.log('🔍 Processed regex generation response:', result);
      
      return result;
    } catch (error) {
      console.error('❌ Regex generation API error:', error);
      throw error;
    }
  }

  // NEW: Export configuration
  async exportConfiguration(versionId: string, format: 'json' | 'yaml'): Promise<Blob> {
    const response = await apiClient.get(
      `/api/admin/intent-config/versions/${versionId}/export?format=${format}`,
      { responseType: 'blob' }
    );
    return response.data;
  }

  // NEW: Validate configuration
  async validateConfiguration(versionId: string): Promise<ValidationResult> {
    const response = await apiClient.post(
      `/api/admin/intent-config/versions/${versionId}/validate`
    );
    return response.data;
  }
}

export const intentConfigService = new IntentConfigService();