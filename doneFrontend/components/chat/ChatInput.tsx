// components/chat/ChatInput.tsx - Added placeholder prop support
'use client'
import { useState, useRef, useEffect } from 'react'
import { Send, Plus, Image, FileText, X, AlertCircle, ChevronDown } from 'lucide-react'
import { fileService, FILE_CONSTANTS } from '@/services/fileService'
import { chatService } from '@/services/chats' // Import chat service

// Import the SidebarBus to trigger auto-collapse
import { SidebarBus } from '@/components/layout/WorkspaceShell'

interface ChatInputProps {
  onSend: (text: string, context?: any) => Promise<void>;
  onSendWithFiles?: (message: string, files: File[], conversationId?: string) => Promise<void>;
  onFileProcessingComplete?: (conversationId: string) => Promise<void>; // New callback for file processing completion
  onNewMessage?: (response: any) => void; // Callback for new messages
  busy?: boolean;
  conversationId?: string;
  placeholder?: string; // Added placeholder prop
}

export default function ChatInput({
  onSend,
  onSendWithFiles,
  onFileProcessingComplete,
  onNewMessage,
  busy,
  conversationId,
  placeholder = "Reply to Olaji Chat..." // Default placeholder
}: ChatInputProps) {
  const [text, setText] = useState('')
  const [showAttachmentMenu, setShowAttachmentMenu] = useState(false)
  const [selectedFiles, setSelectedFiles] = useState<File[]>([])
  const [isProcessingFile, setIsProcessingFile] = useState(false)
  const [fileError, setFileError] = useState<string | null>(null)
  const [menuPosition, setMenuPosition] = useState({ top: 0, left: 0 })
  
  const inputRef = useRef<HTMLTextAreaElement>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)
  const menuRef = useRef<HTMLDivElement>(null)
  const attachButtonRef = useRef<HTMLButtonElement>(null)

  const send = async (messageText?: string, context?: any) => {
    const t = messageText || text.trim()
    
    // CRITICAL: Auto-collapse sidebar when user sends a message
    // This provides a more focused chat experience on desktop
    if (t) {
      SidebarBus.send({ type: 'auto-collapse' })
    }
    
    // FIXED: Handle file uploads with proper flow control
    if (selectedFiles.length > 0 && !isProcessingFile) {
      if (!t) {
        setFileError('Please enter a message to send with the file(s)')
        return
      }
      
      setIsProcessingFile(true)
      setFileError(null)
      
      try {
        console.log('=== FILE UPLOAD DEBUG ===')
        console.log('Message:', t)
        console.log('Files:', selectedFiles.length)
        console.log('ConversationId from props:', conversationId)
        console.log('onSendWithFiles exists:', !!onSendWithFiles)
        
        if (onSendWithFiles) {
          // OPTION 1: Use the provided handler (for existing chats)
          console.log('Using onSendWithFiles handler - existing chat flow')
          await onSendWithFiles(t, selectedFiles, conversationId)
        } else {
          // OPTION 2: Direct backend call (for new chats or landing page)
          console.log('Using chatService.sendMessageWithFiles - new chat flow')
          console.log('ConversationId being passed:', conversationId)
          
          const response = await chatService.sendMessageWithFiles(t, selectedFiles, conversationId)
          
          console.log('Chat service response:', {
            conversation_id: response.conversation_id,
            intent: response.intent,
            attachment_processed: response.attachment_processed
          })
          
          // CRITICAL FIX: For new chats, use the regular onSend with special context
          // This tells the parent that files were processed and a new conversation was created
          const fileProcessingContext = {
            type: 'file_processing_complete',
            conversation_id: response.conversation_id,
            attachment_processed: response.attachment_processed,
            files_count: selectedFiles.length,
            // Include the full response so parent can handle redirect/update
            backend_response: response
          }
          
          // Call the regular onSend handler with the file processing context
          // This allows the parent to handle the redirect to the new conversation
          await onSend(t, fileProcessingContext)
        }
        
        // Clear files and text on success
        setSelectedFiles([])
        setText('')
        
      } catch (error) {
        const errorMessage = error instanceof Error ? error.message : 'File processing failed'
        setFileError(errorMessage)
        console.error('File processing error:', error)
      } finally {
        setIsProcessingFile(false)
      }
      return
    }
    
    // Normal message sending (no files attached)
    if (!t || busy || isProcessingFile) return
    
    if (!messageText) {
      setText('')
    }
    
    try {
      await onSend(t, context)
    } catch (error) {
      console.error('Error in ChatInput:', error)
    }
    inputRef.current?.focus()
  }

  const onKey = async (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      await send()
    }
  }

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto'
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 120)}px`
    }
  }, [text])

  // Close menu when clicking outside
  useEffect(() => {
    const handleClickOutside = (event: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(event.target as Node) &&
          attachButtonRef.current && !attachButtonRef.current.contains(event.target as Node)) {
        setShowAttachmentMenu(false)
      }
    }

    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  const handleAttachmentClick = () => {
    if (!showAttachmentMenu && attachButtonRef.current) {
      const rect = attachButtonRef.current.getBoundingClientRect()
      const scrollY = window.scrollY
      const viewportWidth = window.innerWidth
      
      // Position menu based on available space
      let left = rect.left
      let top = rect.top + scrollY - 10
      
      // For mobile, center the menu horizontally if needed
      if (viewportWidth < 640) {
        left = Math.max(16, Math.min(viewportWidth - 216, rect.left)) // 200px menu width + 16px margin
        top = rect.top + scrollY - 80 // Give more space above on mobile
      }
      
      setMenuPosition({ top, left })
    }
    setShowAttachmentMenu(!showAttachmentMenu)
    setFileError(null)
  }

  const handleFileSelect = (acceptedTypes: string) => {
    if (fileInputRef.current) {
      fileInputRef.current.accept = acceptedTypes
      fileInputRef.current.click()
    }
    setShowAttachmentMenu(false)
  }

  const onFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files
    if (!files || files.length === 0) return

    // Convert FileList to Array
    const fileArray = Array.from(files)
    
    // Validate files using the updated file service
    const validation = fileService.utils.validateMultipleFiles([...selectedFiles, ...fileArray])
    
    if (validation.invalid.length > 0) {
      const errors = validation.invalid.map(item => `${item.file.name}: ${item.error}`)
      setFileError(errors.join(', '))
    } else {
      setFileError(null)
    }

    if (validation.valid.length > 0) {
      // Only add files that aren't already selected
      const newFiles = validation.valid.filter(newFile => 
        !selectedFiles.some(existingFile => 
          existingFile.name === newFile.name && existingFile.size === newFile.size
        )
      )
      
      if (newFiles.length > 0) {
        setSelectedFiles(prev => [...prev, ...newFiles])
      } else if (validation.invalid.length === 0) {
        setFileError('Some files are already selected')
      }
    }
    
    // Reset input
    if (fileInputRef.current) {
      fileInputRef.current.value = ''
    }
  }

  const removeFile = (index: number) => {
    // Clean up any object URLs for images to prevent memory leaks
    const file = selectedFiles[index]
    if (fileService.utils.isImageFile(file)) {
      // Note: We create URLs dynamically in the render, so cleanup happens there
    }
    
    setSelectedFiles(prev => prev.filter((_, i) => i !== index))
    setFileError(null)
  }

  const formatFileSize = (bytes: number): string => {
    return fileService.utils.formatFileSize(bytes)
  }

  const getFileIcon = (file: File) => {
    if (fileService.utils.isImageFile(file)) {
      return <Image size={12} className="text-white" />
    }
    return <FileText size={12} className="text-white" />
  }

  // Calculate if we can send (text + no processing state + not too busy)
  const canSend = (text.trim() || selectedFiles.length > 0) && !busy && !isProcessingFile
  const isAnyProcessing = busy || isProcessingFile

  // Dynamic placeholder based on state
  const getPlaceholder = () => {
    if (selectedFiles.length > 0) {
      return "Ask me about these files..."
    }
    if (isProcessingFile) {
      return "Processing files..."
    }
    return placeholder
  }

  return (
    <>
      <div className="pt-2 pb-3 bg-gradient-to-t from-neutral-100/60 via-neutral-50/20 to-transparent
                      dark:from-neutral-950/60 dark:via-neutral-950/20">
        <div className="mx-auto max-w-4xl px-4 sm:px-6">
          
          <div className="border border-neutral-300/60 bg-white/70
                          dark:border-neutral-700/60 dark:bg-neutral-900/70
                          rounded-2xl sm:rounded-3xl shadow-[var(--shadow-soft)] relative overflow-visible">
            
            {/* File Thumbnails - Mobile responsive grid */}
            {selectedFiles.length > 0 && (
              <div className="px-4 sm:px-6 pt-4 sm:pt-6 pb-2">
                <div className="flex flex-wrap gap-2">
                  {selectedFiles.map((file, index) => (
                    <div
                      key={`${file.name}-${file.size}-${index}`}
                      className="relative w-12 h-12 sm:w-16 sm:h-16"
                      title={`${file.name} (${formatFileSize(file.size)}) - ${fileService.utils.getFileTypeDescription(file)}`}
                    >
                      {/* Main thumbnail container */}
                      <div className="w-full h-full bg-neutral-200 dark:bg-neutral-700 rounded-lg sm:rounded-xl overflow-hidden
                                    border border-neutral-300 dark:border-neutral-600 group relative">
                        {/* File Preview */}
                        {fileService.utils.isImageFile(file) ? (
                          <img
                            src={URL.createObjectURL(file)}
                            alt={file.name}
                            className="w-full h-full object-cover"
                            onLoad={(e) => {
                              // Clean up object URL after image loads to prevent memory leaks
                              const img = e.target as HTMLImageElement;
                              setTimeout(() => {
                                try {
                                  URL.revokeObjectURL(img.src);
                                } catch (e) {
                                  // URL might already be revoked
                                }
                              }, 1000);
                            }}
                            onError={(e) => {
                              // Handle broken image
                              const img = e.target as HTMLImageElement;
                              img.style.display = 'none';
                            }}
                          />
                        ) : (
                          <div className="flex flex-col items-center justify-center w-full h-full bg-neutral-300 dark:bg-neutral-600 text-xs">
                            <FileText size={16} className="sm:w-5 sm:h-5 text-neutral-600 dark:text-neutral-300 mb-1" />
                            <span className="text-[9px] sm:text-[10px] text-neutral-500 dark:text-neutral-400 text-center px-1 leading-tight">
                              {fileService.utils.isPDFFile(file) ? 'PDF' : 'DOC'}
                            </span>
                          </div>
                        )}
                        
                        {/* Processing overlay */}
                        {isProcessingFile && (
                          <div className="absolute inset-0 bg-black/50 flex items-center justify-center">
                            <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin"></div>
                          </div>
                        )}
                        
                        {/* Remove Button - mobile friendly sizing */}
                        <button
                          onClick={(e) => {
                            e.stopPropagation()
                            removeFile(index)
                          }}
                          className="absolute -top-1 -right-1 sm:-top-2 sm:-right-2 w-5 h-5 sm:w-6 sm:h-6 bg-red-500 hover:bg-red-600 rounded-full 
                                   flex items-center justify-center opacity-100 sm:opacity-0 sm:group-hover:opacity-100
                                   transition-all duration-200 shadow-lg border-2 border-white
                                   z-20 touch-manipulation"
                          disabled={isProcessingFile}
                          aria-label={`Remove ${file.name}`}
                        >
                          <X size={10} className="sm:w-3.5 sm:h-3.5 text-white" />
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
                
                {/* File count indicator for multiple files */}
                {selectedFiles.length > 1 && (
                  <div className="text-xs text-neutral-500 dark:text-neutral-400 mt-1">
                    {selectedFiles.length} files selected ({selectedFiles.reduce((acc, file) => acc + file.size, 0) > 1024 * 1024 
                      ? formatFileSize(selectedFiles.reduce((acc, file) => acc + file.size, 0))
                      : formatFileSize(selectedFiles.reduce((acc, file) => acc + file.size, 0))
                    } total)
                  </div>
                )}
              </div>
            )}

            {/* Input Area - No gap between sections */}
            <div className="px-3 sm:px-4 py-2 sm:py-3">
              {/* Textarea - More space for typing */}
              <div>
                <textarea
                  ref={inputRef}
                  value={text}
                  onChange={e => setText(e.target.value)}
                  onKeyDown={onKey}
                  placeholder={getPlaceholder()}
                  aria-label="Chat message"
                  className="w-full bg-transparent outline-none resize-none
                             text-base sm:text-lg leading-relaxed
                             text-neutral-900 dark:text-neutral-100
                             placeholder:text-neutral-500 dark:placeholder:text-neutral-500
                             disabled:opacity-50 min-h-[36px] max-h-[120px] py-1 px-0"
                  disabled={isAnyProcessing}
                  maxLength={2000}
                  rows={1}
                />
              </div>

              {/* Controls Bar - Attachment button on left, Olaji Chat and send button on right */}
              <div className="flex items-center justify-between">
                {/* Left side - Attachment Button */}
                <div className="relative" ref={menuRef}>
                  <button
                    ref={attachButtonRef}
                    onClick={handleAttachmentClick}
                    className="flex items-center justify-center w-9 h-9 sm:w-10 sm:h-10
                               text-neutral-600 hover:text-neutral-800 
                               dark:text-neutral-400 dark:hover:text-neutral-200
                               transition-colors duration-200 touch-manipulation
                               disabled:opacity-50 disabled:cursor-not-allowed"
                    aria-label="Attach files"
                    disabled={isAnyProcessing}
                  >
                    <Plus size={18} />
                  </button>
                </div>

                {/* Hidden File Input */}
                <input
                  ref={fileInputRef}
                  type="file"
                  onChange={onFileChange}
                  className="hidden"
                  multiple
                  accept={FILE_CONSTANTS.SUPPORTED_TYPES.join(',')}
                />

                {/* Right side - Olaji Chat and Send Button */}
                <div className="flex items-center gap-3">
                  {/* Model Selector */}
                  <div className="flex items-center">
                    <span className="text-sm font-medium text-neutral-700 dark:text-neutral-300">
                      Olaji{' '}
                      <span style={{ color: 'var(--color-brand)' }}>Chat</span>
                    </span>
                  </div>
                  
                  {/* Send Button */}
                  <button
                    className="flex items-center justify-center w-10 h-10 sm:w-11 sm:h-11 rounded-full transition-all duration-200
                               disabled:opacity-50 disabled:cursor-not-allowed touch-manipulation
                               shadow-lg hover:shadow-xl"
                    style={{ 
                      backgroundColor: canSend ? 'var(--color-brand)' : 'var(--color-neutral-300)',
                      color: 'white'
                    }}
                    onMouseEnter={(e) => {
                      if (canSend) {
                        e.currentTarget.style.backgroundColor = 'var(--color-brand-dark)'
                      }
                    }}
                    onMouseLeave={(e) => {
                      if (canSend) {
                        e.currentTarget.style.backgroundColor = 'var(--color-brand)'
                      }
                    }}
                    onClick={() => send()}
                    disabled={!canSend}
                    aria-label={selectedFiles.length > 0 ? "Send message with files" : "Send message"}
                  >
                    {isAnyProcessing ? (
                      <div className="flex items-center justify-center">
                        <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                      </div>
                    ) : (
                      <Send size={18} className="sm:w-5 sm:h-5" />
                    )}
                  </button>
                </div>
              </div>
            </div>
          </div>
          
          {/* Error Display - Mobile responsive */}
          {fileError && (
            <div className="mt-3 text-sm bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
              <div className="flex items-start gap-3">
                <AlertCircle size={16} className="text-red-600 dark:text-red-400 mt-0.5 flex-shrink-0" />
                <div className="text-red-600 dark:text-red-400">
                  {fileError}
                </div>
              </div>
            </div>
          )}
          
          {/* Processing status */}
          {isProcessingFile && (
            <div className="mt-3 text-sm text-neutral-600 dark:text-neutral-400 bg-neutral-50 dark:bg-neutral-800 p-3 rounded text-center">
              <div className="flex items-center justify-center gap-2">
                <div className="w-4 h-4 border-2 border-current border-t-transparent rounded-full animate-spin"></div>
                Processing {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''}...
              </div>
            </div>
          )}
          
          {/* Character count - Hide on mobile when not needed */}
          {text.length > 1500 && (
            <div className="text-xs text-neutral-500 text-right mt-2 hidden sm:block">
              {text.length}/2000
            </div>
          )}
          
          {/* Help text for files */}
          {selectedFiles.length > 0 && !isProcessingFile && (
            <div className="mt-3 text-sm text-neutral-500 dark:text-neutral-400 text-center">
              I'll analyze your {selectedFiles.length} file{selectedFiles.length !== 1 ? 's' : ''} along with your message
            </div>
          )}
        </div>
      </div>

      {/* Attachment Menu - Mobile responsive positioning */}
      {showAttachmentMenu && (
        <div 
          className="fixed bg-white dark:bg-neutral-800 
                    border border-neutral-200 dark:border-neutral-700 rounded-lg shadow-xl 
                    min-w-[180px] sm:min-w-[200px] z-[999] py-2 transform -translate-y-full"
          style={{
            top: menuPosition.top,
            left: menuPosition.left,
          }}
          ref={menuRef}
        >
          <button
            onClick={() => handleFileSelect('image/*')}
            className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-neutral-700 
                     dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 
                     transition-colors text-left"
          >
            <Image size={16} className="text-neutral-500 dark:text-neutral-400" />
            <div className="flex-1">
              <div>Attach Images</div>
              <div className="text-xs text-neutral-500 dark:text-neutral-400">
                JPG, PNG, GIF, WebP, etc.
              </div>
            </div>
          </button>
          <button
            onClick={() => handleFileSelect('application/pdf')}
            className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-neutral-700 
                     dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 
                     transition-colors text-left"
          >
            <FileText size={16} className="text-neutral-500 dark:text-neutral-400" />
            <div className="flex-1">
              <div>Upload PDF</div>
              <div className="text-xs text-neutral-500 dark:text-neutral-400">
                PDF documents up to 10MB
              </div>
            </div>
          </button>
          <button
            onClick={() => handleFileSelect(FILE_CONSTANTS.SUPPORTED_TYPES.join(','))}
            className="flex items-center gap-3 w-full px-4 py-2.5 text-sm text-neutral-700 
                     dark:text-neutral-300 hover:bg-neutral-50 dark:hover:bg-neutral-700 
                     transition-colors text-left"
          >
            <div className="w-4 h-4 rounded bg-gradient-to-br from-blue-500 to-purple-500 flex items-center justify-center">
              <div className="w-2 h-2 bg-white rounded-sm"></div>
            </div>
            <div className="flex-1">
              <div>Any File Type</div>
              <div className="text-xs text-neutral-500 dark:text-neutral-400">
                Images, PDFs (max {FILE_CONSTANTS.MAX_FILE_SIZE_MB}MB each)
              </div>
            </div>
          </button>
        </div>
      )}
    </>
  )
}