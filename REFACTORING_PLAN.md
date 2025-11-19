# Clean Architecture Refactoring Plan

## Target Structure

```
app/
├── domain/                    # Domain Layer (Entities, Value Objects, Domain Services)
│   ├── entities/              # Domain entities (move from domain/)
│   ├── repositories/          # Repository interfaces (abstract)
│   └── services/              # Domain services
│
├── application/               # Application Layer (Use Cases, DTOs)
│   ├── use_cases/             # Business use cases
│   ├── dto/                   # Data Transfer Objects (Pydantic schemas)
│   └── services/              # Application services
│
├── infrastructure/            # Infrastructure Layer (External concerns)
│   ├── database/              # Database setup, migrations
│   ├── repositories/         # Repository implementations
│   ├── storage/               # File storage
│   └── external/              # External services
│
├── presentation/              # Presentation Layer (API, UI)
│   ├── api/                   # FastAPI routes
│   │   ├── routes/            # Route handlers
│   │   └── dependencies/      # FastAPI dependencies
│   └── web/                   # Web templates (templates/)
│
├── core/                      # Core configuration
└── static/                    # Static files (unchanged)
```

## Migration Strategy

1. Create new folder structure
2. Move domain entities to domain/entities/
3. Create repository interfaces
4. Create Pydantic schemas
5. Implement repositories
6. Create use cases
7. Refactor routes
8. Update main.py

