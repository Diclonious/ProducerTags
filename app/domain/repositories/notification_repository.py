from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.Notification import Notification


class INotificationRepository(ABC):
    """Abstract repository interface for Notification entity"""
    
    @abstractmethod
    def get_by_user_id(self, user_id: int, limit: int = 50) -> List[Notification]:
        """Get notifications for a user"""
        pass
    
    @abstractmethod
    def get_unread_count(self, user_id: int) -> int:
        """Get count of unread notifications"""
        pass
    
    @abstractmethod
    def create(self, notification: Notification) -> Notification:
        """Create a new notification"""
        pass
    
    @abstractmethod
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        """Mark a notification as read"""
        pass
    
    @abstractmethod
    def mark_all_read(self, user_id: int) -> int:
        """Mark all notifications as read for a user"""
        pass

