"""reward rules table, expanded credit card fields, preset data migration

Revision ID: b1f2c3d4e5a6
Revises: 397a73cf3475
Create Date: 2026-06-05 18:00:00.000000

"""
from decimal import Decimal
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1f2c3d4e5a6'
down_revision: Union[str, None] = '397a73cf3475'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


_REWARD_TYPE = sa.Enum(
    'CASHBACK', 'REWARD_POINTS', 'AIR_MILES', 'MILESTONE_BONUS',
    'LOUNGE_ACCESS', 'FEE_WAIVER', 'VOUCHER',
    name='rewardtype', native_enum=False, length=20,
)
_APPLIES_TO = sa.Enum(
    'ONLINE', 'OFFLINE', 'UPI', 'MERCHANT_SPECIFIC', 'CATEGORY_SPECIFIC', 'ALL',
    name='rewardappliesto', native_enum=False, length=20,
)

# Preset cards -> reward rule (matches the old code-based engine exactly).
# A preset applies when both substrings are found (issuer, card_name lowered).
_PRESETS = [
    {
        "match": ("sbi", "cashback"),
        "rule_name": "5% Cashback Online",
        "reward_type": "CASHBACK", "reward_rate": Decimal("5"), "point_value": Decimal("1"),
        "applies_to": "ONLINE", "merchant_match": None, "min_txn_amount": None,
        "monthly_cap": Decimal("2000"),
    },
    {
        "match": ("sbi", "phonepe"),
        "rule_name": "1% Cashback on UPI",
        "reward_type": "CASHBACK", "reward_rate": Decimal("1"), "point_value": Decimal("1"),
        "applies_to": "UPI", "merchant_match": None, "min_txn_amount": None,
        "monthly_cap": None,
    },
    {
        "match": ("hdfc", "swiggy"),
        "rule_name": "10% on Swiggy",
        "reward_type": "CASHBACK", "reward_rate": Decimal("10"), "point_value": Decimal("1"),
        "applies_to": "MERCHANT_SPECIFIC", "merchant_match": "swiggy",
        "min_txn_amount": Decimal("249"), "monthly_cap": None,
    },
    {
        "match": ("icici", "amazon"),
        "rule_name": "5% on Amazon",
        "reward_type": "CASHBACK", "reward_rate": Decimal("5"), "point_value": Decimal("1"),
        "applies_to": "MERCHANT_SPECIFIC", "merchant_match": "amazon",
        "min_txn_amount": None, "monthly_cap": None,
    },
]


def upgrade() -> None:
    # 1) New credit-card columns (all nullable -> no backfill needed).
    with op.batch_alter_table('credit_cards', schema=None) as batch_op:
        batch_op.add_column(sa.Column('card_color', sa.String(length=20), nullable=True))
        batch_op.add_column(sa.Column('billing_cycle_day', sa.Integer(), nullable=True))
        batch_op.add_column(
            sa.Column('fee_waiver_spend_threshold', sa.Numeric(precision=14, scale=2),
                      nullable=True)
        )

    # 2) reward_rules table.
    op.create_table(
        'reward_rules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('card_id', sa.Integer(), nullable=False),
        sa.Column('rule_name', sa.String(length=120), nullable=False),
        sa.Column('reward_type', _REWARD_TYPE, nullable=False),
        sa.Column('reward_rate', sa.Numeric(precision=10, scale=4), nullable=False),
        sa.Column('point_value', sa.Numeric(precision=10, scale=4), nullable=True),
        sa.Column('applies_to', _APPLIES_TO, nullable=False),
        sa.Column('merchant_match', sa.String(length=120), nullable=True),
        sa.Column('category_match', sa.String(length=60), nullable=True),
        sa.Column('min_txn_amount', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('monthly_cap', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('milestone_threshold', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('milestone_reward', sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True),
                  server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=False),
        sa.ForeignKeyConstraint(['card_id'], ['credit_cards.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    with op.batch_alter_table('reward_rules', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_reward_rules_card_id'), ['card_id'], unique=False)

    # 3) Data migration: seed preset reward rules for existing matching cards so
    #    their cashback numbers stay identical to the old engine.
    bind = op.get_bind()
    cards = bind.execute(
        sa.text("SELECT id, issuer, card_name FROM credit_cards")
    ).fetchall()

    rules_table = sa.table(
        'reward_rules',
        sa.column('card_id', sa.Integer),
        sa.column('rule_name', sa.String),
        sa.column('reward_type', sa.String),
        sa.column('reward_rate', sa.Numeric),
        sa.column('point_value', sa.Numeric),
        sa.column('applies_to', sa.String),
        sa.column('merchant_match', sa.String),
        sa.column('min_txn_amount', sa.Numeric),
        sa.column('monthly_cap', sa.Numeric),
    )

    to_insert = []
    for card_id, issuer, card_name in cards:
        issuer_l = (issuer or "").lower()
        name_l = (card_name or "").lower()
        for preset in _PRESETS:
            a, b = preset["match"]
            if a in issuer_l and b in name_l:
                to_insert.append({
                    "card_id": card_id,
                    "rule_name": preset["rule_name"],
                    "reward_type": preset["reward_type"],
                    "reward_rate": preset["reward_rate"],
                    "point_value": preset["point_value"],
                    "applies_to": preset["applies_to"],
                    "merchant_match": preset["merchant_match"],
                    "min_txn_amount": preset["min_txn_amount"],
                    "monthly_cap": preset["monthly_cap"],
                })
    if to_insert:
        op.bulk_insert(rules_table, to_insert)


def downgrade() -> None:
    with op.batch_alter_table('reward_rules', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_reward_rules_card_id'))
    op.drop_table('reward_rules')
    with op.batch_alter_table('credit_cards', schema=None) as batch_op:
        batch_op.drop_column('fee_waiver_spend_threshold')
        batch_op.drop_column('billing_cycle_day')
        batch_op.drop_column('card_color')
