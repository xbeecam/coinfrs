"""Add sub-account support to DataSource model

Revision ID: ad0a3c00ad72
Revises: 745089f4539e
Create Date: 2025-07-26 09:56:19.520802

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad0a3c00ad72'
down_revision: Union[str, None] = '745089f4539e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns to datasource table
    op.add_column('datasource', sa.Column('email', sa.String(), nullable=True))
    op.add_column('datasource', sa.Column('parent_id', sa.Integer(), nullable=True))
    op.add_column('datasource', sa.Column('is_main_account', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('datasource', sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'))
    op.add_column('datasource', sa.Column('last_sync_at', sa.DateTime(), nullable=True))
    op.add_column('datasource', sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    op.add_column('datasource', sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')))
    
    # Create index on email for faster lookups
    op.create_index(op.f('ix_datasource_email'), 'datasource', ['email'], unique=False)
    
    # Create foreign key constraint for parent_id
    op.create_foreign_key('fk_datasource_parent_id', 'datasource', 'datasource', ['parent_id'], ['id'])


def downgrade() -> None:
    # Drop foreign key constraint
    op.drop_constraint('fk_datasource_parent_id', 'datasource', type_='foreignkey')
    
    # Drop index
    op.drop_index(op.f('ix_datasource_email'), table_name='datasource')
    
    # Drop columns
    op.drop_column('datasource', 'updated_at')
    op.drop_column('datasource', 'created_at')
    op.drop_column('datasource', 'last_sync_at')
    op.drop_column('datasource', 'is_active')
    op.drop_column('datasource', 'is_main_account')
    op.drop_column('datasource', 'parent_id')
    op.drop_column('datasource', 'email')