# fhir-ig-rag

A pragmatic **“IG facts service”** for PS-CA (Patient Summary for Canada). It turns the official StructureDefinition JSON artifacts into deterministic, queryable answers for conformance, testing, and implementation support.

---

## Why this exists
Standards and vendor discussions often stall on questions like:
- What is **Must Support** for this profile?
- What constraints/invariants apply?
- Which ValueSet is bound here, and how strong is the binding?
- If we change a ValueSet, what breaks?

This project makes those answers **traceable to the IG artifacts**, reducing ambiguity, speeding reviews, and enabling “blast radius” analysis for terminology/profile changes. It also exposes MCP tools so agents can fetch facts instead of guessing.

---

## Architecture (high level)

**Data flow**
```
StructureDefinition JSONs
  -> ingestion CLI loaders
    -> Postgres tables (packages, artifacts, sd_elements, sd_bindings, sd_constraints)
      -> FastAPI “facts” endpoints
        -> MCP tools (wrap the API for agent hosts)
```

**Core data model**
- **packages**: ig, ig_version  
- **artifacts**: canonical_url, version, name, sd_type, baseDefinition, title, file_path  
- **sd_elements**: artifact_id + path (unique), must_support, min/max, source (diff/snapshot)  
- **sd_bindings**: artifact_id + path + value_set (unique), strength, source (diff/snapshot), value_set is non-null ('' if missing)  
- **sd_constraints**: artifact_id + path + key (unique), severity, human, expression, source  

---

## Capabilities

### FastAPI endpoints
- `GET /health`
- `GET /gq/must-support`
- `GET /gq/bindings`
- `GET /gq/constraints`
- `GET /gq/value-set/where-used`

### MCP tools (stdio)
- `psca_must_support`
- `psca_bindings`
- `psca_constraints`
- `psca_where_used_value_set`

---

## Setup on your machine

**Prerequisites**
- Python 3.10+
- Postgres reachable (Docker compose included)
- macOS/Linux shell examples (zsh/bash)

### 1) Clone & venv
```bash
git clone <repo-url>
cd fhir-ig-rag
python3 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e .
```

### 2) Environment
Create `.env`:
```bash
cat > .env <<'EOF'
DATABASE_URL=postgresql+psycopg://ig:ig@localhost:5432/igdb
EOF
```

### 3) Start Postgres (Docker option)
```bash
docker compose up -d
# psql inside container:
docker exec -it fhir_ig_rag_postgres psql -U ig -d igdb
```

### 4) Migrations
```bash
.venv/bin/python -m alembic upgrade head
# or: make migrate
```

### 5) Import PS-CA StructureDefinitions
Place the JSONs at `data/artifacts/ps-ca/2.1.1/StructureDefinition/`, then:
```bash
.venv/bin/python -m app.ingest.cli import-structuredefs \
  --ig ps-ca \
  --ig-version 2.1.1 \
  --dir data/artifacts/ps-ca/2.1.1/StructureDefinition
# or: make import-psca
```

### 6) Load extracted features
```bash
.venv/bin.python -m app.ingest.cli load-sd-elements --ig ps-ca --ig-version 2.1.1
.venv/bin.python -m app.ingest.cli load-sd-bindings --ig ps-ca --ig-version 2.1.1
.venv/bin.python -m app.ingest.cli load-sd-constraints --ig ps-ca --ig-version 2.1.1
```

### 7) Smoke test DB connectivity (API layer)
```bash
.venv/bin/python -c "from app.api.db import SessionLocal; from sqlalchemy import text; s=SessionLocal(); s.execute(text('select 1')); print('db ok'); s.close()"
```

### 8) Run FastAPI server
```bash
.venv/bin.python -m uvicorn app.api.main:app --reload --port 8000
# or: make serve
```
Health check:
```bash
curl -s http://localhost:8000/health
```

---

## FastAPI usage examples
```bash
# 1) Must Support paths
curl -s "http://localhost:8000/gq/must-support?canonical=http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps" | jq .

# 2) Binding at a path
curl -s "http://localhost:8000/gq/bindings?canonical=http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/allergyintolerance-ca-ps&path=AllergyIntolerance.code" | jq .

# 3) Constraints for a profile (and optional path filter)
curl -s "http://localhost:8000/gq/constraints?canonical=http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps" | jq .
curl -s "http://localhost:8000/gq/constraints?canonical=http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps&path=Patient.name" | jq .

# 4) ValueSet where-used (blast radius)
curl -s "http://localhost:8000/gq/value-set/where-used?value_set=https://fhir.infoway-inforoute.ca/ValueSet/pharmaceuticalbiologicproductandsubstancecode" | jq .

# 5) Profile summary (top mustSupport/bindings/constraints)
curl -s "http://localhost:8000/gq/profile-summary?canonical=http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps" | jq .
# Full lists (include_all=true)
curl -s "http://localhost:8000/gq/profile-summary?canonical=http://fhir.infoway-inforoute.ca/io/psca/StructureDefinition/patient-ca-ps&include_all=true" | jq .
```

---

## MCP server (tools for agents)

**Prereq:** FastAPI running on `localhost:8000`.

Run MCP server (stdio):
```bash
.venv/bin/python -m app.mcp_server.server
```
Tools exposed:
- `psca_must_support(canonical, version=None)`
- `psca_bindings(canonical, path, version=None)`
- `psca_constraints(canonical, path=None, version=None)`
- `psca_where_used_value_set(value_set, ig='ps-ca', ig_version='2.1.1')`
- `psca_profile_summary(canonical, version=None)`
- `psca_profile_summary_all(canonical, version=None)`

### Claude Desktop quick setup
Add to `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "fhir-ig-rag-psca": {
      "command": "/ABSOLUTE/PATH/TO/fhir-ig-rag/.venv/bin/python",
      "args": ["-m", "app.mcp_server.server"],
      "env": { "PYTHONUNBUFFERED": "1" }
    }
  }
}
```
Restart Claude Desktop. The MCP server stays quiet until the client sends tool calls.

---

## Troubleshooting
- **Port in use:** run uvicorn on another port (`--port 8001`) and adjust MCP base URL in `app/mcp_server/server.py` if needed.
- **MCP seems idle:** stdio servers print nothing until a client sends requests—this is expected.
- **jq errors:** if the response isn’t JSON (e.g., 404 HTML), `jq` will fail; inspect with `curl -i`.

---

## Roadmap ideas
- Support additional artifact types (ValueSet, CodeSystem, CapabilityStatement)
- Profile lineage and “what changed vs base” diffs
- Analytics endpoints (top ValueSets, top constraints)
- Agent client that chains these tools with an LLM for richer reasoning

If you want this README tailored to a specific workflow or deployment target, let me know and I’ll adjust the commands accordingly.
