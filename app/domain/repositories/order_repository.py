from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from app.domain.entities.Order import Order


class IOrderRepository(ABC):
    

    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        
        pass

    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Order]:
        
        pass

    @abstractmethod
    def get_by_status(self, status: str) -> List[Order]:
        
        pass

    @abstractmethod
    def get_by_user_and_status(self, user_id: int, status: str) -> List[Order]:
        
        pass

    @abstractmethod
    def get_by_user_and_id(self, user_id: int, order_id: int) -> Optional[Order]:
        
        pass

    @abstractmethod
    def get_all(self) -> List[Order]:
        
        pass

    @abstractmethod
    def get_with_relationships(self, user_id: Optional[int] = None, status: Optional[str] = None, admin_view: bool = False) -> List[Order]:
        
        pass

    @abstractmethod
    def create(self, order: Order) -> Order:
        
        pass

    @abstractmethod
    def update(self, order: Order) -> Order:
        
        pass

    @abstractmethod
    def update_late_orders(self) -> int:
        
        pass

    @abstractmethod
    def get_completed_orders(self, user_id: Optional[int] = None, start_date: Optional[datetime] = None) -> List[Order]:
        
        pass

    @abstractmethod
    def get_revenue(self, user_id: Optional[int] = None, status: str = "Completed", start_date: Optional[datetime] = None) -> float:
       
        pass

