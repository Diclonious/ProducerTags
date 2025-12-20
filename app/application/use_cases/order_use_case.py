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
      
        package = self.package_repository.get_by_id(order_data.package_id)
        if not package:
            raise ValueError("Package not found")



        due_date = get_current_time() + timedelta(days=package.delivery_days)


        order = Order(
            user_id=user_id,
            package_id=package.id,
            details=order_data.details,
            due_date=due_date,
            status="Active"
        )
        order = self.order_repository.create(order)


        for tag_value, mood_value in zip(order_data.tags, order_data.moods):
            tag = Tag(order_id=order.id, name=tag_value, mood=mood_value)



        self._notify_admins(order, "order_placed", "New Order Placed",
                          f"Order #{order.id} was placed")

        return order

    def deliver_order(self, order_id: int, admin_id: int, delivery_data: OrderDeliver) -> Order:
        
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status not in ["Active", "Revision", "Late"]:
            raise ValueError("Cannot deliver order in this state")



        delivery_number = 1


        delivery = Delivery(
            order_id=order_id,
            delivery_number=delivery_number,
            response_text=delivery_data.response_text,
            delivered_at=get_current_time(),
            user_id=admin_id
        )



        order.status = "Delivered"
        order.response = delivery_data.response_text
        order = self.order_repository.update(order)


        event = OrderEvent(
            order_id=order.id,
            event_type="delivered",
            user_id=admin_id,
            event_message=delivery_data.response_text,
            created_at=get_current_time()
        )



        self._notify_user(order.user_id, order.id, "delivered",
                         "Order Delivered", f"Your order #{order.id} has been delivered!")

        return order

    def complete_order(self, order_id: int, user_id: int) -> Order:
        
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


        event = OrderEvent(
            order_id=order.id,
            event_type="completed",
            user_id=user_id,
            event_message="Order marked as completed",
            created_at=get_current_time()
        )


        self._notify_admins(order, "order_completed", "Order Completed",
                          f"Order #{order.id} was marked as complete")

        return order

    def submit_review(self, order_id: int, user_id: int, review_data: OrderReview) -> Order:
        
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


        self._notify_admins(order, "review_left", f"{review_data.review}-Star Review",
                          f"Review left on order #{order.id}")

        return order

    def get_orders_for_user(self, user_id: int) -> List[Order]:
     
        return self.order_repository.get_with_relationships(user_id=user_id)

    def get_all_orders(self) -> List[Order]:
        
        return self.order_repository.get_with_relationships(admin_view=True)

    def _notify_admins(self, order: Order, notification_type: str, title: str, message: str):
       
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


        if self.user_repository.get_by_id(user_id).is_admin:
            self._notify_user(order.user_id, order.id, "cancellation_requested",
                            "Cancellation Requested", f"Admin requested cancellation for order #{order.id}")
        else:
            self._notify_admins(order, "cancellation_requested", "Cancellation Requested",
                              f"User requested cancellation for order #{order.id}")

        return order

    def request_extension(self, order_id: int, user_id: int, resolution_data: ResolutionRequest) -> Order:
        
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
        is_admin = self.user_repository.get_by_id(user_id).is_admin
        order.requested_by_admin = "true" if is_admin else "false"

        # Only extend the due date immediately if user is requesting (not admin)
        # If admin is requesting, wait for user approval before extending
        if not is_admin and order.due_date:
            order.due_date = order.due_date + timedelta(days=resolution_data.extension_days)

        order = self.order_repository.update(order)


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


        if self.user_repository.get_by_id(user_id).is_admin:
            self._notify_user(order.user_id, order.id, "extension_requested",
                            "Extension Requested", f"Admin requested {resolution_data.extension_days}-day extension for order #{order.id}")
        else:
            self._notify_admins(order, "extension_requested", "Extension Requested",
                              f"User requested {resolution_data.extension_days}-day extension for order #{order.id}")

        return order

    def open_dispute(self, order_id: int, user_id: int, resolution_data: ResolutionRequest) -> Order:
       
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


        self._notify_admins(order, "dispute_opened", "Dispute Opened",
                          f"User opened a dispute for order #{order.id}")

        return order

    def approve_resolution_request(self, order_id: int, admin_id: int) -> Order:
        
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status != "In dispute":
            raise ValueError("Order is not in dispute")


        if order.request_type == "cancellation":
            order.status = "Cancelled"
            order.cancelled_date = get_current_time()
        elif order.request_type == "extend_delivery":
            # If admin requested extension and user is approving, extend the due_date now
            if order.requested_by_admin == "true" and order.extension_days and order.due_date:
                order.due_date = order.due_date + timedelta(days=order.extension_days)
            order.status = "Active"
        elif order.request_type == "revision":
            order.status = "Revision"

            order.due_date = get_current_time() + timedelta(hours=24)
        else:

            order.status = "Active"


        order.request_type = None
        order.request_message = None
        order.cancellation_reason = None
        order.cancellation_message = None
        order.extension_days = None
        order.extension_reason = None
        order.requested_by_admin = None

        order = self.order_repository.update(order)


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


        self._notify_user(order.user_id, order.id, "request_approved",
                         "Request Approved", f"Your request for order #{order.id} has been approved")

        return order

    def reject_resolution_request(self, order_id: int, admin_id: int, rejection_message: str = "") -> Order:
        
        order = self.order_repository.get_by_id(order_id)
        if not order:
            raise ValueError("Order not found")

        if order.status != "In dispute":
            raise ValueError("Order is not in dispute")


        if order.request_type == "cancellation":

            if order.requested_by_admin == "true":
                order.status = "Active"
            else:
                order.status = "Delivered"
        elif order.request_type == "extend_delivery":
            # If admin requested extension and user is rejecting, don't change due_date (it wasn't extended yet)
            # If user requested extension and admin is rejecting, revert the due_date
            if order.requested_by_admin != "true" and order.extension_days and order.due_date:
                order.due_date = order.due_date - timedelta(days=order.extension_days)
            order.status = "Active"
        elif order.request_type == "revision":
            order.status = "Delivered"
        else:

            order.status = "Active"


        order.request_type = None
        order.request_message = None
        order.cancellation_reason = None
        order.cancellation_message = None
        order.extension_days = None
        order.extension_reason = None
        order.requested_by_admin = None

        order = self.order_repository.update(order)


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


        self._notify_user(order.user_id, order.id, "request_rejected",
                         "Request Rejected", f"Your request for order #{order.id} has been rejected" + (f": {rejection_message}" if rejection_message else ""))

        return order

