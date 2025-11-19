from typing import List, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from app.infrastructure.utils.time_utils import get_current_time
from app.domain.entities.Order import Order
from app.domain.entities.Tag import Tag
from app.domain.entities.Delivery import Delivery
from app.domain.entities.DeliveryFile import DeliveryFile
from app.domain.entities.OrderEvent import OrderEvent
from app.domain.repositories.order_repository import IOrderRepository
from app.domain.repositories.package_repository import IPackageRepository
from app.domain.repositories.user_repository import IUserRepository
from app.domain.repositories.notification_repository import INotificationRepository
from app.application.dto.order import OrderCreate, OrderDeliver, OrderReview, ResolutionRequest


class OrderUseCase:
    """Use case for order operations"""
    
    def __init__(
        self,
        order_repository: IOrderRepository,
        package_repository: IPackageRepository,
        user_repository: IUserRepository,
        notification_repository: INotificationRepository,
        db: Optional[Session] = None
    ):
        self.order_repository = order_repository
        self.package_repository = package_repository
        self.user_repository = user_repository
        self.notification_repository = notification_repository
        self.db = db
    
    def create_order(self, user_id: int, order_data: OrderCreate) -> Order:
        """Create a new order"""
        package = self.package_repository.get_by_id(order_data.package_id)
        if not package:
            raise ValueError("Package not found")
        
        # Calculate due date based on package delivery_days
        # If delivery_days is 1, it's 24 hours; if 2, it's 48 hours, etc.
        due_date = get_current_time() + timedelta(days=package.delivery_days)
        
        # Create order
        order = Order(
            user_id=user_id,
            package_id=package.id,
            details=order_data.details,
            due_date=due_date,
            status="Active"
        )
        order = self.order_repository.create(order)
        
        # Create tags
        for tag_value, mood_value in zip(order_data.tags, order_data.moods):
            tag = Tag(order_id=order.id, name=tag_value, mood=mood_value)
            # Note: Tag repository would be needed for proper implementation
        
        # Notify admins
        self._notify_admins(order, "order_placed", "New Order Placed", 
                          f"Order #{order.id} was placed")
        
        return order
    
    def deliver_order(self, order_id: int, admin_id: int, delivery_data: OrderDeliver) -> Order:
        """Deliver an order"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status not in ["Active", "Revision", "Late"]:
            raise ValueError("Cannot deliver order in this state")
        
        # Get delivery number
        # Note: Would need Delivery repository for proper count
        delivery_number = 1  # Simplified
        
        # Create delivery
        delivery = Delivery(
            order_id=order_id,
            delivery_number=delivery_number,
            response_text=delivery_data.response_text,
            delivered_at=get_current_time(),
            user_id=admin_id
        )
        # Note: Would need Delivery repository
        
        # Update order status
        order.status = "Delivered"
        order.response = delivery_data.response_text
        order = self.order_repository.update(order)
        
        # Create event
        event = OrderEvent(
            order_id=order.id,
            event_type="delivered",
            user_id=admin_id,
            event_message=delivery_data.response_text,
            created_at=get_current_time()
        )
        # Note: Would need OrderEvent repository
        
        # Notify customer
        self._notify_user(order.user_id, order.id, "delivered", 
                         "Order Delivered", f"Your order #{order.id} has been delivered!")
        
        return order
    
    def complete_order(self, order_id: int, user_id: int) -> Order:
        """Mark an order as complete"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.user_id != user_id:
            raise ValueError("Unauthorized")
        
        if order.status != "Delivered":
            raise ValueError("Cannot complete order in this state")
        
        order.status = "Completed"
        order.completed_date = get_current_time()
        order = self.order_repository.update(order)
        
        # Create event
        event = OrderEvent(
            order_id=order.id,
            event_type="completed",
            user_id=user_id,
            event_message="Order marked as completed",
            created_at=get_current_time()
        )
        
        # Notify admin
        self._notify_admins(order, "order_completed", "Order Completed",
                          f"Order #{order.id} was marked as complete")
        
        return order
    
    def submit_review(self, order_id: int, user_id: int, review_data: OrderReview) -> Order:
        """Submit a review for an order"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.user_id != user_id:
            raise ValueError("Unauthorized")
        
        if order.status != "Completed":
            raise ValueError("Can only review completed orders")
        
        order.review = review_data.review
        order.review_text = review_data.review_text
        order = self.order_repository.update(order)
        
        # Notify admin
        self._notify_admins(order, "review_left", f"{review_data.review}-Star Review",
                          f"Review left on order #{order.id}")
        
        return order
    
    def get_orders_for_user(self, user_id: int) -> List[Order]:
        """Get all orders for a user"""
        return self.order_repository.get_with_relationships(user_id=user_id)
    
    def get_all_orders(self) -> List[Order]:
        """Get all orders (admin view)"""
        return self.order_repository.get_with_relationships(admin_view=True)
    
    def _notify_admins(self, order: Order, notification_type: str, title: str, message: str):
        """Helper to notify all admins"""
        from app.domain.entities.Notification import Notification
        admins = self.user_repository.get_admins()
        for admin in admins:
            notification = Notification(
                user_id=admin.id,
                order_id=order.id,
                notification_type=notification_type,
                title=title,
                message=message,
                is_read=False,
                created_at=get_current_time()
            )
            self.notification_repository.create(notification)
    
    def _notify_user(self, user_id: int, order_id: int, notification_type: str, title: str, message: str):
        """Helper to notify a user"""
        from app.domain.entities.Notification import Notification
        notification = Notification(
            user_id=user_id,
            order_id=order_id,
            notification_type=notification_type,
            title=title,
            message=message,
            is_read=False,
            created_at=get_current_time()
        )
        self.notification_repository.create(notification)
    
    def request_cancellation(self, order_id: int, user_id: int, resolution_data: ResolutionRequest) -> Order:
        """Request order cancellation"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.user_id != user_id and not self.user_repository.get_by_id(user_id).is_admin:
            raise ValueError("Unauthorized")
        
        if order.status in ["Completed", "Cancelled"]:
            raise ValueError("Cannot cancel order in this state")
        
        order.status = "In dispute"
        order.request_type = "cancellation"
        order.cancellation_reason = resolution_data.cancellation_reason
        order.cancellation_message = resolution_data.cancellation_message
        order.requested_by_admin = "true" if self.user_repository.get_by_id(user_id).is_admin else "false"
        order = self.order_repository.update(order)
        
        # Create event
        if self.db:
            event = OrderEvent(
                order_id=order.id,
                event_type="cancellation_requested",
                user_id=user_id,
                cancellation_reason=resolution_data.cancellation_reason,
                cancellation_message=resolution_data.cancellation_message,
                created_at=get_current_time()
            )
            self.db.add(event)
            self.db.commit()
        
        # Notify
        if self.user_repository.get_by_id(user_id).is_admin:
            self._notify_user(order.user_id, order.id, "cancellation_requested",
                            "Cancellation Requested", f"Admin requested cancellation for order #{order.id}")
        else:
            self._notify_admins(order, "cancellation_requested", "Cancellation Requested",
                              f"User requested cancellation for order #{order.id}")
        
        return order
    
    def request_extension(self, order_id: int, user_id: int, resolution_data: ResolutionRequest) -> Order:
        """Request delivery extension"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.user_id != user_id and not self.user_repository.get_by_id(user_id).is_admin:
            raise ValueError("Unauthorized")
        
        if order.status in ["Completed", "Cancelled", "Delivered"]:
            raise ValueError("Cannot extend delivery in this state")
        
        order.status = "In dispute"
        order.request_type = "extend_delivery"
        order.extension_days = resolution_data.extension_days
        order.extension_reason = resolution_data.extension_reason
        order.requested_by_admin = "true" if self.user_repository.get_by_id(user_id).is_admin else "false"
        
        # Extend due date
        if order.due_date:
            order.due_date = order.due_date + timedelta(days=resolution_data.extension_days)
        
        order = self.order_repository.update(order)
        
        # Create event
        if self.db:
            event = OrderEvent(
                order_id=order.id,
                event_type="extension_requested",
                user_id=user_id,
                extension_days=resolution_data.extension_days,
                extension_reason=resolution_data.extension_reason,
                created_at=get_current_time()
            )
            self.db.add(event)
            self.db.commit()
        
        # Notify
        if self.user_repository.get_by_id(user_id).is_admin:
            self._notify_user(order.user_id, order.id, "extension_requested",
                            "Extension Requested", f"Admin requested {resolution_data.extension_days}-day extension for order #{order.id}")
        else:
            self._notify_admins(order, "extension_requested", "Extension Requested",
                              f"User requested {resolution_data.extension_days}-day extension for order #{order.id}")
        
        return order
    
    def open_dispute(self, order_id: int, user_id: int, resolution_data: ResolutionRequest) -> Order:
        """Open a dispute for an order"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.user_id != user_id:
            raise ValueError("Unauthorized")
        
        if order.status in ["Completed", "Cancelled"]:
            raise ValueError("Cannot open dispute in this state")
        
        order.status = "In dispute"
        order.request_type = "dispute"
        order.request_message = resolution_data.dispute_message or resolution_data.message
        order.requested_by_admin = "false"
        order = self.order_repository.update(order)
        
        # Create event
        if self.db:
            event = OrderEvent(
                order_id=order.id,
                event_type="dispute_opened",
                user_id=user_id,
                event_message=resolution_data.dispute_message or resolution_data.message,
                created_at=get_current_time()
            )
            self.db.add(event)
            self.db.commit()
        
        # Notify admins
        self._notify_admins(order, "dispute_opened", "Dispute Opened",
                          f"User opened a dispute for order #{order.id}")
        
        return order
    
    def approve_resolution_request(self, order_id: int, admin_id: int) -> Order:
        """Approve a resolution request (admin only)"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status != "In dispute":
            raise ValueError("Order is not in dispute")
        
        # Handle different request types
        if order.request_type == "cancellation":
            order.status = "Cancelled"
            order.cancelled_date = get_current_time()
        elif order.request_type == "extend_delivery":
            # Extension already applied, just clear dispute
            order.status = "Active"
        elif order.request_type == "revision":
            order.status = "Revision"
            # Reset timer - 24 hours from now
            order.due_date = get_current_time() + timedelta(hours=24)
        else:
            # Generic dispute - resolve it
            order.status = "Active"
        
        # Clear request fields
        order.request_type = None
        order.request_message = None
        order.cancellation_reason = None
        order.cancellation_message = None
        order.extension_days = None
        order.extension_reason = None
        order.requested_by_admin = None
        
        order = self.order_repository.update(order)
        
        # Create event
        if self.db:
            event = OrderEvent(
                order_id=order.id,
                event_type="request_approved",
                user_id=admin_id,
                event_message="Request approved",
                created_at=get_current_time()
            )
            self.db.add(event)
            self.db.commit()
        
        # Notify user
        self._notify_user(order.user_id, order.id, "request_approved",
                         "Request Approved", f"Your request for order #{order.id} has been approved")
        
        return order
    
    def reject_resolution_request(self, order_id: int, admin_id: int, rejection_message: str = "") -> Order:
        """Reject a resolution request (admin only)"""
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")
        
        if order.status != "In dispute":
            raise ValueError("Order is not in dispute")
        
        # Revert to previous status based on request type
        if order.request_type == "cancellation":
            # Revert to status before cancellation request
            if order.requested_by_admin == "true":
                order.status = "Active"  # Admin requested cancellation, revert to Active
            else:
                order.status = "Delivered"  # User requested cancellation, revert to Delivered
        elif order.request_type == "extend_delivery":
            # Revert extension and status
            if order.extension_days and order.due_date:
                order.due_date = order.due_date - timedelta(days=order.extension_days)
            order.status = "Active"
        elif order.request_type == "revision":
            order.status = "Delivered"
        else:
            # Generic dispute - revert to Active
            order.status = "Active"
        
        # Clear request fields
        order.request_type = None
        order.request_message = None
        order.cancellation_reason = None
        order.cancellation_message = None
        order.extension_days = None
        order.extension_reason = None
        order.requested_by_admin = None
        
        order = self.order_repository.update(order)
        
        # Create event
        if self.db:
            event = OrderEvent(
                order_id=order.id,
                event_type="request_rejected",
                user_id=admin_id,
                event_message=rejection_message or "Request rejected",
                created_at=get_current_time()
            )
            self.db.add(event)
            self.db.commit()
        
        # Notify user
        self._notify_user(order.user_id, order.id, "request_rejected",
                         "Request Rejected", f"Your request for order #{order.id} has been rejected" + (f": {rejection_message}" if rejection_message else ""))
        
        return order

