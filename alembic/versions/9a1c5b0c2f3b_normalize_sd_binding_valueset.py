"""normalize sd_bindings value_set and unique constraint

Revision ID: 9a1c5b0c2f3b
Revises: 7f2b2b8c9f4e
Create Date: 2026-02-05 20:05:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "9a1c5b0c2f3b"
down_revision: Union[str, Sequence[str], None] = "7f2b2b8c9f4e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Normalize existing null value_set to empty string
    op.execute("UPDATE sd_bindings SET value_set = '' WHERE value_set IS NULL")
    # Drop old functional unique index if present
    op.execute("DROP INDEX IF EXISTS uq_sd_binding_artifact_path_vs")
    # Alter column to not null with default
    op.alter_column(
        "sd_bindings",
        "value_set",
        existing_type=sa.Text(),
        nullable=False,
        server_default="",
    )
    # Add new unique constraint
    op.create_unique_constraint(
        "uq_sd_bindings_artifact_path_valueset",
        "sd_bindings",
        ["artifact_id", "path", "value_set"],
    )


def downgrade() -> None:
    op.drop_constraint("uq_sd_bindings_artifact_path_valueset", "sd_bindings", type_="unique")
    op.alter_column(
        "sd_bindings",
        "value_set",
        existing_type=sa.Text(),
        nullable=True,
        server_default=None,
    )
    # Recreate old functional unique index (optional best-effort)
    op.execute(
        "CREATE UNIQUE INDEX IF NOT EXISTS uq_sd_binding_artifact_path_vs "
        "ON sd_bindings (artifact_id, path, coalesce(value_set, ''))"
    )
