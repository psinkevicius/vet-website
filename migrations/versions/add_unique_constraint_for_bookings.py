"""Add unique constraint for bookings"""

from alembic import op
import sqlalchemy as sa


# Revision identifiers, used by Alembic.
revision = 'add_unique_constraint'
down_revision = None  # Update this with the ID of the previous migration if any.
branch_labels = None
depends_on = None


def upgrade():
    with op.batch_alter_table('uzsakymas') as batch_op:
        batch_op.create_unique_constraint(
            'unique_booking_per_employee', ['user_id', 'date', 'time']
        )


def downgrade():
    with op.batch_alter_table('uzsakymas') as batch_op:
        batch_op.drop_constraint('unique_booking_per_employee', type_='unique')
