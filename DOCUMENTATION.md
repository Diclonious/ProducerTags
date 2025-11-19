# TaggedByBelle - Complete Documentation

## Table of Contents
1. [Overview](#overview)
2. [Technologies Used](#technologies-used)
3. [File Structure](#file-structure)
4. [Code Architecture](#code-architecture)
5. [Features](#features)
6. [Setup & Installation](#setup--installation)
7. [API Endpoints](#api-endpoints)
8. [Database Schema](#database-schema)

---

## Overview

TaggedByBelle is a professional audio tagging and metadata services platform for producers and creators. The application allows users to place orders for audio tagging services, manage their orders, communicate with admins, and leave reviews. Admins can manage orders, packages, analytics, and deliver completed work.

**Version:** 2.0.0  
**Architecture:** Clean Architecture (Onion Architecture)

---

## Technologies Used

### Backend
- **FastAPI** (0.118.0) - Modern, fast web framework for building APIs
- **Python** (3.12+) - Programming language
- **SQLAlchemy** (2.0.36) - ORM for database interactions
- **MySQL** - Relational database (via mysql-connector-python 9.0.0)
- **Pydantic** (2.11.10) - Data validation using Python type annotations
- **Jinja2** (3.1.4) - Templating engine for HTML rendering
- **Uvicorn** (0.37.0) - ASGI server for running FastAPI
- **Passlib** (1.7.4) - Password hashing library
- **Starlette** (0.48.0) - Web framework (used by FastAPI)

### Frontend
- **HTML5** - Markup language
- **CSS3** - Styling with CSS variables and modern features
- **JavaScript (Vanilla)** - Client-side interactivity
- **Chart.js** - Analytics visualization (for admin dashboard)

### Development Tools
- **Python zoneinfo** - Timezone handling (CEST/CET)

---

## File Structure

```
fastApiProject/
├── app/
│   ├── main.py                          # Application entry point
│   │
│   ├── domain/                          # Domain Layer (Core)
│   │   ├── base.py                      # SQLAlchemy Base declarative
│   │   ├── entities/                     # Domain entities (models)
│   │   │   ├── User.py                  # User entity
│   │   │   ├── Order.py                 # Order entity
│   │   │   ├── Package.py               # Package entity
│   │   │   ├── Tag.py                   # Tag entity
│   │   │   ├── Delivery.py              # Delivery entity
│   │   │   ├── DeliveryFile.py          # Delivery file entity
│   │   │   ├── OrderEvent.py            # Order event entity
│   │   │   ├── Message.py               # Message entity
│   │   │   └── Notification.py          # Notification entity
│   │   └── repositories/                # Repository interfaces
│   │       ├── order_repository.py      # IOrderRepository interface
│   │       ├── package_repository.py    # IPackageRepository interface
│   │       ├── user_repository.py       # IUserRepository interface
│   │       ├── message_repository.py    # IMessageRepository interface
│   │       └── notification_repository.py # INotificationRepository interface
│   │
│   ├── application/                     # Application Layer
│   │   ├── dto/                         # Data Transfer Objects (Pydantic schemas)
│   │   │   ├── order.py                 # Order DTOs
│   │   │   ├── user.py                  # User DTOs
│   │   │   ├── message.py                # Message DTOs
│   │   │   └── notification.py          # Notification DTOs
│   │   ├── services/                     # Service container (Dependency Injection)
│   │   │   └── service_container.py     # ServiceContainer class
│   │   └── use_cases/                    # Business logic use cases
│   │       ├── order_use_case.py        # Order business logic
│   │       ├── analytics_use_case.py    # Analytics business logic
│   │       ├── message_use_case.py       # Message business logic
│   │       └── notification_use_case.py  # Notification business logic
│   │
│   ├── infrastructure/                   # Infrastructure Layer
│   │   ├── database/                    # Database configuration
│   │   │   ├── database.py              # SQLAlchemy engine, session factory
│   │   │   └── startup.py               # Database initialization
│   │   ├── repositories/                # Repository implementations
│   │   │   ├── order_repository_impl.py # OrderRepository implementation
│   │   │   ├── package_repository_impl.py # PackageRepository implementation
│   │   │   ├── user_repository_impl.py  # UserRepository implementation
│   │   │   ├── message_repository_impl.py # MessageRepository implementation
│   │   │   └── notification_repository_impl.py # NotificationRepository implementation
│   │   ├── storage/                      # File storage
│   │   │   └── file_storage.py          # File upload/storage logic
│   │   └── utils/                        # Utility functions
│   │       └── time_utils.py            # Time synchronization utilities
│   │
│   ├── presentation/                     # Presentation Layer
│   │   └── api/                         # API routes and dependencies
│   │       ├── dependencies/             # FastAPI dependencies
│   │       │   └── auth.py              # Authentication dependencies
│   │       └── routes/                  # Route handlers
│   │           ├── auth_routes.py      # Authentication routes
│   │           ├── order_routes.py      # Order management routes
│   │           ├── package_routes.py   # Package management routes
│   │           ├── message_routes.py    # Message routes
│   │           ├── notification_routes.py # Notification routes
│   │           ├── review_routes.py     # Review routes
│   │           ├── resolution_routes.py # Resolution center routes
│   │           └── analytics_routes.py  # Analytics routes
│   │
│   ├── templates/                        # Jinja2 HTML templates
│   │   ├── base.html                    # Base template
│   │   ├── index.html                   # Homepage
│   │   ├── login.html                   # Login page
│   │   ├── signup.html                  # Signup page
│   │   ├── profile.html                 # User profile page
│   │   ├── choosepackage.html           # Package selection page
│   │   ├── order_form.html              # Order creation form
│   │   ├── myorders.html                # User orders dashboard
│   │   ├── myorders-admin.html          # Admin orders dashboard
│   │   ├── order_detail.html            # Order detail page
│   │   ├── resolution_center.html       # Resolution center page
│   │   ├── analytics.html                # Analytics dashboard
│   │   └── myreviews.html               # Reviews page
│   │
│   ├── static/                           # Static files
│   │   ├── css/                         # Stylesheets
│   │   │   ├── main.css                 # Main styles
│   │   │   └── order-detail.css         # Order detail styles
│   │   ├── js/                          # JavaScript files
│   │   │   └── main.js                  # Main JavaScript
│   │   ├── images/                      # Image assets
│   │   │   └── favicon.svg              # Favicon
│   │   └── audio/                       # Audio files
│   │       └── sample1.mp3             # Sample audio for homepage
│   │
│   └── uploads/                         # User-uploaded files
│       └── (dynamically created files)
│
├── requirements.txt                     # Python dependencies
├── reset_database.py                    # Database reset script
├── reset_passwords.py                   # Password reset utility
└── DOCUMENTATION.md                     # This file
```

---

## Code Architecture

### Clean Architecture (Onion Architecture)

The application follows **Clean Architecture** principles, also known as **Onion Architecture**, which emphasizes:

1. **Dependency Inversion**: Inner layers don't depend on outer layers
2. **Separation of Concerns**: Each layer has a specific responsibility
3. **Testability**: Business logic is independent of frameworks

### Layer Structure

#### 1. Domain Layer (Core)
- **Location**: `app/domain/`
- **Purpose**: Contains business entities and repository interfaces
- **Dependencies**: None (pure Python)
- **Components**:
  - Entities: Domain models (User, Order, Package, etc.)
  - Repository Interfaces: Abstract contracts for data access

#### 2. Application Layer
- **Location**: `app/application/`
- **Purpose**: Contains business logic and use cases
- **Dependencies**: Domain layer only
- **Components**:
  - DTOs: Data Transfer Objects (Pydantic schemas)
  - Use Cases: Business logic orchestration
  - Service Container: Dependency injection

#### 3. Infrastructure Layer
- **Location**: `app/infrastructure/`
- **Purpose**: Implements technical details
- **Dependencies**: Domain and Application layers
- **Components**:
  - Database: SQLAlchemy setup and initialization
  - Repositories: Concrete implementations of repository interfaces
  - Storage: File storage implementation
  - Utils: Utility functions (time synchronization, etc.)

#### 4. Presentation Layer
- **Location**: `app/presentation/`
- **Purpose**: Handles HTTP requests and responses
- **Dependencies**: Application and Infrastructure layers
- **Components**:
  - Routes: FastAPI route handlers
  - Dependencies: Authentication and authorization
  - Templates: Jinja2 HTML templates

### Data Flow

```
HTTP Request
    ↓
Presentation Layer (Routes)
    ↓
Application Layer (Use Cases)
    ↓
Domain Layer (Entities & Interfaces)
    ↓
Infrastructure Layer (Repository Implementations)
    ↓
Database
```

### Key Principles

1. **Dependency Inversion**: 
   - Domain defines interfaces
   - Infrastructure implements interfaces
   - Application uses interfaces (not implementations)

2. **Single Responsibility**: 
   - Each class has one reason to change
   - Use cases handle specific business operations

3. **Open/Closed Principle**: 
   - Open for extension (new use cases)
   - Closed for modification (existing code)

---

## Features

### User Features

#### 1. Authentication & Profile
- User registration and login
- Profile management (username, email, password, avatar)
- Session-based authentication
- Password hashing with Passlib

#### 2. Order Management
- **Create Orders**: Select package, add tags, provide details
- **View Orders**: Dashboard with Active, Completed, Cancelled tabs
- **Order Details**: Full order information with timeline
- **Order Status Tracking**: Real-time status updates
- **Countdown Timer**: Time remaining for delivery

#### 3. Package Selection
- View available packages (Basic, Standard, Premium)
- Package details (price, delivery days, tag count, revisions)
- Package comparison

#### 4. Communication
- **Messages**: Real-time messaging with admins
- **Notifications**: System notifications for order updates
- **Chat Sidebar**: Integrated chat interface on order pages

#### 5. Reviews & Ratings
- Submit reviews for completed orders
- Star ratings (1-5 stars)
- Review text feedback
- Public review display on homepage

#### 6. Resolution Center
- Request revisions for delivered orders
- Request order cancellation
- Request delivery date extensions
- Open disputes
- Approve/reject resolution requests

### Admin Features

#### 1. Order Management
- View all orders (Active, Completed, Cancelled)
- **Active Orders Summary**: Count and total revenue
- **Awaiting Response Section**: Delivered orders awaiting user action
- Filter orders by status
- Order details with full timeline

#### 2. Order Delivery
- Deliver orders with files and messages
- Upload multiple delivery files
- Add delivery notes
- Track delivery history

#### 3. Package Management
- Create, edit, and manage packages
- Set pricing, delivery days, tag counts
- Package descriptions

#### 4. Analytics Dashboard
- **KPIs**: Total orders, active orders, completed orders, revenue
- **Charts**: Revenue trends, completed orders, cancelled orders
- **Time Ranges**: Daily, weekly, monthly views
- Visual data representation with Chart.js

#### 5. Resolution Management
- View and respond to resolution requests
- Approve/reject cancellation requests
- Approve/reject extension requests
- Handle disputes
- Request extensions and cancellations

### System Features

#### 1. Time Management
- Synchronized time system (CEST/CET)
- Automatic order status updates (Late orders)
- Countdown timers for delivery deadlines
- 24-hour delivery standard for new orders

#### 2. File Management
- File uploads (avatars, delivery files)
- File storage in `uploads/` directory
- File download functionality
- Support for multiple file types (audio, images, documents)

#### 3. Notification System
- Real-time notifications
- Unread notification counts
- Notification types (order placed, delivered, completed, etc.)
- Notification badges

#### 4. Order Status Workflow
- **Active**: New order, in progress
- **Revision**: User requested changes
- **Late**: Past due date
- **Delivered**: Admin delivered the order
- **Completed**: User marked as complete
- **Cancelled**: Order cancelled
- **In dispute**: Resolution request active

#### 5. Homepage Features
- Hero section with call-to-action
- Audio player with waveform visualization
- Statistics display (tags delivered, average rating, turnaround)
- Public reviews section
- Professional branding

---

## Setup & Installation

### Prerequisites
- Python 3.12+
- MySQL Server
- pip (Python package manager)

### Installation Steps

1. **Clone the repository**
   ```bash
   cd fastApiProject
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure database**
   - Update `app/infrastructure/database/database.py` with your MySQL credentials:
     ```python
     DATABASE_URL = "mysql+mysqlconnector://username:password@localhost:3306/database_name"
     ```

5. **Initialize database**
   - The database will be automatically initialized on first run
   - Or run manually: `python reset_database.py --yes`

6. **Run the application**
   ```bash
   uvicorn app.main:app --reload
   ```

7. **Access the application**
   - Open browser: `http://localhost:8000`
   - Default admin: `Kohina` / `Luna123!`

---

## API Endpoints

### Authentication
- `GET /` - Homepage
- `GET /login` - Login page
- `POST /users/login` - Login handler
- `GET /signup` - Signup page
- `POST /signup` - Signup handler
- `POST /logout` - Logout
- `GET /profile` - User profile
- `POST /profile` - Update profile

### Orders
- `GET /order/new` - Create new order form
- `POST /order/new` - Submit new order
- `GET /myorders` - User orders dashboard
- `GET /myorders-admin` - Admin orders dashboard
- `GET /order/{order_id}` - Order details
- `POST /order/{order_id}/deliver` - Deliver order (admin)
- `POST /order/{order_id}/complete` - Complete order
- `POST /order/{order_id}/request-revision` - Request revision
- `POST /order/{order_id}/approve-request` - Approve resolution request
- `POST /order/{order_id}/reject-request` - Reject resolution request

### Packages
- `GET /packages` - List packages
- `GET /package/{package_id}/edit` - Edit package form
- `POST /package/{package_id}/edit` - Update package

### Messages
- `GET /order/{order_id}/messages` - Get messages
- `POST /order/{order_id}/messages` - Send message
- `GET /messages/unread-count` - Unread count
- `GET /messages/notifications` - Notifications

### Reviews
- `GET /order/{order_id}/review` - Review form
- `POST /order/{order_id}/review` - Submit review
- `GET /myreviews` - User reviews

### Resolution Center
- `GET /order/{order_id}/resolution` - Resolution center
- `POST /order/{order_id}/resolution/submit` - Submit resolution request

### Analytics (Admin)
- `GET /analytics` - Analytics dashboard

---

## Database Schema

### Users Table
- `id` (INT, Primary Key)
- `username` (VARCHAR, Unique)
- `email` (VARCHAR, Unique)
- `hashed_password` (VARCHAR)
- `is_admin` (BOOLEAN)
- `avatar` (VARCHAR, nullable)

### Orders Table
- `id` (INT, Primary Key)
- `user_id` (INT, Foreign Key → Users)
- `package_id` (INT, Foreign Key → Packages)
- `details` (TEXT)
- `status` (VARCHAR)
- `due_date` (DATETIME)
- `completed_date` (DATETIME, nullable)
- `cancelled_date` (DATETIME, nullable)
- `review` (INT, nullable)
- `review_text` (TEXT, nullable)
- `response` (TEXT, nullable)
- `request_type` (VARCHAR, nullable)
- `request_message` (TEXT, nullable)
- `cancellation_reason` (VARCHAR, nullable)
- `cancellation_message` (TEXT, nullable)
- `extension_days` (INT, nullable)
- `extension_reason` (TEXT, nullable)
- `requested_by_admin` (VARCHAR, nullable)

### Packages Table
- `id` (INT, Primary Key)
- `name` (VARCHAR)
- `price` (DECIMAL)
- `delivery_days` (INT)
- `tag_count` (INT)
- `description` (TEXT)

### Tags Table
- `id` (INT, Primary Key)
- `order_id` (INT, Foreign Key → Orders)
- `name` (VARCHAR)
- `mood` (VARCHAR)

### Deliveries Table
- `id` (INT, Primary Key)
- `order_id` (INT, Foreign Key → Orders)
- `delivery_number` (INT)
- `response_text` (TEXT)
- `delivered_at` (DATETIME)
- `user_id` (INT, Foreign Key → Users)

### DeliveryFiles Table
- `id` (INT, Primary Key)
- `delivery_id` (INT, Foreign Key → Deliveries)
- `filename` (VARCHAR)
- `original_filename` (VARCHAR)
- `uploaded_at` (DATETIME)

### OrderEvents Table
- `id` (INT, Primary Key)
- `order_id` (INT, Foreign Key → Orders)
- `event_type` (VARCHAR)
- `user_id` (INT, Foreign Key → Users)
- `event_message` (TEXT, nullable)
- `cancellation_reason` (VARCHAR, nullable)
- `cancellation_message` (TEXT, nullable)
- `extension_days` (INT, nullable)
- `extension_reason` (TEXT, nullable)
- `created_at` (DATETIME)

### Messages Table
- `id` (INT, Primary Key)
- `order_id` (INT, Foreign Key → Orders)
- `sender_id` (INT, Foreign Key → Users)
- `message_text` (TEXT)
- `created_at` (DATETIME)
- `is_read` (BOOLEAN)

### Notifications Table
- `id` (INT, Primary Key)
- `user_id` (INT, Foreign Key → Users)
- `order_id` (INT, Foreign Key → Orders, nullable)
- `notification_type` (VARCHAR)
- `title` (VARCHAR)
- `message` (TEXT)
- `is_read` (BOOLEAN)
- `created_at` (DATETIME)

---

## Key Design Decisions

### 1. Clean Architecture
- **Why**: Maintainability, testability, and scalability
- **Benefit**: Business logic is independent of frameworks

### 2. Repository Pattern
- **Why**: Abstraction of data access
- **Benefit**: Easy to swap database implementations

### 3. Use Cases
- **Why**: Encapsulate business logic
- **Benefit**: Single responsibility, easy to test

### 4. Pydantic DTOs
- **Why**: Type safety and validation
- **Benefit**: Automatic validation, clear contracts

### 5. Session-Based Auth
- **Why**: Simple, secure for web applications
- **Benefit**: No token management needed

### 6. Synchronized Time
- **Why**: Consistent time across all operations
- **Benefit**: Accurate order status, countdown timers

---

## Development Guidelines

### Adding New Features

1. **Domain Layer**: Define entities and repository interfaces
2. **Application Layer**: Create DTOs and use cases
3. **Infrastructure Layer**: Implement repositories
4. **Presentation Layer**: Add routes and templates

### Code Style
- Follow PEP 8 Python style guide
- Use type hints where possible
- Document complex functions
- Keep functions small and focused

### Testing
- Unit tests for use cases
- Integration tests for repositories
- E2E tests for critical flows

---

## License

This project is proprietary software.

---

## Contact

For questions or support, please contact the development team.

---

**Last Updated**: November 2025  
**Version**: 2.0.0

