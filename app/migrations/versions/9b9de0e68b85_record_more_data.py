"""record more data

Revision ID: 9b9de0e68b85
Revises: d6f61308fc1c
Create Date: 2020-11-01 23:38:30.694006

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9b9de0e68b85'
down_revision = 'd6f61308fc1c'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('clients', sa.Column('last_humidity', sa.Float(), nullable=True))
    op.add_column('clients', sa.Column('last_pm25_10', sa.Float(), nullable=True))
    op.add_column('clients', sa.Column('pref_json', sa.JSON(), nullable=True))
    op.add_column('sensors', sa.Column('humidity', sa.Float(), nullable=True))
    op.add_column('sensors', sa.Column('pm25_10', sa.Float(), nullable=True))
    op.add_column('zipcodes', sa.Column('humidity', sa.Float(), server_default='0', nullable=False))
    op.add_column('zipcodes', sa.Column('pm25_10', sa.Float(), server_default='0', nullable=False))
    op.create_index(op.f('ix_zipcodes_pm25_10'), 'zipcodes', ['pm25_10'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_zipcodes_pm25_10'), table_name='zipcodes')
    op.drop_column('zipcodes', 'pm25_10')
    op.drop_column('zipcodes', 'humidity')
    op.drop_column('sensors', 'pm25_10')
    op.drop_column('sensors', 'humidity')
    op.drop_column('clients', 'pref_json')
    op.drop_column('clients', 'last_pm25_10')
    op.drop_column('clients', 'last_humidity')
    # ### end Alembic commands ###