"""Add indexes on processing_logs.document_id, status, processed_at.

Revision ID: 002
Revises: 001
Create Date: 2026-04-21

"""

from alembic import op
from sqlalchemy import inspect

revision = "002"
down_revision = "6108ef3356a6"
branch_labels = None
depends_on = None


def upgrade():
    existing = {ix["name"] for ix in inspect(op.get_bind()).get_indexes("processing_logs")}
    for name, col in (
        ("ix_log_document_id", "document_id"),
        ("ix_log_status", "status"),
        ("ix_log_processed_at", "processed_at"),
    ):
        if name not in existing:
            op.create_index(name, "processing_logs", [col])


def downgrade():
    op.drop_index("ix_log_document_id", table_name="processing_logs")
    op.drop_index("ix_log_status", table_name="processing_logs")
    op.drop_index("ix_log_processed_at", table_name="processing_logs")
