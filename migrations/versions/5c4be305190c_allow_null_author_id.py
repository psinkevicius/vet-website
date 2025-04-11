"""Allow null author id

Revision ID: 5c4be305190c
Revises: 7d7152155100
Create Date: 2025-01-01 18:44:59.178952

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5c4be305190c'
down_revision = '7d7152155100'
branch_labels = None
depends_on = None


def upgrade():
    connection = op.get_bind()

    # Check if feedback_old exists and drop it if necessary
    feedback_old_exists = connection.execute(
        sa.text(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='feedback_old';"
        )
    ).fetchone()
    if feedback_old_exists:
        connection.execute(sa.text("DROP TABLE feedback_old"))

    # Rename the original table to feedback_old
    op.rename_table('feedback', 'feedback_old')

    # Create a new table with the updated schema
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('author_id', sa.Integer, sa.ForeignKey('user.id', ondelete="SET NULL"), nullable=True),
        sa.Column('comment', sa.Text, nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('date_posted', sa.DateTime, default=sa.func.now())
    )

    # Copy data from feedback_old to feedback
    connection.execute(sa.text(
        "INSERT INTO feedback (id, author_id, comment, rating, date_posted) "
        "SELECT id, author_id, comment, rating, date_posted FROM feedback_old"
    ))

    # Drop the old table
    op.drop_table('feedback_old')


def downgrade():
    connection = op.get_bind()

    # Rename the current table to feedback_new
    op.rename_table('feedback', 'feedback_new')

    # Recreate the original table
    op.create_table(
        'feedback',
        sa.Column('id', sa.Integer, primary_key=True),
        sa.Column('author_id', sa.Integer, sa.ForeignKey('user.id', ondelete="NO ACTION"), nullable=True),
        sa.Column('comment', sa.Text, nullable=False),
        sa.Column('rating', sa.Integer, nullable=False),
        sa.Column('date_posted', sa.DateTime, default=sa.func.now())
    )

    # Copy data from feedback_new to feedback
    connection.execute(sa.text(
        "INSERT INTO feedback (id, author_id, comment, rating, date_posted) "
        "SELECT id, author_id, comment, rating, date_posted FROM feedback_new"
    ))

    # Drop the new table
    op.drop_table('feedback_new')
