from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, List

from fastapi import Depends, FastAPI, HTTPException, Query, Request
from fastapi.responses import JSONResponse
from sqlalchemy import select, desc, func
from sqlalchemy.orm import Session

from app.api.db import get_session
from app.db.models import Artifact, Package, SDBinding, SDElement, SDConstraint


app = FastAPI(title="FHIR IG RAG API", version="0.1.0")


def _resolve_artifact(
    session: Session, canonical: str, version: Optional[str]
) -> tuple[Artifact, Package]:
    stmt = select(Artifact, Package).join(Package).where(Artifact.canonical_url == canonical)
    if version is not None:
        stmt = stmt.where(Artifact.version == version)
    else:
        stmt = stmt.order_by(
            desc(Artifact.version.is_(None)),
            desc(Artifact.version),
            desc(Artifact.indexed_at),
            desc(Artifact.id),
        )
    result = session.execute(stmt).first()
    if not result:
        raise HTTPException(status_code=404, detail="Artifact not found for canonical/version")
    artifact, pkg = result
    return artifact, pkg


@app.exception_handler(Exception)
def json_exception_handler(request: Request, exc: Exception):
    return JSONResponse(
        status_code=500,
        content={"detail": str(exc)},
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/gq/must-support")
def gq_must_support(
    canonical: str = Query(..., description="StructureDefinition canonical URL"),
    version: Optional[str] = Query(None, description="Optional version"),
    session: Session = Depends(get_session),
):
    artifact, pkg = _resolve_artifact(session, canonical, version)
    paths = (
        session.execute(
            select(SDElement.path, SDElement.min, SDElement.max)
            .where(SDElement.artifact_id == artifact.id, SDElement.must_support.is_(True))
            .order_by(SDElement.path)
        )
        .all()
    )
    if not paths:
        raise HTTPException(status_code=404, detail="No mustSupport elements found for this profile")

    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "query_id": "PSCA-GQ-MS-01",
        "question": "List mustSupport paths",
        "scope": {"ig": pkg.ig, "ig_version": pkg.ig_version},
        "profile": {
            "canonical_url": artifact.canonical_url,
            "version": artifact.version,
            "name": artifact.name,
            "sd_type": artifact.sd_type,
        },
        "must_support_paths": [
            {"path": row.path, "min": row.min, "max": row.max} for row in paths
        ],
        "generated_at": generated_at,
    }


@app.get("/gq/bindings")
def gq_bindings(
    canonical: str = Query(..., description="StructureDefinition canonical URL"),
    path: str = Query(..., description="Element path"),
    version: Optional[str] = Query(None, description="Optional version"),
    session: Session = Depends(get_session),
):
    artifact, pkg = _resolve_artifact(session, canonical, version)
    bindings = (
        session.execute(
            select(SDBinding.strength, SDBinding.value_set, SDBinding.source_choice)
            .where(SDBinding.artifact_id == artifact.id, SDBinding.path == path)
            .order_by(SDBinding.value_set)
        )
        .all()
    )
    if not bindings:
        raise HTTPException(status_code=404, detail="No bindings found for this path")

    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "query_id": "PSCA-GQ-BIND-01",
        "question": "List bindings for path",
        "scope": {"ig": pkg.ig, "ig_version": pkg.ig_version},
        "profile": {
            "canonical_url": artifact.canonical_url,
            "version": artifact.version,
            "name": artifact.name,
            "sd_type": artifact.sd_type,
            "file_path": artifact.file_path,
        },
        "path": path,
        "bindings": [
            {"strength": row.strength, "value_set": row.value_set, "source": row.source_choice}
            for row in bindings
        ],
        "generated_at": generated_at,
    }


@app.get("/gq/constraints")
def gq_constraints(
    canonical: str = Query(..., description="StructureDefinition canonical URL"),
    version: Optional[str] = Query(None, description="Optional version"),
    path: Optional[str] = Query(None, description="Optional element path filter"),
    session: Session = Depends(get_session),
):
    artifact, pkg = _resolve_artifact(session, canonical, version)
    stmt = (
        select(
            SDConstraint.path,
            SDConstraint.key,
            SDConstraint.severity,
            SDConstraint.human,
            SDConstraint.expression,
            SDConstraint.source_choice,
        )
        .where(SDConstraint.artifact_id == artifact.id)
        .order_by(SDConstraint.path, SDConstraint.key)
    )
    if path:
        stmt = stmt.where(SDConstraint.path == path)
    rows = session.execute(stmt).all()
    if not rows:
        raise HTTPException(status_code=404, detail="No constraints found for this profile/path")

    generated_at = datetime.now(timezone.utc).isoformat()
    question = "List constraints for path" if path else "List constraints for profile"
    return {
        "query_id": "PSCA-GQ-CONSTR-01",
        "question": question,
        "scope": {"ig": pkg.ig, "ig_version": pkg.ig_version},
        "profile": {
            "canonical_url": artifact.canonical_url,
            "version": artifact.version,
            "name": artifact.name,
            "sd_type": artifact.sd_type,
            "file_path": artifact.file_path,
        },
        "path": path,
        "constraints": [
            {
                "path": r.path,
                "key": r.key,
                "severity": r.severity,
                "human": r.human,
                "expression": r.expression,
                "source": r.source_choice,
            }
            for r in rows
        ],
        "generated_at": generated_at,
    }


@app.get("/gq/value-set/where-used")
def gq_value_set_where_used(
    value_set: str = Query(..., description="ValueSet canonical URL"),
    ig: str = Query("ps-ca", description="IG code"),
    ig_version: str = Query("2.1.1", description="IG version"),
    session: Session = Depends(get_session),
):
    pkg = session.execute(
        select(Package).where(Package.ig == ig, Package.ig_version == ig_version)
    ).scalar_one_or_none()
    if not pkg:
        raise HTTPException(status_code=404, detail="Package not found")

    rows = (
        session.execute(
            select(
                Artifact.canonical_url,
                Artifact.version,
                Artifact.name,
                Artifact.sd_type,
                Artifact.file_path,
                SDBinding.path,
                SDBinding.strength,
                SDBinding.source_choice,
            )
            .join(SDBinding, SDBinding.artifact_id == Artifact.id)
            .where(Artifact.package_id == pkg.id, SDBinding.value_set == value_set)
            .order_by(Artifact.sd_type, Artifact.canonical_url, SDBinding.path)
        )
        .all()
    )
    if not rows:
        raise HTTPException(status_code=404, detail="ValueSet not used in this IG/version")

    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "query_id": "PSCA-GQ-VS-WHEREUSED-01",
        "question": "Where is this ValueSet used?",
        "scope": {"ig": ig, "ig_version": ig_version},
        "value_set": value_set,
        "usages": [
            {
                "profile": {
                    "canonical_url": r.canonical_url,
                    "version": r.version,
                    "name": r.name,
                    "sd_type": r.sd_type,
                    "file_path": r.file_path,
                },
                "path": r.path,
                "strength": r.strength,
                "source": r.source_choice,
            }
            for r in rows
        ],
        "generated_at": generated_at,
    }


@app.get("/gq/profile-summary")
def gq_profile_summary(
    canonical: str = Query(..., description="StructureDefinition canonical URL"),
    version: Optional[str] = Query(None, description="Optional version"),
    include_all: bool = Query(False, description="Include all rows instead of top 10"),
    session: Session = Depends(get_session),
):
    artifact, pkg = _resolve_artifact(session, canonical, version)

    # Counts
    ms_count = session.execute(
        select(func.count()).select_from(SDElement).where(
            SDElement.artifact_id == artifact.id, SDElement.must_support.is_(True)
        )
    ).scalar_one()

    bind_count = session.execute(
        select(func.count()).select_from(SDBinding).where(SDBinding.artifact_id == artifact.id)
    ).scalar_one()

    constr_count = session.execute(
        select(func.count()).select_from(SDConstraint).where(SDConstraint.artifact_id == artifact.id)
    ).scalar_one()

    # Tops (deterministic)
    limit_val = None if include_all else 10
    ms_top = (
        session.execute(
            select(SDElement.path, SDElement.min, SDElement.max)
            .where(SDElement.artifact_id == artifact.id, SDElement.must_support.is_(True))
            .order_by(SDElement.path)
            .limit(limit_val)
        )
        .all()
    )

    bind_top = (
        session.execute(
            select(SDBinding.path, SDBinding.strength, SDBinding.value_set, SDBinding.source_choice)
            .where(SDBinding.artifact_id == artifact.id)
            .order_by(SDBinding.path, SDBinding.strength, SDBinding.value_set)
            .limit(limit_val)
        )
        .all()
    )

    constr_top = (
        session.execute(
            select(
                SDConstraint.path,
                SDConstraint.key,
                SDConstraint.severity,
                SDConstraint.human,
                SDConstraint.expression,
                SDConstraint.source_choice,
            )
            .where(SDConstraint.artifact_id == artifact.id)
            .order_by(SDConstraint.path, SDConstraint.key)
            .limit(limit_val)
        )
        .all()
    )

    has_more_ms = False if include_all else ms_count > len(ms_top)
    has_more_bind = False if include_all else bind_count > len(bind_top)
    has_more_constr = False if include_all else constr_count > len(constr_top)

    generated_at = datetime.now(timezone.utc).isoformat()
    return {
        "query_id": "PSCA-MCP-PROFILE-SUMMARY-01",
        "scope": {"ig": pkg.ig, "ig_version": pkg.ig_version},
        "profile": {
            "canonical_url": artifact.canonical_url,
            "version": artifact.version,
            "name": artifact.name,
            "sd_type": artifact.sd_type,
            "title": artifact.title,
            "base_definition": artifact.base_definition,
            "file_path": artifact.file_path,
        },
        "counts": {
            "must_support_paths": ms_count,
            "bindings": bind_count,
            "constraints": constr_count,
        },
        "top_limit": None if include_all else 10,
        "top": {
            "must_support_paths": [
                {"path": r.path, "min": r.min, "max": r.max} for r in ms_top
            ],
            "must_support_paths_paths": [r.path for r in ms_top],
            "bindings": [
                {
                    "path": r.path,
                    "strength": r.strength,
                    "value_set": r.value_set,
                    "source": r.source_choice,
                }
                for r in bind_top
            ],
            "constraints": [
                {
                    "path": r.path,
                    "key": r.key,
                    "severity": r.severity,
                    "human": r.human,
                    "expression": r.expression,
                    "source": r.source_choice,
                }
                for r in constr_top
            ],
        },
        "has_more": {
            "must_support_paths": has_more_ms,
            "bindings": has_more_bind,
            "constraints": has_more_constr,
        },
        "generated_at": generated_at,
    }
