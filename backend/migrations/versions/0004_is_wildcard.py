"""add is_wildcard to plan_items

Revision ID: 0004
Revises: 0003
Create Date: 2026-04-23
"""

from alembic import op

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        ALTER TABLE plan_items
        ADD COLUMN is_wildcard BOOLEAN NOT NULL DEFAULT false
    """)
    op.execute("""
        CREATE INDEX idx_items_wildcard
        ON plan_items (category_id)
        WHERE is_wildcard = true
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_items_wildcard")
    op.execute("ALTER TABLE plan_items DROP COLUMN IF EXISTS is_wildcard")
