# app/services/ollama_service/base.py - Base service and core communication methods

import os
import requests
import json
import re
from typing import Dict, Any, Optional, List, Set
from datetime import datetime
import asyncio
import aiohttp
import concurrent.futures


class OllamaBaseService:
    """Base service for Ollama API communication and core functionality"""
    
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
    
    # === CORE OLLAMA API COMMUNICATION ===
    
    async def _call_ollama(self, prompt: str) -> Dict[str, Any]:
        """Make async request to Ollama API with enhanced error handling"""
        try:
            payload = {
                "model": self.model,
                "prompt": prompt,
                "stream": False,
                "options": {
                    "temperature": 0.3,  # Lower temperature for more consistent analysis
                    "top_p": 0.9,
                    "num_ctx": 8192,  # Increased context window for complex prompts
                    "repeat_penalty": 1.1,
                    "top_k": 40
                }
            }
            
            print(f"Sending request to Ollama: {len(prompt)} characters")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/api/generate",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=self.timeout)
                ) as response:
                    
                    if response.status != 200:
                        error_text = await response.text()
                        print(f"Ollama API error {response.status}: {error_text}")
                        raise Exception(f"Ollama API error {response.status}: {error_text}")
                    
                    result = await response.json()
                    response_length = len(result.get('response', ''))
                    print(f"Ollama response received: {response_length} characters")
                    
                    # Validate response
                    if not result.get('response'):
                        raise Exception("Empty response from Ollama")
                    
                    return result
                    
        except asyncio.TimeoutError:
            raise Exception(f"Ollama request timed out after {self.timeout} seconds")
        except aiohttp.ClientError as e:
            raise Exception(f"Ollama connection error: {str(e)}")
        except json.JSONDecodeError as e:
            raise Exception(f"Invalid JSON response from Ollama: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama API call failed: {str(e)}")
    
    # === HEALTH CHECK AND UTILITY METHODS ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Comprehensive health check for Ollama service"""
        health_status = {
            "service_available": False,
            "model_loaded": False,
            "response_time": None,
            "error": None
        }
        
        try:
            start_time = datetime.utcnow()
            
            # Check if service is available
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/tags",
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    
                    if response.status == 200:
                        health_status["service_available"] = True
                        
                        # Check if our model is available
                        data = await response.json()
                        models = [model.get("name", "") for model in data.get("models", [])]
                        
                        if self.model in models:
                            health_status["model_loaded"] = True
                        else:
                            health_status["error"] = f"Model '{self.model}' not found. Available: {models}"
                    else:
                        health_status["error"] = f"Service returned status {response.status}"
            
            # Calculate response time
            end_time = datetime.utcnow()
            health_status["response_time"] = (end_time - start_time).total_seconds()
            
        except Exception as e:
            health_status["error"] = str(e)
        
        return health_status
    
    def health_check_sync(self) -> bool:
        """Synchronous health check for Ollama service"""
        try:
            response = requests.get(
                f"{self.base_url}/api/tags",
                timeout=10
            )
            return response.status_code == 200
        except Exception as e:
            print(f"Ollama health check failed: {e}")
            return False
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the current model"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/api/show",
                    json={"name": self.model},
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {"error": f"Failed to get model info: {response.status}"}
                        
        except Exception as e:
            return {"error": str(e)}
    
    # === UTILITY METHODS FOR DEBUGGING ===
    
    def debug_regex_matching(self, regex: str, test_string: str) -> Dict[str, Any]:
        """Debug regex matching with detailed breakdown"""
        debug_info = {
            "regex": regex,
            "test_string": test_string,
            "compiled": False,
            "match_found": False,
            "match_details": None,
            "error": None
        }
        
        try:
            compiled_regex = re.compile(regex, re.IGNORECASE | re.VERBOSE)
            debug_info["compiled"] = True
            
            match = compiled_regex.search(test_string)
            if match:
                debug_info["match_found"] = True
                debug_info["match_details"] = {
                    "full_match": match.group(0),
                    "start": match.start(),
                    "end": match.end(),
                    "groups": match.groups(),
                    "groupdict": match.groupdict()
                }
            
        except re.error as e:
            debug_info["error"] = f"Regex compilation error: {str(e)}"
        except Exception as e:
            debug_info["error"] = f"Matching error: {str(e)}"
        
        return debug_info
    
    def get_regex_examples(self) -> Dict[str, List[str]]:
        """Get examples of good regex patterns for different intent types"""
        return {
            "student_info": [
                r"\b(what|which|show|get|display)?\s*(student|pupil)s?\s+(details?|info|information|record)\b",
                r"\b(student|pupil)\s+(number|id|count)\b"
            ],
            "grades_scores": [
                r"\b(what|how|show)?\s*(are\s+)?my\s+(grades?|scores?|marks?)\b",
                r"\b(get|show|display)\s+(grades?|scores?|results?)\b"
            ],
            "schedule_timetable": [
                r"\b(what|when|show)?\s*(is\s+)?my\s+(schedule|timetable|classes?)\b",
                r"\b(today|tomorrow)s?\s+(schedule|classes?)\b"
            ],
            "fees_payment": [
                r"\b(fee|payment|due|outstanding)\s+(amount|balance|status)\b",
                r"\b(how\s+much|what)\s+(do\s+i\s+owe|fees?|payment)\b"
            ]
        }