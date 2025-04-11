"""Add ForeignKey to Feedback table

Revision ID: 7d7152155100
Revises: 0bcb00098c29
Create Date: 2024-12-22 00:45:50.247937

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7d7152155100'
down_revision = '0bcb00098c29'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        batch_op.add_column(sa.Column('author_id', sa.Integer(), nullable=False))
        batch_op.add_column(sa.Column('rating', sa.Integer(), nullable=False))
        batch_op.create_foreign_key('fk_feedback_author_id', 'user', ['author_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('feedback', schema=None) as batch_op:
        # Specify the constraint name explicitly for dropping
        batch_op.drop_constraint('fk_feedback_author_id', type_='foreignkey')
        batch_op.drop_column('rating')
        batch_op.drop_column('author_id')

    # ### end Alembic commands ###
