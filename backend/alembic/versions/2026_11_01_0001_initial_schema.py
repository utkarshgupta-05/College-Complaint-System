"""Initial schema for complaints, users, predictions, priorities, duplicates, and audits

Revision ID: 0001_initial_schema
Revises: None
Create Date: 2026-11-01 02:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = '0001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('username', sa.String(length=64), nullable=False),
        sa.Column('email', sa.String(length=128), nullable=False),
        sa.Column('hashed_password', sa.String(length=256), nullable=False),
        sa.Column('full_name', sa.String(length=128), nullable=True),
        sa.Column('role', sa.String(length=32), nullable=False),
        sa.Column('department', sa.String(length=64), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # Complaints table
    op.create_table(
        'complaints',
        sa.Column('id', sa.String(length=64), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('complaint_text', sa.Text(), nullable=False),
        sa.Column('location', sa.String(length=128), nullable=True),
        sa.Column('student_dept', sa.String(length=64), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_complaints_id'), 'complaints', ['id'], unique=False)
    op.create_index(op.f('ix_complaints_user_id'), 'complaints', ['user_id'], unique=False)

    # Predictions table
    op.create_table(
        'complaint_predictions',
        sa.Column('complaint_id', sa.String(length=64), nullable=False),
        sa.Column('predicted_category', sa.String(length=16), nullable=False),
        sa.Column('category_name', sa.String(length=64), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('low_confidence', sa.Boolean(), nullable=False),
        sa.Column('needs_human_review', sa.Boolean(), nullable=False),
        sa.Column('all_scores_json', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ),
        sa.PrimaryKeyConstraint('complaint_id'),
    )

    # Priorities table
    op.create_table(
        'complaint_priorities',
        sa.Column('complaint_id', sa.String(length=64), nullable=False),
        sa.Column('score', sa.Float(), nullable=False),
        sa.Column('suggested_priority', sa.String(length=32), nullable=False),
        sa.Column('final_priority', sa.String(length=32), nullable=False),
        sa.Column('safety_flag', sa.Boolean(), nullable=False),
        sa.Column('safety_override', sa.Boolean(), nullable=False),
        sa.Column('needs_human_review', sa.Boolean(), nullable=False),
        sa.Column('signals_json', sa.Text(), nullable=True),
        sa.Column('explanation', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ),
        sa.PrimaryKeyConstraint('complaint_id'),
    )

    # Duplicate suggestions table
    op.create_table(
        'duplicate_suggestions',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('complaint_id', sa.String(length=64), nullable=False),
        sa.Column('candidate_id', sa.String(length=64), nullable=False),
        sa.Column('similarity_score', sa.Float(), nullable=False),
        sa.Column('similarity_level', sa.String(length=32), nullable=False),
        sa.Column('candidate_text', sa.Text(), nullable=False),
        sa.Column('candidate_category', sa.String(length=64), nullable=True),
        sa.Column('candidate_location', sa.String(length=128), nullable=True),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_duplicate_suggestions_complaint_id'), 'duplicate_suggestions', ['complaint_id'], unique=False)

    # Priority override audits table
    op.create_table(
        'priority_override_audits',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('complaint_id', sa.String(length=64), nullable=False),
        sa.Column('staff_id', sa.Integer(), nullable=False),
        sa.Column('staff_username', sa.String(length=64), nullable=False),
        sa.Column('original_priority', sa.String(length=32), nullable=False),
        sa.Column('override_priority', sa.String(length=32), nullable=False),
        sa.Column('reason', sa.Text(), nullable=False),
        sa.Column('timestamp', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['complaint_id'], ['complaints.id'], ),
        sa.ForeignKeyConstraint(['staff_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_priority_override_audits_complaint_id'), 'priority_override_audits', ['complaint_id'], unique=False)


def downgrade() -> None:
    op.drop_table('priority_override_audits')
    op.drop_table('duplicate_suggestions')
    op.drop_table('complaint_priorities')
    op.drop_table('complaint_predictions')
    op.drop_table('complaints')
    op.drop_table('users')

