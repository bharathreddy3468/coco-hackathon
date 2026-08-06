# Insurance Claims Copilot Backend

FastAPI backend server powered by Python `>=3.11` and `uv` package management.

## Key Features
- **API Router**: Versioned REST endpoints (`/api/v1`)
- **Workflow Engine**: Multi-stage insurance claims evaluation pipeline
- **AI Skills**: Pluggable AI skill modules (`claim_extractor`, `coverage_checker`, `fraud_detector`, `decision_synthesis`)
- **Structured Logging**: Production JSON log formatter
- **Environment & Settings**: Pydantic-settings `.env` management
- **Database**: Async SQLAlchemy engine with SQLite/PostgreSQL support
- **Health Endpoints**: Liveness (`/health`) and Readiness (`/ready`) probes
