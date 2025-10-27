# app/services/ollama_service.py - Complete enhanced service with improved regex generation

import os
import requests
import json
import re
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import asyncio
import aiohttp
import concurrent.futures


class OllamaService:
    """Enhanced service for processing OCR-extracted text, general queries, and intelligent regex generation with Ollama AI models"""
    
    def __init__(self):
        self.base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
        self.model = os.getenv("OLLAMA_MODEL", "llama3.2:latest")
        self.timeout = 120  # 2 minutes timeout for AI processing
    
    # === SYNCHRONOUS WRAPPER METHODS ===
    
    def generate_response_sync(self, prompt: str) -> Dict[str, Any]:
        """Synchronous wrapper for async Ollama calls - used for fallback queries"""
        try:
            # Try to get existing event loop
            try:
                loop = asyncio.get_running_loop()
                print("Found running event loop, using executor")
                
                # Running loop exists, use thread executor to avoid blocking
                with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                    # Create a new event loop in the thread
                    future = executor.submit(self._run_async_in_thread, prompt)
                    result = future.result(timeout=self.timeout)
                    return result
                    
            except RuntimeError:
                # No running loop, create new one
                print("No running event loop, creating new one")
                return asyncio.run(self._call_ollama(prompt))
                
        except concurrent.futures.TimeoutError:
            return {
                "response": "I apologize, but the request took too long to process. Please try asking something else or rephrase your question.",
                "success": False,
                "error": "Request timeout"
            }
        except Exception as e:
            print(f"Sync Ollama call error: {e}")
            return {
                "response": "I encountered an error while processing your request. Could you try rephrasing your question?",
                "success": False,
                "error": str(e)
            }
    
    def _run_async_in_thread(self, prompt: str) -> Dict[str, Any]:
        """Helper to run async code in a separate thread with its own event loop"""
        try:
            return asyncio.run(self._call_ollama(prompt))
        except Exception as e:
            print(f"Async in thread error: {e}")
            return {
                "response": f"I encountered an error processing your request: {str(e)}",
                "success": False,
                "error": str(e)
            }
    
    # === OCR DOCUMENT INTERPRETATION ===
    
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
    
    # === ENHANCED REGEX GENERATION METHODS ===
    
    async def generate_regex_from_phrases(
        self, 
        phrases: List[str], 
        intent: str,
        pattern_kind: str = "positive"
    ) -> Dict[str, Any]:
        """
        Generate intelligent regex pattern from natural language phrases using Ollama
        
        Args:
            phrases: List of example phrases that should match
            intent: The intent these phrases represent (for context)
            pattern_kind: positive, negative, or synonym
        
        Returns:
            Dict with regex, confidence, explanation, and validation results
        """
        if not phrases:
            return {
                "regex": "",
                "confidence": 0.0,
                "explanation": "No phrases provided",
                "test_matches": [],
                "errors": ["No input phrases provided"]
            }
        
        # Clean and validate input phrases
        cleaned_phrases = [phrase.strip() for phrase in phrases if phrase.strip()]
        if not cleaned_phrases:
            return {
                "regex": "",
                "confidence": 0.0,
                "explanation": "No valid phrases provided after cleaning",
                "test_matches": [],
                "errors": ["All phrases were empty or whitespace"]
            }
        
        try:
            # Analyze phrases for better context
            phrase_analysis = self._analyze_phrases(cleaned_phrases)
            
            # Build the enhanced prompt for regex generation
            prompt = self._build_enhanced_regex_prompt(cleaned_phrases, intent, pattern_kind, phrase_analysis)
            
            # Generate regex using Ollama
            response = await self._call_ollama(prompt)
            
            # Parse the response to extract regex
            result = self._parse_regex_response(response.get("response", ""), cleaned_phrases)
            
            # Enhance the regex for better flexibility if needed
            if result["regex"]:
                enhanced_regex = self._enhance_regex_flexibility(result["regex"], phrase_analysis)
                result["regex"] = enhanced_regex
            
            # Validate the generated regex
            validation = self._validate_regex_comprehensive(result["regex"], cleaned_phrases)
            result.update(validation)
            
            # Add phrase analysis to result
            result["phrase_analysis"] = phrase_analysis
            
            return result
            
        except Exception as e:
            print(f"Regex generation error: {e}")
            return {
                "regex": "",
                "confidence": 0.0,
                "explanation": f"Error generating regex: {str(e)}",
                "test_matches": [],
                "errors": [str(e)]
            }
    
    def _analyze_phrases(self, phrases: List[str]) -> Dict[str, Any]:
        """Analyze input phrases to understand patterns and extract key information"""
        analysis = {
            "question_words": set(),
            "action_words": set(),
            "key_nouns": set(),
            "common_patterns": [],
            "word_frequency": {},
            "phrase_length_stats": {
                "min": float('inf'),
                "max": 0,
                "avg": 0
            }
        }
        
        # Define word categories
        question_words = {'what', 'how', 'which', 'where', 'when', 'who', 'why'}
        action_words = {'show', 'get', 'display', 'find', 'list', 'give', 'tell', 'search', 'view', 'see'}
        filler_words = {'the', 'a', 'an', 'is', 'are', 'do', 'we', 'have', 'has', 'can', 'you', 'please', 'me', 'my'}
        
        total_length = 0
        
        for phrase in phrases:
            words = phrase.lower().split()
            total_length += len(words)
            
            # Update length stats
            phrase_len = len(words)
            analysis["phrase_length_stats"]["min"] = min(analysis["phrase_length_stats"]["min"], phrase_len)
            analysis["phrase_length_stats"]["max"] = max(analysis["phrase_length_stats"]["max"], phrase_len)
            
            for word in words:
                # Count word frequency
                analysis["word_frequency"][word] = analysis["word_frequency"].get(word, 0) + 1
                
                # Categorize words
                if word in question_words:
                    analysis["question_words"].add(word)
                elif word in action_words:
                    analysis["action_words"].add(word)
                elif word not in filler_words and len(word) > 2:
                    analysis["key_nouns"].add(word)
        
        # Calculate average length
        analysis["phrase_length_stats"]["avg"] = total_length / len(phrases) if phrases else 0
        
        # Find common patterns
        if len(phrases) > 1:
            analysis["common_patterns"] = self._find_common_phrase_patterns(phrases)
        
        # Convert sets to lists for JSON serialization
        analysis["question_words"] = list(analysis["question_words"])
        analysis["action_words"] = list(analysis["action_words"])
        analysis["key_nouns"] = list(analysis["key_nouns"])
        
        return analysis
    
    def _find_common_phrase_patterns(self, phrases: List[str]) -> List[str]:
        """Find common word patterns across phrases"""
        patterns = []
        
        # Look for common word sequences
        word_sequences = []
        for phrase in phrases:
            words = phrase.lower().split()
            for i in range(len(words)):
                for j in range(i + 2, min(i + 5, len(words) + 1)):  # 2-4 word sequences
                    sequence = ' '.join(words[i:j])
                    word_sequences.append(sequence)
        
        # Find sequences that appear in multiple phrases
        from collections import Counter
        sequence_counts = Counter(word_sequences)
        
        for sequence, count in sequence_counts.items():
            if count > 1:  # Appears in multiple phrases
                patterns.append(f"Common sequence: '{sequence}' (appears {count} times)")
        
        return patterns[:5]  # Limit to top 5 patterns
    
    def _build_enhanced_regex_prompt(
        self, 
        phrases: List[str], 
        intent: str, 
        pattern_kind: str,
        phrase_analysis: Dict[str, Any]
    ) -> str:
        """Build an intelligent prompt for Ollama to generate flexible regex"""
        
        examples_text = "\n".join([f"- \"{phrase}\"" for phrase in phrases])
        
        # Build context based on analysis
        context_hints = []
        if phrase_analysis["question_words"]:
            context_hints.append(f"Contains question words: {', '.join(phrase_analysis['question_words'])}")
        if phrase_analysis["action_words"]:
            context_hints.append(f"Contains action words: {', '.join(phrase_analysis['action_words'])}")
        if phrase_analysis["key_nouns"]:
            key_nouns = list(phrase_analysis["key_nouns"])[:5]  # Top 5 key nouns
            context_hints.append(f"Key terms: {', '.join(key_nouns)}")
        
        context_section = "\n".join([f"- {hint}" for hint in context_hints]) if context_hints else "- General conversational patterns detected"
        
        if pattern_kind == "negative":
            purpose = "should NOT match"
            instruction = "Create a negative lookahead or exclusion pattern that avoids these phrases"
        elif pattern_kind == "synonym":
            purpose = "are synonyms/variations that should all match"
            instruction = "Create a pattern that captures all these variations and similar meanings"
        else:  # positive
            purpose = "should match"
            instruction = "Create a flexible pattern that matches these examples and reasonable variations"
        
        prompt = f"""You are an expert in creating flexible JavaScript-compatible regex patterns for natural language intent classification.

TASK: Generate a regex pattern for intent "{intent}"
PATTERN TYPE: {pattern_kind}

EXAMPLE PHRASES (these {purpose}):
{examples_text}

PHRASE ANALYSIS:
{context_section}

CRITICAL REQUIREMENTS FOR FLEXIBLE MATCHING:
1. Use JavaScript regex syntax (no named groups, use \\b for word boundaries)
2. Make it case-insensitive compatible (we'll add the 'i' flag)
3. Be VERY FLEXIBLE - natural language varies enormously:
   - Different word orders: "student details" vs "details about student"
   - Optional filler words: "what", "the", "a", "do", "we", "have", "can", "you", "please"
   - Plural/singular variations: "student/students", "detail/details"
   - Synonyms: "show/display/get/find", "student/pupil", "info/information/details"
   - Question patterns: "what is...", "how do I...", "where can I..."
   - Casual vs formal: "gimme student info" vs "please provide student information"

4. FLEXIBILITY STRATEGIES:
   - Use optional groups liberally: (word)?\\s*
   - Allow flexible spacing: \\s+ between words
   - Use alternation for synonyms: (word1|word2|word3)
   - Make common words optional: (please\\s+)?(can\\s+you\\s+)?
   - Allow different word orders where reasonable

5. ESSENTIAL PATTERNS FOR NATURAL LANGUAGE:
   - Optional question starts: (what|how|which|where)\\s*
   - Optional polite prefixes: (please\\s+)?(can\\s+you\\s+)?(could\\s+you\\s+)?
   - Flexible core terms with alternation
   - Optional endings: (please|thanks)?

EXAMPLE THINKING PROCESS:
For phrases like "What student number do we have?", "student number", "show student ID":
- Core concept: student + number/ID  
- Optional question words: (what|which)?\\s*
- Optional actions: (show|get|display)?\\s*
- Core terms: (student|pupil)s?\\s+(number|id|count)
- Optional endings: (do\\s+we\\s+have|please)?

Good pattern: \\b(what|which|how\\s+many)?\\s*(show|get|display)?\\s*(student|pupil)s?\\s+(number|numbers|id|count)\\s*(do\\s+we\\s+have|are\\s+there|please)?\\b

ADVANCED FLEXIBILITY TECHNIQUES:
- Use \\w* for word variations: student\\w* matches "student", "students", "student's"
- Allow extra words: \\w+\\s+ for flexible insertion
- Group related concepts: (student|pupil|learner)

OUTPUT FORMAT:
```regex
[your flexible regex pattern here]
```

EXPLANATION:
[Explain the key flexibility features and what variations it captures]

CONFIDENCE NOTE:
Rate your confidence (0-100%) in how well this pattern will match natural language variations of the intent.

Generate a highly flexible regex that prioritizes capturing the intent over exact word matching:"""

        return prompt
    
    def _parse_regex_response(self, response: str, original_phrases: List[str]) -> Dict[str, Any]:
        """Parse Ollama's response to extract regex and explanation"""
        
        # Extract regex from code blocks
        regex_pattern = ""
        explanation = ""
        confidence_score = 0.8  # Default confidence
        
        # Look for ```regex blocks first
        regex_match = re.search(r'```regex\s*\n(.*?)\n```', response, re.DOTALL)
        if regex_match:
            regex_pattern = regex_match.group(1).strip()
        else:
            # Look for any code blocks
            code_match = re.search(r'```\s*\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                regex_pattern = code_match.group(1).strip()
        
        # Extract explanation
        explanation_match = re.search(r'EXPLANATION:\s*(.*?)(?:\n\n|\nCONFIDENCE|$)', response, re.DOTALL)
        if explanation_match:
            explanation = explanation_match.group(1).strip()
        else:
            # Look for text after the regex block
            if regex_pattern:
                parts = response.split('```')
                if len(parts) > 2:
                    explanation = parts[2].strip()
        
        # Extract confidence if mentioned
        confidence_match = re.search(r'confidence.*?(\d+)%', response, re.IGNORECASE)
        if confidence_match:
            confidence_score = int(confidence_match.group(1)) / 100.0
        
        # Fallback: try to find any regex-like pattern
        if not regex_pattern:
            # Look for patterns that look like regex
            potential_patterns = re.findall(r'\\b.*?\\b|\\w+.*?\\w+|\([^)]+\)', response)
            if potential_patterns:
                regex_pattern = max(potential_patterns, key=len)  # Take the longest one
        
        # Clean up the regex
        regex_pattern = regex_pattern.strip()
        
        if not explanation:
            explanation = f"Generated pattern to match natural language variations of: {', '.join(original_phrases[:3])}"
            if len(original_phrases) > 3:
                explanation += f" and {len(original_phrases) - 3} more phrases"
        
        return {
            "regex": regex_pattern,
            "explanation": explanation,
            "confidence": confidence_score,
            "test_matches": [],
            "errors": []
        }
    
    def _enhance_regex_flexibility(self, regex: str, phrase_analysis: Dict[str, Any]) -> str:
        """Enhance a generated regex to be more flexible for natural language"""
        
        if not regex:
            return regex
        
        enhanced_regex = regex
        
        # Add common optional prefixes if not already present
        optional_prefixes = [
            r"(please\s+)?",
            r"(can\s+you\s+)?",
            r"(could\s+you\s+)?",
            r"(what\s+is\s+)?",
            r"(what\s+)?"
        ]
        
        # Check if the regex already handles common question/polite words
        has_flexibility = any(word in regex.lower() for word in ['please', 'can', 'what', 'how', 'which'])
        
        if not has_flexibility and phrase_analysis.get("question_words"):
            # Prepend optional question words
            question_words = phrase_analysis["question_words"]
            question_pattern = f"({'|'.join(question_words)})\\s*"
            enhanced_regex = f"({question_pattern})?\\s*{enhanced_regex}"
        
        # Ensure word boundaries are present
        if not enhanced_regex.startswith(('\\b', '(', '^')):
            enhanced_regex = f"\\b{enhanced_regex}"
        
        if not enhanced_regex.endswith(('\\b', ')', '$', '?')):
            enhanced_regex = f"{enhanced_regex}\\b"
        
        # Add optional trailing politeness
        if "please" not in enhanced_regex.lower():
            enhanced_regex = f"{enhanced_regex}(\\s+please)?"
        
        return enhanced_regex
    
    def _validate_regex_comprehensive(self, regex: str, test_phrases: List[str]) -> Dict[str, Any]:
        """Comprehensive validation of the generated regex against input phrases"""
        
        errors = []
        matches = []
        confidence = 0.0
        detailed_results = []
        
        if not regex:
            return {
                "confidence": 0.0,
                "errors": ["Empty regex pattern generated"],
                "test_matches": [],
                "detailed_results": []
            }
        
        try:
            # Test compile the regex
            compiled_regex = re.compile(regex, re.IGNORECASE)
            
            # Test against input phrases
            successful_matches = 0
            failed_phrases = []
            
            for phrase in test_phrases:
                try:
                    match = compiled_regex.search(phrase)
                    if match:
                        matches.append(phrase)
                        successful_matches += 1
                        detailed_results.append({
                            "phrase": phrase,
                            "matched": True,
                            "match_text": match.group(0),
                            "start": match.start(),
                            "end": match.end()
                        })
                    else:
                        failed_phrases.append(phrase)
                        detailed_results.append({
                            "phrase": phrase,
                            "matched": False,
                            "reason": "No match found"
                        })
                except Exception as e:
                    failed_phrases.append(phrase)
                    detailed_results.append({
                        "phrase": phrase,
                        "matched": False,
                        "reason": f"Match error: {str(e)}"
                    })
            
            # Calculate confidence based on match rate with more nuanced scoring
            if test_phrases:
                match_rate = successful_matches / len(test_phrases)
                
                if match_rate >= 0.9:
                    confidence = 0.95  # Excellent
                elif match_rate >= 0.8:
                    confidence = 0.85  # Very good
                elif match_rate >= 0.7:
                    confidence = 0.75  # Good
                elif match_rate >= 0.5:
                    confidence = 0.6   # Acceptable
                elif match_rate >= 0.3:
                    confidence = 0.4   # Poor but usable
                else:
                    confidence = 0.2   # Very poor
                
                # Add detailed error messages for failed matches
                if failed_phrases:
                    errors.append(f"Failed to match {len(failed_phrases)}/{len(test_phrases)} phrases:")
                    for phrase in failed_phrases[:3]:  # Show first 3 failed phrases
                        errors.append(f"  - '{phrase}'")
                    if len(failed_phrases) > 3:
                        errors.append(f"  - ...and {len(failed_phrases) - 3} more phrases")
            
            # Additional validation checks
            if len(regex) < 5:
                errors.append("Pattern is very simple - may be too restrictive")
                confidence *= 0.7
            elif len(regex) < 15:
                errors.append("Pattern seems simple - consider if it's flexible enough")
                confidence *= 0.9
            
            if len(regex) > 300:
                errors.append("Pattern is very complex - may be over-engineered")
                confidence *= 0.8
            elif len(regex) > 150:
                errors.append("Pattern is quite complex - verify it's not overfitted")
                confidence *= 0.95
            
            # Check for balanced parentheses
            if regex.count('(') != regex.count(')'):
                errors.append("Unbalanced parentheses in regex")
                confidence = 0.0
            
            # Check for good flexibility indicators
            flexibility_indicators = ['?', '|', '*', '+']
            if not any(indicator in regex for indicator in flexibility_indicators):
                errors.append("Pattern lacks flexibility indicators - may be too rigid")
                confidence *= 0.8
            
            # Check for word boundaries
            if '\\b' not in regex:
                errors.append("Pattern lacks word boundaries - may have false positives")
                confidence *= 0.9
            
            # Provide improvement suggestions
            if match_rate < 0.8 and len(test_phrases) > 1:
                errors.append("Consider making the pattern more flexible for natural language variations")
                
        except re.error as e:
            errors.append(f"Invalid regex syntax: {str(e)}")
            confidence = 0.0
        except Exception as e:
            errors.append(f"Regex validation error: {str(e)}")
            confidence = 0.0
        
        return {
            "confidence": confidence,
            "errors": errors,
            "test_matches": matches,
            "detailed_results": detailed_results,
            "match_rate": successful_matches / len(test_phrases) if test_phrases else 0
        }
    
    async def improve_regex(
        self, 
        current_regex: str, 
        missed_phrases: List[str],
        false_positives: List[str] = None
    ) -> Dict[str, Any]:
        """Improve an existing regex to handle missed cases"""
        
        if not missed_phrases:
            return {
                "regex": current_regex,
                "confidence": 0.8,
                "explanation": "No improvements needed",
                "test_matches": [],
                "errors": []
            }
        
        false_positives = false_positives or []
        
        # Analyze what the current regex is missing
        missed_analysis = self._analyze_phrases(missed_phrases)
        
        improvement_prompt = f"""You are a regex expert. Improve this existing regex pattern to be more flexible.

CURRENT PATTERN: {current_regex}

PROBLEM: The pattern misses these phrases (should match but doesn't):
{chr(10).join([f'- "{phrase}"' for phrase in missed_phrases])}

{f'''ALSO AVOID: These should NOT match (false positives):
{chr(10).join([f'- "{phrase}"' for phrase in false_positives])}''' if false_positives else ''}

ANALYSIS OF MISSED PHRASES:
- Key terms that might be missing: {', '.join(missed_analysis.get('key_nouns', [])[:5])}
- Question words used: {', '.join(missed_analysis.get('question_words', []))}
- Action words used: {', '.join(missed_analysis.get('action_words', []))}

IMPROVEMENT STRATEGIES: