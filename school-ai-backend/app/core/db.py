# app/core/db.py - Fixed RLS context function
from contextlib import contextmanager
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

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

def set_rls_context(db, *, user_id: str | None, school_id: str | None):
    """
    Set RLS context variables for the current transaction.
    
    Note: set_config expects text values, so we ensure all values are converted to strings.
    """
    # Use set_config(name, value, is_local := true) so it's transaction-local and parameterized
    if user_id:
        # Ensure user_id is converted to string
        user_id_str = str(user_id)
        db.execute(
            text("SELECT set_config('app.current_user_id', :v, true)"),
            {"v": user_id_str},
        )
    if school_id:
        # Ensure school_id is converted to string
        school_id_str = str(school_id)
        db.execute(
            text("SELECT set_config('app.current_school_id', :v, true)"),
            {"v": school_id_str},
        )