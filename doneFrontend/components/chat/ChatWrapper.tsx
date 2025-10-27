// components/chat/ChatWrapper.tsx - Wrapper to integrate file functionality
'use client'
import { useState, useCallback } from 'react'
import { fileService } from '@/services/fileService'
import ChatInput from './ChatInput'

interface ChatWrapperProps {
  onSendMessage: (text: string, context?: any) => Promise<void>;
  busy?: boolean;
  conversationId?: string;
  className?: string;
}

/**
 * This wrapper component handles the integration between your existing chat system
 * and the new file attachment functionality. It manages the dual sending modes:
 * 1. Regular text messages (existing flow)
 * 2. Messages with file attachments (new flow)
 */
export default function ChatWrapper({ 
  onSendMessage, 
  busy, 
  conversationId,
  className 
}: ChatWrapperProps) {
  const [fileProcessingError, setFileProcessingError] = useState<string | null>(null)

  /**
   * Handle sending messages with file attachments
   * This function processes files through the backend and then calls your existing onSendMessage
   */
  const handleSendWithFiles = useCallback(async (
    message: string, 
    files: File[], 
    currentConversationId?: string
  ) => {
    try {
      setFileProcessingError(null)
      
      // CRITICAL FIX: Do NOT call onSendMessage here with the AI response
      // The backend handles both storing the user message AND the AI response
      // We just need to trigger a refresh of the conversation
      
      // Use the file service to send message with files to the backend
      const response = await fileService.sendChatMessageWithFiles(
        message, 
        files, 
        currentConversationId || conversationId
      )
      
      // The backend has already stored:
      // 1. User message with attachments (MessageType.USER)
      // 2. AI response with analysis (MessageType.ASSISTANT)
      
      // Create a simple context to indicate files were processed
      const fileContext = {
        type: 'file_attachment_completed',
        files_count: files.length,
        conversation_id: response.conversation_id,
        attachment_processed: response.attachment_processed
      }
      
      // Call onSendMessage with a simple completion message
      // This should trigger your chat component to refresh/reload the conversation
      await onSendMessage(`Files processed successfully`, fileContext)
      
    } catch (error) {
      const errorMessage = error instanceof Error ? error.message : 'File processing failed'
      setFileProcessingError(errorMessage)
      
      // Call onSendMessage with error context
      const errorContext = {
        type: 'file_processing_error',
        error: errorMessage,
        files_attempted: files.map(f => f.name)
      }
      
      await onSendMessage(`Error processing files: ${errorMessage}`, errorContext)
    }
  }, [onSendMessage, conversationId])

  /**
   * Handle regular text messages (your existing flow)
   */
  const handleRegularSend = useCallback(async (text: string, context?: any) => {
    setFileProcessingError(null)
    await onSendMessage(text, context)
  }, [onSendMessage])

  return (
    <div className={className}>
      {/* Display file processing errors if any */}
      {fileProcessingError && (
        <div className="mb-4 p-3 bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg">
          <div className="text-sm text-red-600 dark:text-red-400">
            <div className="font-medium">File Processing Error</div>
            <div className="mt-1">{fileProcessingError}</div>
          </div>
        </div>
      )}
      
      <ChatInput
        onSend={handleRegularSend}
        onSendWithFiles={handleSendWithFiles}
        busy={busy}
        conversationId={conversationId}
      />
    </div>
  )
}