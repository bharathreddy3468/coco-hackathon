# 🛡️ Insurance Claims Decision Copilot

Production-grade, modular workspace architecture for an **Insurance Claims Decision Copilot**. Built with **FastAPI** on the backend using `uv` for package management, and **React (Vite + TypeScript)** on the frontend with rich HSL glassmorphism UI styling.

---

## 🏛️ Project Architecture & Layout

```
.
├── backend/                  # FastAPI Application (Python >= 3.11 with uv)
│   ├── app/
│   │   ├── api/             # API Router & Versioned Endpoints (v1)
│   │   │   └── v1/endpoints/ # health, claims, skills endpoints
│   │   ├── config/          # Environment Settings & Structured JSON Logging
│   │   ├── database/        # Async SQLAlchemy engine & session factory
│   │   ├── models/          # SQLAlchemy ORM Models (Claim, AuditLog)
│   │   ├── schemas/         # Pydantic Input/Output Schemas
│   │   ├── services/        # Business Logic & Orchestration
│   │   ├── skills/          # Extensible AI Skills Framework (Extractor, Coverage, Fraud, Synthesis)
│   │   ├── utils/           # Structured Logger & Utilities
│   │   ├── workflow/        # Multi-stage Claims Decision Engine Pipeline
│   │   └── main.py          # FastAPI Server Entrypoint & Middleware
│   ├── .env.example         # Backend environment variables reference
│   ├── Dockerfile           # Multi-stage Python uv Docker image
│   └── pyproject.toml       # Dependencies & uv environment settings
├── frontend/                 # React 18 + Vite + TypeScript Frontend
│   ├── src/
│   │   ├── components/      # UI components (Navbar, Metrics, ClaimCard, SkillExecutor, etc.)
│   │   ├── services/        # Typed API client for FastAPI backend
│   │   ├── types/           # TypeScript interfaces matching backend models
│   │   ├── index.css        # Premium Dark Mode Glassmorphism Design System
│   │   ├── App.tsx          # Main Dashboard Application
│   │   └── main.tsx         # React Mount Entrypoint
│   ├── Dockerfile           # Multi-stage Nginx Docker image
│   ├── package.json         # Node dependencies & Vite scripts
│   └── vite.config.ts       # Vite proxy & dev server settings
├── docker-compose.yml        # Orchestration for Backend + Frontend containers
├── .env.example              # Global environment reference
└── README.md                 # Documentation
```

---

## 🚀 Getting Started

### Prerequisites
- [Python 3.11+](https://www.python.org/)
- [`uv`](https://github.com/astral-sh/uv) (Fast Python Package Installer)
- [Node.js 18+](https://nodejs.org/) & `npm`
- [Docker & Docker Compose](https://www.docker.com/) (Optional)

---

### Running Locally

#### 1. Backend (FastAPI + `uv`)

```bash
cd backend

# Install dependencies and create virtualenv via uv
uv venv
uv pip install -e .

# Start development server with reload
uv run uvicorn app.main:app --reload --port 8000
```

- **Swagger Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)
- **Health Check**: [http://localhost:8000/api/v1/health](http://localhost:8000/api/v1/health)
- **Readiness Check**: [http://localhost:8000/api/v1/ready](http://localhost:8000/api/v1/ready)

#### 2. Frontend (React + Vite + TypeScript)

```bash
cd frontend

# Install node packages
npm install

# Start Vite dev server
npm run dev
```

- **Application Dashboard**: [http://localhost:5173](http://localhost:5173)

---

## 🐳 Running with Docker

Orchestrate the entire application stack with a single command:

```bash
docker-compose up --build
```

- Frontend UI: `http://localhost:5173`
- Backend API: `http://localhost:8000`

---

## 🧩 Extending AI Skills

All AI Copilot skills inherit from `BaseSkill` in `backend/app/skills/base.py`:

```python
from app.skills.base import BaseSkill
from app.schemas.skill import SkillMeta, SkillExecutionResult

class CustomSkill(BaseSkill):
    @property
    def meta(self) -> SkillMeta:
        return SkillMeta(
            id="skill_custom",
            name="Custom AI Analysis Skill",
            description="Performs custom domain analysis.",
            version="1.0.0",
            category="Domain Rules"
        )

    async def _execute(self, input_data: dict) -> SkillExecutionResult:
        # Implementation logic here
        return SkillExecutionResult(...)
```

Register new skills in `backend/app/skills/__init__.py` to expose them across the decision engine workflow and the **AI Skills Lab** tab.
