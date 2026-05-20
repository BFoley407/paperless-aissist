"""Add sample metadata to prompts.

Revision ID: 003
Revises: 002
Create Date: 2026-05-20

"""

from alembic import op
import sqlalchemy as sa

revision = "003"
down_revision = "002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("prompts", sa.Column("sample_key", sa.String(), nullable=True))
    op.add_column("prompts", sa.Column("sample_hash", sa.String(), nullable=True))
    op.add_column("prompts", sa.Column("sample_updated_at", sa.DateTime(), nullable=True))
    op.create_index("ix_prompts_sample_key", "prompts", ["sample_key"])


def downgrade():
    op.drop_index("ix_prompts_sample_key", table_name="prompts")
    op.drop_column("prompts", "sample_updated_at")
    op.drop_column("prompts", "sample_hash")
    op.drop_column("prompts", "sample_key")
