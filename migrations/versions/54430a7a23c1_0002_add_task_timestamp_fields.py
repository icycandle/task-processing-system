"""0002 add task timestamp fields

Revision ID: 54430a7a23c1
Revises: 24757941f6cc
Create Date: 2024-11-12 13:31:42.879833

"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "54430a7a23c1"
down_revision: Union[str, None] = "24757941f6cc"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("tasks", sa.Column("created_at", sa.DateTime(), nullable=True))

    op.execute("UPDATE tasks SET created_at = NOW() WHERE created_at IS NULL")
    op.alter_column("tasks", "created_at", nullable=False)

    op.create_index("idx_tasks_id", "tasks", ["id"])
    op.create_index("idx_tasks_status", "tasks", ["status"])
    op.create_index("idx_tasks_status_created_at", "tasks", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("idx_tasks_id", table_name="tasks")
    op.drop_index("idx_tasks_status", table_name="tasks")
    op.drop_index("idx_tasks_status_created_at", table_name="tasks")

    op.drop_column("tasks", "created_at")
