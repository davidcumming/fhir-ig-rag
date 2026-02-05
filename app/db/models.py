from __future__ import annotations

from datetime import datetime

from sqlalchemy import (
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Text,
    UniqueConstraint,
    Boolean,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .base import Base


class Package(Base):
    __tablename__ = "packages"
    __table_args__ = (UniqueConstraint("ig", "ig_version", name="uq_package_ig_version"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    ig: Mapped[str] = mapped_column(Text, nullable=False)
    ig_version: Mapped[str] = mapped_column(Text, nullable=False)
    imported_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    source_path: Mapped[str] = mapped_column(Text, nullable=False)

    artifacts: Mapped[list["Artifact"]] = relationship(
        "Artifact", back_populates="package", cascade="all, delete-orphan"
    )


class Artifact(Base):
    __tablename__ = "artifacts"
    __table_args__ = (
        Index(
            "uq_artifact_pkg_url_version",
            "package_id",
            "canonical_url",
            text("coalesce(version, '')"),
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    package_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("packages.id", ondelete="CASCADE"), nullable=False
    )
    resource_type: Mapped[str] = mapped_column(Text, nullable=False)
    canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str | None] = mapped_column(Text, nullable=True)
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    sd_type: Mapped[str | None] = mapped_column(Text, nullable=True)
    base_definition: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_path: Mapped[str] = mapped_column(Text, nullable=False)
    sha256: Mapped[str] = mapped_column(Text, nullable=False)
    indexed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    package: Mapped[Package] = relationship("Package", back_populates="artifacts")
    sd_elements: Mapped[list["SDElement"]] = relationship(
        "SDElement", back_populates="artifact", cascade="all, delete-orphan"
    )


class SDElement(Base):
    __tablename__ = "sd_elements"
    __table_args__ = (
        UniqueConstraint("artifact_id", "path", name="uq_sd_element_artifact_path"),
        Index("ix_sd_element_sd_canonical_path", "sd_canonical_url", "path"),
        Index("ix_sd_element_artifact_id", "artifact_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    artifact_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False
    )
    sd_canonical_url: Mapped[str] = mapped_column(Text, nullable=False)
    sd_version: Mapped[str | None] = mapped_column(Text, nullable=True)
    element_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    path: Mapped[str] = mapped_column(Text, nullable=False)
    min: Mapped[int | None] = mapped_column(Integer, nullable=True)
    max: Mapped[str | None] = mapped_column(Text, nullable=True)
    must_support: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_modifier: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    is_summary: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    types_json: Mapped[dict | list | None] = mapped_column(JSONB, nullable=True)
    slicing_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    raw_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    source_choice: Mapped[str] = mapped_column(Text, nullable=False)
    loaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )

    artifact: Mapped[Artifact] = relationship("Artifact", back_populates="sd_elements")
