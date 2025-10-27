// components/chat/ChatMessages.tsx - Enhanced with rating preload functionality
import React, { useEffect, useRef, useState } from 'react';
import ReactMarkdown from 'react-markdown';
import ChatBlockRenderer from './tools/ChatBlockRenderer';
import { Block, Action } from './tools/types';
import { Image, FileText, Download, ExternalLink, ThumbsUp, ThumbsDown } from 'lucide-react';
import { chatRatingService } from '@/services/chatRating';

interface FileAttachment {
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

interface ChatMessage {
  id?: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp?: string;
  blocks?: Block[];
  intent?: string;
  response_data?: {
    blocks?: Block[];
    attachments?: FileAttachment[];
    [key: string]: any;
  };
}

interface ChatMessagesProps {
  messages: ChatMessage[];
  isLoading?: boolean;
  onAction?: (action: Action) => void;
}

// Component for rating buttons
const MessageRating: React.FC<{ 
  messageId: string;
  initialRating?: number | null;
  onRatingChange?: (rating: number) => void;
  preloadedRating?: number | null; // New prop for preloaded rating
}> = ({ messageId, initialRating, onRatingChange, preloadedRating }) => {
  // Use preloaded rating if available, otherwise use initial rating
  const [rating, setRating] = useState<number | null>(preloadedRating ?? initialRating ?? null);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Update rating when preloadedRating changes
  useEffect(() => {
    if (preloadedRating !== undefined) {
      setRating(preloadedRating);
    }
  }, [preloadedRating]);

  const handleRate = async (newRating: 1 | -1) => {
    // Don't allow re-rating with the same value
    if (rating === newRating) return;
    
    setIsSubmitting(true);
    setError(null);

    try {
      await chatRatingService.rateMessage(messageId, newRating);
      setRating(newRating);
      onRatingChange?.(newRating);
    } catch (error: any) {
      console.error('Failed to rate message:', error);
      setError('Failed to submit rating');
      
      // Reset rating on error
      setTimeout(() => {
        setError(null);
      }, 3000);
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div className="flex items-center gap-2 mt-3">
      <div className="flex items-center gap-1">
        {/* Thumbs Up */}
        <button
          onClick={() => handleRate(1)}
          disabled={isSubmitting}
          className={`p-2 rounded-lg transition-all duration-200 disabled:opacity-50 ${
            rating === 1
              ? 'bg-green-100 text-green-600 dark:bg-green-900/30 dark:text-green-400'
              : 'hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-500 hover:text-green-600 dark:text-neutral-400 dark:hover:text-green-400'
          }`}
          title={rating === 1 ? 'You liked this response' : 'Rate this response positively'}
        >
          <ThumbsUp size={14} className={rating === 1 ? 'fill-current' : ''} />
        </button>

        {/* Thumbs Down */}
        <button
          onClick={() => handleRate(-1)}
          disabled={isSubmitting}
          className={`p-2 rounded-lg transition-all duration-200 disabled:opacity-50 ${
            rating === -1
              ? 'bg-red-100 text-red-600 dark:bg-red-900/30 dark:text-red-400'
              : 'hover:bg-neutral-100 dark:hover:bg-neutral-800 text-neutral-500 hover:text-red-600 dark:text-neutral-400 dark:hover:text-red-400'
          }`}
          title={rating === -1 ? 'You disliked this response' : 'Rate this response negatively'}
        >
          <ThumbsDown size={14} className={rating === -1 ? 'fill-current' : ''} />
        </button>
      </div>

      {/* Loading indicator */}
      {isSubmitting && (
        <div className="flex items-center gap-1">
          <div className="w-3 h-3 border border-neutral-300 border-t-transparent rounded-full animate-spin"></div>
          <span className="text-xs text-neutral-500">Rating...</span>
        </div>
      )}

      {/* Error message */}
      {error && (
        <span className="text-xs text-red-500">{error}</span>
      )}

      {/* Success feedback */}
      {rating !== null && !isSubmitting && !error && (
        <span className="text-xs text-neutral-500">
          {rating === 1 ? 'Thanks for the feedback!' : 'Feedback received'}
        </span>
      )}
    </div>
  );
};

const ChatMessages: React.FC<ChatMessagesProps> = ({ 
  messages, 
  isLoading = false, 
  onAction 
}) => {
  const scrollContainerRef = useRef<HTMLDivElement>(null);
  const messagesContainerRef = useRef<HTMLDivElement>(null);
  const [isInitialLoad, setIsInitialLoad] = useState(true);
  const [lastUserMessageIndex, setLastUserMessageIndex] = useState<number | null>(null);
  const previousMessageCount = useRef(messages.length);
  
  // Track ratings for messages (both local and preloaded)
  const [messageRatings, setMessageRatings] = useState<Record<string, number>>({});
  const [preloadedRatings, setPreloadedRatings] = useState<Record<string, number>>({});
  const [isLoadingRatings, setIsLoadingRatings] = useState(false);

  // Preload ratings for all assistant messages when messages change
  useEffect(() => {
    const assistantMessageIds = messages
      .filter(msg => msg.role === 'assistant' && msg.id)
      .map(msg => msg.id!);
    
    if (assistantMessageIds.length > 0) {
      const loadRatings = async () => {
        setIsLoadingRatings(true);
        try {
          // Assuming your chatRatingService has a method to get multiple ratings
          const ratings = await chatRatingService.preloadRatings(assistantMessageIds);
          setPreloadedRatings(ratings);
        } catch (error) {
          console.error('Failed to preload ratings:', error);
          // Continue without preloaded ratings
        } finally {
          setIsLoadingRatings(false);
        }
      };
      
      loadRatings();
    }
  }, [messages]);

  // Track when we get new messages
  useEffect(() => {
    const currentMessageCount = messages.length;
    
    // Initial load - scroll to bottom
    if (isInitialLoad && currentMessageCount > 0) {
      setTimeout(() => {
        scrollToBottom();
        setIsInitialLoad(false);
      }, 100);
    }
    // New messages added
    else if (currentMessageCount > previousMessageCount.current && !isInitialLoad) {
      const lastMessage = messages[messages.length - 1];
      
      if (lastMessage?.role === 'user') {
        // User just sent a message - prepare to position it at top when assistant responds
        setLastUserMessageIndex(messages.length - 1);
        scrollToBottom(); // For now, scroll to bottom for user message
      } else if (lastMessage?.role === 'assistant' && lastUserMessageIndex !== null) {
        // Assistant just responded - position the user's question at the top
        setTimeout(() => {
          scrollToUserMessage(lastUserMessageIndex);
          setLastUserMessageIndex(null);
        }, 150);
      }
    }
    
    previousMessageCount.current = currentMessageCount;
  }, [messages.length, isInitialLoad, lastUserMessageIndex]);

  const scrollToBottom = () => {
    const container = scrollContainerRef.current;
    if (container) {
      container.scrollTo({
        top: container.scrollHeight,
        behavior: 'smooth'
      });
    }
  };

  const scrollToUserMessage = (userMessageIndex: number) => {
    const container = scrollContainerRef.current;
    const messagesContainer = messagesContainerRef.current;
    
    if (!container || !messagesContainer) return;
    
    // Find the user message element
    const userMessageElement = messagesContainer.querySelector(
      `[data-message-index="${userMessageIndex}"]`
    ) as HTMLElement;
    
    if (userMessageElement) {
      // Find the actual header element to get its real height
      const header = document.querySelector('header');
      const headerHeight = header ? header.getBoundingClientRect().height : 60;
      
      // Add some breathing room below the header
      const paddingBelowHeader = 16;
      const totalOffset = headerHeight + paddingBelowHeader;
      
      // Get the absolute position of the user message
      const userMessageRect = userMessageElement.getBoundingClientRect();
      const containerRect = container.getBoundingClientRect();
      
      // Calculate how much we need to scroll to position the user message below the header
      const currentScrollTop = container.scrollTop;
      const messageTopRelativeToContainer = userMessageRect.top - containerRect.top;
      const targetScrollTop = currentScrollTop + messageTopRelativeToContainer - totalOffset;
      
      container.scrollTo({
        top: Math.max(0, targetScrollTop),
        behavior: 'smooth'
      });
    }
  };

  const handleBlockAction = async (action: Action) => {
    console.log('Block action triggered:', action);
    
    if (onAction) {
      await onAction(action);
      return;
    }

    // Default action handling if no onAction prop provided
    switch (action.type) {
      case 'query':
        console.log('Query action:', action.payload);
        break;
        
      case 'route':
        if (action.target) {
          window.location.href = action.target;
        }
        break;
        
      case 'download':
        if (action.endpoint) {
          const link = document.createElement('a');
          link.href = action.endpoint;
          if (action.payload?.filename) {
            link.download = action.payload.filename;
          }
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
        }
        break;
        
      case 'mutation':
        if (action.endpoint) {
          try {
            const response = await fetch(action.endpoint, {
              method: action.method || 'POST',
              headers: {
                'Content-Type': 'application/json',
                'Authorization': `Bearer ${localStorage.getItem('token')}`,
                'X-School-ID': localStorage.getItem('schoolId') || ''
              },
              body: action.payload ? JSON.stringify(action.payload) : undefined
            });
            
            if (!response.ok) {
              throw new Error(`HTTP ${response.status}`);
            }
            
            console.log('Mutation successful');
          } catch (error) {
            console.error('Mutation failed:', error);
          }
        }
        break;
        
      default:
        console.warn('Unhandled action type:', action.type);
    }
  };

  // Handle rating change
  const handleRatingChange = (messageId: string, rating: number) => {
    setMessageRatings(prev => ({
      ...prev,
      [messageId]: rating
    }));
  };

  // Helper functions for file attachments
  const formatFileSize = (bytes: number): string => {
    if (bytes === 0) return '0 B';
    const k = 1024;
    const sizes = ['B', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + ' ' + sizes[i];
  };

  const isImageFile = (contentType: string): boolean => {
    return contentType.startsWith('image/');
  };

  const getFileIcon = (contentType: string) => {
    if (isImageFile(contentType)) {
      return <Image size={16} className="text-blue-500" />;
    }
    return <FileText size={16} className="text-gray-500" />;
  };

  // Component to render file attachments
  const FileAttachments: React.FC<{ attachments: FileAttachment[] }> = ({ attachments }) => {
    const [previewImage, setPreviewImage] = useState<string | null>(null);
    
    if (!attachments || attachments.length === 0) {
      return null;
    }

    const openImagePreview = (imageUrl: string) => {
      setPreviewImage(imageUrl);
    };

    const closeImagePreview = () => {
      setPreviewImage(null);
    };

    return (
      <>
        {/* RIGHT-ALIGNED file attachments grid */}
        <div className="flex flex-wrap gap-2 justify-end">
          {attachments.map((attachment, index) => (
            <div
              key={attachment.attachment_id || index}
              className="relative group cursor-pointer"
              onClick={() => {
                if (isImageFile(attachment.content_type)) {
                  openImagePreview(attachment.cloudinary_url);
                } else {
                  window.open(attachment.cloudinary_url, '_blank');
                }
              }}
            >
              {isImageFile(attachment.content_type) ? (
                // Image preview - FIXED: Responsive sizing that won't cause horizontal scroll
                <div className="w-32 h-24 xs:w-40 xs:h-28 sm:w-48 sm:h-32 md:w-56 md:h-36 lg:w-64 lg:h-40 rounded-lg overflow-hidden border border-neutral-300 dark:border-neutral-600 hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors">
                  <img
                    src={attachment.cloudinary_url}
                    alt={attachment.original_filename}
                    className="w-full h-full object-cover"
                  />
                </div>
              ) : (
                // Non-image file preview - FIXED: Responsive sizing
                <div className="w-24 h-24 xs:w-28 xs:h-28 sm:w-32 sm:h-32 md:w-36 md:h-36 lg:w-40 lg:h-40 rounded-lg bg-neutral-100 dark:bg-neutral-800 border border-neutral-300 dark:border-neutral-600 hover:border-neutral-400 dark:hover:border-neutral-500 transition-colors flex flex-col items-center justify-center">
                  <FileText size={24} className="xs:w-6 xs:h-6 sm:w-8 sm:h-8 text-neutral-500 dark:text-neutral-400 mb-2" />
                  <span className="text-xs text-neutral-600 dark:text-neutral-400 font-medium">
                    {attachment.content_type === 'application/pdf' ? 'PDF' : 'DOC'}
                  </span>
                </div>
              )}
              
              {/* Hover overlay with actions */}
              <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-30 transition-all duration-200 rounded-lg flex items-center justify-center opacity-0 group-hover:opacity-100">
                <div className="flex gap-1 xs:gap-2">
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      if (isImageFile(attachment.content_type)) {
                        openImagePreview(attachment.cloudinary_url);
                      } else {
                        window.open(attachment.cloudinary_url, '_blank');
                      }
                    }}
                    className="p-1.5 xs:p-2 bg-white dark:bg-neutral-800 rounded-full shadow-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
                    title="View"
                  >
                    <ExternalLink size={12} className="xs:w-3.5 xs:h-3.5 text-neutral-700 dark:text-neutral-300" />
                  </button>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      const link = document.createElement('a');
                      link.href = attachment.cloudinary_url;
                      link.download = attachment.original_filename;
                      document.body.appendChild(link);
                      link.click();
                      document.body.removeChild(link);
                    }}
                    className="p-1.5 xs:p-2 bg-white dark:bg-neutral-800 rounded-full shadow-lg hover:bg-neutral-50 dark:hover:bg-neutral-700 transition-colors"
                    title="Download"
                  >
                    <Download size={12} className="xs:w-3.5 xs:h-3.5 text-neutral-700 dark:text-neutral-300" />
                  </button>
                </div>
              </div>

              {/* OCR indicator */}
              {attachment.ocr_processed && (
                <div className="absolute top-1 right-1 xs:top-2 xs:right-2 w-1.5 h-1.5 xs:w-2 xs:h-2 bg-green-500 rounded-full shadow-sm" title="OCR Processed"></div>
              )}
            </div>
          ))}
        </div>

        {/* Image Preview Modal */}
        {previewImage && (
          <div 
            className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4"
            onClick={closeImagePreview}
          >
            <div className="relative max-w-full max-h-full w-full h-full flex items-center justify-center">
              <img
                src={previewImage}
                alt="Preview"
                className="max-w-full max-h-full object-contain rounded-lg"
                onClick={(e) => e.stopPropagation()}
              />
              <button
                onClick={closeImagePreview}
                className="absolute top-4 right-4 w-10 h-10 bg-black bg-opacity-50 hover:bg-opacity-75 text-white rounded-full flex items-center justify-center transition-colors"
                title="Close"
              >
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                  <line x1="18" y1="6" x2="6" y2="18"></line>
                  <line x1="6" y1="6" x2="18" y2="18"></line>
                </svg>
              </button>
            </div>
          </div>
        )}
      </>
    );
  };

  const renderMessage = (message: ChatMessage, index: number) => {
    const isUser = message.role === 'user';

    // DEBUG LOGGING - Add this to understand what data is available
    if (message.response_data?.attachments || (message as any).attachments) {
      console.log('=== MESSAGE WITH ATTACHMENTS DEBUG ===');
      console.log('Message role:', message.role);
      console.log('Message content:', message.content);
      console.log('response_data:', message.response_data);
      console.log('response_data.attachments:', message.response_data?.attachments);
      console.log('Direct attachments:', (message as any).attachments);
      console.log('isUser:', isUser);
      console.log('Will show attachments:', isUser && message.response_data?.attachments);
      console.log('=====================================');
    }

    // Determine which blocks to render (only for assistant messages)
    let blocksToRender: Block[] = [];
    if (!isUser) {
      if (message.blocks && message.blocks.length > 0) {
        blocksToRender = message.blocks;
      } else if (message.response_data?.blocks && message.response_data.blocks.length > 0) {
        blocksToRender = message.response_data.blocks;
      }
    }

    // Get attachments - Try multiple possible locations
    let attachments: FileAttachment[] | null = null;
    if (isUser) {
      // Primary location: response_data.attachments
      if (message.response_data?.attachments) {
        attachments = message.response_data.attachments;
      }
      // Fallback: direct attachments property
      else if ((message as any).attachments) {
        attachments = (message as any).attachments;
      }
    }

    // Additional debug for attachments found
    if (attachments) {
      console.log('Found attachments for display:', attachments.length, attachments);
    }

    const messageKey = message.id || `${message.role}-${index}`;

    return (
      <div 
        key={messageKey} 
        className={`mb-6 xs:mb-8 ${isUser ? 'flex justify-end' : ''}`}
        data-message-index={index}
      >
        <div className={`w-full ${isUser ? 'max-w-full xs:max-w-md sm:max-w-lg md:max-w-xl lg:max-w-2xl' : 'max-w-full'}`}>
          
          {isUser ? (
            // User message - FIXED: Responsive sizing and proper containment with right-aligned attachments
            <div className="space-y-3 w-full">
              {/* User message and attachments container - RIGHT ALIGNED */}
              <div className="flex flex-col items-end space-y-3 w-full">
                {/* File attachments ABOVE the message - RIGHT ALIGNED */}
                {attachments && attachments.length > 0 && (
                  <div className="flex justify-end w-full">
                    <div className="max-w-full overflow-hidden">
                      <div className="flex justify-end">
                        <FileAttachments attachments={attachments} />
                      </div>
                    </div>
                  </div>
                )}
                
                {/* User message bubble - FIXED: Proper responsive sizing */}
                <div className="inline-block rounded-2xl px-3 xs:px-4 py-2 xs:py-3 text-white max-w-full break-words" 
                     style={{ backgroundColor: 'var(--color-brand)' }}>
                  <div className="text-sm xs:text-[15px] leading-relaxed">
                    {message.content}
                  </div>
                </div>
              </div>
            </div>
          ) : (
            // Assistant message - FIXED: Better mobile containment
            <div className="space-y-3 xs:space-y-4 w-full">
              
              {/* Text content */}
              {message.content && (
                <div className="prose prose-sm max-w-none text-neutral-900 dark:text-neutral-100 break-words">
                  <ReactMarkdown
                    components={{
                      h1: ({children}) => <h1 className="text-lg xs:text-xl font-semibold mb-2 xs:mb-3 text-neutral-900 dark:text-neutral-100">{children}</h1>,
                      h2: ({children}) => <h2 className="text-base xs:text-lg font-semibold mb-2 text-neutral-900 dark:text-neutral-100">{children}</h2>,
                      h3: ({children}) => <h3 className="text-sm xs:text-base font-semibold mb-2 text-neutral-900 dark:text-neutral-100">{children}</h3>,
                      p: ({children}) => <p className="mb-2 leading-relaxed text-neutral-900 dark:text-neutral-100 break-words">{children}</p>,
                      strong: ({children}) => <strong className="font-semibold text-neutral-900 dark:text-neutral-100">{children}</strong>,
                      em: ({children}) => <em className="italic text-neutral-900 dark:text-neutral-100">{children}</em>,
                      code: ({children}) => (
                        <code className="bg-neutral-100 dark:bg-neutral-800 px-1 py-0.5 rounded text-xs xs:text-sm font-mono text-neutral-900 dark:text-neutral-100 break-all">
                          {children}
                        </code>
                      ),
                      ul: ({children}) => <ul className="list-disc list-inside mb-2 space-y-1 text-neutral-900 dark:text-neutral-100 break-words">{children}</ul>,
                      ol: ({children}) => <ol className="list-decimal list-inside mb-2 space-y-1 text-neutral-900 dark:text-neutral-100 break-words">{children}</ol>,
                      li: ({children}) => <li className="leading-relaxed text-neutral-900 dark:text-neutral-100 break-words">{children}</li>,
                    }}
                  >
                    {message.content}
                  </ReactMarkdown>
                </div>
              )}
              
              {/* Rich blocks */}
              {blocksToRender.length > 0 && (
                <div className="space-y-3 xs:space-y-4 w-full overflow-hidden">
                  <ChatBlockRenderer 
                    blocks={blocksToRender} 
                    onAction={handleBlockAction}
                  />
                </div>
              )}

              {/* Rating buttons - Only for assistant messages with IDs */}
              {!isUser && message.id && (
                <MessageRating
                  messageId={message.id}
                  initialRating={messageRatings[message.id] || null}
                  preloadedRating={preloadedRatings[message.id] || null}
                  onRatingChange={(rating) => handleRatingChange(message.id!, rating)}
                />
              )}
            </div>
          )}
          
          {/* Intent display */}
          {message.intent && !isUser && (
            <div className="text-xs text-neutral-400 mt-2 text-left break-words">
              • {message.intent}
            </div>
          )}
        </div>
      </div>
    );
  };

  return (
    <div 
      ref={scrollContainerRef}
      className="flex-1 overflow-y-auto overflow-x-hidden h-full"
      style={{ 
        // CRITICAL: Ensure proper height calculation
        height: '100%',
        maxHeight: '100%'
      }}
    >
      <div 
        ref={messagesContainerRef}
        className="min-h-full px-3 xs:px-4 sm:px-6 pt-4 pb-6 xs:pb-8 w-full"
      >
        <div className="max-w-4xl mx-auto w-full">
          {messages.map(renderMessage)}
          
          {/* Loading indicator */}
          {isLoading && (
            <div className="mb-4 xs:mb-6">
              <div className="max-w-4xl w-full">
                <div className="flex items-center space-x-2 text-neutral-500">
                  <div className="flex space-x-1">
                    <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce"></div>
                    <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{animationDelay: '0.1s'}}></div>
                    <div className="w-2 h-2 bg-neutral-400 rounded-full animate-bounce" style={{animationDelay: '0.2s'}}></div>
                  </div>
                  <span className="text-xs xs:text-sm">AI is thinking...</span>
                </div>
              </div>
            </div>
          )}

          {/* Rating loading indicator */}
          {isLoadingRatings && (
            <div className="mb-4 xs:mb-6">
              <div className="flex items-center space-x-2 text-neutral-400">
                <div className="w-2 h-2 bg-neutral-300 rounded-full animate-pulse"></div>
                <span className="text-xs">Loading ratings...</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default ChatMessages;