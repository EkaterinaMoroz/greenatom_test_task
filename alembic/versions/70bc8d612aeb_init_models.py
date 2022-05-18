"""Init models

Revision ID: 70bc8d612aeb
Revises: 
Create Date: 2022-05-12 16:23:30.180298

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '70bc8d612aeb'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('inbox',
    sa.Column('request_id', sa.String(), nullable=True),
    sa.Column('filename', sa.String(), nullable=False),
    sa.Column('date_registered', sa.String(), nullable=True),
    sa.PrimaryKeyConstraint('filename'),
    sa.UniqueConstraint('filename')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('inbox')
    # ### end Alembic commands ###
