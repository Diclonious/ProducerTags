from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.Message import Message


class IMessageRepository(ABC):
    """Abstract repository interface for Message entity"""

    @abstractmethod
    def get_by_order_id(self, order_id: int) -> List[Message]:
        """Get all messages for an order"""
        pass

    @abstractmethod
    def get_unread_count(self, user_id: int, is_admin: bool = False) -> int:
        """Get count of unread messages for a user"""
        pass

    @abstractmethod
    def create(self, message: Message) -> Message:
        """Create a new message"""
        pass

    @abstractmethod
    def mark_as_read(self, message_id: int) -> bool:
        """Mark a message as read"""
        pass

    @abstractmethod
    def mark_all_read_for_user(self, user_id: int, is_admin: bool = False) -> int:
        """Mark all messages as read for a user"""
        pass

