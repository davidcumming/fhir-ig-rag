"""add sd_bindings and sd_constraints

Revision ID: 7f2b2b8c9f4e
Revises: 1d3a0c4c0c2d
Create Date: 2026-02-05 19:10:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "7f2b2b8c9f4e"
down_revision: Union[str, Sequence[str], None] = "1d3a0c4c0c2d"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "sd_bindings",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("artifact_id", sa.Integer(), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sd_canonical_url", sa.Text(), nullable=False),
        sa.Column("sd_version", sa.Text(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("strength", sa.Text(), nullable=True),
        sa.Column("value_set", sa.Text(), nullable=True),
        sa.Column("binding_json", postgresql.JSONB(), nullable=True),
        sa.Column("source_choice", sa.Text(), nullable=False),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
    )
    op.create_index(
        "uq_sd_binding_artifact_path_vs",
        "sd_bindings",
        ["artifact_id", "path", sa.text("coalesce(value_set, '')")],
        unique=True,
    )
    op.create_index("ix_sd_binding_sd_canonical_path", "sd_bindings", ["sd_canonical_url", "path"])
    op.create_index("ix_sd_binding_artifact_id", "sd_bindings", ["artifact_id"])

    op.create_table(
        "sd_constraints",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("artifact_id", sa.Integer(), sa.ForeignKey("artifacts.id", ondelete="CASCADE"), nullable=False),
        sa.Column("sd_canonical_url", sa.Text(), nullable=False),
        sa.Column("sd_version", sa.Text(), nullable=True),
        sa.Column("path", sa.Text(), nullable=False),
        sa.Column("key", sa.Text(), nullable=False),
        sa.Column("severity", sa.Text(), nullable=True),
        sa.Column("human", sa.Text(), nullable=True),
        sa.Column("expression", sa.Text(), nullable=True),
        sa.Column("xpath", sa.Text(), nullable=True),
        sa.Column("constraint_json", postgresql.JSONB(), nullable=True),
        sa.Column("source_choice", sa.Text(), nullable=False),
        sa.Column("loaded_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("NOW()")),
        sa.UniqueConstraint("artifact_id", "path", "key", name="uq_sd_constraint_artifact_path_key"),
    )
    op.create_index("ix_sd_constraint_sd_canonical_path", "sd_constraints", ["sd_canonical_url", "path"])
    op.create_index("ix_sd_constraint_artifact_id", "sd_constraints", ["artifact_id"])


def downgrade() -> None:
    op.drop_index("uq_sd_binding_artifact_path_vs", table_name="sd_bindings")
    op.drop_index("ix_sd_constraint_artifact_id", table_name="sd_constraints")
    op.drop_index("ix_sd_constraint_sd_canonical_path", table_name="sd_constraints")
    op.drop_table("sd_constraints")

    op.drop_index("ix_sd_binding_artifact_id", table_name="sd_bindings")
    op.drop_index("ix_sd_binding_sd_canonical_path", table_name="sd_bindings")
    op.drop_table("sd_bindings")
