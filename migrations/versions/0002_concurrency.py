"""Optimistic versions and tenant-scoped idempotency/singleton keys."""
from alembic import op
import sqlalchemy as sa

revision = '0002'
down_revision = '0001'


def upgrade():
    with op.batch_alter_table('records') as batch:
        batch.add_column(sa.Column('resource_key', sa.String(160), nullable=True))
        batch.add_column(sa.Column('version', sa.Integer(), nullable=False, server_default='1'))
        batch.create_unique_constraint('uq_resource_key', ['tenant_id','kind','resource_key'])


def downgrade():
    with op.batch_alter_table('records') as batch:
        batch.drop_constraint('uq_resource_key', type_='unique')
        batch.drop_column('version')
        batch.drop_column('resource_key')
