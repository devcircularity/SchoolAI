# app/services/config_loader.py
"""
Configuration loader service for dynamic intent configuration management.
This service handles loading, caching, and reloading of intent configurations.
"""
import time
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from sqlalchemy.orm import Session
from datetime import datetime, timedelta

from app.models.intent_config import IntentConfigVersion, IntentPattern, PromptTemplate, ConfigStatus, PatternKind
from app.core.db import get_db


@dataclass
class ConfigCache:
    """In-memory cache for intent configuration"""
    version_id: str
    version_name: str
    loaded_at: datetime
    patterns: Dict[str, List[Dict[str, Any]]]  # positive, negative, synonyms
    templates: Dict[str, Dict[str, Any]]  # keyed by handler_intent or handler_type
    stats: Dict[str, int]


class ConfigLoader:
    """Service for loading and managing intent configuration cache"""
    
    def __init__(self):
        self._cache: Optional[ConfigCache] = None
        self._last_check: Optional[datetime] = None
        self._check_interval = timedelta(minutes=5)  # Check for updates every 5 minutes
        
    def get_active_config(self, db: Session) -> Optional[ConfigCache]:
        """Get the active configuration, loading if necessary"""
        # Check if we need to reload
        if self._should_reload(db):
            self.reload_active(db)
        
        return self._cache
    
    def reload_active(self, db: Session) -> bool:
        """Force reload the active configuration from database"""
        try:
            print("ConfigLoader: Reloading active configuration...")
            
            # Get active version
            active_version = db.query(IntentConfigVersion)\
                .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
                .first()
            
            if not active_version:
                print("ConfigLoader: No active configuration version found")
                self._cache = None
                return False
            
            # Load patterns
            patterns = self._load_patterns(db, active_version.id)
            
            # Load templates
            templates = self._load_templates(db, active_version.id)
            
            # Create cache
            self._cache = ConfigCache(
                version_id=active_version.id,
                version_name=active_version.name,
                loaded_at=datetime.utcnow(),
                patterns=patterns,
                templates=templates,
                stats={
                    "total_patterns": sum(len(p) for p in patterns.values()),
                    "total_templates": len(templates),
                    "positive_patterns": len(patterns.get("positive", [])),
                    "negative_patterns": len(patterns.get("negative", [])),
                    "synonyms": len(patterns.get("synonyms", []))
                }
            )
            
            self._last_check = datetime.utcnow()
            
            print(f"ConfigLoader: Successfully loaded '{active_version.name}' with {self._cache.stats['total_patterns']} patterns and {self._cache.stats['total_templates']} templates")
            return True
            
        except Exception as e:
            print(f"ConfigLoader: Error reloading configuration: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def _should_reload(self, db: Session) -> bool:
        """Check if configuration should be reloaded"""
        # Always reload if no cache
        if not self._cache:
            return True
        
        # Check periodically for version changes
        now = datetime.utcnow()
        if not self._last_check or (now - self._last_check) > self._check_interval:
            current_version = db.query(IntentConfigVersion)\
                .filter(IntentConfigVersion.status == ConfigStatus.ACTIVE)\
                .first()
            
            current_version_id = current_version.id if current_version else None
            self._last_check = now
            
            if current_version_id != self._cache.version_id:
                print(f"ConfigLoader: Active version changed from {self._cache.version_id} to {current_version_id}")
                return True
        
        return False
    
    def _load_patterns(self, db: Session, version_id: str) -> Dict[str, List[Dict[str, Any]]]:
        """Load patterns from database"""
        patterns = db.query(IntentPattern)\
            .filter(
                IntentPattern.version_id == version_id,
                IntentPattern.enabled == True
            )\
            .order_by(IntentPattern.priority.desc(), IntentPattern.created_at)\
            .all()
        
        result = {
            "positive": [],
            "negative": [],
            "synonyms": []
        }
        
        for pattern in patterns:
            pattern_data = {
                "id": pattern.id,
                "handler": pattern.handler,
                "intent": pattern.intent,
                "pattern": pattern.pattern,
                "priority": pattern.priority,
                "scope_school_id": pattern.scope_school_id,
                "created_at": pattern.created_at
            }
            
            if pattern.kind == PatternKind.POSITIVE:
                result["positive"].append(pattern_data)
            elif pattern.kind == PatternKind.NEGATIVE:
                result["negative"].append(pattern_data)
            elif pattern.kind == PatternKind.SYNONYM:
                result["synonyms"].append(pattern_data)
        
        return result
    
    def _load_templates(self, db: Session, version_id: str) -> Dict[str, Dict[str, Any]]:
        """Load prompt templates from database"""
        templates = db.query(PromptTemplate)\
            .filter(
                PromptTemplate.version_id == version_id,
                PromptTemplate.enabled == True
            )\
            .all()
        
        result = {}
        
        for template in templates:
            # Key by handler_intent for specific templates, handler_type for general ones
            if template.intent:
                key = f"{template.handler}_{template.intent}"
            else:
                key = f"{template.handler}_{template.template_type.value}"
            
            result[key] = {
                "id": template.id,
                "handler": template.handler,
                "intent": template.intent,
                "template_type": template.template_type.value,
                "template_text": template.template_text,
                "created_at": template.created_at
            }
        
        return result
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        if not self._cache:
            return {"status": "empty", "version": None}
        
        return {
            "status": "loaded",
            "version_id": self._cache.version_id,
            "version_name": self._cache.version_name,
            "loaded_at": self._cache.loaded_at.isoformat(),
            "stats": self._cache.stats,
            "last_check": self._last_check.isoformat() if self._last_check else None
        }
    
    def get_template(self, handler: str, intent: str = None, template_type: str = None) -> Optional[str]:
        """Get a specific template by handler and intent or type"""
        if not self._cache:
            return None
        
        # Try specific intent first
        if intent:
            key = f"{handler}_{intent}"
            if key in self._cache.templates:
                return self._cache.templates[key]["template_text"]
        
        # Try by type
        if template_type:
            key = f"{handler}_{template_type}"
            if key in self._cache.templates:
                return self._cache.templates[key]["template_text"]
        
        return None
    
    def clear_cache(self):
        """Clear the configuration cache"""
        self._cache = None
        self._last_check = None
        print("ConfigLoader: Cache cleared")


# Global instance
config_loader = ConfigLoader()