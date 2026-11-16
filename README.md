# FinSmart FastAPI Backend

> Scalable, industrial-grade multi-tenant backend for FinSmart – Smart Financial Literacy & Budget Planner for Public.

## Architecture & Technology
- **FastAPI (Python 3.12)**: Asynchronous high-performance REST API with OpenAPI 3.1 docs.
- **SQLAlchemy 2.0 Async + asyncpg**: Non-blocking database access with connection pooling.
- **PostgreSQL 16 + pgvector**: Multi-tenant Row-Level Security (RLS) and semantic embeddings.
- **Multi-Tenant Security**: Tenant bound via `SET LOCAL app.current_tenant_id = :tid` in transaction context.
- **Strict Money Math**: Minor units (integer paise) to eliminate floating-point precision issues.
- **Declarative JSON Rule DSL**: Explainable government scheme & scholarship eligibility evaluation.
- **DPDP Act 2023 Compliance**: Real-time PII redaction (Aadhaar, PAN, phone numbers), purpose-specific consent ledger, and DSAR export.
- **AI Financial Mentor**: Grounded RAG assistant with strict statutory guardrails against speculative trading.

## Running Locally

### With Docker:
The backend runs automatically as part of the 3-container topology on port `8000`.

### Standalone:
```bash
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
Interactive Swagger docs available at [http://localhost:8000/docs](http://localhost:8000/docs).

## Running Tests
```bash
python -m unittest discover -s tests
```
*(All 19 unit tests verify money math, rules engine, PII scrubbing, and security).*
