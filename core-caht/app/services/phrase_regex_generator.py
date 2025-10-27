# app/services/phrase_regex_generator.py
"""Simplified service for converting natural phrases to regex patterns using existing OllamaService"""

from typing import List, Optional, Dict, Any
from dataclasses import dataclass

from app.services.ollama_service import OllamaService


@dataclass
class RegexGenerationResult:
    """Result of phrase-to-regex conversion"""
    regex: str
    confidence: float
    explanation: str
    test_matches: List[str]
    errors: List[str]


class PhraseRegexGenerator:
    """Generate regex patterns from natural language phrases using OllamaService"""
    
    def __init__(self):
        self.ollama = OllamaService()
    
    async def phrases_to_regex(
        self, 
        phrases: List[str], 
        intent: str,
        pattern_kind: str = "positive"
    ) -> RegexGenerationResult:
        """
        Convert a list of natural phrases into a regex pattern using Ollama.
        
        Args:
            phrases: List of example phrases that should match
            intent: The intent these phrases represent (for context)
            pattern_kind: positive, negative, or synonym
        
        Returns:
            RegexGenerationResult with the generated regex and metadata
        """
        try:
            # Use the new regex generation method from OllamaService
            result = await self.ollama.generate_regex_from_phrases(phrases, intent, pattern_kind)
            
            return RegexGenerationResult(
                regex=result.get("regex", ""),
                confidence=result.get("confidence", 0.0),
                explanation=result.get("explanation", ""),
                test_matches=result.get("test_matches", []),
                errors=result.get("errors", [])
            )
            
        except Exception as e:
            return RegexGenerationResult(
                regex="",
                confidence=0.0,
                explanation=f"Error generating regex: {str(e)}",
                test_matches=[],
                errors=[str(e)]
            )
    
    async def test_regex_against_phrases(
        self, 
        regex: str, 
        test_phrases: List[str]
    ) -> Dict[str, Any]:
        """Test a regex pattern against a list of phrases"""
        return await self.ollama.test_regex_against_phrases(regex, test_phrases)
    
    async def improve_regex(
        self, 
        current_regex: str, 
        missed_phrases: List[str],
        false_positives: List[str] = None
    ) -> RegexGenerationResult:
        """Improve an existing regex to handle missed cases"""
        try:
            result = await self.ollama.improve_regex(current_regex, missed_phrases, false_positives)
            
            return RegexGenerationResult(
                regex=result.get("regex", current_regex),
                confidence=result.get("confidence", 0.0),
                explanation=result.get("explanation", ""),
                test_matches=result.get("test_matches", []),
                errors=result.get("errors", [])
            )
            
        except Exception as e:
            return RegexGenerationResult(
                regex=current_regex,
                confidence=0.0,
                explanation=f"Error improving regex: {str(e)}",
                test_matches=[],
                errors=[str(e)]
            )