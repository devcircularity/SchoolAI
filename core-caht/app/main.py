# app/main.py - Complete version with startup intent configuration initialization and new configuration router

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
import logging

from app.api.routers import auth as auth_router
from app.api.routers import schools as schools_router
from app.api.routers.chat import router as chat_router
from app.api.routers import whatsapp as whatsapp_router
from app.api.routers import webhooks as webhooks_router
from app.api.routers import mobile as mobile_router
from app.api.routers import test_file as test_router
from app.api.routers import public as public_router
from app.api.routers.admin.intent_config import router as intent_config_router
from app.api.routers.admin import suggestion_management as suggestion_router
from app.api.routers.admin import tester_queue as tester_router
from app.api.routers.admin import user_management as user_management_router
from app.api.routers.admin import configuration as configuration_router  # New configuration router
from app.api.routers.admin import chat_monitoring as chat_monitoring_router
from app.api.routers.admin import tester_rankings as tester_rankings_router  # ADD THIS LINE
from app.api.routers.admin import school_stats as school_stats_router

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_app() -> FastAPI:
    app = FastAPI(
        title="School Management AI with SMS/WhatsApp and Document Processing", 
        version="0.8.2"  # Updated version for new configuration management
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], 
        allow_credentials=True,
        allow_methods=["*"], 
        allow_headers=["*"],
    )

    # Custom middleware to log requests
    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        if request.url.path.startswith("/api/webhooks/"):
            logger.info(f"Webhook request: {request.method} {request.url.path}")
            logger.info(f"Headers: {dict(request.headers)}")
        elif request.url.path.startswith("/api/test/"):
            logger.info(f"Test request: {request.method} {request.url.path}")
        elif request.url.path.startswith("/api/public/"):
            logger.info(f"Public request: {request.method} {request.url.path}")
        elif request.url.path.startswith("/api/admin/"):
            logger.info(f"Admin request: {request.method} {request.url.path}")
        
        response = await call_next(request)
        return response

    # Startup event handler
    @app.on_event("startup")
    async def startup_event():
        """Initialize services on startup"""
        try:
            print("\n" + "="*60)
            print("🚀 Starting School AI Backend v0.8.2")
            print("="*60)
            
            # Initialize database connection and intent configuration
            from app.services.config_router import ConfigRouter
            from app.core.db import get_db
            from app.models.intent_config import IntentConfigVersion
            
            print("📊 Initializing intent configuration...")
            
            try:
                db = next(get_db())
                
                # Check for active configuration first
                active_version = db.query(IntentConfigVersion).filter(
                    IntentConfigVersion.status == 'active'
                ).first()
                
                if not active_version:
                    print("❌ No active intent configuration found!")
                    print("   This means the chat system will not work properly.")
                    print("   Please run: python scripts/seed_intent_config.py")
                    print("   Or use the admin interface to activate a configuration.")
                else:
                    print(f"✅ Found active config: {active_version.name}")
                    
                    # Initialize ConfigRouter and force load
                    config_router = ConfigRouter(db)
                    config_router.reload_config()
                    
                    # Get and display cache stats
                    cache_stats = config_router.get_cache_stats()
                    if cache_stats["status"] == "loaded":
                        print(f"✅ Intent configuration loaded successfully:")
                        print(f"   - Version: {active_version.name}")
                        print(f"   - Positive patterns: {cache_stats['positive_patterns']}")
                        print(f"   - Negative patterns: {cache_stats['negative_patterns']}")
                        print(f"   - Synonyms: {cache_stats['synonyms']}")
                        
                        # Test a few sample patterns
                        print("\n🧪 Testing sample patterns:")
                        test_messages = [
                            "how many students do we have?",
                            "school overview", 
                            "create new student",
                            "generate invoice for all students"
                        ]
                        
                        for test_msg in test_messages:
                            result = config_router.route(test_msg)
                            if result:
                                print(f"   ✅ '{test_msg}' → {result.intent} (confidence: {result.confidence:.3f})")
                            else:
                                print(f"   ❌ '{test_msg}' → No match")
                        
                    else:
                        print("⚠️  Warning: Intent configuration failed to load properly")
                        print(f"   Cache status: {cache_stats}")
                
                db.close()
                
            except Exception as e:
                print(f"❌ Error initializing intent configuration: {e}")
                import traceback
                traceback.print_exc()
            
            # Test other critical services
            print("\n🔧 Testing critical services...")
            
            # Test OCR service
            try:
                import requests
                ocr_response = requests.get("https://ocr.olaji.co/health", timeout=5)
                if ocr_response.status_code == 200:
                    print("✅ OCR service: Available")
                else:
                    print("⚠️  OCR service: Unhealthy")
            except:
                print("❌ OCR service: Unavailable")
            
            # Test Ollama service
            try:
                from app.services.ollama_service import OllamaService
                ollama_service = OllamaService()
                is_healthy = ollama_service.health_check_sync()
                if is_healthy:
                    print(f"✅ Ollama service: Available ({ollama_service.model})")
                else:
                    print("⚠️  Ollama service: Unhealthy")
            except Exception as e:
                print(f"❌ Ollama service: Error - {e}")
            
            # Test Cloudinary
            try:
                import cloudinary
                cloudinary.api.ping()
                print("✅ Cloudinary: Available")
            except:
                print("❌ Cloudinary: Unavailable")
            
            print("\n" + "="*60)
            print("🎯 Startup Summary:")
            print("   Chat system ready for processing messages")
            print("   Admin interface available at /api/admin/")
            print("   Configuration management at /api/admin/configuration/")
            print("   Health check available at /services/health")
            print("="*60 + "\n")
            
        except Exception as e:
            print(f"\n❌ Critical startup error: {e}")
            import traceback
            traceback.print_exc()
            print("\n⚠️  Application may not function correctly!")

    # Include routers
    app.include_router(auth_router.router, prefix="/api")
    app.include_router(schools_router.router, prefix="/api")
    app.include_router(chat_router, prefix="/api")
    app.include_router(whatsapp_router.router, prefix="/api")
    app.include_router(webhooks_router.router, prefix="/api/webhooks")
    app.include_router(mobile_router.router, prefix="/api")
    app.include_router(test_router.router, prefix="/api")
    app.include_router(public_router.router)
    app.include_router(intent_config_router, prefix="/api")
    app.include_router(suggestion_router.router, prefix="/api")  
    app.include_router(tester_router.router, prefix="/api")
    app.include_router(user_management_router.router, prefix="/api")
    app.include_router(configuration_router.router, prefix="/api")  # New configuration management router
    app.include_router(chat_monitoring_router.router, prefix="/api")
    app.include_router(tester_rankings_router.router, prefix="/api")  # ADD THIS LINE
    app.include_router(school_stats_router.router, prefix="/api")

    @app.get("/healthz")
    def health():
        return {
            "ok": True, 
            "version": "0.8.2", 
            "features": [
                "chat", 
                "whatsapp", 
                "file_attachments", 
                "ocr", 
                "ai_interpretation",
                "public_chat",
                "modular_admin_intent_config",
                "startup_configuration_init",
                "unified_configuration_management"  # New feature
            ]
        }

    @app.get("/whatsapp/health")
    async def whatsapp_health():
        """Quick health check endpoint for WhatsApp bridge"""
        try:
            from app.services.whatsapp_service import WhatsAppService
            whatsapp_service = WhatsAppService()
            health_check = whatsapp_service.check_bridge_health()
            return {
                "whatsapp_ready": health_check.get("ready", False),
                "error": health_check.get("error")
            }
        except Exception as e:
            return {
                "whatsapp_ready": False,
                "error": str(e)
            }

    @app.get("/intent-config/health")
    async def intent_config_health():
        """Health check for intent configuration system"""
        try:
            from app.services.config_router import ConfigRouter
            from app.core.db import get_db
            
            # Test configuration loading
            db = next(get_db())
            config_router = ConfigRouter(db)
            cache_stats = config_router.get_cache_stats()
            
            # Check if we have an active configuration
            from app.models.intent_config import IntentConfigVersion
            active_version = db.query(IntentConfigVersion)\
                .filter(IntentConfigVersion.status == 'active')\
                .first()
            
            db.close()
            
            return {
                "intent_config_ready": cache_stats["status"] == "loaded",
                "active_version": active_version.name if active_version else None,
                "active_version_id": active_version.id if active_version else None,
                "cache_stats": cache_stats,
                "error": None if cache_stats["status"] == "loaded" else "No active configuration loaded"
            }
        except Exception as e:
            return {
                "intent_config_ready": False,
                "active_version": None,
                "cache_stats": {"status": "error"},
                "error": str(e)
            }

    @app.get("/services/health")
    async def services_health():
        """Combined health check for all services"""
        try:
            from app.services.config_router import ConfigRouter
            from app.core.db import get_db
            import requests
            import cloudinary
            from datetime import datetime
            
            health = {
                "timestamp": datetime.utcnow().isoformat(),
                "overall": "healthy",
                "services": {},
                "version": "0.8.2"
            }
            
            # Test OCR
            try:
                ocr_response = requests.get("https://ocr.olaji.co/health", timeout=5)
                health["services"]["ocr"] = {
                    "status": "healthy" if ocr_response.status_code == 200 else "unhealthy",
                    "response_code": ocr_response.status_code
                }
            except Exception as e:
                health["services"]["ocr"] = {"status": "unhealthy", "error": str(e)}
            
            # Test Ollama
            try:
                from app.services.ollama_service import OllamaService
                ollama_service = OllamaService()
                is_healthy = ollama_service.health_check_sync()
                health["services"]["ollama"] = {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "model": ollama_service.model,
                    "base_url": ollama_service.base_url
                }
            except Exception as e:
                health["services"]["ollama"] = {"status": "unhealthy", "error": str(e)}
            
            # Test Cloudinary
            try:
                cloudinary.api.ping()
                health["services"]["cloudinary"] = {"status": "healthy"}
            except Exception as e:
                health["services"]["cloudinary"] = {"status": "unhealthy", "error": str(e)}
            
            # Test Intent Configuration System
            try:
                db = next(get_db())
                config_router = ConfigRouter(db)
                cache_stats = config_router.get_cache_stats()
                
                from app.models.intent_config import IntentConfigVersion
                active_version = db.query(IntentConfigVersion)\
                    .filter(IntentConfigVersion.status == 'active')\
                    .first()
                
                health["services"]["intent_config"] = {
                    "status": "healthy" if cache_stats["status"] == "loaded" else "unhealthy",
                    "active_version": active_version.name if active_version else None,
                    "patterns_loaded": cache_stats.get("positive_patterns", 0),
                    "cache_status": cache_stats["status"]
                }
                
                db.close()
            except Exception as e:
                health["services"]["intent_config"] = {"status": "unhealthy", "error": str(e)}
            
            # Test Database
            try:
                db = next(get_db())
                # Simple query to test DB connection
                result = db.execute("SELECT 1 as test").fetchone()
                health["services"]["database"] = {
                    "status": "healthy" if result else "unhealthy"
                }
                db.close()
            except Exception as e:
                health["services"]["database"] = {"status": "unhealthy", "error": str(e)}
            
            # Test Configuration Management endpoints
            try:
                from app.api.routers.admin.configuration import get_configuration_overview
                # This is a basic test to ensure the configuration router is working
                health["services"]["configuration_management"] = {"status": "healthy"}
            except Exception as e:
                health["services"]["configuration_management"] = {"status": "unhealthy", "error": str(e)}
            
            # Set overall status
            unhealthy_services = [
                name for name, service in health["services"].items() 
                if service["status"] != "healthy"
            ]
            
            if unhealthy_services:
                health["overall"] = "degraded"
                health["unhealthy_services"] = unhealthy_services
                health["healthy_count"] = len(health["services"]) - len(unhealthy_services)
                health["total_services"] = len(health["services"])
            else:
                health["healthy_count"] = len(health["services"])
                health["total_services"] = len(health["services"])
            
            return health
            
        except Exception as e:
            from datetime import datetime
            return {
                "overall": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "version": "0.8.2"
            }

    return app

app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)