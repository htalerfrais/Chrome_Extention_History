"""initial modular convergence schema

Revision ID: 0001_modular_convergence
Revises:
Create Date: 2026-02-27
"""

from alembic import op

# revision identifiers, used by Alembic.
revision = "0001_modular_convergence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Schema is currently managed from SQLAlchemy metadata; this migration
    # serves as the versioning baseline for future explicit DDL changes.
    pass


def downgrade() -> None:
    pass
