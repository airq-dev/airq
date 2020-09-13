"""Add clients table

Revision ID: 16035f5c4c4c
Revises: 7170945ad94d
Create Date: 2020-09-13 01:35:03.336915

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.sql import table, column
from sqlalchemy.dialects.postgresql import ENUM


# revision identifiers, used by Alembic.
revision = "16035f5c4c4c"
down_revision = "7170945ad94d"
branch_labels = None
depends_on = None


def upgrade():
    identifier_type = ENUM(
        "PHONE_NUMBER", "IP", name="clientidentifiertype", create_type=False
    )
    clients = op.create_table(
        "clients",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("identifier", sa.String(), nullable=False),
        sa.Column("type_code", identifier_type, nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "_client_identifier_type_code",
        "clients",
        ["identifier", "type_code"],
        unique=True,
    )
    op.add_column("requests", sa.Column("client_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "requests_client_id_fk", "requests", "clients", ["client_id"], ["id"]
    )
    conn = op.get_bind()
    res = conn.execute(
        "SELECT id, client_id, client_identifier, client_identifier_type FROM requests"
    )
    for id, client_id, identifier, type_code in res.fetchall():
        res = conn.execute(
            "SELECT id FROM clients WHERE identifier=%s AND type_code=%s",
            identifier,
            type_code,
        )
        row = res.fetchone()
        if row:
            if not client_id:
                res = conn.execute(
                    "UPDATE requests SET client_id=%s WHERE id=%s", row[0], id
                )
        else:
            res = conn.execute(
                clients.insert().values(identifier=identifier, type_code=type_code)
            )
            last_pk = res.inserted_primary_key[0]
            res = conn.execute(
                "UPDATE requests SET client_id=%s WHERE id=%s", last_pk, id
            )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_constraint("requests_client_id_fk", "requests", type_="foreignkey")
    op.drop_column("requests", "client_id")
    op.drop_index("_client_identifier_type_code", table_name="clients")
    op.drop_table("clients")
    # ### end Alembic commands ###
