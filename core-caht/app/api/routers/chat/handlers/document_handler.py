# app/api/routers/chat/handlers/document_handler.py - Fixed to not include file download in blocks

from typing import Optional, Dict, List
from sqlalchemy.orm import Session
from ..base import BaseHandler, ChatResponse
from ..blocks import text, action_panel, action_panel_item, query_action
from app.services.file_service import FileService
from app.services.ollama_service import OllamaService
import asyncio

class DocumentHandler(BaseHandler):
    """Handler for processing document attachments with OCR and AI interpretation"""
    
    def __init__(self, db: Session, school_id: str, user_id: str):
        super().__init__(db, school_id, user_id)
        self.file_service = FileService()
        self.ollama_service = OllamaService()
    
    def can_handle(self, message: str) -> bool:
        """This handler is invoked when attachments are present"""
        return False  # Don't auto-match, call directly
    
    async def handle_with_attachment(
        self, 
        message: str, 
        attachment_data: Dict,
        context: Optional[Dict] = None
    ) -> ChatResponse:
        """Handle message with file attachment - main entry point"""
        try:
            print(f"DocumentHandler processing message with attachment: {message}")
            print(f"Attachment data keys: {attachment_data.keys()}")
            
            # Validate that we have OCR results
            if 'ocr_result' not in attachment_data:
                return self._handle_processing_error("No OCR results found in attachment data", attachment_data)
            
            ocr_result = attachment_data['ocr_result']
            if not ocr_result.get('success'):
                return self._handle_processing_error("OCR processing was not successful", attachment_data)
            
            print(f"OCR result structure: {ocr_result}")
            
            # Step 1: Get AI interpretation from OCR-extracted text
            interpretation_result = await self.ollama_service.interpret_document(
                ocr_data=ocr_result,  # This contains the OCR-extracted text
                user_message=message,
                file_metadata=attachment_data['file_metadata']
            )
            
            if not interpretation_result['success']:
                return self._handle_interpretation_error(interpretation_result, attachment_data)
            
            # Step 2: Build comprehensive response
            return self._build_document_response(
                message=message,
                attachment_data=attachment_data,
                interpretation=interpretation_result['interpretation'],
                ocr_details=ocr_result
            )
            
        except Exception as e:
            print(f"DocumentHandler error: {e}")
            import traceback
            traceback.print_exc()
            return self._handle_processing_error(str(e), attachment_data)
    
    def handle(self, message: str, context: Optional[Dict] = None) -> ChatResponse:
        """Standard handle method - not used for attachments"""
        return ChatResponse(
            response="Document handler requires file attachments to process.",
            intent="document_handler_direct_call"
        )
    
    def _build_document_response(
        self,
        message: str,
        attachment_data: Dict,
        interpretation: str,
        ocr_details: Dict
    ) -> ChatResponse:
        """Build comprehensive response with document analysis"""
        
        file_metadata = attachment_data['file_metadata']
        
        # Build response text
        response_parts = [
            f"I've analyzed your document '{file_metadata['original_filename']}' and here's what I found:\n"
        ]
        
        response_parts.append(interpretation)
        
        # Add OCR processing details if helpful
        if ocr_details.get('processing_time'):
            response_parts.append(
                f"\n*Processing completed in {ocr_details['processing_time']:.2f} seconds*"
            )
        
        # Build blocks for rich display
        blocks = []
        
        # Document info block
        file_size_mb = file_metadata['bytes'] / (1024 * 1024)
        
        # Show OCR extraction info
        ocr_info_text = f"**📄 Document Information**\n\n"
        ocr_info_text += f"• **File:** {file_metadata['original_filename']}\n"
        ocr_info_text += f"• **Type:** {file_metadata['content_type']}\n"
        ocr_info_text += f"• **Size:** {file_size_mb:.2f} MB\n"
        ocr_info_text += f"• **Uploaded:** {attachment_data['processed_at'][:19]}\n"
        
        # Add OCR details
        if 'ocr_data' in ocr_details and ocr_details['ocr_data']:
            ocr_data = ocr_details['ocr_data']
            if isinstance(ocr_data, dict):
                if 'pages' in ocr_data:
                    page_count = len(ocr_data['pages']) if isinstance(ocr_data['pages'], list) else 1
                    ocr_info_text += f"• **Pages processed:** {page_count}\n"
                if 'language' in ocr_data:
                    ocr_info_text += f"• **OCR Language:** {ocr_data['language']}\n"
        
        blocks.append(text(ocr_info_text))
        
        # Main interpretation
        blocks.append(text(f"**🔍 Analysis Results**\n\n{interpretation}"))
        
        # Action panel for follow-up options
        actions = [
            action_panel_item(
                title="Ask Specific Question",
                description="Ask a specific question about this document",
                icon="help-circle",
                button_label="Ask Question",
                action_type="query",
                payload={"message": "I have a specific question about this document"},
                button_variant="primary"
            ),
            action_panel_item(
                title="Extract Key Data",
                description="Extract specific data points or information",
                icon="database",
                button_label="Extract Data",
                action_type="query",
                payload={"message": "Extract key data from this document"},
                button_variant="secondary"
            ),
            action_panel_item(
                title="Summarize Document",
                description="Get a concise summary of the main points",
                icon="file-text",
                button_label="Summarize",
                action_type="query",
                payload={"message": "Summarize the main points of this document"},
                button_variant="secondary"
            )
        ]
        
        if len(actions) > 0:
            blocks.append(action_panel(
                title="What would you like to do next?",
                items=actions,
                columns=1
            ))
        
        # REMOVED: Don't include file_download block here
        # The file will be shown with the user message instead
        # if file_metadata.get('secure_url'):
        #     blocks.append(file_download(
        #         file_name=file_metadata['original_filename'],
        #         endpoint=file_metadata['secure_url']
        #     ))
        
        return ChatResponse(
            response="\n".join(response_parts),
            intent="document_analysis",
            blocks=blocks,
            attachment_processed=True,
            data={
                "attachment_id": attachment_data.get('attachment_id'),
                "file_url": file_metadata['secure_url'],
                "ocr_success": ocr_details.get('success', False),
                "extracted_text_length": len(self._extract_text_preview(ocr_details))
            }
        )
    
    def _extract_text_preview(self, ocr_details: Dict) -> str:
        """Extract a preview of the OCR text for logging/debugging"""
        try:
            if 'ocr_data' in ocr_details and ocr_details['ocr_data']:
                ocr_data = ocr_details['ocr_data']
                if isinstance(ocr_data, dict) and 'pages' in ocr_data:
                    pages = ocr_data['pages']
                    if isinstance(pages, list) and pages:
                        return " ".join([str(page) for page in pages[:2]])  # First 2 pages
                    elif isinstance(pages, str):
                        return pages[:500]  # First 500 chars
            return ""
        except:
            return ""
    
    def _handle_interpretation_error(
        self, 
        interpretation_result: Dict, 
        attachment_data: Dict
    ) -> ChatResponse:
        """Handle AI interpretation errors"""
        
        file_metadata = attachment_data['file_metadata']
        error_msg = interpretation_result.get('error', 'Unknown error')
        
        # Try to show some OCR results even if AI failed
        ocr_preview = ""
        if 'ocr_result' in attachment_data and attachment_data['ocr_result'].get('success'):
            ocr_preview = self._extract_text_preview(attachment_data['ocr_result'])
            if ocr_preview:
                ocr_preview = f"\n\n**Extracted text preview:**\n{ocr_preview[:300]}..."
        
        blocks = [
            text(f"I successfully extracted text from your document '{file_metadata['original_filename']}' using OCR, but encountered an issue during AI analysis:\n\n"
                 f"**Error:** {error_msg}{ocr_preview}\n\n"
                 f"You can still download the original file or ask me to try processing it again."),
        ]
        
        # REMOVED: Don't provide download option in blocks - files show with user message
        # if file_metadata.get('secure_url'):
        #     blocks.append(file_download(
        #         file_name=file_metadata['original_filename'],
        #         endpoint=file_metadata['secure_url']
        #     ))
        
        return ChatResponse(
            response=f"I extracted text from your document but encountered an AI analysis error: {error_msg}",
            intent="document_analysis_error",
            blocks=blocks,
            attachment_processed=False,
            data={
                "attachment_id": attachment_data.get('attachment_id'),
                "file_url": file_metadata['secure_url'],
                "error": error_msg,
                "ocr_preview": ocr_preview
            }
        )
    
    def _handle_processing_error(self, error_message: str, attachment_data: Dict = None) -> ChatResponse:
        """Handle general processing errors"""
        
        blocks = [
            text(f"I encountered an error while processing your document:\n\n"
                 f"**Error:** {error_message}\n\n"
                 f"Please try uploading the file again or contact support if the issue persists.")
        ]
        
        # REMOVED: Don't show download link in blocks - files show with user message
        # if attachment_data and 'file_metadata' in attachment_data:
        #     file_metadata = attachment_data['file_metadata']
        #     if file_metadata.get('secure_url'):
        #         blocks.append(file_download(
        #             file_name=file_metadata.get('original_filename', 'document'),
        #             endpoint=file_metadata['secure_url']
        #         ))
        
        return ChatResponse(
            response=f"Document processing failed: {error_message}",
            intent="document_processing_error", 
            blocks=blocks,
            attachment_processed=False,
            data={"error": error_message}
        )