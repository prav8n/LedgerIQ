"""subscription credit-card + reward-rule link (auto-posted charges)

Revision ID: d3b4c5e6f7a8
Revises: c2a3b4d5e6f7
Create Date: 2026-06-06 18:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd3b4c5e6f7a8'
down_revision: Union[str, None] = 'c2a3b4d5e6f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.add_column(sa.Column('credit_card_id', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('reward_rule_id', sa.Integer(), nullable=True))
        batch_op.create_index(
            batch_op.f('ix_subscriptions_credit_card_id'), ['credit_card_id'], unique=False
        )
        batch_op.create_index(
            batch_op.f('ix_subscriptions_reward_rule_id'), ['reward_rule_id'], unique=False
        )
        batch_op.create_foreign_key(
            'fk_subscriptions_credit_card_id', 'credit_cards',
            ['credit_card_id'], ['id'], ondelete='SET NULL',
        )
        batch_op.create_foreign_key(
            'fk_subscriptions_reward_rule_id', 'reward_rules',
            ['reward_rule_id'], ['id'], ondelete='SET NULL',
        )


def downgrade() -> None:
    with op.batch_alter_table('subscriptions', schema=None) as batch_op:
        batch_op.drop_constraint('fk_subscriptions_reward_rule_id', type_='foreignkey')
        batch_op.drop_constraint('fk_subscriptions_credit_card_id', type_='foreignkey')
        batch_op.drop_index(batch_op.f('ix_subscriptions_reward_rule_id'))
        batch_op.drop_index(batch_op.f('ix_subscriptions_credit_card_id'))
        batch_op.drop_column('reward_rule_id')
        batch_op.drop_column('credit_card_id')
