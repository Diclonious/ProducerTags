from typing import List
from datetime import datetime
from app.infrastructure.utils.time_utils import get_current_time
from app.domain.entities.Message import Message
from app.domain.repositories.message_repository import IMessageRepository
from app.domain.repositories.order_repository import IOrderRepository
from app.application.dto.message import MessageCreate


class MessageUseCase:
    """Use case for message operations"""

    def __init__(
        self,
        message_repository: IMessageRepository,
        order_repository: IOrderRepository
    ):
        self.message_repository = message_repository
        self.order_repository = order_repository

    def get_messages_for_order(self, order_id: int, user_id: int, is_admin: bool) -> List[Message]:
        """Get all messages for an order"""

        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if not is_admin and order.user_id != user_id:
            raise ValueError("Forbidden")

        messages = self.message_repository.get_by_order_id(order_id)


        for msg in messages:
            if msg.sender_id != user_id and not msg.is_read:
                self.message_repository.mark_as_read(msg.id)

        return messages

    def send_message(self, order_id: int, sender_id: int, message_data: MessageCreate, is_admin: bool) -> Message:
        """Send a message in an order"""

        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if not is_admin and order.user_id != sender_id:
            raise ValueError("Forbidden")

        message = Message(
            order_id=order_id,
            sender_id=sender_id,
            message_text=message_data.message_text,
            created_at=get_current_time(),
            is_read=False
        )

        return self.message_repository.create(message)

    def get_unread_count(self, user_id: int, is_admin: bool) -> int:
        """Get count of unread messages"""
        return self.message_repository.get_unread_count(user_id, is_admin)

    def mark_all_read(self, user_id: int, is_admin: bool) -> int:
        """Mark all messages as read"""
        return self.message_repository.mark_all_read_for_user(user_id, is_admin)

