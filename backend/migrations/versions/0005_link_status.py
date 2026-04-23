"""add link_status to plan_items

Revision ID: 0005
Revises: 0004
Create Date: 2026-04-23
"""

from alembic import op

revision = "0005"
down_revision = "0004"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute(
        "CREATE TYPE link_status AS ENUM ('unchecked','valid','broken','repaired')"
    )
    op.execute("""
        ALTER TABLE plan_items
        ADD COLUMN link_status link_status NOT NULL DEFAULT 'unchecked'
    """)
    op.execute("""
        CREATE INDEX idx_items_broken
        ON plan_items (id)
        WHERE link_status = 'broken'
    """)


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS idx_items_broken")
    op.execute("ALTER TABLE plan_items DROP COLUMN IF EXISTS link_status")
    op.execute("DROP TYPE IF EXISTS link_status")
