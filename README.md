# CuradorIA

> Arquiteto de Aprendizagem Holística — gera planos de estudo culturais em 6 categorias a partir de tema + tempo disponível.

## Início rápido

### Backend (Python 3.12)

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements-dev.txt
cp ../.env.example .env   # preencha as variáveis

alembic upgrade head
uvicorn app.main:app --reload
# → http://localhost:8000/v1/health/ia
```

### Frontend (Node 20+)

```bash
cd frontend
npm install
cp ../.env.example .env.local   # ajuste API_URL se necessário
npm run dev
# → http://localhost:3000
```

## Stack

| Camada | Tecnologia |
|---|---|
| Frontend | Next.js 15 + React 19 + TypeScript strict |
| Backend | FastAPI + Python 3.12 + Pydantic v2 |
| Banco | Neon PostgreSQL (3 GB) com RLS |
| Cache | Upstash Redis |
| IA primária | Groq (Llama 3.3 70B) |
| IA fallback | Google Gemini 2.0 Flash |
| Deploy BE | Fly.io |
| Deploy FE | Vercel Hobby |

Documentação completa de design: [DESIGN.md](DESIGN.md)
