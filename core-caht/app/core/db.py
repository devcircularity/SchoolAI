# app/core/db.py - Fixed database configuration without circular imports
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

# Import Base independently - no circular import
from app.models.base import Base

engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)

@contextmanager
def db_session():
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except:
        db.rollback()
        raise
    finally:
        db.close()

# FastAPI dependency
def get_db():
    with db_session() as db:
        yield db

def set_rls_context(db, *, user_id: str | None = None, school_id: str | None = None):
    """Set RLS context variables for the current transaction"""
    if user_id:
        user_id_str = str(user_id)
        db.execute(
            text("SELECT set_config('app.current_user_id', :v, true)"),
            {"v": user_id_str},
        )
    if school_id:
        school_id_str = str(school_id)
        db.execute(
            text("SELECT set_config('app.current_school_id', :v, true)"),
            {"v": school_id_str},
        )

def create_tables():
    """Create all tables in the database"""
    Base.metadata.create_all(bind=engine)