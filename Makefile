PY=.venv/bin/python

.PHONY: up down ps logs psql smoke migrate import-psca resolve

up:
	docker compose up -d

down:
	docker compose down

ps:
	docker compose ps

logs:
	docker logs -f fhir_ig_rag_postgres

psql:
	docker exec -it fhir_ig_rag_postgres psql -U ig -d igdb

smoke:
	$(PY) scripts/db_smoke_test.py

migrate:
	$(PY) -m alembic upgrade head

import-psca:
	$(PY) -m app.ingest.cli import-structuredefs --ig ps-ca --ig-version 2.1.1 --dir data/artifacts/ps-ca/2.1.1/StructureDefinition

resolve:
	@echo "Usage: make resolve CANONICAL='http://...'"
	$(PY) -m app.ingest.cli resolve --canonical "$(CANONICAL)"
