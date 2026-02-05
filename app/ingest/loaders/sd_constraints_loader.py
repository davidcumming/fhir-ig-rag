from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from sqlalchemy import delete, select
from sqlalchemy.dialects.postgresql import insert as pg_insert

from app.db.config import PROJECT_ROOT
from app.db.engine import SessionLocal
from app.db.models import Artifact, Package, SDConstraint


def _select_elements(structure_def: dict) -> tuple[list[dict], str]:
    differential = structure_def.get("differential", {}) or {}
    snapshot = structure_def.get("snapshot", {}) or {}
    diff_elements = differential.get("element") or []
    snap_elements = snapshot.get("element") or []
    if isinstance(diff_elements, list) and diff_elements:
        return diff_elements, "differential"
    if isinstance(snap_elements, list) and snap_elements:
        return snap_elements, "snapshot"
    return [], ""


def _load_resource(path: Path) -> dict:
    with path.open() as handle:
        return json.load(handle)


def load_sd_constraints(ig: str, ig_version: str, truncate: bool = False) -> Dict[str, int]:
    summary = {
        "artifacts_processed": 0,
        "constraints_inserted": 0,
        "constraints_updated": 0,
        "constraints_skipped": 0,
        "artifacts_skipped_no_elements": 0,
    }

    with SessionLocal() as session:
        pkg = session.execute(
            select(Package).where(Package.ig == ig, Package.ig_version == ig_version)
        ).scalar_one_or_none()
        if not pkg:
            raise RuntimeError(f"Package not found for ig={ig}, ig_version={ig_version}")

        artifacts: List[Artifact] = (
            session.execute(
                select(Artifact)
                .where(Artifact.package_id == pkg.id, Artifact.resource_type == "StructureDefinition")
                .order_by(Artifact.id)
            )
            .scalars()
            .all()
        )

        if truncate and artifacts:
            ids = [a.id for a in artifacts]
            session.execute(delete(SDConstraint).where(SDConstraint.artifact_id.in_(ids)))
            session.commit()

        for artifact in artifacts:
            summary["artifacts_processed"] += 1
            resource_path = PROJECT_ROOT / artifact.file_path
            if not resource_path.exists():
                summary["artifacts_skipped_no_elements"] += 1
                continue

            sd_json = _load_resource(resource_path)
            elements, source_choice = _select_elements(sd_json)
            if not elements:
                summary["artifacts_skipped_no_elements"] += 1
                continue

            for element in elements:
                path_val = element.get("path")
                if not path_val:
                    summary["constraints_skipped"] += 1
                    continue
                constraints = element.get("constraint") or []
                if not isinstance(constraints, list):
                    continue
                for cons in constraints:
                    key = cons.get("key")
                    if not key:
                        summary["constraints_skipped"] += 1
                        continue

                    exists = session.execute(
                        select(SDConstraint.id).where(
                            SDConstraint.artifact_id == artifact.id,
                            SDConstraint.path == path_val,
                            SDConstraint.key == key,
                        )
                    ).scalar_one_or_none()

                    payload = {
                        "artifact_id": artifact.id,
                        "sd_canonical_url": artifact.canonical_url,
                        "sd_version": artifact.version,
                        "path": path_val,
                        "key": key,
                        "severity": cons.get("severity"),
                        "human": cons.get("human"),
                        "expression": cons.get("expression"),
                        "xpath": cons.get("xpath"),
                        "constraint_json": cons,
                        "source_choice": source_choice,
                    }

                    insert_stmt = pg_insert(SDConstraint.__table__).values(**payload)
                    update_cols = {k: payload[k] for k in payload if k not in ("artifact_id", "path", "key")}
                    upsert_stmt = insert_stmt.on_conflict_do_update(
                        index_elements=["artifact_id", "path", "key"],
                        set_=update_cols,
                    )
                    session.execute(upsert_stmt)

                    if exists:
                        summary["constraints_updated"] += 1
                    else:
                        summary["constraints_inserted"] += 1

        session.commit()

    return summary
