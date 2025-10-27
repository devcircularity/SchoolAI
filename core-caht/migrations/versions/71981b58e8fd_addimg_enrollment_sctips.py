"""Adding Enrollment Scripts - FIXED

Revision ID: 71981b58e8fd
Revises: e89679de8cfa
Create Date: 2025-08-20 09:52:28.205502

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '71981b58e8fd'
down_revision: Union[str, Sequence[str], None] = 'e89679de8cfa'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Instead of dropping tables, let's ensure they exist and are properly structured
    
    # Create academic_years table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS academic_years (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            year INTEGER NOT NULL,
            title VARCHAR(64) NOT NULL,
            state VARCHAR(16) NOT NULL DEFAULT 'DRAFT',
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT ck_academic_year_state CHECK (state IN ('DRAFT','ACTIVE','CLOSED')),
            CONSTRAINT uq_academic_year_per_school UNIQUE (school_id, year)
        );
    """)
    
    # Create academic_terms table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS academic_terms (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            year_id UUID NOT NULL REFERENCES academic_years(id) ON DELETE CASCADE,
            term INTEGER NOT NULL,
            title VARCHAR(48) NOT NULL,
            state VARCHAR(16) NOT NULL DEFAULT 'PLANNED',
            start_date DATE,
            end_date DATE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT ck_academic_term_state CHECK (state IN ('PLANNED','ACTIVE','CLOSED')),
            CONSTRAINT uq_term_per_year UNIQUE (school_id, year_id, term)
        );
    """)
    
    # Create enrollments table with proper structure
    op.execute("""
        CREATE TABLE IF NOT EXISTS enrollments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            student_id UUID NOT NULL REFERENCES students(id) ON DELETE CASCADE,
            class_id UUID NOT NULL REFERENCES classes(id) ON DELETE RESTRICT,
            term_id UUID NOT NULL REFERENCES academic_terms(id) ON DELETE CASCADE,
            status VARCHAR(16) NOT NULL DEFAULT 'ENROLLED',
            enrolled_date DATE NOT NULL DEFAULT CURRENT_DATE,
            withdrawn_date DATE,
            invoice_generated BOOLEAN NOT NULL DEFAULT FALSE,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT ck_enrollment_status CHECK (status IN ('ENROLLED','TRANSFERRED_OUT','SUSPENDED','DROPPED','GRADUATED')),
            CONSTRAINT uq_enrollment_student_term UNIQUE (school_id, student_id, term_id)
        );
    """)
    
    # Create enrollment_status_events table
    op.execute("""
        CREATE TABLE IF NOT EXISTS enrollment_status_events (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            school_id UUID NOT NULL,
            enrollment_id UUID NOT NULL REFERENCES enrollments(id) ON DELETE CASCADE,
            prev_status VARCHAR(16),
            new_status VARCHAR(16) NOT NULL,
            reason VARCHAR(256),
            event_date DATE NOT NULL,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT ck_enrollment_event_status CHECK (new_status IN ('ENROLLED','TRANSFERRED_OUT','SUSPENDED','DROPPED','GRADUATED'))
        );
    """)
    
    # Create indexes
    op.execute("CREATE INDEX IF NOT EXISTS ix_academic_years_school_id ON academic_years(school_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_academic_terms_school_id ON academic_terms(school_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_academic_terms_year_id ON academic_terms(year_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_school_id ON enrollments(school_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_student_id ON enrollments(student_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_class_id ON enrollments(class_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollments_term_id ON enrollments(term_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollment_status_events_school_id ON enrollment_status_events(school_id);")
    op.execute("CREATE INDEX IF NOT EXISTS ix_enrollment_status_events_enrollment_id ON enrollment_status_events(enrollment_id);")
    
    # Enable RLS if not already enabled
    op.execute("ALTER TABLE academic_years ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE academic_terms ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE enrollments ENABLE ROW LEVEL SECURITY;")
    op.execute("ALTER TABLE enrollment_status_events ENABLE ROW LEVEL SECURITY;")
    
    # Create RLS policies
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'academic_years_school_isolation') THEN
                CREATE POLICY academic_years_school_isolation ON academic_years
                    FOR ALL USING (school_id::text = current_setting('app.current_school_id', true));
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'academic_terms_school_isolation') THEN
                CREATE POLICY academic_terms_school_isolation ON academic_terms
                    FOR ALL USING (school_id::text = current_setting('app.current_school_id', true));
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'enrollments_school_isolation') THEN
                CREATE POLICY enrollments_school_isolation ON enrollments
                    FOR ALL USING (school_id::text = current_setting('app.current_school_id', true));
            END IF;
        END $$;
    """)
    
    op.execute("""
        DO $$
        BEGIN
            IF NOT EXISTS (SELECT 1 FROM pg_policies WHERE policyname = 'enrollment_status_events_school_isolation') THEN
                CREATE POLICY enrollment_status_events_school_isolation ON enrollment_status_events
                    FOR ALL USING (school_id::text = current_setting('app.current_school_id', true));
            END IF;
        END $$;
    """)


def downgrade() -> None:
    """Downgrade schema."""
    # Only drop if you really want to remove these tables
    op.execute("DROP TABLE IF EXISTS enrollment_status_events CASCADE;")
    op.execute("DROP TABLE IF EXISTS enrollments CASCADE;")
    op.execute("DROP TABLE IF EXISTS academic_terms CASCADE;")
    op.execute("DROP TABLE IF EXISTS academic_years CASCADE;")