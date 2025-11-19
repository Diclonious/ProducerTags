# Clean Architecture Refactoring Guide

## ✅ Completed Structure

### Domain Layer (`app/domain/`)
- ✅ Entities: All domain models (User, Order, Package, etc.)
- ✅ Repository Interfaces: Abstract base classes for data access
- ✅ Domain Services: (Can be added for complex domain logic)

### Application Layer (`app/application/`)
- ✅ DTOs: Pydantic schemas for all entities
- ✅ Use Cases: Business logic (AuthUseCase, OrderUseCase)
- ✅ Services: ServiceContainer for dependency injection

### Infrastructure Layer (`app/infrastructure/`)
- ✅ Repositories: SQLAlchemy implementations
- ✅ Database: Database setup and configuration
- ✅ Storage: File storage service

### Presentation Layer (`app/presentation/`)
- ✅ Dependencies: FastAPI dependencies (auth, service container)
- ✅ Routes: (To be created - see below)

## 📋 Remaining Work

### 1. Complete Use Cases
- Package management use cases
- Message use cases
- Notification use cases
- Analytics use cases

### 2. Create Route Handlers
Organize routes by feature:
- `auth_routes.py` - Login, signup, logout, profile
- `order_routes.py` - Order CRUD, delivery, completion
- `package_routes.py` - Package management (admin)
- `message_routes.py` - Messaging system
- `notification_routes.py` - Notifications
- `analytics_routes.py` - Analytics dashboard
- `review_routes.py` - Review system
- `resolution_routes.py` - Dispute resolution

### 3. Refactor main.py
- Keep only app initialization
- Include all route routers
- Keep startup event (but move logic to infrastructure)

## 🔄 Migration Pattern

### Old Pattern:
```python
@app.post("/order/submit")
async def submit_order(...):
    db = SessionLocal()
    try:
        # Direct database queries
        package = db.query(Package).filter(...).first()
        # Business logic mixed with route
        order = Order(...)
        db.add(order)
        db.commit()
    finally:
        db.close()
```

### New Pattern:
```python
@router.post("/order/submit")
async def submit_order(
    request: Request,
    order_data: OrderCreate,
    current_user: User = Depends(require_login),
    container: ServiceContainer = Depends(get_service_container)
):
    try:
        order = container.order_use_case.create_order(
            current_user.id, 
            order_data
        )
        return RedirectResponse("/myorders", status_code=302)
    except ValueError as e:
        return templates.TemplateResponse(
            "order_form.html",
            {"request": request, "error": str(e)}
        )
```

## 📁 File Organization

All routes should follow this pattern:
1. Import dependencies
2. Create router
3. Define routes using use cases
4. Return responses

