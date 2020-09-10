"""Initial

Revision ID: 7170945ad94d
Revises: 
Create Date: 2020-09-10 02:17:28.928184

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "7170945ad94d"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table(
        "cities",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("state_code", sa.String(length=2), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "_name_state_code_index", "cities", ["name", "state_code"], unique=True
    )
    op.create_table(
        "requests",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zipcode", sa.String(length=5), nullable=False),
        sa.Column("client_identifier", sa.String(length=100), nullable=False),
        sa.Column(
            "client_identifier_type",
            sa.Enum("PHONE_NUMBER", "IP", name="clientidentifiertype"),
            nullable=False,
        ),
        sa.Column("count", sa.Integer(), nullable=False),
        sa.Column("first_ts", sa.Integer(), nullable=False),
        sa.Column("last_ts", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "_zipcode_client_identifier_client_identifier_type_index",
        "requests",
        ["zipcode", "client_identifier", "client_identifier_type"],
        unique=True,
    )
    op.create_index(op.f("ix_requests_zipcode"), "requests", ["zipcode"], unique=False)
    op.create_table(
        "sensors",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("latest_reading", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(), nullable=False),
        sa.Column("longitude", sa.Float(), nullable=False),
        sa.Column("geohash_bit_1", sa.String(), nullable=False),
        sa.Column("geohash_bit_2", sa.String(), nullable=False),
        sa.Column("geohash_bit_3", sa.String(), nullable=False),
        sa.Column("geohash_bit_4", sa.String(), nullable=False),
        sa.Column("geohash_bit_5", sa.String(), nullable=False),
        sa.Column("geohash_bit_6", sa.String(), nullable=False),
        sa.Column("geohash_bit_7", sa.String(), nullable=False),
        sa.Column("geohash_bit_8", sa.String(), nullable=False),
        sa.Column("geohash_bit_9", sa.String(), nullable=False),
        sa.Column("geohash_bit_10", sa.String(), nullable=False),
        sa.Column("geohash_bit_11", sa.String(), nullable=False),
        sa.Column("geohash_bit_12", sa.String(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "zipcodes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("zipcode", sa.String(), nullable=False),
        sa.Column("city_id", sa.Integer(), nullable=False),
        sa.Column("latitude", sa.Float(asdecimal=True), nullable=False),
        sa.Column("longitude", sa.Float(asdecimal=True), nullable=False),
        sa.Column("geohash_bit_1", sa.String(), nullable=False),
        sa.Column("geohash_bit_2", sa.String(), nullable=False),
        sa.Column("geohash_bit_3", sa.String(), nullable=False),
        sa.Column("geohash_bit_4", sa.String(), nullable=False),
        sa.Column("geohash_bit_5", sa.String(), nullable=False),
        sa.Column("geohash_bit_6", sa.String(), nullable=False),
        sa.Column("geohash_bit_7", sa.String(), nullable=False),
        sa.Column("geohash_bit_8", sa.String(), nullable=False),
        sa.Column("geohash_bit_9", sa.String(), nullable=False),
        sa.Column("geohash_bit_10", sa.String(), nullable=False),
        sa.Column("geohash_bit_11", sa.String(), nullable=False),
        sa.Column("geohash_bit_12", sa.String(), nullable=False),
        sa.ForeignKeyConstraint(["city_id"], ["cities.id"],),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_zipcodes_zipcode"), "zipcodes", ["zipcode"], unique=True)
    op.create_table(
        "sensors_zipcodes",
        sa.Column("sensor_id", sa.Integer(), nullable=False),
        sa.Column("zipcode_id", sa.Integer(), nullable=False),
        sa.Column("distance", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["sensor_id"], ["sensors.id"],),
        sa.ForeignKeyConstraint(["zipcode_id"], ["zipcodes.id"],),
        sa.PrimaryKeyConstraint("sensor_id", "zipcode_id"),
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table("sensors_zipcodes")
    op.drop_index(op.f("ix_zipcodes_zipcode"), table_name="zipcodes")
    op.drop_table("zipcodes")
    op.drop_table("sensors")
    op.drop_index(op.f("ix_requests_zipcode"), table_name="requests")
    op.drop_index(
        "_zipcode_client_identifier_client_identifier_type_index", table_name="requests"
    )
    op.drop_table("requests")
    op.drop_index("_name_state_code_index", table_name="cities")
    op.drop_table("cities")
    # ### end Alembic commands ###
