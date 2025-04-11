from alembic import op
import sqlalchemy as sa

# Revision identifiers, used by Alembic.
revision = 'ed7e0d21db26'
down_revision = 'a9bcfd094c3e'
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('uzsakymas', schema=None) as batch_op:
        # Step 1: Add the column as nullable initially
        batch_op.add_column(sa.Column('animal_id', sa.Integer(), nullable=True))
        # Step 2: Add a foreign key constraint
        batch_op.create_foreign_key('fk_animal_appointment', 'animal', ['animal_id'], ['id'], ondelete='CASCADE')

    # Step 3: Update all existing rows to set a default value for animal_id
    # IMPORTANT: Replace `1` with the appropriate default animal ID or handle the existing data
    op.execute("UPDATE uzsakymas SET animal_id = 1 WHERE animal_id IS NULL")

    with op.batch_alter_table('uzsakymas', schema=None) as batch_op:
        # Step 4: Alter the column to make it non-nullable
        batch_op.alter_column('animal_id', nullable=False)


def downgrade():
    with op.batch_alter_table('uzsakymas', schema=None) as batch_op:
        # Drop the foreign key constraint and the column
        batch_op.drop_constraint('fk_animal_appointment', type_='foreignkey')
        batch_op.drop_column('animal_id')
