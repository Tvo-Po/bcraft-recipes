"""images

Revision ID: 22d7c5661546
Revises: 4982ea669b72
Create Date: 2023-04-26 23:38:47.631182

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '22d7c5661546'
down_revision = '4982ea669b72'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('image',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('path', sa.String(), nullable=False),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_image_id'), 'image', ['id'], unique=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_image_id'), table_name='image')
    op.drop_table('image')
    # ### end Alembic commands ###
