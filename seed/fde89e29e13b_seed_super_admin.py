"""seed_super_admin

Revision ID: fde89e29e13b
Revises: 6708ab30a4cc
Create Date: 2025-03-20 21:08:16.692869

"""
from uuid import uuid4
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from bookstore.auth.utils import get_password_hash
from bookstore.config import config


# revision identifiers, used by Alembic.
revision: str = 'fde89e29e13b'
down_revision: Union[str, None] = '6708ab30a4cc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id FROM users WHERE role='admin' LIMIT 1")
    ).fetchone()

    if not result:
        admin_id = uuid4()
        hashed_password = get_password_hash(config.ADMIN_PASSWORD.get_secret_value())
        conn.execute(
            sa.text(
                "INSERT INTO users (id, email, hashed_password, role, is_active, is_superuser) VALUES (:admin_id, :email, :hashed_password, :role, :is_active, :is_superuser)"
            ).bindparams(
                admin_id=admin_id,
                email=config.ADMIN_EMAIL,
                hashed_password=hashed_password,
                role="admin",
                is_active=True,
                is_superuser=True,
            )
        )
        print(f"Super admin created {config.ADMIN_EMAIL} with ID: ", admin_id)


def downgrade() -> None:
    pass
