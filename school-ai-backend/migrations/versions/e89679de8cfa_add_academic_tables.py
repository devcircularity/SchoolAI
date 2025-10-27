"""add academic tables

Revision ID: e89679de8cfa
Revises: 5b36301167e6
Create Date: 2025-08-19 11:55:05.360304

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e89679de8cfa'
down_revision: Union[str, Sequence[str], None] = '5b36301167e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None



def upgrade() -> None:
    """Create academic tables."""
    
    # Create academic_years table
    op.create_table('academic_years',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=64), nullable=False),
        sa.Column('state', sa.String(length=16), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("state IN ('DRAFT','ACTIVE','CLOSED')", name='ck_academic_year_state'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_academic_year_per_school', 'academic_years', ['school_id', 'year'], unique=True)
    op.create_index(op.f('ix_academic_years_school_id'), 'academic_years', ['school_id'], unique=False)

    # Create academic_terms table
    op.create_table('academic_terms',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('year_id', sa.UUID(), nullable=False),
        sa.Column('term', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(length=48), nullable=False),
        sa.Column('state', sa.String(length=16), nullable=False),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("state IN ('PLANNED','ACTIVE','CLOSED')", name='ck_academic_term_state'),
        sa.ForeignKeyConstraint(['year_id'], ['academic_years.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_term_per_year', 'academic_terms', ['school_id', 'year_id', 'term'], unique=True)
    op.create_index(op.f('ix_academic_terms_school_id'), 'academic_terms', ['school_id'], unique=False)
    op.create_index(op.f('ix_academic_terms_year_id'), 'academic_terms', ['year_id'], unique=False)

    # Create enrollments table
    op.create_table('enrollments',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('student_id', sa.UUID(), nullable=False),
        sa.Column('class_id', sa.UUID(), nullable=False),
        sa.Column('term_id', sa.UUID(), nullable=False),
        sa.Column('status', sa.String(length=16), nullable=False),
        sa.Column('joined_on', sa.Date(), nullable=True),
        sa.Column('left_on', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('ENROLLED','TRANSFERRED_OUT','SUSPENDED','DROPPED','GRADUATED')", name='ck_enrollment_status'),
        sa.ForeignKeyConstraint(['student_id'], ['students.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['class_id'], ['classes.id'], ondelete='RESTRICT'),
        sa.ForeignKeyConstraint(['term_id'], ['academic_terms.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('uq_enrollment_student_term', 'enrollments', ['school_id', 'student_id', 'term_id'], unique=True)
    op.create_index(op.f('ix_enrollments_school_id'), 'enrollments', ['school_id'], unique=False)
    op.create_index(op.f('ix_enrollments_student_id'), 'enrollments', ['student_id'], unique=False)
    op.create_index(op.f('ix_enrollments_class_id'), 'enrollments', ['class_id'], unique=False)
    op.create_index(op.f('ix_enrollments_term_id'), 'enrollments', ['term_id'], unique=False)

    # Create enrollment_status_events table
    op.create_table('enrollment_status_events',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('school_id', sa.UUID(), nullable=False),
        sa.Column('enrollment_id', sa.UUID(), nullable=False),
        sa.Column('prev_status', sa.String(length=16), nullable=True),
        sa.Column('new_status', sa.String(length=16), nullable=False),
        sa.Column('reason', sa.String(length=256), nullable=True),
        sa.Column('event_date', sa.Date(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint("new_status IN ('ENROLLED','TRANSFERRED_OUT','SUSPENDED','DROPPED','GRADUATED')", name='ck_enrollment_event_status'),
        sa.ForeignKeyConstraint(['enrollment_id'], ['enrollments.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_enrollment_events_enrollment', 'enrollment_status_events', ['school_id', 'enrollment_id', 'event_date'], unique=False)
    op.create_index(op.f('ix_enrollment_status_events_school_id'), 'enrollment_status_events', ['school_id'], unique=False)
    op.create_index(op.f('ix_enrollment_status_events_enrollment_id'), 'enrollment_status_events', ['enrollment_id'], unique=False)


def downgrade() -> None:
    """Drop academic tables."""
    op.drop_table('enrollment_status_events')
    op.drop_table('enrollments')
    op.drop_table('academic_terms')
    op.drop_table('academic_years')