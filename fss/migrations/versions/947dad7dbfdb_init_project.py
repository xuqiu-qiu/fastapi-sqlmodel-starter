"""init project

Revision ID: 947dad7dbfdb
Revises:
Create Date: 2024-04-02 14:28:52.629148

"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "947dad7dbfdb"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # op.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "system_user",
        sa.Column("id", sa.BigInteger(), nullable=False),
        sa.Column("username", sa.String(length=32), nullable=True, comment="用户名"),
        sa.Column("password", sa.String(length=64), nullable=True, comment="密码"),
        sa.Column("nickname", sa.String(length=32), nullable=True, comment="昵称"),
        sa.Column("create_time", sa.DateTime(), nullable=True),
        sa.Column("update_time", sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        comment="用户信息表",
    )
    op.create_index(op.f("ix_system_user_id"), "system_user", ["id"], unique=False)
    op.create_index(
        op.f("ix_system_user_username"), "system_user", ["username"], unique=True
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f("ix_system_user_username"), table_name="system_user")
    op.drop_index(op.f("ix_system_user_id"), table_name="system_user")
    op.drop_table("system_user")
    # ### end Alembic commands ###