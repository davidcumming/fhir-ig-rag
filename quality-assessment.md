# fhir-ig-rag — Quality Assessment Against Business Objectives

**Date:** February 13, 2026
**Scope:** PS-CA IG Facts Service (all code in `app/`, `tests/`, `scripts/`, plus infrastructure)

---

## Business Objectives (from README)

The project states four core objectives:

1. **Conformance & Testing** — Provide deterministic, traceable answers for IG conformance validation
2. **Vendor Support** — Enable vendors implementing PS-CA to understand must-support requirements, bindings, and constraints
3. **Change Impact ("Blast Radius") Analysis** — Support analysis of what breaks when ValueSets or profiles change
4. **AI/Agent Integration** — Expose MCP tools so LLM agents can fetch facts instead of guessing

---

## Assessment Summary

| Objective | Coverage | Quality | Maturity |
|-----------|----------|---------|----------|
| Conformance & Testing | Partial | Good | Early |
| Vendor Support | Strong | Good | Functional |
| Blast Radius Analysis | Basic | Good | MVP |
| AI/Agent Integration | Strong | Good | Functional |

**Overall rating: Solid MVP with clear gaps in testing and observability.**

---

## Objective 1: Conformance & Testing

### What's working well

The data pipeline (StructureDefinition JSON → PostgreSQL → API) is sound. The ingestion loaders correctly extract mustSupport flags, bindings with strength, and constraints with expression/xpath from both differential and snapshot views. The `source_choice` field tracks provenance, which is important for conformance — you can tell whether a fact came from the differential (profile-specific) or snapshot (inherited).

The 12 golden questions in `tests/acceptance/psca_golden_questions.json` cover the three main query types (mustSupport, bindings, constraints) across three representative profiles (Patient, Observation, MedicationRequest). The EvidenceBundle contract in `docs/golden_questions_psca.md` is well-specified and machine-testable.

### Gaps

**No automated test runner.** The golden questions exist as data fixtures, but there is no test harness that actually executes them against the API and asserts correctness. This is the single biggest gap relative to this objective. A conformance service that can't programmatically verify its own correctness has a credibility problem.

**No unit tests at all.** The `tests/` directory contains only acceptance fixtures — no pytest files, no loader tests, no API endpoint tests. Edge cases like missing bindings, null constraints, malformed JSON, or version conflicts are untested.

**Golden questions 11 and 12 reference unimplemented features.** GQ-11 asks for `lineage_chain` (baseDefinition chain) and GQ-12 asks for `diff_changes` (what changed vs base). Neither endpoint exists yet. These are listed in the roadmap but their presence in the test fixtures creates a false impression of coverage.

### Recommendation

Write a pytest harness that runs the 10 implementable golden questions against a seeded test database. Remove or clearly mark GQ-11 and GQ-12 as "planned." Add unit tests for each loader's edge cases (empty differential, missing canonical URL, duplicate elements).

---

## Objective 2: Vendor Support

### What's working well

The API surface maps directly to the questions vendors actually ask during implementation. The endpoint design is intuitive: `/gq/must-support`, `/gq/bindings`, `/gq/constraints`, `/gq/element-details`, `/gq/profile-summary`. A vendor can look up exactly what they need to implement for a given profile element.

The `profile-summary` endpoint with `include_all` is particularly useful — it gives a vendor a complete picture of a profile's requirements in one call. The `element-details` endpoint combines element metadata, bindings, and constraints into a single response, which avoids multiple round-trips.

Response payloads include `scope` (IG + version), `profile` metadata, and `generated_at` timestamps, making answers traceable and auditable — exactly what you'd want for vendor discussions.

### Gaps

**No pagination.** When `include_all=true`, the profile-summary endpoint returns every row with no limit. For profiles with many elements, this could become a problem. More importantly, there's no way for a vendor to page through results incrementally.

**No search/filter across profiles.** A vendor might ask "which profiles require me to support `Patient.identifier`?" There's no cross-profile element search. The `where-used` endpoint only works for ValueSets, not for element paths or constraints.

**README has typos in setup commands.** Lines 105-108 and 117 use `.venv/bin.python` (missing slash) instead of `.venv/bin/python`. A vendor following the setup instructions would hit errors immediately.

### Recommendation

Fix the README typos. Consider adding a cross-profile search endpoint. Pagination is lower priority given the PS-CA dataset size but would matter if the project expands to other IGs.

---

## Objective 3: Blast Radius Analysis

### What's working well

The `/gq/value-set/where-used` endpoint directly addresses the "if we change this ValueSet, what breaks?" question. It returns every profile + element path that binds to a given ValueSet, along with binding strength and source. This is the right data for impact analysis.

The data model supports this well — the `sd_bindings` table with its `(artifact_id, path, value_set)` unique constraint and the normalized `value_set` column (from the migration `9a1c5b0c2f3b`) make cross-cutting queries efficient.

### Gaps

**ValueSet-only scope.** Blast radius analysis currently only works for ValueSets. You can't ask "what would break if we changed this constraint key?" or "which profiles inherit from this base definition?" The roadmap mentions supporting additional artifact types (ValueSet, CodeSystem, CapabilityStatement), which would unlock richer impact analysis.

**No severity/risk scoring.** The endpoint returns raw usage data but doesn't help prioritize. A binding with strength "required" is a much bigger deal than one with strength "example," but the API treats them equally. A "risk score" or at least grouping by binding strength would make the output more actionable.

**No diff capability.** You can see what *is* bound, but not what *changed* between versions. Version-over-version comparison would be the natural next step for true change impact analysis.

### Recommendation

Group where-used results by binding strength. Add a "summary" field that says something like "3 required bindings, 1 preferred, 2 example." Consider adding constraint and base-definition impact analysis in a future iteration.

---

## Objective 4: AI/Agent Integration

### What's working well

The MCP server (`app/mcp_server/server.py`) exposes all 7 API capabilities plus a natural-language router as stdio-based tools. The tool signatures are clean, with sensible defaults (e.g., `ig='ps-ca'`, `ig_version='2.1.1'`). The Claude Desktop integration instructions are clear and complete.

The hybrid router is a thoughtful design — deterministic heuristics handle common patterns reliably, with an optional Ollama-backed LLM classification for more complex queries. The fallback from Ollama to deterministic routing is a good resilience pattern.

The `execute=False` option on the router lets an agent plan tool calls without executing them, which is useful for multi-step reasoning workflows.

### Gaps

**MCP tools call the FastAPI server over HTTP.** The MCP server is a separate process that makes HTTP calls to `localhost:8000`. This means running the agent integration requires both the FastAPI server *and* the MCP server to be running. A direct-to-database MCP server would be simpler to deploy and more robust.

**Deterministic router is fragile.** The heuristic slot extraction uses simple string matching (e.g., looking for "must" and "support" in the question). This works for the documented examples but would fail for phrasings like "which elements are flagged as MS?" or "what are the mandatory fields?"

**No structured error responses for agents.** When a tool call fails (profile not found, no bindings, etc.), the error comes back as a raw string. LLM agents would benefit from structured error responses with an error code and suggested corrective action.

### Recommendation

Consider a direct-database MCP server for simpler deployment. Improve error responses with structured JSON including error codes. The deterministic router could be strengthened with a broader synonym set or by leaning more heavily on the Ollama path.

---

## Cross-Cutting Quality Concerns

### Code Quality: Good

The codebase is clean, well-organized, and follows Python conventions. Clear separation between layers (DB models → loaders → API → MCP). Type hints are present throughout. Pydantic and SQLAlchemy are used idiomatically. Ruff is configured for linting. At roughly 2,000 lines of production code, the project is appropriately sized for its scope.

### Observability: Weak

There are no logging statements anywhere in the codebase. No structured logging, no debug output, no audit trail. The generic exception handler in `main.py` catches all exceptions and returns `{"detail": str(exc)}`, which loses stack traces. For a service that's meant to provide "traceable answers," the service itself isn't very traceable when things go wrong.

### Data Integrity: Good

The database schema uses proper foreign keys with cascade deletes, unique constraints on natural keys, and strategic indexes. The upsert pattern (`INSERT ... ON CONFLICT DO UPDATE`) makes ingestion idempotent, which is important for reprocessing. The SHA256 checksum on artifacts enables change detection.

### Security: Adequate for local use

The service runs locally with a Docker PostgreSQL instance using default credentials (`ig:ig`). This is fine for a development/internal tool but would need hardening for any shared or production deployment. No authentication, no rate limiting, no input sanitization beyond what FastAPI/Pydantic provides.

### Documentation: Good with gaps

The README is comprehensive for setup and usage. The golden questions spec is well-structured. However, inline code documentation is sparse — most functions lack docstrings. The loader logic for choosing between differential and snapshot views is non-trivial and deserves explanation.

---

## Priority Recommendations

1. **Add a pytest test harness** for the golden questions. This is the highest-value improvement — it directly supports the conformance & testing objective and would catch regressions.

2. **Add logging** throughout the application. At minimum: loader progress, API request/response summaries, MCP tool invocations, and error details with stack traces.

3. **Fix README typos** (`.venv/bin.python` → `.venv/bin/python` on lines 105-108 and 117). Small fix, high impact on first-time setup experience.

4. **Mark unimplemented golden questions** (GQ-11, GQ-12) as planned/future to avoid confusion about current capabilities.

5. **Add structured error responses** for MCP tools to improve agent integration reliability.

---

## Conclusion

This is a well-architected MVP that delivers on its core promise: turning FHIR StructureDefinition artifacts into queryable facts. The data model is sound, the API surface matches real user needs, and the MCP integration is thoughtful. The main weakness is the absence of automated testing — ironic for a service whose purpose is to support conformance testing. Addressing that gap, along with basic observability, would move this from a promising prototype to a reliable tool that teams can depend on.
