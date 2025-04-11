"""Add species, animal_name, and symptoms to Uzsakymas

Revision ID: 6f7b3b542b0d
Revises: add_unique_constraint
Create Date: 2024-12-09 19:24:27.055054

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy import inspect


# revision identifiers, used by Alembic.
revision = '6f7b3b542b0d'
down_revision = 'add_unique_constraint'
branch_labels = None
depends_on = None


def column_exists(table_name, column_name):
    """
    Check if a column exists in a table.
    """
    inspector = inspect(op.get_bind())
    return column_name in [col['name'] for col in inspector.get_columns(table_name)]


def upgrade():
    # Add the new columns with a default value if they don't already exist
    with op.batch_alter_table('uzsakymas', schema=None) as batch_op:
        if not column_exists('uzsakymas', 'species'):
            batch_op.add_column(sa.Column('species', sa.String(length=150), nullable=False, server_default="Unknown"))
        if not column_exists('uzsakymas', 'animal_name'):
            batch_op.add_column(sa.Column('animal_name', sa.String(length=150), nullable=False, server_default="Unknown"))
        if not column_exists('uzsakymas', 'symptoms'):
            batch_op.add_column(sa.Column('symptoms', sa.Text(), nullable=True))

    # Remove the default value after the column is added (optional)
    with op.batch_alter_table('uzsakymas', schema=None) as batch_op:
        if column_exists('uzsakymas', 'species'):
            batch_op.alter_column('species', server_default=None)
        if column_exists('uzsakymas', 'animal_name'):
            batch_op.alter_column('animal_name', server_default=None)


def downgrade():
    # Remove the columns if they exist
    with op.batch_alter_table('uzsakymas', schema=None) as batch_op:
        if column_exists('uzsakymas', 'symptoms'):
            batch_op.drop_column('symptoms')
        if column_exists('uzsakymas', 'animal_name'):
            batch_op.drop_column('animal_name')
        if column_exists('uzsakymas', 'species'):
            batch_op.drop_column('species')
