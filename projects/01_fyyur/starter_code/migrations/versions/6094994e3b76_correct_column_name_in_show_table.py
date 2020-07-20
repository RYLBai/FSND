"""Correct column name in Show table

Revision ID: 6094994e3b76
Revises: fee7ded6fa42
Create Date: 2020-07-11 15:57:26.447500

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '6094994e3b76'
down_revision = 'fee7ded6fa42'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Show', sa.Column('artist_id', sa.Integer(), nullable=False))
    op.drop_constraint('Show_artisit_id_fkey', 'Show', type_='foreignkey')
    op.create_foreign_key(None, 'Show', 'Artist', ['artist_id'], ['id'])
    op.drop_column('Show', 'artisit_id')
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('Show', sa.Column('artisit_id', sa.INTEGER(), autoincrement=False, nullable=False))
    op.drop_constraint(None, 'Show', type_='foreignkey')
    op.create_foreign_key('Show_artisit_id_fkey', 'Show', 'Artist', ['artisit_id'], ['id'])
    op.drop_column('Show', 'artist_id')
    # ### end Alembic commands ###
