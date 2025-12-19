from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.Message import Message


class IMessageRepository(ABC):
    

    @abstractmethod
    def get_by_order_id(self, order_id: int) -> List[Message]:
       
        pass

    @abstractmethod
    def get_unread_count(self, user_id: int, is_admin: bool = False) -> int:
        
        pass

    @abstractmethod
    def create(self, message: Message) -> Message:
        
        pass

    @abstractmethod
    def mark_as_read(self, message_id: int) -> bool:
        
        pass

    @abstractmethod
    def mark_all_read_for_user(self, user_id: int, is_admin: bool = False) -> int:
        
        pass

