# AlphaSync API

A multi-tenant FastAPI backend for service-based businesses with WhatsApp chatbot integration.

## Architecture

- **Framework**: FastAPI (Python 3.12)
- **Database**: PostgreSQL (Replit-managed via SQLAlchemy + psycopg2)
- **Cache**: Redis (optional, configured via `REDIS_URL`)
- **Auth**: JWT-based authentication (python-jose + passlib/bcrypt)
- **Server**: Uvicorn (dev), Gunicorn (production)

## Project Structure

```
app/
├── api/          - API endpoints (v1 router + admin/bot/panel routes)
├── core/         - Config (Settings via pydantic-settings), security, tenancy
├── db/           - SQLAlchemy models, connection, migrations setup
├── domains/      - Business domain logic (cleaning, electrician, hvac, plumbing, etc.)
├── integrations/ - WhatsApp and Google Calendar clients
├── repositories/ - DB access layer (repository pattern)
├── schemas/      - Pydantic schemas for request/response
└── services/     - Business services layer
```

## Key Configuration

- `DATABASE_URL`: Set automatically by Replit (Replit PostgreSQL). App converts `postgresql://` to `postgresql+psycopg2://` automatically.
- `SECRET_KEY`: JWT secret key (set as environment variable)
- `API_V1_PREFIX`: `/api/v1` (default)
- `CORS_ORIGINS`: `["*"]` (all origins allowed in dev)

## Running

**Development**: `uvicorn app.main:app --host 0.0.0.0 --port 5000 --reload`
**Production**: `gunicorn --bind=0.0.0.0:5000 --reuse-port --worker-class uvicorn.workers.UvicornWorker app.main:app`

## API Docs

- Swagger UI: `GET /docs`
- ReDoc: `GET /api/redoc`
- Health check: `GET /health`
- API routes: `/api/v1/...`

## Database

Tables are auto-created on startup via `Base.metadata.create_all()`.
Migrations managed with Alembic (configured but migrations folder not yet seeded).

## Notes

- The `PNAddressCatalog`, `PNAddressPlant`, `PNAddressMeasurement`, `PNAddressJobRule` models had duplicate index definitions (both `index=True` on columns AND named `Index` objects in `__table_args__`). The `index=True` on FK columns in those tables was removed to fix startup failures.
- `DATABASE_URL` from Replit is `postgresql://...`; the config validator auto-converts it to `postgresql+psycopg2://...` for SQLAlchemy compatibility.
