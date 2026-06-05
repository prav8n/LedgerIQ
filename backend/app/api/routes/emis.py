"""EMI / loan CRUD plus a payment endpoint."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import select

from app.core.dependencies import CurrentUser, SessionDep
from app.models.emi import EMI
from app.schemas.emi import EMICreate, EMIRead, EMIUpdate
from app.services import emi_service

router = APIRouter(prefix="/emis", tags=["EMIs"])


def _to_read(emi: EMI) -> EMIRead:
    return EMIRead.model_validate(
        {
            **{c.name: getattr(emi, c.name) for c in emi.__table__.columns},
            "outstanding": emi_service.outstanding(emi),
            "remaining_months": emi_service.remaining_months(emi),
            "progress_percent": emi_service.progress_percent(emi),
        }
    )


async def _get_owned(db: SessionDep, user_id: int, emi_id: int) -> EMI:
    emi = await db.get(EMI, emi_id)
    if emi is None or emi.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "EMI not found")
    return emi


@router.post("", response_model=EMIRead, status_code=status.HTTP_201_CREATED)
async def create_emi(
    payload: EMICreate, current_user: CurrentUser, db: SessionDep
) -> EMIRead:
    emi = EMI(user_id=current_user.id, **payload.model_dump())
    emi_service.ensure_schedule(emi)
    db.add(emi)
    await db.flush()
    await db.refresh(emi)
    return _to_read(emi)


@router.get("", response_model=list[EMIRead])
async def list_emis(
    current_user: CurrentUser, db: SessionDep, is_active: bool | None = None
) -> list[EMIRead]:
    filters = [EMI.user_id == current_user.id]
    if is_active is not None:
        filters.append(EMI.is_active == is_active)
    rows = (
        await db.execute(select(EMI).where(*filters).order_by(EMI.next_due_date))
    ).scalars().all()
    return [_to_read(e) for e in rows]


@router.get("/{emi_id}", response_model=EMIRead)
async def get_emi(emi_id: int, current_user: CurrentUser, db: SessionDep) -> EMIRead:
    return _to_read(await _get_owned(db, current_user.id, emi_id))


@router.put("/{emi_id}", response_model=EMIRead)
async def update_emi(
    emi_id: int, payload: EMIUpdate, current_user: CurrentUser, db: SessionDep
) -> EMIRead:
    emi = await _get_owned(db, current_user.id, emi_id)
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(emi, field, value)
    emi_service.ensure_schedule(emi)
    await db.flush()
    await db.refresh(emi)
    return _to_read(emi)


@router.post("/{emi_id}/pay", response_model=EMIRead)
async def pay_emi(emi_id: int, current_user: CurrentUser, db: SessionDep) -> EMIRead:
    emi = await _get_owned(db, current_user.id, emi_id)
    if not emi.is_active:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "Loan is already closed")
    emi_service.record_payment(emi)
    await db.flush()
    await db.refresh(emi)
    return _to_read(emi)


@router.delete(
    "/{emi_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_emi(
    emi_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    emi = await _get_owned(db, current_user.id, emi_id)
    await db.delete(emi)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
