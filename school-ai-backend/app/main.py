# app/main.py
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routers import auth as auth_router
from app.api.routers import schools as schools_router
from app.api.routers import classes as classes_router
from app.api.routers import guardians as guardians_router
from app.api.routers import students as students_router
from app.api.routers import fees as fees_router
from app.api.routers import academics as academic_router  # NEW
from app.api.routers import invoices as invoices_router
from app.api.routers import payments as payments_router
from app.api.routers import notifications as notifications_router


def create_app() -> FastAPI:
    app = FastAPI(title="School Management AI (Alpha+)", version="0.2.0")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"], allow_credentials=True,
        allow_methods=["*"], allow_headers=["*"],
    )

    # Debug: Check if auth_router has a router attribute
    print(f"🔍 Debug: auth_router module: {auth_router}")
    print(f"🔍 Debug: has router attr: {hasattr(auth_router, 'router')}")
    if hasattr(auth_router, 'router'):
        print(f"🔍 Debug: router object: {auth_router.router}")
        print(f"🔍 Debug: router routes: {auth_router.router.routes}")

    # Core routers with /api prefix
    app.include_router(auth_router.router, prefix="/api")
    app.include_router(schools_router.router, prefix="/api")
    app.include_router(classes_router.router, prefix="/api")
    app.include_router(guardians_router.router, prefix="/api")
    app.include_router(students_router.router, prefix="/api")
    
    # Academic core (NEW)
    app.include_router(academic_router.router, prefix="/api")
    
    # Financial
    app.include_router(fees_router.router, prefix="/api")
    app.include_router(invoices_router.router, prefix="/api")
    app.include_router(payments_router.router, prefix="/api")
    
    # Communications
    app.include_router(notifications_router.router, prefix="/api")

    # Debug: Print all registered routes after adding routers
    print("\n🚀 All registered routes:")
    for route in app.routes:
        if hasattr(route, 'methods') and hasattr(route, 'path'):
            print(f"  {list(route.methods)} {route.path}")
    print()

    @app.get("/healthz")
    def health():
        return {"ok": True}

    return app

app = create_app()