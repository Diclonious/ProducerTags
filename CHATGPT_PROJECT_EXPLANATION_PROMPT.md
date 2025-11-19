# Complete Project Technology Stack & Architecture Explanation

## Project Overview
**TaggedByBelle** is a professional SaaS application for audio tagging services. It's a full-stack web application built with modern Python backend and server-side rendered frontend.

---

## 🗄️ DATABASE

### Database System
- **Primary Database**: MySQL (via mysql-connector-python)
- **Database Name**: `producer_tags`
- **Connection**: MySQL+mysqlconnector driver
- **ORM**: SQLAlchemy 2.0.36 (Declarative Base pattern)
- **Connection Pooling**: Enabled with pool_pre_ping and pool_recycle

### Database Models (Domain Layer)
Located in `app/domain/` directory:

1. **User** (`User.py`)
   - Fields: id, username, email, hashed_password, is_admin, avatar
   - Password hashing: Argon2 (via passlib)
   - Relationships: orders, messages, notifications

2. **Order** (`Order.py`)
   - Fields: id, user_id, package_id, details, due_date, status, response, delivery_file, review, review_text, completed_date, cancelled_date
   - Dispute system fields: request_type, request_message, cancellation_reason, cancellation_message, extension_days, extension_reason, requested_by_admin
   - Status values: "Active", "Delivered", "Revision", "Late", "Completed", "Cancelled", "In dispute"
   - Relationships: user, package, tags, deliveries, events, messages, notifications

3. **Package** (`Package.py`)
   - Fields: id, name, price, delivery_days, tag_count, description
   - Default packages: Basic, Standard, Premium

4. **Tag** (`Tag.py`)
   - Fields: id, order_id, name, mood
   - Relationship: order

5. **Delivery** (`Delivery.py`)
   - Fields: id, order_id, delivery_number, response_text, delivery_file, delivered_at, user_id
   - Supports multiple deliveries per order (revision system)

6. **DeliveryFile** (`DeliveryFile.py`)
   - Fields: id, delivery_id, filename, original_filename, file_size, uploaded_at
   - Supports multiple files per delivery

7. **OrderEvent** (`OrderEvent.py`)
   - Fields: id, order_id, event_type, user_id, event_message, created_at
   - Event types: delivered, revision_requested, completed, cancellation_requested, extension_requested, request_approved, request_rejected, etc.
   - Creates timeline/history for orders

8. **Message** (`Message.py`)
   - Fields: id, order_id, sender_id, message_text, created_at, is_read
   - Order-based chat system between users and admins

9. **Notification** (`Notification.py`)
   - Fields: id, user_id, order_id, notification_type, title, message, is_read, created_at
   - Notification types: order_placed, delivered, revision_requested, cancellation_requested, review_left, order_completed, etc.

---

## 🔧 BACKEND

### Framework & Language
- **Language**: Python 3.12
- **Web Framework**: FastAPI 0.118.0
- **ASGI Server**: Uvicorn 0.37.0
- **Template Engine**: Jinja2 3.1.4
- **Data Validation**: Pydantic 2.11.10

### Backend Architecture

#### Application Structure
```
app/
├── main.py              # Main application file (2169 lines) - all routes and business logic
├── core/
│   └── config.py        # Pydantic-based settings configuration
├── db/
│   └── database.py      # SQLAlchemy engine, session factory, Base
├── domain/              # SQLAlchemy ORM models (9 models)
├── schemas/             # Pydantic schemas (order.py)
├── services/            # Business logic services (order_service.py)
├── static/              # Static assets (CSS, JS, images)
├── templates/           # Jinja2 HTML templates (18 templates)
└── uploads/             # User-uploaded files directory
```

#### Key Backend Features

1. **Authentication & Authorization**
   - Session-based authentication (SessionMiddleware)
   - Password hashing with Argon2
   - Admin/user role-based access control
   - Dependency injection for current user (`get_current_user`, `require_login`)

2. **File Upload System**
   - Upload directory: `app/uploads/`
   - Supports: images (jpg, png, gif), documents (pdf, doc, docx, txt), archives (zip, rar), audio (wav, mp3)
   - File naming: `{prefix}_user{id}_{timestamp}_{filename}`
   - Static file serving via FastAPI StaticFiles

3. **Order Management System**
   - Package selection → Order creation → Delivery → Review workflow
   - Status transitions: Active → Delivered → Completed
   - Revision system: Delivered → Revision → Delivered (with timer reset)
   - Auto-completion: Delivered orders auto-complete after 72 hours
   - Late order detection: Orders past due_date automatically marked "Late"

4. **Dispute/Resolution Center**
   - Request types: revision, cancellation, extend_delivery
   - Status: "In dispute" during resolution
   - Approval/rejection workflow with notifications
   - Timeline events for all actions

5. **Messaging System**
   - Order-based chat between users and admins
   - Real-time message notifications
   - Unread message tracking
   - AJAX endpoints for message loading

6. **Notification System**
   - Real-time notifications via AJAX
   - Unread count badges
   - Notification types for all order events
   - Auto-update every 10 seconds

7. **Analytics Dashboard** (Admin only)
   - KPIs: total orders, completed, delivered, active, late, revision, dispute, cancelled
   - Revenue tracking: monthly earnings, expected earnings, cancelled revenue
   - Charts: Chart.js for revenue and order trends (monthly/yearly)
   - Completion rate, cancellation rate, average rating

8. **Review System**
   - Star rating (1-5 stars)
   - Review text
   - Public reviews on homepage
   - Admin review management

#### Database Session Management
- SessionLocal factory pattern
- Dependency injection via `get_db()` for route handlers
- Automatic session cleanup with try/finally blocks
- Joined loading for relationships (eager loading)

#### Startup Events
- Table creation (Base.metadata.create_all)
- Migration for dispute system columns
- Default admin user creation (Kohina / Luna123!)
- Default package initialization

---

## 🎨 FRONTEND

### Frontend Technologies

#### Core Technologies
- **Template Engine**: Jinja2 (server-side rendering)
- **CSS**: Custom design system (500+ lines in `main.css`)
- **JavaScript**: Vanilla JavaScript (300+ lines in `main.js`)
- **Charts**: Chart.js 4.4.1 (CDN)
- **Fonts**: Google Fonts - Inter (weights: 400, 500, 600, 700, 800, 900)

#### Frontend Architecture

**Templates** (18 HTML files in `app/templates/`):
- `base.html` - Base template with navigation, footer, notifications, messages
- `index.html` - Homepage with public reviews
- `login.html` / `signup.html` - Authentication
- `myorders.html` - User dashboard
- `myorders-admin.html` - Admin dashboard
- `order_detail.html` - Order detail with timeline, chat, file downloads
- `order_form.html` - Order creation form
- `choosepackage.html` - Package selection
- `review_form.html` - Review submission
- `profile.html` - User profile settings
- `analytics.html` - Admin analytics dashboard
- `packages.html` / `edit_package.html` - Package management
- `completed_orders.html` - Completed orders view
- `myreviews.html` / `adminreviews.html` - Review management
- `resolution_center.html` - Dispute resolution interface

**Static Assets**:
- `app/static/css/main.css` - Complete design system
- `app/static/js/main.js` - Interactive components
- `app/static/css/order-detail.css` - Order detail specific styles
- `app/static/images/` - Image assets

#### Design System

**Color Palette**:
- Background: Dark theme (#0a0e17, #0e1422, #151b2b, #1a2235)
- Brand: Electric Lime (#e2fb52)
- Accent: Purple (#7c3aed)
- Status colors: Active (blue), Delivered (green), Late (red), Revision (yellow), Completed (gray), Cancelled (red), Dispute (purple)

**Typography**:
- Font family: Inter (Google Fonts)
- Sizes: xs (0.75rem) to 5xl (3rem)
- Weights: 400-900

**Components**:
- Buttons: Primary, secondary, ghost variants
- Cards: Elevated surfaces with borders
- Modals: Backdrop blur, smooth animations
- Dropdowns: User menu, notifications, messages
- Forms: Input fields, textareas, file uploads
- Badges: Status indicators, unread counts
- Timeline: Order history visualization
- Charts: Chart.js integration

**Responsive Design**:
- Mobile-first approach
- Breakpoints: < 768px (mobile), 768px-1024px (tablet), > 1024px (desktop)
- Touch-friendly interactions
- Responsive grid layouts

#### JavaScript Features

**Interactive Components**:
1. **Dropdown Menus**: User menu, notifications, messages inbox
2. **Modals**: Smooth open/close animations
3. **Toast Notifications**: Success/error messages
4. **Countdown Timers**: Live order due date countdowns
5. **Form Validation**: Client-side validation
6. **File Upload**: Drag-and-drop with preview
7. **Star Rating**: Interactive hover and click
8. **Notifications System**: Real-time updates, unread badges
9. **Messages System**: Inbox dropdown, unread tracking
10. **Charts**: Chart.js initialization and data binding

**AJAX Endpoints Used**:
- `/notifications` - Get all notifications
- `/notifications/unread-count` - Get unread count
- `/notifications/{id}/mark-read` - Mark as read
- `/notifications/mark-all-read` - Mark all as read
- `/messages/notifications` - Get message notifications
- `/messages/unread-count` - Get unread message count
- `/messages/mark-all-read` - Mark all messages read
- `/order/{id}/messages` - Get order messages
- `/order/{id}/messages/send` - Send message

---

## 📁 FILE STRUCTURE

```
fastApiProject/
├── app/
│   ├── __init__.py
│   ├── main.py                    # Main application (2169 lines)
│   ├── core/
│   │   └── config.py              # Settings configuration
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py            # SQLAlchemy setup
│   ├── domain/                    # ORM Models
│   │   ├── User.py
│   │   ├── Order.py
│   │   ├── Package.py
│   │   ├── Tag.py
│   │   ├── Delivery.py
│   │   ├── DeliveryFile.py
│   │   ├── OrderEvent.py
│   │   ├── Message.py
│   │   └── Notification.py
│   ├── schemas/
│   │   └── order.py               # Pydantic schemas
│   ├── services/
│   │   └── order_service.py      # Business logic
│   ├── static/
│   │   ├── css/
│   │   │   ├── main.css          # Design system (500+ lines)
│   │   │   └── order-detail.css
│   │   ├── js/
│   │   │   └── main.js           # Interactive JS (300+ lines)
│   │   └── images/
│   ├── templates/                 # 18 Jinja2 templates
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── login.html
│   │   ├── signup.html
│   │   ├── myorders.html
│   │   ├── myorders-admin.html
│   │   ├── order_detail.html
│   │   ├── order_form.html
│   │   ├── choosepackage.html
│   │   ├── review_form.html
│   │   ├── profile.html
│   │   ├── analytics.html
│   │   ├── packages.html
│   │   ├── edit_package.html
│   │   ├── completed_orders.html
│   │   ├── myreviews.html
│   │   ├── adminreviews.html
│   │   └── resolution_center.html
│   └── uploads/                   # User uploads directory
├── venv/                          # Python virtual environment
├── app.db                         # SQLite database (if used as fallback)
├── requirements.txt               # Python dependencies
├── README.md                      # Project documentation
└── [Various .md documentation files]
```

---

## 🔌 API ENDPOINTS

### Authentication
- `GET /` - Homepage
- `GET /login` - Login page
- `POST /users/login` - Login handler
- `GET /signup` - Signup page
- `POST /signup` - Signup handler
- `POST /logout` - Logout

### Orders
- `GET /order/new` - Package selection
- `POST /order/new` - Select package
- `POST /order/submit` - Create order
- `GET /myorders` - User orders dashboard
- `GET /myorders-admin` - Admin orders dashboard
- `GET /completed-orders` - Completed orders
- `GET /order/{order_id}` - Order detail
- `POST /order/{order_id}/complete` - Mark complete
- `POST /order/{order_id}/deliver` - Admin deliver order
- `POST /order/{order_id}/request-revision` - Request revision
- `POST /order/{order_id}/approve-delivery` - Approve delivery
- `GET /order/{order_id}/download-delivered-file/{file_id}` - Download file

### Reviews
- `GET /order/{order_id}/review` - Review form
- `POST /order/{order_id}/review` - Submit review
- `GET /myreviews` - User reviews
- `GET /adminreviews` - Admin reviews (all users)

### Resolution Center
- `GET /order/{order_id}/resolution` - Resolution center
- `POST /order/{order_id}/resolution/submit` - Submit resolution request
- `POST /order/{order_id}/approve-request` - Approve request
- `POST /order/{order_id}/reject-request` - Reject request

### Package Management (Admin)
- `GET /packages` - List packages
- `GET /package/{package_id}/edit` - Edit package form
- `POST /package/{package_id}/edit` - Update package

### Messaging
- `POST /order/{order_id}/messages/send` - Send message
- `GET /order/{order_id}/messages` - Get messages (AJAX)
- `GET /messages/notifications` - Get message notifications (AJAX)
- `GET /messages/unread-count` - Get unread count (AJAX)
- `POST /messages/mark-all-read` - Mark all read (AJAX)

### Notifications
- `GET /notifications` - Get notifications (AJAX)
- `GET /notifications/unread-count` - Get unread count (AJAX)
- `POST /notifications/{id}/mark-read` - Mark as read (AJAX)
- `POST /notifications/mark-all-read` - Mark all read (AJAX)

### Analytics (Admin)
- `GET /analytics` - Analytics dashboard

### Profile
- `GET /profile` - Profile page
- `POST /profile` - Update profile

---

## 🛠️ DEPENDENCIES

### Python Packages (requirements.txt)
```
fastapi==0.118.0          # Web framework
uvicorn==0.37.0            # ASGI server
pydantic==2.11.10          # Data validation
jinja2==3.1.4              # Template engine
SQLAlchemy==2.0.36         # ORM
mysql-connector-python==9.0.0  # MySQL driver
itsdangerous==2.2.0        # Session security
starlette~=0.48.0          # ASGI framework (FastAPI dependency)
passlib~=1.7.4             # Password hashing (Argon2)
```

### Frontend Dependencies (CDN)
- Chart.js 4.4.1 - Analytics charts
- Google Fonts (Inter) - Typography

---

## 🏗️ CODE STRUCTURE & PATTERNS

### Backend Patterns

1. **Dependency Injection**
   - FastAPI's `Depends()` for database sessions
   - `get_db()` dependency for database access
   - `get_current_user()` for authentication

2. **Session Management**
   - SessionMiddleware for user sessions
   - Session data: user_id, username, is_admin, email, avatar_url

3. **Helper Functions**
   - `update_late_orders()` - Auto-update late orders
   - `auto_complete_delivered_orders()` - Auto-complete after 72h
   - `get_orders_with_relationships()` - Eager loading
   - `calculate_monthly_revenue()` - Revenue calculation
   - `save_uploaded_file()` - File upload helper
   - `create_notification()` - Notification creation
   - `calculate_chart_data()` - Analytics data

4. **Error Handling**
   - HTTPException for API errors
   - RedirectResponse for page redirects
   - Try/finally blocks for database cleanup

5. **Template Rendering**
   - Jinja2Templates for HTML rendering
   - Template context injection
   - Block inheritance (base.html)

### Frontend Patterns

1. **Component-Based CSS**
   - CSS custom properties (variables)
   - Utility classes
   - Component classes

2. **Progressive Enhancement**
   - Works without JavaScript
   - JavaScript enhances UX
   - AJAX for real-time features

3. **Event-Driven JavaScript**
   - DOMContentLoaded initialization
   - Event delegation
   - Async/await for API calls

4. **State Management**
   - Session storage for user data
   - DOM state for UI components
   - Real-time updates via polling

---

## 🔐 SECURITY FEATURES

1. **Authentication**
   - Argon2 password hashing
   - Session-based authentication
   - Role-based access control (admin/user)

2. **Authorization**
   - Route-level protection (`require_login`)
   - Admin-only routes
   - Order ownership validation

3. **Input Validation**
   - Pydantic email validation
   - Form data validation
   - File upload validation

4. **Session Security**
   - Secret key for session signing
   - Session timeout (24 hours)

---

## 📊 BUSINESS LOGIC

### Order Workflow
1. User selects package → Creates order (status: "Active")
2. Admin delivers → Status: "Delivered"
3. User can:
   - Approve → Status: "Completed"
   - Request revision → Status: "Revision" (timer resets)
   - Auto-complete after 72 hours → Status: "Completed"

### Dispute System
1. User/Admin submits request → Status: "In dispute"
2. Other party approves/rejects
3. If approved: Status changes based on request type
4. If rejected: Status reverts to previous state

### Payment Processing
- Payment form validation (card number, expiry, CVV)
- **Note**: No actual payment gateway integration (validation only)

---

## 🚀 DEPLOYMENT

### Development
- Run: `uvicorn app.main:app --reload`
- Database: MySQL on localhost:3306
- Default admin: Kohina / Luna123!

### Production Considerations
- Environment variables for secrets
- Database connection pooling
- Static file serving optimization
- Session secret key configuration
- File upload size limits
- Error logging and monitoring

---

## 📝 KEY FEATURES SUMMARY

1. **User Management**: Registration, login, profiles, avatars
2. **Order Management**: Creation, tracking, delivery, completion
3. **Package System**: Multiple service tiers with pricing
4. **Review System**: Star ratings and text reviews
5. **Messaging**: Order-based chat between users and admins
6. **Notifications**: Real-time notifications for all events
7. **Dispute Resolution**: Cancellation, revision, extension requests
8. **Analytics**: Admin dashboard with KPIs and charts
9. **File Management**: Upload, download, multiple files per delivery
10. **Timeline System**: Complete order history with events

---

This is a complete, production-ready SaaS application with modern architecture, comprehensive features, and professional UI/UX design.

