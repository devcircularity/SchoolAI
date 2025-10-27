# app/services/ollama_service/main.py - Main service with regex generation and improvement

from typing import Dict, Any, List
from .phrase_analyzer import OllamaPhraseAnalyzer
from .regex_validator import OllamaRegexValidator
from .ocr_processor import OllamaOCRProcessor


class OllamaMainService(OllamaPhraseAnalyzer, OllamaRegexValidator, OllamaOCRProcessor):
    """Main service combining all Ollama functionality with enhanced regex generation"""
    
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
1. Add missing synonyms or word variations to alternation groups
2. Make more words optional with (word)?\\s* patterns
3. Add flexible word order alternatives
4. Include missing question or action words
5. Ensure adequate spacing flexibility with \\s+ patterns

REQUIREMENTS:
- Keep the same general intent and core structure
- Use JavaScript regex syntax
- Maintain word boundaries (\\b) for precision
- Be more inclusive while staying focused on the intent
- Test that improvements don't break existing functionality

OUTPUT the improved regex:

```regex
[improved regex here]
```

EXPLANATION:
[What you changed and why, focusing on how it now captures the missed phrases]

Generate the improved pattern:"""

        try:
            response = await self._call_ollama(improvement_prompt)
            result = self._parse_regex_response(response.get("response", ""), missed_phrases)
            
            # Validate the improved regex against both missed phrases and original test cases
            all_test_phrases = missed_phrases
            validation = self._validate_regex_comprehensive(result["regex"], all_test_phrases)
            result.update(validation)
            
            # Add improvement metadata
            result["improvement_analysis"] = {
                "missed_phrases_targeted": missed_phrases,
                "false_positives_avoided": false_positives,
                "original_regex": current_regex
            }
            
            return result
            
        except Exception as e:
            return {
                "regex": current_regex,
                "confidence": 0.0,
                "explanation": f"Error improving regex: {str(e)}",
                "test_matches": [],
                "errors": [str(e)]
            }
    
    async def generate_test_phrases(self, intent: str, existing_phrases: List[str] = None) -> Dict[str, Any]:
        """Generate additional test phrases for a given intent to improve pattern testing"""
        
        existing_phrases = existing_phrases or []
        existing_text = "\n".join([f"- {phrase}" for phrase in existing_phrases]) if existing_phrases else "None provided"
        
        prompt = f"""You are an expert in natural language patterns. Generate diverse test phrases for intent classification.

INTENT: {intent}

EXISTING PHRASES:
{existing_text}

TASK: Generate 10-15 additional phrases that users might naturally use to express this intent.

REQUIREMENTS:
1. Create realistic, natural language variations
2. Include different formality levels (casual, formal, polite)
3. Vary sentence structure and word order
4. Include synonyms and alternative phrasings
5. Add question and statement variations
6. Consider different user contexts (student, parent, admin, etc.)
7. Make phrases diverse but clearly related to the intent

EXAMPLE VARIATIONS TO CONSIDER:
- Questions: "What is...", "How do I...", "Where can I..."
- Statements: "I need...", "Show me...", "Give me..."
- Polite forms: "Could you please...", "Would it be possible to..."
- Casual forms: "Gimme...", "I wanna see...", "Let me check..."

OUTPUT FORMAT:
Generate 10-15 phrases, one per line:
- [phrase 1]
- [phrase 2]
- etc.

Generate diverse test phrases for "{intent}":"""
        
        try:
            response = await self._call_ollama(prompt)
            response_text = response.get("response", "")
            
            # Parse generated phrases
            generated_phrases = []
            lines = response_text.split('\n')
            
            for line in lines:
                line = line.strip()
                if line.startswith('- '):
                    phrase = line[2:].strip().strip('"\'')
                    if phrase and phrase not in existing_phrases:
                        generated_phrases.append(phrase)
            
            return {
                "intent": intent,
                "generated_phrases": generated_phrases,
                "existing_phrases": existing_phrases,
                "total_phrases": len(generated_phrases),
                "success": True
            }
            
        except Exception as e:
            return {
                "intent": intent,
                "generated_phrases": [],
                "existing_phrases": existing_phrases,
                "total_phrases": 0,
                "success": False,
                "error": str(e)
            }