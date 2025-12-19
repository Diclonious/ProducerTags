from abc import ABC, abstractmethod
from typing import List, Optional
from app.domain.entities.Notification import Notification


class INotificationRepository(ABC):
    

    @abstractmethod
    def get_by_user_id(self, user_id: int, limit: int = 50) -> List[Notification]:
       
        pass

    @abstractmethod
    def get_unread_count(self, user_id: int) -> int:
        
        pass

    @abstractmethod
    def create(self, notification: Notification) -> Notification:
       
        pass

    @abstractmethod
    def mark_as_read(self, notification_id: int, user_id: int) -> bool:
        
        pass

    @abstractmethod
    def mark_all_read(self, user_id: int) -> int:
        
        pass

