# app/services/ollama_service/phrase_analyzer.py - Simplified and more effective approach

import re
from typing import Dict, Any, List, Set
from collections import Counter
from .base import OllamaBaseService


class OllamaPhraseAnalyzer(OllamaBaseService):
    """Simplified phrase analysis focused on practical regex generation"""
    
    def _analyze_phrases(self, phrases: List[str]) -> Dict[str, Any]:
        """Analyze input phrases to extract core concepts and variations"""
        analysis = {
            "core_terms": set(),
            "action_words": set(),
            "question_words": set(),
            "modifiers": set(),
            "phrase_patterns": [],
            "complexity_level": "simple"
        }
        
        # Core word categories - keep it simple
        action_words = {'show', 'get', 'list', 'display', 'find', 'see', 'view', 'give', 'tell', 'provide'}
        question_words = {'what', 'how', 'which', 'where', 'when', 'who'}
        filler_words = {'the', 'a', 'an', 'is', 'are', 'do', 'we', 'have', 'can', 'you', 'please', 'me', 'my', 'in', 'of', 'for', 'to'}
        
        for phrase in phrases:
            words = phrase.lower().split()
            
            for word in words:
                if word in action_words:
                    analysis["action_words"].add(word)
                elif word in question_words:
                    analysis["question_words"].add(word)
                elif word not in filler_words and len(word) > 2:
                    analysis["core_terms"].add(word)
        
        # Determine complexity
        total_words = sum(len(phrase.split()) for phrase in phrases)
        if total_words > len(phrases) * 4:  # Average > 4 words per phrase
            analysis["complexity_level"] = "complex"
        
        # Convert to lists
        analysis["core_terms"] = list(analysis["core_terms"])
        analysis["action_words"] = list(analysis["action_words"])
        analysis["question_words"] = list(analysis["question_words"])
        
        return analysis
    
    def _build_enhanced_regex_prompt(
        self, 
        phrases: List[str], 
        intent: str, 
        pattern_kind: str,
        phrase_analysis: Dict[str, Any]
    ) -> str:
        """Build a SIMPLE, focused prompt that generates working patterns"""
        
        examples_text = "\n".join([f"- \"{phrase}\"" for phrase in phrases])
        
        # Extract key information simply
        core_terms = phrase_analysis.get("core_terms", [])[:3]  # Max 3 core terms
        action_words = phrase_analysis.get("action_words", [])[:2]  # Max 2 actions
        question_words = phrase_analysis.get("question_words", [])[:2]  # Max 2 questions
        
        prompt = f"""Create a simple JavaScript regex pattern that matches these phrases:

{examples_text}

REQUIREMENTS:
1. Keep it SIMPLE - avoid overly complex patterns
2. Use JavaScript syntax with \\b word boundaries
3. Make it case-insensitive compatible (we add 'i' flag)
4. Focus on the core meaning, not every variation

KEY TERMS DETECTED: {', '.join(core_terms) if core_terms else 'none'}
ACTION WORDS: {', '.join(action_words) if action_words else 'none'}
QUESTION WORDS: {', '.join(question_words) if question_words else 'none'}

SIMPLE PATTERN STRATEGY:
- If you see action words like "list", "show", "get": include them as optional
- If you see core terms like "student", "grade": make them required
- Use simple alternation: (word1|word2)
- Make common words optional: (word)?
- Don't over-complicate with too many optional groups

EXAMPLES OF GOOD SIMPLE PATTERNS:
- For "list students": \\b(list|show)?\\s*(student|pupil)s?\\b
- For "student grades": \\b(student|pupil)s?\\s+(grade|score|mark)s?\\b
- For "what is grade": \\b(what|how)?\\s*(grade|score|mark)\\b

CREATE A SIMPLE PATTERN:
```regex
[simple pattern here]
```

EXPLANATION:
[Brief explanation - keep it simple]"""

        return prompt
    
    def _parse_regex_response(self, response: str, original_phrases: List[str]) -> Dict[str, Any]:
        """Parse response with better fallbacks for simple patterns"""
        
        # Extract regex from code blocks
        regex_pattern = ""
        explanation = ""
        confidence_score = 0.8
        
        # Look for ```regex blocks
        regex_match = re.search(r'```regex\s*\n(.*?)\n```', response, re.DOTALL)
        if regex_match:
            regex_pattern = regex_match.group(1).strip()
        else:
            # Look for any code blocks
            code_match = re.search(r'```\s*\n(.*?)\n```', response, re.DOTALL)
            if code_match:
                regex_pattern = code_match.group(1).strip()
        
        # If no regex found, create a simple fallback
        if not regex_pattern:
            regex_pattern = self._create_simple_fallback_pattern(original_phrases)
            explanation = "Generated simple fallback pattern based on key terms"
            confidence_score = 0.6
        
        # Clean up
        regex_pattern = regex_pattern.strip().strip('"\'`')
        
        # Extract explanation if not set
        if not explanation:
            explanation_match = re.search(r'EXPLANATION:\s*(.*?)(?:\n\n|$)', response, re.DOTALL)
            if explanation_match:
                explanation = explanation_match.group(1).strip()
            else:
                explanation = "Generated pattern for intent matching"
        
        return {
            "regex": regex_pattern,
            "explanation": explanation,
            "confidence": confidence_score,
            "test_matches": [],
            "errors": []
        }
    
    def _create_simple_fallback_pattern(self, phrases: List[str]) -> str:
        """Create a simple pattern when Ollama fails"""
        
        # Extract key words from all phrases
        all_words = []
        for phrase in phrases:
            words = [w.lower().strip('?.,!') for w in phrase.split()]
            all_words.extend(words)
        
        # Filter out common words
        filler_words = {'the', 'a', 'an', 'is', 'are', 'do', 'we', 'have', 'can', 'you', 'please', 'me', 'my', 'in', 'of', 'for', 'to', 'i', 'want'}
        key_words = [word for word in all_words if word not in filler_words and len(word) > 2]
        
        # Count frequency
        word_counts = Counter(key_words)
        
        # Get most common words
        important_words = [word for word, count in word_counts.most_common(3)]
        
        if not important_words:
            return r'\b\w+\b'  # Ultimate fallback
        
        # Create simple pattern
        if len(important_words) == 1:
            pattern = f"\\b{important_words[0]}s?\\b"
        elif len(important_words) == 2:
            pattern = f"\\b({important_words[0]}|{important_words[1]})s?\\b"
        else:
            # For 3+ words, create a more flexible pattern
            pattern = f"\\b({important_words[0]}s?|{important_words[1]}s?)\\b"
        
        return pattern
    
    def _enhance_regex_flexibility(self, regex: str, phrase_analysis: Dict[str, Any]) -> str:
        """Simple enhancement focused on common cases"""
        
        if not regex:
            return regex
        
        enhanced_regex = regex
        
        # Simple enhancements only
        
        # Ensure word boundaries
        if not enhanced_regex.startswith('\\b'):
            enhanced_regex = f"\\b{enhanced_regex}"
        if not enhanced_regex.endswith('\\b'):
            enhanced_regex = f"{enhanced_regex}\\b"
        
        # Add optional 's' for plurals if not present
        if 's?' not in enhanced_regex and not enhanced_regex.endswith('s'):
            # Simple plural handling
            enhanced_regex = enhanced_regex.replace('\\b', 's?\\b')
            enhanced_regex = f"\\b{enhanced_regex[2:]}"  # Remove duplicate \b
        
        return enhanced_regex
    
    def create_simple_pattern_for_phrases(self, phrases: List[str]) -> str:
        """Direct method to create simple patterns without Ollama"""
        
        if not phrases:
            return ""
        
        # Analyze the phrases simply
        all_words = []
        action_words = set()
        core_terms = set()
        
        actions = {'list', 'show', 'get', 'display', 'find', 'see', 'view', 'give', 'tell', 'provide'}
        fillers = {'the', 'a', 'an', 'is', 'are', 'do', 'we', 'have', 'can', 'you', 'please', 'me', 'my', 'in', 'of', 'for', 'to', 'i', 'want'}
        
        for phrase in phrases:
            words = phrase.lower().split()
            for word in words:
                clean_word = word.strip('?.,!')
                if clean_word in actions:
                    action_words.add(clean_word)
                elif clean_word not in fillers and len(clean_word) > 2:
                    core_terms.add(clean_word)
        
        # Build pattern components
        pattern_parts = []
        
        # Optional action words
        if action_words:
            action_pattern = f"({'|'.join(sorted(action_words))})\\s+"
            pattern_parts.append(f"({action_pattern})?")
        
        # Core terms (required)
        if core_terms:
            # Take up to 2 most common core terms
            core_list = list(sorted(core_terms))[:2]
            core_pattern = f"({'|'.join(core_list)})s?"
            pattern_parts.append(core_pattern)
        
        # Combine parts
        if pattern_parts:
            pattern = "\\b" + "\\s*".join(pattern_parts) + "\\b"
        else:
            # Last resort - match any of the original phrases literally
            escaped_phrases = [re.escape(phrase.lower()) for phrase in phrases]
            pattern = f"\\b({'|'.join(escaped_phrases)})\\b"
        
        return pattern