# app/services/ollama_service/__init__.py - Service initialization and export

from .main import OllamaMainService

# Export the main service class
OllamaService = OllamaMainService

# Export individual components for advanced use cases
from .base import OllamaBaseService
from .phrase_analyzer import OllamaPhraseAnalyzer
from .regex_validator import OllamaRegexValidator
from .ocr_processor import OllamaOCRProcessor

__all__ = [
    'OllamaService',
    'OllamaBaseService', 
    'OllamaPhraseAnalyzer',
    'OllamaRegexValidator',
    'OllamaOCRProcessor'
]