"""add sd_elements table

Revision ID: 1d3a0c4c0c2d
Revises: 4ffc445ce723
Create Date: 2026-02-05 18:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "1d3a0c4c0c2d"
down_revision: Union[str, Sequence[str], None] = "4ffc445ce723"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sd_elements",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("artifact_id", sa.Integer(), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sd_canonical_url", sa.Text(), nullable=False),
        sa.Column("sd_version", sa.Text(), nullable=True),
        sa.Column("element_id", sa.Text(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("min", sa.Integer(), nullable=True),
        sa.Column("max", sa.Text(), nullable=True),
        sa.Column("must_support", sa.Boolean(), nullable=True),
        sa.Column("is_modifier", sa.Boolean(), nullable=True),
        sa.Column("is_summary", sa.Boolean(), nullable=True),
        sa.Column("types_json", postgresql.JSONB(), nullable=True),
        sa.Column("slicing_json", postgresql.JSONB(), nullable=True),
        sa.Column("raw_json", postgresql.JSONB(), nullable=True),
        sa.Column("source_choice", sa.Text(), nullable=False),
        sa.Column(
            "loaded_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.UniqueConstraint("artifact_id", "path", name="uq_sd_element_artifact_path"),
    )
    op.create_index(
        "ix_sd_element_sd_canonical_path",
        "sd_elements",
        ["sd_canonical_url", "path"],
    )
    op.create_index(
        "ix_sd_element_artifact_id",
        "sd_elements",
        ["artifact_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_sd_element_artifact_id", table_name="sd_elements")
    op.drop_index("ix_sd_element_sd_canonical_path", table_name="sd_elements")
    op.drop_table("sd_elements")
