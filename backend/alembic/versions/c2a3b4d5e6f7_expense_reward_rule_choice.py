"""expense reward-rule choice (force a specific card rule)

Revision ID: c2a3b4d5e6f7
Revises: b1f2c3d4e5a6
Create Date: 2026-06-06 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c2a3b4d5e6f7'
down_revision: Union[str, None] = 'b1f2c3d4e5a6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reward_rule_id', sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_expenses_reward_rule_id'), ['reward_rule_id'], unique=False
        )
        batch_op.create_foreign_key(
            'fk_expenses_reward_rule_id', 'reward_rules',
            ['reward_rule_id'], ['id'], ondelete='SET NULL',
        )


def downgrade() -> None:
    with op.batch_alter_table('expenses', schema=None) as batch_op:
        batch_op.drop_constraint('fk_expenses_reward_rule_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_expenses_reward_rule_id'))
        batch_op.drop_column('reward_rule_id')
