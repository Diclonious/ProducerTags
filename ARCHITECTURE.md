# Onion Architecture Structure

This project follows **Onion Architecture** with strict dependency inversion principles.

## Architecture Layers

### 1. Core Layer (Domain) - Innermost
**Location:** `app/domain/`

The core domain layer contains:
- **Entities** (`app/domain/entities/`): Business entities (User, Order, Package, Tag, Delivery, etc.)
- **Repository Interfaces** (`app/domain/repositories/`): Abstract interfaces defining data access contracts
- **Base** (`app/domain/base.py`): SQLAlchemy declarative base (framework-agnostic)

**Key Principles:**
- ✅ **ZERO dependencies** on other layers
- ✅ Pure business logic
- ✅ Framework-agnostic
- ✅ No infrastructure concerns

**Dependencies:** None (innermost layer)

### 2. Application Layer (Use Cases / Services)
**Location:** `app/application/`

Contains application-specific business logic:
- **Use Cases** (`app/application/use_cases/`): Business logic orchestrating domain entities
- **DTOs** (`app/application/dto/`): Data Transfer Objects for API communication
- **Services** (`app/application/services/`): Service container for dependency injection

**Key Principles:**
- ✅ Depends **only** on Domain layer (interfaces and entities)
- ✅ Orchestrates domain entities and repositories
- ✅ Contains application-specific business rules
- ✅ No infrastructure or presentation dependencies

**Dependencies:** Domain layer only

### 3. Infrastructure Layer
**Location:** `app/infrastructure/`

Contains technical implementations:
- **Database** (`app/infrastructure/database/`): Database configuration, session management, SQLAlchemy engine
- **Repositories** (`app/infrastructure/repositories/`): Concrete implementations of repository interfaces
- **Storage** (`app/infrastructure/storage/`): File storage services

**Key Principles:**
- ✅ Implements interfaces defined in Domain layer
- ✅ Handles external concerns (database, file system, external APIs)
- ✅ Depends on Domain layer (implements interfaces)
- ✅ Can depend on Application layer for wiring (ServiceContainer)

**Dependencies:** Domain layer (implements interfaces)

### 4. Presentation Layer (API / UI) - Outermost
**Location:** `app/presentation/`

Contains web framework-specific code:
- **Routes** (`app/presentation/api/routes/`): FastAPI route handlers
- **Dependencies** (`app/presentation/api/dependencies/`): FastAPI dependencies (auth, DI)

**Key Principles:**
- ✅ Uses **use cases** to serve HTTP requests
- ✅ Framework-specific (FastAPI)
- ✅ Thin layer that delegates to Application layer
- ✅ No direct domain entity manipulation (goes through use cases)

**Dependencies:** Application layer (use cases), Infrastructure layer (database sessions)

## Dependency Direction

```
┌─────────────────────────────────────┐
│   Presentation Layer (FastAPI)     │
│   - Routes                          │
│   - Dependencies                    │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│   Application Layer (Use Cases)     │
│   - Use Cases                       │
│   - DTOs                            │
│   - Service Container                │
└──────────────┬──────────────────────┘
               │ depends on
               ▼
┌─────────────────────────────────────┐
│   Domain Layer (Core)               │
│   - Entities                        │
│   - Repository Interfaces           │
│   - Base                            │
└──────────────┬──────────────────────┘
               │ implemented by
               ▼
┌─────────────────────────────────────┐
│   Infrastructure Layer               │
│   - Repository Implementations      │
│   - Database                        │
│   - File Storage                    │
└─────────────────────────────────────┘
```

**Rule:** All dependencies point **inward** toward the Domain layer.

## File Structure

```
app/
├── domain/                           # Core Layer (no dependencies)
│   ├── base.py                       # SQLAlchemy Base (framework-agnostic)
│   ├── entities/                     # Business entities
│   │   ├── User.py
│   │   ├── Order.py
│   │   ├── Package.py
│   │   ├── Tag.py
│   │   ├── Delivery.py
│   │   ├── DeliveryFile.py
│   │   ├── OrderEvent.py
│   │   ├── Message.py
│   │   ├── Notification.py
│   │   └── __init__.py
│   └── repositories/                 # Repository interfaces
│       ├── user_repository.py
│       ├── order_repository.py
│       ├── package_repository.py
│       ├── message_repository.py
│       └── notification_repository.py
│
├── application/                       # Application Layer
│   ├── use_cases/                    # Business use cases
│   │   ├── auth_use_case.py
│   │   ├── order_use_case.py
│   │   ├── package_use_case.py
│   │   ├── message_use_case.py
│   │   ├── notification_use_case.py
│   │   └── analytics_use_case.py
│   ├── dto/                          # Data Transfer Objects
│   │   ├── user.py
│   │   ├── order.py
│   │   ├── package.py
│   │   ├── message.py
│   │   └── notification.py
│   └── services/                     # Dependency injection
│       └── service_container.py
│
├── infrastructure/                    # Infrastructure Layer
│   ├── database/                     # Database setup
│   │   ├── database.py               # Engine, Session, Base import
│   │   └── startup.py                # Database initialization
│   ├── repositories/                 # Repository implementations
│   │   ├── user_repository_impl.py
│   │   ├── order_repository_impl.py
│   │   ├── package_repository_impl.py
│   │   ├── message_repository_impl.py
│   │   └── notification_repository_impl.py
│   └── storage/                      # File storage
│       └── file_storage.py
│
└── presentation/                     # Presentation Layer
    └── api/
        ├── routes/                   # Route handlers
        │   ├── auth_routes.py
        │   ├── order_routes.py
        │   ├── package_routes.py
        │   ├── message_routes.py
        │   ├── notification_routes.py
        │   ├── review_routes.py
        │   ├── resolution_routes.py
        │   └── analytics_routes.py
        └── dependencies/             # FastAPI dependencies
            └── auth.py
```

## Dependency Rules

### ✅ Allowed Dependencies

1. **Domain → Nothing** (innermost, no dependencies)
2. **Application → Domain** (use cases depend on domain interfaces)
3. **Infrastructure → Domain** (implements domain interfaces)
4. **Presentation → Application** (routes use use cases)
5. **Presentation → Infrastructure** (routes need database sessions)

### ❌ Forbidden Dependencies

1. **Domain → Infrastructure** ❌ (violates dependency inversion)
2. **Domain → Application** ❌ (core should not know about application)
3. **Domain → Presentation** ❌ (core should not know about presentation)
4. **Application → Infrastructure** ❌ (should depend on interfaces, not implementations)
5. **Application → Presentation** ❌ (application should not know about presentation)

## Key Implementation Details

### Domain Layer Independence

- Entities use `from app.domain.base import Base` (not infrastructure)
- Infrastructure imports Base from domain: `from app.domain.base import Base`
- This ensures **dependency inversion** - infrastructure depends on domain, not vice versa

### Use Cases Pattern

- Presentation layer routes call use cases
- Use cases orchestrate domain entities through repository interfaces
- Repository implementations are injected via ServiceContainer

### Service Container

- Lives in Application layer
- Wires together infrastructure implementations with use cases
- Provides dependency injection for presentation layer

## Benefits

1. **Testability**: Each layer can be tested independently with mocks
2. **Maintainability**: Clear separation of concerns
3. **Flexibility**: Easy to swap implementations (e.g., change database)
4. **Scalability**: Easy to add new features following the same pattern
5. **Independence**: Domain logic is completely independent of frameworks

## Migration Notes

- ✅ All entities moved to `app/domain/entities/`
- ✅ Base moved to `app/domain/base.py` (domain owns it)
- ✅ Infrastructure imports Base from domain (dependency inversion)
- ✅ All imports updated to use new paths
- ✅ Redundant files removed
- ✅ Database setup moved to infrastructure layer
