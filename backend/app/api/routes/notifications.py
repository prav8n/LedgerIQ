"""Notification center: list, unread count, manual scan, mark read, delete."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Response, status
from sqlalchemy import func, select, update

from app.core.dependencies import CurrentUser, SessionDep
from app.models.enums import NotificationCategory
from app.models.notification import Notification
from app.schemas.notification import NotificationRead, ScanResult, UnreadCount
from app.services import notification_service

router = APIRouter(prefix="/notifications", tags=["Notifications"])


async def _get_owned(db: SessionDep, user_id: int, notif_id: int) -> Notification:
    notif = await db.get(Notification, notif_id)
    if notif is None or notif.user_id != user_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Notification not found")
    return notif


@router.get("", response_model=list[NotificationRead])
async def list_notifications(
    current_user: CurrentUser,
    db: SessionDep,
    is_read: bool | None = None,
    category: NotificationCategory | None = None,
) -> list[NotificationRead]:
    filters = [Notification.user_id == current_user.id]
    if is_read is not None:
        filters.append(Notification.is_read == is_read)
    if category is not None:
        filters.append(Notification.category == category)
    rows = (
        await db.execute(
            select(Notification)
            .where(*filters)
            .order_by(Notification.created_at.desc())
        )
    ).scalars().all()
    return [NotificationRead.model_validate(r) for r in rows]


@router.get("/unread-count", response_model=UnreadCount)
async def unread_count(current_user: CurrentUser, db: SessionDep) -> UnreadCount:
    total = await db.scalar(
        select(func.count())
        .select_from(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
    )
    return UnreadCount(unread=int(total or 0))


@router.post("/scan", response_model=ScanResult)
async def scan_now(current_user: CurrentUser, db: SessionDep) -> ScanResult:
    """Manually trigger a notification scan for the current user."""
    created = await notification_service.scan_user(db, current_user.id)
    return ScanResult(created=created)


@router.patch("/{notif_id}/read", response_model=NotificationRead)
async def mark_read(
    notif_id: int, current_user: CurrentUser, db: SessionDep
) -> NotificationRead:
    notif = await _get_owned(db, current_user.id, notif_id)
    notif.is_read = True
    await db.flush()
    await db.refresh(notif)
    return NotificationRead.model_validate(notif)


@router.post("/read-all", response_model=UnreadCount)
async def mark_all_read(current_user: CurrentUser, db: SessionDep) -> UnreadCount:
    await db.execute(
        update(Notification)
        .where(
            Notification.user_id == current_user.id,
            Notification.is_read.is_(False),
        )
        .values(is_read=True)
    )
    return UnreadCount(unread=0)


@router.delete(
    "/{notif_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_notification(
    notif_id: int, current_user: CurrentUser, db: SessionDep
) -> Response:
    notif = await _get_owned(db, current_user.id, notif_id)
    await db.delete(notif)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
