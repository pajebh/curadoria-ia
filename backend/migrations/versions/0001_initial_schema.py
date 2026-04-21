"""initial schema

Revision ID: 0001
Revises:
Create Date: 2026-04-21
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ENUMs
    op.execute("CREATE TYPE plan_status AS ENUM ('pendente','gerando','concluido','erro')")
    op.execute("CREATE TYPE tempo_unidade AS ENUM ('dias','semanas','meses')")
    op.execute(
        "CREATE TYPE categoria_nome AS ENUM "
        "('formal','visual','leitura','audio','experiencias','referencias')"
    )
    op.execute("CREATE TYPE ia_provider AS ENUM ('groq','gemini')")

    # sessions
    op.execute("""
        CREATE TABLE sessions (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            token_hash TEXT NOT NULL UNIQUE,
            created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            last_seen_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            purge_at TIMESTAMPTZ NOT NULL DEFAULT now() + INTERVAL '180 days'
        )
    """)
    op.execute("CREATE INDEX idx_sessions_purge_at ON sessions(purge_at)")

    # plans
    op.execute("""
        CREATE TABLE plans (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            session_id UUID NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
            tema TEXT NOT NULL CHECK (char_length(tema) BETWEEN 3 AND 200),
            tempo_valor INT NOT NULL CHECK (tempo_valor BETWEEN 1 AND 24),
            tempo_unidade tempo_unidade NOT NULL,
            status plan_status NOT NULL DEFAULT 'pendente',
            ia_provider ia_provider,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now(),
            atualizado_em TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX idx_plans_session ON plans(session_id, criado_em DESC)")
    op.execute(
        "CREATE INDEX idx_plans_status ON plans(status) "
        "WHERE status IN ('pendente','gerando')"
    )

    # plan_categories
    op.execute("""
        CREATE TABLE plan_categories (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
            nome categoria_nome NOT NULL,
            ordem SMALLINT NOT NULL,
            UNIQUE(plan_id, nome)
        )
    """)
    op.execute("CREATE INDEX idx_categories_plan ON plan_categories(plan_id)")

    # plan_items
    op.execute("""
        CREATE TABLE plan_items (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            category_id UUID NOT NULL REFERENCES plan_categories(id) ON DELETE CASCADE,
            nome TEXT NOT NULL,
            link TEXT NOT NULL CHECK (link ~ '^https?://'),
            justificativa TEXT NOT NULL,
            concluido BOOLEAN NOT NULL DEFAULT false,
            ordem SMALLINT NOT NULL
        )
    """)
    op.execute("CREATE INDEX idx_items_category ON plan_items(category_id, ordem)")

    # plan_events
    op.execute("""
        CREATE TABLE plan_events (
            id BIGSERIAL PRIMARY KEY,
            plan_id UUID NOT NULL REFERENCES plans(id) ON DELETE CASCADE,
            tipo TEXT NOT NULL,
            payload JSONB,
            criado_em TIMESTAMPTZ NOT NULL DEFAULT now()
        )
    """)
    op.execute("CREATE INDEX idx_events_plan ON plan_events(plan_id, criado_em)")

    # lgpd_deletions
    op.execute("""
        CREATE TABLE lgpd_deletions (
            id BIGSERIAL PRIMARY KEY,
            session_hash TEXT NOT NULL,
            requested_at TIMESTAMPTZ NOT NULL DEFAULT now(),
            executed_at TIMESTAMPTZ,
            items_deleted INT
        )
    """)

    # Row-Level Security
    op.execute("ALTER TABLE plans ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE plan_categories ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE plan_items ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE plan_events ENABLE ROW LEVEL SECURITY")

    op.execute("""
        CREATE POLICY session_scope_plans ON plans
            USING (session_id = current_setting('app.session_id')::uuid)
    """)
    op.execute("""
        CREATE POLICY session_scope_categories ON plan_categories
            USING (plan_id IN (SELECT id FROM plans))
    """)
    op.execute("""
        CREATE POLICY session_scope_items ON plan_items
            USING (category_id IN (
                SELECT c.id FROM plan_categories c JOIN plans p ON p.id = c.plan_id
            ))
    """)
    op.execute("""
        CREATE POLICY session_scope_events ON plan_events
            USING (plan_id IN (SELECT id FROM plans))
    """)

    # Role curadoria_app — executar como superuser antes do deploy
    # (comentado pois Alembic pode não ter permissão para criar roles)
    # op.execute("CREATE ROLE curadoria_app LOGIN PASSWORD :'app_password'")
    # op.execute("GRANT CONNECT ON DATABASE curadoria TO curadoria_app")
    # ...


def downgrade() -> None:
    op.execute("DROP TABLE IF EXISTS lgpd_deletions CASCADE")
    op.execute("DROP TABLE IF EXISTS plan_events CASCADE")
    op.execute("DROP TABLE IF EXISTS plan_items CASCADE")
    op.execute("DROP TABLE IF EXISTS plan_categories CASCADE")
    op.execute("DROP TABLE IF EXISTS plans CASCADE")
    op.execute("DROP TABLE IF EXISTS sessions CASCADE")
    op.execute("DROP TYPE IF EXISTS ia_provider")
    op.execute("DROP TYPE IF EXISTS categoria_nome")
    op.execute("DROP TYPE IF EXISTS tempo_unidade")
    op.execute("DROP TYPE IF EXISTS plan_status")
