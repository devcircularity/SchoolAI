# app/services/config_router.py
import re
import time
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session

from app.models.intent_config import IntentConfigVersion, IntentPattern, PatternKind


@dataclass
class RouterResult:
    """Result from ConfigRouter pattern matching"""
    intent: str
    reason: str  # "pattern:id" or "synonym:id"
    entities: Dict[str, Any]
    confidence: float
    pattern_id: str


class ConfigRouter:
    """Database-driven pattern-based intent router"""
    
    def __init__(self, db: Session):
        self.db = db
        self._cache = {}
        self._cache_version = None
        self._load_active_config()
    
    def route(self, message: str, school_id: Optional[str] = None) -> Optional[RouterResult]:
        """
        Route message using active configuration patterns
        
        Args:
            message: User message to route
            school_id: Optional school-specific overrides
            
        Returns:
            RouterResult if match found, None otherwise
        """
        # Ensure we have latest config
        self._ensure_cache_current()
        
        if not self._cache:
            print(f"ConfigRouter: Cache is empty! Attempting to load...")
            self._load_active_config()
            if not self._cache:
                print(f"ConfigRouter: Still no cache after reload attempt")
                return None
        
        # Debug: Show cache stats
        print(f"ConfigRouter cache stats: {self.get_cache_stats()}")
        
        message_lower = message.lower().strip()
        print(f"ConfigRouter: Processing message: '{message_lower}'")
        
        # Apply synonyms first
        normalized_message = self._apply_synonyms(message_lower, school_id)
        if normalized_message != message_lower:
            print(f"ConfigRouter: After synonyms: '{normalized_message}'")
        
        # Find best matching positive pattern
        best_match = self._find_best_pattern(normalized_message, school_id)
        
        if best_match:
            print(f"ConfigRouter: Found match - intent: {best_match['intent']}, confidence: {best_match['confidence']:.3f}")
            
            # Check for negative patterns that would exclude this
            if self._has_negative_match(normalized_message, best_match["handler"], school_id):
                print(f"ConfigRouter: Negative pattern excluded match for handler {best_match['handler']}")
                return None
            
            # Extract entities if possible
            entities = self._extract_entities(normalized_message, best_match)
            if entities:
                print(f"ConfigRouter: Extracted entities: {entities}")
            
            return RouterResult(
                intent=best_match["intent"],
                reason=f"pattern:{best_match['id']}",
                entities=entities,
                confidence=best_match["confidence"],
                pattern_id=best_match["id"]
            )
        
        print(f"ConfigRouter: No pattern matched for '{message_lower}'")
        return None
    
    def reload_config(self):
        """Force reload of configuration from database"""
        print("ConfigRouter: Force reloading configuration...")
        self._cache = {}
        self._cache_version = None
        self._load_active_config()
    
    def _ensure_cache_current(self):
        """Check if cache is current and reload if needed"""
        # Get current active version
        current_version = self.db.query(IntentConfigVersion)\
            .filter(IntentConfigVersion.status == 'active')\
            .first()
        
        current_version_id = current_version.id if current_version else None
        
        if self._cache_version != current_version_id:
            print(f"ConfigRouter: Version changed from {self._cache_version} to {current_version_id}, reloading...")
            self._load_active_config()
    
    def _load_active_config(self):
        """Load active configuration from database into memory cache"""
        try:
            # Get active version
            active_version = self.db.query(IntentConfigVersion)\
                .filter(IntentConfigVersion.status == 'active')\
                .first()
            
            if not active_version:
                print("ConfigRouter: No active intent config version found in database")
                self._cache = {}
                self._cache_version = None
                return
            
            print(f"ConfigRouter: Loading patterns from version '{active_version.name}' (ID: {active_version.id})")
            
            # Load all patterns for active version
            patterns = self.db.query(IntentPattern)\
                .filter(
                    IntentPattern.version_id == active_version.id,
                    IntentPattern.enabled == True
                )\
                .order_by(IntentPattern.priority.desc(), IntentPattern.created_at)\
                .all()
            
            print(f"ConfigRouter: Found {len(patterns)} enabled patterns in database")
            
            # Organize patterns by type
            cache = {
                "positive": [],
                "negative": [],
                "synonyms": []
            }
            
            compilation_errors = 0
            
            for pattern in patterns:
                compiled_pattern = self._compile_pattern(pattern.pattern)
                if compiled_pattern:
                    pattern_data = {
                        "id": pattern.id,
                        "handler": pattern.handler,
                        "intent": pattern.intent,
                        "pattern": compiled_pattern,
                        "raw_pattern": pattern.pattern,
                        "priority": pattern.priority,
                        "scope_school_id": pattern.scope_school_id
                    }
                    
                    if pattern.kind == PatternKind.POSITIVE:
                        cache["positive"].append(pattern_data)
                    elif pattern.kind == PatternKind.NEGATIVE:
                        cache["negative"].append(pattern_data)
                    elif pattern.kind == PatternKind.SYNONYM:
                        cache["synonyms"].append(pattern_data)
                else:
                    compilation_errors += 1
                    print(f"ConfigRouter: Failed to compile pattern for {pattern.intent}: {pattern.pattern[:50]}...")
            
            self._cache = cache
            self._cache_version = active_version.id
            
            print(f"ConfigRouter: Successfully loaded {len(cache['positive'])} positive, "
                  f"{len(cache['negative'])} negative, {len(cache['synonyms'])} synonym patterns")
            
            if compilation_errors > 0:
                print(f"ConfigRouter: Warning - {compilation_errors} patterns failed to compile")
            
            # Debug: List some loaded patterns for verification
            if cache["positive"]:
                print("ConfigRouter: Sample loaded patterns:")
                for p in cache["positive"][:5]:  # Show first 5
                    print(f"  - {p['intent']} (priority {p['priority']}): {p['raw_pattern'][:60]}...")
            
        except Exception as e:
            print(f"ConfigRouter: Error loading config: {e}")
            import traceback
            traceback.print_exc()
            self._cache = {}
            self._cache_version = None
    
    def _compile_pattern(self, pattern: str) -> Optional[re.Pattern]:
        """Compile regex pattern with error handling"""
        try:
            # Ensure pattern is a string
            if not isinstance(pattern, str):
                print(f"ConfigRouter: Pattern is not a string: {type(pattern)}")
                return None
            
            # Compile with IGNORECASE flag
            compiled = re.compile(pattern, re.IGNORECASE)
            return compiled
            
        except re.error as e:
            print(f"ConfigRouter: Invalid regex pattern '{pattern[:50]}...': {e}")
            return None
        except Exception as e:
            print(f"ConfigRouter: Unexpected error compiling pattern '{pattern[:50]}...': {e}")
            return None
    
    def _apply_synonyms(self, message: str, school_id: Optional[str]) -> str:
        """Apply synonym replacements to normalize message"""
        normalized = message
        
        for synonym in self._cache.get("synonyms", []):
            # Check school scope
            if synonym["scope_school_id"] and synonym["scope_school_id"] != school_id:
                continue
            
            try:
                if synonym["pattern"].search(normalized):
                    # For synonyms, the "intent" field contains the replacement text
                    old_normalized = normalized
                    normalized = synonym["pattern"].sub(synonym["intent"], normalized)
                    if old_normalized != normalized:
                        print(f"ConfigRouter: Applied synonym: '{old_normalized}' -> '{normalized}'")
            except Exception as e:
                print(f"ConfigRouter: Error applying synonym: {e}")
        
        return normalized
    
    def _find_best_pattern(self, message: str, school_id: Optional[str]) -> Optional[Dict]:
        """Find the best matching positive pattern"""
        matches = []
        
        # Debug: Track what patterns we're checking
        patterns_checked = 0
        patterns_skipped_scope = 0
        
        positive_patterns = self._cache.get("positive", [])
        print(f"ConfigRouter: Checking {len(positive_patterns)} positive patterns...")
        
        for pattern in positive_patterns:
            patterns_checked += 1
            
            # Check school scope
            if pattern["scope_school_id"] and pattern["scope_school_id"] != school_id:
                patterns_skipped_scope += 1
                continue
            
            # Debug: Show pattern being checked (for high-priority or relevant patterns)
            if pattern["priority"] >= 100 or "student" in pattern["intent"]:
                print(f"  Checking [{pattern['priority']}] {pattern['intent']}: {pattern['raw_pattern'][:50]}...")
            
            try:
                match = pattern["pattern"].search(message)
                if match:
                    # Calculate confidence based on match length and priority
                    match_length = len(match.group(0))
                    message_length = len(message)
                    coverage = match_length / message_length if message_length > 0 else 0
                    
                    # Combine coverage and priority for scoring
                    priority_score = pattern["priority"] / 1000.0  # Normalize priority (assuming max 1000)
                    confidence = (coverage * 0.7) + (priority_score * 0.3)
                    confidence = min(1.0, confidence)  # Cap at 1.0
                    
                    print(f"    ✓ MATCHED! Coverage: {coverage:.2f}, Priority: {pattern['priority']}, Confidence: {confidence:.2f}")
                    print(f"      Match text: '{match.group(0)}'")
                    
                    matches.append({
                        **pattern,
                        "confidence": confidence,
                        "match_length": match_length,
                        "coverage": coverage
                    })
            except Exception as e:
                print(f"  Error testing pattern {pattern['intent']}: {e}")
        
        print(f"ConfigRouter: Checked {patterns_checked} patterns ({patterns_skipped_scope} skipped for school scope)")
        print(f"ConfigRouter: Found {len(matches)} matching patterns")
        
        if not matches:
            return None
        
        # Sort by confidence (desc), then priority (desc), then match length (desc)
        matches.sort(key=lambda x: (-x["confidence"], -x["priority"], -x["match_length"]))
        
        # Show top matches
        print(f"ConfigRouter: Top matches:")
        for i, m in enumerate(matches[:3]):
            print(f"  {i+1}. {m['intent']} (confidence: {m['confidence']:.3f}, priority: {m['priority']})")
        
        return matches[0]
    
    def _has_negative_match(self, message: str, handler: str, school_id: Optional[str]) -> bool:
        """Check if message matches any negative patterns for this handler"""
        negative_patterns = self._cache.get("negative", [])
        
        for pattern in negative_patterns:
            # Only check negative patterns for the same handler
            if pattern["handler"] != handler:
                continue
            
            # Check school scope
            if pattern["scope_school_id"] and pattern["scope_school_id"] != school_id:
                continue
            
            try:
                if pattern["pattern"].search(message):
                    print(f"ConfigRouter: Negative pattern matched: {pattern['raw_pattern'][:50]}...")
                    return True
            except Exception as e:
                print(f"ConfigRouter: Error checking negative pattern: {e}")
        
        return False
    
    def _extract_entities(self, message: str, pattern_match: Dict) -> Dict[str, Any]:
        """Extract entities from message using pattern groups"""
        entities = {}
        
        try:
            # Re-run the pattern to get groups
            match = pattern_match["pattern"].search(message)
            if match and match.groups():
                # Get named groups if available
                if match.groupdict():
                    entities.update(match.groupdict())
                    print(f"ConfigRouter: Extracted named groups: {entities}")
                
                # Also try to extract common entities with heuristics
                groups = match.groups()
                for i, group in enumerate(groups):
                    if group and group not in entities.values():
                        # Check if it looks like an admission number
                        if re.match(r'^\d{3,7}$', group):
                            entities["admission_no"] = group
                        # Check if it looks like a name (2+ words with letters)
                        elif re.match(r'^[a-zA-Z\s]{3,}$', group) and ' ' in group:
                            entities["student_name"] = group.strip()
                        # Check if it looks like a class name
                        elif re.match(r'^(Grade|Form|Class|PP[12]|pp[12])\s*\d*', group, re.IGNORECASE):
                            entities["class_name"] = group.strip()
            
            # Additional entity extraction from the full message
            # Look for common patterns even if not captured by groups
            
            # Extract numbers that might be counts or IDs
            numbers = re.findall(r'\b\d+\b', message)
            if numbers and "admission_no" not in entities:
                for num in numbers:
                    if 100 <= int(num) <= 9999999:  # Likely admission number range
                        entities["admission_no"] = num
                        break
            
        except Exception as e:
            print(f"ConfigRouter: Error extracting entities: {e}")
        
        return entities
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get statistics about current cache"""
        if not self._cache:
            return {"status": "empty", "version": None}
        
        return {
            "status": "loaded",
            "version": self._cache_version,
            "positive_patterns": len(self._cache.get("positive", [])),
            "negative_patterns": len(self._cache.get("negative", [])),
            "synonyms": len(self._cache.get("synonyms", []))
        }
    
    def test_pattern(self, message: str, pattern_str: str) -> bool:
        """Test if a pattern matches a message (for debugging)"""
        try:
            pattern = re.compile(pattern_str, re.IGNORECASE)
            match = pattern.search(message.lower())
            return match is not None
        except Exception as e:
            print(f"ConfigRouter: Error testing pattern: {e}")
            return False
    
    def list_patterns_for_handler(self, handler: str) -> List[Dict]:
        """List all patterns for a specific handler (for debugging)"""
        patterns = []
        for pattern in self._cache.get("positive", []):
            if pattern["handler"] == handler:
                patterns.append({
                    "intent": pattern["intent"],
                    "pattern": pattern["raw_pattern"],
                    "priority": pattern["priority"]
                })
        return patterns