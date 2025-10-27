// services/fileService.ts - Complete with enhanced debugging
import { api } from './api';

export interface ChatFileAttachment {
  attachment_id: string;
  original_filename: string;
  content_type: string;
  file_size: number;
  cloudinary_url: string;
  cloudinary_public_id: string;
  upload_timestamp: string;
  ocr_processed: boolean;
  ocr_data?: any;
}

export interface ChatWithFilesResponse {
  response: string;
  intent?: string;
  data?: any;
  action_taken?: string;
  suggestions?: string[];
  conversation_id?: string;
  blocks?: any[];
  attachment_processed?: boolean;
}

export interface FileValidationResult {
  valid: boolean;
  error?: string;
}

export interface HealthCheckResponse {
  status: 'healthy' | 'unhealthy';
  services?: {
    ocr?: { status: string };
    ollama?: { status: string };
    cloudinary?: { status: string };
  };
  error?: string;
}

export const fileService = {
  /**
   * Send chat message with file attachments
   * This integrates directly with the chat system
   */
  async sendChatMessageWithFiles(
    message: string,
    files: File[],
    conversationId?: string
  ): Promise<ChatWithFilesResponse> {
    console.log('=== FILE SERVICE DEBUG START ===')
    console.log('Message:', message)
    console.log('Files count:', files.length)
    console.log('ConversationId received:', conversationId)
    console.log('ConversationId type:', typeof conversationId)
    console.log('ConversationId truthy?', !!conversationId)
    console.log('ConversationId === "undefined"?', conversationId === 'undefined')
    console.log('ConversationId === undefined?', conversationId === undefined)
    console.log('ConversationId === null?', conversationId === null)
    console.log('ConversationId === ""?', conversationId === '')
    
    const formData = new FormData();
    formData.append('message', message);
    
    // Enhanced conversation ID handling with explicit checks
    if (conversationId && conversationId !== 'undefined' && conversationId !== 'null' && conversationId.trim() !== '') {
      console.log('✅ Appending conversation_id to FormData:', conversationId)
      formData.append('conversation_id', conversationId.trim());
    } else {
      console.log('❌ NOT appending conversation_id - will create new conversation')
      console.log('  Reason: conversationId is', conversationId)
    }
    
    // Debug: Log all FormData entries before adding files
    console.log('FormData contents before files:')
    for (let [key, value] of formData.entries()) {
      if (typeof value === 'string') {
        console.log(`  ${key}: "${value}"`)
      } else {
        console.log(`  ${key}:`, value)
      }
    }
    
    // Append all files
    files.forEach((file, index) => {
      console.log(`Appending file ${index}: ${file.name} (${file.size} bytes, ${file.type})`)
      formData.append('files', file);
    });

    // Final FormData check
    console.log('Final FormData entries:')
    let hasConversationId = false;
    for (let [key, value] of formData.entries()) {
      if (key === 'conversation_id') {
        hasConversationId = true;
        console.log(`  ✅ ${key}: "${value}"`)
      } else if (key === 'message') {
        console.log(`  ${key}: "${value}"`)
      } else if (key === 'files') {
        console.log(`  ${key}: [File object]`)
      } else {
        console.log(`  ${key}:`, value)
      }
    }
    console.log('Has conversation_id in FormData?', hasConversationId)

    try {
      console.log('🚀 Making API call to /api/chat/message-with-files')
      const startTime = Date.now();
      
      const { data } = await api.post('/api/chat/message-with-files', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes timeout for file processing
      });
      
      const endTime = Date.now();
      console.log('✅ API Response received in', endTime - startTime, 'ms')
      console.log('Response data:', {
        conversation_id: data.conversation_id,
        intent: data.intent,
        response_preview: data.response?.substring(0, 100) + '...',
        attachment_processed: data.attachment_processed,
        blocks_count: data.blocks?.length || 0
      })
      
      // Check if conversation ID changed
      if (conversationId && data.conversation_id && conversationId !== data.conversation_id) {
        console.log('⚠️ CONVERSATION ID MISMATCH!')
        console.log('  Sent:', conversationId)
        console.log('  Received:', data.conversation_id)
      } else if (!conversationId && data.conversation_id) {
        console.log('✅ New conversation created:', data.conversation_id)
      } else if (conversationId && data.conversation_id && conversationId === data.conversation_id) {
        console.log('✅ Message added to existing conversation:', data.conversation_id)
      }
      
      console.log('=== FILE SERVICE DEBUG END ===')
      return data;
    } catch (error: any) {
      console.error('❌ FILE SERVICE ERROR:', error)
      console.error('Error details:', {
        status: error.response?.status,
        statusText: error.response?.statusText,
        data: error.response?.data,
        message: error.message
      })
      
      const errorMessage = error.response?.data?.detail || error.message || 'File processing failed';
      throw new Error(errorMessage);
    }
  },

  /**
   * Test file upload and OCR processing only (for debugging)
   */
  async testFileUpload(file: File): Promise<any> {
    console.log('Testing file upload for:', file.name)
    const formData = new FormData();
    formData.append('file', file);

    try {
      const { data } = await api.post('/api/test/upload-file', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });
      console.log('Test upload successful:', data)
      return data;
    } catch (error: any) {
      console.error('Test upload failed:', error)
      throw new Error(error.response?.data?.detail || 'Test upload failed');
    }
  },

  /**
   * Test complete pipeline (upload + OCR + AI interpretation)
   */
  async testCompleteProcessing(file: File, message: string = "What is this document about?"): Promise<any> {
    console.log('Testing complete processing for:', file.name)
    const formData = new FormData();
    formData.append('file', file);
    formData.append('message', message);

    try {
      const { data } = await api.post('/api/test/test-ollama', formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
        timeout: 120000, // 2 minutes timeout
      });
      console.log('Complete processing test successful')
      return data;
    } catch (error: any) {
      console.error('Complete processing test failed:', error)
      throw new Error(error.response?.data?.detail || 'Test processing failed');
    }
  },

  /**
   * Check health of all file processing services
   */
  async healthCheck(): Promise<HealthCheckResponse> {
    try {
      const { data } = await api.get('/api/test/health/services');
      console.log('Health check result:', data)
      return data;
    } catch (error: any) {
      console.error('Health check failed:', error)
      return {
        status: 'unhealthy',
        error: error.response?.data?.detail || 'Health check failed'
      };
    }
  },

  /**
   * Check Ollama service specifically
   */
  async checkOllamaHealth(): Promise<any> {
    try {
      const { data } = await api.get('/api/chat/health/ollama');
      console.log('Ollama health check result:', data)
      return data;
    } catch (error: any) {
      console.error('Ollama health check failed:', error)
      return {
        ollama_available: false,
        error: error.response?.data?.detail || 'Ollama health check failed'
      };
    }
  },

  /**
   * Utility functions for client-side file handling
   */
  utils: {
    /**
     * Format file size in human readable format
     */
    formatFileSize(bytes: number): string {
      if (bytes < 1024) return bytes + ' B';
      if (bytes < 1048576) return Math.round(bytes / 1024) + ' KB';
      return Math.round(bytes / 1048576 * 100) / 100 + ' MB';
    },

    /**
     * Validate file client-side before upload
     */
    validateFileClientSide(file: File): FileValidationResult {
      const maxSizeMB = 10;
      const supportedTypes = [
        'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
        'image/webp', 'image/bmp', 'image/tiff',
        'application/pdf'
      ];
      
      // Check file type
      if (!supportedTypes.includes(file.type)) {
        return {
          valid: false,
          error: `Unsupported file type: ${file.type}. Supported: images and PDFs`
        };
      }
      
      // Check file size
      if (file.size > maxSizeMB * 1024 * 1024) {
        return {
          valid: false,
          error: `File too large: ${this.formatFileSize(file.size)}. Maximum: ${maxSizeMB}MB`
        };
      }
      
      return { valid: true };
    },

    /**
     * Get file extension from filename
     */
    getFileExtension(filename: string): string {
      return '.' + filename.split('.').pop()?.toLowerCase() || '';
    },

    /**
     * Check if file is an image
     */
    isImageFile(file: File): boolean {
      return file.type.startsWith('image/');
    },

    /**
     * Check if file is a PDF
     */
    isPDFFile(file: File): boolean {
      return file.type === 'application/pdf';
    },

    /**
     * Create preview URL for image files
     */
    createPreviewURL(file: File): string | null {
      if (this.isImageFile(file)) {
        return URL.createObjectURL(file);
      }
      return null;
    },

    /**
     * Clean up preview URL to prevent memory leaks
     */
    revokePreviewURL(url: string): void {
      try {
        URL.revokeObjectURL(url);
      } catch (e) {
        // URL might already be revoked
        console.warn('Failed to revoke URL:', url)
      }
    },

    /**
     * Get human-friendly file type description
     */
    getFileTypeDescription(file: File): string {
      if (this.isImageFile(file)) {
        return 'Image';
      } else if (this.isPDFFile(file)) {
        return 'PDF Document';
      }
      return 'Document';
    },

    /**
     * Validate multiple files at once
     */
    validateMultipleFiles(files: File[]): { valid: File[], invalid: Array<{file: File, error: string}> } {
      const valid: File[] = [];
      const invalid: Array<{file: File, error: string}> = [];
      
      // Check total count
      if (files.length > 5) {
        files.slice(5).forEach(file => {
          invalid.push({ file, error: 'Maximum 5 files allowed per message' });
        });
        files = files.slice(0, 5);
      }
      
      files.forEach(file => {
        const validation = this.validateFileClientSide(file);
        if (validation.valid) {
          valid.push(file);
        } else {
          invalid.push({ file, error: validation.error || 'Invalid file' });
        }
      });
      
      return { valid, invalid };
    },

    /**
     * Debug conversation ID value
     */
    debugConversationId(conversationId: any): void {
      console.log('=== CONVERSATION ID DEBUG ===')
      console.log('Value:', conversationId)
      console.log('Type:', typeof conversationId)
      console.log('String value:', String(conversationId))
      console.log('JSON stringify:', JSON.stringify(conversationId))
      console.log('Truthy:', !!conversationId)
      console.log('Is undefined:', conversationId === undefined)
      console.log('Is null:', conversationId === null)
      console.log('Is empty string:', conversationId === '')
      console.log('Is "undefined" string:', conversationId === 'undefined')
      console.log('Is "null" string:', conversationId === 'null')
      console.log('Length (if string):', typeof conversationId === 'string' ? conversationId.length : 'N/A')
      console.log('Trimmed (if string):', typeof conversationId === 'string' ? `"${conversationId.trim()}"` : 'N/A')
      console.log('=== END DEBUG ===')
    }
  }
};

// Export constants for file handling
export const FILE_CONSTANTS = {
  MAX_FILE_SIZE_MB: 10,
  MAX_FILES_PER_MESSAGE: 5,
  SUPPORTED_TYPES: [
    'image/jpeg', 'image/jpg', 'image/png', 'image/gif',
    'image/webp', 'image/bmp', 'image/tiff',
    'application/pdf'
  ],
  SUPPORTED_EXTENSIONS: ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.tiff', '.pdf'],
  PROCESSING_TIMEOUT_MS: 120000 // 2 minutes
} as const;

export default fileService;