"""create session_profiles table

Revision ID: 0003
Revises: 0002
Create Date: 2026-04-23
"""

from alembic import op

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("""
        CREATE TABLE session_profiles (
            session_id    UUID PRIMARY KEY
                          REFERENCES sessions(id) ON DELETE CASCADE,
            nivel         nivel_conhecimento,
            orcamento     orcamento_pref,
            idioma        idioma_pref,
            rotina        rotina_pref,
            motivacao     motivacao_pref,
            atualizado_em TIMESTAMP NOT NULL DEFAULT (NOW() AT TIME ZONE 'utc')
        )
    """)
    op.execute("ALTER TABLE session_profiles ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY session_profiles_isolation ON session_profiles
        USING (session_id = current_setting('app.session_id', true)::uuid)
    """)


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS session_profiles CASCADE")
