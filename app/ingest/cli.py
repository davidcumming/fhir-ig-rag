from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Optional

import typer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.config import PROJECT_ROOT
from app.db.engine import SessionLocal
from app.db.models import Artifact, Package
from app.ingest.loaders.sd_elements_loader import load_sd_elements

app = typer.Typer(add_completion=False, no_args_is_help=True)


def sha256_path(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8192)
            if not chunk:
                break
            digest.update(chunk)
    return digest.hexdigest()


def rel_to_repo(path: Path) -> str:
    try:
        return path.resolve().relative_to(PROJECT_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def get_or_create_package(session: Session, ig: str, ig_version: str, source_path: str) -> Package:
    stmt = select(Package).where(Package.ig == ig, Package.ig_version == ig_version)
    pkg = session.execute(stmt).scalars().first()
    if pkg:
        pkg.source_path = source_path
        session.add(pkg)
        session.flush()
        return pkg

    pkg = Package(ig=ig, ig_version=ig_version, source_path=source_path)
    session.add(pkg)
    session.flush()
    return pkg


@app.command("import-structuredefs")
def import_structuredefs(
    ig: str = typer.Option(..., "--ig", help="IG code, e.g., ps-ca"),
    ig_version: str = typer.Option(..., "--ig-version", help="IG version, e.g., 2.1.1"),
    dir: Path = typer.Option(..., "--dir", exists=True, file_okay=False, resolve_path=True),
) -> None:
    """Scan a directory for StructureDefinition JSON and upsert artifacts."""
    json_files = sorted(dir.glob("*.json"))
    scanned = len(json_files)
    sd_count = 0
    inserted = 0
    updated = 0
    skipped = 0

    with SessionLocal() as session:
        package = get_or_create_package(session, ig, ig_version, str(dir))

        for path in json_files:
            with path.open() as handle:
                try:
                    payload = json.load(handle)
                except json.JSONDecodeError:
                    skipped += 1
                    continue

            if payload.get("resourceType") != "StructureDefinition":
                skipped += 1
                continue

            sd_count += 1
            canonical = payload.get("url")
            version = payload.get("version")
            name = payload.get("name")
            title = payload.get("title")
            sd_type = payload.get("type")
            base_definition = payload.get("baseDefinition")
            file_path = rel_to_repo(path)
            checksum = sha256_path(path)

            stmt = select(Artifact).where(
                Artifact.package_id == package.id,
                Artifact.canonical_url == canonical,
                Artifact.version == version,
            )
            artifact = session.execute(stmt).scalars().first()

            if artifact:
                if artifact.sha256 == checksum:
                    skipped += 1
                    continue
                artifact.name = name
                artifact.title = title
                artifact.sd_type = sd_type
                artifact.base_definition = base_definition
                artifact.file_path = file_path
                artifact.sha256 = checksum
                artifact.resource_type = "StructureDefinition"
                updated += 1
            else:
                artifact = Artifact(
                    package_id=package.id,
                    resource_type="StructureDefinition",
                    canonical_url=canonical,
                    version=version,
                    name=name,
                    title=title,
                    sd_type=sd_type,
                    base_definition=base_definition,
                    file_path=file_path,
                    sha256=checksum,
                )
                session.add(artifact)
                inserted += 1

        session.commit()

    typer.echo(
        json.dumps(
            {
                "scanned": scanned,
                "structure_definitions": sd_count,
                "inserted": inserted,
                "updated": updated,
                "skipped": skipped,
            },
            indent=2,
        )
    )


def pick_artifact(session: Session, canonical: str, version: Optional[str]) -> Optional[Artifact]:
    stmt = select(Artifact).where(Artifact.canonical_url == canonical)
    if version is not None:
        stmt = stmt.where(Artifact.version == version)
    else:
        stmt = stmt.order_by(Artifact.version.is_(None), Artifact.version.desc(), Artifact.id.desc())
    return session.execute(stmt).scalars().first()


@app.command("resolve")
def resolve(
    canonical: str = typer.Option(..., "--canonical", help="Canonical URL to resolve"),
    version: Optional[str] = typer.Option(None, "--version", help="Optional version"),
) -> None:
    """Resolve a canonical URL to stored artifact metadata and resource JSON."""
    with SessionLocal() as session:
        artifact = pick_artifact(session, canonical, version)
        if not artifact:
            typer.echo(json.dumps({"error": "not found"}, indent=2))
            raise typer.Exit(code=1)

        resource_path = PROJECT_ROOT / artifact.file_path
        with resource_path.open() as handle:
            resource = json.load(handle)

        payload = {
            "id": artifact.id,
            "package_id": artifact.package_id,
            "resource_type": artifact.resource_type,
            "canonical_url": artifact.canonical_url,
            "version": artifact.version,
            "name": artifact.name,
            "title": artifact.title,
            "sd_type": artifact.sd_type,
            "base_definition": artifact.base_definition,
            "file_path": artifact.file_path,
            "sha256": artifact.sha256,
            "indexed_at": artifact.indexed_at.isoformat() if artifact.indexed_at else None,
            "resource": resource,
        }
        typer.echo(json.dumps(payload, indent=2))


@app.command("load-sd-elements")
def load_sd_elements_cmd(
    ig: str = typer.Option(..., "--ig", help="IG code, e.g., ps-ca"),
    ig_version: str = typer.Option(..., "--ig-version", help="IG version, e.g., 2.1.1"),
    truncate: bool = typer.Option(
        False,
        "--truncate",
        "--reset",
        help="Delete existing sd_elements for this IG/version before loading.",
    ),
) -> None:
    """Populate sd_elements for the given IG and version."""
    summary = load_sd_elements(ig, ig_version, truncate=truncate)
    typer.echo(json.dumps(summary, indent=2))


if __name__ == "__main__":
    app()
