from typing import Optional, List
from datetime import datetime
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import update, func
from app.domain.entities.Order import Order
from app.domain.repositories.order_repository import IOrderRepository
from app.infrastructure.utils.time_utils import get_current_time


class OrderRepository(IOrderRepository):
    """SQLAlchemy implementation of Order repository"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_by_id(self, order_id: int) -> Optional[Order]:
        return self.db.query(Order).options(
            joinedload(Order.package),
            joinedload(Order.user)
        ).filter(Order.id == order_id).first()
    
    def get_by_user_id(self, user_id: int) -> List[Order]:
        return self.db.query(Order).filter(Order.user_id == user_id).all()
    
    def get_by_status(self, status: str) -> List[Order]:
        return self.db.query(Order).options(
            joinedload(Order.package),
            joinedload(Order.user)
        ).filter(Order.status == status).all()
    
    def get_by_user_and_status(self, user_id: int, status: str) -> List[Order]:
        return self.db.query(Order).filter(
            Order.user_id == user_id,
            Order.status == status
        ).all()
    
    def get_by_user_and_id(self, user_id: int, order_id: int) -> Optional[Order]:
        return self.db.query(Order).filter(
            Order.id == order_id,
            Order.user_id == user_id
        ).first()
    
    def get_all(self) -> List[Order]:
        return self.db.query(Order).options(
            joinedload(Order.package),
            joinedload(Order.user)
        ).all()
    
    def get_with_relationships(self, user_id: Optional[int] = None, status: Optional[str] = None, admin_view: bool = False) -> List[Order]:
        query = self.db.query(Order).options(
            joinedload(Order.tags),
            joinedload(Order.package),
            joinedload(Order.user)
        )
        
        if not admin_view and user_id:
            query = query.filter(Order.user_id == user_id)
        
        if status:
            query = query.filter(Order.status == status)
        
        return query.all()
    
    def create(self, order: Order) -> Order:
        self.db.add(order)
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def update(self, order: Order) -> Order:
        self.db.commit()
        self.db.refresh(order)
        return order
    
    def update_late_orders(self) -> int:
        """Update orders that are past due date to Late status"""
        # Use synchronized current time instead of database time
        current_time = get_current_time()
        
        # First, revert orders marked as Late back to Active if they're not actually late
        # (this fixes orders that were incorrectly marked as Late using real database time)
        revert_result = self.db.execute(
            update(Order)
            .where(Order.status == "Late")
            .where(Order.due_date >= current_time)
            .values(status="Active")
        )
        revert_count = revert_result.rowcount
        
        # Then, mark orders as Late if they're past due
        result = self.db.execute(
            update(Order)
            .where(Order.status.in_(["Active", "Revision"]))
            .where(Order.due_date < current_time)
            .values(status="Late")
        )
        late_count = result.rowcount
        
        self.db.commit()
        
        # Return total number of orders updated
        return revert_count + late_count
    
    def get_completed_orders(self, user_id: Optional[int] = None, start_date: Optional[datetime] = None) -> List[Order]:
        query = self.db.query(Order).options(
            joinedload(Order.package),
            joinedload(Order.user)
        ).filter(Order.status == "Completed")
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        if start_date:
            query = query.filter(Order.completed_date >= start_date)
        
        return query.all()
    
    def get_revenue(self, user_id: Optional[int] = None, status: str = "Completed", start_date: Optional[datetime] = None) -> float:
        from app.domain.entities.Package import Package
        
        query = self.db.query(Order).options(joinedload(Order.package)).filter(
            Order.status == status
        )
        
        if user_id:
            query = query.filter(Order.user_id == user_id)
        
        if start_date:
            query = query.filter(Order.completed_date >= start_date)
        
        orders = query.all()
        return sum(float(o.package.price) if o.package and o.package.price is not None else 0.0 for o in orders)

