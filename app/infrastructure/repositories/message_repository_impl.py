from typing import List
from sqlalchemy.orm import Session, joinedload
from app.domain.entities.Message import Message
from app.domain.entities.Order import Order
from app.domain.repositories.message_repository import IMessageRepository


class MessageRepository(IMessageRepository):
    """SQLAlchemy implementation of Message repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_order_id(self, order_id: int) -> List[Message]:
        return (
            self.db.query(Message)
            .options(joinedload(Message.sender))
            .filter(Message.order_id == order_id)
            .order_by(Message.created_at.asc())
            .all()
        )
    
    def get_unread_count(self, user_id: int, is_admin: bool = False) -> int:
        query = self.db.query(Message).join(Order).filter(
            Message.is_read == False,
            Message.sender_id != user_id
        )
        
        if not is_admin:
            query = query.filter(Order.user_id == user_id)
        
        return query.count()
    
    def create(self, message: Message) -> Message:
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message
    
    def mark_as_read(self, message_id: int) -> bool:
        message = self.db.query(Message).filter(Message.id == message_id).first()
        if message:
            message.is_read = True
            self.db.commit()
            return True
        return False
    
    def mark_all_read_for_user(self, user_id: int, is_admin: bool = False) -> int:
        query = self.db.query(Message).join(Order).filter(
            Message.is_read == False,
            Message.sender_id != user_id
        )
        
        if not is_admin:
            query = query.filter(Order.user_id == user_id)
        
        result = query.update({"is_read": True})
        self.db.commit()
        return result

