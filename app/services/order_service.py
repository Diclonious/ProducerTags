from app.domain.order import Order

class OrderService:
    def create_order(self, name: str, email: str, file_path: str, details: str = "") -> Order:
        order = Order(name=name, email=email, file_path=file_path, details=details)
        orders_db.append(order)
        return order