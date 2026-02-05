"""create packages and artifacts

Revision ID: 4ffc445ce723
Revises: 
Create Date: 2026-02-05 17:26:31.112950

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4ffc445ce723'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "packages",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("ig", sa.Text(), nullable=False),
        sa.Column("ig_version", sa.Text(), nullable=False),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.UniqueConstraint("ig", "ig_version", name="uq_package_ig_version"),
    )

    op.create_table(
        "artifacts",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("package_id", sa.Integer(), sa.ForeignKey("packages.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_type", sa.Text(), nullable=False),
        sa.Column("canonical_url", sa.Text(), nullable=False),
        sa.Column("version", sa.Text(), nullable=True),
        sa.Column("name", sa.Text(), nullable=True),
        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("sd_type", sa.Text(), nullable=True),
        sa.Column("base_definition", sa.Text(), nullable=True),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("sha256", sa.Text(), nullable=False),
        sa.Column(
            "indexed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )

    op.create_index(
        "ix_artifact_package_id",
        "artifacts",
        ["package_id"],
    )
    op.execute(
        sa.text(
            "CREATE UNIQUE INDEX uq_artifact_pkg_url_version "
            "ON artifacts (package_id, canonical_url, coalesce(version, ''))"
        )
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.execute(sa.text("DROP INDEX IF EXISTS uq_artifact_pkg_url_version"))
    op.drop_index("ix_artifact_package_id", table_name="artifacts")
    op.drop_table("artifacts")
    op.drop_table("packages")
