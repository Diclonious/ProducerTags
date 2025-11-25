from typing import List
from datetime import datetime
from app.infrastructure.utils.time_utils import get_current_time
from app.domain.entities.Notification import Notification
from app.domain.repositories.notification_repository import INotificationRepository


class NotificationUseCase:
    """Use case for notification operations"""

    def __init__(self, notification_repository: INotificationRepository):
        self.notification_repository = notification_repository

    def get_notifications(self, user_id: int, limit: int = 50) -> List[Notification]:
        """Get notifications for a user"""
        return self.notification_repository.get_by_user_id(user_id, limit)

    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        return self.notification_repository.get_unread_count(user_id)

    def create_notification(
        self,
        user_id: int,
        order_id: int | None,
        notification_type: str,
        title: str,
        message: str
    ) -> Notification:
        """Create a new notification"""
        notification = Notification(
            user_id=user_id,
            order_id=order_id,
            notification_type=notification_type,
            title=title,
            message=message,
            is_read=False,
            created_at=get_current_time()
        )
        return self.notification_repository.create(notification)

    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        return self.notification_repository.mark_as_read(notification_id, user_id)

    def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read"""
        return self.notification_repository.mark_all_read(user_id)

