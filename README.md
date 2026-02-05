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

## Resolve a canonical
```
.venv/bin/python -m app.ingest.cli resolve \
  --canonical http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps
# or: make resolve
```

The resolver prints the stored artifact metadata and the full StructureDefinition JSON payload.
