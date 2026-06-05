"""EMI / loan computations and payment progression."""

from __future__ import annotations

from decimal import Decimal

from app.models.emi import EMI
from app.utils.dates import add_months
from app.utils.finance import emi_amount, money, percent


def ensure_schedule(emi: EMI) -> None:
    """Fill EMI amount / total payable from principal+rate+tenure if missing."""
    if not emi.emi_amount or Decimal(str(emi.emi_amount)) == 0:
        emi.emi_amount = emi_amount(
            Decimal(str(emi.principal_amount)),
            Decimal(str(emi.interest_rate or 0)),
            emi.tenure_months,
        )
    if not emi.total_payable or Decimal(str(emi.total_payable)) == 0:
        emi.total_payable = money(Decimal(str(emi.emi_amount)) * emi.tenure_months)


def outstanding(emi: EMI) -> Decimal:
    total = Decimal(str(emi.total_payable or 0))
    return money(max(total - Decimal(str(emi.amount_paid)), Decimal("0")))


def remaining_months(emi: EMI) -> int:
    return max(emi.tenure_months - emi.months_paid, 0)


def progress_percent(emi: EMI) -> float:
    return min(
        percent(Decimal(str(emi.amount_paid)), Decimal(str(emi.total_payable or 0))),
        100.0,
    )


def record_payment(emi: EMI) -> None:
    """Apply one EMI payment and advance the due date."""
    emi.months_paid = emi.months_paid + 1
    emi.amount_paid = money(Decimal(str(emi.amount_paid)) + Decimal(str(emi.emi_amount)))
    emi.next_due_date = add_months(emi.next_due_date, 1)
    if emi.months_paid >= emi.tenure_months:
        emi.is_active = False
