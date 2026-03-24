"""enable pg_trgm and create index

Revision ID: 742352330c77
Revises: ff397fc6fca2
Create Date: 2026-03-21 11:08:24.522952

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '742352330c77'
down_revision: Union[str, Sequence[str], None] = 'ff397fc6fca2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    op.execute("CREATE INDEX idx_gene_sequence_trgm ON genes USING gin (sequence gin_trgm_ops)")
    pass


def downgrade() -> None:
    op.execute("DROP INDEX idx_gene_sequence_trgm")
    pass
