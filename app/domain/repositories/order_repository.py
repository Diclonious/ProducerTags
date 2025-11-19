from abc import ABC, abstractmethod
from typing import Optional, List
from datetime import datetime
from app.domain.entities.Order import Order


class IOrderRepository(ABC):
    """Abstract repository interface for Order entity"""
    
    @abstractmethod
    def get_by_id(self, order_id: int) -> Optional[Order]:
        """Get order by ID"""
        pass
    
    @abstractmethod
    def get_by_user_id(self, user_id: int) -> List[Order]:
        """Get all orders for a user"""
        pass
    
    @abstractmethod
    def get_by_status(self, status: str) -> List[Order]:
        """Get all orders with a specific status"""
        pass
    
    @abstractmethod
    def get_by_user_and_status(self, user_id: int, status: str) -> List[Order]:
        """Get orders for a user with specific status"""
        pass
    
    @abstractmethod
    def get_by_user_and_id(self, user_id: int, order_id: int) -> Optional[Order]:
        """Get order by ID for a specific user"""
        pass
    
    @abstractmethod
    def get_all(self) -> List[Order]:
        """Get all orders"""
        pass
    
    @abstractmethod
    def get_with_relationships(self, user_id: Optional[int] = None, status: Optional[str] = None, admin_view: bool = False) -> List[Order]:
        """Get orders with relationships loaded"""
        pass
    
    @abstractmethod
    def create(self, order: Order) -> Order:
        """Create a new order"""
        pass
    
    @abstractmethod
    def update(self, order: Order) -> Order:
        """Update an existing order"""
        pass
    
    @abstractmethod
    def update_late_orders(self) -> int:
        """Update orders that are past due date to Late status"""
        pass
    
    @abstractmethod
    def get_completed_orders(self, user_id: Optional[int] = None, start_date: Optional[datetime] = None) -> List[Order]:
        """Get completed orders"""
        pass
    
    @abstractmethod
    def get_revenue(self, user_id: Optional[int] = None, status: str = "Completed", start_date: Optional[datetime] = None) -> float:
        """Calculate revenue from orders"""
        pass

