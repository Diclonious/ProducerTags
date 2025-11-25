from typing import Tuple, List
from datetime import datetime, date, timedelta
from app.infrastructure.utils.time_utils import get_current_time
from sqlalchemy.orm import joinedload
from app.domain.entities.Order import Order
from app.domain.repositories.order_repository import IOrderRepository


class AnalyticsUseCase:
    """Use case for analytics operations"""

    def __init__(self, order_repository: IOrderRepository):
        self.order_repository = order_repository

    def get_order_statistics(self) -> dict:
        """Get order statistics (counts by status)"""


        all_orders = self.order_repository.get_all()

        stats = {
            "total": len(all_orders),
            "completed": len([o for o in all_orders if o.status == "Completed"]),
            "delivered": len([o for o in all_orders if o.status == "Delivered"]),
            "active": len([o for o in all_orders if o.status == "Active"]),
            "late": len([o for o in all_orders if o.status == "Late"]),
            "revision": len([o for o in all_orders if o.status == "Revision"]),
            "dispute": len([o for o in all_orders if o.status == "In dispute"]),
            "cancelled": len([o for o in all_orders if o.status == "Cancelled"]),
        }


        reviews = [o.review for o in all_orders if o.review is not None]
        stats["avg_rating"] = sum(reviews) / len(reviews) if reviews else 0.0


        if stats["total"] > 0:
            stats["completion_rate"] = (stats["completed"] / stats["total"]) * 100.0
            stats["cancellation_rate"] = (stats["cancelled"] / stats["total"]) * 100.0
        else:
            stats["completion_rate"] = 0.0
            stats["cancellation_rate"] = 0.0

        return stats

    def get_revenue_statistics(self, user_id: int | None = None) -> dict:
        """Get revenue statistics"""
        now = get_current_time()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        revenue = self.order_repository.get_revenue(user_id, "Completed", month_start)
        cancelled_revenue = self.order_repository.get_revenue(user_id, "Cancelled", month_start)



        active_orders = self.order_repository.get_by_status("Active")
        revision_orders = self.order_repository.get_by_status("Revision")
        delivered_orders = self.order_repository.get_by_status("Delivered")
        dispute_orders = self.order_repository.get_by_status("In dispute")
        late_orders = self.order_repository.get_by_status("Late")

        expected_earnings = 0.0
        all_active_orders = active_orders + revision_orders + delivered_orders + dispute_orders + late_orders
        for order in all_active_orders:
            if order.package and order.package.price:
                expected_earnings += float(order.package.price)

        return {
            "revenue": revenue,
            "cancelled_revenue": cancelled_revenue,
            "expected_earnings": expected_earnings
        }

    def calculate_chart_data(self, range_q: str = "monthly") -> Tuple[List[str], List[float], List[int], List[int], List[float]]:
        """Calculate chart data for analytics"""
        labels = []
        revenue_series = []
        completed_series = []
        cancelled_series = []
        cancelled_revenue_series = []

        if range_q == "yearly":
            base = date.today().replace(day=1)
            months = []
            for i in range(11, -1, -1):
                y = base.year if base.month - i > 0 else base.year - 1
                m = ((base.month - i - 1) % 12) + 1
                months.append((y, m))

            for y, m in months:
                start = datetime(year=y, month=m, day=1)
                end = datetime(year=y+1, month=1, day=1) if m == 12 else datetime(year=y, month=m+1, day=1)

                completed = self.order_repository.get_completed_orders(start_date=start)
                completed_filtered = [o for o in completed if o.completed_date and o.completed_date < end]


                all_orders = self.order_repository.get_all()
                cancelled_filtered = [
                    o for o in all_orders
                    if o.status == "Cancelled" and o.cancelled_date and start <= o.cancelled_date < end
                ]

                revenue_m = sum(float(o.package.price) if o.package and o.package.price else 0.0 for o in completed_filtered)
                cancelled_revenue_m = sum(float(o.package.price) if o.package and o.package.price else 0.0 for o in cancelled_filtered)

                labels.append(start.strftime('%b %Y'))
                revenue_series.append(round(revenue_m, 2))
                completed_series.append(len(completed_filtered))
                cancelled_series.append(len(cancelled_filtered))
                cancelled_revenue_series.append(round(cancelled_revenue_m, 2))
        else:
            start = date.today() - timedelta(days=29)
            for i in range(30):
                d = start + timedelta(days=i)
                d0 = datetime(d.year, d.month, d.day)
                d1 = d0 + timedelta(days=1)

                completed = self.order_repository.get_completed_orders(start_date=d0)
                completed_filtered = [o for o in completed if o.completed_date and o.completed_date < d1]

                all_orders = self.order_repository.get_all()
                cancelled_filtered = [
                    o for o in all_orders
                    if o.status == "Cancelled" and o.cancelled_date and d0 <= o.cancelled_date < d1
                ]

                revenue_d = sum(float(o.package.price) if o.package and o.package.price else 0.0 for o in completed_filtered)
                cancelled_revenue_d = sum(float(o.package.price) if o.package and o.package.price else 0.0 for o in cancelled_filtered)

                labels.append(d.strftime('%d %b'))
                revenue_series.append(round(revenue_d, 2))
                completed_series.append(len(completed_filtered))
                cancelled_series.append(len(cancelled_filtered))
                cancelled_revenue_series.append(round(cancelled_revenue_d, 2))

        return labels, revenue_series, completed_series, cancelled_series, cancelled_revenue_series

    def get_recent_reviews(self, limit: int = 12) -> List[Order]:
        """Get recent reviews"""
        all_orders = self.order_repository.get_all()
        reviews = [o for o in all_orders if o.review is not None]
        reviews.sort(key=lambda x: x.id, reverse=True)
        return reviews[:limit]

