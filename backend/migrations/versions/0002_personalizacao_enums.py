"""add personalizacao enums

Revision ID: 0002
Revises: 0001
Create Date: 2026-04-23
"""

from alembic import op

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("CREATE TYPE nivel_conhecimento AS ENUM ('zero','basico','intermediario','avancado')")
    op.execute("CREATE TYPE orcamento_pref AS ENUM ('gratuito','aberto_a_investimentos')")
    op.execute(
        "CREATE TYPE idioma_pref AS ENUM "
        "('apenas_portugues','aceita_ingles','aceita_outros')"
    )
    op.execute(
        "CREATE TYPE rotina_pref AS ENUM "
        "('prefere_ler','prefere_ouvir','prefere_assistir')"
    )
    op.execute(
        "CREATE TYPE motivacao_pref AS ENUM "
        "('carreira','hobby','curiosidade','repertorio_social')"
    )


def downgrade() -> None:
    op.execute("DROP TYPE IF EXISTS motivacao_pref")
    op.execute("DROP TYPE IF EXISTS rotina_pref")
    op.execute("DROP TYPE IF EXISTS idioma_pref")
    op.execute("DROP TYPE IF EXISTS orcamento_pref")
    op.execute("DROP TYPE IF EXISTS nivel_conhecimento")
