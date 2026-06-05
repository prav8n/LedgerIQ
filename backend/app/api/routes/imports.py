"""CSV / XLSX import routes (expenses)."""

from __future__ import annotations

import json
from datetime import date

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status

from app.core.dependencies import CurrentUser, SessionDep
from app.models.enums import ExpenseCategory, PaymentMethod
from app.models.expense import Expense
from app.schemas.import_data import ImportPreview, ImportResult, ImportRowError
from app.services import import_service
from app.services.categorization_service import get_categorizer
from app.services.summary_service import get_summary_service

router = APIRouter(prefix="/import", tags=["Import"])

_MAX_BYTES = 5 * 1024 * 1024  # 5 MB


def _enum_or_none(enum_cls, value: str):
    value = (value or "").strip().lower().replace(" ", "_")
    if not value:
        return None
    for member in enum_cls:
        if member.value == value:
            return member
    return None


@router.post("/expenses/preview", response_model=ImportPreview, summary="Preview an import")
async def preview_import(
    current_user: CurrentUser,
    file: UploadFile = File(...),
) -> ImportPreview:
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large (max 5 MB)")
    try:
        headers, rows = import_service.parse_upload(file.filename or "", content)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))

    return ImportPreview(
        headers=headers,
        suggested_mapping=import_service.suggest_mapping(headers),
        sample_rows=rows[:5],
        total_rows=len(rows),
    )


@router.post("/expenses", response_model=ImportResult, summary="Commit an import")
async def commit_import(
    current_user: CurrentUser,
    db: SessionDep,
    file: UploadFile = File(...),
    mapping: str = Form(..., description="JSON object: field -> source header"),
) -> ImportResult:
    content = await file.read()
    if len(content) > _MAX_BYTES:
        raise HTTPException(status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, "File too large (max 5 MB)")
    try:
        headers, rows = import_service.parse_upload(file.filename or "", content)
        field_map: dict[str, str | None] = json.loads(mapping)
    except ValueError as exc:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, str(exc))
    except json.JSONDecodeError:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Invalid mapping JSON")

    date_col = field_map.get("transaction_date")
    amount_col = field_map.get("amount")
    if not date_col or not amount_col:
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            "Mapping must include 'transaction_date' and 'amount'",
        )

    categorizer = get_categorizer()
    created = 0
    skipped = 0
    errors: list[ImportRowError] = []
    affected: set[tuple[int, int]] = set()

    def col(row: dict[str, str], field: str) -> str:
        header = field_map.get(field)
        return row.get(header, "") if header else ""

    for index, row in enumerate(rows, start=2):  # row 1 = header
        txn_date = import_service.coerce_date(row.get(date_col, ""))
        amount = import_service.coerce_amount(row.get(amount_col, ""))
        if txn_date is None:
            skipped += 1
            errors.append(ImportRowError(row=index, error="Unparseable or missing date"))
            continue
        if amount is None or amount <= 0:
            skipped += 1
            errors.append(ImportRowError(row=index, error="Unparseable or non-positive amount"))
            continue

        merchant = col(row, "merchant").strip() or None
        description = col(row, "description").strip() or None
        category = _enum_or_none(ExpenseCategory, col(row, "category"))
        payment_method = _enum_or_none(PaymentMethod, col(row, "payment_method")) or PaymentMethod.UPI

        expense = Expense(
            user_id=current_user.id,
            amount=amount,
            merchant=merchant,
            description=description,
            payment_method=payment_method,
            transaction_date=txn_date,
        )
        if category is not None:
            expense.category = category
            expense.is_ai_categorized = False
        else:
            result = await categorizer.categorize(
                merchant=merchant, description=description, amount=float(amount)
            )
            expense.category = result.category
            expense.is_ai_categorized = True

        db.add(expense)
        created += 1
        affected.add((txn_date.year, txn_date.month))

    await db.flush()
    summary_service = get_summary_service()
    for year, month in affected:
        await summary_service.recompute_month(db, user_id=current_user.id, year=year, month=month)

    return ImportResult(created=created, skipped=skipped, errors=errors[:50])
