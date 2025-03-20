"""seed_super_admin

Revision ID: 20df57e102e3
Revises: f46187300410
Create Date: 2025-03-20 23:18:42.885538

"""
from uuid import uuid4
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

from bookstore.auth.utils import get_password_hash
from bookstore.auth.models import UserRole
from bookstore.config import config


# revision identifiers, used by Alembic.
revision: str = '20df57e102e3'
down_revision: Union[str, None] = 'f46187300410'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    conn = op.get_bind()
    result = conn.execute(
        sa.text("SELECT id FROM users WHERE role='ADMIN' LIMIT 1")
    ).fetchone()

    if not result:
        admin_id = uuid4()
        hashed_password = get_password_hash(config.ADMIN_PASSWORD.get_secret_value())
        conn.execute(
            sa.text(
                "INSERT INTO users (id, email, hashed_password, role, is_active, is_superuser) VALUES (:admin_id, :email, :hashed_password, 'ADMIN', :is_active, :is_superuser)"
            ).bindparams(
                admin_id=admin_id,
                email=config.ADMIN_EMAIL,
                hashed_password=hashed_password,
                is_active=True,
                is_superuser=True,
            )
        )
        print(f"Super admin created {config.ADMIN_EMAIL} with ID: ", admin_id)


def downgrade() -> None:
    pass
