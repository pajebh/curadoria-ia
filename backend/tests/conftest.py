import os

import pytest

# Garante que Settings não tente carregar .env de produção nos testes
os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379")
os.environ.setdefault("JWT_SECRET", "test-secret-for-unit-tests-only")
