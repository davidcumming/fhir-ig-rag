# fhir-ig-rag

Session 1.1 adds a Postgres-backed registry for IG packages and artifacts plus a Typer CLI for ingesting and resolving StructureDefinitions.

## Prerequisites
- `.venv/` virtualenv created from `pyproject.toml`
- Postgres reachable at `DATABASE_URL` (set in `.env`, already pointing to `postgresql+psycopg://ig:ig@localhost:5432/igdb`)
- Optional: `docker compose up -d` to start the bundled database (`make up`/`make down`).

## Migrations
```
.venv/bin/python -m alembic upgrade head
# or: make migrate
```

## Import PS-CA StructureDefinitions
```
.venv/bin/python -m app.ingest.cli import-structuredefs \
  --ig ps-ca \
  --ig-version 2.1.1 \
  --dir data/artifacts/ps-ca/2.1.1/StructureDefinition
# or: make import-psca
```

## Load StructureDefinition elements
```
.venv/bin/python -m app.ingest.cli load-sd-elements --ig ps-ca --ig-version 2.1.1
```

Sanity SQL (psql):
```
-- total elements
select count(*) from sd_elements;
-- mustSupport count
select count(*) from sd_elements where must_support is true;
-- mustSupport paths for a canonical
select path from sd_elements
 where sd_canonical_url = 'http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps'
   and must_support is true
 order by path
 limit 20;
```

## Load bindings and constraints
```
.venv/bin/python -m app.ingest.cli load-sd-bindings --ig ps-ca --ig-version 2.1.1
.venv/bin/python -m app.ingest.cli load-sd-constraints --ig ps-ca --ig-version 2.1.1
```

Sanity SQL (psql):
```
select count(*) from sd_bindings;
select count(*) from sd_constraints;
select value_set, count(*) from sd_bindings group by value_set order by count(*) desc nulls last limit 10;
select path, key, severity from sd_constraints
 where sd_canonical_url='http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps'
 order by path, key limit 30;
```

## Resolve a canonical
```
.venv/bin/python -m app.ingest.cli resolve \
  --canonical http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
# or: make resolve
```

The resolver prints the stored artifact metadata and the full StructureDefinition JSON payload.

## Run the API
```
.venv/bin/python -m uvicorn app.api.main:app --reload
# or: make serve
```

Endpoints:
- GET /health
- GET /gq/must-support?canonical=...&version=optional
- GET /gq/bindings?canonical=...&path=...&version=optional
- GET /gq/constraints?canonical=...&version=optional&path=optional
- GET /gq/value-set/where-used?value_set=...&ig=ps-ca&ig_version=2.1.1

DB smoke test:
```
.venv/bin/python -c "from app.api.db import SessionLocal; from sqlalchemy import text; s=SessionLocal(); s.execute(text('select 1')); print('db ok'); s.close()"
```

Example curls:
```
curl "http://localhost:8000/gq/constraints?canonical=http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps"
curl "http://localhost:8000/gq/value-set/where-used?value_set=https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode"
```

## MCP server
Run the MCP tools (stdio):
```
.venv/bin/python -m app.mcp_server.server
```

Tools exposed:
- `psca_must_support(canonical, version=None)`
- `psca_bindings(canonical, path, version=None)`
- `psca_constraints(canonical, path=None, version=None)`
- `psca_where_used_value_set(value_set, ig='ps-ca', ig_version='2.1.1')`

Point your MCP-compatible client to the stdio command above while the FastAPI server is running on localhost:8000.
