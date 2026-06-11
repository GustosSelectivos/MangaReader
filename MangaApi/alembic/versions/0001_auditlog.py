"""create_apicore_auditlog

Revision ID: 0001_auditlog
Revises:
Create Date: 2026-06-11

Crea la tabla apicore_auditlog que usa el DACAuditMiddleware.
Esta tabla NO existía en el proyecto Django original (era nueva).
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_auditlog"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "apicore_auditlog",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=True),
        sa.Column("path", sa.String(1024), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("view_name", sa.String(255), nullable=False, server_default=""),
        sa.Column("content_type_id", sa.Integer(), nullable=True),
        sa.Column("object_id", sa.String(255), nullable=True),
        sa.Column("allowed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("status_code", sa.Integer(), nullable=True),
        sa.Column("detail", sa.String(2000), nullable=False, server_default=""),
        sa.Column(
            "created",
            sa.DateTime(),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
            index=True,
        ),
        # FK a auth_user (nullable → permite logs de peticiones anónimas)
        sa.ForeignKeyConstraint(["user_id"], ["auth_user.id"], name="fk_auditlog_user"),
        # FK a django_content_type (nullable)
        sa.ForeignKeyConstraint(
            ["content_type_id"], ["django_content_type.id"],
            name="fk_auditlog_contenttype"
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    # Índice compuesto para búsquedas por usuario + fecha
    op.create_index("ix_auditlog_user_created", "apicore_auditlog", ["user_id", "created"])


def downgrade() -> None:
    op.drop_index("ix_auditlog_user_created", table_name="apicore_auditlog")
    op.drop_table("apicore_auditlog")
