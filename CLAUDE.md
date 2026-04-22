# CuradorIA — Contexto do Projeto

> Aplicação que gera planos de estudo culturais e holísticos (6 categorias: Formal, Visual, Leitura, Áudio, Experiências, Referências) a partir de tema + tempo disponível.

**Documentação completa**: [DESIGN.md](DESIGN.md) — consulte sob demanda por seção (ex.: `DESIGN.md §7.3 moderação`). Não carregue o arquivo inteiro por padrão.

---

## Princípios invariantes (não negociáveis)

1. **100% gratuito** — qualquer ferramenta, API, lib ou serviço deve ter free tier **permanente** (sem pause, sem trial). Ao propor qualquer dependência nova, verificar esse critério antes.
2. **LGPD by design** — mínimo de PII (zero, idealmente), anônimo por padrão, purga automática após 180d, endpoint de deleção obrigatório.
3. **WCAG 2.1 AA** — contraste 4.5:1 texto / 3:1 UI, focus ring visível, touch targets ≥44×44px, sem cor como único indicador.
4. **PT-BR único** (v1) — strings em `messages/pt-BR.json` preparadas para i18n futuro.
5. **Clareza > estética decorativa** — interface editorial cultural, não rigor acadêmico. Wireframes clean e organizados.
6. **Contract-first** — OpenAPI é fonte de verdade. Código segue o contrato, não o contrário.

---

## Stack (fixa)

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 15 (App Router) + React 19 + TypeScript strict + CSS Modules |
| Backend | FastAPI + Python 3.12 + Pydantic v2 + SQLAlchemy 2.x async + Alembic |
| Banco | Neon PostgreSQL (3 GB, sem pause) com RLS |
| Cache | Upstash Redis |
| IA primária | Groq (Llama 3.3 70B) |
| IA fallback | Google Gemini 2.0 Flash |
| Deploy BE | Fly.io (2 VMs shared-cpu-1x, `auto_stop_machines=false`) |
| Deploy FE | Vercel Hobby |
| CI/CD | GitHub Actions |
| Erros | Sentry · Logs: Better Stack · Uptime: UptimeRobot |
| Design | Penpot (open-source) |
| Fontes | Fraunces + Instrument Serif + Inter (Google Fonts / Fontsource) |
| Ícones | Phosphor (duotone) |

**Proibido sem discussão prévia**: Supabase (pausa), Railway (sem free), Tavily (latência inaceitável), qualquer serviço com trial ou cartão obrigatório.

---

## Estrutura do monorepo

```
curadoriA/
├── frontend/         # Next.js 15
├── backend/          # FastAPI
├── infra/            # neon/ runbooks/
├── .github/workflows/
├── DESIGN.md         # documentação completa
└── CLAUDE.md         # este arquivo
```

Estrutura interna detalhada: `DESIGN.md §6.1` (frontend) e `§7.1` (backend).

---

## Decisões arquiteturais críticas

- **Anônimo via JWT HttpOnly cookie** `SameSite=Strict`, `Secure`, TTL 180d. **Nunca** usar header `X-Session-ID` ou expor session no body/localStorage.
- **LLM provider abstraction** com fallback automático (Groq → Gemini) + circuit breaker 5 falhas/60s.
- **Idempotência obrigatória** em POST `/planos` via header `Idempotency-Key` + Redis 1h TTL.
- **RLS por sessão** em `plans/plan_categories/plan_items/plan_events`. Backend faz `SET LOCAL app.session_id` a cada conexão.
- **Defesa anti-prompt-injection em 3 camadas**: moderação regex (`PADROES_INJECTION`) → delimiters `<tema>...</tema>` → Pydantic `PlanoGerado` validator que exige as 6 categorias.
- **Migrações expand → deploy → contract** (nunca breaking no mesmo deploy). Alembic roda **antes** de `fly deploy`.
- **Sem busca web antes da geração** (revogado por latência). Links validados por cron mensal.

---

## Convenções de código

**Python (backend)**:
- `ruff` (lint + format) + `mypy` strict.
- Módulos por domínio (`sessoes/`, `planos/`, `ia/`, `lgpd/`, `health/`), cada um com `router.py`, `service.py`, `repository.py`, `schemas.py`, `models.py`.
- Pydantic v2 para validação de entrada e saída.
- `async/await` em tudo que toca I/O. Evitar `requests` (usar `httpx`).
- `print()` proibido — use `structlog`.
- Erros com RFC 7807 Problem Details.

**TypeScript (frontend)**:
- `strict: true`, `noUncheckedIndexedAccess: true`.
- Server Components por padrão; `"use client"` apenas quando necessário (interatividade, hooks).
- Validação com Zod + React Hook Form.
- Data fetching via TanStack Query v5.
- Componentes acessíveis via Radix UI Primitives.
- CSS via CSS Modules + design tokens (custom properties em `styles/tokens.css`).

**Commits**: Conventional Commits (`feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`).

**Branches**: `main` (produção) + feature branches (`feat/nome-curto`). PRs passam por CI obrigatório.

---

## Comandos principais

**Backend** (dentro de `backend/`):
```bash
pip install -r requirements-dev.txt
ruff check app/ && ruff format --check app/
mypy app/
alembic upgrade head
pytest tests/unit --cov=app --cov-fail-under=85
pytest tests/integration
uvicorn app.main:app --reload
```

**Frontend** (dentro de `frontend/`):
```bash
npm ci
npm run lint && npm run typecheck
npm run test:unit
npm run build && npm run start
npm run test:e2e         # Playwright
npm run build-storybook
```

**Deploy**:
```bash
flyctl deploy --remote-only --strategy rolling   # backend
# frontend: push em main → Vercel automático
```

---

## Quando consultar DESIGN.md

| Preciso de... | Seção |
|---|---|
| Contrato de um endpoint específico | §3.2 |
| Schema SQL / constraints / RLS | §4.2–4.4 |
| Wireframe ou tokens de cor | §5.2, §5.7 |
| Como o provider de IA faz fallback | §7.2 |
| Prompt do sistema e defesa anti-injection | §7.3–7.5 |
| Política LGPD / purga | §4.1 (tabela `lgpd_deletions`), §12.3 (cron) |
| CI/CD / Fly / Vercel | §12 inteiro |
| Runbooks de incidente | §12.8 |
| Checklist go-live | §12.9 |

---

## O que NÃO fazer

- ❌ Adicionar dependência paga ou com trial — **sempre** verificar free tier permanente primeiro.
- ❌ Coletar PII (nome, e-mail, telefone) na v1. Anônimo via cookie é lei.
- ❌ Concatenar tema do usuário direto no prompt sem moderação + delimiters.
- ❌ Gerar plano sem `Idempotency-Key` (causa planos duplicados em refresh).
- ❌ Criar migração breaking sem expand/contract.
- ❌ Usar `print()`, `console.log` em código de produção.
- ❌ Retornar erro sem Problem Details (RFC 7807).
- ❌ Ignorar contraste WCAG ou remover focus ring.
- ❌ Fazer deploy manual sem passar pelo pipeline (pula lint/test/scan).
- ❌ Commitar secret (`.env`, chaves) — pre-commit com gitleaks + detect-secrets.

---

## Novas features neste projeto

Após a v1 estar implantada, novas funcionalidades passam pelo orquestrador **`/feature`** (`.claude/commands/feature.md`), que conduz pelas 12 etapas (levantamento → arquitetura → ... → devops).

Enquanto estamos **construindo a v1 do zero**, não usar `/feature` — é para features sobre código existente.

---

## Estado atual

- ✅ Design completo (12 etapas em `DESIGN.md`)
- ⏳ Implementação: ainda não iniciada
- ⏳ Próximo passo: scaffold do monorepo (`frontend/` + `backend/`) e CI básico antes do primeiro módulo
