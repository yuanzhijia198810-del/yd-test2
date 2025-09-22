# Frontend Monitoring Backend

This project implements a lightweight backend service for collecting and analyzing telemetry produced by browser-based monitoring SDKs. It is built with [FastAPI](https://fastapi.tiangolo.com/) and [SQLModel](https://sqlmodel.tiangolo.com/) and persists data to SQLite by default.

## Features

- Project management endpoints for provisioning API keys used by client SDKs.
- Event ingestion endpoint accepting error, performance, interaction, and custom events over HTTPS.
- Event querying API with filtering by type, time range, user, release, and free-text search.
- Summary analytics providing total counts, unique users, and per-type distributions.
- Time-series analytics grouped by hour or day for building dashboards.

## Project Structure

```
app/
  config.py          # Environment-driven configuration
  database.py        # SQLModel engine and session utilities
  main.py            # FastAPI application factory
  models.py          # Pydantic/SQLModel models and schemas
  routers/           # API route definitions
  services/          # Business logic for projects and events
  utils/             # Reserved for future helpers
tests/               # Pytest-based API tests
pyproject.toml       # Project metadata and dependencies
```

## Getting Started

1. **Install dependencies**

   ```bash
   pip install -e .[dev]
   ```

2. **Run the API server**

   ```bash
   uvicorn app.main:app --reload
   ```

   The service listens on `http://127.0.0.1:8000` by default. Interactive API documentation is available at `/docs`.

3. **Create a project**

   ```bash
   curl -X POST http://127.0.0.1:8000/api/projects \
     -H "Content-Type: application/json" \
     -d '{"name": "Web App"}'
   ```

   Record the `api_key` from the response; client SDKs must send it in the `X-API-Key` header when posting events.

4. **Ingest an event**

   ```bash
   curl -X POST http://127.0.0.1:8000/api/events \
     -H "Content-Type: application/json" \
     -H "X-API-Key: <PROJECT_API_KEY>" \
     -d '{
           "event_type": "error",
           "name": "TypeError",
           "message": "Cannot read properties of undefined",
           "page_url": "https://app.example.com/dashboard"
         }'
   ```

## Testing

Run the unit and integration tests with:

```bash
pytest
```

The test suite spins up the FastAPI app against an in-memory SQLite database.
