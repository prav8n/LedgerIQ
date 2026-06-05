"""Pydantic v2 schemas for notifications."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NotificationCategory, NotificationType


class NotificationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    message: str
    type: NotificationType
    category: NotificationCategory
    is_read: bool
    action_url: str | None
    related_entity_type: str | None
    related_entity_id: int | None
    created_at: datetime


class UnreadCount(BaseModel):
    unread: int


class ScanResult(BaseModel):
    created: int
