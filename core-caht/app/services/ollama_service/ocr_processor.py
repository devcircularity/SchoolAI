# app/services/ollama_service/ocr_processor.py - OCR document interpretation methods

from typing import Dict, Any
from datetime import datetime
from .base import OllamaBaseService


class OllamaOCRProcessor(OllamaBaseService):
    """OCR document processing and interpretation functionality"""
    
    async def interpret_document(
        self, 
        ocr_data: Dict[str, Any], 
        user_message: str,
        file_metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Interpret OCR-extracted text based on user's question/context"""
        try:
            # Extract text from OCR results
            extracted_text = self._extract_text_from_ocr(ocr_data)
            
            # Build context-aware prompt
            prompt = self._build_interpretation_prompt(extracted_text, user_message, file_metadata)
            
            # Call Ollama API
            response = await self._call_ollama(prompt)
            
            return {
                "interpretation": response.get("response", ""),
                "model_used": self.model,
                "processed_at": datetime.utcnow().isoformat(),
                "extracted_text_length": len(extracted_text),
                "success": True
            }
            
        except Exception as e:
            print(f"Ollama interpretation error: {e}")
            return {
                "interpretation": f"I encountered an error while analyzing the document: {str(e)}",
                "model_used": self.model,
                "processed_at": datetime.utcnow().isoformat(),
                "success": False,
                "error": str(e)
            }
    
    def _extract_text_from_ocr(self, ocr_data: Dict[str, Any]) -> str:
        """Extract and clean text from OCR results based on your OCR service format"""
        try:
            print(f"Processing OCR data: {ocr_data}")
            
            # Handle the nested structure from your service
            if "ocr_data" in ocr_data:
                actual_ocr = ocr_data["ocr_data"]
            else:
                actual_ocr = ocr_data
            
            print(f"Actual OCR data: {actual_ocr}")
            
            # Based on your OCR service output format (OcrResult with pages list)
            if isinstance(actual_ocr, dict) and "pages" in actual_ocr:
                pages = actual_ocr["pages"]
                if isinstance(pages, list):
                    # Join all pages with double newlines
                    extracted_text = "\n\n".join([str(page).strip() for page in pages if page and str(page).strip()])
                    print(f"Extracted text from {len(pages)} pages: {len(extracted_text)} characters")
                else:
                    extracted_text = str(pages).strip()
            elif isinstance(actual_ocr, dict) and "text" in actual_ocr:
                # Alternative format
                extracted_text = str(actual_ocr["text"]).strip()
            elif isinstance(actual_ocr, str):
                # Direct text response
                extracted_text = actual_ocr.strip()
            else:
                # Fallback: convert entire response to string
                extracted_text = str(actual_ocr).strip()
            
            if not extracted_text:
                return "[No text could be extracted from the document - the image may be unclear, contain no text, or be in an unsupported format]"
            
            # Limit text length to avoid token limits (keep reasonable for LLM)
            if len(extracted_text) > 8000:
                extracted_text = extracted_text[:8000] + "\n\n[Text truncated due to length...]"
            
            return extracted_text
            
        except Exception as e:
            print(f"Error extracting text from OCR: {e}")
            return f"[Error extracting text from OCR results: {str(e)}]"
    
    def _build_interpretation_prompt(
        self, 
        extracted_text: str, 
        user_message: str,
        file_metadata: Dict[str, Any]
    ) -> str:
        """Build a comprehensive prompt for document interpretation"""
        
        document_type = self._detect_document_type(extracted_text, file_metadata)
        
        prompt = f"""You are an AI assistant specialized in document analysis and interpretation. A user has uploaded a document and asked: "{user_message}"

DOCUMENT INFORMATION:
- File type: {file_metadata.get('content_type', 'Unknown')}
- Original filename: {file_metadata.get('original_filename', 'Unknown')}
- Document type detected: {document_type}

EXTRACTED TEXT FROM DOCUMENT:
{extracted_text}

USER'S QUESTION: "{user_message}"

ANALYSIS INSTRUCTIONS:
1. ALWAYS start your response by showing the extracted text in a clearly marked section
2. Then analyze the extracted text and answer the user's specific question: "{user_message}"
3. If the user's question is general (like "hi", "hello", "analyze this"), provide a comprehensive summary of what the document contains
4. Focus on identifying key information such as:
   - Important numbers, dates, amounts, percentages
   - Names of people, organizations, places
   - Key terms, concepts, or topics
   - Action items, requirements, or instructions
   - Deadlines or time-sensitive information

RESPONSE FORMAT - ALWAYS USE THIS STRUCTURE:
**📄 EXTRACTED TEXT FROM DOCUMENT:**
```
[Show the exact extracted text here]
```

**🔍 ANALYSIS:**
[Your analysis and response to the user's question here]

RESPONSE GUIDELINES:
- Be direct and helpful in answering the user's question
- If analyzing a specific document type:
  * Invoice/Receipt: Focus on amounts, dates, vendor/customer info, line items
  * Form: Identify purpose, required fields, instructions
  * Academic document: Extract grades, assignments, dates, requirements  
  * Report: Main findings, conclusions, recommendations
  * General document: Main topics, key points, important details

- Reference specific information from the document text
- If the extracted text is unclear or seems corrupted, mention this limitation
- If no relevant text was extracted, explain this clearly but still show what was found
- Keep your response focused and informative

RESPONSE:"""

        return prompt
    
    def _detect_document_type(self, extracted_text: str, file_metadata: Dict[str, Any]) -> str:
        """Detect document type based on content and metadata"""
        try:
            filename = file_metadata.get('original_filename', '').lower()
            content_type = file_metadata.get('content_type', '')
            text_lower = extracted_text.lower()
            
            # Simple heuristic-based detection
            if any(word in filename for word in ['invoice', 'receipt', 'bill']):
                return "Invoice/Receipt"
            elif any(word in filename for word in ['form', 'application']):
                return "Form"
            elif any(word in filename for word in ['report', 'transcript', 'summary']):
                return "Report/Document"
            elif any(word in text_lower for word in ['total', 'amount', 'invoice', 'payment', '$', 'price', 'cost']):
                return "Financial Document"
            elif any(word in text_lower for word in ['grade', 'score', 'exam', 'assignment', 'course', 'student']):
                return "Academic Document"
            elif any(word in text_lower for word in ['agreement', 'contract', 'terms', 'conditions']):
                return "Legal Document"
            elif content_type.startswith('image/'):
                return "Image/Screenshot"
            elif content_type == 'application/pdf':
                return "PDF Document"
            else:
                return "Text Document"
                
        except Exception:
            return "Document"