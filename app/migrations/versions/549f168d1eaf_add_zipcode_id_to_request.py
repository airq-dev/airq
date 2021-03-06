"""Add zipcode_id to request

Revision ID: 549f168d1eaf
Revises: a13a0afec250
Create Date: 2020-09-14 06:53:25.966624

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "549f168d1eaf"
down_revision = "a13a0afec250"
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column("requests", sa.Column("zipcode_id", sa.Integer(), nullable=True))
    op.create_foreign_key(
        "requests_zipcode_id_fkey", "requests", "zipcodes", ["zipcode_id"], ["id"]
    )
    # ### end Alembic commands ###
    conn = op.get_bind()
    res = conn.execute("SELECT id, zipcode FROM requests")
    if res is None:
        print("Skipping data migration because Alembic is running with --sql")
        return

    for request_id, zipcode in res.fetchall():
        res = conn.execute("SELECT id FROM zipcodes WHERE zipcode=%s", zipcode)
        row = res.fetchone()
        if not res:
            raise Exception(f"Unknown zipcode {zipcode}")
        conn.execute(
            "UPDATE requests SET zipcode_id=%s WHERE id=%s", row[0], request_id
        )


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column(
        "requests",
        sa.Column("zipcode", sa.VARCHAR(length=5), autoincrement=False, nullable=False),
    )
    # ### end Alembic commands ###
