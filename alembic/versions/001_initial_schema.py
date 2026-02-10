"""initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-02-06 00:00:00.000000
"""

from __future__ import annotations

import sys
from pathlib import Path

from alembic import op

# Ensure project root is on sys.path for model imports.
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ghl_real_estate_ai.models.base import Base  # noqa: E402
from ghl_real_estate_ai.models import conversations, leads, properties  # noqa: F401,E402

# revision identifiers, used by Alembic.
revision = "001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create initial schema from SQLAlchemy metadata."""
    bind = op.get_bind()
    Base.metadata.create_all(bind=bind)


def downgrade() -> None:
    """Drop all schema objects created in upgrade."""
    bind = op.get_bind()
    Base.metadata.drop_all(bind=bind)
